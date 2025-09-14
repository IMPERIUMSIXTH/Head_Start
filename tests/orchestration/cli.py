#!/usr/bin/env python3
"""
Command-line interface for the testing orchestration framework.

This script provides a CLI for running the test orchestration framework
with various configuration options and reporting capabilities.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .orchestrator import TestOrchestrator
from .models import TestContext, TestConfiguration
from .config import ConfigurationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_tests(
    branch: str = "main",
    commit_sha: str = "unknown",
    environment: str = "test",
    config_file: Optional[str] = None,
    workspace_root: Optional[Path] = None
) -> int:
    """
    Run the complete test orchestration pipeline.
    
    Args:
        branch: Git branch name
        commit_sha: Git commit SHA
        environment: Target environment
        config_file: Path to configuration file
        workspace_root: Workspace root directory
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Set up workspace
        if workspace_root is None:
            workspace_root = Path.cwd()
        
        # Load configuration
        config_manager = ConfigurationManager(workspace_root)
        
        if config_file:
            # Load from specific file (simplified - would need full implementation)
            config = config_manager.load_configuration(environment)
        else:
            config = config_manager.load_configuration(environment)
        
        # Validate configuration
        validation_errors = config_manager.validate_configuration(config)
        if validation_errors:
            logger.error("Configuration validation failed:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            return 1
        
        # Create test context
        context = TestContext(
            branch=branch,
            commit_sha=commit_sha,
            environment=environment,
            test_config=config,
            workspace_root=workspace_root
        )
        
        # Create and run orchestrator
        orchestrator = TestOrchestrator(context)
        
        logger.info("Starting test orchestration pipeline")
        logger.info(f"Branch: {branch}, Commit: {commit_sha}, Environment: {environment}")
        
        # Execute test pipeline
        results = await orchestrator.execute_test_pipeline()
        
        # Validate quality gates
        quality_passed = await orchestrator.validate_quality_gates(results)
        
        # Generate reports
        report_paths = await orchestrator.generate_reports(results)
        
        # Log results summary
        logger.info("Test orchestration completed")
        logger.info(f"Overall status: {results.overall_status.value}")
        logger.info(f"Quality gates passed: {quality_passed}")
        logger.info(f"Total execution time: {results.total_execution_time:.2f}s")
        
        if report_paths:
            logger.info("Generated reports:")
            for report_type, path in report_paths.items():
                logger.info(f"  - {report_type}: {path}")
        
        # Print summary to stdout
        print("\n" + "="*60)
        print("TEST ORCHESTRATION SUMMARY")
        print("="*60)
        print(f"Overall Status: {results.overall_status.value.upper()}")
        print(f"Quality Gates: {'PASSED' if quality_passed else 'FAILED'}")
        print(f"Execution Time: {results.total_execution_time:.2f}s")
        print()
        
        print("Test Results:")
        print(f"  Unit Tests: {results.unit_tests.passed_tests}/{results.unit_tests.total_tests} passed ({results.unit_tests.coverage_percentage:.1f}% coverage)")
        print(f"  Integration Tests: {results.integration_tests.passed_tests}/{results.integration_tests.total_tests} passed")
        print(f"  E2E Tests: {results.e2e_tests.passed_tests}/{results.e2e_tests.total_tests} passed")
        print(f"  Security Scan: {results.security_scan.status.value} ({len(results.security_scan.vulnerabilities)} vulnerabilities)")
        print(f"  Accessibility: {results.accessibility_test.status.value} ({results.accessibility_test.total_violations} violations)")
        print(f"  Performance: {results.performance_test.status.value}")
        print()
        
        if report_paths:
            print("Reports Generated:")
            for report_type, path in report_paths.items():
                print(f"  - {report_type.upper()}: {path}")
        
        print("="*60)
        
        # Return appropriate exit code
        if results.overall_status.value in ["passed"] and quality_passed:
            return 0
        else:
            return 1
            
    except Exception as e:
        logger.error(f"Test orchestration failed: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Test Orchestration Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --branch main --commit abc123
  %(prog)s --environment staging --config config.staging.yaml
  %(prog)s --branch feature/new-feature --commit def456 --workspace /path/to/project
        """
    )
    
    parser.add_argument(
        "--branch",
        default="main",
        help="Git branch name (default: main)"
    )
    
    parser.add_argument(
        "--commit",
        default="unknown",
        help="Git commit SHA (default: unknown)"
    )
    
    parser.add_argument(
        "--environment",
        default="test",
        choices=["test", "staging", "production"],
        help="Target environment (default: test)"
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Workspace root directory (default: current directory)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--create-sample-config",
        action="store_true",
        help="Create a sample configuration file and exit"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle sample config creation
    if args.create_sample_config:
        workspace = args.workspace or Path.cwd()
        config_manager = ConfigurationManager(workspace)
        sample_path = config_manager.create_sample_config(args.environment)
        print(f"Sample configuration created at: {sample_path}")
        return 0
    
    # Run the test orchestration
    try:
        exit_code = asyncio.run(run_tests(
            branch=args.branch,
            commit_sha=args.commit,
            environment=args.environment,
            config_file=args.config,
            workspace_root=args.workspace
        ))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test orchestration interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT


if __name__ == "__main__":
    main()