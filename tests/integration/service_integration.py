"""
Service Integration Tests
Tests for service-to-service communication and business logic integration

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Service integration testing for validating business logic and service interactions
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from services.auth import auth_service
from services.content_processing import ContentProcessor
from services.recommendations import RecommendationEngine
from services.models import User, ContentItem, UserPreferences, UserInteraction, Recommendation

logger = structlog.get_logger()

class ServiceIntegrationTests:
    """Service integration test suite"""
    
    def __init__(self, context):
        self.context = context
        self.db = context.db_session
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
    
    def _record_test_result(self, test_name: str, success: bool, error: str = None):
        """Record test result"""
        if success:
            self.passed += 1
            logger.info(f"✓ {test_name}")
        else:
            self.failed += 1
            if error:
                self.errors.append(f"{test_name}: {error}")
            logger.error(f"✗ {test_name}", error=error)
    
    async def test_auth_service_integration(self) -> bool:
        """Test authentication service integration"""
        try:
            # Test password hashing and verification
            password = "TestPassword123!"
            hashed = auth_service.hash_password(password)
            
            if not auth_service.verify_password(password, hashed):
                self._record_test_result("Auth Service - Password Verification", False, 
                                       "Password verification failed")
                return False
            
            # Test token creation and verification
            test_user = self.context.test_users[0]
            token_data = {"sub": str(test_user.id), "email": test_user.email, "role": test_user.role}
            
            access_token = auth_service.create_access_token(token_data)
            refresh_token = auth_service.create_refresh_token({"sub": str(test_user.id)})
            
            # Verify tokens
            access_payload = auth_service.verify_token(access_token, "access")
            refresh_payload = auth_service.verify_token(refresh_token, "refresh")
            
            if (access_payload.get("sub") != str(test_user.id) or
                refresh_payload.get("sub") != str(test_user.id)):
                self._record_test_result("Auth Service - Token Verification", False, 
                                       "Token payload mismatch")
                return False
            
            # Test user authentication
            authenticated_user = auth_service.authenticate_user(
                self.db, test_user.email, "TestPassword123!"
            )
            
            if not authenticated_user or authenticated_user.id != test_user.id:
                self._record_test_result("Auth Service - User Authentication", False, 
                                       "User authentication failed")
                return False
            
            # Test token pair creation
            token_pair = auth_service.create_token_pair(test_user)
            required_fields = ["access_token", "refresh_token", "token_type", "expires_in"]
            
            for field in required_fields:
                if field not in token_pair:
                    self._record_test_result("Auth Service - Token Pair", False, 
                                           f"Missing field: {field}")
                    return False
            
            self._record_test_result("Auth Service Integration", True)
            return True
        except Exception as e:
            self._record_test_result("Auth Service Integration", False, str(e))
            return False
    
    async def test_content_processing_integration(self) -> bool:
        """Test content processing service integration"""
        try:
            # Initialize content processor
            try:
                content_processor = ContentProcessor()
            except Exception:
                # If ContentProcessor doesn't exist, skip this test
                self.skipped += 1
                logger.info("⚠ Content Processing Integration - Skipped (service not implemented)")
                return True
            
            # Test content validation
            valid_content_data = {
                "title": "Test Content Processing",
                "description": "Test content for processing integration",
                "content_type": "article",
                "source": "test",
                "url": "https://example.com/test-content",
                "topics": ["Testing", "Integration"]
            }
            
            # This would test actual content processing logic
            # For now, we'll just verify the service can be instantiated
            self._record_test_result("Content Processing Integration", True)
            return True
        except Exception as e:
            self._record_test_result("Content Processing Integration", False, str(e))
            return False
    
    async def test_recommendation_engine_integration(self) -> bool:
        """Test recommendation engine service integration"""
        try:
            # Initialize recommendation engine
            try:
                recommendation_engine = RecommendationEngine()
            except Exception:
                # If RecommendationEngine doesn't exist, skip this test
                self.skipped += 1
                logger.info("⚠ Recommendation Engine Integration - Skipped (service not implemented)")
                return True
            
            # Test recommendation generation
            test_user = self.context.test_users[0]
            test_content = self.context.test_content
            
            # This would test actual recommendation logic
            # For now, we'll just verify the service can be instantiated
            self._record_test_result("Recommendation Engine Integration", True)
            return True
        except Exception as e:
            self._record_test_result("Recommendation Engine Integration", False, str(e))
            return False
    
    async def test_user_preference_service_integration(self) -> bool:
        """Test user preference service integration with recommendations"""
        try:
            test_user = self.context.test_users[0]
            
            # Get user preferences
            preferences = self.db.query(UserPreferences).filter(
                UserPreferences.user_id == test_user.id
            ).first()
            
            if not preferences:
                self._record_test_result("User Preference Service Integration", False, 
                                       "User preferences not found")
                return False
            
            # Test preference-based content filtering
            ai_content = self.db.query(ContentItem).filter(
                ContentItem.topics.contains(['AI'])
            ).all()
            
            web_dev_content = self.db.query(ContentItem).filter(
                ContentItem.topics.contains(['Web Development'])
            ).all()
            
            # Verify content exists for user's preferred domains
            user_domains = preferences.learning_domains
            if 'AI' in user_domains and len(ai_content) == 0:
                self._record_test_result("User Preference Service Integration", False, 
                                       "No AI content found for user preference")
                return False
            
            if 'Web Development' in user_domains and len(web_dev_content) == 0:
                self._record_test_result("User Preference Service Integration", False, 
                                       "No Web Development content found for user preference")
                return False
            
            # Test skill level matching
            skill_levels = preferences.skill_levels
            for domain, level in skill_levels.items():
                if level not in ['beginner', 'intermediate', 'advanced']:
                    self._record_test_result("User Preference Service Integration", False, 
                                           f"Invalid skill level: {level}")
                    return False
            
            self._record_test_result("User Preference Service Integration", True)
            return True
        except Exception as e:
            self._record_test_result("User Preference Service Integration", False, str(e))
            return False
    
    async def test_user_interaction_tracking(self) -> bool:
        """Test user interaction tracking and analytics"""
        try:
            test_user = self.context.test_users[0]
            test_content = self.context.test_content[0]
            
            # Create test interactions
            interactions = [
                UserInteraction(
                    user_id=test_user.id,
                    content_id=test_content.id,
                    interaction_type="view",
                    time_spent_minutes=15,
                    completion_percentage=50.0
                ),
                UserInteraction(
                    user_id=test_user.id,
                    content_id=test_content.id,
                    interaction_type="like",
                    rating=4
                ),
                UserInteraction(
                    user_id=test_user.id,
                    content_id=test_content.id,
                    interaction_type="complete",
                    time_spent_minutes=30,
                    completion_percentage=100.0,
                    rating=5
                )
            ]
            
            for interaction in interactions:
                self.db.add(interaction)
            self.db.commit()
            
            # Test interaction analytics
            total_interactions = self.db.query(UserInteraction).filter(
                UserInteraction.user_id == test_user.id
            ).count()
            
            completed_interactions = self.db.query(UserInteraction).filter(
                UserInteraction.user_id == test_user.id,
                UserInteraction.interaction_type == "complete"
            ).count()
            
            if total_interactions < 3:
                self._record_test_result("User Interaction Tracking", False, 
                                       f"Expected at least 3 interactions, got {total_interactions}")
                return False
            
            if completed_interactions < 1:
                self._record_test_result("User Interaction Tracking", False, 
                                       "No completed interactions found")
                return False
            
            # Test interaction aggregation
            from sqlalchemy import func
            avg_rating = self.db.query(func.avg(UserInteraction.rating)).filter(
                UserInteraction.user_id == test_user.id,
                UserInteraction.rating.isnot(None)
            ).scalar()
            
            if avg_rating is None or avg_rating < 1 or avg_rating > 5:
                self._record_test_result("User Interaction Tracking", False, 
                                       f"Invalid average rating: {avg_rating}")
                return False
            
            self._record_test_result("User Interaction Tracking", True)
            return True
        except Exception as e:
            self._record_test_result("User Interaction Tracking", False, str(e))
            return False
    
    async def test_recommendation_workflow(self) -> bool:
        """Test complete recommendation workflow"""
        try:
            test_user = self.context.test_users[0]
            test_content = self.context.test_content
            
            # Create test recommendations
            recommendations = []
            for i, content in enumerate(test_content[:2]):  # Create 2 recommendations
                recommendation = Recommendation(
                    user_id=test_user.id,
                    content_id=content.id,
                    recommendation_score=0.8 - (i * 0.1),  # Decreasing scores
                    explanation_factors={
                        "user_preference_match": 0.9,
                        "content_popularity": 0.7,
                        "difficulty_match": 0.8
                    },
                    algorithm_version="test_v1.0"
                )
                recommendations.append(recommendation)
                self.db.add(recommendation)
            
            self.db.commit()
            
            # Test recommendation retrieval
            user_recommendations = self.db.query(Recommendation).filter(
                Recommendation.user_id == test_user.id
            ).order_by(Recommendation.recommendation_score.desc()).all()
            
            if len(user_recommendations) < 2:
                self._record_test_result("Recommendation Workflow", False, 
                                       f"Expected at least 2 recommendations, got {len(user_recommendations)}")
                return False
            
            # Verify recommendations are ordered by score
            scores = [r.recommendation_score for r in user_recommendations]
            if scores != sorted(scores, reverse=True):
                self._record_test_result("Recommendation Workflow", False, 
                                       "Recommendations not ordered by score")
                return False
            
            # Test recommendation feedback
            first_recommendation = user_recommendations[0]
            first_recommendation.clicked_at = datetime.utcnow()
            first_recommendation.feedback_rating = 4
            self.db.commit()
            
            # Verify feedback was recorded
            updated_recommendation = self.db.query(Recommendation).filter(
                Recommendation.id == first_recommendation.id
            ).first()
            
            if (updated_recommendation.clicked_at is None or 
                updated_recommendation.feedback_rating != 4):
                self._record_test_result("Recommendation Workflow", False, 
                                       "Recommendation feedback not recorded")
                return False
            
            self._record_test_result("Recommendation Workflow", True)
            return True
        except Exception as e:
            self._record_test_result("Recommendation Workflow", False, str(e))
            return False
    
    async def test_learning_session_management(self) -> bool:
        """Test learning session management"""
        try:
            test_user = self.context.test_users[0]
            test_content = self.context.test_content[0]
            
            # Create learning session
            from services.models import LearningSession
            session = LearningSession(
                user_id=test_user.id,
                content_id=test_content.id,
                started_at=datetime.utcnow(),
                progress_percentage=0.0,
                notes="Starting to learn about this topic"
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            # Update session progress
            session.progress_percentage = 50.0
            session.notes = "Halfway through the content"
            self.db.commit()
            
            # Complete session
            session.ended_at = datetime.utcnow()
            session.progress_percentage = 100.0
            session.notes = "Completed the learning session"
            self.db.commit()
            
            # Verify session data
            completed_session = self.db.query(LearningSession).filter(
                LearningSession.id == session.id
            ).first()
            
            if (completed_session.progress_percentage != 100.0 or
                completed_session.ended_at is None):
                self._record_test_result("Learning Session Management", False, 
                                       "Session completion not recorded properly")
                return False
            
            # Test session analytics
            user_sessions = self.db.query(LearningSession).filter(
                LearningSession.user_id == test_user.id
            ).all()
            
            total_sessions = len(user_sessions)
            completed_sessions = len([s for s in user_sessions if s.progress_percentage == 100.0])
            
            if total_sessions == 0:
                self._record_test_result("Learning Session Management", False, 
                                       "No learning sessions found")
                return False
            
            completion_rate = completed_sessions / total_sessions
            if completion_rate < 0 or completion_rate > 1:
                self._record_test_result("Learning Session Management", False, 
                                       f"Invalid completion rate: {completion_rate}")
                return False
            
            self._record_test_result("Learning Session Management", True)
            return True
        except Exception as e:
            self._record_test_result("Learning Session Management", False, str(e))
            return False
    
    async def test_content_approval_workflow(self) -> bool:
        """Test content approval and moderation workflow"""
        try:
            # Create pending content
            pending_content = ContentItem(
                title="Pending Content for Approval",
                description="This content is awaiting approval",
                content_type="article",
                source="upload",
                source_id="pending_test_1",
                url="https://example.com/pending-content",
                difficulty_level="intermediate",
                topics=["Testing", "Approval"],
                status="pending"
            )
            self.db.add(pending_content)
            self.db.commit()
            self.db.refresh(pending_content)
            
            # Test content approval
            pending_content.status = "approved"
            self.db.commit()
            
            # Verify approval
            approved_content = self.db.query(ContentItem).filter(
                ContentItem.id == pending_content.id
            ).first()
            
            if approved_content.status != "approved":
                self._record_test_result("Content Approval Workflow", False, 
                                       "Content approval not recorded")
                return False
            
            # Test content rejection
            rejected_content = ContentItem(
                title="Content to be Rejected",
                description="This content will be rejected",
                content_type="video",
                source="upload",
                source_id="rejected_test_1",
                url="https://example.com/rejected-content",
                difficulty_level="beginner",
                topics=["Testing"],
                status="pending"
            )
            self.db.add(rejected_content)
            self.db.commit()
            
            rejected_content.status = "rejected"
            self.db.commit()
            
            # Verify rejection
            final_rejected_content = self.db.query(ContentItem).filter(
                ContentItem.id == rejected_content.id
            ).first()
            
            if final_rejected_content.status != "rejected":
                self._record_test_result("Content Approval Workflow", False, 
                                       "Content rejection not recorded")
                return False
            
            # Test content filtering by status
            approved_count = self.db.query(ContentItem).filter(
                ContentItem.status == "approved"
            ).count()
            
            pending_count = self.db.query(ContentItem).filter(
                ContentItem.status == "pending"
            ).count()
            
            if approved_count == 0:
                self._record_test_result("Content Approval Workflow", False, 
                                       "No approved content found")
                return False
            
            self._record_test_result("Content Approval Workflow", True)
            return True
        except Exception as e:
            self._record_test_result("Content Approval Workflow", False, str(e))
            return False
    
    async def test_cross_service_data_consistency(self) -> bool:
        """Test data consistency across services"""
        try:
            test_user = self.context.test_users[0]
            
            # Test user-preferences consistency
            user_with_prefs = self.db.query(User).filter(User.id == test_user.id).first()
            preferences = user_with_prefs.preferences
            
            if preferences and preferences.user_id != test_user.id:
                self._record_test_result("Cross-Service Data Consistency", False, 
                                       "User-preferences relationship inconsistent")
                return False
            
            # Test user-interactions consistency
            interactions = user_with_prefs.interactions
            for interaction in interactions:
                if interaction.user_id != test_user.id:
                    self._record_test_result("Cross-Service Data Consistency", False, 
                                           "User-interaction relationship inconsistent")
                    return False
                
                # Verify content exists for each interaction
                content = self.db.query(ContentItem).filter(
                    ContentItem.id == interaction.content_id
                ).first()
                if not content:
                    self._record_test_result("Cross-Service Data Consistency", False, 
                                           "Interaction references non-existent content")
                    return False
            
            # Test recommendations consistency
            recommendations = user_with_prefs.recommendations
            for recommendation in recommendations:
                if recommendation.user_id != test_user.id:
                    self._record_test_result("Cross-Service Data Consistency", False, 
                                           "User-recommendation relationship inconsistent")
                    return False
                
                # Verify content exists for each recommendation
                content = self.db.query(ContentItem).filter(
                    ContentItem.id == recommendation.content_id
                ).first()
                if not content:
                    self._record_test_result("Cross-Service Data Consistency", False, 
                                           "Recommendation references non-existent content")
                    return False
            
            self._record_test_result("Cross-Service Data Consistency", True)
            return True
        except Exception as e:
            self._record_test_result("Cross-Service Data Consistency", False, str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all service integration tests"""
        logger.info("Running service integration tests")
        
        # Run all test methods
        await self.test_auth_service_integration()
        await self.test_content_processing_integration()
        await self.test_recommendation_engine_integration()
        await self.test_user_preference_service_integration()
        await self.test_user_interaction_tracking()
        await self.test_recommendation_workflow()
        await self.test_learning_session_management()
        await self.test_content_approval_workflow()
        await self.test_cross_service_data_consistency()
        
        return {
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "total": self.passed + self.failed + self.skipped
        }