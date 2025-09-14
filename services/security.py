"""
Security Middleware and Utilities
Security headers, rate limiting, and input validation

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Security middleware and utilities for FastAPI application
"""

import time
from typing import Dict, Any
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

import time
from typing import Dict, Any, Callable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import redis
from functools import wraps

from services.dependencies import get_redis_client

logger = structlog.get_logger()

def rate_limit(calls: int, period: int):
    """
    Decorator to apply rate limiting to an endpoint.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                raise Exception("Request object not found in endpoint arguments")

            redis_client = get_redis_client()
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}:{request.url.path}"

            now = time.time()
            
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - period)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, period)
            results = pipe.execute()

            call_count = results[2]

            if call_count > calls:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            return await func(*args, **kwargs)
        return wrapper
    return decorator

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""

    def __init__(self, app, calls: int = 100, period: int = 60, redis_client: redis.Redis = None):
        super().__init__(app)
        self.calls = calls
        self.period = period
        try:
            self.redis_client = redis_client or get_redis_client()
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
        except Exception as e:
            logger.warning("Redis not available, rate limiting disabled", error=str(e))
            self.redis_available = False

    async def dispatch(self, request: Request, call_next: Callable):
        if not self.redis_available:
            # Skip rate limiting if Redis is not available
            response = await call_next(request)
            return response

        client_ip = request.client.host
        key = f"rate_limit:{client_ip}:global"
        now = time.time()

        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.period)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.period)
            results = pipe.execute()

            call_count = results[2]

            if call_count > self.calls:
                logger.warning(f"Global rate limit exceeded for {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={"error": "Global rate limit exceeded"}
                )
        except Exception as e:
            logger.warning("Rate limiting failed, allowing request", error=str(e))

        response = await call_next(request)
        return response


class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        # Truncate to max length
        return sanitized[:max_length].strip()
    
    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """Check if filename is safe"""
        if not filename or len(filename) > 255:
            return False

        # Check for dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        return not any(char in filename for char in dangerous_chars)

    import bleach

    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email input using bleach"""
        if not isinstance(email, str):
            return ""

        # Use bleach to clean the email string
        sanitized = bleach.clean(email, tags=[], strip=True)

        # Basic email normalization
        return sanitized.strip().lower()

    @staticmethod
    def validate_url(url: str, allowed_schemes: list = None) -> bool:
        """Validate URL format and scheme"""
        if not isinstance(url, str) or not url:
            return False

        import re
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url):
            return False

        if allowed_schemes:
            scheme = url.split('://')[0]
            if scheme not in allowed_schemes:
                return False

        return True

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, bool]:
        """Validate password strength"""
        checks = {
            "min_length": len(password) >= 8,
            "has_upper": any(c.isupper() for c in password),
            "has_lower": any(c.islower() for c in password),
            "has_digit": any(c.isdigit() for c in password),
            "has_special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        }
        
        return checks
    
    @staticmethod
    def is_strong_password(password: str) -> bool:
        """Check if password meets strength requirements"""
        checks = SecurityValidator.validate_password_strength(password)
        return all(checks.values())

    @staticmethod
    def detect_sql_injection(input_str: str) -> bool:
        """Detect potential SQL injection attempts"""
        import re
        sql_patterns = [
            r';\s*DROP\s+TABLE',
            r';\s*DELETE\s+FROM',
            r';\s*UPDATE\s+.*SET',
            r';\s*INSERT\s+INTO',
            r'UNION\s+SELECT',
            r'OR\s+\d+\s*=\s*\d+',
            r'--',
            r'/\*.*\*/'
        ]
        for pattern in sql_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def detect_xss_attempt(input_str: str) -> bool:
        """Detect potential XSS attempts"""
        import re
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>'
        ]
        for pattern in xss_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        return False
