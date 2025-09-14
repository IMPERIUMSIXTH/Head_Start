"""
Authentication System Tests
Test authentication, authorization, and security features

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Test authentication system components
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.auth import AuthService
from services.oauth import OAuth2PKCEService
from services.security import SecurityValidator, InputSanitizer
from services.models import User, Base
from services.exceptions import AuthenticationError, ValidationError

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_service():
    """Create auth service instance for testing"""
    return AuthService()

@pytest.fixture
def oauth_service():
    """Create OAuth service instance for testing"""
    return OAuth2PKCEService()

@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }

class TestAuthService:
    """Test authentication service"""
    
    def test_hash_password(self, auth_service):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # Argon2 hashes are long
        assert hashed.startswith("$argon2id$")
    
    def test_hash_password_too_short(self, auth_service):
        """Test password hashing with short password"""
        with pytest.raises(ValidationError, match="at least 8 characters"):
            auth_service.hash_password("short")
    
    def test_verify_password_correct(self, auth_service):
        """Test password verification with correct password"""
        password = "TestPassword123!"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self, auth_service):
        """Test password verification with incorrect password"""
        password = "TestPassword123!"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password("WrongPassword", hashed) is False
    
    def test_create_access_token(self, auth_service):
        """Test access token creation"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = auth_service.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_create_refresh_token(self, auth_service):
        """Test refresh token creation"""
        data = {"sub": "user123"}
        token = auth_service.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_token_valid(self, auth_service):
        """Test token verification with valid token"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = auth_service.create_access_token(data)
        
        payload = auth_service.verify_token(token, "access")
        
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_verify_token_invalid_type(self, auth_service):
        """Test token verification with wrong token type"""
        data = {"sub": "user123"}
        token = auth_service.create_access_token(data)
        
        with pytest.raises(AuthenticationError, match="Invalid token type"):
            auth_service.verify_token(token, "refresh")
    
    def test_verify_token_invalid(self, auth_service):
        """Test token verification with invalid token"""
        with pytest.raises(AuthenticationError, match="Invalid token"):
            auth_service.verify_token("invalid.token.here", "access")
    
    def test_authenticate_user_success(self, auth_service, db_session, test_user_data):
        """Test successful user authentication"""
        # Create test user
        password_hash = auth_service.hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            password_hash=password_hash,
            full_name=test_user_data["full_name"],
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Authenticate
        authenticated_user = auth_service.authenticate_user(
            db_session, test_user_data["email"], test_user_data["password"]
        )
        
        assert authenticated_user is not None
        assert authenticated_user.email == test_user_data["email"]
    
    def test_authenticate_user_wrong_password(self, auth_service, db_session, test_user_data):
        """Test authentication with wrong password"""
        # Create test user
        password_hash = auth_service.hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            password_hash=password_hash,
            full_name=test_user_data["full_name"],
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Authenticate with wrong password
        authenticated_user = auth_service.authenticate_user(
            db_session, test_user_data["email"], "WrongPassword"
        )
        
        assert authenticated_user is None
    
    def test_authenticate_user_not_found(self, auth_service, db_session):
        """Test authentication with non-existent user"""
        authenticated_user = auth_service.authenticate_user(
            db_session, "nonexistent@example.com", "password"
        )
        
        assert authenticated_user is None
    
    def test_authenticate_user_inactive(self, auth_service, db_session, test_user_data):
        """Test authentication with inactive user"""
        # Create inactive test user
        password_hash = auth_service.hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            password_hash=password_hash,
            full_name=test_user_data["full_name"],
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Authenticate
        authenticated_user = auth_service.authenticate_user(
            db_session, test_user_data["email"], test_user_data["password"]
        )
        
        assert authenticated_user is None
    
    def test_create_token_pair(self, auth_service, db_session, test_user_data):
        """Test token pair creation"""
        # Create test user
        user = User(
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            role="learner",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        tokens = auth_service.create_token_pair(user)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert "expires_in" in tokens

class TestOAuth2PKCEService:
    """Test OAuth2 PKCE service"""
    
    def test_generate_pkce_pair(self, oauth_service):
        """Test PKCE pair generation"""
        pkce_pair = oauth_service.generate_pkce_pair()
        
        assert "code_verifier" in pkce_pair
        assert "code_challenge" in pkce_pair
        assert len(pkce_pair["code_verifier"]) >= 43
        assert len(pkce_pair["code_challenge"]) >= 43
    
    def test_get_google_auth_url(self, oauth_service):
        """Test Google auth URL generation"""
        with patch.object(oauth_service, 'google_client_id', 'test_client_id'):
            redirect_uri = "http://localhost:3000/callback"
            state = "test_state"
            code_challenge = "test_challenge"
            
            auth_url = oauth_service.get_google_auth_url(redirect_uri, state, code_challenge)
            
            assert auth_url.startswith("https://accounts.google.com/o/oauth2/v2/auth")
            assert "client_id=test_client_id" in auth_url
            assert "state=test_state" in auth_url
            assert "code_challenge=test_challenge" in auth_url
    
    def test_get_github_auth_url(self, oauth_service):
        """Test GitHub auth URL generation"""
        with patch.object(oauth_service, 'github_client_id', 'test_client_id'):
            redirect_uri = "http://localhost:3000/callback"
            state = "test_state"
            
            auth_url = oauth_service.get_github_auth_url(redirect_uri, state)
            
            assert auth_url.startswith("https://github.com/login/oauth/authorize")
            assert "client_id=test_client_id" in auth_url
            assert "state=test_state" in auth_url
    
    @patch('httpx.AsyncClient')
    async def test_exchange_google_code_success(self, mock_client, oauth_service):
        """Test successful Google code exchange"""
        # Mock HTTP responses
        mock_token_response = Mock()
        mock_token_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token"
        }
        mock_token_response.raise_for_status.return_value = None
        
        mock_userinfo_response = Mock()
        mock_userinfo_response.json.return_value = {
            "id": "123456789",
            "email": "test@gmail.com",
            "name": "Test User",
            "verified_email": True,
            "picture": "https://example.com/avatar.jpg"
        }
        mock_userinfo_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_token_response
        mock_client_instance.get.return_value = mock_userinfo_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        with patch.object(oauth_service, 'google_client_id', 'test_client_id'):
            with patch.object(oauth_service, 'google_client_secret', 'test_client_secret'):
                result = await oauth_service.exchange_google_code(
                    "test_code", "http://localhost:3000/callback", "test_verifier"
                )
                
                assert result["provider"] == "google"
                assert result["email"] == "test@gmail.com"
                assert result["full_name"] == "Test User"
                assert result["verified_email"] is True

class TestSecurityValidator:
    """Test security validation utilities"""
    
    def test_validate_password_strength_strong(self):
        """Test strong password validation"""
        result = SecurityValidator.validate_password_strength("StrongP@ssw0rd123!")

        assert all(result.values()) is True
        assert len(result) == 5
    
    def test_validate_password_strength_weak(self):
        """Test weak password validation"""
        result = SecurityValidator.validate_password_strength("weak")

        assert all(result.values()) is False
        assert result["min_length"] is False

    def test_validate_password_strength_common_pattern(self):
        """Test password with common patterns"""
        result = SecurityValidator.validate_password_strength("Password123")

        assert result["has_special"] is False
    
    def test_detect_sql_injection_positive(self):
        """Test SQL injection detection - positive case"""
        malicious_input = "'; DROP TABLE users; --"
        
        assert SecurityValidator.detect_sql_injection(malicious_input) is True
    
    def test_detect_sql_injection_negative(self):
        """Test SQL injection detection - negative case"""
        safe_input = "This is a normal search query"
        
        assert SecurityValidator.detect_sql_injection(safe_input) is False
    
    def test_detect_xss_attempt_positive(self):
        """Test XSS detection - positive case"""
        malicious_input = "<script>alert('xss')</script>"
        
        assert SecurityValidator.detect_xss_attempt(malicious_input) is True
    
    def test_detect_xss_attempt_negative(self):
        """Test XSS detection - negative case"""
        safe_input = "This is normal text content"
        
        assert SecurityValidator.detect_xss_attempt(safe_input) is False

class TestInputSanitizer:
    """Test input sanitization utilities"""
    
    def test_sanitize_string_normal(self):
        """Test normal string sanitization"""
        input_str = "  Normal text content  "
        result = InputSanitizer.sanitize_string(input_str)
        
        assert result == "Normal text content"
    
    def test_sanitize_string_with_control_chars(self):
        """Test string sanitization with control characters"""
        input_str = "Text\x00with\x01control\x02chars"
        result = InputSanitizer.sanitize_string(input_str)
        
        assert result == "Textwithcontrolchars"
    
    def test_sanitize_string_max_length(self):
        """Test string sanitization with length limit"""
        input_str = "a" * 2000
        result = InputSanitizer.sanitize_string(input_str, max_length=100)
        
        assert len(result) == 100
    
    def test_sanitize_email_normal(self):
        """Test normal email sanitization"""
        email = "  Test@Example.COM  "
        result = InputSanitizer.sanitize_email(email)
        
        assert result == "test@example.com"
    
    def test_sanitize_email_with_dangerous_chars(self):
        """Test email sanitization with dangerous characters"""
        email = "test<script>@example.com"
        result = InputSanitizer.sanitize_email(email)
        
        assert "<script>" not in result
        assert result == "test@example.com"
    
    def test_validate_url_valid(self):
        """Test URL validation with valid URL"""
        url = "https://www.example.com/path"
        
        assert InputSanitizer.validate_url(url) is True
    
    def test_validate_url_invalid(self):
        """Test URL validation with invalid URL"""
        url = "not-a-valid-url"
        
        assert InputSanitizer.validate_url(url) is False
    
    def test_validate_url_disallowed_scheme(self):
        """Test URL validation with disallowed scheme"""
        url = "ftp://example.com/file"
        
        assert InputSanitizer.validate_url(url, allowed_schemes=['http', 'https']) is False

# Updated 2025-09-05: Comprehensive authentication system tests