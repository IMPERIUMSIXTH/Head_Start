"""
Security integration module for the AI-powered learning platform.

This module integrates the security scanning engine with the existing
application services and provides security validation for deployments.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from .security_scanner import SecurityScanner, SecurityScannerConfig, SeverityLevel
from .vulnerability_analyzer import VulnerabilityAnalyzer, RemediationPriority
from config.security_config import get_security_config, create_scanner_config

logger = logging.getLogger(__name__)


class SecurityValidationService:
    """Service for integrating security validation into the application lifecycle."""
    
    def __init__(self):
        """Initialize the security validation service."""
        self.security_config = get_security_config()
        self.scanner_config = create_scanner_config(self.security_config)
        self.scanner = SecurityScanner(self.scanner_config)
        self.analyzer = VulnerabilityAnalyzer()
        
    async def validate_deployment_security(
        self, 
        project_path: str = ".",
        environment: str = "production"
    ) -> Dict:
        """
        Validate security for deployment readiness.
        
        Args:
            project_path: Path to the project to scan
            environment: Target deployment environment
            
        Returns:
            Dict containing validation results and recommendations
        """
        logger.info(f"Starting security validation for {environment} deployment")
        
        try:
            # Run comprehensive security scan
            scan_results = await self.scanner.run_comprehensive_scan(project_path)
            
            # Analyze vulnerabilities
            analysis_report = self.analyzer.analyze_vulnerabilities(scan_results)
            
            # Determine deployment readiness
            deployment_ready = self._assess_deployment_readiness(
                scan_results, analysis_report, environment
            )
            
            # Generate deployment security report
            security_report = {
                "deployment_ready": deployment_ready,
                "scan_id": scan_results.scan_id,
                "timestamp": scan_results.timestamp.isoformat(),
                "environment": environment,
                "total_vulnerabilities": scan_results.total_vulnerabilities,
                "severity_breakdown": {
                    severity.value: count 
                    for severity, count in scan_results.severity_counts.items()
                },
                "compliance_status": scan_results.compliance_status,
                "critical_issues": self._extract_critical_issues(analysis_report),
                "immediate_actions": self._extract_immediate_actions(analysis_report),
                "security_score": self._calculate_security_score(scan_results),
                "recommendations": analysis_report.recommendations[:5],  # Top 5
                "next_scan_recommended": self._calculate_next_scan_date()
            }
            
            logger.info(f"Security validation completed. Deployment ready: {deployment_ready}")
            return security_report
            
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            return {
                "deployment_ready": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "environment": environment
            }
    
    async def continuous_security_monitoring(
        self, 
        project_path: str = ".",
        interval_hours: int = 24
    ) -> None:
        """
        Run continuous security monitoring.
        
        Args:
            project_path: Path to monitor
            interval_hours: Hours between scans
        """
        logger.info(f"Starting continuous security monitoring (interval: {interval_hours}h)")
        
        while True:
            try:
                # Run security scan
                scan_results = await self.scanner.run_comprehensive_scan(project_path)
                
                # Check for new critical vulnerabilities
                critical_count = scan_results.severity_counts.get(SeverityLevel.CRITICAL, 0)
                high_count = scan_results.severity_counts.get(SeverityLevel.HIGH, 0)
                
                if critical_count > 0:
                    await self._alert_critical_vulnerabilities(scan_results)
                
                if high_count > 10:  # Threshold for high vulnerability alerts
                    await self._alert_high_vulnerability_threshold(scan_results)
                
                # Wait for next scan
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    def _assess_deployment_readiness(
        self, 
        scan_results, 
        analysis_report, 
        environment: str
    ) -> bool:
        """Assess if the application is ready for deployment based on security scan."""
        # Production has stricter requirements
        if environment == "production":
            # No critical vulnerabilities allowed
            if scan_results.severity_counts.get(SeverityLevel.CRITICAL, 0) > 0:
                return False
            
            # Limited high vulnerabilities allowed
            if scan_results.severity_counts.get(SeverityLevel.HIGH, 0) > 2:
                return False
            
            # Must have overall compliance
            if not scan_results.compliance_status.get("overall_compliance", False):
                return False
        
        elif environment == "staging":
            # More lenient for staging
            if scan_results.severity_counts.get(SeverityLevel.CRITICAL, 0) > 2:
                return False
            
            if scan_results.severity_counts.get(SeverityLevel.HIGH, 0) > 10:
                return False
        
        else:  # development
            # Most lenient for development
            if scan_results.severity_counts.get(SeverityLevel.CRITICAL, 0) > 5:
                return False
        
        return True
    
    def _extract_critical_issues(self, analysis_report) -> List[Dict]:
        """Extract critical security issues that need immediate attention."""
        critical_issues = []
        
        for assessment in analysis_report.risk_assessments:
            if assessment.remediation_priority == RemediationPriority.IMMEDIATE:
                critical_issues.append({
                    "vulnerability_id": assessment.vulnerability_id,
                    "risk_level": assessment.risk_level.value,
                    "business_impact": assessment.business_impact,
                    "estimated_hours": assessment.estimated_remediation_hours
                })
        
        return critical_issues[:10]  # Top 10 critical issues
    
    def _extract_immediate_actions(self, analysis_report) -> List[Dict]:
        """Extract immediate actions from remediation plan."""
        immediate_actions = analysis_report.remediation_plan.get_immediate_actions()
        
        return [
            {
                "action_id": action.action_id,
                "title": action.title,
                "description": action.description,
                "estimated_hours": action.estimated_hours,
                "affected_vulnerabilities_count": len(action.affected_vulnerabilities)
            }
            for action in immediate_actions[:5]  # Top 5 immediate actions
        ]
    
    def _calculate_security_score(self, scan_results) -> int:
        """Calculate a security score from 0-100 based on vulnerabilities."""
        base_score = 100
        
        # Deduct points based on severity
        critical_penalty = scan_results.severity_counts.get(SeverityLevel.CRITICAL, 0) * 20
        high_penalty = scan_results.severity_counts.get(SeverityLevel.HIGH, 0) * 10
        medium_penalty = scan_results.severity_counts.get(SeverityLevel.MEDIUM, 0) * 5
        low_penalty = scan_results.severity_counts.get(SeverityLevel.LOW, 0) * 1
        
        total_penalty = critical_penalty + high_penalty + medium_penalty + low_penalty
        
        security_score = max(0, base_score - total_penalty)
        return security_score
    
    def _calculate_next_scan_date(self) -> str:
        """Calculate when the next security scan should be performed."""
        from datetime import timedelta
        
        # Recommend daily scans for active development
        next_scan = datetime.now() + timedelta(days=1)
        return next_scan.isoformat()
    
    async def _alert_critical_vulnerabilities(self, scan_results) -> None:
        """Send alerts for critical vulnerabilities."""
        logger.critical(f"CRITICAL SECURITY ALERT: {scan_results.severity_counts[SeverityLevel.CRITICAL]} critical vulnerabilities found in scan {scan_results.scan_id}")
        
        # In a real implementation, this would send notifications via:
        # - Email
        # - Slack
        # - PagerDuty
        # - JIRA tickets
        # - etc.
    
    async def _alert_high_vulnerability_threshold(self, scan_results) -> None:
        """Send alerts when high vulnerability threshold is exceeded."""
        high_count = scan_results.severity_counts[SeverityLevel.HIGH]
        logger.warning(f"HIGH VULNERABILITY THRESHOLD EXCEEDED: {high_count} high severity vulnerabilities found")


class SecurityMiddleware:
    """Middleware for integrating security checks into API requests."""
    
    def __init__(self, security_service: SecurityValidationService):
        """Initialize security middleware."""
        self.security_service = security_service
        self.last_scan_time = None
        self.scan_cache_duration = 3600  # 1 hour cache
    
    async def __call__(self, request, call_next):
        """Process request with security validation."""
        # Add security headers
        response = await call_next(request)
        
        # Add security headers to response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


def create_security_validation_service() -> SecurityValidationService:
    """Factory function to create security validation service."""
    return SecurityValidationService()


async def run_deployment_security_check(
    project_path: str = ".",
    environment: str = "production"
) -> bool:
    """
    Convenience function to run deployment security check.
    
    Returns:
        bool: True if deployment is approved, False otherwise
    """
    service = create_security_validation_service()
    result = await service.validate_deployment_security(project_path, environment)
    return result.get("deployment_ready", False)


# Integration with existing services
def integrate_with_auth_service():
    """Integrate security scanning with authentication service."""
    # This would add security validation to auth flows
    pass


def integrate_with_content_processing():
    """Integrate security scanning with content processing."""
    # This would add security validation to content uploads
    pass


def integrate_with_recommendations():
    """Integrate security scanning with recommendation service."""
    # This would add security considerations to recommendations
    pass