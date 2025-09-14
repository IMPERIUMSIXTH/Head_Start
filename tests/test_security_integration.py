"""
Integration tests for the security scanning system.

These tests verify that all components work together correctly.
"""

import tempfile
from pathlib import Path

import pytest

from services.security_integration import create_security_validation_service


class TestSecurityIntegration:
    """Integration tests for security validation service."""
    
    @pytest.fixture
    def security_service(self):
        """Create security validation service."""
        return create_security_validation_service()
    
    @pytest.mark.asyncio
    async def test_deployment_validation_service(self, security_service):
        """Test deployment validation service integration."""
        # Create a temporary project with some test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = {
                "app.py": """
# Simple test application
def hello_world():
    return "Hello, World!"
""",
                "requirements.txt": "fastapi==0.104.1\nuvicorn==0.24.0"
            }
            
            for filename, content in test_files.items():
                file_path = Path(temp_dir) / filename
                file_path.write_text(content)
            
            # Run deployment validation
            result = await security_service.validate_deployment_security(
                project_path=temp_dir,
                environment="development"
            )
            
            # Verify result structure
            assert "deployment_ready" in result
            assert "scan_id" in result
            assert "timestamp" in result
            assert "environment" in result
            assert "total_vulnerabilities" in result
            assert "severity_breakdown" in result
            assert "security_score" in result
            
            # Should be ready for development environment
            assert result["environment"] == "development"
            assert isinstance(result["deployment_ready"], bool)
            assert isinstance(result["security_score"], int)
            assert 0 <= result["security_score"] <= 100
    
    @pytest.mark.asyncio
    async def test_security_service_error_handling(self, security_service):
        """Test error handling in security service."""
        # Test with non-existent path
        result = await security_service.validate_deployment_security(
            project_path="/non/existent/path",
            environment="production"
        )
        
        # Should handle gracefully
        assert "deployment_ready" in result
        assert "timestamp" in result
        assert "environment" in result
    
    def test_security_service_creation(self):
        """Test security service factory function."""
        service = create_security_validation_service()
        
        assert service is not None
        assert hasattr(service, 'security_config')
        assert hasattr(service, 'scanner')
        assert hasattr(service, 'analyzer')
    
    @pytest.mark.asyncio
    async def test_security_score_calculation(self, security_service):
        """Test security score calculation logic."""
        # This tests the internal scoring logic
        from services.security_scanner import SecurityScanResults, SeverityLevel
        from datetime import datetime
        
        # Create mock scan results with known vulnerabilities
        scan_results = SecurityScanResults(
            scan_id="test_scan",
            timestamp=datetime.now(),
            total_vulnerabilities=5,
            severity_counts={
                SeverityLevel.CRITICAL: 1,
                SeverityLevel.HIGH: 2,
                SeverityLevel.MEDIUM: 2,
                SeverityLevel.LOW: 0,
                SeverityLevel.INFO: 0
            },
            scan_results=[],
            compliance_status={"overall_compliance": False},
            remediation_required=True,
            scan_tools_used=["TestTool"]
        )
        
        # Calculate security score
        score = security_service._calculate_security_score(scan_results)
        
        # Should be reduced due to vulnerabilities
        # 1 critical (20 points) + 2 high (20 points) + 2 medium (10 points) = 50 points deducted
        expected_score = 100 - 50
        assert score == expected_score
    
    @pytest.mark.asyncio
    async def test_deployment_readiness_assessment(self, security_service):
        """Test deployment readiness assessment for different environments."""
        from services.security_scanner import SecurityScanResults, SeverityLevel
        from services.vulnerability_analyzer import AnalysisReport, RemediationPlan
        from datetime import datetime
        
        # Create scan results with critical vulnerabilities
        critical_scan = SecurityScanResults(
            scan_id="critical_test",
            timestamp=datetime.now(),
            total_vulnerabilities=1,
            severity_counts={
                SeverityLevel.CRITICAL: 1,
                SeverityLevel.HIGH: 0,
                SeverityLevel.MEDIUM: 0,
                SeverityLevel.LOW: 0,
                SeverityLevel.INFO: 0
            },
            scan_results=[],
            compliance_status={"overall_compliance": False},
            remediation_required=True,
            scan_tools_used=["TestTool"]
        )
        
        # Mock analysis report
        mock_plan = RemediationPlan(
            plan_id="test_plan",
            created_at=datetime.now(),
            total_vulnerabilities=1,
            critical_count=1,
            high_count=0,
            estimated_total_hours=4,
            actions=[],
            timeline_weeks=1,
            success_criteria=[]
        )
        
        mock_analysis = type('MockAnalysis', (), {
            'remediation_plan': mock_plan,
            'risk_assessments': []
        })()
        
        # Test different environments
        # Production should reject critical vulnerabilities
        prod_ready = security_service._assess_deployment_readiness(
            critical_scan, mock_analysis, "production"
        )
        assert prod_ready is False
        
        # Development should be more lenient
        dev_ready = security_service._assess_deployment_readiness(
            critical_scan, mock_analysis, "development"
        )
        # Should still be False for critical, but more lenient threshold
        assert isinstance(dev_ready, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])