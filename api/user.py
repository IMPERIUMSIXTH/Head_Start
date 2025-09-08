"""
User Management API Routes
User profile, preferences, and dashboard endpoints

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: User management, preferences, and dashboard data endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime, timedelta
from services.database import get_db
from services.models import User, UserPreferences, UserInteraction, LearningSession, ContentItem, Recommendation
from services.dependencies import get_current_active_user, get_current_verified_user
from services.exceptions import ValidationError, NotFoundError

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models for request/response
class UserPreferencesCreate(BaseModel):
    learning_domains: List[str] = []
    skill_levels: Dict[str, str] = {}
    preferred_content_types: List[str] = []
    time_constraints: Dict[str, Any] = {}
    language_preferences: List[str] = ["en"]
    
    @validator('learning_domains')
    def validate_domains(cls, v):
        allowed_domains = [
            'AI', 'Machine Learning', 'Data Science', 'Web Development', 
            'Mobile Development', 'DevOps', 'Cybersecurity', 'Cloud Computing',
            'Database', 'Programming Languages', 'Software Engineering'
        ]
        for domain in v:
            if domain not in allowed_domains:
                raise ValueError(f'Invalid learning domain: {domain}')
        return v
    
    @validator('skill_levels')
    def validate_skill_levels(cls, v):
        allowed_levels = ['beginner', 'intermediate', 'advanced']
        for domain, level in v.items():
            if level not in allowed_levels:
                raise ValueError(f'Invalid skill level: {level}')
        return v
    
    @validator('preferred_content_types')
    def validate_content_types(cls, v):
        allowed_types = ['video', 'article', 'paper', 'course', 'tutorial', 'documentation']
        for content_type in v:
            if content_type not in allowed_types:
                raise ValueError(f'Invalid content type: {content_type}')
        return v

class UserPreferencesResponse(BaseModel):
    id: str
    learning_domains: List[str]
    skill_levels: Dict[str, str]
    preferred_content_types: List[str]
    time_constraints: Dict[str, Any]
    language_preferences: List[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

class UserDashboardResponse(BaseModel):
    user_profile: Dict[str, Any]
    learning_stats: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    progress_metrics: Dict[str, Any]
    recommendations_count: int

class UserFeedbackRequest(BaseModel):
    content_id: str
    interaction_type: str
    rating: Optional[int] = None
    feedback_text: Optional[str] = None
    time_spent_minutes: Optional[int] = None
    completion_percentage: Optional[float] = None
    
    @validator('interaction_type')
    def validate_interaction_type(cls, v):
        allowed_types = ['view', 'like', 'dislike', 'complete', 'bookmark', 'share']
        if v not in allowed_types:
            raise ValueError(f'Invalid interaction type: {v}')
        return v
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    @validator('completion_percentage')
    def validate_completion(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Completion percentage must be between 0 and 100')
        return v

@router.get("/dashboard", response_model=UserDashboardResponse)
async def get_user_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user dashboard with analytics and progress"""
    logger.info("Dashboard request", user_id=str(current_user.id))
    
    try:
        # Get user preferences
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        # Calculate learning stats
        total_interactions = db.query(UserInteraction).filter(
            UserInteraction.user_id == current_user.id
        ).count()
        
        completed_content = db.query(UserInteraction).filter(
            UserInteraction.user_id == current_user.id,
            UserInteraction.interaction_type == 'complete'
        ).count()
        
        total_time_spent = db.query(func.sum(UserInteraction.time_spent_minutes)).filter(
            UserInteraction.user_id == current_user.id
        ).scalar() or 0
        
        # Get recent activity (last 10 interactions)
        recent_interactions = db.query(UserInteraction).filter(
            UserInteraction.user_id == current_user.id
        ).order_by(desc(UserInteraction.created_at)).limit(10).all()
        
        recent_activity = []
        for interaction in recent_interactions:
            content = db.query(ContentItem).filter(
                ContentItem.id == interaction.content_id
            ).first()
            
            if content:
                recent_activity.append({
                    "content_title": content.title,
                    "content_type": content.content_type,
                    "interaction_type": interaction.interaction_type,
                    "created_at": interaction.created_at.isoformat(),
                    "rating": interaction.rating,
                    "completion_percentage": interaction.completion_percentage
                })
        
        # Calculate learning streak (days with activity in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_days = db.query(func.date(UserInteraction.created_at)).filter(
            UserInteraction.user_id == current_user.id,
            UserInteraction.created_at >= thirty_days_ago
        ).distinct().count()
        
        # Get recommendations count
        recommendations_count = db.query(Recommendation).filter(
            Recommendation.user_id == current_user.id
        ).count()
        
        # Build response
        dashboard_data = UserDashboardResponse(
            user_profile={
                "id": str(current_user.id),
                "full_name": current_user.full_name,
                "email": current_user.email,
                "role": current_user.role,
                "learning_domains": preferences.learning_domains if preferences else [],
                "skill_levels": preferences.skill_levels if preferences else {}
            },
            learning_stats={
                "total_interactions": total_interactions,
                "completed_content": completed_content,
                "total_time_spent_minutes": int(total_time_spent),
                "active_days_last_30": active_days,
                "completion_rate": round((completed_content / max(total_interactions, 1)) * 100, 1)
            },
            recent_activity=recent_activity,
            progress_metrics={
                "weekly_goal_progress": 0,  # TODO: Implement weekly goals
                "skill_progression": {},    # TODO: Implement skill tracking
                "learning_streak": active_days
            },
            recommendations_count=recommendations_count
        )
        
        logger.info("Dashboard data retrieved", user_id=str(current_user.id))
        return dashboard_data
        
    except Exception as e:
        logger.error("Dashboard retrieval failed", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user learning preferences"""
    logger.info("Preferences request", user_id=str(current_user.id))
    
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User preferences not found"
        )
    
    return UserPreferencesResponse(
        id=str(preferences.id),
        learning_domains=preferences.learning_domains,
        skill_levels=preferences.skill_levels,
        preferred_content_types=preferences.preferred_content_types,
        time_constraints=preferences.time_constraints,
        language_preferences=preferences.language_preferences,
        created_at=preferences.created_at.isoformat(),
        updated_at=preferences.updated_at.isoformat()
    )

@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user learning preferences"""
    logger.info("Preferences update", user_id=str(current_user.id))
    
    try:
        # Get existing preferences or create new
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        if preferences:
            # Update existing preferences
            preferences.learning_domains = preferences_data.learning_domains
            preferences.skill_levels = preferences_data.skill_levels
            preferences.preferred_content_types = preferences_data.preferred_content_types
            preferences.time_constraints = preferences_data.time_constraints
            preferences.language_preferences = preferences_data.language_preferences
        else:
            # Create new preferences
            preferences = UserPreferences(
                user_id=current_user.id,
                learning_domains=preferences_data.learning_domains,
                skill_levels=preferences_data.skill_levels,
                preferred_content_types=preferences_data.preferred_content_types,
                time_constraints=preferences_data.time_constraints,
                language_preferences=preferences_data.language_preferences
            )
            db.add(preferences)
        
        db.commit()
        db.refresh(preferences)
        
        logger.info("Preferences updated", user_id=str(current_user.id))
        
        return UserPreferencesResponse(
            id=str(preferences.id),
            learning_domains=preferences.learning_domains,
            skill_levels=preferences.skill_levels,
            preferred_content_types=preferences.preferred_content_types,
            time_constraints=preferences.time_constraints,
            language_preferences=preferences.language_preferences,
            created_at=preferences.created_at.isoformat(),
            updated_at=preferences.updated_at.isoformat()
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Preferences update failed", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )

@router.post("/feedback")
async def submit_user_feedback(
    feedback: UserFeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit user feedback for content"""
    logger.info("Feedback submission", user_id=str(current_user.id), content_id=feedback.content_id)
    
    try:
        # Verify content exists
        content = db.query(ContentItem).filter(ContentItem.id == feedback.content_id).first()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        # Create interaction record
        interaction = UserInteraction(
            user_id=current_user.id,
            content_id=feedback.content_id,
            interaction_type=feedback.interaction_type,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text,
            time_spent_minutes=feedback.time_spent_minutes,
            completion_percentage=feedback.completion_percentage or 0.0
        )
        
        db.add(interaction)
        db.commit()
        
        logger.info("Feedback submitted", 
                   user_id=str(current_user.id), 
                   content_id=feedback.content_id,
                   interaction_type=feedback.interaction_type)
        
        return {"message": "Feedback submitted successfully"}
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Feedback submission failed", error=str(e), 
                    user_id=str(current_user.id), content_id=feedback.content_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )

@router.get("/progress")
async def get_user_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed user learning progress"""
    logger.info("Progress request", user_id=str(current_user.id))
    
    try:
        # Get learning sessions
        sessions = db.query(LearningSession).filter(
            LearningSession.user_id == current_user.id
        ).order_by(desc(LearningSession.started_at)).limit(50).all()
        
        # Calculate progress by domain
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        domain_progress = {}
        if preferences:
            for domain in preferences.learning_domains:
                # Count interactions with content in this domain
                domain_interactions = db.query(UserInteraction).join(ContentItem).filter(
                    UserInteraction.user_id == current_user.id,
                    ContentItem.topics.contains([domain])
                ).count()
                
                completed_in_domain = db.query(UserInteraction).join(ContentItem).filter(
                    UserInteraction.user_id == current_user.id,
                    UserInteraction.interaction_type == 'complete',
                    ContentItem.topics.contains([domain])
                ).count()
                
                domain_progress[domain] = {
                    "total_interactions": domain_interactions,
                    "completed_content": completed_in_domain,
                    "completion_rate": round((completed_in_domain / max(domain_interactions, 1)) * 100, 1)
                }
        
        # Format sessions for response
        session_data = []
        for session in sessions:
            content = db.query(ContentItem).filter(ContentItem.id == session.content_id).first()
            if content:
                session_data.append({
                    "content_title": content.title,
                    "content_type": content.content_type,
                    "started_at": session.started_at.isoformat(),
                    "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                    "progress_percentage": session.progress_percentage,
                    "notes": session.notes
                })
        
        return {
            "domain_progress": domain_progress,
            "recent_sessions": session_data,
            "overall_stats": {
                "total_sessions": len(sessions),
                "average_session_progress": sum(s.progress_percentage for s in sessions) / max(len(sessions), 1)
            }
        }
        
    except Exception as e:
        logger.error("Progress retrieval failed", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve progress data"
        )

# Updated 2025-09-05: Complete user management API with preferences and dashboard