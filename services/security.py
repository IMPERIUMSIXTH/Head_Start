"""
Security Middleware and Utilities
Security headers, rate limiting, and input validation

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Security middleware for FastAPI application
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import time
import hashlib
import re
from typing import Dict, Any, Optional
import structlog
from collections import defaultdict, deque
from datetime import datetime, timedelta
import ipaddress

logger = structlog.get_logger()

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://apis.google.com https://github.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://api.openai.com https://www.googleapis.com https://api.github.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # HSTS (only in production with HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(deque)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get real IP from headers (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host
        
        # Add user ID if authenticated
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token_hash = hashlib.sha256(auth_header.encode()).hexdigest()[:16]
            return f"{client_ip}:{token_hash}"
        
        return client_ip
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_id = self._get_client_id(request)
        now = time.time()
        
        # Clean old entries
        client_requests = self.clients[client_id]
        while client_requests and client_requests[0] <= now - self.period:
            client_requests.popleft()
        
        # Check rate limit
        if len(client_requests) >= self.calls:
            logger.warning("Rate limit exceeded", client_id=client_id, requests=len(client_requests))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(self.period)}
            )
        
        # Add current request
        client_requests.append(now)
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.calls - len(client_requests))
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(now + self.period))
        
        return response

class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # Limit length
        sanitized = sanitized[:max_length]
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email input"""
        if not isinstance(email, str):
            return ""
        
        # Basic email sanitization
        email = email.lower().strip()
        
        # Remove dangerous characters
        email = re.sub(r'[<>"\']', '', email)
        
        return email
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Sanitize search query input"""
        if not isinstance(query, str):
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\'\x00-\x1F\x7F]', '', query)
        
        # Limit length
        sanitized = sanitized[:200]
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def validate_url(url: str, allowed_schemes: list = None) -> bool:
        """Validate URL format and scheme"""
        if not isinstance(url, str):
            return False
        
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            return False
        
        # Check scheme
        scheme = url.split('://')[0].lower()
        return scheme in allowed_schemes
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        result = {
            "valid": True,
            "score": 0,
            "issues": []
        }
        
        if len(password) < 8:
            result["issues"].append("Password must be at least 8 characters long")
            result["valid"] = False
        else:
            result["score"] += 1
        
        if len(password) >= 12:
            result["score"] += 1
        
        if not re.search(r'[a-z]', password):
            result["issues"].append("Password must contain at least one lowercase letter")
            result["valid"] = False
        else:
            result["score"] += 1
        
        if not re.search(r'[A-Z]', password):
            result["issues"].append("Password must contain at least one uppercase letter")
            result["valid"] = False
        else:
            result["score"] += 1
        
        if not re.search(r'\d', password):
            result["issues"].append("Password must contain at least one digit")
            result["valid"] = False
        else:
            result["score"] += 1
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result["issues"].append("Password should contain at least one special character")
        else:
            result["score"] += 1
        
        # Check for common patterns
        common_patterns = [
            r'123456',
            r'password',
            r'qwerty',
            r'abc123',
            r'admin'
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                result["issues"].append("Password contains common patterns")
                result["score"] = max(0, result["score"] - 2)
                break
        
        return result
    
    @staticmethod
    def detect_sql_injection(input_string: str) -> bool:
        """Detect potential SQL injection attempts"""
        if not isinstance(input_string, str):
            return False
        
        # Common SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            r"(--|#|/\*|\*/)",
            r"(\bxp_cmdshell\b)",
            r"(\bsp_executesql\b)"
        ]
        
        input_lower = input_string.lower()
        
        for pattern in sql_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE):
                logger.warning("Potential SQL injection detected", input=input_string[:100])
                return True
        
        return False
    
    @staticmethod
    def detect_xss_attempt(input_string: str) -> bool:
        """Detect potential XSS attempts"""
        if not isinstance(input_string, str):
            return False
        
        # Common XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"vbscript:",
            r"data:text/html"
        ]
        
        input_lower = input_string.lower()
        
        for pattern in xss_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE):
                logger.warning("Potential XSS attempt detected", input=input_string[:100])
                return True
        
        return False

# Global instances
input_sanitizer = InputSanitizer()
security_validator = SecurityValidator()

# Updated 2025-09-05: Comprehensive security middleware and utilities