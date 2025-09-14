"""
Integration Test Runner
Orchestrates and manages integration test execution

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Main runner class for coordinating integration tests across API, database, and services
"""

import asyncio
import pytest
import structlog
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from services.database import Base, get_db
from services.models import User, ContentItem, UserPreferences
from main import app
import os

logger = structlog.get_logger()

@dataclass
class IntegrationTestResult:
    """Result of an integration test suite"""
    test_suite: str
    passed: int
    failed: int
    skipped: int
    errors: List[str]
    execution_time: float
    timestamp: datetime

@dataclass
class IntegrationTestContext:
    """Context for integration test execution"""
    test_database_url: str
    api_client: TestClient
    db_session: Any
    test_users: List[User]
    test_content: List[ContentItem]
    cleanup_required: bool = True

class IntegrationTestRunner:
    """Main integration test runner class"""
    
    def __init__(self, test_database_url: Optional[str] = None):
        self.test_database_url = test_database_url or os.getenv(
            "TEST_DATABASE_URL", 
            "postgresql://test:test@localhost:5432/headstart_test"
        )
        self.results: List[IntegrationTestResult] = []
        self.context: Optional[IntegrationTestContext] = None
        
    async def setup_test_environment(self) -> IntegrationTestContext:
        """Set up test environment with database and API client"""
        logger.info("Setting up integration test environment")
        
        try:
            # Create test database engine
            engine = create_engine(self.test_database_url, echo=False)
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            
            # Create session
            SessionLocal = sessionmaker(bind=engine)
            db_session = SessionLocal()
            
            # Override database dependency for testing
            def override_get_db():
                try:
                    yield db_session
                finally:
                    pass  # Don't close session during tests
            
            app.dependency_overrides[get_db] = override_get_db
            
            # Create test client
            api_client = TestClient(app)
            
            # Create test data
            test_users = await self._create_test_users(db_session)
            test_content = await self._create_test_content(db_session)
            
            context = IntegrationTestContext(
                test_database_url=self.test_database_url,
                api_client=api_client,
                db_session=db_session,
                test_users=test_users,
                test_content=test_content
            )
            
            self.context = context
            logger.info("Integration test environment setup complete")
            return context
            
        except Exception as e:
            logger.error("Failed to setup test environment", error=str(e))
            raise
    
    async def _create_test_users(self, db_session) -> List[User]:
        """Create test users for integration testing"""
        from services.auth import auth_service
        
        test_users = []
        
        # Create different types of test users
        user_configs = [
            {
                "email": "active_user@test.com",
                "full_name": "Active Test User",
                "role": "learner",
                "is_active": True,
                "email_verified": True
            },
            {
                "email": "admin_user@test.com", 
                "full_name": "Admin Test User",
                "role": "admin",
                "is_active": True,
                "email_verified": True
            },
            {
                "email": "inactive_user@test.com",
                "full_name": "Inactive Test User", 
                "role": "learner",
                "is_active": False,
                "email_verified": True
            },
            {
                "email": "unverified_user@test.com",
                "full_name": "Unverified Test User",
                "role": "learner", 
                "is_active": True,
                "email_verified": False
            }
        ]
        
        for config in user_configs:
            password_hash = auth_service.hash_password("TestPassword123!")
            
            user = User(
                email=config["email"],
                password_hash=password_hash,
                full_name=config["full_name"],
                role=config["role"],
                is_active=config["is_active"],
                email_verified=config["email_verified"]
            )
            
            db_session.add(user)
            test_users.append(user)
        
        db_session.commit()
        
        # Create preferences for active users
        for user in test_users:
            if user.is_active:
                preferences = UserPreferences(
                    user_id=user.id,
                    learning_domains=["AI", "Web Development"],
                    skill_levels={"AI": "beginner", "Web Development": "intermediate"},
                    preferred_content_types=["video", "article"],
                    time_constraints={"max_duration": 60, "sessions_per_week": 3}
                )
                db_session.add(preferences)
        
        db_session.commit()
        
        # Refresh all users to get IDs
        for user in test_users:
            db_session.refresh(user)
        
        logger.info(f"Created {len(test_users)} test users")
        return test_users
    
    async def _create_test_content(self, db_session) -> List[ContentItem]:
        """Create test content for integration testing"""
        test_content = []
        
        content_configs = [
            {
                "title": "Introduction to Machine Learning",
                "description": "Basic ML concepts and algorithms",
                "content_type": "video",
                "source": "youtube",
                "difficulty_level": "beginner",
                "topics": ["AI", "Machine Learning"],
                "status": "approved"
            },
            {
                "title": "Advanced Python Programming",
                "description": "Advanced Python concepts and patterns",
                "content_type": "article",
                "source": "upload",
                "difficulty_level": "advanced", 
                "topics": ["Programming", "Python"],
                "status": "approved"
            },
            {
                "title": "Web Development with React",
                "description": "Building modern web applications",
                "content_type": "course",
                "source": "upload",
                "difficulty_level": "intermediate",
                "topics": ["Web Development", "React"],
                "status": "approved"
            },
            {
                "title": "Pending Content Item",
                "description": "Content awaiting approval",
                "content_type": "video",
                "source": "youtube", 
                "difficulty_level": "beginner",
                "topics": ["AI"],
                "status": "pending"
            }
        ]
        
        for config in content_configs:
            content = ContentItem(
                title=config["title"],
                description=config["description"],
                content_type=config["content_type"],
                source=config["source"],
                source_id=f"test_{len(test_content)}",
                url=f"https://example.com/content/{len(test_content)}",
                duration_minutes=30,
                difficulty_level=config["difficulty_level"],
                topics=config["topics"],
                language="en",
                status=config["status"]
            )
            
            db_session.add(content)
            test_content.append(content)
        
        db_session.commit()
        
        # Refresh all content to get IDs
        for content in test_content:
            db_session.refresh(content)
        
        logger.info(f"Created {len(test_content)} test content items")
        return test_content
    
    async def run_database_integration_tests(self) -> IntegrationTestResult:
        """Run database integration tests"""
        logger.info("Running database integration tests")
        start_time = datetime.now()
        
        try:
            from .database_integration import DatabaseIntegrationTests
            
            db_tests = DatabaseIntegrationTests(self.context)
            result = await db_tests.run_all_tests()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_result = IntegrationTestResult(
                test_suite="database_integration",
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", []),
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(test_result)
            return test_result
            
        except Exception as e:
            logger.error("Database integration tests failed", error=str(e))
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_result = IntegrationTestResult(
                test_suite="database_integration",
                passed=0,
                failed=1,
                skipped=0,
                errors=[str(e)],
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(test_result)
            return test_result
    
    async def run_api_integration_tests(self) -> IntegrationTestResult:
        """Run API integration tests"""
        logger.info("Running API integration tests")
        start_time = datetime.now()
        
        try:
            from .api_integration import APIIntegrationTests
            
            api_tests = APIIntegrationTests(self.context)
            result = await api_tests.run_all_tests()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_result = IntegrationTestResult(
                test_suite="api_integration",
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", []),
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(test_result)
            return test_result
            
        except Exception as e:
            logger.error("API integration tests failed", error=str(e))
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_result = IntegrationTestResult(
                test_suite="api_integration",
                passed=0,
                failed=1,
                skipped=0,
                errors=[str(e)],
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(test_result)
            return test_result
    
    async def run_service_integration_tests(self) -> IntegrationTestResult:
        """Run service-to-service integration tests"""
        logger.info("Running service integration tests")
        start_time = datetime.now()
        
        try:
            from .service_integration import ServiceIntegrationTests
            
            service_tests = ServiceIntegrationTests(self.context)
            result = await service_tests.run_all_tests()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_result = IntegrationTestResult(
                test_suite="service_integration",
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", []),
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(test_result)
            return test_result
            
        except Exception as e:
            logger.error("Service integration tests failed", error=str(e))
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_result = IntegrationTestResult(
                test_suite="service_integration",
                passed=0,
                failed=1,
                skipped=0,
                errors=[str(e)],
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(test_result)
            return test_result
    
    async def run_auth_integration_tests(self) -> IntegrationTestResult:
        """Run authentication and authorization integration tests"""
        logger.info("Running authentication integration tests")
        start_time = datetime.now()
        
        try:
            from .auth_integration import AuthIntegrationTests
            
            auth_tests = AuthIntegrationTests(self.context)
            result = await auth_tests.run_all_tests()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_result = IntegrationTestResult(
                test_suite="auth_integration",
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", []),
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(test_result)
            return test_result
            
        except Exception as e:
            logger.error("Authentication integration tests failed", error=str(e))
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_result = IntegrationTestResult(
                test_suite="auth_integration",
                passed=0,
                failed=1,
                skipped=0,
                errors=[str(e)],
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(test_result)
            return test_result
    
    async def run_data_consistency_tests(self) -> IntegrationTestResult:
        """Run data consistency validation tests"""
        logger.info("Running data consistency tests")
        start_time = datetime.now()
        
        try:
            from .data_consistency import DataConsistencyTests
            
            consistency_tests = DataConsistencyTests(self.context)
            result = await consistency_tests.run_all_tests()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_result = IntegrationTestResult(
                test_suite="data_consistency",
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", []),
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(test_result)
            return test_result
            
        except Exception as e:
            logger.error("Data consistency tests failed", error=str(e))
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_result = IntegrationTestResult(
                test_suite="data_consistency",
                passed=0,
                failed=1,
                skipped=0,
                errors=[str(e)],
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(test_result)
            return test_result
    
    async def run_all_integration_tests(self) -> Dict[str, Any]:
        """Run all integration test suites"""
        logger.info("Starting comprehensive integration test run")
        
        try:
            # Setup test environment
            await self.setup_test_environment()
            
            # Run all test suites
            db_result = await self.run_database_integration_tests()
            api_result = await self.run_api_integration_tests()
            service_result = await self.run_service_integration_tests()
            auth_result = await self.run_auth_integration_tests()
            consistency_result = await self.run_data_consistency_tests()
            
            # Calculate overall results
            total_passed = sum(r.passed for r in self.results)
            total_failed = sum(r.failed for r in self.results)
            total_skipped = sum(r.skipped for r in self.results)
            total_errors = []
            for r in self.results:
                total_errors.extend(r.errors)
            
            overall_result = {
                "status": "passed" if total_failed == 0 else "failed",
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_skipped": total_skipped,
                "total_errors": len(total_errors),
                "errors": total_errors,
                "test_suites": {
                    "database_integration": {
                        "passed": db_result.passed,
                        "failed": db_result.failed,
                        "execution_time": db_result.execution_time
                    },
                    "api_integration": {
                        "passed": api_result.passed,
                        "failed": api_result.failed,
                        "execution_time": api_result.execution_time
                    },
                    "service_integration": {
                        "passed": service_result.passed,
                        "failed": service_result.failed,
                        "execution_time": service_result.execution_time
                    },
                    "auth_integration": {
                        "passed": auth_result.passed,
                        "failed": auth_result.failed,
                        "execution_time": auth_result.execution_time
                    },
                    "data_consistency": {
                        "passed": consistency_result.passed,
                        "failed": consistency_result.failed,
                        "execution_time": consistency_result.execution_time
                    }
                },
                "total_execution_time": sum(r.execution_time for r in self.results)
            }
            
            logger.info("Integration test run completed", 
                       status=overall_result["status"],
                       total_passed=total_passed,
                       total_failed=total_failed)
            
            return overall_result
            
        except Exception as e:
            logger.error("Integration test run failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "total_passed": 0,
                "total_failed": 1
            }
        
        finally:
            # Cleanup test environment
            await self.cleanup_test_environment()
    
    async def cleanup_test_environment(self):
        """Clean up test environment and resources"""
        logger.info("Cleaning up integration test environment")
        
        try:
            if self.context and self.context.cleanup_required:
                # Clear dependency overrides
                app.dependency_overrides.clear()
                
                # Close database session
                if self.context.db_session:
                    self.context.db_session.close()
                
                # Drop test tables if needed
                if "test" in self.test_database_url:
                    from sqlalchemy import create_engine
                    engine = create_engine(self.test_database_url)
                    Base.metadata.drop_all(bind=engine)
                    engine.dispose()
                
                logger.info("Test environment cleanup completed")
                
        except Exception as e:
            logger.error("Test environment cleanup failed", error=str(e))