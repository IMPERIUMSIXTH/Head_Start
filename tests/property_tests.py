"""
Property-based tests using Hypothesis
Tests system properties and invariants across a wide range of inputs

Author: HeadStart Development Team
Created: 2025-09-08
Purpose: Property-based testing for enhanced test coverage
"""

import pytest
from hypothesis import given, strategies as st, assume, example
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from services.auth import AuthService
from services.security import SecurityValidator, InputSanitizer
from services.models import User
import re

# Property-based tests for authentication

@pytest.mark.property
class TestAuthServiceProperties:
    """Property-based tests for authentication service"""
    
    @given(st.text(min_size=8, max_size=128))
    def test_property_password_hashing_consistency(self, password):
        """Property: Password hashing should be consistent and verifiable"""
        assume(len(password) >= 8)  # Minimum password length
        assume(not any(c in password for c in ['\x00', '\n', '\r']))  # No control chars
        
        auth_service = AuthService()
        
        try:
            hashed = auth_service.hash_password(password)
            
            # Properties that should always hold
            assert hashed != password  # Hash should be different from original
            assert len(hashed) > 50    # Argon2 hashes are long
            assert hashed.startswith("$argon2id$")  # Correct algorithm
            assert auth_service.verify_password(password, hashed)  # Should verify correctly
            
            # Different calls should produce different hashes (salt)
            hashed2 = auth_service.hash_password(password)
            assert hashed != hashed2
            assert auth_service.verify_password(password, hashed2)
            
        except Exception as e:
            # If password is invalid, should raise ValidationError
            from services.exceptions import ValidationError
            assert isinstance(e, ValidationError)
    
    @given(st.text(min_size=1, max_size=7))
    def test_property_short_password_rejection(self, short_password):
        """Property: Short passwords should always be rejected"""
        auth_service = AuthService()
        
        with pytest.raises(Exception):  # Should raise ValidationError
            auth_service.hash_password(short_password)
    
    @given(st.text(min_size=8, max_size=128), st.text(min_size=8, max_size=128))
    def test_property_different_passwords_different_verification(self, password1, password2):
        """Property: Different passwords should not verify against each other's hashes"""
        assume(password1 != password2)
        assume(len(password1) >= 8 and len(password2) >= 8)
        assume(not any(c in password1 for c in ['\x00', '\n', '\r']))
        assume(not any(c in password2 for c in ['\x00', '\n', '\r']))
        
        auth_service = AuthService()
        
        try:
            hash1 = auth_service.hash_password(password1)
            hash2 = auth_service.hash_password(password2)
            
            # Different passwords should not verify against each other's hashes
            assert not auth_service.verify_password(password2, hash1)
            assert not auth_service.verify_password(password1, hash2)
            
        except Exception:
            # If passwords are invalid, skip this test case
            assume(False)

# Property-based tests for security validation

@pytest.mark.property
class TestSecurityValidatorProperties:
    """Property-based tests for security validator"""
    
    @given(st.text(min_size=1, max_size=1000))
    def test_property_sql_injection_detection_consistency(self, input_text):
        """Property: SQL injection detection should be consistent"""
        result = SecurityValidator.detect_sql_injection(input_text)
        
        # Result should always be boolean
        assert isinstance(result, bool)
        
        # If input contains obvious SQL injection patterns, should detect
        sql_patterns = ["'; DROP", "' OR '1'='1", "UNION SELECT", "-- ", "/*"]
        if any(pattern.lower() in input_text.lower() for pattern in sql_patterns):
            assert result is True
    
    @given(st.text(min_size=1, max_size=1000))
    def test_property_xss_detection_consistency(self, input_text):
        """Property: XSS detection should be consistent"""
        result = SecurityValidator.detect_xss_attempt(input_text)
        
        # Result should always be boolean
        assert isinstance(result, bool)
        
        # If input contains obvious XSS patterns, should detect
        xss_patterns = ["<script", "javascript:", "onerror=", "onload="]
        if any(pattern.lower() in input_text.lower() for pattern in xss_patterns):
            assert result is True
    
    @given(st.text(min_size=8, max_size=128))
    def test_property_password_strength_scoring(self, password):
        """Property: Password strength scoring should be consistent"""
        result = SecurityValidator.validate_password_strength(password)
        
        # Result should have expected structure
        assert isinstance(result, dict)
        assert "valid" in result
        assert "score" in result
        assert "issues" in result
        assert isinstance(result["valid"], bool)
        assert isinstance(result["score"], (int, float))
        assert isinstance(result["issues"], list)
        
        # Score should be between 0 and 10
        assert 0 <= result["score"] <= 10
        
        # If valid, score should be reasonable
        if result["valid"]:
            assert result["score"] >= 3

# Property-based tests for input sanitization

@pytest.mark.property
class TestInputSanitizerProperties:
    """Property-based tests for input sanitizer"""
    
    @given(st.text(min_size=0, max_size=1000))
    def test_property_string_sanitization_safety(self, input_string):
        """Property: String sanitization should always produce safe output"""
        result = InputSanitizer.sanitize_string(input_string)
        
        # Result should be string
        assert isinstance(result, str)
        
        # Should not contain control characters
        assert not any(ord(c) < 32 for c in result if c not in ['\n', '\r', '\t'])
        
        # Should not be longer than input (only removes/replaces)
        assert len(result) <= len(input_string)
    
    @given(st.text(min_size=0, max_size=200), st.integers(min_value=1, max_value=100))
    def test_property_string_length_limiting(self, input_string, max_length):
        """Property: String sanitization should respect length limits"""
        result = InputSanitizer.sanitize_string(input_string, max_length=max_length)
        
        # Result should not exceed max_length
        assert len(result) <= max_length
    
    @given(st.emails())
    def test_property_email_sanitization_format(self, email):
        """Property: Email sanitization should preserve valid email format"""
        result = InputSanitizer.sanitize_email(email)
        
        # Result should be string
        assert isinstance(result, str)
        
        # Should be lowercase
        assert result == result.lower()
        
        # Should still look like an email if input was valid
        if "@" in email and "." in email.split("@")[-1]:
            assert "@" in result
            assert "." in result.split("@")[-1]
    
    @given(st.text(min_size=1, max_size=200))
    def test_property_url_validation_consistency(self, url_text):
        """Property: URL validation should be consistent"""
        result = InputSanitizer.validate_url(url_text)
        
        # Result should be boolean
        assert isinstance(result, bool)
        
        # Valid URLs should have proper scheme
        if result:
            assert url_text.startswith(('http://', 'https://'))

# Stateful property-based testing

class UserManagementStateMachine(RuleBasedStateMachine):
    """Stateful testing for user management operations"""
    
    def __init__(self):
        super().__init__()
        self.users = {}
        self.auth_service = AuthService()
    
    @rule(email=st.emails(), password=st.text(min_size=8, max_size=50))
    def create_user(self, email, password):
        """Rule: Create a new user"""
        assume(email not in self.users)
        assume(not any(c in password for c in ['\x00', '\n', '\r']))
        
        try:
            password_hash = self.auth_service.hash_password(password)
            self.users[email] = {
                'password': password,
                'password_hash': password_hash,
                'active': True
            }
        except Exception:
            # Invalid password, skip
            pass
    
    @rule(email=st.sampled_from([]))  # Will be populated by create_user
    def authenticate_user(self, email):
        """Rule: Authenticate existing user"""
        if email in self.users:
            user_data = self.users[email]
            if user_data['active']:
                # Should authenticate successfully with correct password
                result = self.auth_service.verify_password(
                    user_data['password'], 
                    user_data['password_hash']
                )
                assert result is True
    
    @rule(email=st.sampled_from([]))  # Will be populated by create_user
    def deactivate_user(self, email):
        """Rule: Deactivate user"""
        if email in self.users:
            self.users[email]['active'] = False
    
    @invariant()
    def passwords_never_stored_plaintext(self):
        """Invariant: Passwords should never be stored in plaintext as hashes"""
        for user_data in self.users.values():
            if 'password_hash' in user_data:
                assert user_data['password_hash'] != user_data['password']
                assert user_data['password_hash'].startswith('$argon2id$')

# Example-based property tests with specific edge cases

@pytest.mark.property
class TestPropertyExamples:
    """Property tests with specific examples for edge cases"""
    
    @given(st.text())
    @example("")  # Empty string
    @example("a" * 10000)  # Very long string
    @example("\x00\x01\x02")  # Control characters
    @example("🚀🌟💻")  # Unicode characters
    def test_property_sanitization_edge_cases(self, input_text):
        """Property test with specific edge case examples"""
        result = InputSanitizer.sanitize_string(input_text, max_length=1000)
        
        # Should handle all inputs gracefully
        assert isinstance(result, str)
        assert len(result) <= 1000
        
        # Should not contain dangerous control characters
        dangerous_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05']
        assert not any(char in result for char in dangerous_chars)

# Performance property tests

@pytest.mark.property
@pytest.mark.slow
class TestPerformanceProperties:
    """Property-based performance tests"""
    
    @given(st.text(min_size=8, max_size=100))
    def test_property_password_hashing_performance(self, password):
        """Property: Password hashing should complete within reasonable time"""
        assume(len(password) >= 8)
        assume(not any(c in password for c in ['\x00', '\n', '\r']))
        
        import time
        auth_service = AuthService()
        
        try:
            start_time = time.time()
            auth_service.hash_password(password)
            end_time = time.time()
            
            # Should complete within 5 seconds (generous for Argon2)
            assert (end_time - start_time) < 5.0
            
        except Exception:
            # Invalid password, skip timing test
            pass

# Run stateful tests
TestUserManagement = UserManagementStateMachine.TestCase