"""
Custom Exceptions
Application-specific exception classes

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Custom exception handling for HeadStart application
"""

from fastapi import status

class HeadStartException(Exception):
    """Base exception for HeadStart application"""
    
    def __init__(self, message: str, error_code: str = "GENERIC_ERROR", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(HeadStartException):
    """Validation error exception"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class AuthenticationError(HeadStartException):
    """Authentication error exception"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationError(HeadStartException):
    """Authorization error exception"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN
        )

class NotFoundError(HeadStartException):
    """Not found error exception"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="NOT_FOUND_ERROR",
            status_code=status.HTTP_404_NOT_FOUND
        )

class ConflictError(HeadStartException):
    """Conflict error exception"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="CONFLICT_ERROR",
            status_code=status.HTTP_409_CONFLICT
        )

class RateLimitError(HeadStartException):
    """Rate limit error exception"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

class ExternalServiceError(HeadStartException):
    """External service error exception"""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY
        )
