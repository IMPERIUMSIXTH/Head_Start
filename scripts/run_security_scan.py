#!/usr/bin/env python3
"""
Security scanning CLI script.

This script provides a command-line interface for running comprehensive
security scans and generating reports.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.security_config import (
    get_security_config,
    create_scanner_config,
    setup_security_environment,
    validate_security_tools
)
from services.security_scanner import SecurityScanner
from services.vulnerability_analyzer import VulnerabilityAnalyzer


def setup_logging():
    """Set up logging for the security scan."""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('security_scan.log')
        ]
    )
    
    return logging.getLogger(__name__)


def print_banner():
    """Print security scan banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    Security Scanning Engine                  ║
║              AI-Powered Learning Platform Security           ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_scan_summary(scan_results, analysis_report=None):
    """Print a summary of scan results."""
    print("\n" + "="*60)
    print("SECURITY SCAN SUMMARY")
    print("="*60)
    
    print(f"Scan ID: {scan_results.scan_id}")
    print(f"Timestamp: {scan_results.timestamp}")
    print(f"Total Vulnerabilities: {scan_results.total_vulnerabilities}")
    
    print("\nVulnerabilities by Severity:")
    for severity, count in scan_results.severity_counts.items():
        if count > 0:
            print(f"  {severity.value}: {count}")
    
    print(f"\nTools Used: {', '.join(scan_results.scan_tools_used)}")
    print(f"Compliance Status: {'PASS' if scan_results.compliance_status.get('overall_compliance', False) else 'FAIL'}")
    print(f"Remediation Required: {'YES' if scan_results.remediation_required else 'NO'}")
    
    if analysis_report:
        print(f"\nRisk Assessments: {len(analysis_report.risk_assessments)}")
        print(f"Remediation Actions: {len(analysis_report.remediation_plan.actions)}")
        print(f"Estimated Remediation Time: {analysis_report.remediation_plan.estimated_total_hours} hours")
        
        immediate_actions = analysis_report.remediation_plan.get_immediate_actions()
        if immediate_actions:
            print(f"IMMEDIATE ACTIONS REQUIRED: {len(immediate_actions)}")
    
    print("="*60)


def save_results(scan_results, analysis_report, output_dir: Path):
    """Save scan results and analysis to files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw scan results
    scan_file = output_dir / f"security_scan_{timestamp}.json"
    with open(scan_file, 'w') as f:
        # Convert to dict for JSON serialization
        scan_data = {
            "scan_id": scan_results.scan_id,
            "timestamp": scan_results.timestamp.isoformat(),
            "total_vulnerabilities": scan_results.total_vulnerabilities,
            "severity_counts": {k.value: v for k, v in scan_results.severity_counts.items()},
            "compliance_status": scan_results.compliance_status,
            "remediation_required": scan_results.remediation_required,
            "scan_tools_used": scan_results.scan_tools_used,
            "vulnerabilities": []
        }
        
        # Add vulnerabilities
        for scan_result in scan_results.scan_results:
            for vuln in scan_result.vulnerabilities:
                vuln_data = {
                    "id": vuln.id,
                    "title": vuln.title,
                    "description": vuln.description,
                    "severity": vuln.severity.value,
                    "type": vuln.vulnerability_type.value,
                    "file_path": vuln.file_path,
                    "line_number": vuln.line_number,
                    "cwe_id": vuln.cwe_id,
                    "cve_id": vuln.cve_id,
                    "remediation": vuln.remediation
                }
                scan_data["vulnerabilities"].append(vuln_data)
        
        json.dump(scan_data, f, indent=2, default=str)
    
    print(f"Scan results saved to: {scan_file}")
    
    if analysis_report:
        # Save analysis report
        analysis_file = output_dir / f"security_analysis_{timestamp}.json"
        with open(analysis_file, 'w') as f:
            analysis_data = {
                "report_id": analysis_report.report_id,
                "executive_summary": analysis_report.executive_summary,
                "recommendations": analysis_report.recommendations,
                "remediation_plan": {
                    "plan_id": analysis_report.remediation_plan.plan_id,
                    "total_vulnerabilities": analysis_report.remediation_plan.total_vulnerabilities,
                    "estimated_total_hours": analysis_report.remediation_plan.estimated_total_hours,
                    "timeline_weeks": analysis_report.remediation_plan.timeline_weeks,
                    "success_criteria": analysis_report.remediation_plan.success_criteria,
                    "actions": [
                        {
                            "action_id": action.action_id,
                            "title": action.title,
                            "description": action.description,
                            "priority": action.priority.value,
                            "estimated_hours": action.estimated_hours,
                            "affected_vulnerabilities": action.affected_vulnerabilities
                        }
                        for action in analysis_report.remediation_plan.actions
                    ]
                }
            }
            json.dump(analysis_data, f, indent=2, default=str)
        
        print(f"Analysis report saved to: {analysis_file}")
        
        # Save executive summary as text
        summary_file = output_dir / f"executive_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(analysis_report.executive_summary)
            f.write("\n\nRecommendations:\n")
            for i, rec in enumerate(analysis_report.recommendations, 1):
                f.write(f"{i}. {rec}\n")
        
        print(f"Executive summary saved to: {summary_file}")


async def run_security_scan(
    project_path: str,
    output_dir: Optional[str] = None,
    analyze: bool = True,
    tools: Optional[list] = None
) -> tuple:
    """Run comprehensive security scan."""
    logger = setup_logging()
    
    # Setup environment
    logger.info("Setting up security environment...")
    tools_status = setup_security_environment()
    
    # Validate required tools
    missing_tools = [tool for tool, available in tools_status.items() 
                    if not available and tool in ['bandit', 'safety']]
    if missing_tools:
        logger.error(f"Missing required tools: {', '.join(missing_tools)}")
        return None, None
    
    # Load configuration
    logger.info("Loading security configuration...")
    security_config = get_security_config()
    scanner_config = create_scanner_config(security_config)
    
    # Create scanner
    logger.info("Initializing security scanner...")
    scanner = SecurityScanner(scanner_config)
    
    # Run scan
    logger.info(f"Starting security scan of: {project_path}")
    scan_results = await scanner.run_comprehensive_scan(project_path)
    
    analysis_report = None
    if analyze:
        logger.info("Analyzing vulnerabilities...")
        analyzer = VulnerabilityAnalyzer()
        analysis_report = analyzer.analyze_vulnerabilities(scan_results)
    
    # Save results
    if output_dir:
        output_path = Path(output_dir)
        save_results(scan_results, analysis_report, output_path)
    
    return scan_results, analysis_report


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive security scan",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_security_scan.py                    # Scan current directory
  python scripts/run_security_scan.py --path /app        # Scan specific path
  python scripts/run_security_scan.py --no-analyze      # Skip analysis
  python scripts/run_security_scan.py --output reports   # Save to reports directory
  python scripts/run_security_scan.py --tools bandit safety  # Run specific tools only
        """
    )
    
    parser.add_argument(
        "--path", "-p",
        default=".",
        help="Path to scan (default: current directory)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output directory for reports"
    )
    
    parser.add_argument(
        "--no-analyze",
        action="store_true",
        help="Skip vulnerability analysis"
    )
    
    parser.add_argument(
        "--tools", "-t",
        nargs="+",
        choices=["bandit", "safety", "secrets", "container"],
        help="Specific tools to run"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress output except errors"
    )
    
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="Exit with error code if high severity vulnerabilities found"
    )
    
    parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        default=True,
        help="Exit with error code if critical vulnerabilities found (default: True)"
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_banner()
    
    # Run the scan
    try:
        scan_results, analysis_report = asyncio.run(
            run_security_scan(
                project_path=args.path,
                output_dir=args.output,
                analyze=not args.no_analyze,
                tools=args.tools
            )
        )
        
        if scan_results is None:
            print("Security scan failed due to missing tools or configuration errors.")
            sys.exit(1)
        
        if not args.quiet:
            print_scan_summary(scan_results, analysis_report)
        
        # Determine exit code based on results
        exit_code = 0
        
        if args.fail_on_critical and scan_results.severity_counts.get('CRITICAL', 0) > 0:
            exit_code = 1
            if not args.quiet:
                print("\nFAILURE: Critical vulnerabilities found!")
        
        if args.fail_on_high and scan_results.severity_counts.get('HIGH', 0) > 0:
            exit_code = 1
            if not args.quiet:
                print("\nFAILURE: High severity vulnerabilities found!")
        
        if exit_code == 0 and not args.quiet:
            print("\nSUCCESS: Security scan completed successfully!")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nScan interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"Error during security scan: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()