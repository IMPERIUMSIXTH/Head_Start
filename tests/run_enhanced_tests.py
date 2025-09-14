"""
Enhanced test runner with advanced capabilities
Demonstrates running tests with various configurations and reporting

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Enhanced test execution with comprehensive reporting
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class EnhancedTestRunner:
    """Enhanced test runner with multiple execution modes"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.test_dir = self.base_dir / "tests"
        self.reports_dir = self.base_dir / "test_reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_unit_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run unit tests with enhanced reporting"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "unit",
            "--cov=services",
            "--cov=api",
            "--cov-report=html:htmlcov",
            "--cov-report=json:coverage.json",
            "--json-report",
            f"--json-report-file={self.reports_dir}/unit_test_report.json",
            "--html=test_reports/unit_test_report.html",
            "--self-contained-html"
        ]
        
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        else:
            cmd.extend(["-q"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'report_file': self.reports_dir / "unit_test_report.json"
        }
    
    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run integration tests"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "integration",
            "--json-report",
            f"--json-report-file={self.reports_dir}/integration_test_report.json",
            "--html=test_reports/integration_test_report.html",
            "--self-contained-html"
        ]
        
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        else:
            cmd.extend(["-q"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'report_file': self.reports_dir / "integration_test_report.json"
        }
    
    def run_property_tests(self, max_examples: int = 100) -> Dict[str, Any]:
        """Run property-based tests with Hypothesis"""
        env = os.environ.copy()
        env['HYPOTHESIS_PROFILE'] = 'ci'
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "property",
            f"--hypothesis-show-statistics",
            "--json-report",
            f"--json-report-file={self.reports_dir}/property_test_report.json",
            "--html=test_reports/property_test_report.html",
            "--self-contained-html",
            "-v"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'report_file': self.reports_dir / "property_test_report.json"
        }
    
    def run_async_tests(self) -> Dict[str, Any]:
        """Run async tests"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "asyncio",
            "--asyncio-mode=auto",
            "--json-report",
            f"--json-report-file={self.reports_dir}/async_test_report.json",
            "--html=test_reports/async_test_report.html",
            "--self-contained-html",
            "-v"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'report_file': self.reports_dir / "async_test_report.json"
        }
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security-focused tests"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "security",
            "--json-report",
            f"--json-report-file={self.reports_dir}/security_test_report.json",
            "--html=test_reports/security_test_report.html",
            "--self-contained-html",
            "-v"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'report_file': self.reports_dir / "security_test_report.json"
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests with benchmarking"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "performance",
            "--benchmark-only",
            "--benchmark-json=test_reports/benchmark_report.json",
            "--json-report",
            f"--json-report-file={self.reports_dir}/performance_test_report.json",
            "--html=test_reports/performance_test_report.html",
            "--self-contained-html",
            "-v"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'report_file': self.reports_dir / "performance_test_report.json"
        }
    
    def run_mutation_tests(self) -> Dict[str, Any]:
        """Run mutation tests (simulation)"""
        # In a real implementation, this would run mutmut
        # For now, we'll run the mutation testing validation tests
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "mutation",
            "--json-report",
            f"--json-report-file={self.reports_dir}/mutation_test_report.json",
            "--html=test_reports/mutation_test_report.html",
            "--self-contained-html",
            "-v"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'report_file': self.reports_dir / "mutation_test_report.json"
        }
    
    def run_smoke_tests(self) -> Dict[str, Any]:
        """Run smoke tests for quick validation"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "smoke",
            "--json-report",
            f"--json-report-file={self.reports_dir}/smoke_test_report.json",
            "--html=test_reports/smoke_test_report.html",
            "--self-contained-html",
            "-v"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'report_file': self.reports_dir / "smoke_test_report.json"
        }
    
    def run_all_tests(self, exclude_slow: bool = False) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        marker_expr = "not slow" if exclude_slow else ""
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "--cov=services",
            "--cov=api",
            "--cov-report=html:htmlcov",
            "--cov-report=json:coverage.json",
            "--json-report",
            f"--json-report-file={self.reports_dir}/comprehensive_test_report.json",
            "--html=test_reports/comprehensive_test_report.html",
            "--self-contained-html",
            "--durations=10"
        ]
        
        if marker_expr:
            cmd.extend(["-m", marker_expr])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'report_file': self.reports_dir / "comprehensive_test_report.json"
        }
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report from all test runs"""
        summary = {
            'test_runs': [],
            'overall_status': 'PASSED',
            'total_tests': 0,
            'total_passed': 0,
            'total_failed': 0,
            'total_skipped': 0,
            'coverage_percentage': 0.0
        }
        
        # Collect results from all report files
        for report_file in self.reports_dir.glob("*_test_report.json"):
            try:
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                
                test_run = {
                    'name': report_file.stem,
                    'tests': report_data.get('summary', {}).get('total', 0),
                    'passed': report_data.get('summary', {}).get('passed', 0),
                    'failed': report_data.get('summary', {}).get('failed', 0),
                    'skipped': report_data.get('summary', {}).get('skipped', 0),
                    'duration': report_data.get('duration', 0)
                }
                
                summary['test_runs'].append(test_run)
                summary['total_tests'] += test_run['tests']
                summary['total_passed'] += test_run['passed']
                summary['total_failed'] += test_run['failed']
                summary['total_skipped'] += test_run['skipped']
                
                if test_run['failed'] > 0:
                    summary['overall_status'] = 'FAILED'
                    
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        
        # Get coverage data if available
        coverage_file = self.base_dir / "coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                summary['coverage_percentage'] = coverage_data.get('totals', {}).get('percent_covered', 0.0)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        
        # Save summary report
        summary_file = self.reports_dir / "test_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Test Runner")
    parser.add_argument("--test-type", choices=[
        "unit", "integration", "property", "async", "security", 
        "performance", "mutation", "smoke", "all"
    ], default="all", help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--exclude-slow", action="store_true", help="Exclude slow tests")
    parser.add_argument("--max-examples", type=int, default=100, help="Max examples for property tests")
    
    args = parser.parse_args()
    
    runner = EnhancedTestRunner()
    
    print(f"Running {args.test_type} tests...")
    
    if args.test_type == "unit":
        result = runner.run_unit_tests(verbose=args.verbose)
    elif args.test_type == "integration":
        result = runner.run_integration_tests(verbose=args.verbose)
    elif args.test_type == "property":
        result = runner.run_property_tests(max_examples=args.max_examples)
    elif args.test_type == "async":
        result = runner.run_async_tests()
    elif args.test_type == "security":
        result = runner.run_security_tests()
    elif args.test_type == "performance":
        result = runner.run_performance_tests()
    elif args.test_type == "mutation":
        result = runner.run_mutation_tests()
    elif args.test_type == "smoke":
        result = runner.run_smoke_tests()
    elif args.test_type == "all":
        result = runner.run_all_tests(exclude_slow=args.exclude_slow)
    
    print(f"Test execution completed with exit code: {result['exit_code']}")
    
    if result['stdout']:
        print("STDOUT:")
        print(result['stdout'])
    
    if result['stderr']:
        print("STDERR:")
        print(result['stderr'])
    
    # Generate summary report
    summary = runner.generate_summary_report()
    print(f"\nTest Summary:")
    print(f"Overall Status: {summary['overall_status']}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['total_passed']}")
    print(f"Failed: {summary['total_failed']}")
    print(f"Skipped: {summary['total_skipped']}")
    print(f"Coverage: {summary['coverage_percentage']:.1f}%")
    
    return result['exit_code']

if __name__ == "__main__":
    sys.exit(main())