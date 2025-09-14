"""
Main test orchestration class for coordinating test execution.

This module provides the TestOrchestrator class that coordinates the execution
of all testing layers, manages dependencies, and enforces quality gates.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import (
    TestContext, TestResults, TestConfiguration, TestStatus,
    UnitTestResults, IntegrationTestResults, E2ETestResults,
    SecurityScanResults, AccessibilityResults, PerformanceResults
)
from .runner import TestRunner
from .reporter import TestReporter
from .quality_gates import QualityGateValidator

logger = logging.getLogger(__name__)


class TestOrchestrator:
    """
    Main orchestrator for coordinating test execution across all layers.
    
    This class manages the execution flow of different test types, enforces
    dependencies between test layers, and validates quality gates.
    """
    
    def __init__(self, context: TestContext):
        self.context = context
        self.test_runner = TestRunner(context)
        self.reporter = TestReporter(context)
        self.quality_gate_validator = QualityGateValidator(context.test_config)
        
    async def execute_test_pipeline(self) -> TestResults:
        """
        Execute the complete test pipeline with all enabled test types.
        
        Returns:
            TestResults: Comprehensive results from all test executions
        """
        logger.info("Starting test pipeline execution")
        start_time = datetime.now()
        
        # Initialize results with default values
        results = TestResults(
            unit_tests=UnitTestResults(0, 0, 0, 0, 0.0, 0.0),
            integration_tests=IntegrationTestResults(0, 0, 0, 0, 0.0),
            e2e_tests=E2ETestResults(0, 0, 0, 0, 0.0),
            security_scan=SecurityScanResults(),
            accessibility_test=AccessibilityResults(),
            performance_test=PerformanceResults(),
            execution_start_time=start_time
        )
        
        try:
            # Execute tests in dependency order
            if self.context.test_config.run_unit_tests:
                logger.info("Executing unit tests")
                results.unit_tests = await self.test_runner.run_unit_tests()
                
                # Stop if unit tests fail critically
                if results.unit_tests.status == TestStatus.FAILED:
                    if results.unit_tests.coverage_percentage < self.context.test_config.min_unit_test_coverage:
                        logger.error("Unit test coverage below threshold, stopping pipeline")
                        results.overall_status = TestStatus.FAILED
                        return results
            
            # Integration tests depend on unit tests passing
            if self.context.test_config.run_integration_tests and results.unit_tests.status != TestStatus.FAILED:
                logger.info("Executing integration tests")
                results.integration_tests = await self.test_runner.run_integration_tests()
            
            # Security tests can run in parallel with other tests
            security_task = None
            if self.context.test_config.run_security_tests:
                logger.info("Starting security tests")
                security_task = asyncio.create_task(self.test_runner.run_security_tests())
            
            # Accessibility tests can run in parallel
            accessibility_task = None
            if self.context.test_config.run_accessibility_tests:
                logger.info("Starting accessibility tests")
                accessibility_task = asyncio.create_task(self.test_runner.run_accessibility_tests())
            
            # E2E tests depend on integration tests passing
            if (self.context.test_config.run_e2e_tests and 
                results.integration_tests.status != TestStatus.FAILED):
                logger.info("Executing E2E tests")
                results.e2e_tests = await self.test_runner.run_e2e_tests()
            
            # Performance tests run after core functionality is validated
            if (self.context.test_config.run_performance_tests and
                results.e2e_tests.status != TestStatus.FAILED):
                logger.info("Executing performance tests")
                results.performance_test = await self.test_runner.run_performance_tests()
            
            # Wait for parallel tasks to complete
            if security_task:
                results.security_scan = await security_task
            if accessibility_task:
                results.accessibility_test = await accessibility_task
            
            # Determine overall status
            results.overall_status = self._determine_overall_status(results)
            
        except Exception as e:
            logger.error(f"Test pipeline execution failed: {e}")
            results.overall_status = TestStatus.ERROR
        
        finally:
            end_time = datetime.now()
            results.execution_end_time = end_time
            results.total_execution_time = (end_time - start_time).total_seconds()
            
        logger.info(f"Test pipeline completed with status: {results.overall_status}")
        return results
    
    async def validate_quality_gates(self, results: TestResults) -> bool:
        """
        Validate all quality gates against test results.
        
        Args:
            results: Test results to validate against quality gates
            
        Returns:
            bool: True if all quality gates pass, False otherwise
        """
        logger.info("Validating quality gates")
        
        try:
            gate_results = await self.quality_gate_validator.validate_all_gates(results)
            results.quality_gate_passed = gate_results.overall_passed
            
            if not gate_results.overall_passed:
                logger.error(f"Quality gates failed: {gate_results.blocking_failures}")
                
            return gate_results.overall_passed
            
        except Exception as e:
            logger.error(f"Quality gate validation failed: {e}")
            return False
    
    async def generate_reports(self, results: TestResults) -> Dict[str, str]:
        """
        Generate comprehensive test reports.
        
        Args:
            results: Test results to generate reports for
            
        Returns:
            Dict[str, str]: Dictionary mapping report types to file paths
        """
        logger.info("Generating test reports")
        
        try:
            report_paths = await self.reporter.generate_all_reports(results)
            logger.info(f"Generated reports: {list(report_paths.keys())}")
            return report_paths
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {}
    
    def _determine_overall_status(self, results: TestResults) -> TestStatus:
        """
        Determine the overall test status based on individual test results.
        
        Args:
            results: Test results to analyze
            
        Returns:
            TestStatus: Overall status of the test execution
        """
        # Check for any errors first
        test_statuses = [
            results.unit_tests.status,
            results.integration_tests.status,
            results.e2e_tests.status,
            results.security_scan.status,
            results.accessibility_test.status,
            results.performance_test.status
        ]
        
        if TestStatus.ERROR in test_statuses:
            return TestStatus.ERROR
        
        # Check for critical failures
        if (results.unit_tests.status == TestStatus.FAILED or
            results.integration_tests.status == TestStatus.FAILED):
            return TestStatus.FAILED
        
        # Check for security failures (blocking)
        if (results.security_scan.status == TestStatus.FAILED and
            results.security_scan.remediation_required):
            return TestStatus.FAILED
        
        # Check for accessibility failures (blocking)
        if (results.accessibility_test.status == TestStatus.FAILED and
            results.accessibility_test.critical_violations > 0):
            return TestStatus.FAILED
        
        # If any non-critical tests failed, overall status is failed
        if TestStatus.FAILED in test_statuses:
            return TestStatus.FAILED
        
        # If all enabled tests passed
        return TestStatus.PASSED
    
    async def execute_parallel_tests(self, test_types: List[str]) -> Dict[str, any]:
        """
        Execute multiple test types in parallel for improved performance.
        
        Args:
            test_types: List of test types to execute in parallel
            
        Returns:
            Dict[str, any]: Results from parallel test execution
        """
        logger.info(f"Executing tests in parallel: {test_types}")
        
        tasks = {}
        
        if "security" in test_types:
            tasks["security"] = asyncio.create_task(self.test_runner.run_security_tests())
        
        if "accessibility" in test_types:
            tasks["accessibility"] = asyncio.create_task(self.test_runner.run_accessibility_tests())
        
        if "performance" in test_types:
            tasks["performance"] = asyncio.create_task(self.test_runner.run_performance_tests())
        
        # Wait for all tasks to complete
        results = {}
        for test_type, task in tasks.items():
            try:
                results[test_type] = await task
            except Exception as e:
                logger.error(f"Parallel test {test_type} failed: {e}")
                results[test_type] = None
        
        return results