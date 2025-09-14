"""
Data models for the testing orchestration framework.

This module defines the core data structures used throughout the testing system
for configuration, context, and results management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path


class TestStatus(Enum):
    """Test execution status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(Enum):
    """Test type enumeration."""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    SMOKE = "smoke"
    REGRESSION = "regression"


@dataclass
class TestFileResult:
    """Result for a single test file."""
    file_path: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    coverage_percentage: Optional[float] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class UnitTestResults:
    """Results from unit test execution."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    coverage_percentage: float
    execution_time: float
    test_files: List[TestFileResult] = field(default_factory=list)
    status: TestStatus = TestStatus.NOT_STARTED


@dataclass
class IntegrationTestResults:
    """Results from integration test execution."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    database_tests: int = 0
    api_tests: int = 0
    service_tests: int = 0
    status: TestStatus = TestStatus.NOT_STARTED


@dataclass
class E2ETestResults:
    """Results from end-to-end test execution."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    browser_tests: Dict[str, int] = field(default_factory=dict)
    user_journey_tests: int = 0
    status: TestStatus = TestStatus.NOT_STARTED


@dataclass
class Vulnerability:
    """Security vulnerability information."""
    severity: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    cve_id: Optional[str] = None
    remediation: Optional[str] = None


@dataclass
class SecurityScanResults:
    """Results from security scanning."""
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    severity_counts: Dict[str, int] = field(default_factory=dict)
    scan_tools_used: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    compliance_status: str = "unknown"
    remediation_required: bool = False
    status: TestStatus = TestStatus.NOT_STARTED


@dataclass
class AccessibilityResults:
    """Results from accessibility testing."""
    total_violations: int = 0
    critical_violations: int = 0
    serious_violations: int = 0
    moderate_violations: int = 0
    minor_violations: int = 0
    wcag_level: str = "AA"
    pages_tested: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    status: TestStatus = TestStatus.NOT_STARTED


@dataclass
class PerformanceResults:
    """Results from performance testing."""
    response_time_p50: float = 0.0
    response_time_p95: float = 0.0
    response_time_p99: float = 0.0
    throughput_rps: float = 0.0
    error_rate: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    execution_time: float = 0.0
    baseline_comparison: Optional[Dict[str, float]] = None
    status: TestStatus = TestStatus.NOT_STARTED


@dataclass
class TestResults:
    """Comprehensive test results from all testing layers."""
    unit_tests: UnitTestResults
    integration_tests: IntegrationTestResults
    e2e_tests: E2ETestResults
    security_scan: SecurityScanResults
    accessibility_test: AccessibilityResults
    performance_test: PerformanceResults
    overall_status: TestStatus = TestStatus.NOT_STARTED
    quality_gate_passed: bool = False
    execution_start_time: Optional[datetime] = None
    execution_end_time: Optional[datetime] = None
    total_execution_time: float = 0.0


@dataclass
class TestConfiguration:
    """Configuration for test execution."""
    # General settings
    parallel_execution: bool = True
    max_workers: int = 4
    timeout_seconds: int = 3600
    
    # Test type enablement
    run_unit_tests: bool = True
    run_integration_tests: bool = True
    run_e2e_tests: bool = True
    run_security_tests: bool = True
    run_accessibility_tests: bool = True
    run_performance_tests: bool = True
    
    # Quality gate thresholds
    min_unit_test_coverage: float = 80.0
    min_integration_test_coverage: float = 70.0
    max_critical_vulnerabilities: int = 0
    max_high_vulnerabilities: int = 5
    max_accessibility_violations: int = 0
    max_performance_regression: float = 10.0
    
    # Environment settings
    test_database_url: Optional[str] = None
    test_redis_url: Optional[str] = None
    test_environment: str = "test"
    
    # Reporting settings
    generate_html_reports: bool = True
    generate_json_reports: bool = True
    report_output_dir: Path = field(default_factory=lambda: Path("test_reports"))


@dataclass
class TestContext:
    """Context information for test execution."""
    branch: str
    commit_sha: str
    environment: str
    test_config: TestConfiguration
    deployment_target: str = "staging"
    triggered_by: str = "ci"
    workspace_root: Path = field(default_factory=lambda: Path.cwd())
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class QualityGateResult:
    """Result of a quality gate check."""
    gate_name: str
    passed: bool
    threshold: float
    actual_value: float
    message: str
    blocking: bool = True


@dataclass
class QualityGateResults:
    """Results from all quality gate validations."""
    results: List[QualityGateResult] = field(default_factory=list)
    overall_passed: bool = True
    blocking_failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)