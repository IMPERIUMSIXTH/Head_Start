"""
Authentication and Authorization Integration Tests
Tests for authentication flows, authorization checks, and security validation

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Comprehensive authentication and authorization integration testing
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from services.auth import auth_service
from services.models import User
from jose import jwt

logger = structlog.get_logger()

class AuthIntegrationTests:
    """Authentication and authorization integration test suite"""
    
    def __init__(self, context):
        self.context = context
        self.client = context.api_client
        self.db = context.db_session
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
    
    def _record_test_result(self, test_name: str, success: bool, error: str = None):
        """Record test result"""
        if success:
            self.passed += 1
            logger.info(f"✓ {test_name}")
        else:
            self.failed += 1
            if error:
                self.errors.append(f"{test_name}: {error}")
            logger.error(f"✗ {test_name}", error=error)
    
    async def test_user_registration_flow(self) -> bool:
        """Test complete user registration flow"""
        try:
            # Test registration with valid data
            registration_data = {
                "email": "auth_test_user@example.com",
                "password": "SecurePassword123!",
                "full_name": "Auth Test User"
            }
            
            response = self.client.post("/api/auth/register", json=registration_data)
            
            if response.status_code != 201:
                self._record_test_result("User Registration Flow", False, 
                                       f"Registration failed: {response.status_code} - {response.text}")
                return False
            
            response_data = response.json()
            
            # Verify response contains tokens
            if not all(key in response_data for key in ["access_token", "refresh_token", "token_type"]):
                self._record_test_result("User Registration Flow", False, 
                                       "Missing token fields in response")
                return False
            
            # Verify user was created in database
            created_user = self.db.query(User).filter(
                User.email == "auth_test_user@example.com"
            ).first()
            
            if not created_user:
                self._record_test_result("User Registration Flow", False, 
                                       "User not created in database")
                return False
            
            # Verify user properties
            if (created_user.full_name != "Auth Test User" or
                created_user.role != "learner" or
                not created_user.is_active):
                self._record_test_result("User Registration Flow", False, 
                                       "User properties incorrect")
                return False
            
            # Verify password was hashed
            if not created_user.password_hash or created_user.password_hash == "SecurePassword123!":
                self._record_test_result("User Registration Flow", False, 
                                       "Password not properly hashed")
                return False
            
            self._record_test_result("User Registration Flow", True)
            return True
        except Exception as e:
            self._record_test_result("User Registration Flow", False, str(e))
            return False
    
    async def test_user_login_flow(self) -> bool:
        """Test complete user login flow"""
        try:
            test_user = self.context.test_users[0]  # active_user@test.com
            
            # Test login with correct credentials
            login_data = {
                "email": test_user.email,
                "password": "TestPassword123!"
            }
            
            response = self.client.post("/api/auth/login", json=login_data)
            
            if response.status_code != 200:
                self._record_test_result("User Login Flow", False, 
                                       f"Login failed: {response.status_code} - {response.text}")
                return False
            
            response_data = response.json()
            
            # Verify response contains tokens
            if not all(key in response_data for key in ["access_token", "refresh_token", "token_type"]):
                self._record_test_result("User Login Flow", False, 
                                       "Missing token fields in response")
                return False
            
            # Verify token validity
            access_token = response_data["access_token"]
            try:
                payload = auth_service.verify_token(access_token, "access")
                if payload.get("sub") != str(test_user.id):
                    self._record_test_result("User Login Flow", False, 
                                           "Token payload incorrect")
                    return False
            except Exception as e:
                self._record_test_result("User Login Flow", False, 
                                       f"Token verification failed: {str(e)}")
                return False
            
            self._record_test_result("User Login Flow", True)
            return True
        except Exception as e:
            self._record_test_result("User Login Flow", False, str(e))
            return False
    
    async def test_invalid_login_attempts(self) -> bool:
        """Test various invalid login scenarios"""
        try:
            # Test with non-existent user
            response = self.client.post("/api/auth/login", json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!"
            })
            
            if response.status_code != 401:
                self._record_test_result("Invalid Login - Non-existent User", False, 
                                       f"Expected 401, got {response.status_code}")
                return False
            
            # Test with wrong password
            test_user = self.context.test_users[0]
            response = self.client.post("/api/auth/login", json={
                "email": test_user.email,
                "password": "WrongPassword123!"
            })
            
            if response.status_code != 401:
                self._record_test_result("Invalid Login - Wrong Password", False, 
                                       f"Expected 401, got {response.status_code}")
                return False
            
            # Test with inactive user
            inactive_user = next((u for u in self.context.test_users if not u.is_active), None)
            if inactive_user:
                response = self.client.post("/api/auth/login", json={
                    "email": inactive_user.email,
                    "password": "TestPassword123!"
                })
                
                if response.status_code != 401:
                    self._record_test_result("Invalid Login - Inactive User", False, 
                                           f"Expected 401, got {response.status_code}")
                    return False
            
            # Test with malformed email
            response = self.client.post("/api/auth/login", json={
                "email": "not-an-email",
                "password": "TestPassword123!"
            })
            
            if response.status_code not in [400, 422]:
                self._record_test_result("Invalid Login - Malformed Email", False, 
                                       f"Expected 400/422, got {response.status_code}")
                return False
            
            self._record_test_result("Invalid Login Attempts", True)
            return True
        except Exception as e:
            self._record_test_result("Invalid Login Attempts", False, str(e))
            return False
    
    async def test_token_refresh_flow(self) -> bool:
        """Test token refresh functionality"""
        try:
            test_user = self.context.test_users[0]
            
            # First, login to get tokens
            login_response = self.client.post("/api/auth/login", json={
                "email": test_user.email,
                "password": "TestPassword123!"
            })
            
            if login_response.status_code != 200:
                self._record_test_result("Token Refresh Flow", False, 
                                       "Initial login failed")
                return False
            
            tokens = login_response.json()
            refresh_token = tokens["refresh_token"]
            
            # Test token refresh
            refresh_response = self.client.post("/api/auth/refresh", json={
                "refresh_token": refresh_token
            })
            
            if refresh_response.status_code != 200:
                self._record_test_result("Token Refresh Flow", False, 
                                       f"Token refresh failed: {refresh_response.status_code} - {refresh_response.text}")
                return False
            
            new_tokens = refresh_response.json()
            
            # Verify new tokens are different
            if (new_tokens["access_token"] == tokens["access_token"] or
                new_tokens["refresh_token"] == tokens["refresh_token"]):
                self._record_test_result("Token Refresh Flow", False, 
                                       "New tokens are same as old tokens")
                return False
            
            # Verify new access token is valid
            try:
                payload = auth_service.verify_token(new_tokens["access_token"], "access")
                if payload.get("sub") != str(test_user.id):
                    self._record_test_result("Token Refresh Flow", False, 
                                           "New token payload incorrect")
                    return False
            except Exception as e:
                self._record_test_result("Token Refresh Flow", False, 
                                       f"New token verification failed: {str(e)}")
                return False
            
            self._record_test_result("Token Refresh Flow", True)
            return True
        except Exception as e:
            self._record_test_result("Token Refresh Flow", False, str(e))
            return False
    
    async def test_invalid_token_scenarios(self) -> bool:
        """Test various invalid token scenarios"""
        try:
            # Test with invalid token format
            response = self.client.get("/api/auth/profile", headers={
                "Authorization": "Bearer invalid-token-format"
            })
            
            if response.status_code not in [401, 403]:
                self._record_test_result("Invalid Token - Format", False, 
                                       f"Expected 401/403, got {response.status_code}")
                return False
            
            # Test with expired token (simulate by creating token with past expiry)
            test_user = self.context.test_users[0]
            expired_token_data = {
                "sub": str(test_user.id),
                "email": test_user.email,
                "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
                "type": "access"
            }
            
            expired_token = jwt.encode(
                expired_token_data, 
                auth_service.secret_key, 
                algorithm=auth_service.algorithm
            )
            
            response = self.client.get("/api/auth/profile", headers={
                "Authorization": f"Bearer {expired_token}"
            })
            
            if response.status_code not in [401, 403]:
                self._record_test_result("Invalid Token - Expired", False, 
                                       f"Expected 401/403, got {response.status_code}")
                return False
            
            # Test with wrong token type (using refresh token for access)
            refresh_token_data = {
                "sub": str(test_user.id),
                "exp": datetime.utcnow() + timedelta(days=1),
                "type": "refresh"  # Wrong type
            }
            
            wrong_type_token = jwt.encode(
                refresh_token_data,
                auth_service.secret_key,
                algorithm=auth_service.algorithm
            )
            
            response = self.client.get("/api/auth/profile", headers={
                "Authorization": f"Bearer {wrong_type_token}"
            })
            
            if response.status_code not in [401, 403]:
                self._record_test_result("Invalid Token - Wrong Type", False, 
                                       f"Expected 401/403, got {response.status_code}")
                return False
            
            # Test with missing Authorization header
            response = self.client.get("/api/auth/profile")
            
            if response.status_code not in [401, 403]:
                self._record_test_result("Invalid Token - Missing Header", False, 
                                       f"Expected 401/403, got {response.status_code}")
                return False
            
            self._record_test_result("Invalid Token Scenarios", True)
            return True
        except Exception as e:
            self._record_test_result("Invalid Token Scenarios", False, str(e))
            return False
    
    async def test_role_based_authorization(self) -> bool:
        """Test role-based access control"""
        try:
            # Get admin and regular user
            admin_user = next((u for u in self.context.test_users if u.role == "admin"), None)
            regular_user = next((u for u in self.context.test_users if u.role == "learner"), None)
            
            if not admin_user or not regular_user:
                self.skipped += 1
                logger.info("⚠ Role-based Authorization - Skipped (missing admin or regular user)")
                return True
            
            # Create tokens for both users
            admin_token_data = {"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role}
            admin_token = auth_service.create_access_token(admin_token_data)
            
            regular_token_data = {"sub": str(regular_user.id), "email": regular_user.email, "role": regular_user.role}
            regular_token = auth_service.create_access_token(regular_token_data)
            
            # Test admin access to admin endpoint (if it exists)
            admin_response = self.client.get("/admin/users", headers={
                "Authorization": f"Bearer {admin_token}"
            })
            
            # If endpoint doesn't exist, skip this part
            if admin_response.status_code == 404:
                self.skipped += 1
                logger.info("⚠ Role-based Authorization - Skipped (admin endpoints not implemented)")
                return True
            
            # Test regular user access to admin endpoint (should be forbidden)
            regular_response = self.client.get("/admin/users", headers={
                "Authorization": f"Bearer {regular_token}"
            })
            
            if regular_response.status_code not in [401, 403]:
                self._record_test_result("Role-based Authorization", False, 
                                       f"Regular user accessed admin endpoint: {regular_response.status_code}")
                return False
            
            # Test both users can access regular endpoints
            admin_profile = self.client.get("/api/auth/profile", headers={
                "Authorization": f"Bearer {admin_token}"
            })
            
            regular_profile = self.client.get("/api/auth/profile", headers={
                "Authorization": f"Bearer {regular_token}"
            })
            
            if admin_profile.status_code != 200 or regular_profile.status_code != 200:
                self._record_test_result("Role-based Authorization", False, 
                                       "Users cannot access regular endpoints")
                return False
            
            self._record_test_result("Role-based Authorization", True)
            return True
        except Exception as e:
            self._record_test_result("Role-based Authorization", False, str(e))
            return False
    
    async def test_password_security(self) -> bool:
        """Test password security requirements"""
        try:
            # Test weak password rejection
            weak_passwords = [
                "123456",           # Too short, no complexity
                "password",         # Common password, no complexity
                "Password",         # Missing numbers and special chars
                "Password123",      # Missing special chars
                "password123!",     # Missing uppercase
                "PASSWORD123!",     # Missing lowercase
            ]
            
            for weak_password in weak_passwords:
                response = self.client.post("/api/auth/register", json={
                    "email": f"weak_test_{weak_password[:3]}@example.com",
                    "password": weak_password,
                    "full_name": "Weak Password Test"
                })
                
                if response.status_code not in [400, 422]:
                    self._record_test_result("Password Security", False, 
                                           f"Weak password '{weak_password}' was accepted")
                    return False
            
            # Test strong password acceptance
            strong_password = "StrongPassword123!"
            response = self.client.post("/api/auth/register", json={
                "email": "strong_password_test@example.com",
                "password": strong_password,
                "full_name": "Strong Password Test"
            })
            
            if response.status_code != 201:
                self._record_test_result("Password Security", False, 
                                       f"Strong password was rejected: {response.status_code}")
                return False
            
            # Verify password is properly hashed
            created_user = self.db.query(User).filter(
                User.email == "strong_password_test@example.com"
            ).first()
            
            if not created_user or not created_user.password_hash:
                self._record_test_result("Password Security", False, 
                                       "User not created or password not hashed")
                return False
            
            # Verify password hash is not the plain password
            if created_user.password_hash == strong_password:
                self._record_test_result("Password Security", False, 
                                       "Password stored in plain text")
                return False
            
            # Verify password can be verified
            if not auth_service.verify_password(strong_password, created_user.password_hash):
                self._record_test_result("Password Security", False, 
                                       "Password verification failed")
                return False
            
            self._record_test_result("Password Security", True)
            return True
        except Exception as e:
            self._record_test_result("Password Security", False, str(e))
            return False
    
    async def test_session_management(self) -> bool:
        """Test session management and logout"""
        try:
            test_user = self.context.test_users[0]
            
            # Login to get token
            login_response = self.client.post("/api/auth/login", json={
                "email": test_user.email,
                "password": "TestPassword123!"
            })
            
            if login_response.status_code != 200:
                self._record_test_result("Session Management", False, 
                                       "Login failed")
                return False
            
            tokens = login_response.json()
            access_token = tokens["access_token"]
            
            # Verify token works
            profile_response = self.client.get("/api/auth/profile", headers={
                "Authorization": f"Bearer {access_token}"
            })
            
            if profile_response.status_code != 200:
                self._record_test_result("Session Management", False, 
                                       "Token doesn't work after login")
                return False
            
            # Test logout
            logout_response = self.client.post("/api/auth/logout", headers={
                "Authorization": f"Bearer {access_token}"
            })
            
            if logout_response.status_code != 200:
                self._record_test_result("Session Management", False, 
                                       f"Logout failed: {logout_response.status_code}")
                return False
            
            # Note: In a real implementation, the token would be blacklisted
            # For now, we just verify the logout endpoint works
            
            self._record_test_result("Session Management", True)
            return True
        except Exception as e:
            self._record_test_result("Session Management", False, str(e))
            return False
    
    async def test_concurrent_authentication(self) -> bool:
        """Test concurrent authentication requests"""
        try:
            test_user = self.context.test_users[0]
            
            # Create multiple concurrent login requests
            async def login_attempt():
                try:
                    response = self.client.post("/api/auth/login", json={
                        "email": test_user.email,
                        "password": "TestPassword123!"
                    })
                    return response.status_code == 200
                except Exception:
                    return False
            
            # Run 5 concurrent login attempts
            tasks = [login_attempt() for _ in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful logins
            successful_logins = sum(1 for r in results if r is True)
            
            # All should succeed (no rate limiting implemented yet)
            if successful_logins < 4:  # Allow for some potential failures
                self._record_test_result("Concurrent Authentication", False, 
                                       f"Only {successful_logins}/5 concurrent logins succeeded")
                return False
            
            self._record_test_result("Concurrent Authentication", True)
            return True
        except Exception as e:
            self._record_test_result("Concurrent Authentication", False, str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all authentication integration tests"""
        logger.info("Running authentication integration tests")
        
        # Run all test methods
        await self.test_user_registration_flow()
        await self.test_user_login_flow()
        await self.test_invalid_login_attempts()
        await self.test_token_refresh_flow()
        await self.test_invalid_token_scenarios()
        await self.test_role_based_authorization()
        await self.test_password_security()
        await self.test_session_management()
        await self.test_concurrent_authentication()
        
        return {
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "total": self.passed + self.failed + self.skipped
        }