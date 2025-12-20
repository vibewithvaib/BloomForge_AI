"""
Configuration management for the backend.
All environment variables and constants are defined here.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # Database Configuration
    database_path: str = "./data/app.db"
    chroma_persist_dir: str = "./data/chromadb"
    
    # Application Configuration
    app_name: str = "Autonomous Knowledge Extractor"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Agent Configuration
    max_retries: int = 3
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
