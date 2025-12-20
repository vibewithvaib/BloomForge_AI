"""
Pydantic models for API contracts and internal data structures.
These models ensure type safety and validation across the entire backend.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ====================================================
# CONCEPT MODELS
# ====================================================

class Concept(BaseModel):
    """
    Represents a single educational concept extracted from text.
    This is the ONLY knowledge structure - no separate topics/subtopics.
    """
    id: str = Field(..., description="Unique concept ID (e.g., C1, C2)")
    name: str = Field(..., description="Human-readable concept name")
    definition: str = Field(..., description="Short definition of the concept")
    importance: float = Field(..., ge=0.0, le=1.0, description="Importance score 0-1")
    level: int = Field(..., ge=0, description="Hierarchy level (0=foundational)")
    prerequisites: List[str] = Field(default_factory=list, description="List of prerequisite concept IDs")


class ConceptHierarchy(BaseModel):
    """Output from Agent 1: Complete concept hierarchy for a document."""
    concepts: List[Concept]


# ====================================================
# DOCUMENT MODELS
# ====================================================

class DocumentCreateRequest(BaseModel):
    """Request to create a new document from educational text."""
    user_id: str = Field(..., description="User identifier")
    text: str = Field(..., min_length=100, description="Raw educational text")


class DocumentCreateResponse(BaseModel):
    """Response after initiating document creation."""
    document_id: str
    status: Literal["processing", "completed", "failed"]
    message: Optional[str] = None


class DocumentResponse(BaseModel):
    """Full document details including extracted concepts."""
    document_id: str
    user_id: str
    status: Literal["processing", "completed", "failed"]
    concepts: List[Concept]
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """List of documents for a user."""
    documents: List[DocumentResponse]


# ====================================================
# EXPLANATION MODELS (Agent 2, Mode A)
# ====================================================

class ExplanationRequest(BaseModel):
    """Request to explain a specific concept."""
    document_id: str
    concept_id: str = Field(..., description="The concept to explain (e.g., C2)")
    tone: Literal["simple", "exam", "detailed", "intuitive"] = Field(
        default="simple",
        description="Explanation style"
    )


class ExplanationResponse(BaseModel):
    """Plain text explanation of a concept."""
    document_id: str
    concept_id: str
    tone: str
    explanation: str
    generated_at: datetime


# ====================================================
# QUIZ MODELS (Agent 2, Mode B)
# ====================================================

class Question(BaseModel):
    """A single quiz question with metadata."""
    id: str = Field(..., description="Question ID (e.g., Q1)")
    question: str = Field(..., description="The question text")
    blooms_level: Literal[
        "Remember",
        "Understand",
        "Apply",
        "Analyze",
        "Evaluate",
        "Create"
    ] = Field(..., description="Bloom's taxonomy level")
    concepts: List[str] = Field(..., description="Concept IDs tested by this question")
    difficulty_score: int = Field(..., ge=1, le=10, description="Difficulty score 1-10")

class QuizOutput(BaseModel):
    """
    Structured output from quiz generation agent.
    Enforces presence of 'questions' key.
    """
    questions: List[Question]


class QuizRequest(BaseModel):
    """Request to generate a quiz for a concept."""
    document_id: str
    concept_id: str = Field(..., description="The concept to quiz on")
    difficulty: Literal["easy", "medium", "hard"] = Field(
        default="medium",
        description="Desired difficulty level"
    )


class QuizResponse(BaseModel):
    """Quiz containing exactly 10 questions, ranked by difficulty."""
    document_id: str
    concept_id: str
    difficulty: str
    questions: List[Question] = Field(..., min_length=10, max_length=10)
    validation_passed: bool
    validation_feedback: Optional[str] = None
    generated_at: datetime


# ====================================================
# INTERNAL DATABASE MODELS
# ====================================================

class DocumentDB(BaseModel):
    """Internal representation of a document in SQLite."""
    id: str
    user_id: str
    raw_text: str
    status: str
    concept_hierarchy: Optional[str] = None  # JSON string
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConceptDB(BaseModel):
    """Internal representation of a concept in SQLite."""
    id: str  # e.g., "C1"
    document_id: str
    name: str
    definition: str
    importance: float
    level: int
    prerequisites: str  # JSON array as string
    created_at: datetime

    class Config:
        from_attributes = True


# ====================================================
# VALIDATION MODELS
# ====================================================

class ValidationResult(BaseModel):
    """Result from difficulty validation."""
    passed: bool
    feedback: Optional[str] = None
    issues: List[str] = Field(default_factory=list)
