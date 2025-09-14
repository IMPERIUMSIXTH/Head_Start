"""
Basic pytest configuration and fixtures
Provides essential testing capabilities without external dependencies

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Basic unit testing framework configuration
"""

import pytest
import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Generator
from unittest.mock import Mock, AsyncMock, patch
from faker import Faker

fake = Faker()

# Basic fixtures without external dependencies

@pytest.fixture(scope="function")
def sample_user_data():
    """Provide sample user data for testing"""
    return {
        'email': fake.email(),
        'full_name': fake.name(),
        'role': 'learner',
        'is_active': True,
        'email_verified': True,
        'created_at': datetime.utcnow()
    }

@pytest.fixture(scope="function")
def sample_content_data():
    """Provide sample content data for testing"""
    return {
        'title': fake.sentence(nb_words=4),
        'description': fake.text(max_nb_chars=200),
        'content_type': 'video',
        'source': 'youtube',
        'source_id': fake.uuid4(),
        'url': fake.url(),
        'duration_minutes': fake.random_int(min=5, max=120),
        'difficulty_level': 'beginner',
        'topics': ['AI', 'Machine Learning'],
        'language': 'en',
        'status': 'approved'
    }

@pytest.fixture(scope="function")
def mock_external_apis():
    """Mock external APIs for testing"""
    mocks = {
        'youtube_api': Mock(),
        'arxiv_api': Mock(),
        'openai_api': AsyncMock()
    }
    
    # Configure YouTube API mock
    mocks['youtube_api'].json.return_value = {
        'items': [{
            'snippet': {
                'title': 'Test Video',
                'description': 'Test video description',
                'tags': ['test', 'education'],
                'channelTitle': 'Test Channel',
                'publishedAt': '2023-01-01T00:00:00Z'
            },
            'contentDetails': {'duration': 'PT15M33S'},
            'statistics': {'viewCount': '1000', 'likeCount': '100'}
        }]
    }
    
    # Configure arXiv API mock
    mocks['arxiv_api'].content = '''<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <entry>
            <title>Test Paper</title>
            <summary>Test paper abstract</summary>
            <author><name>Test Author</name></author>
            <category term="cs.AI"/>
        </entry>
    </feed>'''.encode()
    
    # Configure OpenAI API mock
    mocks['openai_api'].Embedding.acreate.return_value = {
        'data': [{'embedding': [0.1] * 1536}]
    }
    
    return mocks

@pytest.fixture(scope="function")
def security_test_data():
    """Provide security test data for various attack vectors"""
    return {
        'sql_injection_payloads': [
            "'; DROP TABLE users; --",
            "' OR '1'='1' --",
            "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --",
            "' UNION SELECT * FROM users --",
            "'; UPDATE users SET role='admin' WHERE email='victim@example.com'; --"
        ],
        'xss_payloads': [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//"
        ],
        'safe_inputs': [
            "normal@example.com",
            "user with spaces",
            "user123@domain.co.uk",
            "Normal text content",
            "Text with <b>HTML</b> tags"
        ]
    }

@pytest.fixture(scope="function")
def benchmark_config():
    """Configuration for benchmark tests"""
    return {
        'min_rounds': 5,
        'max_time': 10.0,
        'warmup': True,
        'warmup_iterations': 2
    }

@pytest.fixture(scope="function")
def performance_test_data():
    """Generate test data for performance testing"""
    return {
        'small_dataset': {
            'users': 10,
            'content_items': 50,
            'interactions': 100
        },
        'medium_dataset': {
            'users': 100,
            'content_items': 500,
            'interactions': 1000
        },
        'large_dataset': {
            'users': 1000,
            'content_items': 5000,
            'interactions': 10000
        }
    }

@pytest.fixture(scope="function")
def test_data_generators():
    """Provide data generators for testing"""
    return {
        'email': lambda: fake.email(),
        'name': lambda: fake.name(),
        'password': lambda: fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        'url': lambda: fake.url(),
        'text': lambda length=100: fake.text(max_nb_chars=length),
        'uuid': lambda: fake.uuid4(),
        'datetime': lambda: fake.date_time_between(start_date='-1y', end_date='now'),
        'integer': lambda min_val=1, max_val=100: fake.random_int(min=min_val, max=max_val),
        'float': lambda min_val=0.0, max_val=1.0: fake.random.uniform(min_val, max_val)
    }

@pytest.fixture(scope="function")
def async_scenario_complex():
    """Complex async testing scenario"""
    return {
        'concurrent_operations': 10,
        'operation_delay': 0.1,
        'timeout_threshold': 1.0,
        'retry_attempts': 3,
        'circuit_breaker_threshold': 5
    }

@pytest.fixture(scope="function")
def mutation_test_config():
    """Configuration for mutation testing"""
    return {
        'timeout': 60,
        'test_command': 'python -m pytest tests/unit/ -x --tb=no -q',
        'paths_to_mutate': ['services/', 'api/'],
        'min_mutation_score': 75
    }

# Pytest hooks for enhanced functionality

def pytest_configure(config):
    """Configure pytest with custom settings"""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (database, external services)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full workflows)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "security: Security-related tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "smoke: Smoke tests for critical functionality")
    config.addinivalue_line("markers", "regression: Regression tests")
    config.addinivalue_line("markers", "property: Property-based tests using Hypothesis")
    config.addinivalue_line("markers", "mutation: Tests for mutation testing validation")
    config.addinivalue_line("markers", "asyncio: Asynchronous tests")
    config.addinivalue_line("markers", "celery: Celery task tests")
    config.addinivalue_line("markers", "auth: Authentication and authorization tests")
    config.addinivalue_line("markers", "content: Content processing tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "models: Database model tests")
    config.addinivalue_line("markers", "fixtures: Tests that use complex fixtures")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location and name"""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add markers based on test name patterns
        if "async" in item.name:
            item.add_marker(pytest.mark.asyncio)
        if "property" in item.name:
            item.add_marker(pytest.mark.property)
        if "auth" in item.name:
            item.add_marker(pytest.mark.auth)
        if "security" in item.name:
            item.add_marker(pytest.mark.security)
        if "performance" in item.name or "benchmark" in item.name:
            item.add_marker(pytest.mark.performance)
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for each test"""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"
    
    yield
    
    # Cleanup after test
    if "TESTING" in os.environ:
        del os.environ["TESTING"]