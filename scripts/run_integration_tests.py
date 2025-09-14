#!/usr/bin/env python3
"""
Integration Test Runner Script
Script to run integration tests with various configurations

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Command-line script for running integration tests
"""

import argparse
import asyncio
import sys
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.config import get_integration_config, get_ci_config, get_local_config, get_docker_config
from tests.integration.runner import IntegrationTestRunner

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run integration tests for HeadStart platform")
    
    parser.add_argument(
        "--environment", "-e",
        choices=["local", "ci", "docker"],
        default="local",
        help="Test environment configuration"
    )
    
    parser.add_argument(
        "--suite", "-s",
        choices=["all", "database", "api", "service", "auth", "consistency"],
        default="all",
        help="Test suite to run"
    )
    
    parser.add_argument(
        "--database-url", "-d",
        help="Test database URL (overrides environment config)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup after tests (for debugging)"
    )
    
    parser.add_argument(
        "--pytest-args",
        nargs="*",
        help="Additional arguments to pass to pytest"
    )
    
    parser.add_argument(
        "--report-format",
        choices=["console", "json", "html"],
        default="console",
        help="Test report format"
    )
    
    parser.add_argument(
        "--output-file", "-o",
        help="Output file for test results"
    )
    
    return parser.parse_args()

def get_config_for_environment(environment: str):
    """Get configuration for specified environment"""
    if environment == "ci":
        return get_ci_config()
    elif environment == "docker":
        return get_docker_config()
    else:
        return get_local_config()

def build_pytest_command(args, config) -> List[str]:
    """Build pytest command with appropriate arguments"""
    cmd = ["python", "-m", "pytest"]
    
    # Add test file
    cmd.append("tests/test_integration_suite.py")
    
    # Add markers based on suite selection
    if args.suite != "all":
        cmd.extend(["-m", args.suite])
    else:
        cmd.extend(["-m", "integration"])
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage if requested
    cmd.extend([
        "--cov=services",
        "--cov=api",
        "--cov-report=term-missing"
    ])
    
    # Add report format
    if args.report_format == "json":
        cmd.extend(["--json-report", "--json-report-file=integration_test_report.json"])
    elif args.report_format == "html":
        cmd.extend(["--html=integration_test_report.html", "--self-contained-html"])
    
    # Add output file if specified
    if args.output_file:
        cmd.extend(["--resultlog", args.output_file])
    
    # Add any additional pytest arguments
    if args.pytest_args:
        cmd.extend(args.pytest_args)
    
    return cmd

def setup_environment(config):
    """Setup test environment"""
    # Set environment variables
    os.environ["TEST_DATABASE_URL"] = config.test_database_url
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = config.log_level
    
    # Create log directory if needed
    if config.log_to_file:
        log_dir = Path(config.log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

def validate_prerequisites(config):
    """Validate test prerequisites"""
    print("Validating test prerequisites...")
    
    # Check database connection
    try:
        from sqlalchemy import create_engine
        engine = create_engine(config.test_database_url)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    
    # Check required Python packages
    required_packages = ["pytest", "sqlalchemy", "fastapi", "httpx"]
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} available")
        except ImportError:
            print(f"✗ {package} not available")
            return False
    
    return True

async def run_integration_tests_async(args, config):
    """Run integration tests asynchronously"""
    print(f"Running integration tests with {args.environment} configuration...")
    print(f"Database URL: {config.test_database_url}")
    print(f"Test suite: {args.suite}")
    
    runner = IntegrationTestRunner(config.test_database_url)
    
    try:
        if args.suite == "all":
            result = await runner.run_all_integration_tests()
        elif args.suite == "database":
            await runner.setup_test_environment()
            result = await runner.run_database_integration_tests()
        elif args.suite == "api":
            await runner.setup_test_environment()
            result = await runner.run_api_integration_tests()
        elif args.suite == "service":
            await runner.setup_test_environment()
            result = await runner.run_service_integration_tests()
        elif args.suite == "auth":
            await runner.setup_test_environment()
            result = await runner.run_auth_integration_tests()
        elif args.suite == "consistency":
            await runner.setup_test_environment()
            result = await runner.run_data_consistency_tests()
        
        # Print results
        if isinstance(result, dict) and "status" in result:
            print(f"\nTest Results:")
            print(f"Status: {result['status']}")
            print(f"Passed: {result.get('total_passed', 0)}")
            print(f"Failed: {result.get('total_failed', 0)}")
            print(f"Skipped: {result.get('total_skipped', 0)}")
            print(f"Execution Time: {result.get('total_execution_time', 0):.2f}s")
            
            if result.get('errors'):
                print(f"\nErrors:")
                for error in result['errors']:
                    print(f"  - {error}")
            
            return result['status'] == 'passed'
        else:
            print(f"Test completed with result: {result}")
            return True
            
    except Exception as e:
        print(f"Integration tests failed with error: {e}")
        return False
    finally:
        if not args.no_cleanup:
            await runner.cleanup_test_environment()

def run_with_pytest(args, config):
    """Run tests using pytest"""
    print("Running integration tests with pytest...")
    
    # Build pytest command
    cmd = build_pytest_command(args, config)
    
    if args.verbose:
        print(f"Running command: {' '.join(cmd)}")
    
    # Run pytest
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Get configuration for environment
    config = get_config_for_environment(args.environment)
    
    # Override database URL if provided
    if args.database_url:
        config.test_database_url = args.database_url
    
    # Setup environment
    setup_environment(config)
    
    # Validate prerequisites
    if not validate_prerequisites(config):
        print("Prerequisites validation failed. Please check your setup.")
        sys.exit(1)
    
    # Run tests
    try:
        # Use pytest for better integration with CI/CD
        success = run_with_pytest(args, config)
        
        if success:
            print("\n✓ All integration tests passed!")
            sys.exit(0)
        else:
            print("\n✗ Some integration tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()