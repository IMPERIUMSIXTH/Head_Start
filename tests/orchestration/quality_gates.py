"""
Quality gate validation for enforcing testing standards and thresholds.

This module provides the QualityGateValidator class that validates test results
against configurable quality thresholds and determines deployment readiness.
"""

import logging
from typing import List, Dict, Any

from .models import (
    TestResults, TestConfiguration, QualityGateResult, QualityGateResults,
    TestStatus
)

logger = logging.getLogger(__name__)


class QualityGateValidator:
    """
    Validates test results against quality gate thresholds.
    
    This class enforces quality standards by checking test results against
    configurable thresholds for coverage, security, accessibility, and performance.
    """
    
    def __init__(self, config: TestConfiguration):
        self.config = config
        
    async def validate_all_gates(self, results: TestResults) -> QualityGateResults:
        """
        Validate all quality gates against test results.
        
        Args:
            results: Test results to validate
            
        Returns:
            QualityGateResults: Comprehensive quality gate validation results
        """
        logger.info("Starting quality gate validation")
        
        gate_results = []
        
        # Unit test coverage gate
        coverage_result = self._validate_unit_test_coverage(results)
        gate_results.append(coverage_result)
        
        # Integration test coverage gate (if applicable)
        if results.integration_tests.status != TestStatus.NOT_STARTED:
            integration_result = self._validate_integration_tests(results)
            gate_results.append(integration_result)
        
        # Security vulnerability gates
        security_results = self._validate_security_gates(results)
        gate_results.extend(security_results)
        
        # Accessibility gates
        accessibility_result = self._validate_accessibility_gates(results)
        gate_results.append(accessibility_result)
        
        # Performance gates
        if results.performance_test.status != TestStatus.NOT_STARTED:
            performance_results = self._validate_performance_gates(results)
            gate_results.extend(performance_results)
        
        # Test execution gates
        execution_results = self._validate_test_execution_gates(results)
        gate_results.extend(execution_results)
        
        # Determine overall status
        overall_passed = all(result.passed or not result.blocking for result in gate_results)
        blocking_failures = [result.gate_name for result in gate_results 
                           if not result.passed and result.blocking]
        warnings = [result.gate_name for result in gate_results 
                   if not result.passed and not result.blocking]
        
        quality_gate_results = QualityGateResults(
            results=gate_results,
            overall_passed=overall_passed,
            blocking_failures=blocking_failures,
            warnings=warnings
        )
        
        logger.info(f"Quality gate validation completed. Overall passed: {overall_passed}")
        if blocking_failures:
            logger.warning(f"Blocking failures: {blocking_failures}")
        if warnings:
            logger.info(f"Warnings: {warnings}")
        
        return quality_gate_results
    
    def _validate_unit_test_coverage(self, results: TestResults) -> QualityGateResult:
        """Validate unit test coverage threshold."""
        threshold = self.config.min_unit_test_coverage
        actual = results.unit_tests.coverage_percentage
        passed = actual >= threshold
        
        return QualityGateResult(
            gate_name="Unit Test Coverage",
            passed=passed,
            threshold=threshold,
            actual_value=actual,
            message=f"Unit test coverage is {actual:.1f}% (threshold: {threshold}%)",
            blocking=True
        )
    
    def _validate_integration_tests(self, results: TestResults) -> QualityGateResult:
        """Validate integration test execution and basic coverage."""
        # For integration tests, we check that they ran successfully
        # and had a reasonable pass rate
        total_tests = results.integration_tests.total_tests
        passed_tests = results.integration_tests.passed_tests
        
        if total_tests == 0:
            return QualityGateResult(
                gate_name="Integration Test Execution",
                passed=False,
                threshold=1.0,
                actual_value=0.0,
                message="No integration tests were executed",
                blocking=True
            )
        
        pass_rate = (passed_tests / total_tests) * 100
        threshold = self.config.min_integration_test_coverage
        passed = pass_rate >= threshold
        
        return QualityGateResult(
            gate_name="Integration Test Pass Rate",
            passed=passed,
            threshold=threshold,
            actual_value=pass_rate,
            message=f"Integration test pass rate is {pass_rate:.1f}% (threshold: {threshold}%)",
            blocking=True
        )
    
    def _validate_security_gates(self, results: TestResults) -> List[QualityGateResult]:
        """Validate security-related quality gates."""
        security_results = []
        
        # Critical vulnerabilities gate
        critical_count = results.security_scan.severity_counts.get('critical', 0)
        critical_threshold = self.config.max_critical_vulnerabilities
        
        security_results.append(QualityGateResult(
            gate_name="Critical Security Vulnerabilities",
            passed=critical_count <= critical_threshold,
            threshold=float(critical_threshold),
            actual_value=float(critical_count),
            message=f"Found {critical_count} critical vulnerabilities (max allowed: {critical_threshold})",
            blocking=True
        ))
        
        # High vulnerabilities gate
        high_count = results.security_scan.severity_counts.get('high', 0)
        high_threshold = self.config.max_high_vulnerabilities
        
        security_results.append(QualityGateResult(
            gate_name="High Security Vulnerabilities",
            passed=high_count <= high_threshold,
            threshold=float(high_threshold),
            actual_value=float(high_count),
            message=f"Found {high_count} high vulnerabilities (max allowed: {high_threshold})",
            blocking=True
        ))
        
        # Security scan execution gate
        security_results.append(QualityGateResult(
            gate_name="Security Scan Execution",
            passed=results.security_scan.status in [TestStatus.PASSED, TestStatus.FAILED],
            threshold=1.0,
            actual_value=1.0 if results.security_scan.status != TestStatus.ERROR else 0.0,
            message=f"Security scan status: {results.security_scan.status.value}",
            blocking=True
        ))
        
        return security_results
    
    def _validate_accessibility_gates(self, results: TestResults) -> QualityGateResult:
        """Validate accessibility quality gates."""
        critical_violations = results.accessibility_test.critical_violations
        threshold = self.config.max_accessibility_violations
        passed = critical_violations <= threshold
        
        return QualityGateResult(
            gate_name="Accessibility Violations",
            passed=passed,
            threshold=float(threshold),
            actual_value=float(critical_violations),
            message=f"Found {critical_violations} critical accessibility violations (max allowed: {threshold})",
            blocking=True
        )
    
    def _validate_performance_gates(self, results: TestResults) -> List[QualityGateResult]:
        """Validate performance-related quality gates."""
        performance_results = []
        
        # Response time gate (P95 should be reasonable)
        p95_threshold = 1000.0  # 1 second
        p95_actual = results.performance_test.response_time_p95
        
        performance_results.append(QualityGateResult(
            gate_name="Response Time P95",
            passed=p95_actual <= p95_threshold,
            threshold=p95_threshold,
            actual_value=p95_actual,
            message=f"P95 response time is {p95_actual:.1f}ms (threshold: {p95_threshold}ms)",
            blocking=False  # Performance issues are warnings, not blocking
        ))
        
        # Error rate gate
        error_rate_threshold = 5.0  # 5% error rate
        error_rate_actual = results.performance_test.error_rate
        
        performance_results.append(QualityGateResult(
            gate_name="Error Rate",
            passed=error_rate_actual <= error_rate_threshold,
            threshold=error_rate_threshold,
            actual_value=error_rate_actual,
            message=f"Error rate is {error_rate_actual:.2f}% (threshold: {error_rate_threshold}%)",
            blocking=True
        ))
        
        # Performance regression gate (if baseline exists)
        if results.performance_test.baseline_comparison:
            regression_threshold = self.config.max_performance_regression
            # This would compare against baseline - simplified for now
            regression_actual = 5.0  # Simulated 5% regression
            
            performance_results.append(QualityGateResult(
                gate_name="Performance Regression",
                passed=regression_actual <= regression_threshold,
                threshold=regression_threshold,
                actual_value=regression_actual,
                message=f"Performance regression is {regression_actual:.1f}% (threshold: {regression_threshold}%)",
                blocking=False
            ))
        
        return performance_results
    
    def _validate_test_execution_gates(self, results: TestResults) -> List[QualityGateResult]:
        """Validate that critical tests executed successfully."""
        execution_results = []
        
        # Unit tests must execute successfully
        execution_results.append(QualityGateResult(
            gate_name="Unit Test Execution",
            passed=results.unit_tests.status in [TestStatus.PASSED, TestStatus.FAILED],
            threshold=1.0,
            actual_value=1.0 if results.unit_tests.status != TestStatus.ERROR else 0.0,
            message=f"Unit test execution status: {results.unit_tests.status.value}",
            blocking=True
        ))
        
        # Unit tests must not have critical failures
        if results.unit_tests.total_tests > 0:
            unit_pass_rate = (results.unit_tests.passed_tests / results.unit_tests.total_tests) * 100
            execution_results.append(QualityGateResult(
                gate_name="Unit Test Pass Rate",
                passed=unit_pass_rate >= 90.0,  # At least 90% of unit tests must pass
                threshold=90.0,
                actual_value=unit_pass_rate,
                message=f"Unit test pass rate: {unit_pass_rate:.1f}%",
                blocking=True
            ))
        
        # E2E tests should execute if enabled (but failures might not be blocking)
        if self.config.run_e2e_tests:
            execution_results.append(QualityGateResult(
                gate_name="E2E Test Execution",
                passed=results.e2e_tests.status in [TestStatus.PASSED, TestStatus.FAILED],
                threshold=1.0,
                actual_value=1.0 if results.e2e_tests.status != TestStatus.ERROR else 0.0,
                message=f"E2E test execution status: {results.e2e_tests.status.value}",
                blocking=False  # E2E test failures might not block deployment
            ))
        
        return execution_results
    
    async def validate_custom_gate(self, gate_name: str, threshold: float, 
                                 actual_value: float, blocking: bool = True) -> QualityGateResult:
        """
        Validate a custom quality gate.
        
        Args:
            gate_name: Name of the quality gate
            threshold: Threshold value for the gate
            actual_value: Actual measured value
            blocking: Whether this gate blocks deployment if failed
            
        Returns:
            QualityGateResult: Result of the custom gate validation
        """
        passed = actual_value >= threshold
        
        return QualityGateResult(
            gate_name=gate_name,
            passed=passed,
            threshold=threshold,
            actual_value=actual_value,
            message=f"{gate_name}: {actual_value} (threshold: {threshold})",
            blocking=blocking
        )
    
    def get_quality_score(self, results: QualityGateResults) -> float:
        """
        Calculate an overall quality score based on gate results.
        
        Args:
            results: Quality gate results to score
            
        Returns:
            float: Quality score between 0.0 and 100.0
        """
        if not results.results:
            return 0.0
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for result in results.results:
            # Blocking gates have higher weight
            weight = 2.0 if result.blocking else 1.0
            score = 100.0 if result.passed else 0.0
            
            weighted_score += score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0