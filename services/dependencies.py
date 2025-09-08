"""
FastAPI Dependencies
Authentication and authorization dependencies

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: FastAPI dependencies for authentication, authorization, and database access
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import structlog
from services.database import get_db
from services.auth import auth_service
from services.models import User
from services.exceptions import AuthenticationError, AuthorizationError

logger = structlog.get_logger()
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        user = auth_service.get_user_by_token(db, token)
        
        if user is None:
            raise AuthenticationError("Invalid authentication credentials")
        
        return user
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user"""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user

def require_role(required_role: str):
    """Dependency factory for role-based access control"""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role != required_role and current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker

def require_admin():
    """Dependency for admin-only access"""
    return require_role('admin')

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        user = auth_service.get_user_by_token(db, token)
        return user
    except Exception:
        return None

# Rate limiting dependency (placeholder for future implementation)
async def rate_limit_dependency():
    """Rate limiting dependency"""
    # TODO: Implement rate limiting logic
    pass

# Updated 2025-09-05: Authentication and authorization dependencies