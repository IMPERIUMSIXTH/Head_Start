"""
Unit Tests for User Management API
Test user preferences, dashboard, and feedback endpoints

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Test user management API functionality
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.database import Base, get_db
from services.models import User, UserPreferences, ContentItem, UserInteraction
from services.auth import auth_service
from main import app
import uuid

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_user_api.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    """Create test client"""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

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
    password_hash = auth_service.hash_password("TestPassword123!")
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=password_hash,
        role="learner",
        is_active=True,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(sample_user):
    """Create authentication headers"""
    tokens = auth_service.create_token_pair(sample_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}

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

@pytest.fixture
def sample_preferences(db_session, sample_user):
    """Create sample user preferences"""
    preferences = UserPreferences(
        user_id=sample_user.id,
        learning_domains=["AI", "Machine Learning"],
        skill_levels={"AI": "beginner", "Python": "intermediate"},
        preferred_content_types=["video", "article"],
        time_constraints={"max_duration": 45, "sessions_per_week": 3},
        language_preferences=["en"]
    )
    db_session.add(preferences)
    db_session.commit()
    db_session.refresh(preferences)
    return preferences

class TestUserDashboard:
    """Test user dashboard endpoint"""
    
    def test_get_dashboard_success(self, client, auth_headers, sample_preferences):
        """Test successful dashboard retrieval"""
        response = client.get("/api/user/dashboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_profile" in data
        assert "learning_stats" in data
        assert "recent_activity" in data
        assert "progress_metrics" in data
        assert "recommendations_count" in data
        
        # Check user profile data
        assert data["user_profile"]["full_name"] == "Test User"
        assert data["user_profile"]["email"] == "test@example.com"
        assert "AI" in data["user_profile"]["learning_domains"]
    
    def test_get_dashboard_unauthorized(self, client):
        """Test dashboard access without authentication"""
        response = client.get("/api/user/dashboard")
        
        assert response.status_code == 401
    
    def test_get_dashboard_with_interactions(self, client, auth_headers, sample_user, sample_content, db_session):
        """Test dashboard with user interactions"""
        # Create some interactions
        interaction1 = UserInteraction(
            user_id=sample_user.id,
            content_id=sample_content.id,
            interaction_type="view",
            rating=4,
            time_spent_minutes=25,
            completion_percentage=75.0
        )
        
        interaction2 = UserInteraction(
            user_id=sample_user.id,
            content_id=sample_content.id,
            interaction_type="complete",
            rating=5,
            time_spent_minutes=30,
            completion_percentage=100.0
        )
        
        db_session.add_all([interaction1, interaction2])
        db_session.commit()
        
        response = client.get("/api/user/dashboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["learning_stats"]["total_interactions"] == 2
        assert data["learning_stats"]["completed_content"] == 1
        assert data["learning_stats"]["total_time_spent_minutes"] == 55
        assert len(data["recent_activity"]) == 2

class TestUserPreferences:
    """Test user preferences endpoints"""
    
    def test_get_preferences_success(self, client, auth_headers, sample_preferences):
        """Test successful preferences retrieval"""
        response = client.get("/api/user/preferences", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["learning_domains"] == ["AI", "Machine Learning"]
        assert data["skill_levels"]["AI"] == "beginner"
        assert data["preferred_content_types"] == ["video", "article"]
        assert data["language_preferences"] == ["en"]
    
    def test_get_preferences_not_found(self, client, auth_headers):
        """Test preferences retrieval when none exist"""
        response = client.get("/api/user/preferences", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_update_preferences_create_new(self, client, auth_headers):
        """Test creating new preferences"""
        preferences_data = {
            "learning_domains": ["Data Science", "AI"],
            "skill_levels": {"Python": "advanced", "SQL": "intermediate"},
            "preferred_content_types": ["video", "tutorial"],
            "time_constraints": {"max_duration": 60, "sessions_per_week": 4},
            "language_preferences": ["en", "es"]
        }
        
        response = client.put("/api/user/preferences", json=preferences_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["learning_domains"] == ["Data Science", "AI"]
        assert data["skill_levels"]["Python"] == "advanced"
        assert data["preferred_content_types"] == ["video", "tutorial"]
        assert data["time_constraints"]["max_duration"] == 60
    
    def test_update_preferences_existing(self, client, auth_headers, sample_preferences):
        """Test updating existing preferences"""
        updated_data = {
            "learning_domains": ["Web Development", "DevOps"],
            "skill_levels": {"JavaScript": "intermediate", "Docker": "beginner"},
            "preferred_content_types": ["article", "documentation"],
            "time_constraints": {"max_duration": 30, "sessions_per_week": 5},
            "language_preferences": ["en"]
        }
        
        response = client.put("/api/user/preferences", json=updated_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["learning_domains"] == ["Web Development", "DevOps"]
        assert data["skill_levels"]["JavaScript"] == "intermediate"
    
    def test_update_preferences_invalid_domain(self, client, auth_headers):
        """Test updating preferences with invalid domain"""
        invalid_data = {
            "learning_domains": ["Invalid Domain"],
            "skill_levels": {},
            "preferred_content_types": ["video"],
            "time_constraints": {},
            "language_preferences": ["en"]
        }
        
        response = client.put("/api/user/preferences", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_update_preferences_invalid_skill_level(self, client, auth_headers):
        """Test updating preferences with invalid skill level"""
        invalid_data = {
            "learning_domains": ["AI"],
            "skill_levels": {"AI": "expert"},  # Invalid level
            "preferred_content_types": ["video"],
            "time_constraints": {},
            "language_preferences": ["en"]
        }
        
        response = client.put("/api/user/preferences", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error

class TestUserFeedback:
    """Test user feedback endpoint"""
    
    def test_submit_feedback_success(self, client, auth_headers, sample_content):
        """Test successful feedback submission"""
        feedback_data = {
            "content_id": str(sample_content.id),
            "interaction_type": "view",
            "rating": 4,
            "feedback_text": "Great content!",
            "time_spent_minutes": 25,
            "completion_percentage": 75.0
        }
        
        response = client.post("/api/user/feedback", json=feedback_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Feedback submitted successfully"
    
    def test_submit_feedback_content_not_found(self, client, auth_headers):
        """Test feedback submission for non-existent content"""
        feedback_data = {
            "content_id": str(uuid.uuid4()),
            "interaction_type": "view",
            "rating": 4
        }
        
        response = client.post("/api/user/feedback", json=feedback_data, headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_submit_feedback_invalid_interaction_type(self, client, auth_headers, sample_content):
        """Test feedback with invalid interaction type"""
        feedback_data = {
            "content_id": str(sample_content.id),
            "interaction_type": "invalid_type",
            "rating": 4
        }
        
        response = client.post("/api/user/feedback", json=feedback_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_submit_feedback_invalid_rating(self, client, auth_headers, sample_content):
        """Test feedback with invalid rating"""
        feedback_data = {
            "content_id": str(sample_content.id),
            "interaction_type": "view",
            "rating": 6  # Invalid rating (should be 1-5)
        }
        
        response = client.post("/api/user/feedback", json=feedback_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_submit_feedback_minimal_data(self, client, auth_headers, sample_content):
        """Test feedback submission with minimal required data"""
        feedback_data = {
            "content_id": str(sample_content.id),
            "interaction_type": "bookmark"
        }
        
        response = client.post("/api/user/feedback", json=feedback_data, headers=auth_headers)
        
        assert response.status_code == 200

class TestUserProgress:
    """Test user progress endpoint"""
    
    def test_get_progress_success(self, client, auth_headers, sample_preferences):
        """Test successful progress retrieval"""
        response = client.get("/api/user/progress", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "domain_progress" in data
        assert "recent_sessions" in data
        assert "overall_stats" in data
    
    def test_get_progress_with_data(self, client, auth_headers, sample_user, sample_content, sample_preferences, db_session):
        """Test progress retrieval with actual data"""
        # Create some interactions
        interaction = UserInteraction(
            user_id=sample_user.id,
            content_id=sample_content.id,
            interaction_type="complete",
            rating=5,
            time_spent_minutes=30,
            completion_percentage=100.0
        )
        db_session.add(interaction)
        db_session.commit()
        
        response = client.get("/api/user/progress", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check domain progress
        assert "AI" in data["domain_progress"]
        assert data["domain_progress"]["AI"]["total_interactions"] == 1
        assert data["domain_progress"]["AI"]["completed_content"] == 1
        assert data["domain_progress"]["AI"]["completion_rate"] == 100.0

# Updated 2025-09-05: Comprehensive user management API tests