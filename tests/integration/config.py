"""
Integration Test Configuration
Configuration settings and utilities for integration tests

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Centralized configuration for integration testing
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class IntegrationTestConfig:
    """Configuration for integration tests"""
    
    # Database configuration
    test_database_url: str = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql://test:test@localhost:5432/headstart_test"
    )
    
    # Test data configuration
    create_test_data: bool = True
    cleanup_after_tests: bool = True
    
    # Test execution configuration
    max_concurrent_tests: int = 5
    test_timeout_seconds: int = 300  # 5 minutes
    
    # API testing configuration
    api_base_url: str = "http://localhost:8000"
    api_timeout_seconds: int = 30
    
    # Authentication configuration
    test_jwt_secret: str = os.getenv("TEST_JWT_SECRET", "test-secret-key-for-integration-tests")
    test_password: str = "TestPassword123!"
    
    # Content testing configuration
    test_content_count: int = 10
    test_user_count: int = 5
    
    # Performance testing configuration
    performance_test_enabled: bool = os.getenv("ENABLE_PERFORMANCE_TESTS", "false").lower() == "true"
    max_query_time_seconds: float = 5.0
    max_api_response_time_seconds: float = 2.0
    
    # Logging configuration
    log_level: str = os.getenv("TEST_LOG_LEVEL", "INFO")
    log_to_file: bool = False
    log_file_path: str = "tests/logs/integration_tests.log"
    
    # Error handling configuration
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    
    # Feature flags for optional tests
    test_oauth: bool = os.getenv("TEST_OAUTH", "false").lower() == "true"
    test_external_apis: bool = os.getenv("TEST_EXTERNAL_APIS", "false").lower() == "true"
    test_celery_tasks: bool = os.getenv("TEST_CELERY_TASKS", "false").lower() == "true"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "test_database_url": self.test_database_url,
            "create_test_data": self.create_test_data,
            "cleanup_after_tests": self.cleanup_after_tests,
            "max_concurrent_tests": self.max_concurrent_tests,
            "test_timeout_seconds": self.test_timeout_seconds,
            "api_base_url": self.api_base_url,
            "api_timeout_seconds": self.api_timeout_seconds,
            "test_jwt_secret": self.test_jwt_secret,
            "test_content_count": self.test_content_count,
            "test_user_count": self.test_user_count,
            "performance_test_enabled": self.performance_test_enabled,
            "max_query_time_seconds": self.max_query_time_seconds,
            "max_api_response_time_seconds": self.max_api_response_time_seconds,
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
            "log_file_path": self.log_file_path,
            "max_retry_attempts": self.max_retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
            "test_oauth": self.test_oauth,
            "test_external_apis": self.test_external_apis,
            "test_celery_tasks": self.test_celery_tasks
        }

# Global configuration instance
integration_config = IntegrationTestConfig()

def get_integration_config() -> IntegrationTestConfig:
    """Get integration test configuration"""
    return integration_config

def update_config(**kwargs) -> None:
    """Update configuration values"""
    global integration_config
    for key, value in kwargs.items():
        if hasattr(integration_config, key):
            setattr(integration_config, key, value)

# Environment-specific configurations
def get_ci_config() -> IntegrationTestConfig:
    """Get configuration for CI environment"""
    config = IntegrationTestConfig()
    config.test_database_url = os.getenv("CI_DATABASE_URL", config.test_database_url)
    config.test_timeout_seconds = 600  # 10 minutes for CI
    config.performance_test_enabled = False  # Disable performance tests in CI
    config.log_level = "WARNING"  # Reduce logging in CI
    config.max_retry_attempts = 5  # More retries in CI
    return config

def get_local_config() -> IntegrationTestConfig:
    """Get configuration for local development"""
    config = IntegrationTestConfig()
    config.performance_test_enabled = True
    config.log_level = "DEBUG"
    config.log_to_file = True
    return config

def get_docker_config() -> IntegrationTestConfig:
    """Get configuration for Docker environment"""
    config = IntegrationTestConfig()
    config.test_database_url = "postgresql://postgres:postgres@db:5432/headstart_test"
    config.api_base_url = "http://web:8000"
    return config

# Test data templates
TEST_USER_TEMPLATES = [
    {
        "email": "active_user@test.com",
        "full_name": "Active Test User",
        "role": "learner",
        "is_active": True,
        "email_verified": True
    },
    {
        "email": "admin_user@test.com",
        "full_name": "Admin Test User",
        "role": "admin",
        "is_active": True,
        "email_verified": True
    },
    {
        "email": "inactive_user@test.com",
        "full_name": "Inactive Test User",
        "role": "learner",
        "is_active": False,
        "email_verified": True
    },
    {
        "email": "unverified_user@test.com",
        "full_name": "Unverified Test User",
        "role": "learner",
        "is_active": True,
        "email_verified": False
    }
]

TEST_CONTENT_TEMPLATES = [
    {
        "title": "Introduction to Machine Learning",
        "description": "Basic ML concepts and algorithms",
        "content_type": "video",
        "source": "youtube",
        "difficulty_level": "beginner",
        "topics": ["AI", "Machine Learning"],
        "status": "approved"
    },
    {
        "title": "Advanced Python Programming",
        "description": "Advanced Python concepts and patterns",
        "content_type": "article",
        "source": "upload",
        "difficulty_level": "advanced",
        "topics": ["Programming", "Python"],
        "status": "approved"
    },
    {
        "title": "Web Development with React",
        "description": "Building modern web applications",
        "content_type": "course",
        "source": "upload",
        "difficulty_level": "intermediate",
        "topics": ["Web Development", "React"],
        "status": "approved"
    },
    {
        "title": "Data Science Fundamentals",
        "description": "Introduction to data science concepts",
        "content_type": "article",
        "source": "upload",
        "difficulty_level": "beginner",
        "topics": ["Data Science", "Statistics"],
        "status": "approved"
    }
]

# Test validation functions
def validate_database_connection(database_url: str) -> bool:
    """Validate database connection string"""
    try:
        from sqlalchemy import create_engine
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False

def validate_api_endpoint(api_url: str) -> bool:
    """Validate API endpoint availability"""
    try:
        import requests
        response = requests.get(f"{api_url}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

# Configuration validation
def validate_config(config: IntegrationTestConfig) -> Dict[str, bool]:
    """Validate integration test configuration"""
    validation_results = {
        "database_connection": validate_database_connection(config.test_database_url),
        "api_endpoint": validate_api_endpoint(config.api_base_url),
        "test_data_templates": len(TEST_USER_TEMPLATES) > 0 and len(TEST_CONTENT_TEMPLATES) > 0,
        "environment_variables": bool(config.test_jwt_secret),
    }
    
    return validation_results