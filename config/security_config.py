"""
Security scanning configuration and settings.

This module provides configuration management for the security scanning system,
including tool-specific settings, thresholds, and integration parameters.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from services.security_scanner import SecurityScannerConfig, SeverityLevel


class BanditConfig(BaseModel):
    """Configuration for Bandit static analysis tool."""
    config_file: Optional[str] = None
    exclude_paths: List[str] = Field(default_factory=lambda: [
        "*/tests/*", "*/test_*", "*_test.py", "*/migrations/*"
    ])
    skip_tests: List[str] = Field(default_factory=lambda: [
        "B101",  # assert_used - common in tests
        "B601",  # paramiko_calls - if using paramiko legitimately
    ])
    confidence_level: str = "HIGH"  # LOW, MEDIUM, HIGH
    severity_level: str = "LOW"     # LOW, MEDIUM, HIGH


class SafetyConfig(BaseModel):
    """Configuration for Safety dependency scanner."""
    db_path: Optional[str] = None
    ignore_vulnerabilities: List[str] = Field(default_factory=list)
    requirements_files: List[str] = Field(default_factory=lambda: [
        "requirements.txt",
        "requirements-dev.txt", 
        "requirements/base.txt",
        "requirements/production.txt"
    ])
    full_report: bool = True
    output_format: str = "json"


class ContainerSecurityConfig(BaseModel):
    """Configuration for container security scanning."""
    dockerfile_patterns: List[str] = Field(default_factory=lambda: [
        "Dockerfile*", "*.dockerfile", "docker/Dockerfile*"
    ])
    base_image_whitelist: List[str] = Field(default_factory=lambda: [
        "python:3.11-slim",
        "node:18-alpine",
        "nginx:alpine",
        "postgres:15-alpine"
    ])
    security_checks: Dict[str, bool] = Field(default_factory=lambda: {
        "check_root_user": True,
        "check_latest_tag": True,
        "check_add_vs_copy": True,
        "check_exposed_ports": True,
        "check_health_check": True,
        "check_user_creation": True
    })


class SecretsDetectionConfig(BaseModel):
    """Configuration for secrets detection."""
    enabled_patterns: Dict[str, str] = Field(default_factory=lambda: {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "AWS Secret Key": r"[0-9a-zA-Z/+]{40}",
        "GitHub Token": r"ghp_[0-9a-zA-Z]{36}",
        "Generic API Key": r"[aA][pP][iI][_]?[kK][eE][yY].*['\"][0-9a-zA-Z]{32,45}['\"]",
        "Generic Secret": r"[sS][eE][cC][rR][eE][tT].*['\"][0-9a-zA-Z]{16,}['\"]",
        "Database URL": r"(postgresql|mysql|mongodb)://[^\\s]+",
        "Private Key": r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----",
        "JWT Token": r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*",
        "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})?",
        "Discord Token": r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}",
        "Stripe Key": r"sk_live_[0-9a-zA-Z]{24}"
    })
    exclude_patterns: List[str] = Field(default_factory=lambda: [
        r"example",
        r"placeholder",
        r"your_.*_here",
        r"xxx+",
        r"test.*key",
        r"fake.*secret"
    ])
    file_extensions: List[str] = Field(default_factory=lambda: [
        ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".env", 
        ".config", ".ini", ".conf", ".properties"
    ])


class QualityGateConfig(BaseModel):
    """Configuration for security quality gates."""
    max_critical_vulnerabilities: int = 0
    max_high_vulnerabilities: int = 5
    max_medium_vulnerabilities: int = 20
    max_low_vulnerabilities: int = 50
    
    # Fail build conditions
    fail_on_critical: bool = True
    fail_on_high: bool = True
    fail_on_medium: bool = False
    fail_on_low: bool = False
    
    # Compliance requirements
    require_zero_secrets: bool = True
    require_dependency_scan: bool = True
    require_container_scan: bool = True
    
    # Remediation requirements
    require_remediation_plan: bool = True
    max_remediation_days: int = 30


class SecurityReportingConfig(BaseModel):
    """Configuration for security reporting."""
    output_formats: List[str] = Field(default_factory=lambda: ["json", "html", "pdf"])
    include_executive_summary: bool = True
    include_technical_details: bool = True
    include_remediation_plan: bool = True
    include_compliance_status: bool = True
    
    # Report distribution
    email_recipients: List[str] = Field(default_factory=list)
    slack_webhook: Optional[str] = None
    jira_integration: bool = False
    
    # Report storage
    report_retention_days: int = 90
    archive_reports: bool = True


class SecuritySettings(BaseSettings):
    """Main security settings configuration."""
    
    # Tool configurations
    bandit: BanditConfig = Field(default_factory=BanditConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    container_security: ContainerSecurityConfig = Field(default_factory=ContainerSecurityConfig)
    secrets_detection: SecretsDetectionConfig = Field(default_factory=SecretsDetectionConfig)
    
    # Quality gates and thresholds
    quality_gates: QualityGateConfig = Field(default_factory=QualityGateConfig)
    
    # Reporting configuration
    reporting: SecurityReportingConfig = Field(default_factory=SecurityReportingConfig)
    
    # General settings
    project_root: str = Field(default=".")
    exclude_paths: List[str] = Field(default_factory=lambda: [
        ".git", ".pytest_cache", "__pycache__", ".venv", "node_modules",
        ".mypy_cache", ".coverage", "htmlcov", "dist", "build"
    ])
    
    # Integration settings
    ci_mode: bool = Field(default=False, description="Enable CI/CD specific behaviors")
    parallel_scanning: bool = Field(default=True, description="Enable parallel tool execution")
    cache_results: bool = Field(default=True, description="Cache scan results for performance")
    
    # Environment-specific overrides
    environment: str = Field(default="development", description="Current environment")
    
    class Config:
        env_prefix = "SECURITY_"
        env_file = ".env"
        case_sensitive = False


def get_security_config() -> SecuritySettings:
    """Get security configuration with environment overrides."""
    return SecuritySettings()


def create_scanner_config(security_settings: SecuritySettings) -> SecurityScannerConfig:
    """Create SecurityScannerConfig from SecuritySettings."""
    return SecurityScannerConfig(
        bandit_config_file=security_settings.bandit.config_file,
        safety_db_path=security_settings.safety.db_path,
        container_scan_enabled=True,
        secrets_scan_enabled=True,
        zap_scan_enabled=False,  # Requires separate OWASP ZAP installation
        exclude_paths=security_settings.exclude_paths,
        severity_threshold=SeverityLevel.HIGH,
        fail_on_critical=security_settings.quality_gates.fail_on_critical,
        fail_on_high=security_settings.quality_gates.fail_on_high
    )


def get_bandit_config_file(security_settings: SecuritySettings) -> Optional[str]:
    """Generate Bandit configuration file if needed."""
    if not security_settings.bandit.config_file:
        return None
    
    config_path = Path(security_settings.bandit.config_file)
    if config_path.exists():
        return str(config_path)
    
    # Generate default Bandit configuration
    bandit_config = {
        "exclude_dirs": security_settings.bandit.exclude_paths,
        "skips": security_settings.bandit.skip_tests,
        "tests": [],  # Use all tests by default
    }
    
    # Write configuration file
    import yaml
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(bandit_config, f, default_flow_style=False)
    
    return str(config_path)


def validate_security_tools() -> Dict[str, bool]:
    """Validate that required security tools are available."""
    import subprocess
    import shutil
    
    tools_status = {}
    
    # Check Bandit
    tools_status["bandit"] = shutil.which("bandit") is not None
    
    # Check Safety
    tools_status["safety"] = shutil.which("safety") is not None
    
    # Check Docker (for container scanning)
    tools_status["docker"] = shutil.which("docker") is not None
    
    # Check OWASP ZAP (optional)
    tools_status["zap"] = shutil.which("zap.sh") is not None or shutil.which("zap.bat") is not None
    
    return tools_status


def setup_security_environment():
    """Set up security scanning environment."""
    # Create necessary directories
    directories = [
        "reports/security",
        "config/security",
        ".security_cache"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Validate tools
    tools_status = validate_security_tools()
    
    missing_tools = [tool for tool, available in tools_status.items() if not available and tool != "zap"]
    if missing_tools:
        print(f"Warning: Missing security tools: {', '.join(missing_tools)}")
        print("Install missing tools:")
        if "bandit" in missing_tools:
            print("  pip install bandit")
        if "safety" in missing_tools:
            print("  pip install safety")
        if "docker" in missing_tools:
            print("  Install Docker from https://docker.com")
    
    return tools_status


if __name__ == "__main__":
    # Setup and validate security environment
    print("Setting up security scanning environment...")
    tools_status = setup_security_environment()
    
    print("\nSecurity Tools Status:")
    for tool, available in tools_status.items():
        status = "✓ Available" if available else "✗ Missing"
        print(f"  {tool}: {status}")
    
    # Load and display configuration
    config = get_security_config()
    print(f"\nSecurity configuration loaded for environment: {config.environment}")
    print(f"Quality gates - Critical: {config.quality_gates.max_critical_vulnerabilities}, High: {config.quality_gates.max_high_vulnerabilities}")