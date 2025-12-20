"""
FastAPI routes for explanation generation (Agent 2, Mode A).

Endpoints:
- POST /api/explain - Generate concept explanation
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from models.schemas import ExplanationRequest, ExplanationResponse
from db.database import Database
from agents.adaptive_agent import generate_explanation
from config import settings


router = APIRouter(prefix="/api", tags=["explanations"])


def get_db() -> Database:
    """Get database instance."""
    return Database(settings.database_path)


@router.post("/explain", response_model=ExplanationResponse)
async def explain_concept(
    request: ExplanationRequest,
    user_id: str,  # Required query parameter
    db: Database = Depends(get_db)
):
    """
    Generate an explanation for a specific concept.
    
    Args:
        request: Explanation request with document_id, concept_id, tone
        user_id: User ID (query parameter for isolation)
    
    Returns:
        Explanation response with generated text
    """
    # Verify user owns this document
    doc = db.get_document(request.document_id, user_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document {request.document_id} not found or access denied"
        )
    
    # Get all concepts for context
    all_concepts = db.get_concepts(request.document_id, user_id)
    if not all_concepts:
        raise HTTPException(
            status_code=400,
            detail=f"No concepts found for document {request.document_id}"
        )
    
    # Find target concept
    target_concept = next(
        (c for c in all_concepts if c.id == request.concept_id),
        None
    )
    
    if not target_concept:
        raise HTTPException(
            status_code=404,
            detail=f"Concept {request.concept_id} not found in document"
        )
    
    # Generate explanation using Agent 2
    explanation = await generate_explanation(
        target_concept=target_concept,
        all_concepts=all_concepts,
        tone=request.tone
    )
    
    # Save to database (cache)
    db.save_explanation(
        document_id=request.document_id,
        concept_id=request.concept_id,
        tone=request.tone,
        explanation=explanation
    )
    
    return ExplanationResponse(
        document_id=request.document_id,
        concept_id=request.concept_id,
        tone=request.tone,
        explanation=explanation,
        generated_at=datetime.utcnow()
    )
