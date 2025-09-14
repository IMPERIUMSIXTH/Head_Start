#!/usr/bin/env python3
"""
Enhanced test runner script
Demonstrates all enhanced testing capabilities including property-based testing,
async patterns, mutation testing, and comprehensive reporting

Author: HeadStart Development Team
Created: 2025-09-08
Purpose: Comprehensive test execution with enhanced capabilities
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class EnhancedTestRunner:
    """Enhanced test runner with advanced capabilities"""
    
    def __init__(self):
        self.project_root = project_root
        self.results = {}
    
    def run_all_tests(self, test_types: List[str] = None) -> Dict[str, Any]:
        """Run all enhanced tests"""
        if test_types is None:
            test_types = [
                'unit',
                'property',
                'async',
                'security',
                'performance',
                'mutation'
            ]
        
        print("🚀 Starting enhanced test suite...")
        print(f"📋 Test types: {', '.join(test_types)}")
        
        results = {}
        
        for test_type in test_types:
            print(f"\n🧪 Running {test_type} tests...")
            test_result = self._run_test_type(test_type)
            results[test_type] = test_result
        
        self.results = results
        return results
    
    def _run_test_type(self, test_type: str) -> Dict[str, Any]:
        """Run a specific type of test"""
        start_time = time.time()
        
        try:
            if test_type == 'unit':
                result = self._run_unit_tests()
            elif test_type == 'property':
                result = self._run_property_tests()
            elif test_type == 'async':
                result = self._run_async_tests()
            elif test_type == 'security':
                result = self._run_security_tests()
            elif test_type == 'performance':
                result = self._run_performance_tests()
            elif test_type == 'mutation':
                result = self._run_mutation_tests()
            else:
                result = {'status': 'unknown', 'error': f'Unknown test type: {test_type}'}
            
            end_time = time.time()
            result['duration'] = end_time - start_time
            
            return result
            
        except Exception as e:
            end_time = time.time()
            return {
                'status': 'error',
                'error': str(e),
                'duration': end_time - start_time
            }
    
    def _run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests with coverage"""
        cmd = [
            'python', '-m', 'pytest',
            'tests/unit/',
            'tests/test_authentication.py',
            'tests/test_content_processing.py',
            'tests/enhanced_unit_tests.py',
            '-v',
            '--cov=services',
            '--cov=api',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-report=xml',
            '--tb=short',
            '-m', 'unit'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'status': 'passed' if result.returncode == 0 else 'failed',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'coverage_report': 'htmlcov/index.html'
        }
    
    def _run_property_tests(self) -> Dict[str, Any]:
        """Run property-based tests with Hypothesis"""
        cmd = [
            'python', '-m', 'pytest',
            'tests/property_tests.py',
            'tests/enhanced_unit_tests.py',
            '-v',
            '--tb=short',
            '-m', 'property',
            '--hypothesis-profile=ci'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'status': 'passed' if result.returncode == 0 else 'failed',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'test_type': 'property-based'
        }
    
    def _run_async_tests(self) -> Dict[str, Any]:
        """Run async tests"""
        cmd = [
            'python', '-m', 'pytest',
            'tests/async_tests.py',
            'tests/enhanced_unit_tests.py',
            '-v',
            '--tb=short',
            '-m', 'async',
            '--asyncio-mode=auto'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'status': 'passed' if result.returncode == 0 else 'failed',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'test_type': 'async'
        }
    
    def _run_security_tests(self) -> Dict[str, Any]:
        """Run security tests"""
        cmd = [
            'python', '-m', 'pytest',
            'tests/enhanced_unit_tests.py',
            'tests/property_tests.py',
            '-v',
            '--tb=short',
            '-m', 'security'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'status': 'passed' if result.returncode == 0 else 'failed',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'test_type': 'security'
        }
    
    def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        cmd = [
            'python', '-m', 'pytest',
            'tests/enhanced_unit_tests.py',
            'tests/async_tests.py',
            '-v',
            '--tb=short',
            '-m', 'performance or slow',
            '--benchmark-only',
            '--benchmark-sort=mean'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'status': 'passed' if result.returncode == 0 else 'failed',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'test_type': 'performance'
        }
    
    def _run_mutation_tests(self) -> Dict[str, Any]:
        """Run mutation tests"""
        try:
            # Import and run mutation testing
            from scripts.run_mutation_tests import MutationTestRunner
            
            mutation_runner = MutationTestRunner()
            mutation_results = mutation_runner.run_mutation_tests(
                paths=['services/auth.py', 'services/security.py']
            )
            
            # Generate report
            report_file = mutation_runner.generate_report('mutation_report.html')
            
            # Check quality gates
            gates_passed = mutation_runner.check_quality_gates()
            
            return {
                'status': 'passed' if gates_passed else 'failed',
                'mutation_results': mutation_results,
                'report_file': report_file,
                'quality_gates_passed': gates_passed,
                'test_type': 'mutation'
            }
            
        except ImportError:
            return {
                'status': 'skipped',
                'error': 'mutmut not available',
                'test_type': 'mutation'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'test_type': 'mutation'
            }
    
    def generate_comprehensive_report(self, output_file: str = 'test_report.html') -> str:
        """Generate comprehensive test report"""
        print(f"\n📊 Generating comprehensive test report...")
        
        html_report = self._generate_html_report()
        
        with open(output_file, 'w') as f:
            f.write(html_report)
        
        print(f"📄 Report saved to: {output_file}")
        return output_file
    
    def _generate_html_report(self) -> str:
        """Generate HTML test report"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Testing Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background-color: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }
        .test-section { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .success { color: #28a745; }
        .failure { color: #dc3545; }
        .warning { color: #ffc107; }
        .skipped { color: #6c757d; }
        .status-badge { padding: 4px 12px; border-radius: 20px; color: white; font-weight: bold; }
        .status-passed { background-color: #28a745; }
        .status-failed { background-color: #dc3545; }
        .status-skipped { background-color: #6c757d; }
        .status-error { background-color: #fd7e14; }
        table { border-collapse: collapse; width: 100%; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        .code-block { background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
        .metric { font-size: 24px; font-weight: bold; margin: 10px 0; }
        .chart { width: 100%; height: 200px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Enhanced Testing Report</h1>
            <p>Comprehensive test results with advanced capabilities</p>
            <p>Generated on: {timestamp}</p>
        </div>
        
        <div class="summary">
            {summary_cards}
        </div>
        
        <div class="test-results">
            <h2>📋 Test Results by Type</h2>
            {test_sections}
        </div>
        
        <div class="recommendations">
            <h2>💡 Recommendations</h2>
            {recommendations}
        </div>
    </div>
</body>
</html>
        """.strip()
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        summary_cards = self._generate_summary_cards()
        test_sections = self._generate_test_sections()
        recommendations = self._generate_recommendations()
        
        return html.format(
            timestamp=timestamp,
            summary_cards=summary_cards,
            test_sections=test_sections,
            recommendations=recommendations
        )
    
    def _generate_summary_cards(self) -> str:
        """Generate summary cards"""
        if not self.results:
            return "<div class='summary-card'><h3>No Results</h3><p>No test results available</p></div>"
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r.get('status') == 'passed')
        failed_tests = sum(1 for r in self.results.values() if r.get('status') == 'failed')
        skipped_tests = sum(1 for r in self.results.values() if r.get('status') == 'skipped')
        
        total_duration = sum(r.get('duration', 0) for r in self.results.values())
        
        cards = f"""
        <div class="summary-card">
            <h3>Total Test Types</h3>
            <div class="metric">{total_tests}</div>
        </div>
        <div class="summary-card">
            <h3>Passed</h3>
            <div class="metric success">{passed_tests}</div>
        </div>
        <div class="summary-card">
            <h3>Failed</h3>
            <div class="metric failure">{failed_tests}</div>
        </div>
        <div class="summary-card">
            <h3>Skipped</h3>
            <div class="metric skipped">{skipped_tests}</div>
        </div>
        <div class="summary-card">
            <h3>Total Duration</h3>
            <div class="metric">{total_duration:.1f}s</div>
        </div>
        """
        
        return cards
    
    def _generate_test_sections(self) -> str:
        """Generate test sections"""
        if not self.results:
            return "<p>No test results available.</p>"
        
        sections = ""
        
        for test_type, result in self.results.items():
            status = result.get('status', 'unknown')
            duration = result.get('duration', 0)
            
            status_class = f"status-{status}"
            status_badge = f'<span class="status-badge {status_class}">{status.upper()}</span>'
            
            sections += f"""
            <div class="test-section">
                <h3>🧪 {test_type.title()} Tests {status_badge}</h3>
                <p><strong>Duration:</strong> {duration:.2f} seconds</p>
            """
            
            # Add specific details based on test type
            if test_type == 'unit' and 'coverage_report' in result:
                sections += f'<p><strong>Coverage Report:</strong> <a href="{result["coverage_report"]}" target="_blank">View Coverage</a></p>'
            
            if test_type == 'mutation' and 'report_file' in result:
                sections += f'<p><strong>Mutation Report:</strong> <a href="{result["report_file"]}" target="_blank">View Mutations</a></p>'
                if 'quality_gates_passed' in result:
                    gate_status = "✅ PASSED" if result['quality_gates_passed'] else "❌ FAILED"
                    sections += f'<p><strong>Quality Gates:</strong> {gate_status}</p>'
            
            # Add stdout/stderr if available
            if 'stdout' in result and result['stdout']:
                sections += f'<h4>Output:</h4><div class="code-block">{result["stdout"][:1000]}{"..." if len(result["stdout"]) > 1000 else ""}</div>'
            
            if 'stderr' in result and result['stderr']:
                sections += f'<h4>Errors:</h4><div class="code-block">{result["stderr"][:1000]}{"..." if len(result["stderr"]) > 1000 else ""}</div>'
            
            sections += "</div>"
        
        return sections
    
    def _generate_recommendations(self) -> str:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if not self.results:
            return "<p>No recommendations available.</p>"
        
        # Check for failed tests
        failed_tests = [test_type for test_type, result in self.results.items() if result.get('status') == 'failed']
        if failed_tests:
            recommendations.append(f"❌ Fix failing tests: {', '.join(failed_tests)}")
        
        # Check for skipped tests
        skipped_tests = [test_type for test_type, result in self.results.items() if result.get('status') == 'skipped']
        if skipped_tests:
            recommendations.append(f"⚠️ Address skipped tests: {', '.join(skipped_tests)}")
        
        # Check mutation testing results
        if 'mutation' in self.results:
            mutation_result = self.results['mutation']
            if not mutation_result.get('quality_gates_passed', True):
                recommendations.append("🧬 Improve mutation test coverage - quality gates failed")
        
        # Check test duration
        total_duration = sum(r.get('duration', 0) for r in self.results.values())
        if total_duration > 300:  # 5 minutes
            recommendations.append("⏰ Consider optimizing test performance - tests taking too long")
        
        # General recommendations
        if all(r.get('status') == 'passed' for r in self.results.values()):
            recommendations.append("✅ All tests passing! Consider adding more edge cases and property-based tests")
        
        if not recommendations:
            recommendations.append("🎉 No specific recommendations - test suite looks good!")
        
        return "<ul>" + "".join(f"<li>{rec}</li>" for rec in recommendations) + "</ul>"
    
    def check_quality_gates(self) -> bool:
        """Check if all quality gates pass"""
        if not self.results:
            return False
        
        # All test types should pass (except skipped ones)
        for test_type, result in self.results.items():
            status = result.get('status')
            if status == 'failed' or status == 'error':
                return False
        
        # Specific checks for mutation testing
        if 'mutation' in self.results:
            mutation_result = self.results['mutation']
            if not mutation_result.get('quality_gates_passed', True):
                return False
        
        return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run enhanced tests')
    parser.add_argument('--types', nargs='+', 
                       choices=['unit', 'property', 'async', 'security', 'performance', 'mutation'],
                       help='Test types to run')
    parser.add_argument('--output', default='test_report.html', help='Output file for report')
    parser.add_argument('--check-gates', action='store_true', help='Check quality gates and exit with error if failed')
    
    args = parser.parse_args()
    
    runner = EnhancedTestRunner()
    
    # Run tests
    results = runner.run_all_tests(test_types=args.types)
    
    # Generate report
    report_file = runner.generate_comprehensive_report(args.output)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    for test_type, result in results.items():
        status = result.get('status', 'unknown')
        duration = result.get('duration', 0)
        status_emoji = {'passed': '✅', 'failed': '❌', 'skipped': '⏭️', 'error': '💥'}.get(status, '❓')
        print(f"  {status_emoji} {test_type}: {status} ({duration:.1f}s)")
    
    # Check quality gates if requested
    if args.check_gates:
        if runner.check_quality_gates():
            print("\n✅ All quality gates passed!")
            sys.exit(0)
        else:
            print("\n❌ Quality gates failed!")
            sys.exit(1)
    
    print(f"\n🎉 Enhanced testing completed! Report: {report_file}")

if __name__ == '__main__':
    main()