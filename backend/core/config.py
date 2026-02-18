from pydantic_settings import BaseSettings
from typing import List, Union, Optional
from pydantic import field_validator

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
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    # LLM-Powered Detection
    LLM_DETECTOR_ENABLED: bool = False
    GEMINI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-2.0-flash-exp"
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Auth
    SECRET_KEY: str = "changethis"  # TODO: Generate a strong key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
             return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
