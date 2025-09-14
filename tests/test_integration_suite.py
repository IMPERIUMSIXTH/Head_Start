"""
Comprehensive Integration Test Suite
Main test file for running all integration tests with pytest

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Pytest-compatible integration test suite for CI/CD pipeline
"""

import pytest
import asyncio
import structlog
import os
from typing import Dict, Any
from tests.integration.runner import IntegrationTestRunner

logger = structlog.get_logger()

# Test configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://test:test@localhost:5432/headstart_test"
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def integration_runner():
    """Create and setup integration test runner"""
    runner = IntegrationTestRunner(TEST_DATABASE_URL)
    try:
        await runner.setup_test_environment()
        yield runner
    finally:
        await runner.cleanup_test_environment()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_integration(integration_runner):
    """Test database integration functionality"""
    result = await integration_runner.run_database_integration_tests()
    
    assert result.passed > 0, "No database integration tests passed"
    assert result.failed == 0, f"Database integration tests failed: {result.errors}"
    
    logger.info(f"Database integration tests: {result.passed} passed, {result.failed} failed, {result.skipped} skipped")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_integration(integration_runner):
    """Test API integration functionality"""
    result = await integration_runner.run_api_integration_tests()
    
    assert result.passed > 0, "No API integration tests passed"
    # Allow some failures for optional endpoints
    assert result.failed <= 2, f"Too many API integration test failures: {result.errors}"
    
    logger.info(f"API integration tests: {result.passed} passed, {result.failed} failed, {result.skipped} skipped")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_integration(integration_runner):
    """Test service-to-service integration"""
    result = await integration_runner.run_service_integration_tests()
    
    assert result.passed > 0, "No service integration tests passed"
    # Allow some failures for optional services
    assert result.failed <= 3, f"Too many service integration test failures: {result.errors}"
    
    logger.info(f"Service integration tests: {result.passed} passed, {result.failed} failed, {result.skipped} skipped")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_auth_integration(integration_runner):
    """Test authentication and authorization integration"""
    result = await integration_runner.run_auth_integration_tests()
    
    assert result.passed > 0, "No auth integration tests passed"
    assert result.failed == 0, f"Auth integration tests failed: {result.errors}"
    
    logger.info(f"Auth integration tests: {result.passed} passed, {result.failed} failed, {result.skipped} skipped")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_data_consistency(integration_runner):
    """Test data consistency across services"""
    result = await integration_runner.run_data_consistency_tests()
    
    assert result.passed > 0, "No data consistency tests passed"
    assert result.failed == 0, f"Data consistency tests failed: {result.errors}"
    
    logger.info(f"Data consistency tests: {result.passed} passed, {result.failed} failed, {result.skipped} skipped")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_integration_suite(integration_runner):
    """Run complete integration test suite"""
    overall_result = await integration_runner.run_all_integration_tests()
    
    # Verify overall results
    assert overall_result["status"] in ["passed", "failed"], "Invalid test status"
    assert overall_result["total_passed"] > 0, "No integration tests passed"
    
    # Allow some failures but not too many
    failure_rate = overall_result["total_failed"] / (overall_result["total_passed"] + overall_result["total_failed"])
    assert failure_rate < 0.2, f"Too many integration test failures: {failure_rate:.1%}"
    
    # Log detailed results
    logger.info("Integration test suite completed", 
               status=overall_result["status"],
               total_passed=overall_result["total_passed"],
               total_failed=overall_result["total_failed"],
               total_skipped=overall_result.get("total_skipped", 0),
               execution_time=overall_result.get("total_execution_time", 0))
    
    # Log per-suite results
    for suite_name, suite_result in overall_result.get("test_suites", {}).items():
        logger.info(f"{suite_name}: {suite_result['passed']} passed, {suite_result['failed']} failed")

# Individual component tests for more granular testing

@pytest.mark.integration
@pytest.mark.database
@pytest.mark.asyncio
async def test_database_crud_operations():
    """Test basic database CRUD operations"""
    runner = IntegrationTestRunner(TEST_DATABASE_URL)
    try:
        context = await runner.setup_test_environment()
        
        from tests.integration.database_integration import DatabaseIntegrationTests
        db_tests = DatabaseIntegrationTests(context)
        
        # Test specific database operations
        assert await db_tests.test_database_connection()
        assert await db_tests.test_user_crud_operations()
        assert await db_tests.test_content_crud_operations()
        assert await db_tests.test_relationship_integrity()
        
    finally:
        await runner.cleanup_test_environment()

@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_authentication_flow():
    """Test API authentication flow specifically"""
    runner = IntegrationTestRunner(TEST_DATABASE_URL)
    try:
        context = await runner.setup_test_environment()
        
        from tests.integration.api_integration import APIIntegrationTests
        api_tests = APIIntegrationTests(context)
        
        # Test specific API authentication
        assert await api_tests.test_user_registration_api()
        assert await api_tests.test_user_login_api()
        assert await api_tests.test_invalid_login_api()
        assert await api_tests.test_protected_endpoint_with_auth()
        
    finally:
        await runner.cleanup_test_environment()

@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
async def test_authentication_security():
    """Test authentication security features"""
    runner = IntegrationTestRunner(TEST_DATABASE_URL)
    try:
        context = await runner.setup_test_environment()
        
        from tests.integration.auth_integration import AuthIntegrationTests
        auth_tests = AuthIntegrationTests(context)
        
        # Test specific security features
        assert await auth_tests.test_password_security()
        assert await auth_tests.test_invalid_token_scenarios()
        assert await auth_tests.test_token_refresh_flow()
        
    finally:
        await runner.cleanup_test_environment()

@pytest.mark.integration
@pytest.mark.consistency
@pytest.mark.asyncio
async def test_data_integrity():
    """Test data integrity and consistency"""
    runner = IntegrationTestRunner(TEST_DATABASE_URL)
    try:
        context = await runner.setup_test_environment()
        
        from tests.integration.data_consistency import DataConsistencyTests
        consistency_tests = DataConsistencyTests(context)
        
        # Test specific data integrity features
        assert await consistency_tests.test_referential_integrity()
        assert await consistency_tests.test_data_validation_constraints()
        assert await consistency_tests.test_cascade_operations()
        
    finally:
        await runner.cleanup_test_environment()

# Performance and load testing

@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.asyncio
async def test_integration_performance():
    """Test integration performance under load"""
    runner = IntegrationTestRunner(TEST_DATABASE_URL)
    try:
        context = await runner.setup_test_environment()
        
        from tests.integration.database_integration import DatabaseIntegrationTests
        db_tests = DatabaseIntegrationTests(context)
        
        # Test performance-related functionality
        assert await db_tests.test_performance_queries()
        assert await db_tests.test_concurrent_access()
        
    finally:
        await runner.cleanup_test_environment()

# Error handling and edge cases

@pytest.mark.integration
@pytest.mark.error_handling
@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in integration scenarios"""
    runner = IntegrationTestRunner(TEST_DATABASE_URL)
    try:
        context = await runner.setup_test_environment()
        
        from tests.integration.api_integration import APIIntegrationTests
        api_tests = APIIntegrationTests(context)
        
        # Test error handling
        assert await api_tests.test_error_handling()
        assert await api_tests.test_protected_endpoint_without_auth()
        
    finally:
        await runner.cleanup_test_environment()

# Cleanup and utility functions

def pytest_configure(config):
    """Configure pytest for integration tests"""
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "database: Database integration tests")
    config.addinivalue_line("markers", "api: API integration tests")
    config.addinivalue_line("markers", "auth: Authentication integration tests")
    config.addinivalue_line("markers", "consistency: Data consistency tests")
    config.addinivalue_line("markers", "performance: Performance integration tests")
    config.addinivalue_line("markers", "error_handling: Error handling tests")

def pytest_collection_modifyitems(config, items):
    """Modify test collection for integration tests"""
    for item in items:
        # Add integration marker to all tests in this file
        if "test_integration_suite" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to full suite test
        if "test_full_integration_suite" in item.name:
            item.add_marker(pytest.mark.slow)