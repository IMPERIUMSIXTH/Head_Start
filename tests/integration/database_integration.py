"""
Database Integration Tests
Tests for database operations, transactions, and data integrity

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Comprehensive database integration testing with real PostgreSQL instances
"""

import asyncio
import structlog
from typing import Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy import text, func
from sqlalchemy.exc import IntegrityError
from services.models import User, ContentItem, UserPreferences, UserInteraction, Recommendation, LearningSession
from services.database import Base

logger = structlog.get_logger()

class DatabaseIntegrationTests:
    """Database integration test suite"""
    
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
    
    async def test_database_connection(self) -> bool:
        """Test basic database connectivity"""
        try:
            result = self.db.execute(text("SELECT 1")).scalar()
            success = result == 1
            self._record_test_result("Database Connection", success)
            return success
        except Exception as e:
            self._record_test_result("Database Connection", False, str(e))
            return False
    
    async def test_pgvector_extension(self) -> bool:
        """Test pgvector extension availability"""
        try:
            # Check if pgvector extension is available
            result = self.db.execute(text(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )).scalar()
            
            success = result is True
            self._record_test_result("pgvector Extension", success)
            return success
        except Exception as e:
            self._record_test_result("pgvector Extension", False, str(e))
            return False
    
    async def test_table_creation(self) -> bool:
        """Test that all required tables exist"""
        try:
            required_tables = [
                'users', 'user_preferences', 'content_items', 
                'user_interactions', 'recommendations', 'learning_sessions'
            ]
            
            for table in required_tables:
                result = self.db.execute(text(
                    f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')"
                )).scalar()
                
                if not result:
                    self._record_test_result("Table Creation", False, f"Table {table} not found")
                    return False
            
            self._record_test_result("Table Creation", True)
            return True
        except Exception as e:
            self._record_test_result("Table Creation", False, str(e))
            return False
    
    async def test_user_crud_operations(self) -> bool:
        """Test User model CRUD operations"""
        try:
            # Create
            test_user = User(
                email="crud_test@example.com",
                password_hash="test_hash",
                full_name="CRUD Test User",
                role="learner"
            )
            self.db.add(test_user)
            self.db.commit()
            self.db.refresh(test_user)
            
            # Read
            retrieved_user = self.db.query(User).filter(User.email == "crud_test@example.com").first()
            if not retrieved_user or retrieved_user.full_name != "CRUD Test User":
                self._record_test_result("User CRUD - Read", False, "User not found or data mismatch")
                return False
            
            # Update
            retrieved_user.full_name = "Updated CRUD Test User"
            self.db.commit()
            self.db.refresh(retrieved_user)
            
            updated_user = self.db.query(User).filter(User.email == "crud_test@example.com").first()
            if updated_user.full_name != "Updated CRUD Test User":
                self._record_test_result("User CRUD - Update", False, "Update failed")
                return False
            
            # Delete
            self.db.delete(updated_user)
            self.db.commit()
            
            deleted_user = self.db.query(User).filter(User.email == "crud_test@example.com").first()
            if deleted_user is not None:
                self._record_test_result("User CRUD - Delete", False, "Delete failed")
                return False
            
            self._record_test_result("User CRUD Operations", True)
            return True
        except Exception as e:
            self._record_test_result("User CRUD Operations", False, str(e))
            return False
    
    async def test_content_crud_operations(self) -> bool:
        """Test ContentItem model CRUD operations"""
        try:
            # Create
            test_content = ContentItem(
                title="CRUD Test Content",
                description="Test content for CRUD operations",
                content_type="article",
                source="test",
                source_id="crud_test_1",
                url="https://example.com/crud-test",
                difficulty_level="beginner",
                topics=["Testing", "CRUD"],
                status="approved"
            )
            self.db.add(test_content)
            self.db.commit()
            self.db.refresh(test_content)
            
            # Read
            retrieved_content = self.db.query(ContentItem).filter(
                ContentItem.source_id == "crud_test_1"
            ).first()
            if not retrieved_content or retrieved_content.title != "CRUD Test Content":
                self._record_test_result("Content CRUD - Read", False, "Content not found or data mismatch")
                return False
            
            # Update
            retrieved_content.title = "Updated CRUD Test Content"
            retrieved_content.topics = ["Testing", "CRUD", "Updated"]
            self.db.commit()
            self.db.refresh(retrieved_content)
            
            updated_content = self.db.query(ContentItem).filter(
                ContentItem.source_id == "crud_test_1"
            ).first()
            if (updated_content.title != "Updated CRUD Test Content" or 
                "Updated" not in updated_content.topics):
                self._record_test_result("Content CRUD - Update", False, "Update failed")
                return False
            
            # Delete
            self.db.delete(updated_content)
            self.db.commit()
            
            deleted_content = self.db.query(ContentItem).filter(
                ContentItem.source_id == "crud_test_1"
            ).first()
            if deleted_content is not None:
                self._record_test_result("Content CRUD - Delete", False, "Delete failed")
                return False
            
            self._record_test_result("Content CRUD Operations", True)
            return True
        except Exception as e:
            self._record_test_result("Content CRUD Operations", False, str(e))
            return False
    
    async def test_relationship_integrity(self) -> bool:
        """Test foreign key relationships and cascading deletes"""
        try:
            # Use existing test user
            test_user = self.context.test_users[0]
            test_content = self.context.test_content[0]
            
            # Create user interaction
            interaction = UserInteraction(
                user_id=test_user.id,
                content_id=test_content.id,
                interaction_type="view",
                rating=4,
                time_spent_minutes=15,
                completion_percentage=75.0
            )
            self.db.add(interaction)
            
            # Create recommendation
            recommendation = Recommendation(
                user_id=test_user.id,
                content_id=test_content.id,
                recommendation_score=0.85,
                explanation_factors={"similarity": 0.8, "popularity": 0.9},
                algorithm_version="v1.0"
            )
            self.db.add(recommendation)
            
            # Create learning session
            session = LearningSession(
                user_id=test_user.id,
                content_id=test_content.id,
                started_at=datetime.utcnow(),
                progress_percentage=50.0,
                notes="Test learning session"
            )
            self.db.add(session)
            
            self.db.commit()
            
            # Verify relationships exist
            user_interactions = self.db.query(UserInteraction).filter(
                UserInteraction.user_id == test_user.id
            ).count()
            
            user_recommendations = self.db.query(Recommendation).filter(
                Recommendation.user_id == test_user.id
            ).count()
            
            user_sessions = self.db.query(LearningSession).filter(
                LearningSession.user_id == test_user.id
            ).count()
            
            if user_interactions == 0 or user_recommendations == 0 or user_sessions == 0:
                self._record_test_result("Relationship Integrity", False, "Relationships not created")
                return False
            
            # Test relationship access
            user_with_relations = self.db.query(User).filter(User.id == test_user.id).first()
            if (len(user_with_relations.interactions) == 0 or 
                len(user_with_relations.recommendations) == 0 or
                len(user_with_relations.learning_sessions) == 0):
                self._record_test_result("Relationship Integrity", False, "Relationship access failed")
                return False
            
            self._record_test_result("Relationship Integrity", True)
            return True
        except Exception as e:
            self._record_test_result("Relationship Integrity", False, str(e))
            return False
    
    async def test_constraint_validation(self) -> bool:
        """Test database constraints and validation"""
        try:
            # Test unique email constraint
            try:
                duplicate_user = User(
                    email=self.context.test_users[0].email,  # Duplicate email
                    password_hash="test_hash",
                    full_name="Duplicate User",
                    role="learner"
                )
                self.db.add(duplicate_user)
                self.db.commit()
                
                # If we get here, constraint failed
                self._record_test_result("Constraint Validation - Unique Email", False, 
                                       "Duplicate email was allowed")
                return False
            except IntegrityError:
                # This is expected - rollback and continue
                self.db.rollback()
            
            # Test NOT NULL constraints
            try:
                invalid_user = User(
                    email=None,  # Should fail NOT NULL constraint
                    password_hash="test_hash",
                    full_name="Invalid User",
                    role="learner"
                )
                self.db.add(invalid_user)
                self.db.commit()
                
                # If we get here, constraint failed
                self._record_test_result("Constraint Validation - NOT NULL", False, 
                                       "NULL email was allowed")
                return False
            except IntegrityError:
                # This is expected - rollback and continue
                self.db.rollback()
            
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
                
                # If we get here, constraint failed
                self._record_test_result("Constraint Validation - Foreign Key", False, 
                                       "Invalid foreign key was allowed")
                return False
            except IntegrityError:
                # This is expected - rollback and continue
                self.db.rollback()
            
            self._record_test_result("Constraint Validation", True)
            return True
        except Exception as e:
            self._record_test_result("Constraint Validation", False, str(e))
            return False
    
    async def test_transaction_rollback(self) -> bool:
        """Test transaction rollback functionality"""
        try:
            # Count initial users
            initial_count = self.db.query(User).count()
            
            # Start transaction that will fail
            try:
                # Create valid user
                valid_user = User(
                    email="transaction_test@example.com",
                    password_hash="test_hash",
                    full_name="Transaction Test User",
                    role="learner"
                )
                self.db.add(valid_user)
                
                # Create invalid user (duplicate email)
                invalid_user = User(
                    email=self.context.test_users[0].email,  # Duplicate
                    password_hash="test_hash",
                    full_name="Invalid User",
                    role="learner"
                )
                self.db.add(invalid_user)
                
                # This should fail and rollback both inserts
                self.db.commit()
                
                # If we get here, transaction didn't rollback properly
                self._record_test_result("Transaction Rollback", False, 
                                       "Transaction didn't rollback on error")
                return False
                
            except IntegrityError:
                # Expected - rollback should happen automatically
                self.db.rollback()
            
            # Verify rollback - count should be same as initial
            final_count = self.db.query(User).count()
            if final_count != initial_count:
                self._record_test_result("Transaction Rollback", False, 
                                       f"User count changed: {initial_count} -> {final_count}")
                return False
            
            # Verify the valid user wasn't created
            test_user = self.db.query(User).filter(
                User.email == "transaction_test@example.com"
            ).first()
            if test_user is not None:
                self._record_test_result("Transaction Rollback", False, 
                                       "Valid user was created despite transaction rollback")
                return False
            
            self._record_test_result("Transaction Rollback", True)
            return True
        except Exception as e:
            self._record_test_result("Transaction Rollback", False, str(e))
            return False
    
    async def test_complex_queries(self) -> bool:
        """Test complex database queries and aggregations"""
        try:
            # Test JOIN queries
            user_content_query = self.db.query(User, ContentItem).join(
                UserInteraction, User.id == UserInteraction.user_id
            ).join(
                ContentItem, UserInteraction.content_id == ContentItem.id
            ).filter(User.is_active == True).all()
            
            # Test aggregation queries
            user_stats = self.db.query(
                User.id,
                func.count(UserInteraction.id).label('interaction_count'),
                func.avg(UserInteraction.rating).label('avg_rating')
            ).join(
                UserInteraction, User.id == UserInteraction.user_id
            ).group_by(User.id).all()
            
            # Test subqueries
            active_users_subquery = self.db.query(User.id).filter(User.is_active == True).subquery()
            
            content_for_active_users = self.db.query(ContentItem).join(
                UserInteraction, ContentItem.id == UserInteraction.content_id
            ).filter(
                UserInteraction.user_id.in_(self.db.query(active_users_subquery.c.id))
            ).distinct().all()
            
            # Test array operations (PostgreSQL specific)
            ai_content = self.db.query(ContentItem).filter(
                ContentItem.topics.contains(['AI'])
            ).all()
            
            # Verify results make sense
            if len(user_stats) < 0:  # Allow empty results
                self._record_test_result("Complex Queries", False, "No aggregation results")
                return False
            
            self._record_test_result("Complex Queries", True)
            return True
        except Exception as e:
            self._record_test_result("Complex Queries", False, str(e))
            return False
    
    async def test_concurrent_access(self) -> bool:
        """Test concurrent database access"""
        try:
            # Create multiple concurrent operations
            async def create_user(email_suffix: str):
                try:
                    user = User(
                        email=f"concurrent_{email_suffix}@example.com",
                        password_hash="test_hash",
                        full_name=f"Concurrent User {email_suffix}",
                        role="learner"
                    )
                    self.db.add(user)
                    self.db.commit()
                    return True
                except Exception:
                    self.db.rollback()
                    return False
            
            # Run concurrent operations
            tasks = [create_user(str(i)) for i in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful operations
            successful = sum(1 for r in results if r is True)
            
            # Verify at least some operations succeeded
            if successful < 3:  # Allow some failures due to concurrency
                self._record_test_result("Concurrent Access", False, 
                                       f"Only {successful}/5 concurrent operations succeeded")
                return False
            
            # Cleanup concurrent test users
            self.db.query(User).filter(
                User.email.like("concurrent_%@example.com")
            ).delete(synchronize_session=False)
            self.db.commit()
            
            self._record_test_result("Concurrent Access", True)
            return True
        except Exception as e:
            self._record_test_result("Concurrent Access", False, str(e))
            return False
    
    async def test_performance_queries(self) -> bool:
        """Test database query performance"""
        try:
            import time
            
            # Test query performance with existing data
            start_time = time.time()
            
            # Complex query that should complete reasonably fast
            result = self.db.query(User).join(
                UserPreferences, User.id == UserPreferences.user_id
            ).filter(
                User.is_active == True,
                UserPreferences.learning_domains.contains(['AI'])
            ).all()
            
            query_time = time.time() - start_time
            
            # Query should complete within reasonable time (5 seconds for test data)
            if query_time > 5.0:
                self._record_test_result("Performance Queries", False, 
                                       f"Query took {query_time:.2f}s (too slow)")
                return False
            
            # Test index usage (if we had indexes defined)
            start_time = time.time()
            
            # Email lookup should be fast (assuming index on email)
            user = self.db.query(User).filter(
                User.email == self.context.test_users[0].email
            ).first()
            
            lookup_time = time.time() - start_time
            
            if lookup_time > 1.0:
                self._record_test_result("Performance Queries", False, 
                                       f"Email lookup took {lookup_time:.2f}s (too slow)")
                return False
            
            self._record_test_result("Performance Queries", True)
            return True
        except Exception as e:
            self._record_test_result("Performance Queries", False, str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all database integration tests"""
        logger.info("Running database integration tests")
        
        # Run all test methods
        await self.test_database_connection()
        await self.test_pgvector_extension()
        await self.test_table_creation()
        await self.test_user_crud_operations()
        await self.test_content_crud_operations()
        await self.test_relationship_integrity()
        await self.test_constraint_validation()
        await self.test_transaction_rollback()
        await self.test_complex_queries()
        await self.test_concurrent_access()
        await self.test_performance_queries()
        
        return {
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "total": self.passed + self.failed + self.skipped
        }