from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "ClarityCheck API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Database
    # Default to local SQLite, can be overridden by DATABASE_URL env var
    DATABASE_URL: str = "sqlite+aiosqlite:///./clarity.db"
    
    # Redis / Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Security / CORS
    # In production, this should be a comma-separated list of allowed domains
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
