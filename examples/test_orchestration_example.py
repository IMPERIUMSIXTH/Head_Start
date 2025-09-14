#!/usr/bin/env python3
"""
Example script demonstrating the testing orchestration framework.

This script shows how to use the orchestration framework programmatically
to run comprehensive testing pipelines with quality gates and reporting.
"""

import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.orchestration import (
    TestOrchestrator, TestContext, TestConfiguration
)
from tests.orchestration.config import ConfigurationManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_orchestration_example():
    """
    Basic example of running the test orchestration framework.
    """
    print("="*60)
    print("BASIC ORCHESTRATION EXAMPLE")
    print("="*60)
    
    # Create a basic configuration
    config = TestConfiguration(
        parallel_execution=True,
        max_workers=2,
        run_unit_tests=True,
        run_integration_tests=True,
        run_e2e_tests=False,  # Disable for demo
        run_security_tests=True,
        run_accessibility_tests=False,  # Disable for demo
        run_performance_tests=False,  # Disable for demo
        min_unit_test_coverage=75.0,
        max_critical_vulnerabilities=0,
        generate_html_reports=True,
        generate_json_reports=True
    )
    
    # Create test context
    context = TestContext(
        branch="example-branch",
        commit_sha="example123abc",
        environment="test",
        test_config=config,
        deployment_target="staging"
    )
    
    # Create orchestrator
    orchestrator = TestOrchestrator(context)
    
    try:
        # Execute test pipeline
        print("Executing test pipeline...")
        results = await orchestrator.execute_test_pipeline()
        
        # Validate quality gates
        print("Validating quality gates...")
        quality_passed = await orchestrator.validate_quality_gates(results)
        
        # Generate reports
        print("Generating reports...")
        report_paths = await orchestrator.generate_reports(results)
        
        # Display results
        print("\nRESULTS:")
        print(f"Overall Status: {results.overall_status.value.upper()}")
        print(f"Quality Gates: {'PASSED' if quality_passed else 'FAILED'}")
        print(f"Execution Time: {results.total_execution_time:.2f}s")
        
        print("\nTest Breakdown:")
        print(f"  Unit Tests: {results.unit_tests.passed_tests}/{results.unit_tests.total_tests} passed")
        print(f"  Coverage: {results.unit_tests.coverage_percentage:.1f}%")
        print(f"  Integration Tests: {results.integration_tests.passed_tests}/{results.integration_tests.total_tests} passed")
        print(f"  Security Vulnerabilities: {len(results.security_scan.vulnerabilities)}")
        
        if report_paths:
            print("\nGenerated Reports:")
            for report_type, path in report_paths.items():
                print(f"  {report_type}: {path}")
        
        return results.overall_status.value == "passed" and quality_passed
        
    except Exception as e:
        print(f"Error during orchestration: {e}")
        return False


async def configuration_management_example():
    """
    Example of using the configuration management system.
    """
    print("\n" + "="*60)
    print("CONFIGURATION MANAGEMENT EXAMPLE")
    print("="*60)
    
    # Create a temporary workspace for demo
    workspace = Path.cwd()
    config_manager = ConfigurationManager(workspace)
    
    # Load default configuration
    print("Loading default configuration...")
    default_config = config_manager.load_configuration()
    print(f"Default max workers: {default_config.max_workers}")
    print(f"Default unit test coverage threshold: {default_config.min_unit_test_coverage}%")
    
    # Create a custom configuration
    print("\nCreating custom configuration...")
    custom_config = TestConfiguration(
        max_workers=6,
        min_unit_test_coverage=85.0,
        run_performance_tests=False,
        generate_html_reports=True
    )
    
    # Validate configuration
    print("Validating configuration...")
    errors = config_manager.validate_configuration(custom_config)
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
    
    # Create sample configuration file
    print("Creating sample configuration file...")
    sample_path = config_manager.create_sample_config("example")
    print(f"Sample configuration created at: {sample_path}")
    
    return True


async def quality_gates_example():
    """
    Example of quality gate validation with different scenarios.
    """
    print("\n" + "="*60)
    print("QUALITY GATES EXAMPLE")
    print("="*60)
    
    from tests.orchestration.quality_gates import QualityGateValidator
    from tests.orchestration.models import (
        TestResults, UnitTestResults, SecurityScanResults, 
        AccessibilityResults, TestStatus
    )
    
    # Create a configuration with strict quality gates
    config = TestConfiguration(
        min_unit_test_coverage=80.0,
        max_critical_vulnerabilities=0,
        max_high_vulnerabilities=3,
        max_accessibility_violations=0
    )
    
    validator = QualityGateValidator(config)
    
    # Test scenario 1: All gates pass
    print("Scenario 1: All quality gates pass")
    good_results = TestResults(
        unit_tests=UnitTestResults(10, 10, 0, 0, 85.0, 5.0, status=TestStatus.PASSED),
        integration_tests=None,
        e2e_tests=None,
        security_scan=SecurityScanResults(
            severity_counts={"high": 2, "medium": 5}, status=TestStatus.PASSED
        ),
        accessibility_test=AccessibilityResults(
            critical_violations=0, status=TestStatus.PASSED
        ),
        performance_test=None,
        overall_status=TestStatus.PASSED
    )
    
    gate_results = await validator.validate_all_gates(good_results)
    print(f"  Overall passed: {gate_results.overall_passed}")
    print(f"  Blocking failures: {gate_results.blocking_failures}")
    
    # Test scenario 2: Coverage failure
    print("\nScenario 2: Unit test coverage below threshold")
    bad_coverage_results = TestResults(
        unit_tests=UnitTestResults(10, 7, 3, 0, 70.0, 5.0, status=TestStatus.FAILED),
        integration_tests=None,
        e2e_tests=None,
        security_scan=SecurityScanResults(status=TestStatus.PASSED),
        accessibility_test=AccessibilityResults(status=TestStatus.PASSED),
        performance_test=None,
        overall_status=TestStatus.FAILED
    )
    
    gate_results = await validator.validate_all_gates(bad_coverage_results)
    print(f"  Overall passed: {gate_results.overall_passed}")
    print(f"  Blocking failures: {gate_results.blocking_failures}")
    
    # Test scenario 3: Security vulnerabilities
    print("\nScenario 3: Critical security vulnerabilities found")
    security_fail_results = TestResults(
        unit_tests=UnitTestResults(10, 10, 0, 0, 85.0, 5.0, status=TestStatus.PASSED),
        integration_tests=None,
        e2e_tests=None,
        security_scan=SecurityScanResults(
            severity_counts={"critical": 2, "high": 1}, status=TestStatus.FAILED
        ),
        accessibility_test=AccessibilityResults(status=TestStatus.PASSED),
        performance_test=None,
        overall_status=TestStatus.FAILED
    )
    
    gate_results = await validator.validate_all_gates(security_fail_results)
    print(f"  Overall passed: {gate_results.overall_passed}")
    print(f"  Blocking failures: {gate_results.blocking_failures}")
    
    return True


async def main():
    """
    Main function that runs all examples.
    """
    print("Testing Orchestration Framework Examples")
    print("This demonstrates the core functionality of the framework")
    print()
    
    try:
        # Run basic orchestration example
        success1 = await basic_orchestration_example()
        
        # Run configuration management example
        success2 = await configuration_management_example()
        
        # Run quality gates example
        success3 = await quality_gates_example()
        
        print("\n" + "="*60)
        print("EXAMPLES SUMMARY")
        print("="*60)
        print(f"Basic Orchestration: {'SUCCESS' if success1 else 'FAILED'}")
        print(f"Configuration Management: {'SUCCESS' if success2 else 'FAILED'}")
        print(f"Quality Gates: {'SUCCESS' if success3 else 'FAILED'}")
        
        if all([success1, success2, success3]):
            print("\nAll examples completed successfully! ✅")
            print("\nNext steps:")
            print("1. Run the unit tests: python -m pytest tests/test_orchestration.py -v")
            print("2. Try the CLI: python -m tests.orchestration.cli --help")
            print("3. Create a custom configuration for your project")
        else:
            print("\nSome examples failed. Check the logs above for details.")
        
    except Exception as e:
        print(f"Examples failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())