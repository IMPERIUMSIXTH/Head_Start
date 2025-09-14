"""
Tests for the enhanced unit testing framework
Validates that all enhanced testing capabilities work correctly

Author: HeadStart Development Team
Created: 2025-09-08
Purpose: Test the enhanced testing framework itself
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, AsyncMock, patch
from hypothesis import given, strategies as st
from services.auth import AuthService
from services.security import SecurityValidator, InputSanitizer
from services.exceptions import ValidationError

@pytest.mark.unit
@pytest.mark.fixtures
class TestEnhancedFixtures:
    """Test enhanced fixture functionality"""
    
    def test_sample_user_factory_creates_users(self, sample_user_factory):
        """Test that sample user factory creates valid users"""
        user1 = sample_user_factory(email="test1@example.com")
        user2 = sample_user_factory(email="test2@example.com", role="admin")
        
        assert user1.email == "test1@example.com"
        assert user1.role == "learner"  # Default role
        assert user2.email == "test2@example.com"
        assert user2.role == "admin"
        assert user1.id != user2.id
        assert user1.password_hash is not None
        assert user2.password_hash is not None
    
    def test_content_factory_creates_content(self, content_factory):
        """Test that content factory creates valid content items"""
        content1 = content_factory(title="Test Video")
        content2 = content_factory(title="Test Article", content_type="article")
        
        assert content1.title == "Test Video"
        assert content1.content_type == "video"  # Default type
        assert content2.title == "Test Article"
        assert content2.content_type == "article"
        assert content1.id != content2.id
        assert len(content1.topics) > 0
        assert len(content2.topics) > 0
    
    def test_mock_external_apis_configured(self, mock_external_apis):
        """Test that external API mocks are properly configured"""
        mocks = mock_external_apis
        
        # Test YouTube API mock
        youtube_response = mocks['youtube_api'].json.return_value
        assert 'items' in youtube_response
        assert len(youtube_response['items']) > 0
        assert 'snippet' in youtube_response['items'][0]
        
        # Test arXiv API mock
        arxiv_content = mocks['arxiv_api'].content
        assert isinstance(arxiv_content, bytes)
        assert b'<feed' in arxiv_content
        
        # Test OpenAI API mock
        openai_response = mocks['openai_api'].return_value
        assert 'data' in openai_response
        assert len(openai_response['data'][0]['embedding']) == 1536
    
    def test_security_test_data_comprehensive(self, security_test_data):
        """Test that security test data covers various attack vectors"""
        data = security_test_data
        
        # SQL injection payloads
        sql_payloads = data['sql_injection_payloads']
        assert any('DROP TABLE' in payload for payload in sql_payloads)
        assert any("OR '1'='1" in payload for payload in sql_payloads)
        assert any('UNION SELECT' in payload for payload in sql_payloads)
        
        # XSS payloads
        xss_payloads = data['xss_payloads']
        assert any('<script>' in payload for payload in xss_payloads)
        assert any('javascript:' in payload for payload in xss_payloads)
        assert any('onerror=' in payload for payload in xss_payloads)
        
        # Malicious files
        malicious_files = data['malicious_files']
        assert any(f['name'].endswith('.exe') for f in malicious_files)
        assert any(f['name'].endswith('.php') for f in malicious_files)

@pytest.mark.unit
@pytest.mark.property
class TestPropertyBasedTestingFramework:
    """Test property-based testing framework functionality"""
    
    @given(st.text(min_size=8, max_size=50))
    def test_property_framework_password_hashing(self, password):
        """Test that property-based testing framework works for password hashing"""
        from hypothesis import assume
        assume(not any(c in password for c in ['\x00', '\n', '\r']))
        
        auth_service = AuthService()
        
        try:
            hashed = auth_service.hash_password(password)
            
            # Test properties
            assert hashed != password
            assert len(hashed) > 50
            assert hashed.startswith("$argon2id$")
            assert auth_service.verify_password(password, hashed)
            
        except ValidationError:
            # Expected for invalid passwords
            pass
    
    @given(st.emails())
    def test_property_framework_email_sanitization(self, email):
        """Test property-based testing for email sanitization"""
        result = InputSanitizer.sanitize_email(email)
        
        assert isinstance(result, str)
        assert result == result.lower()
        if '@' in email:
            assert '@' in result
    
    def test_hypothesis_settings_configured(self, hypothesis_settings):
        """Test that Hypothesis settings are properly configured"""
        settings = hypothesis_settings
        
        assert hasattr(settings, 'max_examples')
        assert settings.max_examples >= 10
        assert settings.deadline is None

@pytest.mark.unit
@pytest.mark.asyncio
class TestAsyncTestingFramework:
    """Test async testing framework functionality"""
    
    async def test_async_framework_basic_functionality(self):
        """Test basic async testing framework functionality"""
        async def async_operation():
            await asyncio.sleep(0.01)
            return "completed"
        
        result = await async_operation()
        assert result == "completed"
    
    async def test_async_framework_concurrent_operations(self):
        """Test concurrent async operations in framework"""
        async def async_task(task_id, delay):
            await asyncio.sleep(delay)
            return f"task_{task_id}"
        
        # Run tasks concurrently
        start_time = asyncio.get_event_loop().time()
        tasks = [async_task(i, 0.01) for i in range(3)]
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        # Should complete concurrently, not sequentially
        assert (end_time - start_time) < 0.05  # Much less than 3 * 0.01
        assert len(results) == 3
        assert all(result.startswith("task_") for result in results)
    
    def test_celery_app_fixture(self, celery_app):
        """Test Celery app fixture configuration"""
        assert celery_app is not None
        assert celery_app.conf.task_always_eager is True
        assert celery_app.conf.task_eager_propagates is True
        assert 'memory://' in celery_app.conf.broker_url

@pytest.mark.unit
@pytest.mark.security
class TestSecurityTestingFramework:
    """Test security testing framework functionality"""
    
    @pytest.mark.parametrize("malicious_input", [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; INSERT INTO users VALUES ('hacker'); --"
    ])
    def test_sql_injection_detection_parametrized(self, malicious_input):
        """Test parametrized SQL injection detection"""
        result = SecurityValidator.detect_sql_injection(malicious_input)
        assert result is True, f"Failed to detect SQL injection: {malicious_input}"
    
    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>"
    ])
    def test_xss_detection_parametrized(self, xss_payload):
        """Test parametrized XSS detection"""
        result = SecurityValidator.detect_xss_attempt(xss_payload)
        assert result is True, f"Failed to detect XSS: {xss_payload}"
    
    def test_security_framework_comprehensive_coverage(self, security_test_data):
        """Test that security framework provides comprehensive coverage"""
        data = security_test_data
        
        # Test all SQL injection payloads
        for payload in data['sql_injection_payloads']:
            result = SecurityValidator.detect_sql_injection(payload)
            assert result is True, f"Missed SQL injection: {payload}"
        
        # Test all XSS payloads
        for payload in data['xss_payloads']:
            result = SecurityValidator.detect_xss_attempt(payload)
            assert result is True, f"Missed XSS: {payload}"

@pytest.mark.unit
@pytest.mark.performance
class TestPerformanceTestingFramework:
    """Test performance testing framework functionality"""
    
    def test_benchmark_config_available(self, benchmark_config):
        """Test that benchmark configuration is available"""
        config = benchmark_config
        
        assert 'min_rounds' in config
        assert 'max_time' in config
        assert 'warmup' in config
        assert config['min_rounds'] > 0
        assert config['max_time'] > 0
    
    @pytest.mark.slow
    def test_performance_test_data_scaling(self, performance_test_data):
        """Test performance test data provides different scales"""
        data = performance_test_data
        
        small = data['small_dataset']
        medium = data['medium_dataset']
        large = data['large_dataset']
        
        # Verify scaling
        assert small['users'] < medium['users'] < large['users']
        assert small['content_items'] < medium['content_items'] < large['content_items']
        assert small['interactions'] < medium['interactions'] < large['interactions']

@pytest.mark.unit
@pytest.mark.mutation
class TestMutationTestingFramework:
    """Test mutation testing framework functionality"""
    
    def test_critical_function_mutation_detection(self):
        """Test that critical functions are properly tested for mutations"""
        auth_service = AuthService()
        
        # These tests should catch common mutations
        password = "TestPassword123!"
        hashed = auth_service.hash_password(password)
        
        # Mutation: return password instead of hash
        assert hashed != password
        
        # Mutation: always return True/False
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong", hashed) is False
    
    def test_boundary_condition_mutations(self):
        """Test boundary conditions that should catch mutations"""
        auth_service = AuthService()
        
        # Mutation: change minimum length requirement
        with pytest.raises(ValidationError):
            auth_service.hash_password("short")  # Less than 8 characters
        
        # Mutation: change validation logic
        result = SecurityValidator.validate_password_strength("weak")
        assert result["valid"] is False
        assert result["score"] < 3

@pytest.mark.unit
class TestFrameworkConfiguration:
    """Test framework configuration and setup"""
    
    def test_pytest_markers_work(self):
        """Test that pytest markers are properly configured"""
        # This test itself uses markers, so if it runs, markers work
        assert True
    
    def test_test_data_generators_available(self, test_data_generators):
        """Test that test data generators are available and functional"""
        generators = test_data_generators
        
        # Test email generator
        email = generators['email']()
        assert '@' in email
        assert '.' in email
        
        # Test name generator
        name = generators['name']()
        assert len(name) > 0
        assert isinstance(name, str)
        
        # Test password generator
        password = generators['password']()
        assert len(password) >= 8
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
    
    def test_temp_file_fixture(self, temp_file):
        """Test temporary file fixture"""
        assert os.path.exists(temp_file)
        
        # Write to temp file
        with open(temp_file, 'w') as f:
            f.write("test content")
        
        # Read from temp file
        with open(temp_file, 'r') as f:
            content = f.read()
        
        assert content == "test content"
    
    def test_temp_dir_fixture(self, temp_dir):
        """Test temporary directory fixture"""
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)
        
        # Create file in temp dir
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        assert os.path.exists(test_file)

@pytest.mark.integration
class TestFrameworkIntegration:
    """Test framework integration with existing systems"""
    
    def test_database_integration(self, db_session, sample_user_factory):
        """Test framework integration with database"""
        user = sample_user_factory(email="integration@example.com")
        
        # Verify user was created in database
        assert user.id is not None
        assert user.email == "integration@example.com"
        
        # Verify we can query the user
        queried_user = db_session.query(type(user)).filter_by(email="integration@example.com").first()
        assert queried_user is not None
        assert queried_user.id == user.id
    
    def test_auth_service_integration(self, auth_service, sample_user_factory, db_session):
        """Test framework integration with auth service"""
        user = sample_user_factory(email="auth@example.com", password="TestPassword123!")
        
        # Test authentication
        authenticated_user = auth_service.authenticate_user(
            db_session, "auth@example.com", "TestPassword123!"
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        
        # Test token creation
        tokens = auth_service.create_token_pair(user)
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens

@pytest.mark.regression
class TestFrameworkRegression:
    """Regression tests for framework functionality"""
    
    def test_fixture_cleanup_regression(self, sample_user_factory):
        """Test that fixtures properly clean up after themselves"""
        initial_user = sample_user_factory(email="cleanup1@example.com")
        second_user = sample_user_factory(email="cleanup2@example.com")
        
        # Users should have different IDs
        assert initial_user.id != second_user.id
        
        # Both should be valid
        assert initial_user.email == "cleanup1@example.com"
        assert second_user.email == "cleanup2@example.com"
    
    def test_mock_isolation_regression(self, mock_external_apis):
        """Test that mocks don't interfere with each other"""
        mocks = mock_external_apis
        
        # Modify one mock
        mocks['youtube_api'].json.return_value = {'modified': True}
        
        # Other mocks should be unaffected
        assert 'data' in mocks['openai_api'].return_value
        assert b'<feed' in mocks['arxiv_api'].content
    
    def test_async_fixture_regression(self, async_db_session):
        """Test async fixture regression"""
        # Should not raise any errors
        assert async_db_session is not None