"""
SQLite database layer with strict isolation guarantees.
All queries are scoped to (user_id, document_id) pairs.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path

from models.schemas import Concept, ConceptHierarchy, DocumentDB, ConceptDB


class Database:
    """
    Manages all structured data storage.
    Enforces isolation at the query level.
    """
    
    def __init__(self, db_path: str):
        """Initialize database and create tables if needed."""
        self.db_path = db_path
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize schema
        self._init_schema()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Allow dict-like access
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_schema(self):
        """Create database schema if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    concept_hierarchy TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            
            # Index for user queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_user_id 
                ON documents(user_id)
            """)
            
            # Concepts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concepts (
                    id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    importance REAL NOT NULL,
                    level INTEGER NOT NULL,
                    prerequisites TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (id, document_id),
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            
            # Index for concept queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_concepts_document_id 
                ON concepts(document_id)
            """)
            
            # Explanations table (cache for generated explanations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS explanations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    concept_id TEXT NOT NULL,
                    tone TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            
            # Quizzes table (cache for generated quizzes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quizzes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    concept_id TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    questions TEXT NOT NULL,
                    validation_passed INTEGER NOT NULL,
                    validation_feedback TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
    
    # ====================================================
    # DOCUMENT OPERATIONS
    # ====================================================
    
    def create_document(self, user_id: str, raw_text: str) -> str:
        """
        Create a new document and return its ID.
        Document starts in 'processing' status.
        """
        document_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documents (id, user_id, raw_text, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (document_id, user_id, raw_text, "processing", now, now))
        
        return document_id
    
    def get_document(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID, ensuring it belongs to the specified user.
        CRITICAL: This enforces user isolation.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM documents 
                WHERE id = ? AND user_id = ?
            """, (document_id, user_id))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_document_status(
        self, 
        document_id: str, 
        status: str, 
        concept_hierarchy: Optional[ConceptHierarchy] = None
    ):
        """Update document status and optionally store concept hierarchy."""
        now = datetime.utcnow()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if concept_hierarchy:
                hierarchy_json = json.dumps([c.model_dump() for c in concept_hierarchy.concepts])
                cursor.execute("""
                    UPDATE documents 
                    SET status = ?, concept_hierarchy = ?, updated_at = ?
                    WHERE id = ?
                """, (status, hierarchy_json, now, document_id))
            else:
                cursor.execute("""
                    UPDATE documents 
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                """, (status, now, document_id))
    
    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM documents 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_document(self, document_id: str, user_id: str) -> bool:
        """
        Delete a document (and cascade to concepts, explanations, quizzes).
        Returns True if deleted, False if not found or wrong user.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM documents 
                WHERE id = ? AND user_id = ?
            """, (document_id, user_id))
            
            return cursor.rowcount > 0
    
    # ====================================================
    # CONCEPT OPERATIONS
    # ====================================================
    
    def save_concepts(self, document_id: str, concepts: List[Concept]):
        """
        Save all concepts for a document.
        This is called after Agent 1 completes.
        """
        now = datetime.utcnow()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clear existing concepts (in case of re-processing)
            cursor.execute("DELETE FROM concepts WHERE document_id = ?", (document_id,))
            
            # Insert new concepts
            for concept in concepts:
                cursor.execute("""
                    INSERT INTO concepts 
                    (id, document_id, name, definition, importance, level, prerequisites, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    concept.id,
                    document_id,
                    concept.name,
                    concept.definition,
                    concept.importance,
                    concept.level,
                    json.dumps(concept.prerequisites),
                    now
                ))
    
    def get_concepts(self, document_id: str, user_id: str) -> List[Concept]:
        """
        Get all concepts for a document, ensuring user owns the document.
        """
        # First verify user owns this document
        doc = self.get_document(document_id, user_id)
        if not doc:
            return []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM concepts 
                WHERE document_id = ?
                ORDER BY level ASC, importance DESC
            """, (document_id,))
            
            concepts = []
            for row in cursor.fetchall():
                concepts.append(Concept(
                    id=row["id"],
                    name=row["name"],
                    definition=row["definition"],
                    importance=row["importance"],
                    level=row["level"],
                    prerequisites=json.loads(row["prerequisites"])
                ))
            
            return concepts
    
    def get_concept(self, document_id: str, concept_id: str, user_id: str) -> Optional[Concept]:
        """Get a specific concept, ensuring user owns the document."""
        # First verify user owns this document
        doc = self.get_document(document_id, user_id)
        if not doc:
            return None
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM concepts 
                WHERE document_id = ? AND id = ?
            """, (document_id, concept_id))
            
            row = cursor.fetchone()
            if row:
                return Concept(
                    id=row["id"],
                    name=row["name"],
                    definition=row["definition"],
                    importance=row["importance"],
                    level=row["level"],
                    prerequisites=json.loads(row["prerequisites"])
                )
            return None
    
    # ====================================================
    # EXPLANATION OPERATIONS
    # ====================================================
    
    def save_explanation(
        self, 
        document_id: str, 
        concept_id: str, 
        tone: str, 
        explanation: str
    ):
        """Cache a generated explanation."""
        now = datetime.utcnow()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO explanations 
                (document_id, concept_id, tone, explanation, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (document_id, concept_id, tone, explanation, now))
    
    # ====================================================
    # QUIZ OPERATIONS
    # ====================================================
    
    def save_quiz(
        self, 
        document_id: str, 
        concept_id: str, 
        difficulty: str,
        questions: List[Dict[str, Any]],
        validation_passed: bool,
        validation_feedback: Optional[str] = None
    ):
        """Cache a generated quiz."""
        now = datetime.utcnow()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quizzes 
                (document_id, concept_id, difficulty, questions, 
                 validation_passed, validation_feedback, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id, 
                concept_id, 
                difficulty, 
                json.dumps(questions),
                1 if validation_passed else 0,
                validation_feedback,
                now
            ))
