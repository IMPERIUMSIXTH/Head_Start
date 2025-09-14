#!/usr/bin/env python3
"""
Mutation testing runner script
Executes mutation testing with mutmut and generates reports

Author: HeadStart Development Team
Created: 2025-09-08
Purpose: Automated mutation testing execution and reporting
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mutmut_config import get_mutation_config

class MutationTestRunner:
    """Runs mutation tests and generates reports"""
    
    def __init__(self, config_path: str = None):
        self.config = get_mutation_config()
        self.project_root = project_root
        self.results = {}
    
    def run_mutation_tests(self, paths: List[str] = None, test_command: str = None) -> Dict[str, Any]:
        """Run mutation tests on specified paths"""
        if paths is None:
            paths = self.config['settings']['paths_to_mutate']
        
        if test_command is None:
            test_command = self.config['settings']['test_command']
        
        print("🧬 Starting mutation testing...")
        print(f"📁 Testing paths: {', '.join(paths)}")
        print(f"🧪 Test command: {test_command}")
        
        results = {}
        
        for path in paths:
            if not os.path.exists(path):
                print(f"⚠️  Path {path} does not exist, skipping...")
                continue
            
            print(f"\n🔬 Running mutation tests on {path}...")
            path_results = self._run_mutmut_on_path(path, test_command)
            results[path] = path_results
        
        self.results = results
        return results
    
    def _run_mutmut_on_path(self, path: str, test_command: str) -> Dict[str, Any]:
        """Run mutmut on a specific path"""
        start_time = time.time()
        
        # Prepare mutmut command
        cmd = [
            'python', '-m', 'mutmut', 'run',
            '--paths-to-mutate', path,
            '--tests-dir', 'tests/',
            '--runner', test_command,
            '--use-coverage'
        ]
        
        try:
            # Run mutmut
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config['settings']['test_timeout'] * 10  # Allow more time for mutation testing
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            if result.returncode == 0:
                print(f"✅ Mutation testing completed for {path}")
                status = "completed"
            else:
                print(f"❌ Mutation testing failed for {path}")
                print(f"Error: {result.stderr}")
                status = "failed"
            
            # Get mutation results
            mutation_results = self._get_mutation_results()
            
            return {
                'status': status,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'mutation_results': mutation_results
            }
            
        except subprocess.TimeoutExpired:
            print(f"⏰ Mutation testing timed out for {path}")
            return {
                'status': 'timeout',
                'duration': self.config['settings']['test_timeout'] * 10,
                'error': 'Timeout expired'
            }
        except Exception as e:
            print(f"💥 Error running mutation tests on {path}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_mutation_results(self) -> Dict[str, Any]:
        """Get mutation test results from mutmut"""
        try:
            # Run mutmut results command
            result = subprocess.run(
                ['python', '-m', 'mutmut', 'results'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse mutmut results
                lines = result.stdout.strip().split('\n')
                results = {
                    'total_mutants': 0,
                    'killed_mutants': 0,
                    'survived_mutants': 0,
                    'skipped_mutants': 0,
                    'timeout_mutants': 0,
                    'mutation_score': 0.0
                }
                
                for line in lines:
                    if 'total' in line.lower():
                        results['total_mutants'] = self._extract_number(line)
                    elif 'killed' in line.lower():
                        results['killed_mutants'] = self._extract_number(line)
                    elif 'survived' in line.lower():
                        results['survived_mutants'] = self._extract_number(line)
                    elif 'skipped' in line.lower():
                        results['skipped_mutants'] = self._extract_number(line)
                    elif 'timeout' in line.lower():
                        results['timeout_mutants'] = self._extract_number(line)
                
                # Calculate mutation score
                if results['total_mutants'] > 0:
                    results['mutation_score'] = (
                        results['killed_mutants'] / results['total_mutants']
                    ) * 100
                
                return results
            
        except Exception as e:
            print(f"Error getting mutation results: {e}")
        
        return {}
    
    def _extract_number(self, text: str) -> int:
        """Extract number from text"""
        import re
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else 0
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate mutation testing report"""
        if output_file is None:
            output_file = self.config['reporting']['output_file']
        
        print(f"\n📊 Generating mutation testing report...")
        
        # Generate HTML report
        html_report = self._generate_html_report()
        
        # Write report to file
        with open(output_file, 'w') as f:
            f.write(html_report)
        
        print(f"📄 Report saved to: {output_file}")
        
        # Also generate JSON report for CI/CD
        json_file = output_file.replace('.html', '.json')
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 JSON report saved to: {json_file}")
        
        return output_file
    
    def _generate_html_report(self) -> str:
        """Generate HTML mutation testing report"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Mutation Testing Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .path-results { margin: 20px 0; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .success { color: green; }
        .failure { color: red; }
        .warning { color: orange; }
        .score { font-size: 24px; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧬 Mutation Testing Report</h1>
        <p>Generated on: {timestamp}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        {summary_content}
    </div>
    
    <div class="details">
        <h2>📋 Detailed Results</h2>
        {details_content}
    </div>
    
    <div class="quality-gates">
        <h2>🚪 Quality Gates</h2>
        {quality_gates_content}
    </div>
</body>
</html>
        """.strip()
        
        # Generate content
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        summary_content = self._generate_summary_content()
        details_content = self._generate_details_content()
        quality_gates_content = self._generate_quality_gates_content()
        
        return html.format(
            timestamp=timestamp,
            summary_content=summary_content,
            details_content=details_content,
            quality_gates_content=quality_gates_content
        )
    
    def _generate_summary_content(self) -> str:
        """Generate summary content for report"""
        if not self.results:
            return "<p>No mutation testing results available.</p>"
        
        total_paths = len(self.results)
        successful_paths = sum(1 for r in self.results.values() if r.get('status') == 'completed')
        
        overall_score = 0
        total_mutants = 0
        killed_mutants = 0
        
        for path_results in self.results.values():
            mutation_results = path_results.get('mutation_results', {})
            if mutation_results:
                total_mutants += mutation_results.get('total_mutants', 0)
                killed_mutants += mutation_results.get('killed_mutants', 0)
        
        if total_mutants > 0:
            overall_score = (killed_mutants / total_mutants) * 100
        
        score_class = "success" if overall_score >= 75 else "failure" if overall_score < 50 else "warning"
        
        return f"""
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Paths Tested</td><td>{total_paths}</td></tr>
            <tr><td>Successful Runs</td><td>{successful_paths}</td></tr>
            <tr><td>Total Mutants</td><td>{total_mutants}</td></tr>
            <tr><td>Killed Mutants</td><td>{killed_mutants}</td></tr>
            <tr><td>Overall Mutation Score</td><td><span class="{score_class} score">{overall_score:.1f}%</span></td></tr>
        </table>
        """
    
    def _generate_details_content(self) -> str:
        """Generate detailed results content"""
        if not self.results:
            return "<p>No detailed results available.</p>"
        
        content = ""
        for path, results in self.results.items():
            status = results.get('status', 'unknown')
            duration = results.get('duration', 0)
            mutation_results = results.get('mutation_results', {})
            
            status_class = "success" if status == "completed" else "failure"
            
            content += f"""
            <div class="path-results">
                <h3>📁 {path}</h3>
                <p><strong>Status:</strong> <span class="{status_class}">{status}</span></p>
                <p><strong>Duration:</strong> {duration:.2f} seconds</p>
            """
            
            if mutation_results:
                score = mutation_results.get('mutation_score', 0)
                score_class = "success" if score >= 75 else "failure" if score < 50 else "warning"
                
                content += f"""
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Mutants</td><td>{mutation_results.get('total_mutants', 0)}</td></tr>
                    <tr><td>Killed Mutants</td><td>{mutation_results.get('killed_mutants', 0)}</td></tr>
                    <tr><td>Survived Mutants</td><td>{mutation_results.get('survived_mutants', 0)}</td></tr>
                    <tr><td>Mutation Score</td><td><span class="{score_class}">{score:.1f}%</span></td></tr>
                </table>
                """
            
            content += "</div>"
        
        return content
    
    def _generate_quality_gates_content(self) -> str:
        """Generate quality gates content"""
        gates = self.config['quality_gates']
        min_score = gates['min_mutation_score']
        
        # Check overall score against quality gates
        overall_score = 0
        total_mutants = 0
        killed_mutants = 0
        
        for path_results in self.results.values():
            mutation_results = path_results.get('mutation_results', {})
            if mutation_results:
                total_mutants += mutation_results.get('total_mutants', 0)
                killed_mutants += mutation_results.get('killed_mutants', 0)
        
        if total_mutants > 0:
            overall_score = (killed_mutants / total_mutants) * 100
        
        gate_status = "✅ PASSED" if overall_score >= min_score else "❌ FAILED"
        gate_class = "success" if overall_score >= min_score else "failure"
        
        return f"""
        <p><strong>Minimum Required Score:</strong> {min_score}%</p>
        <p><strong>Actual Score:</strong> {overall_score:.1f}%</p>
        <p><strong>Quality Gate Status:</strong> <span class="{gate_class}">{gate_status}</span></p>
        """
    
    def check_quality_gates(self) -> bool:
        """Check if mutation testing passes quality gates"""
        if not self.results:
            return False
        
        gates = self.config['quality_gates']
        min_score = gates['min_mutation_score']
        
        # Calculate overall score
        total_mutants = 0
        killed_mutants = 0
        
        for path_results in self.results.values():
            mutation_results = path_results.get('mutation_results', {})
            if mutation_results:
                total_mutants += mutation_results.get('total_mutants', 0)
                killed_mutants += mutation_results.get('killed_mutants', 0)
        
        if total_mutants == 0:
            return False
        
        overall_score = (killed_mutants / total_mutants) * 100
        
        return overall_score >= min_score

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run mutation tests')
    parser.add_argument('--paths', nargs='+', help='Paths to test')
    parser.add_argument('--test-command', help='Test command to use')
    parser.add_argument('--output', help='Output file for report')
    parser.add_argument('--check-gates', action='store_true', help='Check quality gates and exit with error if failed')
    
    args = parser.parse_args()
    
    runner = MutationTestRunner()
    
    # Run mutation tests
    results = runner.run_mutation_tests(
        paths=args.paths,
        test_command=args.test_command
    )
    
    # Generate report
    report_file = runner.generate_report(args.output)
    
    # Check quality gates if requested
    if args.check_gates:
        if runner.check_quality_gates():
            print("✅ Quality gates passed!")
            sys.exit(0)
        else:
            print("❌ Quality gates failed!")
            sys.exit(1)
    
    print(f"\n🎉 Mutation testing completed! Report: {report_file}")

if __name__ == '__main__':
    main()