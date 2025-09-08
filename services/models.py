"""
Database Models
SQLAlchemy models for HeadStart application

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Define database schema and relationships for users, content, and recommendations
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from services.database import Base

class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # NULL for OAuth-only users
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default='learner', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    interactions = relationship("UserInteraction", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    learning_sessions = relationship("LearningSession", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

class UserPreferences(Base):
    """User learning preferences and goals"""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    learning_domains = Column(ARRAY(String), default=list)  # ['AI', 'Web Dev', etc.]
    skill_levels = Column(JSONB, default=dict)  # {"AI": "beginner", "Python": "intermediate"}
    preferred_content_types = Column(ARRAY(String), default=list)  # ['video', 'article', 'paper']
    time_constraints = Column(JSONB, default=dict)  # {"max_duration": 30, "sessions_per_week": 3}
    language_preferences = Column(ARRAY(String), default=['en'])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, domains={self.learning_domains})>"

class ContentItem(Base):
    """Content items from various sources"""
    __tablename__ = "content_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    content_type = Column(String(50), nullable=False)  # 'video', 'article', 'paper', 'course'
    source = Column(String(100), nullable=False)  # 'youtube', 'arxiv', 'upload'
    source_id = Column(String(255))  # External ID from source
    url = Column(String(1000))
    duration_minutes = Column(Integer)
    difficulty_level = Column(String(20))  # 'beginner', 'intermediate', 'advanced'
    topics = Column(ARRAY(String), default=list)  # Array of topic tags
    language = Column(String(10), default='en')
    metadata = Column(JSONB, default=dict)  # Source-specific metadata
    embedding = Column(Vector(1536))  # OpenAI embedding dimension
    status = Column(String(20), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    interactions = relationship("UserInteraction", back_populates="content")
    recommendations = relationship("Recommendation", back_populates="content")
    learning_sessions = relationship("LearningSession", back_populates="content")
    
    def __repr__(self):
        return f"<ContentItem(id={self.id}, title={self.title[:50]}, type={self.content_type})>"

class UserInteraction(Base):
    """User interactions with content"""
    __tablename__ = "user_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey('content_items.id', ondelete='CASCADE'), nullable=False)
    interaction_type = Column(String(50), nullable=False)  # 'view', 'like', 'dislike', 'complete', 'bookmark'
    rating = Column(Integer)  # 1-5 rating
    feedback_text = Column(Text)
    time_spent_minutes = Column(Integer)
    completion_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    content = relationship("ContentItem", back_populates="interactions")
    
    def __repr__(self):
        return f"<UserInteraction(user_id={self.user_id}, content_id={self.content_id}, type={self.interaction_type})>"

class Recommendation(Base):
    """Recommendation log and explanations"""
    __tablename__ = "recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey('content_items.id', ondelete='CASCADE'), nullable=False)
    recommendation_score = Column(Float, nullable=False)
    explanation_factors = Column(JSONB, default=dict)  # Factors that influenced the recommendation
    algorithm_version = Column(String(50))
    shown_at = Column(DateTime(timezone=True), server_default=func.now())
    clicked_at = Column(DateTime(timezone=True))
    feedback_rating = Column(Integer)  # User feedback on recommendation quality
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    content = relationship("ContentItem", back_populates="recommendations")
    
    def __repr__(self):
        return f"<Recommendation(user_id={self.user_id}, content_id={self.content_id}, score={self.recommendation_score})>"

class LearningSession(Base):
    """Learning session tracking"""
    __tablename__ = "learning_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey('content_items.id', ondelete='CASCADE'), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    progress_percentage = Column(Float, default=0.0)
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="learning_sessions")
    content = relationship("ContentItem", back_populates="learning_sessions")
    
    def __repr__(self):
        return f"<LearningSession(user_id={self.user_id}, content_id={self.content_id}, progress={self.progress_percentage})>"

# Updated 2025-09-05: Core database models with relationships and pgvector support