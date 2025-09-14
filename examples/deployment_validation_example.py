#!/usr/bin/env python3
"""
Deployment Validation Example

This example demonstrates how to use the deployment validation engine
to check deployment readiness for different environments.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.deployment_validator import DeploymentValidator, validate_deployment


async def basic_validation_example():
    """Basic deployment validation example."""
    print("="*60)
    print("BASIC DEPLOYMENT VALIDATION EXAMPLE")
    print("="*60)
    
    # Run basic validation for development environment
    results = await validate_deployment(
        project_root=".",
        environment="development"
    )
    
    print(f"Environment: {results.environment}")
    print(f"Deployment Ready: {results.deployment_ready}")
    print(f"Overall Score: {results.overall_score:.1f}/100")
    print(f"Recommendations: {len(results.recommendations)}")
    
    if results.recommendations:
        print("\nTop Recommendations:")
        for i, rec in enumerate(results.recommendations[:3], 1):
            print(f"  {i}. {rec}")


async def comprehensive_validation_example():
    """Comprehensive deployment validation example."""
    print("\n" + "="*60)
    print("COMPREHENSIVE DEPLOYMENT VALIDATION EXAMPLE")
    print("="*60)
    
    validator = DeploymentValidator(".")
    
    # Run validation for different environments
    environments = ["development", "staging", "production"]
    
    for env in environments:
        print(f"\n--- {env.upper()} ENVIRONMENT ---")
        
        results = await validator.validate_deployment_readiness(
            environment=env,
            validate_k8s=True,
            validate_helm=True,
            validate_network=True,
            validate_secrets=True
        )
        
        print(f"Deployment Ready: {'✅' if results.deployment_ready else '❌'}")
        print(f"Overall Score: {results.overall_score:.1f}/100")
        
        # Show validation component scores
        k8s = results.kubernetes_validation
        network = results.network_security
        secrets = results.secrets_validation
        
        print(f"Kubernetes: {'✅' if k8s.manifest_syntax_valid else '❌'}")
        print(f"Network Security: {'✅' if network.tls_configured else '❌'}")
        print(f"Secrets Management: {'✅' if secrets.no_hardcoded_secrets else '❌'}")
        
        if not results.deployment_ready:
            print(f"Blocking Issues: {len([r for r in results.recommendations if 'CRITICAL' in r])}")


async def selective_validation_example():
    """Selective validation example."""
    print("\n" + "="*60)
    print("SELECTIVE VALIDATION EXAMPLE")
    print("="*60)
    
    validator = DeploymentValidator(".")
    
    # Run only security-related validations
    print("\n--- SECURITY-FOCUSED VALIDATION ---")
    results = await validator.validate_deployment_readiness(
        environment="production",
        validate_k8s=False,
        validate_helm=False,
        validate_network=True,
        validate_secrets=True
    )
    
    print(f"Network Security Valid: {results.network_security.tls_configured}")
    print(f"No Hardcoded Secrets: {results.secrets_validation.no_hardcoded_secrets}")
    print(f"Secrets Externalized: {results.secrets_validation.secrets_externalized}")
    
    # Run only Kubernetes validations
    print("\n--- KUBERNETES-FOCUSED VALIDATION ---")
    results = await validator.validate_deployment_readiness(
        environment="development",
        validate_k8s=True,
        validate_helm=True,
        validate_network=False,
        validate_secrets=False
    )
    
    print(f"Manifest Syntax Valid: {results.kubernetes_validation.manifest_syntax_valid}")
    print(f"Best Practices Followed: {results.kubernetes_validation.best_practices_followed}")
    
    if results.helm_validation:
        print(f"Helm Templates Valid: {results.helm_validation.template_syntax_valid}")


async def error_handling_example():
    """Error handling example."""
    print("\n" + "="*60)
    print("ERROR HANDLING EXAMPLE")
    print("="*60)
    
    try:
        # Try to validate a non-existent project
        validator = DeploymentValidator("/non/existent/path")
        results = await validator.validate_deployment_readiness()
        
        print(f"Validation completed with score: {results.overall_score}")
        
        # Check for validation errors
        all_errors = []
        all_errors.extend(results.kubernetes_validation.validation_errors)
        all_errors.extend(results.network_security.validation_errors)
        all_errors.extend(results.secrets_validation.validation_errors)
        
        if results.helm_validation:
            all_errors.extend(results.helm_validation.validation_errors)
        
        print(f"Total validation errors: {len(all_errors)}")
        
        if all_errors:
            print("Sample errors:")
            for error in all_errors[:3]:
                print(f"  - {error.message}")
    
    except Exception as e:
        print(f"Validation failed with exception: {e}")


async def deployment_readiness_check_example():
    """Deployment readiness check example matching the original requirements."""
    print("\n" + "="*60)
    print("DEPLOYMENT READINESS CHECK EXAMPLE")
    print("="*60)
    
    validator = DeploymentValidator(".")
    
    # Check all the deployment readiness criteria from the original prompt
    results = await validator.validate_deployment_readiness(environment="production")
    
    checks = [
        {
            "name": "Environment variables defined and stored securely",
            "status": results.secrets_validation.environment_vars_configured and results.secrets_validation.secrets_externalized,
            "action": "Add environment variables to secret manager" if not (results.secrets_validation.environment_vars_configured and results.secrets_validation.secrets_externalized) else "Proceed"
        },
        {
            "name": "Kubernetes manifests validated",
            "status": results.kubernetes_validation.manifest_syntax_valid,
            "action": "Fix manifest syntax errors" if not results.kubernetes_validation.manifest_syntax_valid else "Proceed"
        },
        {
            "name": "Network security policies configured",
            "status": results.network_security.network_policies_configured,
            "action": "Configure network policies" if not results.network_security.network_policies_configured else "Proceed"
        },
        {
            "name": "HTTPS/TLS enabled and certificates valid",
            "status": results.network_security.tls_configured,
            "action": "Configure TLS certificates" if not results.network_security.tls_configured else "Proceed"
        },
        {
            "name": "Security scans clean of critical issues",
            "status": results.secrets_validation.no_hardcoded_secrets,
            "action": "Remove hardcoded secrets" if not results.secrets_validation.no_hardcoded_secrets else "Proceed"
        },
        {
            "name": "Best practices followed",
            "status": results.kubernetes_validation.best_practices_followed,
            "action": "Follow Kubernetes best practices" if not results.kubernetes_validation.best_practices_followed else "Proceed"
        }
    ]
    
    print(f"\nDeployment Readiness Assessment:")
    print(f"Overall Status: {'✅ APPROVED' if results.deployment_ready else '❌ BLOCKED'}")
    print(f"Overall Score: {results.overall_score:.1f}/100")
    
    print(f"\nDetailed Checks:")
    for check in checks:
        status_icon = "✅" if check["status"] else "❌"
        print(f"  {status_icon} {check['name']}")
        if not check["status"]:
            print(f"     Action: {check['action']}")
    
    if results.deployment_ready:
        print(f"\n✅ Deployment Readiness: APPROVED")
        print(f"Action: Proceed with deployment.")
    else:
        print(f"\n❌ Deployment Readiness: BLOCKED")
        print(f"Action: Address the failed checks above before proceeding with production rollout.")


async def main():
    """Run all deployment validation examples."""
    print("DEPLOYMENT VALIDATION ENGINE EXAMPLES")
    print("="*80)
    
    try:
        await basic_validation_example()
        await comprehensive_validation_example()
        await selective_validation_example()
        await error_handling_example()
        await deployment_readiness_check_example()
        
        print(f"\n" + "="*80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"Example execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())