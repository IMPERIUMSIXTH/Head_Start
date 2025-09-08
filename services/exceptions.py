"""
Custom Exception Classes
HeadStart application-specific exceptions

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Define custom exceptions for consistent error handling across the application
"""

class HeadStartException(Exception):
    """Base exception class for HeadStart application"""
    
    def __init__(self, message: str, error_code: str, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(HeadStartException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 400)

class AuthenticationError(HeadStartException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, "AUTH_ERROR", 401)

class AuthorizationError(HeadStartException):
    """Raised when user lacks required permissions"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHZ_ERROR", 403)

class NotFoundError(HeadStartException):
    """Raised when requested resource is not found"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "NOT_FOUND", 404)

class ConflictError(HeadStartException):
    """Raised when there's a conflict with existing data"""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, "CONFLICT", 409)

class RateLimitError(HeadStartException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT", 429)

class ExternalServiceError(HeadStartException):
    """Raised when external service call fails"""
    
    def __init__(self, message: str = "External service unavailable"):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", 502)

class ContentProcessingError(HeadStartException):
    """Raised when content processing fails"""
    
    def __init__(self, message: str = "Content processing failed"):
        super().__init__(message, "CONTENT_PROCESSING_ERROR", 422)

# Updated 2025-09-05: Custom exception classes for HeadStart application