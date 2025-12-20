"""
Main FastAPI Application

This is the entry point for the Autonomous Knowledge Extractor backend.

Architecture:
- Two AI agents (concept extraction, adaptive tutoring)
- Rule-based validation
- Strict user/document isolation
- Vector + structured storage

Run with: uvicorn main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from db.database import Database
from vectorstore.chroma_client import VectorStore
from routes import document, explain, quiz


# ====================================================
# LIFECYCLE MANAGEMENT
# ====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Startup:
    - Initialize database schema
    - Initialize vector store
    
    Shutdown:
    - Clean up resources
    """
    # Startup
    print("🚀 Starting Autonomous Knowledge Extractor Backend...")
    
    # Initialize database
    db = Database(settings.database_path)
    print(f"✅ Database initialized at {settings.database_path}")
    
    # Initialize vector store
    vector_store = VectorStore(settings.chroma_persist_dir)
    print(f"✅ Vector store initialized at {settings.chroma_persist_dir}")
    
    print("✅ All systems ready!")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# ====================================================
# APPLICATION SETUP
# ====================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Autonomous Knowledge Extractor API
    
    Upload educational texts and get:
    - Structured concept hierarchies
    - Adaptive explanations
    - Difficulty-validated quizzes
    
    Built with:
    - FastAPI + Python
    - OpenAI GPT-4o-mini
    - LangGraph orchestration
    - ChromaDB vectors
    - SQLite storage
    """,
    lifespan=lifespan,
    debug=settings.debug
)


# ====================================================
# MIDDLEWARE
# ====================================================

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================================================
# ROUTES
# ====================================================

# Include all routers
app.include_router(document.router)
app.include_router(explain.router)
app.include_router(quiz.router)


# ====================================================
# ROOT ENDPOINTS
# ====================================================

@app.get("/")
async def root():
    """API health check and info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "documents": "/api/document",
            "explanations": "/api/explain",
            "quizzes": "/api/quiz"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": settings.database_path,
        "vector_store": settings.chroma_persist_dir,
        "model": settings.openai_model
    }


# ====================================================
# MAIN ENTRY POINT
# ====================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
