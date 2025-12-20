"""
FastAPI routes for quiz generation (Agent 2, Mode B).

Endpoints:
- POST /api/quiz - Generate adaptive quiz with validation
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List

from models.schemas import QuizRequest, QuizResponse, Question
from db.database import Database
from agents.adaptive_agent import generate_quiz
from validation.difficulty_rules import validate_quiz_difficulty
from config import settings


router = APIRouter(prefix="/api", tags=["quizzes"])


def get_db() -> Database:
    """Get database instance."""
    return Database(settings.database_path)


@router.post("/quiz", response_model=QuizResponse)
async def generate_adaptive_quiz(
    request: QuizRequest,
    user_id: str,  # Required query parameter for isolation
    db: Database = Depends(get_db)
):
    """
    Generate an adaptive quiz for a specific concept.
    
    This implements the validation loop:
    1. Agent 2 generates quiz
    2. Validator checks difficulty
    3. If fails, Agent 2 retries (up to max_retries)
    4. Return validated quiz or error
    
    Args:
        request: Quiz request with document_id, concept_id, difficulty
        user_id: User ID (query parameter for isolation)
    
    Returns:
        Quiz response with exactly 10 questions
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
    
    # Validation loop with retries
    validation_passed = False
    validation_feedback = None
    questions: List[Question] = []
    
    for attempt in range(settings.max_retries):
        try:
            # Generate quiz using Agent 2
            questions = await generate_quiz(
                target_concept=target_concept,
                all_concepts=all_concepts,
                difficulty=request.difficulty
            )
            
            # Validate difficulty
            validation_result = validate_quiz_difficulty(
                questions=questions,
                target_concept=target_concept,
                all_concepts=all_concepts,
                requested_difficulty=request.difficulty
            )
            
            if validation_result.passed:
                validation_passed = True
                break
            else:
                # Store feedback for potential retry
                validation_feedback = validation_result.feedback
                print(f"Validation failed (attempt {attempt + 1}/{settings.max_retries}): {validation_feedback}")
        
        except Exception as e:
            print(f"Quiz generation failed (attempt {attempt + 1}/{settings.max_retries}): {e}")
            if attempt == settings.max_retries - 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate quiz after {settings.max_retries} attempts: {str(e)}"
                )
    
    # If validation never passed after all retries
    if not validation_passed:
        # Still return the quiz but mark as unvalidated
        # In production, you might want to reject this
        print(f"Warning: Quiz validation failed after {settings.max_retries} attempts")
    
    # Save to database (cache)
    db.save_quiz(
        document_id=request.document_id,
        concept_id=request.concept_id,
        difficulty=request.difficulty,
        questions=[q.model_dump() for q in questions],
        validation_passed=validation_passed,
        validation_feedback=validation_feedback
    )
    
    return QuizResponse(
        document_id=request.document_id,
        concept_id=request.concept_id,
        difficulty=request.difficulty,
        questions=questions,
        validation_passed=validation_passed,
        validation_feedback=validation_feedback,
        generated_at=datetime.utcnow()
    )
