"""
Configuration management for the testing orchestration framework.

This module provides configuration loading, validation, and management
for test execution settings, quality gate thresholds, and environment-specific
configurations.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .models import TestConfiguration

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Manages configuration loading and validation for the testing framework.
    
    This class handles loading configuration from multiple sources including
    environment variables, configuration files, and default values.
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.cwd()
        self.config_dir = self.workspace_root / ".kiro" / "testing"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def load_configuration(self, environment: str = "test") -> TestConfiguration:
        """
        Load test configuration from multiple sources.
        
        Args:
            environment: Target environment (test, staging, production)
            
        Returns:
            TestConfiguration: Loaded and validated configuration
        """
        logger.info(f"Loading configuration for environment: {environment}")
        
        # Start with default configuration
        config_data = self._get_default_config()
        
        # Load from configuration files
        config_file_data = self._load_config_files(environment)
        config_data.update(config_file_data)
        
        # Override with environment variables
        env_overrides = self._load_environment_overrides()
        config_data.update(env_overrides)
        
        # Validate and create configuration object
        config = self._create_configuration(config_data)
        
        logger.info("Configuration loaded successfully")
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            # General settings
            "parallel_execution": True,
            "max_workers": 4,
            "timeout_seconds": 3600,
            
            # Test type enablement
            "run_unit_tests": True,
            "run_integration_tests": True,
            "run_e2e_tests": True,
            "run_security_tests": True,
            "run_accessibility_tests": True,
            "run_performance_tests": True,
            
            # Quality gate thresholds
            "min_unit_test_coverage": 80.0,
            "min_integration_test_coverage": 70.0,
            "max_critical_vulnerabilities": 0,
            "max_high_vulnerabilities": 5,
            "max_accessibility_violations": 0,
            "max_performance_regression": 10.0,
            
            # Environment settings
            "test_database_url": None,
            "test_redis_url": None,
            "test_environment": "test",
            
            # Reporting settings
            "generate_html_reports": True,
            "generate_json_reports": True,
            "report_output_dir": "test_reports"
        }
    
    def _load_config_files(self, environment: str) -> Dict[str, Any]:
        """Load configuration from YAML/JSON files."""
        config_data = {}
        
        # Load base configuration
        base_config_path = self.config_dir / "config.yaml"
        if base_config_path.exists():
            config_data.update(self._load_yaml_file(base_config_path))
        
        # Load environment-specific configuration
        env_config_path = self.config_dir / f"config.{environment}.yaml"
        if env_config_path.exists():
            env_config = self._load_yaml_file(env_config_path)
            config_data.update(env_config)
        
        # Also check for JSON files
        json_config_path = self.config_dir / "config.json"
        if json_config_path.exists():
            config_data.update(self._load_json_file(json_config_path))
        
        return config_data
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from a YAML file."""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load YAML config from {file_path}: {e}")
            return {}
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load JSON config from {file_path}: {e}")
            return {}
    
    def _load_environment_overrides(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables."""
        env_overrides = {}
        
        # Map environment variables to configuration keys
        env_mappings = {
            "TEST_PARALLEL_EXECUTION": ("parallel_execution", bool),
            "TEST_MAX_WORKERS": ("max_workers", int),
            "TEST_TIMEOUT_SECONDS": ("timeout_seconds", int),
            
            "TEST_RUN_UNIT_TESTS": ("run_unit_tests", bool),
            "TEST_RUN_INTEGRATION_TESTS": ("run_integration_tests", bool),
            "TEST_RUN_E2E_TESTS": ("run_e2e_tests", bool),
            "TEST_RUN_SECURITY_TESTS": ("run_security_tests", bool),
            "TEST_RUN_ACCESSIBILITY_TESTS": ("run_accessibility_tests", bool),
            "TEST_RUN_PERFORMANCE_TESTS": ("run_performance_tests", bool),
            
            "TEST_MIN_UNIT_COVERAGE": ("min_unit_test_coverage", float),
            "TEST_MIN_INTEGRATION_COVERAGE": ("min_integration_test_coverage", float),
            "TEST_MAX_CRITICAL_VULNS": ("max_critical_vulnerabilities", int),
            "TEST_MAX_HIGH_VULNS": ("max_high_vulnerabilities", int),
            "TEST_MAX_ACCESSIBILITY_VIOLATIONS": ("max_accessibility_violations", int),
            "TEST_MAX_PERFORMANCE_REGRESSION": ("max_performance_regression", float),
            
            "TEST_DATABASE_URL": ("test_database_url", str),
            "TEST_REDIS_URL": ("test_redis_url", str),
            "TEST_ENVIRONMENT": ("test_environment", str),
            
            "TEST_GENERATE_HTML_REPORTS": ("generate_html_reports", bool),
            "TEST_GENERATE_JSON_REPORTS": ("generate_json_reports", bool),
            "TEST_REPORT_OUTPUT_DIR": ("report_output_dir", str)
        }
        
        for env_var, (config_key, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if value_type == bool:
                        env_overrides[config_key] = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == int:
                        env_overrides[config_key] = int(env_value)
                    elif value_type == float:
                        env_overrides[config_key] = float(env_value)
                    else:
                        env_overrides[config_key] = env_value
                except ValueError as e:
                    logger.warning(f"Invalid value for {env_var}: {env_value} ({e})")
        
        return env_overrides
    
    def _create_configuration(self, config_data: Dict[str, Any]) -> TestConfiguration:
        """Create a TestConfiguration object from configuration data."""
        # Convert report_output_dir to Path if it's a string
        if isinstance(config_data.get("report_output_dir"), str):
            config_data["report_output_dir"] = Path(config_data["report_output_dir"])
        
        return TestConfiguration(**config_data)
    
    def save_configuration(self, config: TestConfiguration, environment: str = "test") -> Path:
        """
        Save configuration to a YAML file.
        
        Args:
            config: Configuration to save
            environment: Target environment
            
        Returns:
            Path: Path to the saved configuration file
        """
        config_path = self.config_dir / f"config.{environment}.yaml"
        
        # Convert configuration to dictionary
        config_dict = {
            "parallel_execution": config.parallel_execution,
            "max_workers": config.max_workers,
            "timeout_seconds": config.timeout_seconds,
            
            "run_unit_tests": config.run_unit_tests,
            "run_integration_tests": config.run_integration_tests,
            "run_e2e_tests": config.run_e2e_tests,
            "run_security_tests": config.run_security_tests,
            "run_accessibility_tests": config.run_accessibility_tests,
            "run_performance_tests": config.run_performance_tests,
            
            "min_unit_test_coverage": config.min_unit_test_coverage,
            "min_integration_test_coverage": config.min_integration_test_coverage,
            "max_critical_vulnerabilities": config.max_critical_vulnerabilities,
            "max_high_vulnerabilities": config.max_high_vulnerabilities,
            "max_accessibility_violations": config.max_accessibility_violations,
            "max_performance_regression": config.max_performance_regression,
            
            "test_database_url": config.test_database_url,
            "test_redis_url": config.test_redis_url,
            "test_environment": config.test_environment,
            
            "generate_html_reports": config.generate_html_reports,
            "generate_json_reports": config.generate_json_reports,
            "report_output_dir": str(config.report_output_dir)
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
        return config_path
    
    def validate_configuration(self, config: TestConfiguration) -> List[str]:
        """
        Validate configuration for consistency and correctness.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate numeric ranges
        if config.max_workers < 1:
            errors.append("max_workers must be at least 1")
        
        if config.timeout_seconds < 60:
            errors.append("timeout_seconds must be at least 60")
        
        if not (0 <= config.min_unit_test_coverage <= 100):
            errors.append("min_unit_test_coverage must be between 0 and 100")
        
        if not (0 <= config.min_integration_test_coverage <= 100):
            errors.append("min_integration_test_coverage must be between 0 and 100")
        
        if config.max_critical_vulnerabilities < 0:
            errors.append("max_critical_vulnerabilities cannot be negative")
        
        if config.max_high_vulnerabilities < 0:
            errors.append("max_high_vulnerabilities cannot be negative")
        
        if config.max_accessibility_violations < 0:
            errors.append("max_accessibility_violations cannot be negative")
        
        if not (0 <= config.max_performance_regression <= 100):
            errors.append("max_performance_regression must be between 0 and 100")
        
        # Validate that at least one test type is enabled
        test_types_enabled = [
            config.run_unit_tests,
            config.run_integration_tests,
            config.run_e2e_tests,
            config.run_security_tests,
            config.run_accessibility_tests,
            config.run_performance_tests
        ]
        
        if not any(test_types_enabled):
            errors.append("At least one test type must be enabled")
        
        # Validate report output directory
        try:
            config.report_output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create report output directory: {e}")
        
        return errors
    
    def create_sample_config(self, environment: str = "test") -> Path:
        """
        Create a sample configuration file with comments.
        
        Args:
            environment: Target environment for the sample config
            
        Returns:
            Path: Path to the created sample configuration file
        """
        sample_config = """# Test Orchestration Framework Configuration
# This file contains configuration settings for the testing framework

# General execution settings
parallel_execution: true        # Enable parallel test execution
max_workers: 4                 # Maximum number of parallel workers
timeout_seconds: 3600          # Overall timeout for test execution

# Test type enablement - set to false to disable specific test types
run_unit_tests: true
run_integration_tests: true
run_e2e_tests: true
run_security_tests: true
run_accessibility_tests: true
run_performance_tests: true

# Quality gate thresholds - adjust based on your project requirements
min_unit_test_coverage: 80.0          # Minimum unit test coverage percentage
min_integration_test_coverage: 70.0   # Minimum integration test coverage percentage
max_critical_vulnerabilities: 0       # Maximum allowed critical security vulnerabilities
max_high_vulnerabilities: 5           # Maximum allowed high security vulnerabilities
max_accessibility_violations: 0       # Maximum allowed critical accessibility violations
max_performance_regression: 10.0      # Maximum allowed performance regression percentage

# Environment-specific settings
test_database_url: null        # Override database URL for testing (null = use default)
test_redis_url: null          # Override Redis URL for testing (null = use default)
test_environment: test        # Environment identifier

# Reporting settings
generate_html_reports: true   # Generate HTML reports
generate_json_reports: true   # Generate JSON reports
report_output_dir: test_reports  # Directory for report output
"""
        
        config_path = self.config_dir / f"config.{environment}.sample.yaml"
        
        with open(config_path, 'w') as f:
            f.write(sample_config)
        
        logger.info(f"Sample configuration created at {config_path}")
        return config_path