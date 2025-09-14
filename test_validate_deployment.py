#!/usr/bin/env python3
"""
Test script for the validate_deployment convenience function.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path to import the module
sys.path.insert(0, os.getcwd())

from services.deployment_validator import validate_deployment, DeploymentValidationResults


async def test_validate_deployment_default():
    """Test validate_deployment with default parameters."""
    print("Testing validate_deployment with default parameters...")

    try:
        results = await validate_deployment()

        # Verify return type
        assert isinstance(results, DeploymentValidationResults), f"Expected DeploymentValidationResults, got {type(results)}"

        # Verify required fields exist
        assert hasattr(results, 'deployment_ready'), "Missing deployment_ready field"
        assert hasattr(results, 'overall_score'), "Missing overall_score field"
        assert hasattr(results, 'environment'), "Missing environment field"
        assert hasattr(results, 'recommendations'), "Missing recommendations field"
        assert hasattr(results, 'kubernetes_validation'), "Missing kubernetes_validation field"
        assert hasattr(results, 'network_security'), "Missing network_security field"
        assert hasattr(results, 'secrets_validation'), "Missing secrets_validation field"

        # Verify field types
        assert isinstance(results.deployment_ready, bool), f"deployment_ready should be bool, got {type(results.deployment_ready)}"
        assert isinstance(results.overall_score, (int, float)), f"overall_score should be numeric, got {type(results.overall_score)}"
        assert isinstance(results.environment, str), f"environment should be str, got {type(results.environment)}"
        assert isinstance(results.recommendations, list), f"recommendations should be list, got {type(results.recommendations)}"

        print("✓ Default parameters test passed")
        print(f"  - Environment: {results.environment}")
        print(f"  - Deployment ready: {results.deployment_ready}")
        print(".1f")
        print(f"  - Recommendations count: {len(results.recommendations)}")

        return True

    except Exception as e:
        print(f"✗ Default parameters test failed: {e}")
        return False


async def test_validate_deployment_custom_params():
    """Test validate_deployment with custom parameters."""
    print("\nTesting validate_deployment with custom parameters...")

    try:
        # Test with custom environment and selective validation
        results = await validate_deployment(
            project_root=".",
            environment="staging",
            validate_k8s=True,
            validate_helm=False,  # Skip Helm validation
            validate_network=True,
            validate_secrets=True
        )

        # Verify return type
        assert isinstance(results, DeploymentValidationResults), f"Expected DeploymentValidationResults, got {type(results)}"

        # Verify environment is set correctly
        assert results.environment == "staging", f"Expected environment 'staging', got '{results.environment}'"

        # Verify Helm results are default (since validation was skipped)
        if results.helm_validation:
            # Should have default results indicating validation was skipped
            assert len(results.helm_validation.validation_warnings) > 0, "Expected warnings for skipped Helm validation"

        print("✓ Custom parameters test passed")
        print(f"  - Environment: {results.environment}")
        print(f"  - Deployment ready: {results.deployment_ready}")
        print(".1f")

        return True

    except Exception as e:
        print(f"✗ Custom parameters test failed: {e}")
        return False


async def test_validate_deployment_error_handling():
    """Test validate_deployment error handling."""
    print("\nTesting validate_deployment error handling...")

    try:
        # Test with invalid project root
        results = await validate_deployment(project_root="/nonexistent/path")

        # Should still return results (graceful error handling)
        assert isinstance(results, DeploymentValidationResults), f"Expected DeploymentValidationResults, got {type(results)}"

        print("✓ Error handling test passed")
        print(f"  - Deployment ready: {results.deployment_ready}")
        print(f"  - Has validation errors: {len(results.kubernetes_validation.validation_errors) > 0}")

        return True

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


async def test_validate_deployment_selective_validation():
    """Test validate_deployment with selective validation flags."""
    print("\nTesting validate_deployment with selective validation...")

    try:
        # Test skipping all validations except network
        results = await validate_deployment(
            validate_k8s=False,
            validate_helm=False,
            validate_network=True,
            validate_secrets=False
        )

        # Verify return type
        assert isinstance(results, DeploymentValidationResults), f"Expected DeploymentValidationResults, got {type(results)}"

        # Verify K8s results are default (validation skipped)
        assert len(results.kubernetes_validation.validation_warnings) > 0, "Expected warnings for skipped K8s validation"

        # Verify network validation was performed
        assert hasattr(results.network_security, 'tls_configured'), "Network validation should have been performed"

        print("✓ Selective validation test passed")
        print(f"  - K8s validation skipped: {len(results.kubernetes_validation.validation_warnings) > 0}")
        print(f"  - Network validation performed: {hasattr(results.network_security, 'tls_configured')}")

        return True

    except Exception as e:
        print(f"✗ Selective validation test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Starting comprehensive testing of validate_deployment function...\n")

    tests = [
        test_validate_deployment_default,
        test_validate_deployment_custom_params,
        test_validate_deployment_error_handling,
        test_validate_deployment_selective_validation
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if await test():
            passed += 1

    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The validate_deployment function is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
