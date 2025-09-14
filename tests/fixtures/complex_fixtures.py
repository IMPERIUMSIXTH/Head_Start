"""
Complex pytest fixtures for advanced testing scenarios
Provides sophisticated test data and mock configurations

Author: HeadStart Development Team
Created: 2025-09-08
Purpose: Complex fixtures for enhanced testing capabilities
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
from faker import Faker
from factory import Factory, Sequence, SubFactory, LazyAttribute
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.orm import Session

from services.models import User, ContentItem, UserPreferences, UserInteraction, Recommendation
from services.auth import AuthService

fake = Faker()

# Factory classes for generating test data

class UserFactory(SQLAlchemyModelFactory):
    """Factory for creating User instances"""
    
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    email = Sequence(lambda n: f"user{n}@example.com")
    full_name = LazyAttribute(lambda obj: fake.name())
    password_hash = LazyAttribute(lambda obj: AuthService().hash_password("TestPassword123!"))
    role = "learner"
    is_active = True
    email_verified = True
    created_at = LazyAttribute(lambda obj: fake.date_time_between(start_date='-1y', end_date='now'))

class ContentItemFactory(SQLAlchemyModelFactory):
    """Factory for creating ContentItem instances"""
    
    class Meta:
        model = ContentItem
        sqlalchemy_session_persistence = "commit"
    
    title = LazyAttribute(lambda obj: fake.sentence(nb_words=4))
    description = LazyAttribute(lambda obj: fake.text(max_nb_chars=200))
    content_type = "video"
    source = "youtube"
    source_id = Sequence(lambda n: f"test_id_{n}")
    url = LazyAttribute(lambda obj: fake.url())
    duration_minutes = LazyAttribute(lambda obj: fake.random_int(min=5, max=120))
    difficulty_level = LazyAttribute(lambda obj: fake.random_element(elements=["beginner", "intermediate", "advanced"]))
    topics = LazyAttribute(lambda obj: fake.random_elements(
        elements=["AI", "Machine Learning", "Python", "Web Development", "Data Science"],
        length=fake.random_int(min=1, max=3),
        unique=True
    ))
    language = "en"
    status = "approved"

class UserPreferencesFactory(SQLAlchemyModelFactory):
    """Factory for creating UserPreferences instances"""
    
    class Meta:
        model = UserPreferences
        sqlalchemy_session_persistence = "commit"
    
    user = SubFactory(UserFactory)
    learning_domains = LazyAttribute(lambda obj: fake.random_elements(
        elements=["AI", "Web Development", "Data Science", "Mobile Development"],
        length=fake.random_int(min=1, max=3),
        unique=True
    ))
    skill_levels = LazyAttribute(lambda obj: {
        domain: fake.random_element(elements=["beginner", "intermediate", "advanced"])
        for domain in obj.learning_domains
    })
    preferred_content_types = LazyAttribute(lambda obj: fake.random_elements(
        elements=["video", "article", "tutorial", "course"],
        length=fake.random_int(min=1, max=3),
        unique=True
    ))
    time_constraints = LazyAttribute(lambda obj: {
        "max_duration": fake.random_int(min=15, max=120),
        "sessions_per_week": fake.random_int(min=1, max=7)
    })

# Complex fixture scenarios

@pytest.fixture
def learning_scenario_basic(db_session):
    """Basic learning scenario with user, preferences, and content"""
    # Create user with preferences
    user = UserFactory(db_session=db_session)
    preferences = UserPreferencesFactory(user=user, db_session=db_session)
    
    # Create relevant content
    content_items = [
        ContentItemFactory(
            title="Introduction to Machine Learning",
            topics=["AI", "Machine Learning"],
            difficulty_level="beginner",
            db_session=db_session
        ),
        ContentItemFactory(
            title="Advanced Python Programming",
            topics=["Python", "Programming"],
            difficulty_level="advanced",
            db_session=db_session
        ),
        ContentItemFactory(
            title="Web Development Basics",
            topics=["Web Development", "HTML", "CSS"],
            difficulty_level="beginner",
            db_session=db_session
        )
    ]
    
    return {
        'user': user,
        'preferences': preferences,
        'content_items': content_items
    }

@pytest.fixture
def learning_scenario_advanced(db_session):
    """Advanced learning scenario with interactions and recommendations"""
    # Create multiple users with different preferences
    users = [
        UserFactory(
            email="beginner@example.com",
            full_name="Beginner User",
            db_session=db_session
        ),
        UserFactory(
            email="intermediate@example.com",
            full_name="Intermediate User",
            db_session=db_session
        ),
        UserFactory(
            email="advanced@example.com",
            full_name="Advanced User",
            db_session=db_session
        )
    ]
    
    # Create preferences for each user
    preferences = [
        UserPreferencesFactory(
            user=users[0],
            learning_domains=["AI", "Python"],
            skill_levels={"AI": "beginner", "Python": "beginner"},
            db_session=db_session
        ),
        UserPreferencesFactory(
            user=users[1],
            learning_domains=["Web Development", "Data Science"],
            skill_levels={"Web Development": "intermediate", "Data Science": "intermediate"},
            db_session=db_session
        ),
        UserPreferencesFactory(
            user=users[2],
            learning_domains=["AI", "Machine Learning"],
            skill_levels={"AI": "advanced", "Machine Learning": "advanced"},
            db_session=db_session
        )
    ]
    
    # Create diverse content
    content_items = []
    topics_by_level = {
        "beginner": [["Python", "Basics"], ["AI", "Introduction"], ["Web Development", "HTML"]],
        "intermediate": [["Python", "OOP"], ["Data Science", "Pandas"], ["Web Development", "JavaScript"]],
        "advanced": [["AI", "Deep Learning"], ["Machine Learning", "Neural Networks"], ["Python", "Async"]]
    }
    
    for level, topic_sets in topics_by_level.items():
        for topics in topic_sets:
            content_items.append(ContentItemFactory(
                topics=topics,
                difficulty_level=level,
                db_session=db_session
            ))
    
    return {
        'users': users,
        'preferences': preferences,
        'content_items': content_items
    }

@pytest.fixture
def authentication_scenario_complex(db_session):
    """Complex authentication scenario with various user states"""
    auth_service = AuthService()
    
    users = {
        'active_verified': UserFactory(
            email="active@example.com",
            is_active=True,
            email_verified=True,
            db_session=db_session
        ),
        'active_unverified': UserFactory(
            email="unverified@example.com",
            is_active=True,
            email_verified=False,
            db_session=db_session
        ),
        'inactive_verified': UserFactory(
            email="inactive@example.com",
            is_active=False,
            email_verified=True,
            db_session=db_session
        ),
        'oauth_user': UserFactory(
            email="oauth@example.com",
            password_hash=None,  # OAuth-only user
            is_active=True,
            email_verified=True,
            db_session=db_session
        ),
        'admin_user': UserFactory(
            email="admin@example.com",
            role="admin",
            is_active=True,
            email_verified=True,
            db_session=db_session
        )
    }
    
    # Generate tokens for active users
    tokens = {}
    for user_type, user in users.items():
        if user.is_active and user.password_hash:
            tokens[user_type] = auth_service.create_token_pair(user)
    
    return {
        'users': users,
        'tokens': tokens,
        'auth_service': auth_service
    }

@pytest.fixture
def content_processing_scenario(mock_external_apis):
    """Complex content processing scenario with various content types"""
    scenarios = {
        'youtube_success': {
            'url': 'https://www.youtube.com/watch?v=success123',
            'expected_result': {
                'title': 'Test Video',
                'content_type': 'video',
                'source': 'youtube',
                'duration_minutes': 16
            }
        },
        'youtube_not_found': {
            'url': 'https://www.youtube.com/watch?v=notfound123',
            'mock_response': {'items': []},
            'expected_error': 'Video not found'
        },
        'arxiv_success': {
            'arxiv_id': '2301.00001',
            'expected_result': {
                'title': 'Test Paper',
                'content_type': 'paper',
                'source': 'arxiv'
            }
        },
        'api_failure': {
            'url': 'https://www.youtube.com/watch?v=failure123',
            'mock_error': Exception("API Error"),
            'expected_error': 'ContentProcessingError'
        }
    }
    
    return scenarios

@pytest.fixture
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

@pytest.fixture
def security_test_scenarios():
    """Security testing scenarios with various attack vectors"""
    return {
        'sql_injection': {
            'payloads': [
                "'; DROP TABLE users; --",
                "' OR '1'='1' --",
                "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --",
                "' UNION SELECT * FROM users --",
                "'; UPDATE users SET role='admin' WHERE email='victim@example.com'; --"
            ],
            'safe_inputs': [
                "normal@example.com",
                "user with spaces",
                "user123@domain.co.uk"
            ]
        },
        'xss_attacks': {
            'payloads': [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "<svg onload=alert('xss')>",
                "';alert('xss');//"
            ],
            'safe_inputs': [
                "Normal text content",
                "Text with <b>HTML</b> tags",
                "Email: user@example.com"
            ]
        },
        'authentication_attacks': {
            'brute_force': {
                'username': 'admin@example.com',
                'passwords': ['password', '123456', 'admin', 'password123', 'qwerty']
            },
            'token_manipulation': {
                'invalid_tokens': [
                    'invalid.token.here',
                    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid',
                    '',
                    'Bearer invalid'
                ]
            }
        }
    }

@pytest.fixture
def mock_external_services():
    """Comprehensive mock for all external services"""
    mocks = {
        'openai': AsyncMock(),
        'youtube_api': Mock(),
        'arxiv_api': Mock(),
        'email_service': AsyncMock(),
        'redis': Mock(),
        'celery': Mock()
    }
    
    # Configure OpenAI mock
    mocks['openai'].Embedding.acreate.return_value = {
        'data': [{'embedding': [0.1] * 1536}]
    }
    
    # Configure YouTube API mock
    mocks['youtube_api'].get.return_value.json.return_value = {
        'items': [{
            'snippet': {
                'title': 'Mock Video Title',
                'description': 'Mock video description',
                'tags': ['test', 'mock'],
                'channelTitle': 'Mock Channel',
                'publishedAt': '2023-01-01T00:00:00Z'
            },
            'contentDetails': {'duration': 'PT15M33S'},
            'statistics': {'viewCount': '1000', 'likeCount': '100'}
        }]
    }
    
    # Configure arXiv API mock
    mocks['arxiv_api'].get.return_value.content = '''<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <entry>
            <title>Mock Paper Title</title>
            <summary>Mock paper abstract</summary>
            <author><name>Mock Author</name></author>
            <category term="cs.AI"/>
        </entry>
    </feed>'''.encode()
    
    # Configure email service mock
    mocks['email_service'].send_email.return_value = {'status': 'sent', 'message_id': 'mock123'}
    
    # Configure Redis mock
    mocks['redis'].get.return_value = None
    mocks['redis'].set.return_value = True
    mocks['redis'].delete.return_value = 1
    
    # Configure Celery mock
    mocks['celery'].send_task.return_value = Mock(id='mock_task_id', status='SUCCESS')
    
    return mocks

@pytest.fixture
def database_scenario_complex(db_session):
    """Complex database scenario with relationships and constraints"""
    # Create users with various states
    users = [UserFactory(db_session=db_session) for _ in range(5)]
    
    # Create content items
    content_items = [ContentItemFactory(db_session=db_session) for _ in range(10)]
    
    # Create user preferences
    preferences = [
        UserPreferencesFactory(user=user, db_session=db_session) 
        for user in users
    ]
    
    # Create user interactions
    interactions = []
    for user in users:
        for content in content_items[:3]:  # Each user interacts with first 3 content items
            interaction = UserInteraction(
                user_id=user.id,
                content_id=content.id,
                interaction_type=fake.random_element(elements=["view", "like", "bookmark"]),
                rating=fake.random_int(min=1, max=5),
                time_spent_minutes=fake.random_int(min=5, max=60),
                completion_percentage=fake.random_int(min=10, max=100)
            )
            db_session.add(interaction)
            interactions.append(interaction)
    
    # Create recommendations
    recommendations = []
    for user in users:
        for content in content_items[3:6]:  # Recommend different content
            recommendation = Recommendation(
                user_id=user.id,
                content_id=content.id,
                recommendation_score=fake.random.uniform(0.1, 1.0),
                explanation_factors={
                    "topic_match": fake.random.uniform(0.5, 1.0),
                    "difficulty_match": fake.random.uniform(0.3, 1.0),
                    "user_history": fake.random.uniform(0.2, 0.9)
                },
                algorithm_version="v1.0"
            )
            db_session.add(recommendation)
            recommendations.append(recommendation)
    
    db_session.commit()
    
    return {
        'users': users,
        'content_items': content_items,
        'preferences': preferences,
        'interactions': interactions,
        'recommendations': recommendations
    }

@pytest.fixture
def async_scenario_complex():
    """Complex async testing scenario"""
    return {
        'concurrent_operations': 10,
        'operation_delay': 0.1,
        'timeout_threshold': 1.0,
        'retry_attempts': 3,
        'circuit_breaker_threshold': 5
    }