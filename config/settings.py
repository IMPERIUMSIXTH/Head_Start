"""
HeadStart Application Settings
Configuration management using Pydantic Settings

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Centralized configuration management with environment variable support
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Configuration
    APP_NAME: str = Field(default="HeadStart", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="production", description="Environment name")
    
    # Database Configuration
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    DATABASE_TEST_URL: Optional[str] = Field(default=None, description="Test database URL")
    
    # Redis Configuration
    REDIS_URL: str = Field(..., description="Redis connection URL")
    
    # JWT Configuration
    JWT_SECRET: str = Field(..., description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiry in minutes")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry in days")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    
    # External APIs
    YOUTUBE_API_KEY: Optional[str] = Field(default=None, description="YouTube API key")
    ARXIV_API_BASE_URL: str = Field(default="http://export.arxiv.org/api/query", description="arXiv API base URL")
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, description="Google OAuth client secret")
    GITHUB_CLIENT_ID: Optional[str] = Field(default=None, description="GitHub OAuth client ID")
    GITHUB_CLIENT_SECRET: Optional[str] = Field(default=None, description="GitHub OAuth client secret")
    
    # Security Configuration
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"], description="Allowed CORS origins")
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"], description="Allowed hosts")
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE: str = Field(default="50MB", description="Maximum file upload size")
    UPLOAD_PATH: str = Field(default="./uploads", description="File upload directory")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = Field(..., description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(..., description="Celery result backend URL")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format")
    
    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('ALLOWED_HOSTS', pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
    
    @validator('MAX_UPLOAD_SIZE')
    def validate_upload_size(cls, v):
        """Validate upload size format"""
        if not v.upper().endswith(('B', 'KB', 'MB', 'GB')):
            raise ValueError('Upload size must end with B, KB, MB, or GB')
        return v
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment name"""
        valid_environments = ['development', 'staging', 'production', 'testing']
        if v.lower() not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v.lower()
    
    def get_upload_size_bytes(self) -> int:
        """Convert upload size string to bytes"""
        size_str = self.MAX_UPLOAD_SIZE.upper()
        
        if size_str.endswith('B'):
            return int(size_str[:-1])
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        
        return int(size_str)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Updated 2025-09-05: Application settings with comprehensive configuration management