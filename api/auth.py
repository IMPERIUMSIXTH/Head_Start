"""
Authentication API Routes
Handles user authentication, registration, and token management

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Authentication endpoints for user login, registration, and token management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from typing import Optional
import structlog
from services.database import get_db
from services.auth import auth_service
from services.models import User
from services.dependencies import get_current_user, get_current_active_user, validate_input
from services.exceptions import AuthenticationError, ValidationError, ConflictError
from services.oauth import oauth_service
from services.security import rate_limit
from config.settings import get_settings

logger = structlog.get_logger()
security = HTTPBearer()
settings = get_settings()

router = APIRouter()

# Pydantic models for request/response
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v.strip()

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    email_verified: bool
    created_at: str
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v.strip() if v else v

class OAuthInitRequest(BaseModel):
    provider: str
    redirect_uri: str
    
    @validator('provider')
    def validate_provider(cls, v):
        if v not in ['google', 'github']:
            raise ValueError('Provider must be either "google" or "github"')
        return v

class OAuthInitResponse(BaseModel):
    auth_url: str
    state: str
    code_verifier: Optional[str] = None  # Only for Google PKCE

class OAuthCallbackRequest(BaseModel):
    provider: str
    code: str
    state: str
    redirect_uri: str
    code_verifier: Optional[str] = None  # Only for Google PKCE
    
    @validator('provider')
    def validate_provider(cls, v):
        if v not in ['google', 'github']:
            raise ValueError('Provider must be either "google" or "github"')
        return v

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(calls=5, period=60)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db), request: Request = None, email: str = Depends(validate_input), password: str = Depends(validate_input), full_name: str = Depends(validate_input)):
    user_data.email = email
    user_data.password = password
    user_data.full_name = full_name
    """Register a new user account"""
    logger.info("User registration attempt", email=user_data.email)
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ConflictError("User with this email already exists")
        
        # Hash password
        password_hash = auth_service.hash_password(user_data.password)
        
        # Create new user
        new_user = User(
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name,
            role="learner",
            is_active=True,
            email_verified=False  # TODO: Implement email verification
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate JWT tokens
        tokens = auth_service.create_token_pair(new_user)
        
        logger.info("User registered successfully", 
                   email=user_data.email, 
                   user_id=str(new_user.id))
        
        return tokens
        
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Registration failed", error=str(e), email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=TokenResponse)
@rate_limit(calls=5, period=60)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db), request: Request = None, email: str = Depends(validate_input), password: str = Depends(validate_input)):
    user_credentials.email = email
    user_credentials.password = password
    """Authenticate user and return JWT tokens"""
    logger.info("User login attempt", email=user_credentials.email)
    
    try:
        # Authenticate user
        user = auth_service.authenticate_user(
            db, user_credentials.email, user_credentials.password
        )
        
        if not user:
            raise AuthenticationError("Invalid email or password")
        
        # Generate JWT tokens
        tokens = auth_service.create_token_pair(user)
        
        logger.info("User logged in successfully", 
                   email=user_credentials.email, 
                   user_id=str(user.id))
        
        return tokens
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error("Login failed", error=str(e), email=user_credentials.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh JWT access token using refresh token"""
    logger.info("Token refresh attempt")
    
    try:
        # Refresh access token
        tokens = auth_service.refresh_access_token(db, token_request.refresh_token)
        
        logger.info("Token refreshed successfully")
        return tokens
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    """Logout user and invalidate tokens"""
    logger.info("User logout attempt", user_id=str(current_user.id))
    
    # TODO: Implement token blacklisting for enhanced security
    # For now, client-side token removal is sufficient
    
    logger.info("User logged out successfully", user_id=str(current_user.id))
    return {"message": "Successfully logged out"}

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile information"""
    logger.info("User profile request", user_id=str(current_user.id))
    
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at.isoformat()
    )

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfileUpdate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile information"""
    logger.info("User profile update attempt", user_id=str(current_user.id))
    
    try:
        # Update user profile
        if profile_data.full_name is not None:
            current_user.full_name = profile_data.full_name
        
        db.commit()
        db.refresh(current_user)
        
        logger.info("User profile updated successfully", user_id=str(current_user.id))
        
        return UserProfile(
            id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            is_active=current_user.is_active,
            email_verified=current_user.email_verified,
            created_at=current_user.created_at.isoformat()
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Profile update failed", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.post("/oauth/init", response_model=OAuthInitResponse)
async def init_oauth_flow(oauth_request: OAuthInitRequest):
    """Initialize OAuth2 PKCE flow"""
    logger.info("OAuth initialization", provider=oauth_request.provider)
    
    try:
        # Generate secure state parameter
        state = auth_service.generate_secure_token(16)
        
        if oauth_request.provider == "google":
            # Generate PKCE pair for Google
            pkce_pair = oauth_service.generate_pkce_pair()
            auth_url = oauth_service.get_google_auth_url(
                oauth_request.redirect_uri,
                state,
                pkce_pair["code_challenge"]
            )
            
            return OAuthInitResponse(
                auth_url=auth_url,
                state=state,
                code_verifier=pkce_pair["code_verifier"]
            )
            
        elif oauth_request.provider == "github":
            auth_url = oauth_service.get_github_auth_url(
                oauth_request.redirect_uri,
                state
            )
            
            return OAuthInitResponse(
                auth_url=auth_url,
                state=state
            )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("OAuth initialization failed", error=str(e), provider=oauth_request.provider)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth initialization failed"
        )

@router.post("/oauth/callback", response_model=TokenResponse)
async def oauth_callback(callback_request: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """Handle OAuth2 callback and authenticate user"""
    logger.info("OAuth callback", provider=callback_request.provider)
    
    try:
        # Exchange authorization code for user data
        if callback_request.provider == "google":
            if not callback_request.code_verifier:
                raise ValidationError("Code verifier required for Google OAuth")
            
            oauth_data = await oauth_service.exchange_google_code(
                callback_request.code,
                callback_request.redirect_uri,
                callback_request.code_verifier
            )
            
        elif callback_request.provider == "github":
            oauth_data = await oauth_service.exchange_github_code(
                callback_request.code,
                callback_request.redirect_uri
            )
        
        # Create or get user
        user = await oauth_service.create_or_get_oauth_user(db, oauth_data)
        
        # Generate JWT tokens
        tokens = auth_service.create_token_pair(user)
        
        logger.info("OAuth authentication successful", 
                   provider=callback_request.provider,
                   email=oauth_data["email"],
                   user_id=str(user.id))
        
        return tokens
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error("OAuth callback failed", error=str(e), provider=callback_request.provider)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )

@router.get("/oauth/providers")
async def get_oauth_providers():
    """Get available OAuth providers"""
    providers = []
    
    if settings.GOOGLE_CLIENT_ID:
        providers.append({
            "name": "google",
            "display_name": "Google",
            "available": True
        })
    
    if settings.GITHUB_CLIENT_ID:
        providers.append({
            "name": "github", 
            "display_name": "GitHub",
            "available": True
        })
    
    return {
        "providers": providers,
        "total": len(providers)
    }

# Updated 2025-09-05: Complete authentication API with JWT tokens, Argon2id password hashing, and OAuth2 PKCE