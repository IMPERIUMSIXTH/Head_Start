"""
Security scanning and validation engine for comprehensive security testing.

This module provides security scanning capabilities including:
- Static code analysis with Bandit
- Dependency vulnerability scanning with Safety
- Container security scanning
- Secrets detection and validation
- Integration with OWASP ZAP for dynamic analysis
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SeverityLevel(str, Enum):
    """Security vulnerability severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class VulnerabilityType(str, Enum):
    """Types of security vulnerabilities."""
    CODE_VULNERABILITY = "CODE_VULNERABILITY"
    DEPENDENCY_VULNERABILITY = "DEPENDENCY_VULNERABILITY"
    CONTAINER_VULNERABILITY = "CONTAINER_VULNERABILITY"
    SECRET_EXPOSURE = "SECRET_EXPOSURE"
    CONFIGURATION_ISSUE = "CONFIGURATION_ISSUE"


@dataclass
class Vulnerability:
    """Represents a security vulnerability."""
    id: str
    title: str
    description: str
    severity: SeverityLevel
    vulnerability_type: VulnerabilityType
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    remediation: Optional[str] = None
    confidence: Optional[str] = None
    more_info: Optional[str] = None


@dataclass
class ScanResult:
    """Base class for security scan results."""
    tool_name: str
    scan_type: str
    timestamp: datetime
    duration_seconds: float
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class SecurityScanResults:
    """Comprehensive security scan results."""
    scan_id: str
    timestamp: datetime
    total_vulnerabilities: int
    severity_counts: Dict[SeverityLevel, int]
    scan_results: List[ScanResult]
    compliance_status: Dict[str, bool]
    remediation_required: bool
    scan_tools_used: List[str]
    
    def get_critical_vulnerabilities(self) -> List[Vulnerability]:
        """Get all critical vulnerabilities."""
        critical_vulns = []
        for scan_result in self.scan_results:
            critical_vulns.extend([
                v for v in scan_result.vulnerabilities 
                if v.severity == SeverityLevel.CRITICAL
            ])
        return critical_vulns
    
    def get_high_vulnerabilities(self) -> List[Vulnerability]:
        """Get all high severity vulnerabilities."""
        high_vulns = []
        for scan_result in self.scan_results:
            high_vulns.extend([
                v for v in scan_result.vulnerabilities 
                if v.severity == SeverityLevel.HIGH
            ])
        return high_vulns


class SecurityScannerConfig(BaseModel):
    """Configuration for security scanner."""
    bandit_config_file: Optional[str] = None
    safety_db_path: Optional[str] = None
    container_scan_enabled: bool = True
    secrets_scan_enabled: bool = True
    zap_scan_enabled: bool = False  # Requires OWASP ZAP installation
    exclude_paths: List[str] = Field(default_factory=lambda: [
        ".git", ".pytest_cache", "__pycache__", ".venv", "node_modules"
    ])
    severity_threshold: SeverityLevel = SeverityLevel.HIGH
    fail_on_critical: bool = True
    fail_on_high: bool = True


class SecurityScanner:
    """Main security scanner class that orchestrates various security tools."""
    
    def __init__(self, config: Optional[SecurityScannerConfig] = None):
        """Initialize the security scanner."""
        self.config = config or SecurityScannerConfig()
        self.scan_id = f"security_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    async def run_comprehensive_scan(
        self, 
        project_path: str = "."
    ) -> SecurityScanResults:
        """Run comprehensive security scan including all enabled tools."""
        logger.info(f"Starting comprehensive security scan: {self.scan_id}")
        start_time = datetime.now()
        
        scan_results = []
        
        # Run static code analysis with Bandit
        bandit_result = await self.run_bandit_scan(project_path)
        if bandit_result:
            scan_results.append(bandit_result)
        
        # Run dependency vulnerability scan with Safety
        safety_result = await self.run_safety_scan(project_path)
        if safety_result:
            scan_results.append(safety_result)
        
        # Run secrets detection
        if self.config.secrets_scan_enabled:
            secrets_result = await self.run_secrets_scan(project_path)
            if secrets_result:
                scan_results.append(secrets_result)
        
        # Run container security scan if enabled
        if self.config.container_scan_enabled:
            container_result = await self.run_container_scan(project_path)
            if container_result:
                scan_results.append(container_result)
        
        # Aggregate results
        all_vulnerabilities = []
        for result in scan_results:
            all_vulnerabilities.extend(result.vulnerabilities)
        
        severity_counts = self._count_vulnerabilities_by_severity(all_vulnerabilities)
        
        return SecurityScanResults(
            scan_id=self.scan_id,
            timestamp=start_time,
            total_vulnerabilities=len(all_vulnerabilities),
            severity_counts=severity_counts,
            scan_results=scan_results,
            compliance_status=self._assess_compliance(severity_counts),
            remediation_required=self._requires_remediation(severity_counts),
            scan_tools_used=[result.tool_name for result in scan_results]
        )
    
    async def run_bandit_scan(self, project_path: str) -> Optional[ScanResult]:
        """Run Bandit static code analysis."""
        logger.info("Running Bandit static code analysis")
        start_time = datetime.now()
        
        try:
            # Prepare Bandit command
            cmd = [
                "bandit",
                "-r", project_path,
                "-f", "json",
                "--skip", ",".join(self.config.exclude_paths)
            ]
            
            if self.config.bandit_config_file:
                cmd.extend(["-c", self.config.bandit_config_file])
            
            # Run Bandit
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            duration = (datetime.now() - start_time).total_seconds()
            
            if process.returncode not in [0, 1]:  # Bandit returns 1 when issues found
                logger.error(f"Bandit scan failed: {stderr.decode()}")
                return None
            
            # Parse Bandit results
            vulnerabilities = self._parse_bandit_results(stdout.decode())
            
            return ScanResult(
                tool_name="Bandit",
                scan_type="Static Code Analysis",
                timestamp=start_time,
                duration_seconds=duration,
                vulnerabilities=vulnerabilities,
                metadata={"return_code": process.returncode}
            )
            
        except Exception as e:
            logger.error(f"Error running Bandit scan: {e}")
            return None
    
    async def run_safety_scan(self, project_path: str) -> Optional[ScanResult]:
        """Run Safety dependency vulnerability scan."""
        logger.info("Running Safety dependency vulnerability scan")
        start_time = datetime.now()
        
        try:
            # Look for requirements files
            requirements_files = [
                "requirements.txt",
                "requirements-dev.txt",
                "requirements/base.txt",
                "requirements/production.txt"
            ]
            
            found_requirements = []
            for req_file in requirements_files:
                req_path = Path(project_path) / req_file
                if req_path.exists():
                    found_requirements.append(str(req_path))
            
            if not found_requirements:
                logger.warning("No requirements files found for Safety scan")
                return None
            
            vulnerabilities = []
            
            for req_file in found_requirements:
                cmd = ["safety", "check", "-r", req_file, "--json"]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    # No vulnerabilities found
                    continue
                elif process.returncode == 64:
                    # Vulnerabilities found
                    vulns = self._parse_safety_results(stdout.decode(), req_file)
                    vulnerabilities.extend(vulns)
                else:
                    logger.error(f"Safety scan failed for {req_file}: {stderr.decode()}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return ScanResult(
                tool_name="Safety",
                scan_type="Dependency Vulnerability Scan",
                timestamp=start_time,
                duration_seconds=duration,
                vulnerabilities=vulnerabilities,
                metadata={"requirements_files": found_requirements}
            )
            
        except Exception as e:
            logger.error(f"Error running Safety scan: {e}")
            return None
    
    async def run_secrets_scan(self, project_path: str) -> Optional[ScanResult]:
        """Run secrets detection scan."""
        logger.info("Running secrets detection scan")
        start_time = datetime.now()
        
        try:
            vulnerabilities = []
            
            # Define patterns for common secrets
            secret_patterns = {
                "AWS Access Key": r"AKIA[0-9A-Z]{16}",
                "AWS Secret Key": r"[0-9a-zA-Z/+]{40}",
                "GitHub Token": r"ghp_[0-9a-zA-Z]{36}",
                "Generic API Key": r"[aA][pP][iI][_]?[kK][eE][yY].*['\"][0-9a-zA-Z]{32,45}['\"]",
                "Generic Secret": r"[sS][eE][cC][rR][eE][tT].*['\"][0-9a-zA-Z]{16,}['\"]",
                "Database URL": r"(postgresql|mysql|mongodb)://[^\\s]+",
                "Private Key": r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----"
            }
            
            # Scan files for secrets
            for root, dirs, files in os.walk(project_path):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in self.config.exclude_paths]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.json', '.yaml', '.yml', '.env')):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, project_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                            secrets_found = self._scan_file_for_secrets(
                                content, relative_path, secret_patterns
                            )
                            vulnerabilities.extend(secrets_found)
                            
                        except Exception as e:
                            logger.warning(f"Could not scan file {file_path}: {e}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return ScanResult(
                tool_name="SecretsDetector",
                scan_type="Secrets Detection",
                timestamp=start_time,
                duration_seconds=duration,
                vulnerabilities=vulnerabilities,
                metadata={"patterns_used": list(secret_patterns.keys())}
            )
            
        except Exception as e:
            logger.error(f"Error running secrets scan: {e}")
            return None
    
    async def run_container_scan(self, project_path: str) -> Optional[ScanResult]:
        """Run container security scan."""
        logger.info("Running container security scan")
        start_time = datetime.now()
        
        try:
            vulnerabilities = []
            
            # Look for Dockerfiles
            dockerfiles = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.lower().startswith('dockerfile'):
                        dockerfiles.append(os.path.join(root, file))
            
            if not dockerfiles:
                logger.info("No Dockerfiles found for container scan")
                return None
            
            # Analyze Dockerfiles for security issues
            for dockerfile_path in dockerfiles:
                relative_path = os.path.relpath(dockerfile_path, project_path)
                docker_vulns = await self._analyze_dockerfile(dockerfile_path, relative_path)
                vulnerabilities.extend(docker_vulns)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return ScanResult(
                tool_name="DockerfileAnalyzer",
                scan_type="Container Security Scan",
                timestamp=start_time,
                duration_seconds=duration,
                vulnerabilities=vulnerabilities,
                metadata={"dockerfiles_scanned": len(dockerfiles)}
            )
            
        except Exception as e:
            logger.error(f"Error running container scan: {e}")
            return None
    
    def _parse_bandit_results(self, bandit_output: str) -> List[Vulnerability]:
        """Parse Bandit JSON output into Vulnerability objects."""
        vulnerabilities = []
        
        try:
            if not bandit_output.strip():
                return vulnerabilities
                
            data = json.loads(bandit_output)
            
            for result in data.get("results", []):
                severity_map = {
                    "HIGH": SeverityLevel.HIGH,
                    "MEDIUM": SeverityLevel.MEDIUM,
                    "LOW": SeverityLevel.LOW
                }
                
                vulnerability = Vulnerability(
                    id=f"BANDIT-{result.get('test_id', 'UNKNOWN')}",
                    title=result.get("test_name", "Unknown Bandit Issue"),
                    description=result.get("issue_text", ""),
                    severity=severity_map.get(result.get("issue_severity", "LOW"), SeverityLevel.LOW),
                    vulnerability_type=VulnerabilityType.CODE_VULNERABILITY,
                    file_path=result.get("filename"),
                    line_number=result.get("line_number"),
                    cwe_id=result.get("test_id"),
                    confidence=result.get("issue_confidence"),
                    more_info=result.get("more_info")
                )
                vulnerabilities.append(vulnerability)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bandit results: {e}")
        except Exception as e:
            logger.error(f"Error processing Bandit results: {e}")
        
        return vulnerabilities
    
    def _parse_safety_results(self, safety_output: str, requirements_file: str) -> List[Vulnerability]:
        """Parse Safety JSON output into Vulnerability objects."""
        vulnerabilities = []
        
        try:
            if not safety_output.strip():
                return vulnerabilities
                
            data = json.loads(safety_output)
            
            for vuln_data in data:
                vulnerability = Vulnerability(
                    id=f"SAFETY-{vuln_data.get('id', 'UNKNOWN')}",
                    title=f"Vulnerable dependency: {vuln_data.get('package_name', 'Unknown')}",
                    description=vuln_data.get("advisory", ""),
                    severity=SeverityLevel.HIGH,  # Safety typically reports high-severity issues
                    vulnerability_type=VulnerabilityType.DEPENDENCY_VULNERABILITY,
                    file_path=requirements_file,
                    cve_id=vuln_data.get("cve"),
                    remediation=f"Update {vuln_data.get('package_name')} to version {vuln_data.get('analyzed_version', 'latest')} or higher",
                    more_info=vuln_data.get("more_info_url")
                )
                vulnerabilities.append(vulnerability)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Safety results: {e}")
        except Exception as e:
            logger.error(f"Error processing Safety results: {e}")
        
        return vulnerabilities
    
    def _scan_file_for_secrets(
        self, 
        content: str, 
        file_path: str, 
        patterns: Dict[str, str]
    ) -> List[Vulnerability]:
        """Scan file content for potential secrets."""
        import re
        
        vulnerabilities = []
        lines = content.split('\n')
        
        for pattern_name, pattern in patterns.items():
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    # Skip if it looks like a test or example
                    if any(keyword in file_path.lower() for keyword in ['test', 'example', 'sample', 'demo']):
                        continue
                    
                    # Skip if it's clearly a placeholder
                    matched_text = match.group(0)
                    if any(placeholder in matched_text.lower() for placeholder in ['example', 'placeholder', 'your_', 'xxx', 'test']):
                        continue
                    
                    vulnerability = Vulnerability(
                        id=f"SECRET-{pattern_name.replace(' ', '_').upper()}-{line_num}",
                        title=f"Potential {pattern_name} exposure",
                        description=f"Potential {pattern_name} found in source code",
                        severity=SeverityLevel.CRITICAL,
                        vulnerability_type=VulnerabilityType.SECRET_EXPOSURE,
                        file_path=file_path,
                        line_number=line_num,
                        remediation=f"Remove hardcoded {pattern_name} and use environment variables or secure secret management"
                    )
                    vulnerabilities.append(vulnerability)
        
        return vulnerabilities
    
    async def _analyze_dockerfile(self, dockerfile_path: str, relative_path: str) -> List[Vulnerability]:
        """Analyze Dockerfile for security issues."""
        vulnerabilities = []
        
        try:
            with open(dockerfile_path, 'r') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip().upper()
                
                # Check for running as root
                if line.startswith('USER ROOT') or (line.startswith('USER') and '0' in line):
                    vulnerabilities.append(Vulnerability(
                        id=f"DOCKER-ROOT-USER-{line_num}",
                        title="Container running as root user",
                        description="Container is configured to run as root user, which poses security risks",
                        severity=SeverityLevel.HIGH,
                        vulnerability_type=VulnerabilityType.CONFIGURATION_ISSUE,
                        file_path=relative_path,
                        line_number=line_num,
                        remediation="Create and use a non-root user in the container"
                    ))
                
                # Check for ADD instead of COPY
                if line.startswith('ADD ') and not any(url in line for url in ['HTTP://', 'HTTPS://']):
                    vulnerabilities.append(Vulnerability(
                        id=f"DOCKER-ADD-USAGE-{line_num}",
                        title="Use of ADD instead of COPY",
                        description="ADD has additional features that can be security risks. Use COPY when possible",
                        severity=SeverityLevel.MEDIUM,
                        vulnerability_type=VulnerabilityType.CONFIGURATION_ISSUE,
                        file_path=relative_path,
                        line_number=line_num,
                        remediation="Use COPY instead of ADD for local files"
                    ))
                
                # Check for latest tag usage
                if 'FROM' in line and ':LATEST' in line:
                    vulnerabilities.append(Vulnerability(
                        id=f"DOCKER-LATEST-TAG-{line_num}",
                        title="Use of 'latest' tag in base image",
                        description="Using 'latest' tag can lead to unpredictable builds and security issues",
                        severity=SeverityLevel.MEDIUM,
                        vulnerability_type=VulnerabilityType.CONFIGURATION_ISSUE,
                        file_path=relative_path,
                        line_number=line_num,
                        remediation="Use specific version tags for base images"
                    ))
        
        except Exception as e:
            logger.error(f"Error analyzing Dockerfile {dockerfile_path}: {e}")
        
        return vulnerabilities
    
    def _count_vulnerabilities_by_severity(
        self, 
        vulnerabilities: List[Vulnerability]
    ) -> Dict[SeverityLevel, int]:
        """Count vulnerabilities by severity level."""
        counts = {severity: 0 for severity in SeverityLevel}
        
        for vuln in vulnerabilities:
            counts[vuln.severity] += 1
        
        return counts
    
    def _assess_compliance(self, severity_counts: Dict[SeverityLevel, int]) -> Dict[str, bool]:
        """Assess compliance based on vulnerability counts."""
        return {
            "no_critical_vulnerabilities": severity_counts[SeverityLevel.CRITICAL] == 0,
            "acceptable_high_vulnerabilities": severity_counts[SeverityLevel.HIGH] <= 5,
            "overall_compliance": (
                severity_counts[SeverityLevel.CRITICAL] == 0 and 
                severity_counts[SeverityLevel.HIGH] <= 5
            )
        }
    
    def _requires_remediation(self, severity_counts: Dict[SeverityLevel, int]) -> bool:
        """Determine if remediation is required based on configuration."""
        if self.config.fail_on_critical and severity_counts[SeverityLevel.CRITICAL] > 0:
            return True
        
        if self.config.fail_on_high and severity_counts[SeverityLevel.HIGH] > 0:
            return True
        
        return False