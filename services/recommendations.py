"""
Recommendation Engine Service
AI-powered content recommendations with vector similarity and reranking

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Generate personalized content recommendations using embeddings and user preferences
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_
import structlog
from datetime import datetime, timedelta
import redis
import json
from services.models import User, UserPreferences, ContentItem, UserInteraction, Recommendation
from services.exceptions import ExternalServiceError
from config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Redis client for caching
redis_client = redis.from_url(settings.REDIS_URL)

class RecommendationEngine:
    """AI-powered recommendation engine"""
    
    def __init__(self):
        self.algorithm_version = "v1.0"
        self.cache_ttl = 3600  # 1 hour cache
        self.max_recommendations = 50
        self.similarity_threshold = 0.7
    
    async def generate_recommendations(
        self, 
        user: User, 
        db: Session, 
        limit: int = 20,
        refresh_cache: bool = False
    ) -> List[Dict[str, Any]]:
        """Generate personalized recommendations for user"""
        logger.info("Generating recommendations", user_id=str(user.id), limit=limit)
        
        try:
            # Check cache first
            cache_key = f"recommendations:{user.id}:{limit}"
            if not refresh_cache:
                cached_recommendations = self._get_cached_recommendations(cache_key)
                if cached_recommendations:
                    logger.info("Returning cached recommendations", user_id=str(user.id))
                    return cached_recommendations
            
            # Get user preferences
            preferences = db.query(UserPreferences).filter(
                UserPreferences.user_id == user.id
            ).first()
            
            # Get user interaction history
            user_interactions = db.query(UserInteraction).filter(
                UserInteraction.user_id == user.id
            ).all()
            
            # Generate recommendations using multiple strategies
            recommendations = []
            
            # Strategy 1: Content-based filtering using embeddings
            content_based_recs = await self._content_based_recommendations(
                user, preferences, user_interactions, db, limit // 2
            )
            recommendations.extend(content_based_recs)
            
            # Strategy 2: Preference-based filtering
            preference_based_recs = await self._preference_based_recommendations(
                user, preferences, user_interactions, db, limit // 2
            )
            recommendations.extend(preference_based_recs)
            
            # Strategy 3: Trending content for new users
            if len(user_interactions) < 5:
                trending_recs = await self._trending_content_recommendations(
                    user, db, limit // 4
                )
                recommendations.extend(trending_recs)
            
            # Remove duplicates and already interacted content
            recommendations = self._deduplicate_recommendations(
                recommendations, user_interactions
            )
            
            # Rerank recommendations
            final_recommendations = await self._rerank_recommendations(
                recommendations, user, preferences, user_interactions, db
            )
            
            # Limit results
            final_recommendations = final_recommendations[:limit]
            
            # Generate explanations
            explained_recommendations = self._add_explanations(
                final_recommendations, user, preferences
            )
            
            # Cache results
            self._cache_recommendations(cache_key, explained_recommendations)
            
            # Log recommendations to database
            await self._log_recommendations(user.id, explained_recommendations, db)
            
            logger.info("Recommendations generated", 
                       user_id=str(user.id), 
                       count=len(explained_recommendations))
            
            return explained_recommendations
            
        except Exception as e:
            logger.error("Recommendation generation failed", error=str(e), user_id=str(user.id))
            # Return fallback recommendations
            return await self._fallback_recommendations(user, db, limit)
    
    async def _content_based_recommendations(
        self, 
        user: User, 
        preferences: Optional[UserPreferences],
        user_interactions: List[UserInteraction],
        db: Session, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on content similarity"""
        
        if not user_interactions:
            return []
        
        try:
            # Get embeddings of content user has interacted with positively
            positive_interactions = [
                interaction for interaction in user_interactions
                if interaction.interaction_type in ['like', 'complete', 'bookmark'] or
                (interaction.rating and interaction.rating >= 4)
            ]
            
            if not positive_interactions:
                return []
            
            # Get content embeddings for positive interactions
            content_ids = [str(interaction.content_id) for interaction in positive_interactions]
            
            # Query for similar content using vector similarity
            similar_content_query = text("""
                SELECT c.*, 
                       1 - (c.embedding <=> (
                           SELECT AVG(embedding) 
                           FROM content_items 
                           WHERE id = ANY(:content_ids) AND embedding IS NOT NULL
                       )) as similarity_score
                FROM content_items c
                WHERE c.status = 'approved' 
                  AND c.embedding IS NOT NULL
                  AND c.id != ALL(:content_ids)
                ORDER BY similarity_score DESC
                LIMIT :limit
            """)
            
            result = db.execute(similar_content_query, {
                'content_ids': content_ids,
                'limit': limit * 2  # Get more to allow for filtering
            })
            
            recommendations = []
            for row in result:
                content = db.query(ContentItem).filter(ContentItem.id == row.id).first()
                if content and row.similarity_score > self.similarity_threshold:
                    recommendations.append({
                        'content': content,
                        'score': float(row.similarity_score),
                        'strategy': 'content_based',
                        'reasoning': 'Similar to content you liked'
                    })
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error("Content-based recommendations failed", error=str(e))
            return []
    
    async def _preference_based_recommendations(
        self,
        user: User,
        preferences: Optional[UserPreferences],
        user_interactions: List[UserInteraction],
        db: Session,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on user preferences"""
        
        if not preferences:
            return []
        
        try:
            # Build query based on preferences
            query = db.query(ContentItem).filter(ContentItem.status == 'approved')
            
            # Filter by learning domains
            if preferences.learning_domains:
                domain_filters = []
                for domain in preferences.learning_domains:
                    domain_filters.append(ContentItem.topics.contains([domain]))
                query = query.filter(or_(*domain_filters))
            
            # Filter by preferred content types
            if preferences.preferred_content_types:
                query = query.filter(
                    ContentItem.content_type.in_(preferences.preferred_content_types)
                )
            
            # Filter by language preferences
            if preferences.language_preferences:
                query = query.filter(
                    ContentItem.language.in_(preferences.language_preferences)
                )
            
            # Filter by time constraints
            if preferences.time_constraints.get('max_duration'):
                max_duration = preferences.time_constraints['max_duration']
                query = query.filter(
                    or_(
                        ContentItem.duration_minutes.is_(None),
                        ContentItem.duration_minutes <= max_duration
                    )
                )
            
            # Exclude already interacted content
            interacted_content_ids = [interaction.content_id for interaction in user_interactions]
            if interacted_content_ids:
                query = query.filter(~ContentItem.id.in_(interacted_content_ids))
            
            # Order by creation date (newer first) and limit
            content_items = query.order_by(ContentItem.created_at.desc()).limit(limit * 2).all()
            
            recommendations = []
            for content in content_items:
                # Calculate preference match score
                score = self._calculate_preference_score(content, preferences)
                
                recommendations.append({
                    'content': content,
                    'score': score,
                    'strategy': 'preference_based',
                    'reasoning': 'Matches your learning preferences'
                })
            
            # Sort by score and return top results
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error("Preference-based recommendations failed", error=str(e))
            return []
    
    async def _trending_content_recommendations(
        self,
        user: User,
        db: Session,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on trending content"""
        
        try:
            # Get content with high engagement in the last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            trending_query = text("""
                SELECT c.*, 
                       COUNT(ui.id) as interaction_count,
                       AVG(COALESCE(ui.rating, 3)) as avg_rating
                FROM content_items c
                LEFT JOIN user_interactions ui ON c.id = ui.content_id 
                    AND ui.created_at >= :thirty_days_ago
                WHERE c.status = 'approved'
                GROUP BY c.id
                HAVING COUNT(ui.id) > 0
                ORDER BY interaction_count DESC, avg_rating DESC
                LIMIT :limit
            """)
            
            result = db.execute(trending_query, {
                'thirty_days_ago': thirty_days_ago,
                'limit': limit
            })
            
            recommendations = []
            for row in result:
                content = db.query(ContentItem).filter(ContentItem.id == row.id).first()
                if content:
                    # Calculate trending score
                    score = (row.interaction_count * 0.7) + (row.avg_rating * 0.3)
                    
                    recommendations.append({
                        'content': content,
                        'score': float(score),
                        'strategy': 'trending',
                        'reasoning': 'Popular content this month'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error("Trending content recommendations failed", error=str(e))
            return []
    
    def _calculate_preference_score(
        self, 
        content: ContentItem, 
        preferences: UserPreferences
    ) -> float:
        """Calculate how well content matches user preferences"""
        score = 0.0
        
        # Domain match score
        if preferences.learning_domains and content.topics:
            domain_matches = len(set(preferences.learning_domains) & set(content.topics))
            score += domain_matches * 0.4
        
        # Content type match score
        if preferences.preferred_content_types:
            if content.content_type in preferences.preferred_content_types:
                score += 0.3
        
        # Language match score
        if preferences.language_preferences:
            if content.language in preferences.language_preferences:
                score += 0.2
        
        # Duration match score
        if preferences.time_constraints.get('max_duration') and content.duration_minutes:
            max_duration = preferences.time_constraints['max_duration']
            if content.duration_minutes <= max_duration:
                score += 0.1
        
        return score
    
    async def _rerank_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        user: User,
        preferences: Optional[UserPreferences],
        user_interactions: List[UserInteraction],
        db: Session
    ) -> List[Dict[str, Any]]:
        """Rerank recommendations using advanced scoring"""
        
        try:
            # Calculate user's topic preferences from interactions
            topic_preferences = self._calculate_topic_preferences(user_interactions, db)
            
            # Calculate recency boost
            now = datetime.utcnow()
            
            for rec in recommendations:
                content = rec['content']
                
                # Base score from strategy
                final_score = rec['score']
                
                # Topic preference boost
                if content.topics and topic_preferences:
                    topic_boost = sum(
                        topic_preferences.get(topic, 0) for topic in content.topics
                    ) / len(content.topics)
                    final_score += topic_boost * 0.3
                
                # Recency boost (newer content gets slight boost)
                days_old = (now - content.created_at).days
                recency_boost = max(0, (30 - days_old) / 30) * 0.1
                final_score += recency_boost
                
                # Diversity penalty (reduce score for similar content types)
                diversity_penalty = self._calculate_diversity_penalty(
                    content, recommendations, rec
                )
                final_score -= diversity_penalty
                
                rec['final_score'] = final_score
            
            # Sort by final score
            recommendations.sort(key=lambda x: x['final_score'], reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error("Reranking failed", error=str(e))
            return recommendations
    
    def _calculate_topic_preferences(
        self, 
        user_interactions: List[UserInteraction], 
        db: Session
    ) -> Dict[str, float]:
        """Calculate user's topic preferences from interaction history"""
        
        topic_scores = {}
        
        for interaction in user_interactions:
            content = db.query(ContentItem).filter(
                ContentItem.id == interaction.content_id
            ).first()
            
            if not content or not content.topics:
                continue
            
            # Weight based on interaction type and rating
            weight = 1.0
            if interaction.interaction_type == 'like':
                weight = 1.5
            elif interaction.interaction_type == 'complete':
                weight = 2.0
            elif interaction.interaction_type == 'bookmark':
                weight = 1.8
            elif interaction.interaction_type == 'dislike':
                weight = -1.0
            
            if interaction.rating:
                weight *= (interaction.rating / 3.0)  # Normalize rating
            
            # Add weight to each topic
            for topic in content.topics:
                topic_scores[topic] = topic_scores.get(topic, 0) + weight
        
        # Normalize scores
        if topic_scores:
            max_score = max(topic_scores.values())
            if max_score > 0:
                topic_scores = {
                    topic: score / max_score 
                    for topic, score in topic_scores.items()
                }
        
        return topic_scores
    
    def _calculate_diversity_penalty(
        self,
        content: ContentItem,
        all_recommendations: List[Dict[str, Any]],
        current_rec: Dict[str, Any]
    ) -> float:
        """Calculate penalty for lack of diversity"""
        
        penalty = 0.0
        
        # Count similar content types and topics in top recommendations
        similar_type_count = 0
        similar_topic_count = 0
        
        for rec in all_recommendations:
            if rec == current_rec:
                continue
            
            other_content = rec['content']
            
            # Same content type
            if other_content.content_type == content.content_type:
                similar_type_count += 1
            
            # Similar topics
            if content.topics and other_content.topics:
                common_topics = set(content.topics) & set(other_content.topics)
                if len(common_topics) > 0:
                    similar_topic_count += 1
        
        # Apply penalty based on similarity
        penalty += similar_type_count * 0.05
        penalty += similar_topic_count * 0.03
        
        return min(penalty, 0.3)  # Cap penalty at 0.3
    
    def _deduplicate_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        user_interactions: List[UserInteraction]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate and already interacted content"""
        
        seen_content_ids = set()
        interacted_content_ids = {interaction.content_id for interaction in user_interactions}
        
        deduplicated = []
        for rec in recommendations:
            content_id = rec['content'].id
            
            if (content_id not in seen_content_ids and 
                content_id not in interacted_content_ids):
                seen_content_ids.add(content_id)
                deduplicated.append(rec)
        
        return deduplicated
    
    def _add_explanations(
        self,
        recommendations: List[Dict[str, Any]],
        user: User,
        preferences: Optional[UserPreferences]
    ) -> List[Dict[str, Any]]:
        """Add detailed explanations for recommendations"""
        
        explained_recommendations = []
        
        for rec in recommendations:
            content = rec['content']
            
            # Build explanation factors
            explanation_factors = {
                'strategy': rec['strategy'],
                'base_score': rec['score'],
                'final_score': rec.get('final_score', rec['score']),
                'reasoning': rec['reasoning']
            }
            
            # Add specific factors based on content and preferences
            if preferences:
                if preferences.learning_domains and content.topics:
                    matching_domains = list(set(preferences.learning_domains) & set(content.topics))
                    if matching_domains:
                        explanation_factors['matching_domains'] = matching_domains
                
                if preferences.preferred_content_types:
                    if content.content_type in preferences.preferred_content_types:
                        explanation_factors['preferred_content_type'] = True
            
            explained_recommendations.append({
                'content_id': str(content.id),
                'title': content.title,
                'description': content.description,
                'content_type': content.content_type,
                'source': content.source,
                'url': content.url,
                'duration_minutes': content.duration_minutes,
                'difficulty_level': content.difficulty_level,
                'topics': content.topics,
                'language': content.language,
                'recommendation_score': rec.get('final_score', rec['score']),
                'explanation_factors': explanation_factors,
                'created_at': content.created_at.isoformat()
            })
        
        return explained_recommendations
    
    async def _fallback_recommendations(
        self, 
        user: User, 
        db: Session, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Generate fallback recommendations when main algorithm fails"""
        
        try:
            # Get most recent approved content
            recent_content = db.query(ContentItem).filter(
                ContentItem.status == 'approved'
            ).order_by(ContentItem.created_at.desc()).limit(limit).all()
            
            fallback_recommendations = []
            for content in recent_content:
                fallback_recommendations.append({
                    'content_id': str(content.id),
                    'title': content.title,
                    'description': content.description,
                    'content_type': content.content_type,
                    'source': content.source,
                    'url': content.url,
                    'duration_minutes': content.duration_minutes,
                    'difficulty_level': content.difficulty_level,
                    'topics': content.topics,
                    'language': content.language,
                    'recommendation_score': 0.5,
                    'explanation_factors': {
                        'strategy': 'fallback',
                        'reasoning': 'Recent content'
                    },
                    'created_at': content.created_at.isoformat()
                })
            
            return fallback_recommendations
            
        except Exception as e:
            logger.error("Fallback recommendations failed", error=str(e))
            return []
    
    def _get_cached_recommendations(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get recommendations from cache"""
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning("Cache retrieval failed", error=str(e))
        return None
    
    def _cache_recommendations(self, cache_key: str, recommendations: List[Dict[str, Any]]):
        """Cache recommendations"""
        try:
            redis_client.setex(
                cache_key, 
                self.cache_ttl, 
                json.dumps(recommendations, default=str)
            )
        except Exception as e:
            logger.warning("Cache storage failed", error=str(e))
    
    async def _log_recommendations(
        self, 
        user_id: str, 
        recommendations: List[Dict[str, Any]], 
        db: Session
    ):
        """Log recommendations to database for tracking"""
        try:
            for rec in recommendations:
                recommendation_log = Recommendation(
                    user_id=user_id,
                    content_id=rec['content_id'],
                    recommendation_score=rec['recommendation_score'],
                    explanation_factors=rec['explanation_factors'],
                    algorithm_version=self.algorithm_version
                )
                db.add(recommendation_log)
            
            db.commit()
            
        except Exception as e:
            logger.error("Failed to log recommendations", error=str(e))

# Global recommendation engine instance
recommendation_engine = RecommendationEngine()

# Updated 2025-09-05: Comprehensive AI-powered recommendation engine with vector similarity and reranking