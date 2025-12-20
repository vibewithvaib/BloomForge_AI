"""
ChromaDB vector store with strict namespace isolation.
Each document gets its own collection: user_id::document_id

This ensures:
1. No cross-user data leakage
2. No cross-document data leakage
3. Easy cleanup on document deletion
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path


class VectorStore:
    """
    Manages vector storage for document chunks.
    Uses namespace pattern: {user_id}::{document_id}
    """
    
    def __init__(self, persist_dir: str):
        """Initialize ChromaDB client."""
        # Ensure persist directory exists
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    
    def _get_collection_name(self, user_id: str, document_id: str) -> str:
        """
        Generate namespaced collection name.
        Format: {user_id}__{document_id}
        
        This ensures complete isolation.
        Note: Uses __ instead of :: to comply with ChromaDB naming rules [a-zA-Z0-9._-]
        """
        return f"{user_id}__{document_id}"
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks.
        Overlap helps maintain context across boundaries.
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundaries
            if end < text_length:
                # Look for last period, question mark, or exclamation
                for delimiter in ['. ', '? ', '! ', '\n\n']:
                    last_delim = chunk.rfind(delimiter)
                    if last_delim > chunk_size * 0.7:  # Only if we're far enough
                        chunk = chunk[:last_delim + 1]
                        break
            
            chunks.append(chunk.strip())
            start += chunk_size - overlap
        
        return chunks
    
    def store_document(
        self, 
        user_id: str, 
        document_id: str, 
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Store document text in ChromaDB with namespace isolation.
        
        Steps:
        1. Chunk the text
        2. Create isolated collection
        3. Store chunks with metadata
        """
        collection_name = self._get_collection_name(user_id, document_id)
        
        # Create or get collection
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "user_id": user_id,
                "document_id": document_id,
                "description": "Document chunks for concept extraction"
            }
        )
        
        # Chunk the text
        chunks = self._chunk_text(text, chunk_size, chunk_overlap)
        
        # Prepare data for insertion
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "chunk_index": i,
                "user_id": user_id,
                "document_id": document_id
            }
            for i in range(len(chunks))
        ]
        
        # Store in ChromaDB
        collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
    
    def get_all_chunks(self, user_id: str, document_id: str) -> List[str]:
        """
        Retrieve all chunks for a document.
        Used by Agent 1 to read entire document.
        """
        collection_name = self._get_collection_name(user_id, document_id)
        
        try:
            collection = self.client.get_collection(name=collection_name)
            
            # Get all documents
            results = collection.get()
            
            # Sort by chunk index
            chunks_with_index = [
                (doc, meta['chunk_index']) 
                for doc, meta in zip(results['documents'], results['metadatas'])
            ]
            chunks_with_index.sort(key=lambda x: x[1])
            
            return [chunk for chunk, _ in chunks_with_index]
        
        except Exception:
            # Collection doesn't exist
            return []
    
    def semantic_search(
        self, 
        user_id: str, 
        document_id: str, 
        query: str, 
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search within a specific document.
        Used by Agent 2 to retrieve relevant context.
        """
        collection_name = self._get_collection_name(user_id, document_id)
        
        try:
            collection = self.client.get_collection(name=collection_name)
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            search_results = []
            if results['documents'] and results['documents'][0]:
                for doc, meta, distance in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    search_results.append({
                        'text': doc,
                        'metadata': meta,
                        'distance': distance
                    })
            
            return search_results
        
        except Exception:
            # Collection doesn't exist
            return []
    
    def delete_document(self, user_id: str, document_id: str):
        """
        Delete all vector data for a document.
        Called when user deletes a document.
        """
        collection_name = self._get_collection_name(user_id, document_id)
        
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            # Collection doesn't exist - that's fine
            pass
    
    def get_full_text(self, user_id: str, document_id: str) -> str:
        """
        Reconstruct full text from chunks.
        Useful for Agent 1.
        """
        chunks = self.get_all_chunks(user_id, document_id)
        return "\n\n".join(chunks)
