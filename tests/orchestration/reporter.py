"""
Test reporting functionality for generating comprehensive test reports.

This module provides the TestReporter class that generates various types of
reports including HTML, JSON, and markdown reports for test results.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from jinja2 import Template

from .models import TestContext, TestResults, TestStatus

logger = logging.getLogger(__name__)


class TestReporter:
    """
    Generates comprehensive test reports in multiple formats.
    
    This class handles the generation of HTML, JSON, and markdown reports
    for test results, including summary reports and detailed breakdowns.
    """
    
    def __init__(self, context: TestContext):
        self.context = context
        self.report_dir = context.test_config.report_output_dir
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
    async def generate_all_reports(self, results: TestResults) -> Dict[str, str]:
        """
        Generate all configured report types.
        
        Args:
            results: Test results to generate reports for
            
        Returns:
            Dict[str, str]: Dictionary mapping report types to file paths
        """
        report_paths = {}
        
        try:
            # Generate JSON report
            if self.context.test_config.generate_json_reports:
                json_path = await self.generate_json_report(results)
                report_paths["json"] = str(json_path)
            
            # Generate HTML report
            if self.context.test_config.generate_html_reports:
                html_path = await self.generate_html_report(results)
                report_paths["html"] = str(html_path)
            
            # Generate markdown summary
            markdown_path = await self.generate_markdown_summary(results)
            report_paths["markdown"] = str(markdown_path)
            
            # Generate quality gate report
            quality_gate_path = await self.generate_quality_gate_report(results)
            report_paths["quality_gates"] = str(quality_gate_path)
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            
        return report_paths
    
    async def generate_json_report(self, results: TestResults) -> Path:
        """
        Generate a comprehensive JSON report.
        
        Args:
            results: Test results to include in the report
            
        Returns:
            Path: Path to the generated JSON report file
        """
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "branch": self.context.branch,
                "commit_sha": self.context.commit_sha,
                "environment": self.context.environment,
                "triggered_by": self.context.triggered_by
            },
            "summary": {
                "overall_status": results.overall_status.value,
                "quality_gate_passed": results.quality_gate_passed,
                "total_execution_time": results.total_execution_time,
                "execution_start_time": results.execution_start_time.isoformat() if results.execution_start_time else None,
                "execution_end_time": results.execution_end_time.isoformat() if results.execution_end_time else None
            },
            "test_results": {
                "unit_tests": {
                    "status": results.unit_tests.status.value,
                    "total_tests": results.unit_tests.total_tests,
                    "passed_tests": results.unit_tests.passed_tests,
                    "failed_tests": results.unit_tests.failed_tests,
                    "skipped_tests": results.unit_tests.skipped_tests,
                    "coverage_percentage": results.unit_tests.coverage_percentage,
                    "execution_time": results.unit_tests.execution_time
                },
                "integration_tests": {
                    "status": results.integration_tests.status.value,
                    "total_tests": results.integration_tests.total_tests,
                    "passed_tests": results.integration_tests.passed_tests,
                    "failed_tests": results.integration_tests.failed_tests,
                    "execution_time": results.integration_tests.execution_time,
                    "database_tests": results.integration_tests.database_tests,
                    "api_tests": results.integration_tests.api_tests,
                    "service_tests": results.integration_tests.service_tests
                },
                "e2e_tests": {
                    "status": results.e2e_tests.status.value,
                    "total_tests": results.e2e_tests.total_tests,
                    "passed_tests": results.e2e_tests.passed_tests,
                    "failed_tests": results.e2e_tests.failed_tests,
                    "execution_time": results.e2e_tests.execution_time,
                    "browser_tests": results.e2e_tests.browser_tests,
                    "user_journey_tests": results.e2e_tests.user_journey_tests
                },
                "security_scan": {
                    "status": results.security_scan.status.value,
                    "vulnerability_count": len(results.security_scan.vulnerabilities),
                    "severity_counts": results.security_scan.severity_counts,
                    "scan_tools_used": results.security_scan.scan_tools_used,
                    "compliance_status": results.security_scan.compliance_status,
                    "remediation_required": results.security_scan.remediation_required,
                    "execution_time": results.security_scan.execution_time
                },
                "accessibility_test": {
                    "status": results.accessibility_test.status.value,
                    "total_violations": results.accessibility_test.total_violations,
                    "critical_violations": results.accessibility_test.critical_violations,
                    "serious_violations": results.accessibility_test.serious_violations,
                    "wcag_level": results.accessibility_test.wcag_level,
                    "pages_tested": results.accessibility_test.pages_tested,
                    "execution_time": results.accessibility_test.execution_time
                },
                "performance_test": {
                    "status": results.performance_test.status.value,
                    "response_time_p50": results.performance_test.response_time_p50,
                    "response_time_p95": results.performance_test.response_time_p95,
                    "response_time_p99": results.performance_test.response_time_p99,
                    "throughput_rps": results.performance_test.throughput_rps,
                    "error_rate": results.performance_test.error_rate,
                    "resource_utilization": results.performance_test.resource_utilization,
                    "execution_time": results.performance_test.execution_time
                }
            }
        }
        
        report_path = self.report_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Generated JSON report: {report_path}")
        return report_path
    
    async def generate_html_report(self, results: TestResults) -> Path:
        """
        Generate an HTML report with visual charts and detailed breakdown.
        
        Args:
            results: Test results to include in the report
            
        Returns:
            Path: Path to the generated HTML report file
        """
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Results Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .status-badge { padding: 5px 15px; border-radius: 20px; color: white; font-weight: bold; }
        .status-passed { background-color: #28a745; }
        .status-failed { background-color: #dc3545; }
        .status-error { background-color: #ffc107; color: black; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }
        .test-section { margin-bottom: 30px; }
        .test-section h3 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .metrics { display: flex; justify-content: space-between; flex-wrap: wrap; }
        .metric { text-align: center; padding: 10px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .metric-label { font-size: 12px; color: #666; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Results Report</h1>
            <div class="status-badge status-{{ overall_status }}">{{ overall_status.upper() }}</div>
            <p>Generated on {{ generated_at }} | Branch: {{ branch }} | Commit: {{ commit_sha[:8] }}</p>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h4>Execution Summary</h4>
                <p><strong>Total Time:</strong> {{ "%.2f"|format(total_execution_time) }}s</p>
                <p><strong>Quality Gates:</strong> {{ "PASSED" if quality_gate_passed else "FAILED" }}</p>
                <p><strong>Environment:</strong> {{ environment }}</p>
            </div>
            
            <div class="summary-card">
                <h4>Unit Tests</h4>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{{ unit_tests.passed_tests }}</div>
                        <div class="metric-label">Passed</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{{ unit_tests.failed_tests }}</div>
                        <div class="metric-label">Failed</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{{ "%.1f"|format(unit_tests.coverage_percentage) }}%</div>
                        <div class="metric-label">Coverage</div>
                    </div>
                </div>
            </div>
            
            <div class="summary-card">
                <h4>Security Scan</h4>
                <p><strong>Status:</strong> {{ security_scan.status.value.upper() }}</p>
                <p><strong>Vulnerabilities:</strong> {{ security_scan.vulnerabilities|length }}</p>
                <p><strong>Tools Used:</strong> {{ security_scan.scan_tools_used|join(", ") }}</p>
            </div>
        </div>
        
        <div class="test-section">
            <h3>Detailed Results</h3>
            <table>
                <thead>
                    <tr>
                        <th>Test Type</th>
                        <th>Status</th>
                        <th>Total Tests</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Execution Time</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Unit Tests</td>
                        <td><span class="status-badge status-{{ unit_tests.status.value }}">{{ unit_tests.status.value.upper() }}</span></td>
                        <td>{{ unit_tests.total_tests }}</td>
                        <td>{{ unit_tests.passed_tests }}</td>
                        <td>{{ unit_tests.failed_tests }}</td>
                        <td>{{ "%.2f"|format(unit_tests.execution_time) }}s</td>
                    </tr>
                    <tr>
                        <td>Integration Tests</td>
                        <td><span class="status-badge status-{{ integration_tests.status.value }}">{{ integration_tests.status.value.upper() }}</span></td>
                        <td>{{ integration_tests.total_tests }}</td>
                        <td>{{ integration_tests.passed_tests }}</td>
                        <td>{{ integration_tests.failed_tests }}</td>
                        <td>{{ "%.2f"|format(integration_tests.execution_time) }}s</td>
                    </tr>
                    <tr>
                        <td>E2E Tests</td>
                        <td><span class="status-badge status-{{ e2e_tests.status.value }}">{{ e2e_tests.status.value.upper() }}</span></td>
                        <td>{{ e2e_tests.total_tests }}</td>
                        <td>{{ e2e_tests.passed_tests }}</td>
                        <td>{{ e2e_tests.failed_tests }}</td>
                        <td>{{ "%.2f"|format(e2e_tests.execution_time) }}s</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Report generated by Test Orchestration Framework</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            overall_status=results.overall_status.value,
            quality_gate_passed=results.quality_gate_passed,
            total_execution_time=results.total_execution_time,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            branch=self.context.branch,
            commit_sha=self.context.commit_sha,
            environment=self.context.environment,
            unit_tests=results.unit_tests,
            integration_tests=results.integration_tests,
            e2e_tests=results.e2e_tests,
            security_scan=results.security_scan,
            accessibility_test=results.accessibility_test,
            performance_test=results.performance_test
        )
        
        report_path = self.report_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML report: {report_path}")
        return report_path
    
    async def generate_markdown_summary(self, results: TestResults) -> Path:
        """
        Generate a markdown summary report.
        
        Args:
            results: Test results to include in the summary
            
        Returns:
            Path: Path to the generated markdown summary file
        """
        status_emoji = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌", 
            TestStatus.ERROR: "⚠️",
            TestStatus.NOT_STARTED: "⏸️",
            TestStatus.IN_PROGRESS: "🔄",
            TestStatus.SKIPPED: "⏭️"
        }
        
        markdown_content = f"""# Test Results Summary

**Overall Status:** {status_emoji.get(results.overall_status, '❓')} {results.overall_status.value.upper()}
**Quality Gates:** {'✅ PASSED' if results.quality_gate_passed else '❌ FAILED'}
**Execution Time:** {results.total_execution_time:.2f}s
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Context
- **Branch:** {self.context.branch}
- **Commit:** {self.context.commit_sha}
- **Environment:** {self.context.environment}
- **Triggered By:** {self.context.triggered_by}

## Test Results

### Unit Tests {status_emoji.get(results.unit_tests.status, '❓')}
- **Total Tests:** {results.unit_tests.total_tests}
- **Passed:** {results.unit_tests.passed_tests}
- **Failed:** {results.unit_tests.failed_tests}
- **Coverage:** {results.unit_tests.coverage_percentage:.1f}%
- **Execution Time:** {results.unit_tests.execution_time:.2f}s

### Integration Tests {status_emoji.get(results.integration_tests.status, '❓')}
- **Total Tests:** {results.integration_tests.total_tests}
- **Passed:** {results.integration_tests.passed_tests}
- **Failed:** {results.integration_tests.failed_tests}
- **Database Tests:** {results.integration_tests.database_tests}
- **API Tests:** {results.integration_tests.api_tests}
- **Service Tests:** {results.integration_tests.service_tests}
- **Execution Time:** {results.integration_tests.execution_time:.2f}s

### End-to-End Tests {status_emoji.get(results.e2e_tests.status, '❓')}
- **Total Tests:** {results.e2e_tests.total_tests}
- **Passed:** {results.e2e_tests.passed_tests}
- **Failed:** {results.e2e_tests.failed_tests}
- **User Journey Tests:** {results.e2e_tests.user_journey_tests}
- **Browser Tests:** {dict(results.e2e_tests.browser_tests)}
- **Execution Time:** {results.e2e_tests.execution_time:.2f}s

### Security Scan {status_emoji.get(results.security_scan.status, '❓')}
- **Vulnerabilities Found:** {len(results.security_scan.vulnerabilities)}
- **Severity Breakdown:** {dict(results.security_scan.severity_counts)}
- **Compliance Status:** {results.security_scan.compliance_status}
- **Remediation Required:** {'Yes' if results.security_scan.remediation_required else 'No'}
- **Tools Used:** {', '.join(results.security_scan.scan_tools_used)}
- **Execution Time:** {results.security_scan.execution_time:.2f}s

### Accessibility Test {status_emoji.get(results.accessibility_test.status, '❓')}
- **Total Violations:** {results.accessibility_test.total_violations}
- **Critical Violations:** {results.accessibility_test.critical_violations}
- **Serious Violations:** {results.accessibility_test.serious_violations}
- **WCAG Level:** {results.accessibility_test.wcag_level}
- **Pages Tested:** {len(results.accessibility_test.pages_tested)}
- **Execution Time:** {results.accessibility_test.execution_time:.2f}s

### Performance Test {status_emoji.get(results.performance_test.status, '❓')}
- **Response Time P50:** {results.performance_test.response_time_p50:.1f}ms
- **Response Time P95:** {results.performance_test.response_time_p95:.1f}ms
- **Response Time P99:** {results.performance_test.response_time_p99:.1f}ms
- **Throughput:** {results.performance_test.throughput_rps:.1f} RPS
- **Error Rate:** {results.performance_test.error_rate:.2f}%
- **Resource Utilization:** {dict(results.performance_test.resource_utilization)}
- **Execution Time:** {results.performance_test.execution_time:.2f}s

---
*Report generated by Test Orchestration Framework*
"""
        
        report_path = self.report_dir / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, 'w') as f:
            f.write(markdown_content)
        
        logger.info(f"Generated markdown summary: {report_path}")
        return report_path
    
    async def generate_quality_gate_report(self, results: TestResults) -> Path:
        """
        Generate a detailed quality gate report.
        
        Args:
            results: Test results to analyze for quality gates
            
        Returns:
            Path: Path to the generated quality gate report file
        """
        report_content = f"""# Quality Gate Report

**Overall Status:** {'✅ PASSED' if results.quality_gate_passed else '❌ FAILED'}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Quality Gate Thresholds

| Gate | Threshold | Actual | Status |
|------|-----------|--------|--------|
| Unit Test Coverage | ≥{self.context.test_config.min_unit_test_coverage}% | {results.unit_tests.coverage_percentage:.1f}% | {'✅' if results.unit_tests.coverage_percentage >= self.context.test_config.min_unit_test_coverage else '❌'} |
| Critical Vulnerabilities | ≤{self.context.test_config.max_critical_vulnerabilities} | {results.security_scan.severity_counts.get('critical', 0)} | {'✅' if results.security_scan.severity_counts.get('critical', 0) <= self.context.test_config.max_critical_vulnerabilities else '❌'} |
| High Vulnerabilities | ≤{self.context.test_config.max_high_vulnerabilities} | {results.security_scan.severity_counts.get('high', 0)} | {'✅' if results.security_scan.severity_counts.get('high', 0) <= self.context.test_config.max_high_vulnerabilities else '❌'} |
| Accessibility Violations | ≤{self.context.test_config.max_accessibility_violations} | {results.accessibility_test.critical_violations} | {'✅' if results.accessibility_test.critical_violations <= self.context.test_config.max_accessibility_violations else '❌'} |

## Recommendations

"""
        
        # Add recommendations based on results
        if results.unit_tests.coverage_percentage < self.context.test_config.min_unit_test_coverage:
            report_content += "- 🔴 **Unit Test Coverage:** Increase test coverage to meet the minimum threshold\n"
        
        if results.security_scan.severity_counts.get('critical', 0) > 0:
            report_content += "- 🔴 **Critical Security Issues:** Address all critical vulnerabilities before deployment\n"
        
        if results.accessibility_test.critical_violations > 0:
            report_content += "- 🔴 **Accessibility Issues:** Fix critical accessibility violations for WCAG compliance\n"
        
        if results.quality_gate_passed:
            report_content += "- ✅ **All Quality Gates Passed:** Ready for deployment\n"
        
        report_path = self.report_dir / f"quality_gates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Generated quality gate report: {report_path}")
        return report_path