"""
Application Settings
Configuration management using Pydantic settings

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Centralized application configuration
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./headstart.db"
    DATABASE_TEST_URL: str = "sqlite:///./headstart_test.db"

    # External APIs
    ARXIV_API_BASE_URL: str = "http://export.arxiv.org/api/query"

    # Application Configuration
    APP_NAME: str = "HeadStart"
    APP_VERSION: str = "1.0.0"

    # File Upload
    MAX_UPLOAD_SIZE: str = "50MB"
    UPLOAD_PATH: str = "./uploads"

    # Logging
    LOG_FORMAT: str = "json"
    
    # JWT Configuration
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # OAuth (optional)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    
    # External APIs (optional)
    OPENAI_API_KEY: Optional[str] = None
    GPT_API_KEY: Optional[str] = "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"
    YOUTUBE_API_KEY: Optional[str] = None

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Frontend URL
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"

    # Encryption
    ENCRYPTION_KEY: str = "default-encryption-key-change-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get application settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reset_settings():
    """Reset the settings cache"""
    global _settings
    _settings = None