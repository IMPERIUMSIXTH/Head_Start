#!/usr/bin/env python3
"""
Check deployment readiness using the convenience function.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

from services.deployment_validator import validate_deployment


async def check_readiness():
    """Check deployment readiness for different environments."""
    print("🔍 Checking deployment readiness...\n")

    environments = ["development", "staging", "production"]

    for env in environments:
        print(f"📋 Validating {env} environment:")
        print("-" * 40)

        try:
            results = await validate_deployment(environment=env)

            print(f"✅ Deployment Ready: {results.deployment_ready}")
            print(f"📊 Overall Score: {results.overall_score:.1f}")
            print(f"📅 Environment: {results.environment}")
            print(f"📝 Recommendations: {len(results.recommendations)}")

            if results.recommendations:
                print("\n💡 Recommendations:")
                for i, rec in enumerate(results.recommendations[:5], 1):  # Show first 5
                    print(f"   {i}. {rec}")
                if len(results.recommendations) > 5:
                    print(f"   ... and {len(results.recommendations) - 5} more")

            # Show validation status
            k8s_status = "✅" if results.kubernetes_validation.manifest_syntax_valid else "❌"
            helm_status = "✅" if results.helm_validation and results.helm_validation.template_syntax_valid else "⚠️"
            network_status = "✅" if results.network_security.tls_configured else "❌"
            secrets_status = "✅" if results.secrets_validation.no_hardcoded_secrets else "❌"

            print("\n🔧 Validation Status:")
            print(f"   Kubernetes: {k8s_status}")
            print(f"   Helm: {helm_status}")
            print(f"   Network Security: {network_status}")
            print(f"   Secrets Management: {secrets_status}")

        except Exception as e:
            print(f"❌ Validation failed: {e}")

        print("\n" + "="*50 + "\n")

    # Overall assessment
    print("🎯 DEPLOYMENT READINESS ASSESSMENT")
    print("="*50)

    # Run one more validation for development to get final assessment
    try:
        final_results = await validate_deployment(environment="development")

        if final_results.deployment_ready:
            print("🎉 DEPLOYMENT IS READY!")
            print("   All validations passed. You can proceed with deployment.")
        else:
            print("⚠️  DEPLOYMENT NEEDS ATTENTION")
            print("   Some validations failed. Review the recommendations above.")

        print(f"📊 Final Score: {final_results.overall_score:.1f}/100")
        print(f"🔍 Critical Issues: {len([r for r in final_results.recommendations if 'CRITICAL' in r])}")

    except Exception as e:
        print(f"❌ Could not complete readiness assessment: {e}")


if __name__ == "__main__":
    asyncio.run(check_readiness())
