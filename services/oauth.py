"""
OAuth2 PKCE Integration Service
Social login integration with Google and GitHub

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Handle OAuth2 PKCE flows for social authentication
"""

import httpx
import secrets
import hashlib
import base64
from typing import Dict, Any, Optional
from urllib.parse import urlencode, parse_qs, urlparse
import structlog
from sqlalchemy.orm import Session
from services.models import User
from services.auth import auth_service
from services.exceptions import AuthenticationError, ValidationError
from config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()

class OAuth2PKCEService:
    """OAuth2 PKCE service for social login"""
    
    def __init__(self):
        self.google_client_id = settings.GOOGLE_CLIENT_ID
        self.google_client_secret = settings.GOOGLE_CLIENT_SECRET
        self.github_client_id = settings.GITHUB_CLIENT_ID
        self.github_client_secret = settings.GITHUB_CLIENT_SECRET
        
        # OAuth endpoints
        self.google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.google_token_url = "https://oauth2.googleapis.com/token"
        self.google_userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        self.github_auth_url = "https://github.com/login/oauth/authorize"
        self.github_token_url = "https://github.com/login/oauth/access_token"
        self.github_userinfo_url = "https://api.github.com/user"
    
    def generate_pkce_pair(self) -> Dict[str, str]:
        """Generate PKCE code verifier and challenge"""
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return {
            "code_verifier": code_verifier,
            "code_challenge": code_challenge
        }
    
    def get_google_auth_url(self, redirect_uri: str, state: str, code_challenge: str) -> str:
        """Generate Google OAuth2 authorization URL"""
        if not self.google_client_id:
            raise ValidationError("Google OAuth not configured")
        
        params = {
            "client_id": self.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        return f"{self.google_auth_url}?{urlencode(params)}"
    
    def get_github_auth_url(self, redirect_uri: str, state: str) -> str:
        """Generate GitHub OAuth2 authorization URL"""
        if not self.github_client_id:
            raise ValidationError("GitHub OAuth not configured")
        
        params = {
            "client_id": self.github_client_id,
            "redirect_uri": redirect_uri,
            "scope": "user:email",
            "state": state
        }
        
        return f"{self.github_auth_url}?{urlencode(params)}"
    
    async def exchange_google_code(
        self, 
        code: str, 
        redirect_uri: str, 
        code_verifier: str
    ) -> Dict[str, Any]:
        """Exchange Google authorization code for access token"""
        if not self.google_client_id or not self.google_client_secret:
            raise ValidationError("Google OAuth not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                # Exchange code for tokens
                token_data = {
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                    "code_verifier": code_verifier
                }
                
                token_response = await client.post(
                    self.google_token_url,
                    data=token_data,
                    headers={"Accept": "application/json"}
                )
                token_response.raise_for_status()
                tokens = token_response.json()
                
                if "error" in tokens:
                    raise AuthenticationError(f"Google OAuth error: {tokens['error']}")
                
                # Get user info
                access_token = tokens["access_token"]
                userinfo_response = await client.get(
                    self.google_userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                userinfo_response.raise_for_status()
                user_info = userinfo_response.json()
                
                return {
                    "provider": "google",
                    "provider_id": user_info["id"],
                    "email": user_info["email"],
                    "full_name": user_info["name"],
                    "verified_email": user_info.get("verified_email", False),
                    "picture": user_info.get("picture"),
                    "tokens": tokens
                }
                
        except httpx.HTTPError as e:
            logger.error("Google OAuth token exchange failed", error=str(e))
            raise AuthenticationError("Failed to authenticate with Google")
        except Exception as e:
            logger.error("Google OAuth error", error=str(e))
            raise AuthenticationError("Google authentication failed")
    
    async def exchange_github_code(
        self, 
        code: str, 
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange GitHub authorization code for access token"""
        if not self.github_client_id or not self.github_client_secret:
            raise ValidationError("GitHub OAuth not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                # Exchange code for tokens
                token_data = {
                    "client_id": self.github_client_id,
                    "client_secret": self.github_client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri
                }
                
                token_response = await client.post(
                    self.github_token_url,
                    data=token_data,
                    headers={"Accept": "application/json"}
                )
                token_response.raise_for_status()
                tokens = token_response.json()
                
                if "error" in tokens:
                    raise AuthenticationError(f"GitHub OAuth error: {tokens['error']}")
                
                # Get user info
                access_token = tokens["access_token"]
                userinfo_response = await client.get(
                    self.github_userinfo_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                userinfo_response.raise_for_status()
                user_info = userinfo_response.json()
                
                # Get user email (GitHub may not return email in user info)
                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                email_response.raise_for_status()
                emails = email_response.json()
                
                # Find primary verified email
                primary_email = None
                for email_data in emails:
                    if email_data.get("primary") and email_data.get("verified"):
                        primary_email = email_data["email"]
                        break
                
                if not primary_email:
                    raise AuthenticationError("No verified email found in GitHub account")
                
                return {
                    "provider": "github",
                    "provider_id": str(user_info["id"]),
                    "email": primary_email,
                    "full_name": user_info.get("name") or user_info["login"],
                    "verified_email": True,
                    "picture": user_info.get("avatar_url"),
                    "tokens": tokens
                }
                
        except httpx.HTTPError as e:
            logger.error("GitHub OAuth token exchange failed", error=str(e))
            raise AuthenticationError("Failed to authenticate with GitHub")
        except Exception as e:
            logger.error("GitHub OAuth error", error=str(e))
            raise AuthenticationError("GitHub authentication failed")
    
    async def create_or_get_oauth_user(
        self, 
        db: Session, 
        oauth_data: Dict[str, Any]
    ) -> User:
        """Create or get user from OAuth data"""
        try:
            email = oauth_data["email"]
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            
            if existing_user:
                # Update user info if needed
                if not existing_user.email_verified and oauth_data.get("verified_email"):
                    existing_user.email_verified = True
                    db.commit()
                
                logger.info("OAuth user login", 
                           email=email, 
                           provider=oauth_data["provider"],
                           user_id=str(existing_user.id))
                return existing_user
            
            # Create new user
            new_user = User(
                email=email,
                password_hash=None,  # OAuth users don't have passwords
                full_name=oauth_data["full_name"],
                role="learner",
                is_active=True,
                email_verified=oauth_data.get("verified_email", False)
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info("OAuth user created", 
                       email=email, 
                       provider=oauth_data["provider"],
                       user_id=str(new_user.id))
            
            return new_user
            
        except Exception as e:
            logger.error("OAuth user creation failed", error=str(e))
            raise AuthenticationError("Failed to create OAuth user")

# Global OAuth service instance
oauth_service = OAuth2PKCEService()

# Updated 2025-09-05: OAuth2 PKCE service for social authentication