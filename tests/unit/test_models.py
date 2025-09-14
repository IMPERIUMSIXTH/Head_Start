"""
Unit Tests for Database Models
Test database models and relationships

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Test database models, relationships, and constraints
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.database import Base
from services.models import User, UserPreferences, ContentItem, UserInteraction, Recommendation, LearningSession

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
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
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash="hashed_password",
        role="learner",
        is_active=True,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_content(db_session):
    """Create sample content for testing"""
    content = ContentItem(
        title="Test Content",
        description="Test description",
        content_type="video",
        source="youtube",
        source_id="test123",
        url="https://youtube.com/watch?v=test123",
        duration_minutes=30,
        difficulty_level="beginner",
        topics=["AI", "Machine Learning"],
        language="en",
        status="approved"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)
    return content

class TestUserModel:
    """Test User model"""
    
    def test_create_user(self, db_session):
        """Test creating a new user"""
        user = User(
            email="newuser@example.com",
            full_name="New User",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.role == "learner"  # Default role
        assert user.is_active is True  # Default active
        assert user.email_verified is False  # Default not verified
        assert user.created_at is not None
    
    def test_user_relationships(self, db_session, sample_user):
        """Test user relationships"""
        # Create user preferences
        preferences = UserPreferences(
            user_id=sample_user.id,
            learning_domains=["AI", "Web Development"],
            skill_levels={"AI": "beginner", "Python": "intermediate"}
        )
        db_session.add(preferences)
        db_session.commit()
        
        # Test relationship
        db_session.refresh(sample_user)
        assert sample_user.preferences is not None
        assert sample_user.preferences.learning_domains == ["AI", "Web Development"]

class TestUserPreferencesModel:
    """Test UserPreferences model"""
    
    def test_create_preferences(self, db_session, sample_user):
        """Test creating user preferences"""
        preferences = UserPreferences(
            user_id=sample_user.id,
            learning_domains=["Data Science", "AI"],
            skill_levels={"Python": "advanced", "SQL": "intermediate"},
            preferred_content_types=["video", "article"],
            time_constraints={"max_duration": 45, "sessions_per_week": 5},
            language_preferences=["en", "es"]
        )
        db_session.add(preferences)
        db_session.commit()
        
        assert preferences.id is not None
        assert preferences.user_id == sample_user.id
        assert "Data Science" in preferences.learning_domains
        assert preferences.skill_levels["Python"] == "advanced"
        assert preferences.time_constraints["max_duration"] == 45

class TestContentItemModel:
    """Test ContentItem model"""
    
    def test_create_content_item(self, db_session):
        """Test creating a content item"""
        content = ContentItem(
            title="Introduction to Machine Learning",
            description="A comprehensive guide to ML basics",
            content_type="video",
            source="youtube",
            source_id="abc123",
            url="https://youtube.com/watch?v=abc123",
            duration_minutes=60,
            difficulty_level="beginner",
            topics=["Machine Learning", "AI", "Python"],
            metadata={"channel": "ML Academy", "views": 10000}
        )
        db_session.add(content)
        db_session.commit()
        
        assert content.id is not None
        assert content.title == "Introduction to Machine Learning"
        assert content.content_type == "video"
        assert content.status == "pending"  # Default status
        assert "Machine Learning" in content.topics
        assert content.metadata["channel"] == "ML Academy"

class TestUserInteractionModel:
    """Test UserInteraction model"""
    
    def test_create_interaction(self, db_session, sample_user, sample_content):
        """Test creating user interaction"""
        interaction = UserInteraction(
            user_id=sample_user.id,
            content_id=sample_content.id,
            interaction_type="view",
            rating=4,
            feedback_text="Great content!",
            time_spent_minutes=25,
            completion_percentage=85.5
        )
        db_session.add(interaction)
        db_session.commit()
        
        assert interaction.id is not None
        assert interaction.user_id == sample_user.id
        assert interaction.content_id == sample_content.id
        assert interaction.interaction_type == "view"
        assert interaction.rating == 4
        assert interaction.completion_percentage == 85.5

class TestRecommendationModel:
    """Test Recommendation model"""
    
    def test_create_recommendation(self, db_session, sample_user, sample_content):
        """Test creating recommendation"""
        recommendation = Recommendation(
            user_id=sample_user.id,
            content_id=sample_content.id,
            recommendation_score=0.85,
            explanation_factors={
                "topic_match": 0.9,
                "difficulty_match": 0.8,
                "user_history": 0.7
            },
            algorithm_version="v1.0"
        )
        db_session.add(recommendation)
        db_session.commit()
        
        assert recommendation.id is not None
        assert recommendation.recommendation_score == 0.85
        assert recommendation.explanation_factors["topic_match"] == 0.9
        assert recommendation.algorithm_version == "v1.0"

class TestLearningSessionModel:
    """Test LearningSession model"""
    
    def test_create_learning_session(self, db_session, sample_user, sample_content):
        """Test creating learning session"""
        session = LearningSession(
            user_id=sample_user.id,
            content_id=sample_content.id,
            progress_percentage=75.0,
            notes="Good progress on ML concepts"
        )
        db_session.add(session)
        db_session.commit()
        
        assert session.id is not None
        assert session.user_id == sample_user.id
        assert session.content_id == sample_content.id
        assert session.progress_percentage == 75.0
        assert session.notes == "Good progress on ML concepts"

# Updated 2025-09-05: Comprehensive unit tests for database models