"""
Authentication Services
JWT token management, password hashing, and OAuth integration

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Handle user authentication, token generation, and password security
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import argon2
import secrets
import structlog
from sqlalchemy.orm import Session
from services.models import User
from services.exceptions import AuthenticationError, ValidationError
from config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Password hashing context with Argon2id
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,        # 3 iterations
    argon2__parallelism=1,      # 1 thread
)

class AuthService:
    """Authentication service class"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def hash_password(self, password: str) -> str:
        """Hash password using Argon2id"""
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error("Password verification failed", error=str(e))
            return False
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error("Failed to create access token", error=str(e))
            raise AuthenticationError("Failed to create access token")
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error("Failed to create refresh token", error=str(e))
            raise AuthenticationError("Failed to create refresh token")
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise AuthenticationError("Invalid token type")
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcfromtimestamp(exp) < datetime.utcnow():
                raise AuthenticationError("Token has expired")
            
            return payload
            
        except JWTError as e:
            logger.error("JWT verification failed", error=str(e))
            raise AuthenticationError("Invalid token")
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                logger.warning("Authentication failed - user not found", email=email)
                return None
            
            if not user.is_active:
                logger.warning("Authentication failed - user inactive", email=email)
                return None
            
            if not user.password_hash:
                logger.warning("Authentication failed - no password set", email=email)
                return None
            
            if not self.verify_password(password, user.password_hash):
                logger.warning("Authentication failed - invalid password", email=email)
                return None
            
            logger.info("User authenticated successfully", email=email, user_id=str(user.id))
            return user
            
        except Exception as e:
            logger.error("Authentication error", error=str(e), email=email)
            return None
    
    def get_user_by_token(self, db: Session, token: str) -> Optional[User]:
        """Get user from JWT token"""
        try:
            payload = self.verify_token(token)
            user_id = payload.get("sub")
            
            if user_id is None:
                return None
            
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                return None
            
            return user
            
        except AuthenticationError:
            return None
    
    def create_token_pair(self, user: User) -> Dict[str, Any]:
        """Create access and refresh token pair"""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }
    
    def refresh_access_token(self, db: Session, refresh_token: str) -> Dict[str, Any]:
        """Create new access token from refresh token"""
        try:
            payload = self.verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")
            
            if user_id is None:
                raise AuthenticationError("Invalid refresh token")
            
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            return self.create_token_pair(user)
            
        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            raise AuthenticationError("Failed to refresh token")
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)

# Global auth service instance
auth_service = AuthService()

# Updated 2025-09-05: Comprehensive authentication service with JWT and Argon2id