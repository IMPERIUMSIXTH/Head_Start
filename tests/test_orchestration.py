"""
Unit tests for the testing orchestration framework.

This module contains comprehensive unit tests for the core orchestration
components including TestOrchestrator, TestRunner, TestReporter, and
QualityGateValidator.
"""

import asyncio
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import json

from tests.orchestration import (
    TestOrchestrator, TestRunner, TestReporter, QualityGateValidator,
    TestContext, TestResults, TestConfiguration, TestStatus,
    UnitTestResults, IntegrationTestResults, E2ETestResults,
    SecurityScanResults, AccessibilityResults, PerformanceResults
)
from tests.orchestration.config import ConfigurationManager


class TestTestOrchestrator:
    """Test cases for the TestOrchestrator class."""
    
    @pytest.fixture
    def test_context(self):
        """Create a test context for testing."""
        config = TestConfiguration(
            parallel_execution=True,
            max_workers=2,
            timeout_seconds=300,
            run_unit_tests=True,
            run_integration_tests=True,
            run_e2e_tests=False,  # Disable for faster testing
            run_security_tests=True,
            run_accessibility_tests=False,
            run_performance_tests=False
        )
        
        return TestContext(
            branch="test-branch",
            commit_sha="abc123def456",
            environment="test",
            test_config=config,
            deployment_target="staging"
        )
    
    @pytest.fixture
    def orchestrator(self, test_context):
        """Create a TestOrchestrator instance for testing."""
        return TestOrchestrator(test_context)
    
    @pytest.mark.asyncio
    async def test_execute_test_pipeline_success(self, orchestrator):
        """Test successful execution of the test pipeline."""
        # Mock the test runner methods
        with patch.object(orchestrator.test_runner, 'run_unit_tests') as mock_unit, \
             patch.object(orchestrator.test_runner, 'run_integration_tests') as mock_integration, \
             patch.object(orchestrator.test_runner, 'run_security_tests') as mock_security:
            
            # Configure mocks to return successful results
            mock_unit.return_value = UnitTestResults(
                total_tests=10, passed_tests=10, failed_tests=0, skipped_tests=0,
                coverage_percentage=85.0, execution_time=5.0, status=TestStatus.PASSED
            )
            
            mock_integration.return_value = IntegrationTestResults(
                total_tests=5, passed_tests=5, failed_tests=0, skipped_tests=0,
                execution_time=10.0, status=TestStatus.PASSED
            )
            
            mock_security.return_value = SecurityScanResults(
                vulnerabilities=[], severity_counts={}, scan_tools_used=["bandit"],
                execution_time=3.0, status=TestStatus.PASSED
            )
            
            # Execute the pipeline
            results = await orchestrator.execute_test_pipeline()
            
            # Verify results
            assert results.overall_status == TestStatus.PASSED
            assert results.unit_tests.status == TestStatus.PASSED
            assert results.integration_tests.status == TestStatus.PASSED
            assert results.security_scan.status == TestStatus.PASSED
            assert results.execution_start_time is not None
            assert results.execution_end_time is not None
            assert results.total_execution_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_test_pipeline_unit_test_failure(self, orchestrator):
        """Test pipeline behavior when unit tests fail."""
        with patch.object(orchestrator.test_runner, 'run_unit_tests') as mock_unit:
            # Configure unit tests to fail with low coverage
            mock_unit.return_value = UnitTestResults(
                total_tests=10, passed_tests=7, failed_tests=3, skipped_tests=0,
                coverage_percentage=60.0, execution_time=5.0, status=TestStatus.FAILED
            )
            
            # Execute the pipeline
            results = await orchestrator.execute_test_pipeline()
            
            # Verify that pipeline stops early due to low coverage
            assert results.overall_status == TestStatus.FAILED
            assert results.unit_tests.status == TestStatus.FAILED
            # Integration tests should not run due to unit test failure
            assert results.integration_tests.total_tests == 0
    
    @pytest.mark.asyncio
    async def test_validate_quality_gates(self, orchestrator):
        """Test quality gate validation."""
        # Create test results
        results = TestResults(
            unit_tests=UnitTestResults(10, 10, 0, 0, 85.0, 5.0, status=TestStatus.PASSED),
            integration_tests=IntegrationTestResults(5, 5, 0, 0, 10.0, status=TestStatus.PASSED),
            e2e_tests=E2ETestResults(3, 3, 0, 0, 15.0, status=TestStatus.PASSED),
            security_scan=SecurityScanResults(status=TestStatus.PASSED),
            accessibility_test=AccessibilityResults(status=TestStatus.PASSED),
            performance_test=PerformanceResults(status=TestStatus.PASSED),
            overall_status=TestStatus.PASSED
        )
        
        # Mock quality gate validator
        with patch.object(orchestrator.quality_gate_validator, 'validate_all_gates') as mock_validate:
            from tests.orchestration.models import QualityGateResults
            mock_validate.return_value = QualityGateResults(
                results=[], overall_passed=True, blocking_failures=[], warnings=[]
            )
            
            # Validate quality gates
            passed = await orchestrator.validate_quality_gates(results)
            
            assert passed is True
            assert results.quality_gate_passed is True
    
    @pytest.mark.asyncio
    async def test_generate_reports(self, orchestrator):
        """Test report generation."""
        # Create test results
        results = TestResults(
            unit_tests=UnitTestResults(10, 10, 0, 0, 85.0, 5.0, status=TestStatus.PASSED),
            integration_tests=IntegrationTestResults(5, 5, 0, 0, 10.0, status=TestStatus.PASSED),
            e2e_tests=E2ETestResults(3, 3, 0, 0, 15.0, status=TestStatus.PASSED),
            security_scan=SecurityScanResults(status=TestStatus.PASSED),
            accessibility_test=AccessibilityResults(status=TestStatus.PASSED),
            performance_test=PerformanceResults(status=TestStatus.PASSED),
            overall_status=TestStatus.PASSED
        )
        
        # Mock reporter
        with patch.object(orchestrator.reporter, 'generate_all_reports') as mock_generate:
            mock_generate.return_value = {
                "json": "/path/to/report.json",
                "html": "/path/to/report.html"
            }
            
            # Generate reports
            report_paths = await orchestrator.generate_reports(results)
            
            assert "json" in report_paths
            assert "html" in report_paths
            mock_generate.assert_called_once_with(results)


class TestTestRunner:
    """Test cases for the TestRunner class."""
    
    @pytest.fixture
    def test_context(self):
        """Create a test context for testing."""
        config = TestConfiguration()
        return TestContext(
            branch="test-branch",
            commit_sha="abc123def456",
            environment="test",
            test_config=config
        )
    
    @pytest.fixture
    def test_runner(self, test_context):
        """Create a TestRunner instance for testing."""
        return TestRunner(test_context)
    
    @pytest.mark.asyncio
    async def test_run_unit_tests_success(self, test_runner):
        """Test successful unit test execution."""
        with patch.object(test_runner, '_run_command') as mock_run:
            # Mock successful pytest execution
            mock_run.return_value = Mock(returncode=0)
            
            results = await test_runner.run_unit_tests()
            
            assert results.status == TestStatus.PASSED
            assert results.total_tests > 0
            assert results.execution_time > 0
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_unit_tests_failure(self, test_runner):
        """Test unit test execution with failures."""
        with patch.object(test_runner, '_run_command') as mock_run:
            # Mock failed pytest execution
            mock_run.return_value = Mock(returncode=1)
            
            results = await test_runner.run_unit_tests()
            
            assert results.status == TestStatus.FAILED
            assert results.failed_tests > 0
    
    @pytest.mark.asyncio
    async def test_run_integration_tests(self, test_runner):
        """Test integration test execution."""
        with patch.object(test_runner, '_run_command') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            results = await test_runner.run_integration_tests()
            
            assert results.status == TestStatus.PASSED
            assert results.database_tests > 0
            assert results.api_tests > 0
    
    @pytest.mark.asyncio
    async def test_run_security_tests(self, test_runner):
        """Test security test execution."""
        with patch.object(test_runner, '_run_command') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            results = await test_runner.run_security_tests()
            
            assert results.status == TestStatus.PASSED
            assert "bandit" in results.scan_tools_used
            assert results.compliance_status == "compliant"


class TestQualityGateValidator:
    """Test cases for the QualityGateValidator class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return TestConfiguration(
            min_unit_test_coverage=80.0,
            max_critical_vulnerabilities=0,
            max_high_vulnerabilities=5,
            max_accessibility_violations=0
        )
    
    @pytest.fixture
    def validator(self, config):
        """Create a QualityGateValidator instance."""
        return QualityGateValidator(config)
    
    @pytest.mark.asyncio
    async def test_validate_all_gates_success(self, validator):
        """Test successful quality gate validation."""
        results = TestResults(
            unit_tests=UnitTestResults(10, 10, 0, 0, 85.0, 5.0, status=TestStatus.PASSED),
            integration_tests=IntegrationTestResults(5, 5, 0, 0, 10.0, status=TestStatus.PASSED),
            e2e_tests=E2ETestResults(3, 3, 0, 0, 15.0, status=TestStatus.PASSED),
            security_scan=SecurityScanResults(
                severity_counts={"critical": 0, "high": 2}, status=TestStatus.PASSED
            ),
            accessibility_test=AccessibilityResults(
                critical_violations=0, status=TestStatus.PASSED
            ),
            performance_test=PerformanceResults(status=TestStatus.PASSED),
            overall_status=TestStatus.PASSED
        )
        
        gate_results = await validator.validate_all_gates(results)
        
        assert gate_results.overall_passed is True
        assert len(gate_results.blocking_failures) == 0
    
    @pytest.mark.asyncio
    async def test_validate_all_gates_coverage_failure(self, validator):
        """Test quality gate validation with coverage failure."""
        results = TestResults(
            unit_tests=UnitTestResults(10, 7, 3, 0, 60.0, 5.0, status=TestStatus.FAILED),
            integration_tests=IntegrationTestResults(5, 5, 0, 0, 10.0, status=TestStatus.PASSED),
            e2e_tests=E2ETestResults(3, 3, 0, 0, 15.0, status=TestStatus.PASSED),
            security_scan=SecurityScanResults(status=TestStatus.PASSED),
            accessibility_test=AccessibilityResults(status=TestStatus.PASSED),
            performance_test=PerformanceResults(status=TestStatus.PASSED),
            overall_status=TestStatus.FAILED
        )
        
        gate_results = await validator.validate_all_gates(results)
        
        assert gate_results.overall_passed is False
        assert "Unit Test Coverage" in gate_results.blocking_failures
    
    @pytest.mark.asyncio
    async def test_validate_all_gates_security_failure(self, validator):
        """Test quality gate validation with security failure."""
        results = TestResults(
            unit_tests=UnitTestResults(10, 10, 0, 0, 85.0, 5.0, status=TestStatus.PASSED),
            integration_tests=IntegrationTestResults(5, 5, 0, 0, 10.0, status=TestStatus.PASSED),
            e2e_tests=E2ETestResults(3, 3, 0, 0, 15.0, status=TestStatus.PASSED),
            security_scan=SecurityScanResults(
                severity_counts={"critical": 2, "high": 3}, status=TestStatus.FAILED
            ),
            accessibility_test=AccessibilityResults(status=TestStatus.PASSED),
            performance_test=PerformanceResults(status=TestStatus.PASSED),
            overall_status=TestStatus.FAILED
        )
        
        gate_results = await validator.validate_all_gates(results)
        
        assert gate_results.overall_passed is False
        assert "Critical Security Vulnerabilities" in gate_results.blocking_failures


class TestConfigurationManager:
    """Test cases for the ConfigurationManager class."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def config_manager(self, temp_workspace):
        """Create a ConfigurationManager instance."""
        return ConfigurationManager(temp_workspace)
    
    def test_load_default_configuration(self, config_manager):
        """Test loading default configuration."""
        config = config_manager.load_configuration()
        
        assert config.parallel_execution is True
        assert config.max_workers == 4
        assert config.min_unit_test_coverage == 80.0
        assert config.run_unit_tests is True
    
    def test_load_configuration_with_env_overrides(self, config_manager):
        """Test loading configuration with environment variable overrides."""
        with patch.dict('os.environ', {
            'TEST_MAX_WORKERS': '8',
            'TEST_MIN_UNIT_COVERAGE': '90.0',
            'TEST_RUN_E2E_TESTS': 'false'
        }):
            config = config_manager.load_configuration()
            
            assert config.max_workers == 8
            assert config.min_unit_test_coverage == 90.0
            assert config.run_e2e_tests is False
    
    def test_save_and_load_configuration(self, config_manager):
        """Test saving and loading configuration."""
        # Create a custom configuration
        original_config = TestConfiguration(
            max_workers=6,
            min_unit_test_coverage=85.0,
            run_performance_tests=False
        )
        
        # Save the configuration
        config_path = config_manager.save_configuration(original_config, "custom")
        assert config_path.exists()
        
        # Load the configuration back
        loaded_config = config_manager.load_configuration("custom")
        
        assert loaded_config.max_workers == 6
        assert loaded_config.min_unit_test_coverage == 85.0
        assert loaded_config.run_performance_tests is False
    
    def test_validate_configuration_success(self, config_manager):
        """Test successful configuration validation."""
        config = TestConfiguration()
        errors = config_manager.validate_configuration(config)
        
        assert len(errors) == 0
    
    def test_validate_configuration_errors(self, config_manager):
        """Test configuration validation with errors."""
        config = TestConfiguration(
            max_workers=0,  # Invalid
            min_unit_test_coverage=150.0,  # Invalid
            max_critical_vulnerabilities=-1  # Invalid
        )
        
        errors = config_manager.validate_configuration(config)
        
        assert len(errors) > 0
        assert any("max_workers" in error for error in errors)
        assert any("min_unit_test_coverage" in error for error in errors)
        assert any("max_critical_vulnerabilities" in error for error in errors)
    
    def test_create_sample_config(self, config_manager):
        """Test creating a sample configuration file."""
        sample_path = config_manager.create_sample_config("development")
        
        assert sample_path.exists()
        assert sample_path.name == "config.development.sample.yaml"
        
        # Verify the file contains expected content
        content = sample_path.read_text()
        assert "parallel_execution" in content
        assert "min_unit_test_coverage" in content
        assert "# Test Orchestration Framework Configuration" in content


class TestTestReporter:
    """Test cases for the TestReporter class."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def test_context(self, temp_workspace):
        """Create a test context with temporary workspace."""
        config = TestConfiguration(
            report_output_dir=temp_workspace / "reports"
        )
        return TestContext(
            branch="test-branch",
            commit_sha="abc123def456",
            environment="test",
            test_config=config
        )
    
    @pytest.fixture
    def reporter(self, test_context):
        """Create a TestReporter instance."""
        return TestReporter(test_context)
    
    @pytest.fixture
    def sample_results(self):
        """Create sample test results for testing."""
        return TestResults(
            unit_tests=UnitTestResults(10, 9, 1, 0, 85.0, 5.0, status=TestStatus.PASSED),
            integration_tests=IntegrationTestResults(5, 5, 0, 0, 10.0, status=TestStatus.PASSED),
            e2e_tests=E2ETestResults(3, 3, 0, 0, 15.0, status=TestStatus.PASSED),
            security_scan=SecurityScanResults(
                severity_counts={"high": 1, "medium": 2}, 
                scan_tools_used=["bandit"], 
                status=TestStatus.PASSED
            ),
            accessibility_test=AccessibilityResults(
                total_violations=0, critical_violations=0, status=TestStatus.PASSED
            ),
            performance_test=PerformanceResults(
                response_time_p50=120.0, throughput_rps=150.0, status=TestStatus.PASSED
            ),
            overall_status=TestStatus.PASSED,
            quality_gate_passed=True,
            execution_start_time=datetime.now(),
            execution_end_time=datetime.now(),
            total_execution_time=30.0
        )
    
    @pytest.mark.asyncio
    async def test_generate_json_report(self, reporter, sample_results):
        """Test JSON report generation."""
        report_path = await reporter.generate_json_report(sample_results)
        
        assert report_path.exists()
        assert report_path.suffix == ".json"
        
        # Verify JSON content
        with open(report_path) as f:
            report_data = json.load(f)
        
        assert "metadata" in report_data
        assert "summary" in report_data
        assert "test_results" in report_data
        assert report_data["summary"]["overall_status"] == "passed"
    
    @pytest.mark.asyncio
    async def test_generate_html_report(self, reporter, sample_results):
        """Test HTML report generation."""
        report_path = await reporter.generate_html_report(sample_results)
        
        assert report_path.exists()
        assert report_path.suffix == ".html"
        
        # Verify HTML content contains expected elements
        content = report_path.read_text()
        assert "<html" in content
        assert "Test Results Report" in content
        assert "PASSED" in content
    
    @pytest.mark.asyncio
    async def test_generate_markdown_summary(self, reporter, sample_results):
        """Test markdown summary generation."""
        report_path = await reporter.generate_markdown_summary(sample_results)
        
        assert report_path.exists()
        assert report_path.suffix == ".md"
        
        # Verify markdown content
        content = report_path.read_text()
        assert "# Test Results Summary" in content
        assert "✅ PASSED" in content
        assert "Unit Tests" in content
    
    @pytest.mark.asyncio
    async def test_generate_all_reports(self, reporter, sample_results):
        """Test generating all report types."""
        report_paths = await reporter.generate_all_reports(sample_results)
        
        assert "json" in report_paths
        assert "html" in report_paths
        assert "markdown" in report_paths
        assert "quality_gates" in report_paths
        
        # Verify all files exist
        for report_type, path in report_paths.items():
            assert Path(path).exists()


# Integration test for the complete orchestration flow
class TestOrchestrationIntegration:
    """Integration tests for the complete orchestration framework."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_orchestration_flow(self, temp_workspace):
        """Test the complete orchestration flow from configuration to reporting."""
        # Set up configuration
        config_manager = ConfigurationManager(temp_workspace)
        config = config_manager.load_configuration()
        config.report_output_dir = temp_workspace / "reports"
        config.run_e2e_tests = False  # Disable for faster testing
        config.run_performance_tests = False
        
        # Create test context
        context = TestContext(
            branch="integration-test",
            commit_sha="integration123",
            environment="test",
            test_config=config,
            workspace_root=temp_workspace
        )
        
        # Create orchestrator
        orchestrator = TestOrchestrator(context)
        
        # Mock test execution to avoid actual test runs
        with patch.object(orchestrator.test_runner, 'run_unit_tests') as mock_unit, \
             patch.object(orchestrator.test_runner, 'run_integration_tests') as mock_integration, \
             patch.object(orchestrator.test_runner, 'run_security_tests') as mock_security:
            
            # Configure successful test results
            mock_unit.return_value = UnitTestResults(
                10, 10, 0, 0, 85.0, 5.0, status=TestStatus.PASSED
            )
            mock_integration.return_value = IntegrationTestResults(
                5, 5, 0, 0, 10.0, status=TestStatus.PASSED
            )
            mock_security.return_value = SecurityScanResults(
                severity_counts={}, status=TestStatus.PASSED
            )
            
            # Execute the complete flow
            results = await orchestrator.execute_test_pipeline()
            quality_passed = await orchestrator.validate_quality_gates(results)
            report_paths = await orchestrator.generate_reports(results)
            
            # Verify results
            assert results.overall_status == TestStatus.PASSED
            assert quality_passed is True
            assert results.quality_gate_passed is True
            assert len(report_paths) > 0
            
            # Verify reports were generated
            for report_path in report_paths.values():
                assert Path(report_path).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])