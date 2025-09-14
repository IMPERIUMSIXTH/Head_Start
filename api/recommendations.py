"""
Recommendations API Routes
Personalized content recommendation endpoints

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: API endpoints for generating and managing personalized content recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import structlog
from services.database import get_db
from services.models import User, Recommendation, ContentItem
from services.dependencies import get_current_active_user, get_current_verified_user
from services.recommendations import RecommendationEngine
from services.exceptions import ExternalServiceError
from services.ai_client import get_ai_client

logger = structlog.get_logger()
router = APIRouter()

# Initialize recommendation engine
recommendation_engine = RecommendationEngine()

# Pydantic models for request/response
class RecommendationResponse(BaseModel):
    content_id: str
    title: str
    description: Optional[str]
    content_type: str
    source: str
    url: Optional[str]
    duration_minutes: Optional[int]
    difficulty_level: Optional[str]
    topics: List[str]
    language: str
    recommendation_score: float
    explanation_factors: Dict[str, Any]
    created_at: str

class RecommendationFeedResponse(BaseModel):
    recommendations: List[RecommendationResponse]
    total_count: int
    algorithm_version: str
    generated_at: str

class RecommendationFeedbackRequest(BaseModel):
    recommendation_id: str
    feedback_rating: int
    feedback_type: Optional[str] = None
    
    @validator('feedback_rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Feedback rating must be between 1 and 5')
        return v
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        if v is not None:
            allowed_types = ['helpful', 'not_helpful', 'irrelevant', 'already_seen', 'not_interested']
            if v not in allowed_types:
                raise ValueError(f'Invalid feedback type. Allowed: {allowed_types}')
        return v

class ExplainRecommendationResponse(BaseModel):
    content_id: str
    title: str
    recommendation_score: float
    explanation: Dict[str, Any]
    similar_content: List[Dict[str, Any]]
    user_factors: Dict[str, Any]

@router.get("/feed", response_model=RecommendationFeedResponse)
async def get_recommendation_feed(
    limit: int = Query(default=20, ge=1, le=50, description="Number of recommendations to return"),
    refresh: bool = Query(default=False, description="Force refresh of recommendations"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get personalized recommendation feed for user"""
    logger.info("Recommendation feed request", 
               user_id=str(current_user.id), 
               limit=limit, 
               refresh=refresh)
    
    try:
        ai_client = get_ai_client()
        # Generate recommendations
        recommendations = await recommendation_engine.generate_recommendations(
            user=current_user,
            db=db,
            limit=limit,
            refresh_cache=refresh
        )
        
        # Convert to response format
        recommendation_responses = []
        for rec in recommendations:
            # Fetch content details for each recommendation
            content = db.query(ContentItem).filter(ContentItem.id == rec["content"].id).first()
            if not content:
                continue
            # Generate explanation text using AI client
            explanation_text = await ai_client.generate_explanation(
                prompt=f"Explain why this content titled '{content.title}' is recommended."
            )
            recommendation_responses.append(RecommendationResponse(
                content_id=str(content.id),
                title=content.title,
                description=content.description,
                content_type=content.content_type,
                source=content.source,
                url=content.url,
                duration_minutes=content.duration_minutes,
                difficulty_level=content.difficulty_level,
                topics=content.topics,
                language=content.language,
                recommendation_score=rec["score"],
                explanation_factors={"text": explanation_text},
                created_at=content.created_at.isoformat()
            ))
        
        from datetime import datetime
        response = RecommendationFeedResponse(
            recommendations=recommendation_responses,
            total_count=len(recommendation_responses),
            algorithm_version=recommendation_engine.algorithm_version,
            generated_at=datetime.utcnow().isoformat()
        )
        
        logger.info("Recommendation feed generated", 
                   user_id=str(current_user.id), 
                   count=len(recommendation_responses))
        
        return response
        
    except Exception as e:
        logger.error("Recommendation feed generation failed", 
                    error=str(e), 
                    user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendation feed"
        )

@router.get("/", response_model=RecommendationFeedResponse)
async def get_personalized_recommendations(
    limit: int = Query(default=10, ge=1, le=20, description="Number of recommendations to return"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Fetch personalized course/resource recommendations using vector similarity"""
    logger.info("Personalized recommendations request",
               user_id=str(current_user.id),
               limit=limit)

    try:
        ai_client = get_ai_client()

        # Get user's interaction history for context
        interactions = db.query(UserInteraction).filter(
            UserInteraction.user_id == current_user.id
        ).all()

        # Get available content with embeddings
        available_content = db.query(ContentItem).filter(
            ContentItem.status == "approved",
            ContentItem.embedding.isnot(None)
        ).all()

        if not available_content:
            return RecommendationFeedResponse(
                recommendations=[],
                total_count=0,
                algorithm_version="v1.0",
                generated_at=datetime.utcnow().isoformat()
            )

        # Calculate recommendations based on user preferences and embeddings
        recommendations = []

        # Get user preferences for context
        from services.models import UserPreferences
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()

        for content in available_content:
            score = 0.0
            explanation_factors = {}

            # Vector similarity with user's recent interactions
            if interactions:
                user_embedding = None
                # Create a composite embedding from user's recent content
                recent_content_ids = [i.content_id for i in interactions[-5:]]  # Last 5 interactions
                recent_embeddings = []

                for content_id in recent_content_ids:
                    recent_content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
                    if recent_content and recent_content.embedding:
                        recent_embeddings.append(recent_content.embedding)

                if recent_embeddings:
                    # Average the recent embeddings to create user profile embedding
                    import numpy as np
                    user_embedding = np.mean(recent_embeddings, axis=0).tolist()

                    # Calculate similarity
                    if content.embedding:
                        similarity = ai_client.calculate_similarity(user_embedding, content.embedding)
                        score += similarity * 0.6  # Weight vector similarity
                        explanation_factors["vector_similarity"] = similarity

            # Preference-based scoring
            if preferences:
                # Domain match
                if preferences.learning_domains and content.topics:
                    domain_match = any(domain in content.topics for domain in preferences.learning_domains)
                    if domain_match:
                        score += 0.2
                        explanation_factors["domain_match"] = 0.8

                # Content type preference
                if preferences.preferred_content_types and content.content_type in preferences.preferred_content_types:
                    score += 0.15
                    explanation_factors["content_type_match"] = 0.7

            # Avoid already interacted content
            if any(i.content_id == content.id for i in interactions):
                score *= 0.3  # Reduce score for already seen content

            if score > 0.1:  # Minimum threshold
                # Generate AI explanation
                explanation_text = await ai_client.generate_explanation(
                    prompt=f"Explain why '{content.title}' would be a good recommendation for a learner interested in {', '.join(content.topics[:3])}."
                )

                recommendations.append({
                    "content": content,
                    "score": score,
                    "explanation_factors": {"text": explanation_text, **explanation_factors}
                })

        # Sort by score and limit results
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        recommendations = recommendations[:limit]

        # Convert to response format
        recommendation_responses = []
        for rec in recommendations:
            content = rec["content"]
            recommendation_responses.append(RecommendationResponse(
                content_id=str(content.id),
                title=content.title,
                description=content.description,
                content_type=content.content_type,
                source=content.source,
                url=content.url,
                duration_minutes=content.duration_minutes,
                difficulty_level=content.difficulty_level,
                topics=content.topics,
                language=content.language,
                recommendation_score=rec["score"],
                explanation_factors=rec["explanation_factors"],
                created_at=content.created_at.isoformat()
            ))

        from datetime import datetime
        response = RecommendationFeedResponse(
            recommendations=recommendation_responses,
            total_count=len(recommendation_responses),
            algorithm_version="v1.0-vector",
            generated_at=datetime.utcnow().isoformat()
        )

        logger.info("Personalized recommendations generated",
                   user_id=str(current_user.id),
                   count=len(recommendation_responses))

        return response

    except Exception as e:
        logger.error("Personalized recommendations failed",
                    error=str(e),
                    user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate personalized recommendations"
        )

@router.post("/feedback")
async def submit_recommendation_feedback(
    feedback: RecommendationFeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit feedback on recommendation quality"""
    logger.info("Recommendation feedback submission", 
               user_id=str(current_user.id), 
               recommendation_id=feedback.recommendation_id)
    
    try:
        # Find the recommendation
        recommendation = db.query(Recommendation).filter(
            Recommendation.id == feedback.recommendation_id,
            Recommendation.user_id == current_user.id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )
        
        # Update recommendation with feedback
        recommendation.feedback_rating = feedback.feedback_rating
        
        # Store additional feedback in explanation_factors
        if not recommendation.explanation_factors:
            recommendation.explanation_factors = {}
        
        recommendation.explanation_factors['user_feedback'] = {
            'rating': feedback.feedback_rating,
            'type': feedback.feedback_type,
            'submitted_at': datetime.utcnow().isoformat()
        }
        
        db.commit()
        
        logger.info("Recommendation feedback recorded", 
                   user_id=str(current_user.id), 
                   recommendation_id=feedback.recommendation_id,
                   rating=feedback.feedback_rating)
        
        return {"message": "Feedback recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Recommendation feedback failed", 
                    error=str(e), 
                    user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback"
        )

@router.get("/explain/{recommendation_id}", response_model=ExplainRecommendationResponse)
async def explain_recommendation(
    recommendation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed explanation for a specific recommendation"""
    logger.info("Recommendation explanation request", 
               user_id=str(current_user.id), 
               recommendation_id=recommendation_id)
    
    try:
        # Find the recommendation
        recommendation = db.query(Recommendation).filter(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == current_user.id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )
        
        # Get the content item
        from services.models import ContentItem
        content = db.query(ContentItem).filter(
            ContentItem.id == recommendation.content_id
        ).first()
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        # Build detailed explanation
        explanation = {
            'algorithm_version': recommendation.algorithm_version,
            'recommendation_score': recommendation.recommendation_score,
            'factors': recommendation.explanation_factors,
            'content_topics': content.topics,
            'content_type': content.content_type,
            'content_source': content.source
        }
        
        # Get user's learning preferences for context
        from services.models import UserPreferences
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        user_factors = {}
        if preferences:
            user_factors = {
                'learning_domains': preferences.learning_domains,
                'skill_levels': preferences.skill_levels,
                'preferred_content_types': preferences.preferred_content_types,
                'language_preferences': preferences.language_preferences
            }
        
        # Find similar content (simplified version)
        similar_content = []
        if content.topics:
            similar_items = db.query(ContentItem).filter(
                ContentItem.status == 'approved',
                ContentItem.id != content.id,
                ContentItem.topics.overlap(content.topics)
            ).limit(5).all()
            
            for item in similar_items:
                similar_content.append({
                    'content_id': str(item.id),
                    'title': item.title,
                    'content_type': item.content_type,
                    'topics': item.topics,
                    'similarity_reason': 'Shared topics'
                })
        
        response = ExplainRecommendationResponse(
            content_id=str(content.id),
            title=content.title,
            recommendation_score=recommendation.recommendation_score,
            explanation=explanation,
            similar_content=similar_content,
            user_factors=user_factors
        )
        
        logger.info("Recommendation explanation generated", 
                   user_id=str(current_user.id), 
                   recommendation_id=recommendation_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Recommendation explanation failed", 
                    error=str(e), 
                    user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation"
        )

@router.post("/refresh")
async def refresh_recommendations(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Force refresh of user's recommendation cache"""
    logger.info("Recommendation refresh request", user_id=str(current_user.id))
    
    try:
        # Clear cache and generate fresh recommendations
        recommendations = await recommendation_engine.generate_recommendations(
            user=current_user,
            db=db,
            limit=20,
            refresh_cache=True
        )
        
        logger.info("Recommendations refreshed", 
                   user_id=str(current_user.id), 
                   count=len(recommendations))
        
        return {
            "message": "Recommendations refreshed successfully",
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error("Recommendation refresh failed", 
                    error=str(e), 
                    user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh recommendations"
        )

@router.get("/history")
async def get_recommendation_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's recommendation history"""
    logger.info("Recommendation history request", 
               user_id=str(current_user.id), 
               limit=limit, 
               offset=offset)
    
    try:
        # Get recommendation history
        recommendations = db.query(Recommendation).filter(
            Recommendation.user_id == current_user.id
        ).order_by(Recommendation.shown_at.desc()).offset(offset).limit(limit).all()
        
        # Get total count
        total_count = db.query(Recommendation).filter(
            Recommendation.user_id == current_user.id
        ).count()
        
        # Format response
        history_items = []
        for rec in recommendations:
            # Get content details
            from services.models import ContentItem
            content = db.query(ContentItem).filter(
                ContentItem.id == rec.content_id
            ).first()
            
            if content:
                history_items.append({
                    'recommendation_id': str(rec.id),
                    'content_id': str(content.id),
                    'title': content.title,
                    'content_type': content.content_type,
                    'recommendation_score': rec.recommendation_score,
                    'shown_at': rec.shown_at.isoformat(),
                    'clicked_at': rec.clicked_at.isoformat() if rec.clicked_at else None,
                    'feedback_rating': rec.feedback_rating,
                    'algorithm_version': rec.algorithm_version
                })
        
        return {
            'history': history_items,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        logger.error("Recommendation history retrieval failed", 
                    error=str(e), 
                    user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recommendation history"
        )

# Updated 2025-09-05: Complete recommendations API with feed, feedback, and explanations