"""
Data Consistency Integration Tests
Tests for data integrity, consistency, and validation across services

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Data consistency validation across all system components
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from services.models import User, ContentItem, UserPreferences, UserInteraction, Recommendation, LearningSession

logger = structlog.get_logger()

class DataConsistencyTests:
    """Data consistency integration test suite"""
    
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
    
    async def test_referential_integrity(self) -> bool:
        """Test referential integrity across all relationships"""
        try:
            # Test User -> UserPreferences relationship
            users_with_prefs = self.db.query(User).join(UserPreferences).all()
            for user in users_with_prefs:
                if user.preferences.user_id != user.id:
                    self._record_test_result("Referential Integrity - User Preferences", False, 
                                           f"User {user.id} preferences reference wrong user")
                    return False
            
            # Test User -> UserInteraction relationship
            users_with_interactions = self.db.query(User).join(UserInteraction).all()
            for user in users_with_interactions:
                for interaction in user.interactions:
                    if interaction.user_id != user.id:
                        self._record_test_result("Referential Integrity - User Interactions", False, 
                                               f"User {user.id} interaction references wrong user")
                        return False
                    
                    # Verify content exists for interaction
                    content = self.db.query(ContentItem).filter(
                        ContentItem.id == interaction.content_id
                    ).first()
                    if not content:
                        self._record_test_result("Referential Integrity - Interaction Content", False, 
                                               f"Interaction {interaction.id} references non-existent content")
                        return False
            
            # Test User -> Recommendation relationship
            users_with_recommendations = self.db.query(User).join(Recommendation).all()
            for user in users_with_recommendations:
                for recommendation in user.recommendations:
                    if recommendation.user_id != user.id:
                        self._record_test_result("Referential Integrity - User Recommendations", False, 
                                               f"User {user.id} recommendation references wrong user")
                        return False
                    
                    # Verify content exists for recommendation
                    content = self.db.query(ContentItem).filter(
                        ContentItem.id == recommendation.content_id
                    ).first()
                    if not content:
                        self._record_test_result("Referential Integrity - Recommendation Content", False, 
                                               f"Recommendation {recommendation.id} references non-existent content")
                        return False
            
            # Test User -> LearningSession relationship
            users_with_sessions = self.db.query(User).join(LearningSession).all()
            for user in users_with_sessions:
                for session in user.learning_sessions:
                    if session.user_id != user.id:
                        self._record_test_result("Referential Integrity - User Sessions", False, 
                                               f"User {user.id} session references wrong user")
                        return False
                    
                    # Verify content exists for session
                    content = self.db.query(ContentItem).filter(
                        ContentItem.id == session.content_id
                    ).first()
                    if not content:
                        self._record_test_result("Referential Integrity - Session Content", False, 
                                               f"Session {session.id} references non-existent content")
                        return False
            
            self._record_test_result("Referential Integrity", True)
            return True
        except Exception as e:
            self._record_test_result("Referential Integrity", False, str(e))
            return False
    
    async def test_data_validation_constraints(self) -> bool:
        """Test data validation and database constraints"""
        try:
            # Test email uniqueness constraint
            try:
                duplicate_user = User(
                    email=self.context.test_users[0].email,  # Duplicate email
                    password_hash="test_hash",
                    full_name="Duplicate User",
                    role="learner"
                )
                self.db.add(duplicate_user)
                self.db.commit()
                
                self._record_test_result("Data Validation - Email Uniqueness", False, 
                                       "Duplicate email was allowed")
                return False
            except IntegrityError:
                self.db.rollback()  # Expected behavior
            
            # Test NOT NULL constraints
            try:
                invalid_user = User(
                    email=None,  # Should violate NOT NULL
                    password_hash="test_hash",
                    full_name="Invalid User",
                    role="learner"
                )
                self.db.add(invalid_user)
                self.db.commit()
                
                self._record_test_result("Data Validation - NOT NULL", False, 
                                       "NULL email was allowed")
                return False
            except IntegrityError:
                self.db.rollback()  # Expected behavior
            
            # Test foreign key constraints
            try:
                import uuid
                invalid_interaction = UserInteraction(
                    user_id=uuid.uuid4(),  # Non-existent user
                    content_id=self.context.test_content[0].id,
                    interaction_type="view"
                )
                self.db.add(invalid_interaction)
                self.db.commit()
                
                self._record_test_result("Data Validation - Foreign Key", False, 
                                       "Invalid foreign key was allowed")
                return False
            except IntegrityError:
                self.db.rollback()  # Expected behavior
            
            # Test enum-like constraints (if implemented)
            valid_roles = ["learner", "admin", "moderator"]
            test_user = self.context.test_users[0]
            
            if test_user.role not in valid_roles:
                self._record_test_result("Data Validation - Role Constraint", False, 
                                       f"Invalid role found: {test_user.role}")
                return False
            
            # Test rating constraints (1-5 range)
            interactions_with_ratings = self.db.query(UserInteraction).filter(
                UserInteraction.rating.isnot(None)
            ).all()
            
            for interaction in interactions_with_ratings:
                if interaction.rating < 1 or interaction.rating > 5:
                    self._record_test_result("Data Validation - Rating Range", False, 
                                           f"Invalid rating found: {interaction.rating}")
                    return False
            
            self._record_test_result("Data Validation Constraints", True)
            return True
        except Exception as e:
            self._record_test_result("Data Validation Constraints", False, str(e))
            return False
    
    async def test_cascade_operations(self) -> bool:
        """Test cascade delete and update operations"""
        try:
            # Create test user with related data
            test_user = User(
                email="cascade_test@example.com",
                password_hash="test_hash",
                full_name="Cascade Test User",
                role="learner"
            )
            self.db.add(test_user)
            self.db.commit()
            self.db.refresh(test_user)
            
            # Create related data
            preferences = UserPreferences(
                user_id=test_user.id,
                learning_domains=["Testing"],
                skill_levels={"Testing": "advanced"}
            )
            self.db.add(preferences)
            
            interaction = UserInteraction(
                user_id=test_user.id,
                content_id=self.context.test_content[0].id,
                interaction_type="view"
            )
            self.db.add(interaction)
            
            recommendation = Recommendation(
                user_id=test_user.id,
                content_id=self.context.test_content[0].id,
                recommendation_score=0.8,
                algorithm_version="test_v1.0"
            )
            self.db.add(recommendation)
            
            session = LearningSession(
                user_id=test_user.id,
                content_id=self.context.test_content[0].id,
                progress_percentage=50.0
            )
            self.db.add(session)
            
            self.db.commit()
            
            # Verify related data exists
            prefs_count = self.db.query(UserPreferences).filter(
                UserPreferences.user_id == test_user.id
            ).count()
            interactions_count = self.db.query(UserInteraction).filter(
                UserInteraction.user_id == test_user.id
            ).count()
            recommendations_count = self.db.query(Recommendation).filter(
                Recommendation.user_id == test_user.id
            ).count()
            sessions_count = self.db.query(LearningSession).filter(
                LearningSession.user_id == test_user.id
            ).count()
            
            if (prefs_count == 0 or interactions_count == 0 or 
                recommendations_count == 0 or sessions_count == 0):
                self._record_test_result("Cascade Operations - Setup", False, 
                                       "Related data not created properly")
                return False
            
            # Delete user (should cascade to related data)
            self.db.delete(test_user)
            self.db.commit()
            
            # Verify cascade delete worked
            remaining_prefs = self.db.query(UserPreferences).filter(
                UserPreferences.user_id == test_user.id
            ).count()
            remaining_interactions = self.db.query(UserInteraction).filter(
                UserInteraction.user_id == test_user.id
            ).count()
            remaining_recommendations = self.db.query(Recommendation).filter(
                Recommendation.user_id == test_user.id
            ).count()
            remaining_sessions = self.db.query(LearningSession).filter(
                LearningSession.user_id == test_user.id
            ).count()
            
            if (remaining_prefs > 0 or remaining_interactions > 0 or 
                remaining_recommendations > 0 or remaining_sessions > 0):
                self._record_test_result("Cascade Operations", False, 
                                       "Cascade delete did not work properly")
                return False
            
            self._record_test_result("Cascade Operations", True)
            return True
        except Exception as e:
            self._record_test_result("Cascade Operations", False, str(e))
            return False
    
    async def test_data_consistency_across_transactions(self) -> bool:
        """Test data consistency across multiple transactions"""
        try:
            test_user = self.context.test_users[0]
            test_content = self.context.test_content[0]
            
            # Start first transaction - create interaction
            interaction1 = UserInteraction(
                user_id=test_user.id,
                content_id=test_content.id,
                interaction_type="view",
                time_spent_minutes=10
            )
            self.db.add(interaction1)
            self.db.commit()
            
            # Start second transaction - create another interaction
            interaction2 = UserInteraction(
                user_id=test_user.id,
                content_id=test_content.id,
                interaction_type="like",
                rating=4
            )
            self.db.add(interaction2)
            self.db.commit()
            
            # Verify both interactions exist and are consistent
            user_interactions = self.db.query(UserInteraction).filter(
                UserInteraction.user_id == test_user.id,
                UserInteraction.content_id == test_content.id
            ).all()
            
            if len(user_interactions) < 2:
                self._record_test_result("Transaction Consistency", False, 
                                       f"Expected at least 2 interactions, found {len(user_interactions)}")
                return False
            
            # Verify data integrity
            for interaction in user_interactions:
                if (interaction.user_id != test_user.id or 
                    interaction.content_id != test_content.id):
                    self._record_test_result("Transaction Consistency", False, 
                                           "Interaction data inconsistent")
                    return False
            
            # Test concurrent transaction scenario
            async def create_interaction(interaction_type: str, rating: int = None):
                try:
                    interaction = UserInteraction(
                        user_id=test_user.id,
                        content_id=test_content.id,
                        interaction_type=interaction_type,
                        rating=rating
                    )
                    self.db.add(interaction)
                    self.db.commit()
                    return True
                except Exception:
                    self.db.rollback()
                    return False
            
            # Run concurrent transactions
            tasks = [
                create_interaction("bookmark"),
                create_interaction("share"),
                create_interaction("complete", 5)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify at least some transactions succeeded
            successful = sum(1 for r in results if r is True)
            if successful < 2:
                self._record_test_result("Transaction Consistency", False, 
                                       f"Only {successful}/3 concurrent transactions succeeded")
                return False
            
            self._record_test_result("Data Consistency Across Transactions", True)
            return True
        except Exception as e:
            self._record_test_result("Data Consistency Across Transactions", False, str(e))
            return False
    
    async def test_data_aggregation_consistency(self) -> bool:
        """Test consistency of data aggregations and calculations"""
        try:
            test_user = self.context.test_users[0]
            
            # Get user interactions for aggregation
            interactions = self.db.query(UserInteraction).filter(
                UserInteraction.user_id == test_user.id
            ).all()
            
            if len(interactions) == 0:
                # Create some test interactions
                test_content = self.context.test_content[0]
                for i in range(3):
                    interaction = UserInteraction(
                        user_id=test_user.id,
                        content_id=test_content.id,
                        interaction_type="view",
                        rating=4 + i % 2,  # Ratings of 4 and 5
                        time_spent_minutes=10 + i * 5
                    )
                    self.db.add(interaction)
                self.db.commit()
                
                interactions = self.db.query(UserInteraction).filter(
                    UserInteraction.user_id == test_user.id
                ).all()
            
            # Test aggregation consistency
            # Manual calculation
            manual_total_time = sum(i.time_spent_minutes or 0 for i in interactions)
            manual_avg_rating = sum(i.rating for i in interactions if i.rating) / len([i for i in interactions if i.rating])
            manual_interaction_count = len(interactions)
            
            # Database aggregation
            db_total_time = self.db.query(func.sum(UserInteraction.time_spent_minutes)).filter(
                UserInteraction.user_id == test_user.id
            ).scalar() or 0
            
            db_avg_rating = self.db.query(func.avg(UserInteraction.rating)).filter(
                UserInteraction.user_id == test_user.id,
                UserInteraction.rating.isnot(None)
            ).scalar()
            
            db_interaction_count = self.db.query(func.count(UserInteraction.id)).filter(
                UserInteraction.user_id == test_user.id
            ).scalar()
            
            # Compare results
            if abs(manual_total_time - db_total_time) > 0.01:
                self._record_test_result("Data Aggregation Consistency", False, 
                                       f"Total time mismatch: manual={manual_total_time}, db={db_total_time}")
                return False
            
            if db_avg_rating and abs(manual_avg_rating - float(db_avg_rating)) > 0.01:
                self._record_test_result("Data Aggregation Consistency", False, 
                                       f"Average rating mismatch: manual={manual_avg_rating}, db={db_avg_rating}")
                return False
            
            if manual_interaction_count != db_interaction_count:
                self._record_test_result("Data Aggregation Consistency", False, 
                                       f"Count mismatch: manual={manual_interaction_count}, db={db_interaction_count}")
                return False
            
            self._record_test_result("Data Aggregation Consistency", True)
            return True
        except Exception as e:
            self._record_test_result("Data Aggregation Consistency", False, str(e))
            return False
    
    async def test_temporal_data_consistency(self) -> bool:
        """Test consistency of temporal data (timestamps, dates)"""
        try:
            # Test created_at timestamps
            users = self.db.query(User).all()
            for user in users:
                if user.created_at is None:
                    self._record_test_result("Temporal Data Consistency", False, 
                                           f"User {user.id} missing created_at timestamp")
                    return False
                
                if user.created_at > datetime.utcnow():
                    self._record_test_result("Temporal Data Consistency", False, 
                                           f"User {user.id} created_at is in the future")
                    return False
            
            # Test updated_at timestamps
            preferences = self.db.query(UserPreferences).all()
            for pref in preferences:
                if pref.created_at is None or pref.updated_at is None:
                    self._record_test_result("Temporal Data Consistency", False, 
                                           f"Preferences {pref.id} missing timestamps")
                    return False
                
                if pref.updated_at < pref.created_at:
                    self._record_test_result("Temporal Data Consistency", False, 
                                           f"Preferences {pref.id} updated_at before created_at")
                    return False
            
            # Test learning session temporal consistency
            sessions = self.db.query(LearningSession).all()
            for session in sessions:
                if session.started_at is None:
                    self._record_test_result("Temporal Data Consistency", False, 
                                           f"Session {session.id} missing started_at")
                    return False
                
                if session.ended_at and session.ended_at < session.started_at:
                    self._record_test_result("Temporal Data Consistency", False, 
                                           f"Session {session.id} ended before it started")
                    return False
            
            # Test recommendation temporal data
            recommendations = self.db.query(Recommendation).all()
            for rec in recommendations:
                if rec.shown_at is None:
                    self._record_test_result("Temporal Data Consistency", False, 
                                           f"Recommendation {rec.id} missing shown_at")
                    return False
                
                if rec.clicked_at and rec.clicked_at < rec.shown_at:
                    self._record_test_result("Temporal Data Consistency", False, 
                                           f"Recommendation {rec.id} clicked before shown")
                    return False
            
            self._record_test_result("Temporal Data Consistency", True)
            return True
        except Exception as e:
            self._record_test_result("Temporal Data Consistency", False, str(e))
            return False
    
    async def test_json_data_consistency(self) -> bool:
        """Test consistency of JSON/JSONB data fields"""
        try:
            # Test user preferences JSON fields
            preferences = self.db.query(UserPreferences).all()
            for pref in preferences:
                # Test skill_levels JSON structure
                if pref.skill_levels:
                    if not isinstance(pref.skill_levels, dict):
                        self._record_test_result("JSON Data Consistency", False, 
                                               f"Preferences {pref.id} skill_levels not a dict")
                        return False
                    
                    for domain, level in pref.skill_levels.items():
                        if level not in ['beginner', 'intermediate', 'advanced']:
                            self._record_test_result("JSON Data Consistency", False, 
                                                   f"Invalid skill level: {level}")
                            return False
                
                # Test time_constraints JSON structure
                if pref.time_constraints:
                    if not isinstance(pref.time_constraints, dict):
                        self._record_test_result("JSON Data Consistency", False, 
                                               f"Preferences {pref.id} time_constraints not a dict")
                        return False
            
            # Test content metadata JSON fields
            content_items = self.db.query(ContentItem).all()
            for content in content_items:
                if content.content_metadata:
                    if not isinstance(content.content_metadata, dict):
                        self._record_test_result("JSON Data Consistency", False,
                                               f"Content {content.id} content_metadata not a dict")
                        return False
            
            # Test recommendation explanation_factors JSON
            recommendations = self.db.query(Recommendation).all()
            for rec in recommendations:
                if rec.explanation_factors:
                    if not isinstance(rec.explanation_factors, dict):
                        self._record_test_result("JSON Data Consistency", False, 
                                               f"Recommendation {rec.id} explanation_factors not a dict")
                        return False
                    
                    # Verify all factors are numeric
                    for factor, value in rec.explanation_factors.items():
                        if not isinstance(value, (int, float)):
                            self._record_test_result("JSON Data Consistency", False, 
                                                   f"Non-numeric factor value: {factor}={value}")
                            return False
            
            self._record_test_result("JSON Data Consistency", True)
            return True
        except Exception as e:
            self._record_test_result("JSON Data Consistency", False, str(e))
            return False
    
    async def test_array_data_consistency(self) -> bool:
        """Test consistency of array data fields"""
        try:
            # Test content topics arrays
            content_items = self.db.query(ContentItem).all()
            for content in content_items:
                if content.topics:
                    if not isinstance(content.topics, list):
                        self._record_test_result("Array Data Consistency", False, 
                                               f"Content {content.id} topics not a list")
                        return False
                    
                    # Verify all topics are strings
                    for topic in content.topics:
                        if not isinstance(topic, str):
                            self._record_test_result("Array Data Consistency", False, 
                                                   f"Non-string topic: {topic}")
                            return False
            
            # Test user preferences arrays
            preferences = self.db.query(UserPreferences).all()
            for pref in preferences:
                if pref.learning_domains:
                    if not isinstance(pref.learning_domains, list):
                        self._record_test_result("Array Data Consistency", False, 
                                               f"Preferences {pref.id} learning_domains not a list")
                        return False
                
                if pref.preferred_content_types:
                    if not isinstance(pref.preferred_content_types, list):
                        self._record_test_result("Array Data Consistency", False, 
                                               f"Preferences {pref.id} preferred_content_types not a list")
                        return False
                
                if pref.language_preferences:
                    if not isinstance(pref.language_preferences, list):
                        self._record_test_result("Array Data Consistency", False, 
                                               f"Preferences {pref.id} language_preferences not a list")
                        return False
            
            self._record_test_result("Array Data Consistency", True)
            return True
        except Exception as e:
            self._record_test_result("Array Data Consistency", False, str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all data consistency tests"""
        logger.info("Running data consistency tests")
        
        # Run all test methods
        await self.test_referential_integrity()
        await self.test_data_validation_constraints()
        await self.test_cascade_operations()
        await self.test_data_consistency_across_transactions()
        await self.test_data_aggregation_consistency()
        await self.test_temporal_data_consistency()
        await self.test_json_data_consistency()
        await self.test_array_data_consistency()
        
        return {
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "total": self.passed + self.failed + self.skipped
        }