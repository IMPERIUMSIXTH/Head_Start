"""
Tests for the Deployment Validation Engine

This module tests the comprehensive deployment validation capabilities including
Kubernetes manifest validation, Helm template validation, environment configuration
validation, and network security policy validation.
"""

import asyncio
import tempfile
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from services.deployment_validator import (
    DeploymentValidator,
    DeploymentValidationResults,
    KubernetesValidationResults,
    HelmValidationResults,
    NetworkSecurityResults,
    SecretsValidationResults,
    ValidationResult,
    validate_deployment
)


class TestDeploymentValidator:
    """Test cases for DeploymentValidator class."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create basic project structure
            (project_path / "k8s").mkdir()
            (project_path / "helm").mkdir()
            
            # Create a basic docker-compose.yml
            docker_compose_content = {
                'version': '3.8',
                'services': {
                    'backend': {
                        'build': '.',
                        'ports': ['8000:8000'],
                        'environment': ['DATABASE_URL=postgresql://user:pass@db:5432/app']
                    }
                }
            }
            with open(project_path / "docker-compose.yml", 'w') as f:
                yaml.dump(docker_compose_content, f)
            
            # Create .env.example
            with open(project_path / ".env.example", 'w') as f:
                f.write("DATABASE_URL=postgresql://user:${DB_PASSWORD}@localhost:5432/app\n")
                f.write("REDIS_URL=redis://localhost:6379/0\n")
                f.write("JWT_SECRET=${JWT_SECRET}\n")
                f.write("CELERY_BROKER_URL=redis://localhost:6379/1\n")
                f.write("CELERY_RESULT_BACKEND=redis://localhost:6379/2\n")
            
            yield project_path
    
    @pytest.fixture
    def deployment_validator(self, temp_project_dir):
        """Create a DeploymentValidator instance for testing."""
        return DeploymentValidator(str(temp_project_dir))
    
    @pytest.mark.asyncio
    async def test_validate_deployment_readiness_basic(self, deployment_validator):
        """Test basic deployment readiness validation."""
        results = await deployment_validator.validate_deployment_readiness(
            environment="development"
        )
        
        assert isinstance(results, DeploymentValidationResults)
        assert results.environment == "development"
        assert isinstance(results.overall_score, float)
        assert 0.0 <= results.overall_score <= 100.0
        assert isinstance(results.deployment_ready, bool)
        assert isinstance(results.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_validate_deployment_readiness_production(self, deployment_validator):
        """Test deployment readiness validation for production environment."""
        results = await deployment_validator.validate_deployment_readiness(
            environment="production"
        )
        
        assert results.environment == "production"
        # Production should have stricter requirements
        assert len(results.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_kubernetes_validation_no_manifests(self, deployment_validator):
        """Test Kubernetes validation when no manifests are present."""
        k8s_results = await deployment_validator._validate_kubernetes_manifests()
        
        assert isinstance(k8s_results, KubernetesValidationResults)
        # Should handle gracefully when no manifests are found
        assert len(k8s_results.validation_warnings) > 0
    
    @pytest.mark.asyncio
    async def test_kubernetes_validation_with_manifests(self, deployment_validator, temp_project_dir):
        """Test Kubernetes validation with manifest files."""
        # Create a sample Kubernetes manifest
        manifest_content = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {'name': 'test-app'},
            'spec': {
                'replicas': 1,
                'selector': {'matchLabels': {'app': 'test-app'}},
                'template': {
                    'metadata': {'labels': {'app': 'test-app'}},
                    'spec': {
                        'containers': [{
                            'name': 'test-app',
                            'image': 'test:latest',
                            'ports': [{'containerPort': 8000}]
                        }]
                    }
                }
            }
        }
        
        manifest_path = temp_project_dir / "k8s" / "deployment.yaml"
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest_content, f)
        
        k8s_results = await deployment_validator._validate_kubernetes_manifests()
        
        assert isinstance(k8s_results, KubernetesValidationResults)
        assert k8s_results.manifest_syntax_valid
        # Should have warnings about missing resource limits and health checks
        assert len(k8s_results.validation_warnings) > 0
    
    @pytest.mark.asyncio
    async def test_helm_validation_no_charts(self, deployment_validator):
        """Test Helm validation when no charts are present."""
        helm_results = await deployment_validator._validate_helm_templates()
        
        assert isinstance(helm_results, HelmValidationResults)
        assert helm_results.template_syntax_valid
        assert helm_results.chart_structure_valid
        assert len(helm_results.validation_warnings) > 0
    
    @pytest.mark.asyncio
    async def test_helm_validation_with_chart(self, deployment_validator, temp_project_dir):
        """Test Helm validation with a chart."""
        # Create a sample Helm chart
        chart_dir = temp_project_dir / "helm" / "test-chart"
        chart_dir.mkdir()
        
        # Create Chart.yaml
        chart_yaml = {
            'name': 'test-chart',
            'version': '1.0.0',
            'description': 'A test chart'
        }
        with open(chart_dir / "Chart.yaml", 'w') as f:
            yaml.dump(chart_yaml, f)
        
        # Create values.yaml
        values_yaml = {'replicaCount': 1}
        with open(chart_dir / "values.yaml", 'w') as f:
            yaml.dump(values_yaml, f)
        
        helm_results = await deployment_validator._validate_helm_templates()
        
        assert isinstance(helm_results, HelmValidationResults)
        assert helm_results.chart_structure_valid
    
    @pytest.mark.asyncio
    async def test_network_security_validation(self, deployment_validator):
        """Test network security validation."""
        network_results = await deployment_validator._validate_network_security()
        
        assert isinstance(network_results, NetworkSecurityResults)
        # Should have warnings about missing network policies and TLS
        assert len(network_results.validation_warnings) > 0
    
    @pytest.mark.asyncio
    async def test_secrets_validation_development(self, deployment_validator):
        """Test secrets validation for development environment."""
        secrets_results = await deployment_validator._validate_secrets_management("development")
        
        assert isinstance(secrets_results, SecretsValidationResults)
        assert secrets_results.environment_vars_configured
        assert secrets_results.no_hardcoded_secrets
    
    @pytest.mark.asyncio
    async def test_secrets_validation_production(self, deployment_validator, temp_project_dir):
        """Test secrets validation for production environment."""
        # Create a .env file (should trigger warning in production)
        with open(temp_project_dir / ".env", 'w') as f:
            f.write("DATABASE_URL=postgresql://user:pass@localhost:5432/app\n")
        
        secrets_results = await deployment_validator._validate_secrets_management("production")
        
        assert isinstance(secrets_results, SecretsValidationResults)
        # Should have warnings about .env file in production
        assert len(secrets_results.validation_warnings) > 0
    
    @pytest.mark.asyncio
    async def test_hardcoded_secrets_detection(self, deployment_validator, temp_project_dir):
        """Test detection of hardcoded secrets."""
        # Create a file with hardcoded secrets
        test_file = temp_project_dir / "config.py"
        with open(test_file, 'w') as f:
            f.write('password = "hardcoded_password"\n')
            f.write('api_key = "sk-1234567890abcdef"\n')
        
        hardcoded_secrets = await deployment_validator._scan_for_hardcoded_secrets()
        
        assert len(hardcoded_secrets) > 0
        assert any('password' in secret['content'] for secret in hardcoded_secrets)
    
    @pytest.mark.asyncio
    async def test_kubectl_availability_check(self, deployment_validator):
        """Test kubectl availability check."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful kubectl check
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b'', b'')
            mock_subprocess.return_value = mock_process
            
            result = await deployment_validator._check_kubectl_available()
            assert result is True
            
            # Mock failed kubectl check
            mock_process.returncode = 1
            result = await deployment_validator._check_kubectl_available()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_kubeval_validation(self, deployment_validator, temp_project_dir):
        """Test kubeval validation integration."""
        # Create a test manifest
        manifest_content = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'name': 'test-pod'},
            'spec': {
                'containers': [{
                    'name': 'test-container',
                    'image': 'nginx:latest'
                }]
            }
        }
        
        manifest_path = temp_project_dir / "test-manifest.yaml"
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest_content, f)
        
        errors = []
        warnings = []
        
        # Test with kubeval available
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock kubeval version check (success)
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b'kubeval version', b'')
            mock_subprocess.return_value = mock_process
            
            await deployment_validator._run_kubeval_validation(manifest_path, errors, warnings)
            
            # Should have called kubeval twice (version check + validation)
            assert mock_subprocess.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_helm_lint_validation(self, deployment_validator, temp_project_dir):
        """Test Helm lint validation."""
        # Create a basic Helm chart structure
        chart_dir = temp_project_dir / "test-chart"
        chart_dir.mkdir()
        
        chart_yaml = {
            'name': 'test-chart',
            'version': '1.0.0',
            'description': 'Test chart'
        }
        with open(chart_dir / "Chart.yaml", 'w') as f:
            yaml.dump(chart_yaml, f)
        
        errors = []
        warnings = []
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful helm lint
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b'==> Linting test-chart\n1 chart(s) linted, 0 chart(s) failed', b'')
            mock_subprocess.return_value = mock_process
            
            await deployment_validator._run_helm_lint_validation(chart_dir, errors, warnings)
            
            assert len(errors) == 0
            mock_subprocess.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tls_certificate_validation(self, deployment_validator, temp_project_dir):
        """Test TLS certificate validation."""
        # Create a mock certificate directory
        cert_dir = temp_project_dir / "certs"
        cert_dir.mkdir()
        
        # Create a mock certificate file
        cert_file = cert_dir / "server.crt"
        with open(cert_file, 'w') as f:
            f.write("-----BEGIN CERTIFICATE-----\nMOCK_CERT_DATA\n-----END CERTIFICATE-----")
        
        cert_validation = await deployment_validator._validate_tls_certificates()
        
        assert isinstance(cert_validation, dict)
        assert "valid" in cert_validation
        assert "warnings" in cert_validation
    
    @pytest.mark.asyncio
    async def test_best_practices_validation(self, deployment_validator, temp_project_dir):
        """Test Kubernetes best practices validation."""
        # Create a deployment without best practices
        deployment_resource = {
            'kind': 'Deployment',
            'metadata': {'name': 'test-app'},  # Missing recommended labels
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{
                            'name': 'test-container',
                            'image': 'test:latest'
                            # Missing resource limits, health checks, security context
                        }]
                    }
                }
            }
        }
        
        manifest_file = temp_project_dir / "deployment.yaml"
        errors = []
        warnings = []
        
        await deployment_validator._validate_k8s_best_practices(
            deployment_resource, manifest_file, errors, warnings
        )
        
        # Should have multiple warnings for missing best practices
        assert len(warnings) > 0
        warning_messages = [w.message for w in warnings]
        assert any("missing recommended labels" in msg for msg in warning_messages)
        assert any("missing resource limits" in msg for msg in warning_messages)
    
    @pytest.mark.asyncio
    async def test_environment_specific_validation(self, deployment_validator):
        """Test environment-specific validation requirements."""
        # Test production environment (stricter requirements)
        prod_results = await deployment_validator.validate_deployment_readiness(
            environment="production"
        )
        
        # Test development environment (more lenient)
        dev_results = await deployment_validator.validate_deployment_readiness(
            environment="development"
        )
        
        # Production should have more recommendations
        assert len(prod_results.recommendations) >= len(dev_results.recommendations)
        
        # Both should complete without errors
        assert isinstance(prod_results, DeploymentValidationResults)
        assert isinstance(dev_results, DeploymentValidationResults)
    
    @pytest.mark.asyncio
    async def test_helm_availability_check(self, deployment_validator):
        """Test helm availability check."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful helm check
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b'', b'')
            mock_subprocess.return_value = mock_process
            
            result = await deployment_validator._check_helm_available()
            assert result is True
            
            # Mock failed helm check
            mock_process.returncode = 1
            result = await deployment_validator._check_helm_available()
            assert result is False
    
    def test_deployment_readiness_scoring(self, deployment_validator):
        """Test deployment readiness scoring logic."""
        # Create mock results
        k8s_results = KubernetesValidationResults(
            manifest_syntax_valid=True,
            resource_quotas_valid=True,
            security_policies_valid=False,
            best_practices_followed=False
        )
        
        network_results = NetworkSecurityResults(
            network_policies_configured=False,
            least_privilege_enforced=False,
            tls_configured=False,
            ingress_security_valid=False,
            service_mesh_configured=False
        )
        
        secrets_results = SecretsValidationResults(
            secrets_externalized=True,
            environment_vars_configured=True,
            no_hardcoded_secrets=True,
            secret_rotation_configured=False
        )
        
        deployment_ready, overall_score, recommendations = deployment_validator._assess_deployment_readiness(
            k8s_results, None, network_results, secrets_results, "development"
        )
        
        assert isinstance(deployment_ready, bool)
        assert isinstance(overall_score, float)
        assert isinstance(recommendations, list)
        assert 0.0 <= overall_score <= 100.0
    
    def test_production_deployment_requirements(self, deployment_validator):
        """Test that production deployment has stricter requirements."""
        # Create results with security issues
        secrets_results = SecretsValidationResults(
            secrets_externalized=True,
            environment_vars_configured=True,
            no_hardcoded_secrets=False,  # Critical issue
            secret_rotation_configured=False
        )
        
        k8s_results = KubernetesValidationResults(
            manifest_syntax_valid=True,
            resource_quotas_valid=True,
            security_policies_valid=True,
            best_practices_followed=True
        )
        
        network_results = NetworkSecurityResults(
            network_policies_configured=True,
            least_privilege_enforced=True,
            tls_configured=False,  # Missing TLS
            ingress_security_valid=False,
            service_mesh_configured=False
        )
        
        # Should block production deployment
        deployment_ready, _, _ = deployment_validator._assess_deployment_readiness(
            k8s_results, None, network_results, secrets_results, "production"
        )
        
        assert deployment_ready is False
    
    def test_development_deployment_leniency(self, deployment_validator):
        """Test that development deployment is more lenient."""
        # Create results with some issues
        secrets_results = SecretsValidationResults(
            secrets_externalized=True,
            environment_vars_configured=True,
            no_hardcoded_secrets=True,  # No critical issues
            secret_rotation_configured=False
        )
        
        k8s_results = KubernetesValidationResults(
            manifest_syntax_valid=True,
            resource_quotas_valid=False,
            security_policies_valid=False,
            best_practices_followed=False
        )
        
        network_results = NetworkSecurityResults(
            network_policies_configured=False,
            least_privilege_enforced=False,
            tls_configured=False,
            ingress_security_valid=False,
            service_mesh_configured=False
        )
        
        # Should allow development deployment
        deployment_ready, _, _ = deployment_validator._assess_deployment_readiness(
            k8s_results, None, network_results, secrets_results, "development"
        )
        
        assert deployment_ready is True
    
    @pytest.mark.asyncio
    async def test_validate_deployment_convenience_function(self, temp_project_dir):
        """Test the convenience function for deployment validation."""
        results = await validate_deployment(
            project_root=str(temp_project_dir),
            environment="development"
        )
        
        assert isinstance(results, DeploymentValidationResults)
        assert results.environment == "development"
    
    @pytest.mark.asyncio
    async def test_selective_validation(self, deployment_validator):
        """Test selective validation (skipping certain validations)."""
        results = await deployment_validator.validate_deployment_readiness(
            environment="development",
            validate_k8s=False,
            validate_helm=False,
            validate_network=True,
            validate_secrets=True
        )
        
        assert isinstance(results, DeploymentValidationResults)
        # Should have default results for skipped validations
        assert results.kubernetes_validation is not None
        assert results.helm_validation is not None
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation and properties."""
        result = ValidationResult(
            passed=False,
            message="Test validation failed",
            details={"error_code": "TEST001"},
            severity="error"
        )
        
        assert result.passed is False
        assert result.message == "Test validation failed"
        assert result.details["error_code"] == "TEST001"
        assert result.severity == "error"
    
    def test_kubernetes_resource_validation(self, deployment_validator):
        """Test individual Kubernetes resource validation."""
        # Test deployment resource
        deployment_resource = {
            'kind': 'Deployment',
            'metadata': {'name': 'test-app'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{
                            'name': 'test-container',
                            'image': 'test:latest'
                        }]
                    }
                }
            }
        }
        
        errors = []
        warnings = []
        
        # This should run without exceptions
        asyncio.run(deployment_validator._validate_k8s_resource(
            deployment_resource, errors, warnings
        ))
        
        # Should have warnings about missing resource limits and health checks
        assert len(warnings) > 0
    
    def test_environment_variable_validation(self, deployment_validator):
        """Test environment variable validation logic."""
        # Test development environment
        result = deployment_validator._validate_environment_variables("development")
        assert isinstance(result, dict)
        assert "valid" in result
        assert "errors" in result
        
        # Test production environment (should be stricter)
        result = deployment_validator._validate_environment_variables("production")
        assert isinstance(result, dict)


class TestDeploymentValidationIntegration:
    """Integration tests for deployment validation."""
    
    @pytest.mark.asyncio
    async def test_full_deployment_validation_pipeline(self):
        """Test the complete deployment validation pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a realistic project structure
            (project_path / "k8s").mkdir()
            (project_path / "src").mkdir()
            
            # Create docker-compose.yml
            docker_compose = {
                'version': '3.8',
                'services': {
                    'backend': {
                        'build': '.',
                        'environment': {
                            'DATABASE_URL': '${DATABASE_URL}',
                            'REDIS_URL': '${REDIS_URL}'
                        }
                    }
                }
            }
            with open(project_path / "docker-compose.yml", 'w') as f:
                yaml.dump(docker_compose, f)
            
            # Create .env.example
            with open(project_path / ".env.example", 'w') as f:
                f.write("DATABASE_URL=postgresql://user:pass@localhost:5432/app\n")
                f.write("REDIS_URL=redis://localhost:6379/0\n")
                f.write("JWT_SECRET=your-secret-key\n")
                f.write("CELERY_BROKER_URL=redis://localhost:6379/1\n")
                f.write("CELERY_RESULT_BACKEND=redis://localhost:6379/2\n")
            
            # Create a Kubernetes deployment
            k8s_deployment = {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {'name': 'backend'},
                'spec': {
                    'replicas': 2,
                    'selector': {'matchLabels': {'app': 'backend'}},
                    'template': {
                        'metadata': {'labels': {'app': 'backend'}},
                        'spec': {
                            'containers': [{
                                'name': 'backend',
                                'image': 'backend:latest',
                                'ports': [{'containerPort': 8000}],
                                'resources': {
                                    'requests': {'memory': '256Mi', 'cpu': '250m'},
                                    'limits': {'memory': '512Mi', 'cpu': '500m'}
                                },
                                'livenessProbe': {
                                    'httpGet': {'path': '/health', 'port': 8000},
                                    'initialDelaySeconds': 30
                                },
                                'readinessProbe': {
                                    'httpGet': {'path': '/ready', 'port': 8000},
                                    'initialDelaySeconds': 5
                                }
                            }]
                        }
                    }
                }
            }
            
            with open(project_path / "k8s" / "deployment.yaml", 'w') as f:
                yaml.dump(k8s_deployment, f)
            
            # Run full validation
            validator = DeploymentValidator(str(project_path))
            results = await validator.validate_deployment_readiness(
                environment="staging"
            )
            
            # Verify results
            assert isinstance(results, DeploymentValidationResults)
            assert results.environment == "staging"
            assert results.kubernetes_validation.manifest_syntax_valid
            assert results.kubernetes_validation.best_practices_followed
            assert results.secrets_validation.no_hardcoded_secrets
            assert results.overall_score > 0.0
    
    @pytest.mark.asyncio
    async def test_deployment_validation_with_errors(self):
        """Test deployment validation with various error conditions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create invalid Kubernetes manifest
            (project_path / "k8s").mkdir()
            with open(project_path / "k8s" / "invalid.yaml", 'w') as f:
                f.write("invalid: yaml: content: [")
            
            # Create file with hardcoded secrets
            with open(project_path / "config.py", 'w') as f:
                f.write('password = "hardcoded_secret"\n')
            
            # Run validation
            validator = DeploymentValidator(str(project_path))
            results = await validator.validate_deployment_readiness(
                environment="production"
            )
            
            # Should have errors and not be ready for deployment
            assert not results.deployment_ready
            assert len(results.kubernetes_validation.validation_errors) > 0
            assert not results.secrets_validation.no_hardcoded_secrets
            assert results.overall_score < 50.0


if __name__ == "__main__":
    pytest.main([__file__])


class TestDeploymentValidationEnhancements:
    """Test cases for enhanced deployment validation features."""
    
    @pytest.fixture
    def enhanced_project_dir(self):
        """Create an enhanced project directory with comprehensive test fixtures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create Kubernetes manifests with various configurations
            k8s_dir = project_path / "k8s"
            k8s_dir.mkdir()
            
            # Create a comprehensive deployment manifest
            deployment_manifest = {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': 'backend-app',
                    'labels': {
                        'app': 'backend',
                        'version': 'v1.0.0',
                        'component': 'api'
                    }
                },
                'spec': {
                    'replicas': 3,
                    'selector': {'matchLabels': {'app': 'backend'}},
                    'template': {
                        'metadata': {'labels': {'app': 'backend'}},
                        'spec': {
                            'securityContext': {
                                'runAsNonRoot': True,
                                'runAsUser': 1000,
                                'fsGroup': 2000
                            },
                            'containers': [{
                                'name': 'backend',
                                'image': 'backend:v1.0.0',
                                'ports': [{'containerPort': 8000}],
                                'resources': {
                                    'requests': {'memory': '256Mi', 'cpu': '250m'},
                                    'limits': {'memory': '512Mi', 'cpu': '500m'}
                                },
                                'livenessProbe': {
                                    'httpGet': {'path': '/health', 'port': 8000},
                                    'initialDelaySeconds': 30,
                                    'periodSeconds': 10
                                },
                                'readinessProbe': {
                                    'httpGet': {'path': '/ready', 'port': 8000},
                                    'initialDelaySeconds': 5,
                                    'periodSeconds': 5
                                },
                                'securityContext': {
                                    'allowPrivilegeEscalation': False,
                                    'readOnlyRootFilesystem': True,
                                    'capabilities': {'drop': ['ALL']}
                                }
                            }]
                        }
                    }
                }
            }
            
            with open(k8s_dir / "deployment.yaml", 'w') as f:
                yaml.dump(deployment_manifest, f)
            
            # Create a network policy
            network_policy = {
                'apiVersion': 'networking.k8s.io/v1',
                'kind': 'NetworkPolicy',
                'metadata': {'name': 'backend-netpol'},
                'spec': {
                    'podSelector': {'matchLabels': {'app': 'backend'}},
                    'policyTypes': ['Ingress', 'Egress'],
                    'ingress': [{
                        'from': [{'podSelector': {'matchLabels': {'app': 'frontend'}}}],
                        'ports': [{'protocol': 'TCP', 'port': 8000}]
                    }],
                    'egress': [{
                        'to': [{'podSelector': {'matchLabels': {'app': 'database'}}}],
                        'ports': [{'protocol': 'TCP', 'port': 5432}]
                    }]
                }
            }
            
            with open(k8s_dir / "network-policy.yaml", 'w') as f:
                yaml.dump(network_policy, f)
            
            # Create an Ingress with TLS
            ingress_manifest = {
                'apiVersion': 'networking.k8s.io/v1',
                'kind': 'Ingress',
                'metadata': {'name': 'backend-ingress'},
                'spec': {
                    'tls': [{
                        'hosts': ['api.example.com'],
                        'secretName': 'backend-tls'
                    }],
                    'rules': [{
                        'host': 'api.example.com',
                        'http': {
                            'paths': [{
                                'path': '/',
                                'pathType': 'Prefix',
                                'backend': {
                                    'service': {
                                        'name': 'backend-service',
                                        'port': {'number': 8000}
                                    }
                                }
                            }]
                        }
                    }]
                }
            }
            
            with open(k8s_dir / "ingress.yaml", 'w') as f:
                yaml.dump(ingress_manifest, f)
            
            # Create a TLS secret
            tls_secret = {
                'apiVersion': 'v1',
                'kind': 'Secret',
                'type': 'kubernetes.io/tls',
                'metadata': {'name': 'backend-tls'},
                'data': {
                    'tls.crt': 'LS0tLS1CRUdJTi==',  # Base64 encoded mock cert
                    'tls.key': 'LS0tLS1CRUdJTi=='   # Base64 encoded mock key
                }
            }
            
            with open(k8s_dir / "tls-secret.yaml", 'w') as f:
                yaml.dump(tls_secret, f)
            
            # Create Helm chart
            helm_dir = project_path / "helm" / "backend-chart"
            helm_dir.mkdir(parents=True)
            
            chart_yaml = {
                'apiVersion': 'v2',
                'name': 'backend-chart',
                'description': 'Backend application Helm chart',
                'version': '1.0.0',
                'appVersion': '1.0.0'
            }
            
            with open(helm_dir / "Chart.yaml", 'w') as f:
                yaml.dump(chart_yaml, f)
            
            values_yaml = {
                'replicaCount': 3,
                'image': {
                    'repository': 'backend',
                    'tag': 'v1.0.0',
                    'pullPolicy': 'IfNotPresent'
                },
                'service': {
                    'type': 'ClusterIP',
                    'port': 8000
                },
                'ingress': {
                    'enabled': True,
                    'className': 'nginx',
                    'hosts': [{'host': 'api.example.com', 'paths': [{'path': '/', 'pathType': 'Prefix'}]}],
                    'tls': [{'secretName': 'backend-tls', 'hosts': ['api.example.com']}]
                },
                'resources': {
                    'limits': {'cpu': '500m', 'memory': '512Mi'},
                    'requests': {'cpu': '250m', 'memory': '256Mi'}
                }
            }
            
            with open(helm_dir / "values.yaml", 'w') as f:
                yaml.dump(values_yaml, f)
            
            # Create templates directory with helper file
            templates_dir = helm_dir / "templates"
            templates_dir.mkdir()
            
            with open(templates_dir / "_helpers.tpl", 'w') as f:
                f.write('{{/* Common labels */}}\n{{- define "backend.labels" -}}\napp: {{ .Chart.Name }}\n{{- end }}\n')
            
            with open(templates_dir / "NOTES.txt", 'w') as f:
                f.write('Thank you for installing {{ .Chart.Name }}!\n')
            
            # Create certificate directory
            cert_dir = project_path / "certs"
            cert_dir.mkdir()
            
            with open(cert_dir / "server.crt", 'w') as f:
                f.write("-----BEGIN CERTIFICATE-----\nMIIC...MOCK_CERT_DATA...==\n-----END CERTIFICATE-----\n")
            
            # Create .env.example with comprehensive variables
            with open(project_path / ".env.example", 'w') as f:
                f.write("# Database Configuration\n")
                f.write("DATABASE_URL=postgresql://user:password@localhost:5432/app\n")
                f.write("DB_HOST=localhost\n")
                f.write("DB_PORT=5432\n")
                f.write("DB_NAME=app\n")
                f.write("DB_USER=user\n")
                f.write("DB_PASSWORD=password\n\n")
                f.write("# Redis Configuration\n")
                f.write("REDIS_URL=redis://localhost:6379/0\n")
                f.write("REDIS_HOST=localhost\n")
                f.write("REDIS_PORT=6379\n\n")
                f.write("# Security\n")
                f.write("JWT_SECRET=your-jwt-secret-key\n")
                f.write("JWT_ALGORITHM=HS256\n")
                f.write("JWT_EXPIRATION=3600\n\n")
                f.write("# Celery Configuration\n")
                f.write("CELERY_BROKER_URL=redis://localhost:6379/1\n")
                f.write("CELERY_RESULT_BACKEND=redis://localhost:6379/2\n\n")
                f.write("# Application Settings\n")
                f.write("DEBUG=false\n")
                f.write("LOG_LEVEL=INFO\n")
                f.write("API_HOST=0.0.0.0\n")
                f.write("API_PORT=8000\n")
            
            yield project_path
    
    @pytest.fixture
    def enhanced_deployment_validator(self, enhanced_project_dir):
        """Create a DeploymentValidator instance with enhanced test project."""
        return DeploymentValidator(str(enhanced_project_dir))
    
    @pytest.mark.asyncio
    async def test_comprehensive_deployment_validation(self, enhanced_deployment_validator):
        """Test comprehensive deployment validation with all features."""
        results = await enhanced_deployment_validator.validate_deployment_readiness(
            environment="production"
        )
        
        assert isinstance(results, DeploymentValidationResults)
        assert results.environment == "production"
        
        # Should have good scores due to comprehensive configuration
        assert results.overall_score > 70.0
        
        # Kubernetes validation should pass
        assert results.kubernetes_validation.manifest_syntax_valid
        assert results.kubernetes_validation.best_practices_followed
        
        # Network security should be configured
        assert results.network_security.network_policies_configured
        assert results.network_security.tls_configured
        
        # Secrets should be properly managed
        assert results.secrets_validation.no_hardcoded_secrets
        assert results.secrets_validation.environment_vars_configured
    
    @pytest.mark.asyncio
    async def test_helm_comprehensive_validation(self, enhanced_deployment_validator):
        """Test comprehensive Helm validation."""
        helm_results = await enhanced_deployment_validator._validate_helm_templates()
        
        assert isinstance(helm_results, HelmValidationResults)
        assert helm_results.chart_structure_valid
        assert helm_results.template_syntax_valid
        
        # Should have minimal warnings due to good chart structure
        assert len(helm_results.validation_errors) == 0
    
    @pytest.mark.asyncio
    async def test_network_security_comprehensive_validation(self, enhanced_deployment_validator):
        """Test comprehensive network security validation."""
        network_results = await enhanced_deployment_validator._validate_network_security()
        
        assert isinstance(network_results, NetworkSecurityResults)
        assert network_results.network_policies_configured
        assert network_results.least_privilege_enforced
        assert network_results.tls_configured
        assert network_results.ingress_security_valid
    
    @pytest.mark.asyncio
    async def test_production_deployment_requirements(self, enhanced_deployment_validator):
        """Test that production deployment meets all requirements."""
        results = await enhanced_deployment_validator.validate_deployment_readiness(
            environment="production"
        )
        
        # Production should be ready with comprehensive configuration
        assert results.deployment_ready
        assert results.overall_score >= 80.0
        
        # Should have minimal critical recommendations
        critical_recommendations = [r for r in results.recommendations if "CRITICAL" in r]
        assert len(critical_recommendations) == 0
    
    @pytest.mark.asyncio
    async def test_selective_validation_comprehensive(self, enhanced_deployment_validator):
        """Test selective validation with comprehensive project."""
        # Test with only Kubernetes validation
        results = await enhanced_deployment_validator.validate_deployment_readiness(
            environment="development",
            validate_k8s=True,
            validate_helm=False,
            validate_network=False,
            validate_secrets=False
        )
        
        assert results.kubernetes_validation.manifest_syntax_valid
        # Other validations should have default results
        assert len(results.helm_validation.validation_warnings) > 0  # Should indicate skipped
        assert len(results.network_security.validation_warnings) > 0  # Should indicate skipped
        assert len(results.secrets_validation.validation_warnings) > 0  # Should indicate skipped
    
    @pytest.mark.asyncio
    async def test_deployment_scoring_algorithm(self, enhanced_deployment_validator):
        """Test the deployment scoring algorithm."""
        # Create mock results with known values
        k8s_results = KubernetesValidationResults(
            manifest_syntax_valid=True,
            resource_quotas_valid=True,
            security_policies_valid=True,
            best_practices_followed=True
        )
        
        network_results = NetworkSecurityResults(
            network_policies_configured=True,
            least_privilege_enforced=True,
            tls_configured=True,
            ingress_security_valid=True,
            service_mesh_configured=False
        )
        
        secrets_results = SecretsValidationResults(
            secrets_externalized=True,
            environment_vars_configured=True,
            no_hardcoded_secrets=True,
            secret_rotation_configured=False
        )
        
        helm_results = HelmValidationResults(
            template_syntax_valid=True,
            values_schema_valid=True,
            chart_structure_valid=True,
            dependencies_resolved=True
        )
        
        deployment_ready, overall_score, recommendations = enhanced_deployment_validator._assess_deployment_readiness(
            k8s_results, helm_results, network_results, secrets_results, "production"
        )
        
        # Should be ready with high score
        assert deployment_ready
        assert overall_score >= 90.0
        assert isinstance(recommendations, list)
    
    def test_validation_result_serialization(self):
        """Test that validation results can be serialized to JSON."""
        result = ValidationResult(
            passed=True,
            message="Test validation passed",
            details={"test_key": "test_value"},
            severity="info"
        )
        
        # Should be able to convert to dict for JSON serialization
        result_dict = {
            "passed": result.passed,
            "message": result.message,
            "details": result.details,
            "severity": result.severity
        }
        
        assert result_dict["passed"] is True
        assert result_dict["message"] == "Test validation passed"
        assert result_dict["details"]["test_key"] == "test_value"
        assert result_dict["severity"] == "info"


class TestDeploymentValidationCLI:
    """Test cases for the deployment validation CLI script."""
    
    @pytest.mark.asyncio
    async def test_validate_deployment_convenience_function(self):
        """Test the convenience function for deployment validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create basic project structure
            project_path = Path(temp_dir)
            (project_path / ".env.example").touch()
            
            results = await validate_deployment(
                project_root=str(project_path),
                environment="development"
            )
            
            assert isinstance(results, DeploymentValidationResults)
            assert results.environment == "development"
    
    def test_deployment_validator_initialization(self):
        """Test DeploymentValidator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = DeploymentValidator(temp_dir)
            
            assert validator.project_root == Path(temp_dir)
            assert validator.k8s_manifests_path == Path(temp_dir) / "k8s"
            assert validator.helm_charts_path == Path(temp_dir) / "helm"
            assert validator.docker_compose_path == Path(temp_dir) / "docker-compose.yml"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])