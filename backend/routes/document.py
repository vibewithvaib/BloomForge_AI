"""
FastAPI routes for document operations.

Endpoints:
- POST /api/document/create - Upload educational text
- GET /api/document/{document_id} - Get document with concepts
- GET /api/user/{user_id}/documents - List user's documents
- DELETE /api/document/{document_id} - Delete document
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from datetime import datetime
from typing import List
import json

from models.schemas import (
    DocumentCreateRequest,
    DocumentCreateResponse,
    DocumentResponse,
    DocumentListResponse,
    Concept
)
from db.database import Database
from vectorstore.chroma_client import VectorStore
from agents.concept_agent import extract_concept_hierarchy
from config import settings


router = APIRouter(prefix="/api/document", tags=["documents"])


# Dependency injection
def get_db() -> Database:
    """Get database instance."""
    return Database(settings.database_path)


def get_vector_store() -> VectorStore:
    """Get vector store instance."""
    return VectorStore(settings.chroma_persist_dir)


# ====================================================
# BACKGROUND TASK: Process Document
# ====================================================

async def process_document_background(
    document_id: str,
    user_id: str,
    text: str
):
    """
    Background task to process uploaded document.
    
    Steps:
    1. Store text in ChromaDB
    2. Run Agent 1 to extract concepts
    3. Save concepts to database
    4. Update document status
    """
    db = get_db()
    vector_store = get_vector_store()
    
    try:
        # Step 1: Store in vector database
        vector_store.store_document(
            user_id=user_id,
            document_id=document_id,
            text=text,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        # Step 2: Extract concepts using Agent 1
        hierarchy = await extract_concept_hierarchy(text)
        
        # Step 3: Save concepts to database
        db.save_concepts(document_id, hierarchy.concepts)
        
        # Step 4: Update document status
        db.update_document_status(
            document_id=document_id,
            status="completed",
            concept_hierarchy=hierarchy
        )
    
    except Exception as e:
        # Mark as failed
        db.update_document_status(
            document_id=document_id,
            status="failed"
        )
        print(f"Document processing failed: {e}")


# ====================================================
# ROUTES
# ====================================================

@router.post("/create", response_model=DocumentCreateResponse)
async def create_document(
    request: DocumentCreateRequest,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db)
):
    """
    Upload educational text and start processing.
    
    This returns immediately with 'processing' status.
    Processing happens in background.
    """
    # Create document record
    document_id = db.create_document(
        user_id=request.user_id,
        raw_text=request.text
    )
    
    # Queue background processing
    background_tasks.add_task(
        process_document_background,
        document_id=document_id,
        user_id=request.user_id,
        text=request.text
    )
    
    return DocumentCreateResponse(
        document_id=document_id,
        status="processing",
        message="Document is being processed. Check status with GET /api/document/{document_id}"
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    user_id: str,
    db: Database = Depends(get_db)
):
    """
    Get document details including extracted concepts.
    
    CRITICAL: user_id is required to enforce isolation.
    """
    # Get document (enforces user ownership)
    doc = db.get_document(document_id, user_id)
    
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found or access denied"
        )
    
    # Get concepts
    concepts = db.get_concepts(document_id, user_id)
    
    return DocumentResponse(
        document_id=doc["id"],
        user_id=doc["user_id"],
        status=doc["status"],
        concepts=concepts,
        created_at=doc["created_at"],
        updated_at=doc["updated_at"]
    )


@router.get("/user/{user_id}/list", response_model=DocumentListResponse)
async def list_user_documents(
    user_id: str,
    db: Database = Depends(get_db)
):
    """
    List all documents for a user.
    """
    docs = db.get_user_documents(user_id)
    
    # Convert to response format
    document_responses = []
    for doc in docs:
        # Get concepts for each document
        concepts = db.get_concepts(doc["id"], user_id)
        
        document_responses.append(DocumentResponse(
            document_id=doc["id"],
            user_id=doc["user_id"],
            status=doc["status"],
            concepts=concepts,
            created_at=doc["created_at"],
            updated_at=doc["updated_at"]
        ))
    
    return DocumentListResponse(documents=document_responses)


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str,
    db: Database = Depends(get_db),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Delete a document and all associated data.
    
    This cascades to:
    - Concepts
    - Explanations
    - Quizzes
    - Vector embeddings
    """
    # Delete from database (cascades to concepts, explanations, quizzes)
    deleted = db.delete_document(document_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found or access denied"
        )
    
    # Delete from vector store
    vector_store.delete_document(user_id, document_id)
    
    return {
        "message": f"Document {document_id} deleted successfully",
        "document_id": document_id
    }
