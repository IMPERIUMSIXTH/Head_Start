"""
Enhanced pytest configuration and fixtures
Provides advanced testing capabilities including property-based testing,
async patterns, complex fixtures, and mutation testing support

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Enhanced unit testing framework configuration
"""

import pytest
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Generator
from unittest.mock import Mock, AsyncMock, patch
from faker import Faker
from hypothesis import settings, Verbosity

# Import application components
from services.auth import AuthService
from services.content_processing import ContentProcessor
from services.security import SecurityValidator, InputSanitizer
from services.database import get_db_session, create_tables
from services.models import User, ContentItem, UserPreferences
from services.exceptions import ValidationError, AuthenticationError

fake = Faker()

# Hypothesis configuration for property-based testing
settings.register_profile("default", max_examples=50, deadline=None, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=100, deadline=None, verbosity=Verbosity.quiet)
settings.register_profile("dev", max_examples=20, deadline=None, verbosity=Verbosity.verbose)

# Load profile based on environment
profile = os.getenv("HYPOTHESIS_PROFILE", "default")
settings.load_profile(profile)

@pytest.fixture(scope="session")
def hypothesis_settings():
    """Provide Hypothesis settings for tests"""
    return settings.get_profile(profile)

# Database fixtures

@pytest.fixture(scope="session")
def test_database_url():
    """Provide test database URL"""
    return os.getenv("TEST_DATABASE_URL", "sqlite:///test.db")

@pytest.fixture(scope="function")
def db_session(test_database_url):
    """Provide database session for tests"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(test_database_url, echo=False)
    create_tables(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def async_db_session(db_session):
    """Provide async-compatible database session"""
    # For now, return sync session - can be enhanced for true async later
    return db_session

# Authentication fixtures

@pytest.fixture(scope="function")
def auth_service():
    """Provide AuthService instance for testing"""
    return AuthService()

@pytest.fixture(scope="function")
def sample_user_factory(db_session):
    """Factory for creating test users"""
    created_users = []
    
    def _create_user(
        email: Optional[str] = None,
        password: Optional[str] = None,
        role: str = "learner",
        is_active: bool = True,
        email_verified: bool = True
    ) -> User:
        if email is None:
            email = fake.email()
        if password is None:
            password = "TestPassword123!"
        
        auth_service = AuthService()
        password_hash = auth_service.hash_password(password) if password else None
        
        user = User(
            email=email.lower(),
            full_name=fake.name(),
            password_hash=password_hash,
            role=role,
            is_active=is_active,
            email_verified=email_verified,
            created_at=datetime.utcnow()
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        created_users.append(user)
        
        return user
    
    yield _create_user
    
    # Cleanup
    for user in created_users:
        db_session.delete(user)
    db_session.commit()

@pytest.fixture(scope="function")
def authentication_scenario_complex(db_session, sample_user_factory):
    """Complex authentication scenario with various user states"""
    auth_service = AuthService()
    
    users = {
        'active_verified': sample_user_factory(
            email="active@example.com",
            is_active=True,
            email_verified=True
        ),
        'active_unverified': sample_user_factory(
            email="unverified@example.com",
            is_active=True,
            email_verified=False
        ),
        'inactive_verified': sample_user_factory(
            email="inactive@example.com",
            is_active=False,
            email_verified=True
        ),
        'oauth_user': sample_user_factory(
            email="oauth@example.com",
            password=None,  # OAuth-only user
            is_active=True,
            email_verified=True
        ),
        'admin_user': sample_user_factory(
            email="admin@example.com",
            role="admin",
            is_active=True,
            email_verified=True
        )
    }
    
    # Generate tokens for active users with passwords
    tokens = {}
    for user_type, user in users.items():
        if user.is_active and user.password_hash:
            try:
                token_data = {"sub": str(user.id), "email": user.email}
                tokens[user_type] = auth_service.create_access_token(token_data)
            except Exception:
                # Skip token creation if it fails
                pass
    
    return {
        'users': users,
        'tokens': tokens,
        'auth_service': auth_service
    }

# Content processing fixtures

@pytest.fixture(scope="function")
def content_processor():
    """Provide ContentProcessor instance for testing"""
    return ContentProcessor()

@pytest.fixture(scope="function")
def content_factory(db_session):
    """Factory for creating test content items"""
    created_content = []
    
    def _create_content(
        title: Optional[str] = None,
        content_type: str = "video",
        source: str = "youtube",
        difficulty_level: str = "beginner",
        topics: Optional[List[str]] = None
    ) -> ContentItem:
        if title is None:
            title = fake.sentence(nb_words=4)
        if topics is None:
            topics = fake.random_elements(
                elements=["AI", "Machine Learning", "Python", "Web Development"],
                length=2,
                unique=True
            )
        
        content = ContentItem(
            title=title,
            description=fake.text(max_nb_chars=200),
            content_type=content_type,
            source=source,
            source_id=fake.uuid4(),
            url=fake.url(),
            duration_minutes=fake.random_int(min=5, max=120),
            difficulty_level=difficulty_level,
            topics=topics,
            language="en",
            status="approved",
            created_at=datetime.utcnow()
        )
        
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        created_content.append(content)
        
        return content
    
    yield _create_content
    
    # Cleanup
    for content in created_content:
        db_session.delete(content)
    db_session.commit()

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

# Security testing fixtures

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
        'malicious_files': [
            {'name': 'malware.exe', 'content': b'MZ\x90\x00'},  # PE header
            {'name': 'script.js', 'content': b'eval(atob("malicious"))'},  # Base64 eval
            {'name': 'shell.php', 'content': b'<?php system($_GET["cmd"]); ?>'}
        ],
        'safe_inputs': [
            "normal@example.com",
            "user with spaces",
            "user123@domain.co.uk",
            "Normal text content",
            "Text with <b>HTML</b> tags"
        ]
    }

# Learning scenario fixtures

@pytest.fixture(scope="function")
def learning_scenario_basic(db_session, sample_user_factory, content_factory):
    """Basic learning scenario with user, preferences, and content"""
    user = sample_user_factory(email="learner@example.com")
    
    preferences = UserPreferences(
        user_id=user.id,
        learning_domains=["AI", "Python"],
        skill_levels={"AI": "beginner", "Python": "intermediate"},
        preferred_content_types=["video", "article"],
        time_constraints={"max_duration": 60, "sessions_per_week": 3}
    )
    db_session.add(preferences)
    db_session.commit()
    
    content_items = [
        content_factory(
            title="Introduction to Machine Learning",
            topics=["AI", "Machine Learning"],
            difficulty_level="beginner"
        ),
        content_factory(
            title="Advanced Python Programming",
            topics=["Python", "Programming"],
            difficulty_level="advanced"
        ),
        content_factory(
            title="Web Development Basics",
            topics=["Web Development", "HTML"],
            difficulty_level="beginner"
        )
    ]
    
    return {
        'user': user,
        'preferences': preferences,
        'content_items': content_items
    }

@pytest.fixture(scope="function")
def learning_scenario_advanced(db_session, sample_user_factory, content_factory):
    """Advanced learning scenario with multiple users and interactions"""
    users = [
        sample_user_factory(email="beginner@example.com"),
        sample_user_factory(email="intermediate@example.com"),
        sample_user_factory(email="advanced@example.com")
    ]
    
    preferences = []
    skill_levels = ["beginner", "intermediate", "advanced"]
    domains = [["AI", "Python"], ["Web Development", "Data Science"], ["AI", "Machine Learning"]]
    
    for i, user in enumerate(users):
        pref = UserPreferences(
            user_id=user.id,
            learning_domains=domains[i],
            skill_levels={domain: skill_levels[i] for domain in domains[i]},
            preferred_content_types=["video", "article"],
            time_constraints={"max_duration": 60, "sessions_per_week": 3}
        )
        db_session.add(pref)
        preferences.append(pref)
    
    db_session.commit()
    
    # Create diverse content
    content_items = []
    topics_by_level = {
        "beginner": [["Python", "Basics"], ["AI", "Introduction"]],
        "intermediate": [["Python", "OOP"], ["Data Science", "Pandas"]],
        "advanced": [["AI", "Deep Learning"], ["Machine Learning", "Neural Networks"]]
    }
    
    for level, topic_sets in topics_by_level.items():
        for topics in topic_sets:
            content_items.append(content_factory(
                topics=topics,
                difficulty_level=level
            ))
    
    return {
        'users': users,
        'preferences': preferences,
        'content_items': content_items
    }

# Performance testing fixtures

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

# Async testing fixtures

@pytest.fixture(scope="function")
def celery_app():
    """Provide Celery app for testing"""
    from services.celery_app import create_celery_app
    
    app = create_celery_app()
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True
    
    return app

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

# Data generation fixtures

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

# Database scenario fixtures

@pytest.fixture(scope="function")
def database_scenario_complex(db_session, sample_user_factory, content_factory):
    """Complex database scenario with relationships and constraints"""
    # Create users
    users = [sample_user_factory() for _ in range(5)]
    
    # Create content items
    content_items = [content_factory() for _ in range(10)]
    
    # Create user preferences
    preferences = []
    for user in users:
        pref = UserPreferences(
            user_id=user.id,
            learning_domains=fake.random_elements(
                elements=["AI", "Web Development", "Data Science", "Mobile Development"],
                length=2,
                unique=True
            ),
            skill_levels={"AI": "beginner", "Python": "intermediate"},
            preferred_content_types=["video", "article"],
            time_constraints={"max_duration": 60, "sessions_per_week": 3}
        )
        db_session.add(pref)
        preferences.append(pref)
    
    db_session.commit()
    
    return {
        'users': users,
        'content_items': content_items,
        'preferences': preferences,
        'interactions': [],  # Can be extended
        'recommendations': []  # Can be extended
    }

# Mutation testing support fixtures

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