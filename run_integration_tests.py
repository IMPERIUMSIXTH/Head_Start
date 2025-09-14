#!/usr/bin/env python3
"""
Simple Integration Test Runner
Quick script to run integration tests

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Simple script to run integration tests
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def run_simple_integration_test():
    """Run a simple integration test"""
    try:
        from tests.integration.runner import IntegrationTestRunner
        
        # Use SQLite for simple testing
        test_db_url = "sqlite:///test_integration.db"
        
        print("Starting integration test...")
        print(f"Using database: {test_db_url}")
        
        runner = IntegrationTestRunner(test_db_url)
        
        # Run database tests only for now
        print("\n=== Setting up test environment ===")
        await runner.setup_test_environment()
        
        print("\n=== Running database integration tests ===")
        db_result = await runner.run_database_integration_tests()
        
        print(f"\nDatabase Tests Results:")
        print(f"  Passed: {db_result.passed}")
        print(f"  Failed: {db_result.failed}")
        print(f"  Skipped: {db_result.skipped}")
        print(f"  Execution Time: {db_result.execution_time:.2f}s")
        
        if db_result.errors:
            print(f"  Errors:")
            for error in db_result.errors:
                print(f"    - {error}")
        
        print("\n=== Running service integration tests ===")
        service_result = await runner.run_service_integration_tests()
        
        print(f"\nService Tests Results:")
        print(f"  Passed: {service_result.passed}")
        print(f"  Failed: {service_result.failed}")
        print(f"  Skipped: {service_result.skipped}")
        print(f"  Execution Time: {service_result.execution_time:.2f}s")
        
        if service_result.errors:
            print(f"  Errors:")
            for error in service_result.errors:
                print(f"    - {error}")
        
        # Cleanup
        print("\n=== Cleaning up ===")
        await runner.cleanup_test_environment()
        
        # Summary
        total_passed = db_result.passed + service_result.passed
        total_failed = db_result.failed + service_result.failed
        total_skipped = db_result.skipped + service_result.skipped
        
        print(f"\n=== SUMMARY ===")
        print(f"Total Passed: {total_passed}")
        print(f"Total Failed: {total_failed}")
        print(f"Total Skipped: {total_skipped}")
        
        if total_failed == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_simple_integration_test())
    sys.exit(0 if success else 1)