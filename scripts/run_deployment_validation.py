#!/usr/bin/env python3
"""
Deployment Validation CLI Script

This script provides a command-line interface for running comprehensive deployment
validation checks including Kubernetes manifests, Helm charts, network security,
and environment configuration validation.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.deployment_validator import DeploymentValidator, validate_deployment


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def print_validation_results(results):
    """Print validation results in a formatted way."""
    print("\n" + "="*80)
    print("DEPLOYMENT VALIDATION RESULTS")
    print("="*80)

    print(f"\nEnvironment: {results.environment}")
    print(f"Overall Score: {results.overall_score:.1f}/100")
    print(f"Deployment Ready: {'✅ YES' if results.deployment_ready else '❌ NO'}")
    print(f"Validation Timestamp: {results.validation_timestamp}")

    # Kubernetes Validation Results
    print("\n" + "-"*60)
    print("KUBERNETES VALIDATION")
    print("-"*60)
    k8s = results.kubernetes_validation
    print(f"Manifest Syntax Valid: {'✅' if k8s.manifest_syntax_valid else '❌'}")
    print(f"Resource Quotas Valid: {'✅' if k8s.resource_quotas_valid else '❌'}")
    print(f"Security Policies Valid: {'✅' if k8s.security_policies_valid else '❌'}")
    print(f"Best Practices Followed: {'✅' if k8s.best_practices_followed else '❌'}")

    if k8s.validation_errors:
        print("\nErrors:")
        for error in k8s.validation_errors:
            print(f"  ❌ {error.message}")

    if k8s.validation_warnings:
        print("\nWarnings:")
        for warning in k8s.validation_warnings:
            print(f"  ⚠️  {warning.message}")

    # Helm Validation Results
    if results.helm_validation:
        print("\n" + "-"*60)
        print("HELM VALIDATION")
        print("-"*60)
        helm = results.helm_validation
        print(f"Template Syntax Valid: {'✅' if helm.template_syntax_valid else '❌'}")
        print(f"Values Schema Valid: {'✅' if helm.values_schema_valid else '❌'}")
        print(f"Chart Structure Valid: {'✅' if helm.chart_structure_valid else '❌'}")
        print(f"Dependencies Resolved: {'✅' if helm.dependencies_resolved else '❌'}")

        if helm.validation_errors:
            print("\nErrors:")
            for error in helm.validation_errors:
                print(f"  ❌ {error.message}")

        if helm.validation_warnings:
            print("\nWarnings:")
            for warning in helm.validation_warnings:
                print(f"  ⚠️  {warning.message}")

    # Network Security Results
    print("\n" + "-"*60)
    print("NETWORK SECURITY")
    print("-"*60)
    network = results.network_security
    print(f"Network Policies Configured: {'✅' if network.network_policies_configured else '❌'}")
    print(f"Least Privilege Enforced: {'✅' if network.least_privilege_enforced else '❌'}")
    print(f"TLS Configured: {'✅' if network.tls_configured else '❌'}")
    print(f"Ingress Security Valid: {'✅' if network.ingress_security_valid else '❌'}")
    print(f"Service Mesh Configured: {'✅' if network.service_mesh_configured else '❌'}")

    if network.validation_errors:
        print("\nErrors:")
        for error in network.validation_errors:
            print(f"  ❌ {error.message}")

    if network.validation_warnings:
        print("\nWarnings:")
        for warning in network.validation_warnings:
            print(f"  ⚠️  {warning.message}")

    # Secrets Validation Results
    print("\n" + "-"*60)
    print("SECRETS MANAGEMENT")
    print("-"*60)
    secrets = results.secrets_validation
    print(f"Secrets Externalized: {'✅' if secrets.secrets_externalized else '❌'}")
    print(f"Environment Vars Configured: {'✅' if secrets.environment_vars_configured else '❌'}")
    print(f"No Hardcoded Secrets: {'✅' if secrets.no_hardcoded_secrets else '❌'}")
    print(f"Secret Rotation Configured: {'✅' if secrets.secret_rotation_configured else '❌'}")

    if secrets.validation_errors:
        print("\nErrors:")
        for error in secrets.validation_errors:
            print(f"  ❌ {error.message}")

    if secrets.validation_warnings:
        print("\nWarnings:")
        for warning in secrets.validation_warnings:
            print(f"  ⚠️  {warning.message}")

    # Recommendations
    if results.recommendations:
        print("\n" + "-"*60)
        print("RECOMMENDATIONS")
        print("-"*60)
        for i, recommendation in enumerate(results.recommendations, 1):
            print(f"{i}. {recommendation}")

    print("\n" + "="*80)


def print_deployment_readiness_summary(results):
    """Print a deployment readiness summary based on the original requirements."""
    print("\n" + "="*80)
    print("DEPLOYMENT READINESS ASSESSMENT")
    print("="*80)

    checks = [
        {
            "name": "Environment variables defined and stored securely",
            "status": results.secrets_validation.environment_vars_configured and results.secrets_validation.secrets_externalized,
            "details": "Environment variables configured and externalized properly"
        },
        {
            "name": "Kubernetes manifests validated",
            "status": results.kubernetes_validation.manifest_syntax_valid,
            "details": "Kubernetes manifest syntax and structure validation"
        },
        {
            "name": "Network security policies configured",
            "status": results.network_security.network_policies_configured,
            "details": "Network policies and security configurations"
        },
        {
            "name": "TLS/HTTPS enabled",
            "status": results.network_security.tls_configured,
            "details": "TLS certificates and HTTPS configuration"
        },
        {
            "name": "No hardcoded secrets detected",
            "status": results.secrets_validation.no_hardcoded_secrets,
            "details": "Codebase scanned for hardcoded credentials"
        },
        {
            "name": "Best practices followed",
            "status": results.kubernetes_validation.best_practices_followed,
            "details": "Kubernetes and deployment best practices"
        }
    ]

    passed_checks = sum(1 for check in checks if check["status"])
    total_checks = len(checks)

    print(f"\nOverall Status: {passed_checks}/{total_checks} checks passed")
    print(f"Deployment Readiness: {'✅ APPROVED' if results.deployment_ready else '❌ BLOCKED'}")

    print(f"\nDetailed Checks:")
    for check in checks:
        status_icon = "✅" if check["status"] else "❌"
        print(f"  {status_icon} {check['name']}")
        print(f"     {check['details']}")

    if not results.deployment_ready:
        print(f"\n❌ DEPLOYMENT BLOCKED")
        print("Action Required: Address the failed checks above before proceeding with deployment.")
    else:
        print(f"\n✅ DEPLOYMENT APPROVED")
        print("Action: Proceed with deployment.")

    print("\n" + "="*80)


async def main():
    """Main function for the deployment validation CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run comprehensive deployment validation checks"
    )
    parser.add_argument(
        "--environment", "-e",
        default="development",
        choices=["development", "staging", "production"],
        help="Target deployment environment"
    )
    parser.add_argument(
        "--project-root", "-p",
        default=".",
        help="Project root directory"
    )
    parser.add_argument(
        "--skip-k8s",
        action="store_true",
        help="Skip Kubernetes validation"
    )
    parser.add_argument(
        "--skip-helm",
        action="store_true",
        help="Skip Helm validation"
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Skip network security validation"
    )
    parser.add_argument(
        "--skip-secrets",
        action="store_true",
        help="Skip secrets validation"
    )
    parser.add_argument(
        "--output", "-o",
        choices=["console", "json"],
        default="console",
        help="Output format"
    )
    parser.add_argument(
        "--output-file",
        help="Output file path (for JSON output)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Treat warnings as failures"
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)

    try:
        # Run deployment validation
        print(f"Running deployment validation for {args.environment} environment...")

        results = await validate_deployment(
            project_root=args.project_root,
            environment=args.environment,
            validate_k8s=not args.skip_k8s,
            validate_helm=not args.skip_helm,
            validate_network=not args.skip_network,
            validate_secrets=not args.skip_secrets
        )

        # Output results
        if args.output == "json":
            # Convert results to JSON-serializable format
            results_dict = {
                "environment": results.environment,
                "deployment_ready": results.deployment_ready,
                "overall_score": results.overall_score,
                "validation_timestamp": results.validation_timestamp.isoformat(),
                "kubernetes_validation": {
                    "manifest_syntax_valid": results.kubernetes_validation.manifest_syntax_valid,
                    "resource_quotas_valid": results.kubernetes_validation.resource_quotas_valid,
                    "security_policies_valid": results.kubernetes_validation.security_policies_valid,
                    "best_practices_followed": results.kubernetes_validation.best_practices_followed,
                    "errors": [{"message": e.message, "severity": e.severity} for e in results.kubernetes_validation.validation_errors],
                    "warnings": [{"message": w.message, "severity": w.severity} for w in results.kubernetes_validation.validation_warnings]
                },
                "network_security": {
                    "network_policies_configured": results.network_security.network_policies_configured,
                    "least_privilege_enforced": results.network_security.least_privilege_enforced,
                    "tls_configured": results.network_security.tls_configured,
                    "ingress_security_valid": results.network_security.ingress_security_valid,
                    "service_mesh_configured": results.network_security.service_mesh_configured,
                    "errors": [{"message": e.message, "severity": e.severity} for e in results.network_security.validation_errors],
                    "warnings": [{"message": w.message, "severity": w.severity} for w in results.network_security.validation_warnings]
                },
                "secrets_validation": {
                    "secrets_externalized": results.secrets_validation.secrets_externalized,
                    "environment_vars_configured": results.secrets_validation.environment_vars_configured,
                    "no_hardcoded_secrets": results.secrets_validation.no_hardcoded_secrets,
                    "secret_rotation_configured": results.secrets_validation.secret_rotation_configured,
                    "errors": [{"message": e.message, "severity": e.severity} for e in results.secrets_validation.validation_errors],
                    "warnings": [{"message": w.message, "severity": w.severity} for w in results.secrets_validation.validation_warnings]
                },
                "recommendations": results.recommendations
            }

            if results.helm_validation:
                results_dict["helm_validation"] = {
                    "template_syntax_valid": results.helm_validation.template_syntax_valid,
                    "values_schema_valid": results.helm_validation.values_schema_valid,
                    "chart_structure_valid": results.helm_validation.chart_structure_valid,
                    "dependencies_resolved": results.helm_validation.dependencies_resolved,
                    "errors": [{"message": e.message, "severity": e.severity} for e in results.helm_validation.validation_errors],
                    "warnings": [{"message": w.message, "severity": w.severity} for w in results.helm_validation.validation_warnings]
                }

            json_output = json.dumps(results_dict, indent=2)

            if args.output_file:
                with open(args.output_file, 'w') as f:
                    f.write(json_output)
                print(f"Results written to {args.output_file}")
            else:
                print(json_output)
        else:
            # Console output
            print_validation_results(results)
            print_deployment_readiness_summary(results)

        # Determine exit code
        exit_code = 0

        if not results.deployment_ready:
            exit_code = 1
        elif args.fail_on_warnings:
            # Check if there are any warnings
            has_warnings = (
                results.kubernetes_validation.validation_warnings or
                results.network_security.validation_warnings or
                results.secrets_validation.validation_warnings or
                (results.helm_validation and results.helm_validation.validation_warnings)
            )
            if has_warnings:
                exit_code = 1

        sys.exit(exit_code)

    except Exception as e:
        logging.error(f"Deployment validation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
