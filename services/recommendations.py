"""
Recommendation Engine Service
Service for generating personalized content recommendations

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: AI-powered recommendation engine for personalized learning
"""

import structlog
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from services.models import User, ContentItem, UserPreferences, UserInteraction, Recommendation
from services.ai_client import get_ai_client

logger = structlog.get_logger()

class RecommendationEngine:
    """Recommendation engine service"""
    
    def __init__(self):
        self.algorithm_version = "v1.1"
        self.min_score_threshold = 0.3
        self.ai_client = get_ai_client()
    
    async def generate_recommendations(self, user: User, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate personalized recommendations for user"""
        try:
            # Get user preferences
            preferences = db.query(UserPreferences).filter(
                UserPreferences.user_id == user.id
            ).first()
            
            if not preferences:
                logger.warning(f"No preferences found for user {user.id}")
                return self._get_popular_content(db, limit)
            
            # Get user interaction history
            interactions = db.query(UserInteraction).filter(
                UserInteraction.user_id == user.id
            ).all()
            
            # Get available content
            available_content = db.query(ContentItem).filter(
                ContentItem.status == "approved"
            ).all()
            
            # Generate recommendations
            recommendations = []
            for content in available_content:
                score = await self._calculate_recommendation_score(content, preferences, interactions)
                
                if score >= self.min_score_threshold:
                    recommendations.append({
                        "content": content,
                        "score": score,
                        "explanation": self._generate_explanation(content, preferences, score)
                    })
            
            # Sort by score and limit results
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error("Recommendation generation failed", error=str(e), user_id=str(user.id))
            return self._get_popular_content(db, limit)
    
    async def _calculate_recommendation_score(self, content: ContentItem, preferences: UserPreferences, interactions: List[UserInteraction]) -> float:
        """Calculate recommendation score for content"""
        score = 0.0
        
        # Domain preference match
        if preferences.learning_domains:
            domain_match = any(domain in content.topics for domain in preferences.learning_domains)
            if domain_match:
                score += 0.2
        
        # Skill level match
        if preferences.skill_levels and content.difficulty_level:
            for domain in content.topics:
                if domain in preferences.skill_levels:
                    user_level = preferences.skill_levels[domain]
                    if user_level == content.difficulty_level:
                        score += 0.15
                    elif self._is_appropriate_level(user_level, content.difficulty_level):
                        score += 0.1
        
        # Content type preference
        if preferences.preferred_content_types and content.content_type in preferences.preferred_content_types:
            score += 0.1
        
        # Avoid already interacted content (reduce score)
        interacted_content_ids = [i.content_id for i in interactions]
        if content.id in interacted_content_ids:
            score *= 0.5
        
        # Content popularity boost (simplified)
        content_interactions = len([i for i in interactions if i.content_id == content.id])
        if content_interactions > 0:
            score += min(content_interactions * 0.05, 0.05)

        # AI relevance score
        user_prompt = f"My learning domains are {preferences.learning_domains} and my skill levels are {preferences.skill_levels}"
        relevance_score = await self.ai_client.get_relevance_score(user_prompt, content.description)
        score += relevance_score * 0.5
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _is_appropriate_level(self, user_level: str, content_level: str) -> bool:
        """Check if content level is appropriate for user level"""
        levels = ["beginner", "intermediate", "advanced"]
        
        try:
            user_idx = levels.index(user_level)
            content_idx = levels.index(content_level)
            
            # Allow same level or one level up
            return content_idx <= user_idx + 1
        except ValueError:
            return True  # Default to appropriate if levels not recognized
    
    def _generate_explanation(self, content: ContentItem, preferences: UserPreferences, score: float) -> Dict[str, Any]:
        """Generate explanation for recommendation"""
        factors = {}
        
        # Domain match
        if preferences.learning_domains:
            domain_match = any(domain in content.topics for domain in preferences.learning_domains)
            if domain_match:
                factors["domain_match"] = 0.8
        
        # Content type match
        if preferences.preferred_content_types and content.content_type in preferences.preferred_content_types:
            factors["content_type_match"] = 0.7
        
        # Difficulty appropriateness
        factors["difficulty_appropriateness"] = 0.6
        
        return {
            "factors": factors,
            "primary_reason": self._get_primary_reason(content, preferences),
            "confidence": score
        }
    
    def _get_primary_reason(self, content: ContentItem, preferences: UserPreferences) -> str:
        """Get primary reason for recommendation"""
        if preferences.learning_domains:
            matching_domains = [domain for domain in preferences.learning_domains if domain in content.topics]
            if matching_domains:
                return f"Matches your interest in {matching_domains[0]}"
        
        if preferences.preferred_content_types and content.content_type in preferences.preferred_content_types:
            return f"Matches your preferred content type: {content.content_type}"
        
        return "Popular content in your area"
    
    def _get_popular_content(self, db: Session, limit: int) -> List[Dict[str, Any]]:
        """Get popular content as fallback"""
        try:
            popular_content = db.query(ContentItem).filter(
                ContentItem.status == "approved"
            ).limit(limit).all()
            
            return [{
                "content": content,
                "score": 0.5,
                "explanation": {
                    "factors": {"popularity": 0.5},
                    "primary_reason": "Popular content",
                    "confidence": 0.5
                }
            } for content in popular_content]
            
        except Exception as e:
            logger.error("Failed to get popular content", error=str(e))
            return []
    
    def store_recommendation(self, user_id: str, content_id: str, score: float, explanation: Dict[str, Any], db: Session) -> Recommendation:
        """Store recommendation in database"""
        try:
            recommendation = Recommendation(
                user_id=user_id,
                content_id=content_id,
                recommendation_score=score,
                explanation_factors=explanation.get("factors", {}),
                algorithm_version=self.algorithm_version
            )
            
            db.add(recommendation)
            db.commit()
            db.refresh(recommendation)
            
            logger.info(f"Stored recommendation for user {user_id}, content {content_id}")
            return recommendation
            
        except Exception as e:
            logger.error("Failed to store recommendation", error=str(e))
            db.rollback()
            raise