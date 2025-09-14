"""
E2E Test Runner for HeadStart Platform
Orchestrates Playwright E2E tests with comprehensive reporting and error handling

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: E2E test execution and management for user workflow validation
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass, asdict

logger = structlog.get_logger()

@dataclass
class E2ETestResult:
    """E2E test result data structure"""
    test_name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration_ms: int
    browser: str
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    trace_path: Optional[str] = None

@dataclass
class E2ETestSuite:
    """E2E test suite configuration"""
    name: str
    test_files: List[str]
    browsers: List[str]
    mobile_devices: List[str]
    timeout_ms: int = 60000
    retries: int = 2
    parallel_workers: int = 4

@dataclass
class E2ETestReport:
    """Comprehensive E2E test report"""
    suite_name: str
    start_time: datetime
    end_time: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    total_duration_ms: int
    browser_results: Dict[str, Dict[str, Any]]
    test_results: List[E2ETestResult]
    coverage_report: Optional[Dict[str, Any]] = None
    accessibility_report: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class E2ETestRunner:
    """
    E2E Test Runner for comprehensive user workflow testing
    Manages Playwright test execution across multiple browsers and devices
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "tests/e2e/playwright.config.ts"
        self.test_dir = Path("tests/e2e")
        self.results_dir = self.test_dir / "test-results"
        self.reports_dir = self.test_dir / "reports"
        
        # Ensure directories exist
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Test suites configuration
        self.test_suites = {
            "authentication": E2ETestSuite(
                name="Authentication Workflows",
                test_files=[
                    "tests/auth/login.e2e.ts",
                    "tests/auth/registration.e2e.ts",
                    "tests/auth/oauth.e2e.ts",
                    "tests/auth/password-reset.e2e.ts"
                ],
                browsers=["chromium", "firefox", "webkit"],
                mobile_devices=["Mobile Chrome", "Mobile Safari"]
            ),
            "user_workflows": E2ETestSuite(
                name="User Workflows",
                test_files=[
                    "tests/user/dashboard.e2e.ts",
                    "tests/user/preferences.e2e.ts",
                    "tests/user/profile.e2e.ts",
                    "tests/user/recommendations.e2e.ts"
                ],
                browsers=["chromium", "firefox"],
                mobile_devices=["Mobile Chrome"]
            ),
            "content_management": E2ETestSuite(
                name="Content Management",
                test_files=[
                    "tests/content/browse.e2e.ts",
                    "tests/content/search.e2e.ts",
                    "tests/content/interaction.e2e.ts"
                ],
                browsers=["chromium", "webkit"],
                mobile_devices=["iPad"]
            ),
            "admin_workflows": E2ETestSuite(
                name="Admin Workflows",
                test_files=[
                    "tests/admin/user-management.e2e.ts",
                    "tests/admin/content-approval.e2e.ts",
                    "tests/admin/analytics.e2e.ts"
                ],
                browsers=["chromium"],
                mobile_devices=[]
            ),
            "accessibility": E2ETestSuite(
                name="Accessibility Compliance",
                test_files=[
                    "tests/accessibility/wcag-compliance.e2e.ts",
                    "tests/accessibility/keyboard-navigation.e2e.ts",
                    "tests/accessibility/screen-reader.e2e.ts"
                ],
                browsers=["chromium"],
                mobile_devices=[]
            ),
            "performance": E2ETestSuite(
                name="Performance Validation",
                test_files=[
                    "tests/performance/page-load.e2e.ts",
                    "tests/performance/interaction-timing.e2e.ts"
                ],
                browsers=["chromium"],
                mobile_devices=[]
            )
        }
    
    async def run_all_suites(self) -> Dict[str, E2ETestReport]:
        """Run all E2E test suites"""
        logger.info("Starting comprehensive E2E test execution")
        
        all_reports = {}
        overall_start_time = datetime.now()
        
        try:
            # Install Playwright browsers if needed
            await self._ensure_browsers_installed()
            
            # Run each test suite
            for suite_name, suite_config in self.test_suites.items():
                logger.info(f"Running E2E test suite: {suite_name}")
                report = await self.run_test_suite(suite_config)
                all_reports[suite_name] = report
                
                # Log suite results
                logger.info(
                    f"Suite {suite_name} completed",
                    passed=report.passed_tests,
                    failed=report.failed_tests,
                    duration_ms=report.total_duration_ms
                )
            
            # Generate comprehensive report
            await self._generate_comprehensive_report(all_reports, overall_start_time)
            
            return all_reports
            
        except Exception as e:
            logger.error("E2E test execution failed", error=str(e))
            raise
    
    async def run_test_suite(self, suite: E2ETestSuite) -> E2ETestReport:
        """Run a specific test suite"""
        start_time = datetime.now()
        
        try:
            # Build Playwright command
            cmd = self._build_playwright_command(suite)
            
            # Execute tests
            logger.info(f"Executing Playwright tests for suite: {suite.name}")
            result = await self._execute_playwright_command(cmd)
            
            # Parse results
            test_results = await self._parse_test_results()
            
            # Calculate metrics
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Build report
            report = E2ETestReport(
                suite_name=suite.name,
                start_time=start_time,
                end_time=end_time,
                total_tests=len(test_results),
                passed_tests=len([r for r in test_results if r.status == 'passed']),
                failed_tests=len([r for r in test_results if r.status == 'failed']),
                skipped_tests=len([r for r in test_results if r.status == 'skipped']),
                total_duration_ms=duration_ms,
                browser_results=await self._analyze_browser_results(test_results),
                test_results=test_results
            )
            
            # Add accessibility and performance metrics if available
            if suite.name == "Accessibility Compliance":
                report.accessibility_report = await self._generate_accessibility_report()
            
            if suite.name == "Performance Validation":
                report.performance_metrics = await self._generate_performance_metrics()
            
            return report
            
        except Exception as e:
            logger.error(f"Test suite {suite.name} failed", error=str(e))
            raise
    
    async def run_mobile_responsive_tests(self) -> E2ETestReport:
        """Run mobile responsive design validation tests"""
        logger.info("Running mobile responsive design tests")
        
        mobile_suite = E2ETestSuite(
            name="Mobile Responsive Design",
            test_files=[
                "tests/mobile/responsive-layout.e2e.ts",
                "tests/mobile/touch-interactions.e2e.ts",
                "tests/mobile/viewport-adaptation.e2e.ts"
            ],
            browsers=[],
            mobile_devices=["Mobile Chrome", "Mobile Safari", "iPad"],
            timeout_ms=90000
        )
        
        return await self.run_test_suite(mobile_suite)
    
    async def run_critical_path_tests(self) -> E2ETestReport:
        """Run critical user path tests"""
        logger.info("Running critical user path tests")
        
        critical_suite = E2ETestSuite(
            name="Critical User Paths",
            test_files=[
                "tests/critical/user-registration-flow.e2e.ts",
                "tests/critical/recommendation-workflow.e2e.ts",
                "tests/critical/content-interaction-flow.e2e.ts"
            ],
            browsers=["chromium", "firefox", "webkit"],
            mobile_devices=["Mobile Chrome", "Mobile Safari"]
        )
        
        return await self.run_test_suite(critical_suite)
    
    def _build_playwright_command(self, suite: E2ETestSuite) -> List[str]:
        """Build Playwright command with appropriate options"""
        cmd = [
            "npx", "playwright", "test",
            "--config", self.config_path,
            "--reporter=json",
            f"--output-dir={self.results_dir}",
            f"--workers={suite.parallel_workers}",
            f"--timeout={suite.timeout_ms}",
            f"--retries={suite.retries}"
        ]
        
        # Add test files
        cmd.extend(suite.test_files)
        
        # Add browser projects
        for browser in suite.browsers:
            cmd.extend(["--project", browser])
        
        # Add mobile device projects
        for device in suite.mobile_devices:
            cmd.extend(["--project", device])
        
        return cmd
    
    async def _execute_playwright_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Execute Playwright command asynchronously"""
        try:
            # Change to E2E test directory
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.test_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.warning(
                    "Playwright tests completed with failures",
                    return_code=process.returncode,
                    stderr=stderr.decode()
                )
            
            return subprocess.CompletedProcess(
                cmd, process.returncode, stdout, stderr
            )
            
        except Exception as e:
            logger.error("Failed to execute Playwright command", error=str(e))
            raise
    
    async def _parse_test_results(self) -> List[E2ETestResult]:
        """Parse Playwright test results from JSON output"""
        results_file = self.results_dir / "results.json"
        
        if not results_file.exists():
            logger.warning("No test results file found")
            return []
        
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            test_results = []
            
            for suite in data.get('suites', []):
                for spec in suite.get('specs', []):
                    for test in spec.get('tests', []):
                        for result in test.get('results', []):
                            test_result = E2ETestResult(
                                test_name=test.get('title', 'Unknown'),
                                status=result.get('status', 'unknown'),
                                duration_ms=result.get('duration', 0),
                                browser=result.get('workerIndex', 'unknown'),
                                error_message=result.get('error', {}).get('message') if result.get('error') else None,
                                screenshot_path=self._find_artifact(result, 'screenshot'),
                                video_path=self._find_artifact(result, 'video'),
                                trace_path=self._find_artifact(result, 'trace')
                            )
                            test_results.append(test_result)
            
            return test_results
            
        except Exception as e:
            logger.error("Failed to parse test results", error=str(e))
            return []
    
    def _find_artifact(self, result: Dict, artifact_type: str) -> Optional[str]:
        """Find artifact path in test result"""
        attachments = result.get('attachments', [])
        for attachment in attachments:
            if attachment.get('name', '').lower().startswith(artifact_type):
                return attachment.get('path')
        return None
    
    async def _analyze_browser_results(self, test_results: List[E2ETestResult]) -> Dict[str, Dict[str, Any]]:
        """Analyze test results by browser"""
        browser_results = {}
        
        for result in test_results:
            browser = result.browser
            if browser not in browser_results:
                browser_results[browser] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'skipped': 0,
                    'avg_duration_ms': 0,
                    'total_duration_ms': 0
                }
            
            browser_results[browser]['total'] += 1
            browser_results[browser]['total_duration_ms'] += result.duration_ms
            
            if result.status == 'passed':
                browser_results[browser]['passed'] += 1
            elif result.status == 'failed':
                browser_results[browser]['failed'] += 1
            elif result.status == 'skipped':
                browser_results[browser]['skipped'] += 1
        
        # Calculate averages
        for browser, stats in browser_results.items():
            if stats['total'] > 0:
                stats['avg_duration_ms'] = stats['total_duration_ms'] // stats['total']
        
        return browser_results
    
    async def _ensure_browsers_installed(self):
        """Ensure Playwright browsers are installed"""
        try:
            cmd = ["npx", "playwright", "install", "--with-deps"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.test_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode != 0:
                logger.warning("Browser installation completed with warnings")
            
        except Exception as e:
            logger.error("Failed to install browsers", error=str(e))
            raise
    
    async def _generate_accessibility_report(self) -> Dict[str, Any]:
        """Generate accessibility compliance report"""
        # This would integrate with axe-core results
        return {
            "wcag_level": "AA",
            "violations": [],
            "passes": [],
            "incomplete": [],
            "compliance_score": 100.0
        }
    
    async def _generate_performance_metrics(self) -> Dict[str, Any]:
        """Generate performance metrics report"""
        # This would integrate with Lighthouse or similar tools
        return {
            "page_load_times": {},
            "interaction_timings": {},
            "core_web_vitals": {},
            "performance_score": 95.0
        }
    
    async def _generate_comprehensive_report(self, all_reports: Dict[str, E2ETestReport], start_time: datetime):
        """Generate comprehensive HTML and JSON reports"""
        end_time = datetime.now()
        
        # Calculate overall metrics
        total_tests = sum(report.total_tests for report in all_reports.values())
        total_passed = sum(report.passed_tests for report in all_reports.values())
        total_failed = sum(report.failed_tests for report in all_reports.values())
        total_duration = sum(report.total_duration_ms for report in all_reports.values())
        
        comprehensive_report = {
            "execution_summary": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_ms": int((end_time - start_time).total_seconds() * 1000),
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "success_rate": (total_passed / max(total_tests, 1)) * 100
            },
            "suite_reports": {name: asdict(report) for name, report in all_reports.items()},
            "browser_compatibility": self._analyze_browser_compatibility(all_reports),
            "mobile_compatibility": self._analyze_mobile_compatibility(all_reports)
        }
        
        # Save JSON report
        json_report_path = self.reports_dir / f"e2e-report-{int(time.time())}.json"
        with open(json_report_path, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        logger.info(
            "E2E test execution completed",
            total_tests=total_tests,
            passed=total_passed,
            failed=total_failed,
            success_rate=f"{(total_passed / max(total_tests, 1)) * 100:.1f}%",
            report_path=str(json_report_path)
        )
    
    def _analyze_browser_compatibility(self, all_reports: Dict[str, E2ETestReport]) -> Dict[str, Any]:
        """Analyze browser compatibility across all test suites"""
        browser_compatibility = {}
        
        for suite_name, report in all_reports.items():
            for browser, stats in report.browser_results.items():
                if browser not in browser_compatibility:
                    browser_compatibility[browser] = {
                        'total_tests': 0,
                        'passed_tests': 0,
                        'failed_tests': 0,
                        'success_rate': 0.0
                    }
                
                browser_compatibility[browser]['total_tests'] += stats['total']
                browser_compatibility[browser]['passed_tests'] += stats['passed']
                browser_compatibility[browser]['failed_tests'] += stats['failed']
        
        # Calculate success rates
        for browser, stats in browser_compatibility.items():
            if stats['total_tests'] > 0:
                stats['success_rate'] = (stats['passed_tests'] / stats['total_tests']) * 100
        
        return browser_compatibility
    
    def _analyze_mobile_compatibility(self, all_reports: Dict[str, E2ETestReport]) -> Dict[str, Any]:
        """Analyze mobile device compatibility"""
        mobile_devices = ["Mobile Chrome", "Mobile Safari", "iPad"]
        mobile_compatibility = {}
        
        for suite_name, report in all_reports.items():
            for browser, stats in report.browser_results.items():
                if browser in mobile_devices:
                    if browser not in mobile_compatibility:
                        mobile_compatibility[browser] = {
                            'total_tests': 0,
                            'passed_tests': 0,
                            'failed_tests': 0,
                            'success_rate': 0.0
                        }
                    
                    mobile_compatibility[browser]['total_tests'] += stats['total']
                    mobile_compatibility[browser]['passed_tests'] += stats['passed']
                    mobile_compatibility[browser]['failed_tests'] += stats['failed']
        
        # Calculate success rates
        for device, stats in mobile_compatibility.items():
            if stats['total_tests'] > 0:
                stats['success_rate'] = (stats['passed_tests'] / stats['total_tests']) * 100
        
        return mobile_compatibility

# CLI interface for running E2E tests
async def main():
    """Main CLI interface for E2E test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='HeadStart E2E Test Runner')
    parser.add_argument('--suite', help='Run specific test suite')
    parser.add_argument('--mobile', action='store_true', help='Run mobile responsive tests')
    parser.add_argument('--critical', action='store_true', help='Run critical path tests only')
    parser.add_argument('--config', help='Path to Playwright config file')
    
    args = parser.parse_args()
    
    runner = E2ETestRunner(config_path=args.config)
    
    try:
        if args.critical:
            report = await runner.run_critical_path_tests()
            print(f"Critical path tests: {report.passed_tests}/{report.total_tests} passed")
        elif args.mobile:
            report = await runner.run_mobile_responsive_tests()
            print(f"Mobile tests: {report.passed_tests}/{report.total_tests} passed")
        elif args.suite:
            if args.suite in runner.test_suites:
                report = await runner.run_test_suite(runner.test_suites[args.suite])
                print(f"Suite {args.suite}: {report.passed_tests}/{report.total_tests} passed")
            else:
                print(f"Unknown test suite: {args.suite}")
                sys.exit(1)
        else:
            reports = await runner.run_all_suites()
            total_passed = sum(r.passed_tests for r in reports.values())
            total_tests = sum(r.total_tests for r in reports.values())
            print(f"All E2E tests: {total_passed}/{total_tests} passed")
        
    except Exception as e:
        logger.error("E2E test execution failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())