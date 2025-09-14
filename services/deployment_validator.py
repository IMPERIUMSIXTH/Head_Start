"""
Deployment Validation Engine

This module provides comprehensive deployment validation capabilities including
Kubernetes manifest validation, Helm template validation, environment configuration
validation, and network security policy validation.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Base class for validation results."""
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info, warning, error, critical


@dataclass
class KubernetesValidationResults:
    """Results from Kubernetes manifest validation."""
    manifest_syntax_valid: bool
    resource_quotas_valid: bool
    security_policies_valid: bool
    best_practices_followed: bool
    validation_errors: List[ValidationResult] = field(default_factory=list)
    validation_warnings: List[ValidationResult] = field(default_factory=list)


@dataclass
class HelmValidationResults:
    """Results from Helm template validation."""
    template_syntax_valid: bool
    values_schema_valid: bool
    chart_structure_valid: bool
    dependencies_resolved: bool
    validation_errors: List[ValidationResult] = field(default_factory=list)
    validation_warnings: List[ValidationResult] = field(default_factory=list)


@dataclass
class NetworkSecurityResults:
    """Results from network security validation."""
    network_policies_configured: bool
    least_privilege_enforced: bool
    tls_configured: bool
    ingress_security_valid: bool
    service_mesh_configured: bool
    validation_errors: List[ValidationResult] = field(default_factory=list)
    validation_warnings: List[ValidationResult] = field(default_factory=list)


@dataclass
class SecretsValidationResults:
    """Results from secrets and environment validation."""
    secrets_externalized: bool
    environment_vars_configured: bool
    no_hardcoded_secrets: bool
    secret_rotation_configured: bool
    validation_errors: List[ValidationResult] = field(default_factory=list)
    validation_warnings: List[ValidationResult] = field(default_factory=list)


@dataclass
class DeploymentValidationResults:
    """Comprehensive deployment validation results."""
    kubernetes_validation: KubernetesValidationResults
    helm_validation: Optional[HelmValidationResults]
    network_security: NetworkSecurityResults
    secrets_validation: SecretsValidationResults
    deployment_ready: bool
    overall_score: float
    validation_timestamp: datetime = field(default_factory=datetime.now)
    environment: str = "development"
    recommendations: List[str] = field(default_factory=list)


class DeploymentValidator:
    """
    Comprehensive deployment validation engine that validates Kubernetes manifests,
    Helm charts, network security policies, and environment configurations.
    """
    
    def __init__(self, project_root: str = "."):
        """
        Initialize the deployment validator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        
        # Default paths for deployment artifacts
        self.k8s_manifests_path = self.project_root / "k8s"
        self.helm_charts_path = self.project_root / "helm"
        self.docker_compose_path = self.project_root / "docker-compose.yml"
        
    async def validate_deployment_readiness(
        self, 
        environment: str = "development",
        validate_k8s: bool = True,
        validate_helm: bool = True,
        validate_network: bool = True,
        validate_secrets: bool = True
    ) -> DeploymentValidationResults:
        """
        Perform comprehensive deployment validation.
        
        Args:
            environment: Target deployment environment
            validate_k8s: Whether to validate Kubernetes manifests
            validate_helm: Whether to validate Helm charts
            validate_network: Whether to validate network security
            validate_secrets: Whether to validate secrets management
            
        Returns:
            DeploymentValidationResults with comprehensive validation results
        """
        self.logger.info(f"Starting deployment validation for {environment} environment")
        
        # Initialize results
        k8s_results = None
        helm_results = None
        network_results = None
        secrets_results = None
        
        try:
            # Run validations in parallel where possible
            validation_tasks = []
            
            if validate_k8s:
                validation_tasks.append(self._validate_kubernetes_manifests())
            
            if validate_helm:
                validation_tasks.append(self._validate_helm_templates())
                
            if validate_network:
                validation_tasks.append(self._validate_network_security())
                
            if validate_secrets:
                validation_tasks.append(self._validate_secrets_management(environment))
            
            # Execute validations
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Process results
            result_index = 0
            if validate_k8s:
                k8s_results = results[result_index] if not isinstance(results[result_index], Exception) else self._create_error_k8s_results(results[result_index])
                result_index += 1
                
            if validate_helm:
                helm_results = results[result_index] if not isinstance(results[result_index], Exception) else self._create_error_helm_results(results[result_index])
                result_index += 1
                
            if validate_network:
                network_results = results[result_index] if not isinstance(results[result_index], Exception) else self._create_error_network_results(results[result_index])
                result_index += 1
                
            if validate_secrets:
                secrets_results = results[result_index] if not isinstance(results[result_index], Exception) else self._create_error_secrets_results(results[result_index])
                result_index += 1
            
            # Create default results for skipped validations
            if not validate_k8s:
                k8s_results = self._create_default_k8s_results()
            if not validate_helm:
                helm_results = self._create_default_helm_results()
            if not validate_network:
                network_results = self._create_default_network_results()
            if not validate_secrets:
                secrets_results = self._create_default_secrets_results()
            
            # Calculate overall deployment readiness
            deployment_ready, overall_score, recommendations = self._assess_deployment_readiness(
                k8s_results, helm_results, network_results, secrets_results, environment
            )
            
            # Create comprehensive results
            validation_results = DeploymentValidationResults(
                kubernetes_validation=k8s_results,
                helm_validation=helm_results,
                network_security=network_results,
                secrets_validation=secrets_results,
                deployment_ready=deployment_ready,
                overall_score=overall_score,
                environment=environment,
                recommendations=recommendations
            )
            
            self.logger.info(f"Deployment validation completed. Ready: {deployment_ready}, Score: {overall_score:.1f}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Deployment validation failed: {e}")
            # Return failed validation results
            return self._create_failed_validation_results(environment, str(e))
    
    async def _validate_kubernetes_manifests(self) -> KubernetesValidationResults:
        """Validate Kubernetes manifests using kubectl and custom validation."""
        self.logger.info("Validating Kubernetes manifests")
        
        validation_errors = []
        validation_warnings = []
        
        # Check if kubectl is available
        kubectl_available = await self._check_kubectl_available()
        if not kubectl_available:
            validation_warnings.append(ValidationResult(
                passed=False,
                message="kubectl not available - skipping manifest validation",
                severity="warning"
            ))
        
        # Look for Kubernetes manifests
        manifest_files = self._find_kubernetes_manifests()
        
        if not manifest_files:
            # Check if we're using docker-compose instead
            if self.docker_compose_path.exists():
                validation_warnings.append(ValidationResult(
                    passed=True,
                    message="No Kubernetes manifests found, using docker-compose for local deployment",
                    severity="info"
                ))
                return self._create_docker_compose_k8s_results()
            else:
                validation_errors.append(ValidationResult(
                    passed=False,
                    message="No Kubernetes manifests or docker-compose.yml found",
                    severity="error"
                ))
        
        manifest_syntax_valid = True
        resource_quotas_valid = True
        security_policies_valid = True
        best_practices_followed = True
        
        # Validate each manifest file
        for manifest_file in manifest_files:
            try:
                # Validate YAML syntax
                with open(manifest_file, 'r') as f:
                    yaml_content = yaml.safe_load_all(f)
                    for doc in yaml_content:
                        if doc:
                            await self._validate_k8s_resource(doc, validation_errors, validation_warnings)
                            
            except yaml.YAMLError as e:
                manifest_syntax_valid = False
                validation_errors.append(ValidationResult(
                    passed=False,
                    message=f"YAML syntax error in {manifest_file}: {e}",
                    severity="error"
                ))
            except Exception as e:
                validation_errors.append(ValidationResult(
                    passed=False,
                    message=f"Error validating {manifest_file}: {e}",
                    severity="error"
                ))
        
        # Run kubectl validation if available
        if kubectl_available and manifest_files:
            kubectl_results = await self._run_kubectl_validation(manifest_files)
            validation_errors.extend(kubectl_results.get('errors', []))
            validation_warnings.extend(kubectl_results.get('warnings', []))
        
        # Update overall status based on errors
        if validation_errors:
            manifest_syntax_valid = False
            best_practices_followed = False
        
        return KubernetesValidationResults(
            manifest_syntax_valid=manifest_syntax_valid,
            resource_quotas_valid=resource_quotas_valid,
            security_policies_valid=security_policies_valid,
            best_practices_followed=best_practices_followed,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings
        )  
  
    async def _validate_helm_templates(self) -> HelmValidationResults:
        """Validate Helm templates and charts."""
        self.logger.info("Validating Helm templates")
        
        validation_errors = []
        validation_warnings = []
        
        # Check if helm is available
        helm_available = await self._check_helm_available()
        if not helm_available:
            validation_warnings.append(ValidationResult(
                passed=False,
                message="Helm not available - skipping Helm validation",
                severity="warning"
            ))
        
        # Look for Helm charts
        chart_files = self._find_helm_charts()
        
        if not chart_files:
            validation_warnings.append(ValidationResult(
                passed=True,
                message="No Helm charts found - using direct Kubernetes manifests or docker-compose",
                severity="info"
            ))
            return HelmValidationResults(
                template_syntax_valid=True,
                values_schema_valid=True,
                chart_structure_valid=True,
                dependencies_resolved=True,
                validation_warnings=validation_warnings
            )
        
        template_syntax_valid = True
        values_schema_valid = True
        chart_structure_valid = True
        dependencies_resolved = True
        
        # Validate each Helm chart
        for chart_path in chart_files:
            try:
                # Validate chart structure
                chart_validation = await self._validate_helm_chart_structure(chart_path)
                if not chart_validation['valid']:
                    chart_structure_valid = False
                    validation_errors.extend(chart_validation['errors'])
                
                # Run helm template validation if helm is available
                if helm_available:
                    template_validation = await self._run_helm_template_validation(chart_path)
                    if not template_validation['valid']:
                        template_syntax_valid = False
                        validation_errors.extend(template_validation['errors'])
                
            except Exception as e:
                validation_errors.append(ValidationResult(
                    passed=False,
                    message=f"Error validating Helm chart {chart_path}: {e}",
                    severity="error"
                ))
        
        return HelmValidationResults(
            template_syntax_valid=template_syntax_valid,
            values_schema_valid=values_schema_valid,
            chart_structure_valid=chart_structure_valid,
            dependencies_resolved=dependencies_resolved,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings
        )
    
    async def _validate_network_security(self) -> NetworkSecurityResults:
        """Validate network security configurations."""
        self.logger.info("Validating network security configurations")
        
        validation_errors = []
        validation_warnings = []
        
        # Check for network policies in Kubernetes manifests
        network_policies_configured = False
        least_privilege_enforced = False
        tls_configured = False
        ingress_security_valid = False
        service_mesh_configured = False
        
        # Look for network policies
        manifest_files = self._find_kubernetes_manifests()
        for manifest_file in manifest_files:
            try:
                with open(manifest_file, 'r') as f:
                    yaml_content = yaml.safe_load_all(f)
                    for doc in yaml_content:
                        if doc and doc.get('kind') == 'NetworkPolicy':
                            network_policies_configured = True
                            # Validate network policy configuration
                            if self._validate_network_policy(doc):
                                least_privilege_enforced = True
                        
                        elif doc and doc.get('kind') == 'Ingress':
                            # Check for TLS configuration
                            if doc.get('spec', {}).get('tls'):
                                tls_configured = True
                                ingress_security_valid = True
                        
                        elif doc and doc.get('kind') in ['Service', 'ServiceMonitor']:
                            # Check for service mesh annotations
                            annotations = doc.get('metadata', {}).get('annotations', {})
                            if any('istio' in key or 'linkerd' in key for key in annotations.keys()):
                                service_mesh_configured = True
                                
            except Exception as e:
                validation_errors.append(ValidationResult(
                    passed=False,
                    message=f"Error validating network security in {manifest_file}: {e}",
                    severity="error"
                ))
        
        # Check docker-compose for TLS configuration
        if self.docker_compose_path.exists():
            tls_configured = self._check_docker_compose_tls()
        
        # Validate TLS certificates if configured
        if tls_configured:
            cert_validation = await self._validate_tls_certificates()
            if not cert_validation['valid']:
                validation_warnings.extend(cert_validation['warnings'])
        
        # Add recommendations based on findings
        if not network_policies_configured:
            validation_warnings.append(ValidationResult(
                passed=False,
                message="No network policies found - consider implementing network segmentation",
                severity="warning"
            ))
        
        if not tls_configured:
            validation_warnings.append(ValidationResult(
                passed=False,
                message="TLS not configured - ensure HTTPS is enabled for production",
                severity="warning"
            ))
        
        return NetworkSecurityResults(
            network_policies_configured=network_policies_configured,
            least_privilege_enforced=least_privilege_enforced,
            tls_configured=tls_configured,
            ingress_security_valid=ingress_security_valid,
            service_mesh_configured=service_mesh_configured,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings
        )
    
    async def _validate_secrets_management(self, environment: str) -> SecretsValidationResults:
        """Validate secrets and environment variable management."""
        self.logger.info("Validating secrets management")
        
        validation_errors = []
        validation_warnings = []
        
        secrets_externalized = True
        environment_vars_configured = True
        no_hardcoded_secrets = True
        secret_rotation_configured = False
        
        # Check for hardcoded secrets in codebase
        hardcoded_secrets = await self._scan_for_hardcoded_secrets()
        if hardcoded_secrets:
            no_hardcoded_secrets = False
            for secret in hardcoded_secrets:
                validation_errors.append(ValidationResult(
                    passed=False,
                    message=f"Hardcoded secret found: {secret['file']}:{secret['line']}",
                    details=secret,
                    severity="critical"
                ))
        
        # Check environment variable configuration
        env_validation = self._validate_environment_variables(environment)
        if not env_validation['valid']:
            environment_vars_configured = False
            validation_errors.extend(env_validation['errors'])
        
        # Check for .env files in production
        if environment == "production":
            env_files = list(self.project_root.glob("**/.env*"))
            if env_files:
                validation_warnings.append(ValidationResult(
                    passed=False,
                    message="Environment files found - ensure secrets are managed via secret manager in production",
                    severity="warning"
                ))
        
        # Check Kubernetes secrets configuration
        k8s_secrets = self._check_kubernetes_secrets()
        if not k8s_secrets['configured']:
            secrets_externalized = False
            validation_warnings.extend(k8s_secrets['warnings'])
        
        # Check for secret rotation configuration
        if k8s_secrets['rotation_configured']:
            secret_rotation_configured = True
        
        return SecretsValidationResults(
            secrets_externalized=secrets_externalized,
            environment_vars_configured=environment_vars_configured,
            no_hardcoded_secrets=no_hardcoded_secrets,
            secret_rotation_configured=secret_rotation_configured,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings
        )
    
    # Helper methods for validation
    
    async def _check_kubectl_available(self) -> bool:
        """Check if kubectl is available."""
        try:
            result = await asyncio.create_subprocess_exec(
                'kubectl', 'version', '--client',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    async def _check_helm_available(self) -> bool:
        """Check if helm is available."""
        try:
            result = await asyncio.create_subprocess_exec(
                'helm', 'version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _find_kubernetes_manifests(self) -> List[Path]:
        """Find Kubernetes manifest files."""
        manifest_files = []
        
        # Look in common locations
        search_paths = [
            self.k8s_manifests_path,
            self.project_root / "kubernetes",
            self.project_root / "manifests",
            self.project_root / "deploy"
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                manifest_files.extend(search_path.glob("**/*.yaml"))
                manifest_files.extend(search_path.glob("**/*.yml"))
        
        return manifest_files
    
    def _find_helm_charts(self) -> List[Path]:
        """Find Helm chart directories."""
        chart_dirs = []
        
        # Look in common locations
        search_paths = [
            self.helm_charts_path,
            self.project_root / "charts",
            self.project_root / "helm-charts"
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                # Look for Chart.yaml files
                for chart_file in search_path.glob("**/Chart.yaml"):
                    chart_dirs.append(chart_file.parent)
        
        return chart_dirs   
 
    async def _validate_k8s_resource(self, resource: Dict, errors: List, warnings: List):
        """Validate a single Kubernetes resource."""
        kind = resource.get('kind', '')
        metadata = resource.get('metadata', {})
        spec = resource.get('spec', {})
        
        # Validate required fields
        if not kind:
            errors.append(ValidationResult(
                passed=False,
                message="Resource missing 'kind' field",
                severity="error"
            ))
        
        if not metadata.get('name'):
            errors.append(ValidationResult(
                passed=False,
                message=f"{kind} resource missing 'metadata.name' field",
                severity="error"
            ))
        
        # Validate specific resource types
        if kind == 'Deployment':
            await self._validate_deployment_resource(resource, errors, warnings)
        elif kind == 'Service':
            await self._validate_service_resource(resource, errors, warnings)
        elif kind == 'Ingress':
            await self._validate_ingress_resource(resource, errors, warnings)
        elif kind == 'ConfigMap' or kind == 'Secret':
            await self._validate_config_resource(resource, errors, warnings)
    
    async def _validate_deployment_resource(self, deployment: Dict, errors: List, warnings: List):
        """Validate Deployment resource."""
        spec = deployment.get('spec', {})
        template = spec.get('template', {})
        containers = template.get('spec', {}).get('containers', [])
        
        # Check for resource limits
        for container in containers:
            resources = container.get('resources', {})
            if not resources.get('limits'):
                warnings.append(ValidationResult(
                    passed=False,
                    message=f"Container {container.get('name', 'unknown')} missing resource limits",
                    severity="warning"
                ))
            
            if not resources.get('requests'):
                warnings.append(ValidationResult(
                    passed=False,
                    message=f"Container {container.get('name', 'unknown')} missing resource requests",
                    severity="warning"
                ))
        
        # Check for health checks
        for container in containers:
            if not container.get('livenessProbe'):
                warnings.append(ValidationResult(
                    passed=False,
                    message=f"Container {container.get('name', 'unknown')} missing liveness probe",
                    severity="warning"
                ))
            
            if not container.get('readinessProbe'):
                warnings.append(ValidationResult(
                    passed=False,
                    message=f"Container {container.get('name', 'unknown')} missing readiness probe",
                    severity="warning"
                ))
        
        # Check security context
        security_context = template.get('spec', {}).get('securityContext', {})
        if not security_context.get('runAsNonRoot'):
            warnings.append(ValidationResult(
                passed=False,
                message="Deployment not configured to run as non-root user",
                severity="warning"
            ))
    
    async def _validate_service_resource(self, service: Dict, errors: List, warnings: List):
        """Validate Service resource."""
        spec = service.get('spec', {})
        
        # Check for proper selector
        if not spec.get('selector'):
            errors.append(ValidationResult(
                passed=False,
                message="Service missing selector",
                severity="error"
            ))
        
        # Check port configuration
        ports = spec.get('ports', [])
        if not ports:
            errors.append(ValidationResult(
                passed=False,
                message="Service missing port configuration",
                severity="error"
            ))
    
    async def _validate_ingress_resource(self, ingress: Dict, errors: List, warnings: List):
        """Validate Ingress resource."""
        spec = ingress.get('spec', {})
        
        # Check for TLS configuration
        if not spec.get('tls'):
            warnings.append(ValidationResult(
                passed=False,
                message="Ingress missing TLS configuration",
                severity="warning"
            ))
        
        # Check for proper rules
        rules = spec.get('rules', [])
        if not rules:
            errors.append(ValidationResult(
                passed=False,
                message="Ingress missing rules",
                severity="error"
            ))
    
    async def _validate_config_resource(self, config: Dict, errors: List, warnings: List):
        """Validate ConfigMap or Secret resource."""
        kind = config.get('kind')
        data = config.get('data', {})
        
        if not data:
            warnings.append(ValidationResult(
                passed=False,
                message=f"{kind} has no data",
                severity="warning"
            ))
    
    async def _run_kubectl_validation(self, manifest_files: List[Path]) -> Dict:
        """Run kubectl validation on manifest files."""
        errors = []
        warnings = []
        
        for manifest_file in manifest_files:
            try:
                # Run kubectl dry-run validation
                result = await asyncio.create_subprocess_exec(
                    'kubectl', 'apply', '--dry-run=client', '-f', str(manifest_file),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode != 0:
                    errors.append(ValidationResult(
                        passed=False,
                        message=f"kubectl validation failed for {manifest_file}: {stderr.decode()}",
                        severity="error"
                    ))
                
                # Run kubectl lint validation using kubeval if available
                await self._run_kubeval_validation(manifest_file, errors, warnings)
                
                # Run additional kubectl best practices validation
                await self._run_kubectl_best_practices_validation(manifest_file, errors, warnings)
                
            except Exception as e:
                errors.append(ValidationResult(
                    passed=False,
                    message=f"Error running kubectl validation on {manifest_file}: {e}",
                    severity="error"
                ))
        
        return {'errors': errors, 'warnings': warnings}
    
    async def _run_kubeval_validation(self, manifest_file: Path, errors: List, warnings: List):
        """Run kubeval validation for Kubernetes manifest linting."""
        try:
            # Check if kubeval is available
            result = await asyncio.create_subprocess_exec(
                'kubeval', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            if result.returncode == 0:
                # Run kubeval validation
                result = await asyncio.create_subprocess_exec(
                    'kubeval', str(manifest_file),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode != 0:
                    errors.append(ValidationResult(
                        passed=False,
                        message=f"kubeval validation failed for {manifest_file}: {stderr.decode()}",
                        severity="error"
                    ))
                elif stdout:
                    # Parse kubeval output for warnings
                    output = stdout.decode()
                    if "WARN" in output:
                        warnings.append(ValidationResult(
                            passed=True,
                            message=f"kubeval warnings for {manifest_file}: {output}",
                            severity="warning"
                        ))
            else:
                # kubeval not available, use alternative validation
                await self._run_alternative_lint_validation(manifest_file, errors, warnings)
                
        except FileNotFoundError:
            # kubeval not installed, use alternative validation
            await self._run_alternative_lint_validation(manifest_file, errors, warnings)
        except Exception as e:
            warnings.append(ValidationResult(
                passed=False,
                message=f"Error running kubeval on {manifest_file}: {e}",
                severity="warning"
            ))
    
    async def _run_alternative_lint_validation(self, manifest_file: Path, errors: List, warnings: List):
        """Run alternative lint validation when kubeval is not available."""
        try:
            # Use kubectl validate with strict mode
            result = await asyncio.create_subprocess_exec(
                'kubectl', 'apply', '--dry-run=client', '--validate=strict', '-f', str(manifest_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                # Parse stderr for specific validation issues
                stderr_text = stderr.decode()
                if "unknown field" in stderr_text.lower():
                    errors.append(ValidationResult(
                        passed=False,
                        message=f"Manifest contains unknown fields: {stderr_text}",
                        severity="error"
                    ))
                elif "invalid value" in stderr_text.lower():
                    errors.append(ValidationResult(
                        passed=False,
                        message=f"Manifest contains invalid values: {stderr_text}",
                        severity="error"
                    ))
                    
        except Exception as e:
            warnings.append(ValidationResult(
                passed=False,
                message=f"Error running alternative lint validation: {e}",
                severity="warning"
            ))
    
    async def _run_kubectl_best_practices_validation(self, manifest_file: Path, errors: List, warnings: List):
        """Run kubectl best practices validation."""
        try:
            with open(manifest_file, 'r') as f:
                yaml_content = yaml.safe_load_all(f)
                for doc in yaml_content:
                    if doc:
                        await self._validate_k8s_best_practices(doc, manifest_file, errors, warnings)
        except Exception as e:
            warnings.append(ValidationResult(
                passed=False,
                message=f"Error running best practices validation on {manifest_file}: {e}",
                severity="warning"
            ))
    
    async def _validate_k8s_best_practices(self, resource: Dict, manifest_file: Path, errors: List, warnings: List):
        """Validate Kubernetes best practices."""
        kind = resource.get('kind', '')
        metadata = resource.get('metadata', {})
        spec = resource.get('spec', {})
        
        # Check for required labels
        labels = metadata.get('labels', {})
        required_labels = ['app', 'version', 'component']
        missing_labels = [label for label in required_labels if label not in labels]
        
        if missing_labels:
            warnings.append(ValidationResult(
                passed=False,
                message=f"{kind} in {manifest_file} missing recommended labels: {', '.join(missing_labels)}",
                severity="warning"
            ))
        
        # Check for resource limits and requests (for Deployments, StatefulSets, DaemonSets)
        if kind in ['Deployment', 'StatefulSet', 'DaemonSet']:
            containers = spec.get('template', {}).get('spec', {}).get('containers', [])
            for container in containers:
                resources = container.get('resources', {})
                if not resources.get('limits'):
                    warnings.append(ValidationResult(
                        passed=False,
                        message=f"Container {container.get('name', 'unknown')} in {manifest_file} missing resource limits",
                        severity="warning"
                    ))
                if not resources.get('requests'):
                    warnings.append(ValidationResult(
                        passed=False,
                        message=f"Container {container.get('name', 'unknown')} in {manifest_file} missing resource requests",
                        severity="warning"
                    ))
        
        # Check for security context
        if kind in ['Deployment', 'StatefulSet', 'DaemonSet', 'Pod']:
            pod_spec = spec.get('template', {}).get('spec', {}) if kind != 'Pod' else spec
            security_context = pod_spec.get('securityContext', {})
            
            if not security_context.get('runAsNonRoot'):
                warnings.append(ValidationResult(
                    passed=False,
                    message=f"{kind} in {manifest_file} should run as non-root user",
                    severity="warning"
                ))
            
            if not security_context.get('readOnlyRootFilesystem'):
                warnings.append(ValidationResult(
                    passed=False,
                    message=f"{kind} in {manifest_file} should use read-only root filesystem",
                    severity="warning"
                ))
    
    async def _validate_helm_chart_structure(self, chart_path: Path) -> Dict:
        """Validate Helm chart structure."""
        errors = []
        
        # Check for required files
        required_files = ['Chart.yaml', 'values.yaml']
        for required_file in required_files:
            if not (chart_path / required_file).exists():
                errors.append(ValidationResult(
                    passed=False,
                    message=f"Missing required file: {required_file}",
                    severity="error"
                ))
        
        # Validate Chart.yaml
        chart_yaml_path = chart_path / 'Chart.yaml'
        if chart_yaml_path.exists():
            try:
                with open(chart_yaml_path, 'r') as f:
                    chart_data = yaml.safe_load(f)
                    
                required_fields = ['name', 'version', 'description']
                for field in required_fields:
                    if not chart_data.get(field):
                        errors.append(ValidationResult(
                            passed=False,
                            message=f"Chart.yaml missing required field: {field}",
                            severity="error"
                        ))
                        
            except Exception as e:
                errors.append(ValidationResult(
                    passed=False,
                    message=f"Error parsing Chart.yaml: {e}",
                    severity="error"
                ))
        
        return {'valid': len(errors) == 0, 'errors': errors}
    
    async def _run_helm_template_validation(self, chart_path: Path) -> Dict:
        """Run helm template validation."""
        errors = []
        warnings = []
        
        try:
            # Run helm template command
            result = await asyncio.create_subprocess_exec(
                'helm', 'template', str(chart_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                errors.append(ValidationResult(
                    passed=False,
                    message=f"Helm template validation failed: {stderr.decode()}",
                    severity="error"
                ))
            else:
                # Validate the generated templates
                await self._validate_helm_generated_templates(stdout.decode(), chart_path, errors, warnings)
            
            # Run helm lint validation
            await self._run_helm_lint_validation(chart_path, errors, warnings)
            
            # Validate Helm best practices
            await self._validate_helm_best_practices(chart_path, errors, warnings)
            
        except Exception as e:
            errors.append(ValidationResult(
                passed=False,
                message=f"Error running helm template validation: {e}",
                severity="error"
            ))
        
        return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}
    
    async def _run_helm_lint_validation(self, chart_path: Path, errors: List, warnings: List):
        """Run helm lint validation."""
        try:
            result = await asyncio.create_subprocess_exec(
                'helm', 'lint', str(chart_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                errors.append(ValidationResult(
                    passed=False,
                    message=f"Helm lint validation failed: {stderr.decode()}",
                    severity="error"
                ))
            else:
                # Parse helm lint output for warnings
                output = stdout.decode()
                if "WARNING" in output:
                    warnings.append(ValidationResult(
                        passed=True,
                        message=f"Helm lint warnings: {output}",
                        severity="warning"
                    ))
                    
        except Exception as e:
            warnings.append(ValidationResult(
                passed=False,
                message=f"Error running helm lint: {e}",
                severity="warning"
            ))
    
    async def _validate_helm_generated_templates(self, template_output: str, chart_path: Path, errors: List, warnings: List):
        """Validate the generated Helm templates."""
        try:
            # Parse the generated YAML templates
            yaml_docs = list(yaml.safe_load_all(template_output))
            
            for doc in yaml_docs:
                if doc:
                    # Validate each generated resource
                    await self._validate_k8s_resource(doc, errors, warnings)
                    
        except yaml.YAMLError as e:
            errors.append(ValidationResult(
                passed=False,
                message=f"Generated Helm templates contain invalid YAML: {e}",
                severity="error"
            ))
        except Exception as e:
            warnings.append(ValidationResult(
                passed=False,
                message=f"Error validating generated Helm templates: {e}",
                severity="warning"
            ))
    
    async def _validate_helm_best_practices(self, chart_path: Path, errors: List, warnings: List):
        """Validate Helm best practices."""
        # Check for templates directory
        templates_dir = chart_path / 'templates'
        if not templates_dir.exists():
            errors.append(ValidationResult(
                passed=False,
                message="Helm chart missing templates directory",
                severity="error"
            ))
            return
        
        # Check for NOTES.txt
        notes_file = templates_dir / 'NOTES.txt'
        if not notes_file.exists():
            warnings.append(ValidationResult(
                passed=False,
                message="Helm chart missing NOTES.txt file",
                severity="warning"
            ))
        
        # Check for _helpers.tpl
        helpers_file = templates_dir / '_helpers.tpl'
        if not helpers_file.exists():
            warnings.append(ValidationResult(
                passed=False,
                message="Helm chart missing _helpers.tpl file",
                severity="warning"
            ))
        
        # Validate values.yaml structure
        values_file = chart_path / 'values.yaml'
        if values_file.exists():
            try:
                with open(values_file, 'r') as f:
                    values_data = yaml.safe_load(f)
                    
                # Check for common best practice fields
                recommended_fields = ['image', 'service', 'ingress', 'resources']
                missing_fields = [field for field in recommended_fields if field not in values_data]
                
                if missing_fields:
                    warnings.append(ValidationResult(
                        passed=False,
                        message=f"values.yaml missing recommended sections: {', '.join(missing_fields)}",
                        severity="warning"
                    ))
                    
            except Exception as e:
                warnings.append(ValidationResult(
                    passed=False,
                    message=f"Error validating values.yaml: {e}",
                    severity="warning"
                ))
    
    def _validate_network_policy(self, policy: Dict) -> bool:
        """Validate network policy for least privilege."""
        spec = policy.get('spec', {})
        
        # Check if policy has proper ingress/egress rules
        ingress = spec.get('ingress', [])
        egress = spec.get('egress', [])
        
        # A good network policy should have specific rules
        return len(ingress) > 0 or len(egress) > 0
    
    def _check_docker_compose_tls(self) -> bool:
        """Check if docker-compose has TLS configuration."""
        try:
            with open(self.docker_compose_path, 'r') as f:
                compose_data = yaml.safe_load(f)
                
            # Look for TLS-related configurations
            services = compose_data.get('services', {})
            for service_name, service_config in services.items():
                environment = service_config.get('environment', [])
                if isinstance(environment, list):
                    for env_var in environment:
                        if 'TLS' in env_var or 'SSL' in env_var or 'HTTPS' in env_var:
                            return True
                elif isinstance(environment, dict):
                    for key in environment.keys():
                        if 'TLS' in key or 'SSL' in key or 'HTTPS' in key:
                            return True
            
            return False
            
        except Exception:
            return False
    
    async def _validate_tls_certificates(self) -> Dict:
        """Validate TLS certificate configuration."""
        warnings = []
        errors = []
        
        try:
            # Check for certificate files in common locations
            cert_paths = [
                self.project_root / "certs",
                self.project_root / "ssl",
                self.project_root / "tls",
                self.project_root / "k8s" / "certs"
            ]
            
            cert_files_found = []
            for cert_path in cert_paths:
                if cert_path.exists():
                    cert_files = list(cert_path.glob("*.crt")) + list(cert_path.glob("*.pem"))
                    cert_files_found.extend(cert_files)
            
            if cert_files_found:
                # Validate certificate files
                for cert_file in cert_files_found:
                    await self._validate_certificate_file(cert_file, warnings, errors)
            else:
                # Check for certificate references in Kubernetes manifests
                await self._check_k8s_certificate_references(warnings, errors)
            
            # Check for certificate auto-renewal configuration
            await self._check_certificate_auto_renewal(warnings)
            
        except Exception as e:
            warnings.append(ValidationResult(
                passed=False,
                message=f"Error validating TLS certificates: {e}",
                severity="warning"
            ))
        
        return {'valid': len(errors) == 0, 'warnings': warnings, 'errors': errors}
    
    async def _validate_certificate_file(self, cert_file: Path, warnings: List, errors: List):
        """Validate a certificate file."""
        try:
            # Try to use openssl to validate certificate if available
            result = await asyncio.create_subprocess_exec(
                'openssl', 'x509', '-in', str(cert_file), '-text', '-noout',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                # Parse certificate information
                cert_info = stdout.decode()
                
                # Check for expiration (basic check)
                if "Not After" in cert_info:
                    warnings.append(ValidationResult(
                        passed=True,
                        message=f"Certificate {cert_file.name} found - verify expiration date manually",
                        severity="info"
                    ))
                
                # Check for self-signed certificates
                if "Issuer:" in cert_info and "Subject:" in cert_info:
                    issuer_line = [line for line in cert_info.split('\n') if 'Issuer:' in line]
                    subject_line = [line for line in cert_info.split('\n') if 'Subject:' in line]
                    
                    if issuer_line and subject_line and issuer_line[0] == subject_line[0]:
                        warnings.append(ValidationResult(
                            passed=False,
                            message=f"Certificate {cert_file.name} appears to be self-signed",
                            severity="warning"
                        ))
            else:
                errors.append(ValidationResult(
                    passed=False,
                    message=f"Invalid certificate file: {cert_file}",
                    severity="error"
                ))
                
        except FileNotFoundError:
            # openssl not available, skip detailed validation
            warnings.append(ValidationResult(
                passed=True,
                message=f"Certificate file {cert_file.name} found - openssl not available for validation",
                severity="info"
            ))
        except Exception as e:
            warnings.append(ValidationResult(
                passed=False,
                message=f"Error validating certificate {cert_file}: {e}",
                severity="warning"
            ))
    
    async def _check_k8s_certificate_references(self, warnings: List, errors: List):
        """Check for certificate references in Kubernetes manifests."""
        manifest_files = self._find_kubernetes_manifests()
        
        for manifest_file in manifest_files:
            try:
                with open(manifest_file, 'r') as f:
                    yaml_content = yaml.safe_load_all(f)
                    for doc in yaml_content:
                        if doc and doc.get('kind') == 'Secret':
                            secret_type = doc.get('type', '')
                            if secret_type == 'kubernetes.io/tls':
                                # Found TLS secret
                                data = doc.get('data', {})
                                if 'tls.crt' in data and 'tls.key' in data:
                                    warnings.append(ValidationResult(
                                        passed=True,
                                        message=f"TLS secret found in {manifest_file} - verify certificate validity",
                                        severity="info"
                                    ))
                                else:
                                    errors.append(ValidationResult(
                                        passed=False,
                                        message=f"TLS secret in {manifest_file} missing required keys",
                                        severity="error"
                                    ))
                        elif doc and doc.get('kind') == 'Ingress':
                            # Check ingress TLS configuration
                            tls_config = doc.get('spec', {}).get('tls', [])
                            for tls_entry in tls_config:
                                if not tls_entry.get('secretName'):
                                    errors.append(ValidationResult(
                                        passed=False,
                                        message=f"Ingress TLS configuration in {manifest_file} missing secretName",
                                        severity="error"
                                    ))
                                    
            except Exception as e:
                warnings.append(ValidationResult(
                    passed=False,
                    message=f"Error checking certificate references in {manifest_file}: {e}",
                    severity="warning"
                ))
    
    async def _check_certificate_auto_renewal(self, warnings: List):
        """Check for certificate auto-renewal configuration."""
        # Check for cert-manager configuration
        manifest_files = self._find_kubernetes_manifests()
        cert_manager_found = False
        
        for manifest_file in manifest_files:
            try:
                with open(manifest_file, 'r') as f:
                    content = f.read()
                    if 'cert-manager' in content or 'Certificate' in content:
                        cert_manager_found = True
                        break
            except Exception:
                continue
        
        if not cert_manager_found:
            warnings.append(ValidationResult(
                passed=False,
                message="No certificate auto-renewal configuration found - consider using cert-manager",
                severity="warning"
            ))
    
    async def _scan_for_hardcoded_secrets(self) -> List[Dict]:
        """Scan codebase for hardcoded secrets."""
        secrets = []
        
        # Common secret patterns
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']'
        ]
        
        # Files to scan
        file_patterns = ['*.py', '*.js', '*.ts', '*.yaml', '*.yml', '*.json']
        
        import re
        
        for pattern in file_patterns:
            for file_path in self.project_root.glob(f"**/{pattern}"):
                # Skip certain directories
                if any(skip_dir in str(file_path) for skip_dir in ['.git', 'node_modules', '.venv', '__pycache__']):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for line_num, line in enumerate(content.split('\n'), 1):
                        for secret_pattern in secret_patterns:
                            if re.search(secret_pattern, line, re.IGNORECASE):
                                # Skip if it's in a comment or example
                                if '#' in line or 'example' in line.lower() or 'test' in line.lower():
                                    continue
                                    
                                secrets.append({
                                    'file': str(file_path.relative_to(self.project_root)),
                                    'line': line_num,
                                    'content': line.strip()
                                })
                                
                except Exception as e:
                    # Skip files that can't be read
                    continue
        
        return secrets
    
    def _validate_environment_variables(self, environment: str) -> Dict:
        """Validate environment variable configuration."""
        errors = []
        
        # Required environment variables for the application
        required_vars = [
            'DATABASE_URL',
            'REDIS_URL',
            'JWT_SECRET',
            'CELERY_BROKER_URL',
            'CELERY_RESULT_BACKEND'
        ]
        
        # Check if .env.example exists
        env_example_path = self.project_root / '.env.example'
        if not env_example_path.exists():
            errors.append(ValidationResult(
                passed=False,
                message="Missing .env.example file for environment variable documentation",
                severity="warning"
            ))
        else:
            # Validate that all required vars are documented
            try:
                with open(env_example_path, 'r') as f:
                    env_example_content = f.read()
                
                for var in required_vars:
                    if var not in env_example_content:
                        errors.append(ValidationResult(
                            passed=False,
                            message=f"Required environment variable {var} not documented in .env.example",
                            severity="warning"
                        ))
                        
            except Exception as e:
                errors.append(ValidationResult(
                    passed=False,
                    message=f"Error reading .env.example: {e}",
                    severity="error"
                ))
        
        # For production, check that sensitive vars are not in .env files
        if environment == "production":
            env_files = ['.env', '.env.local', '.env.production']
            for env_file in env_files:
                env_path = self.project_root / env_file
                if env_path.exists():
                    errors.append(ValidationResult(
                        passed=False,
                        message=f"Environment file {env_file} found - use secret manager for production",
                        severity="critical"
                    ))
        
        return {'valid': len(errors) == 0, 'errors': errors}
    
    def _check_kubernetes_secrets(self) -> Dict:
        """Check Kubernetes secrets configuration."""
        warnings = []
        configured = False
        rotation_configured = False
        
        # Look for Secret resources in manifests
        manifest_files = self._find_kubernetes_manifests()
        for manifest_file in manifest_files:
            try:
                with open(manifest_file, 'r') as f:
                    yaml_content = yaml.safe_load_all(f)
                    for doc in yaml_content:
                        if doc and doc.get('kind') == 'Secret':
                            configured = True
                            
                            # Check for rotation annotations
                            annotations = doc.get('metadata', {}).get('annotations', {})
                            if any('rotation' in key.lower() for key in annotations.keys()):
                                rotation_configured = True
                                
            except Exception:
                continue
        
        if not configured:
            warnings.append(ValidationResult(
                passed=False,
                message="No Kubernetes secrets configured - ensure secrets are managed properly",
                severity="warning"
            ))
        
        return {
            'configured': configured,
            'rotation_configured': rotation_configured,
            'warnings': warnings
        }
    
    def _assess_deployment_readiness(
        self, 
        k8s_results: KubernetesValidationResults,
        helm_results: Optional[HelmValidationResults],
        network_results: NetworkSecurityResults,
        secrets_results: SecretsValidationResults,
        environment: str
    ) -> tuple[bool, float, List[str]]:
        """Assess overall deployment readiness."""
        
        # Calculate scores for each component
        k8s_score = self._calculate_k8s_score(k8s_results)
        helm_score = self._calculate_helm_score(helm_results) if helm_results else 100.0
        network_score = self._calculate_network_score(network_results)
        secrets_score = self._calculate_secrets_score(secrets_results)
        
        # Weighted average (adjust weights as needed)
        overall_score = (
            k8s_score * 0.3 +
            helm_score * 0.2 +
            network_score * 0.25 +
            secrets_score * 0.25
        )
        
        # Determine deployment readiness based on environment
        deployment_ready = self._determine_deployment_readiness(
            overall_score, k8s_results, network_results, secrets_results, environment
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            k8s_results, helm_results, network_results, secrets_results, environment
        )
        
        return deployment_ready, overall_score, recommendations
    
    def _calculate_k8s_score(self, results: KubernetesValidationResults) -> float:
        """Calculate Kubernetes validation score."""
        score = 100.0
        
        if not results.manifest_syntax_valid:
            score -= 30.0
        if not results.resource_quotas_valid:
            score -= 20.0
        if not results.security_policies_valid:
            score -= 25.0
        if not results.best_practices_followed:
            score -= 15.0
        
        # Deduct points for errors and warnings
        score -= len(results.validation_errors) * 10.0
        score -= len(results.validation_warnings) * 5.0
        
        return max(0.0, score)
    
    def _calculate_helm_score(self, results: HelmValidationResults) -> float:
        """Calculate Helm validation score."""
        score = 100.0
        
        if not results.template_syntax_valid:
            score -= 30.0
        if not results.values_schema_valid:
            score -= 25.0
        if not results.chart_structure_valid:
            score -= 25.0
        if not results.dependencies_resolved:
            score -= 20.0
        
        # Deduct points for errors and warnings
        score -= len(results.validation_errors) * 10.0
        score -= len(results.validation_warnings) * 5.0
        
        return max(0.0, score)
    
    def _calculate_network_score(self, results: NetworkSecurityResults) -> float:
        """Calculate network security score."""
        score = 100.0
        
        if not results.tls_configured:
            score -= 30.0
        if not results.network_policies_configured:
            score -= 25.0
        if not results.least_privilege_enforced:
            score -= 20.0
        if not results.ingress_security_valid:
            score -= 15.0
        if not results.service_mesh_configured:
            score -= 10.0
        
        # Deduct points for errors and warnings
        score -= len(results.validation_errors) * 10.0
        score -= len(results.validation_warnings) * 5.0
        
        return max(0.0, score)
    
    def _calculate_secrets_score(self, results: SecretsValidationResults) -> float:
        """Calculate secrets management score."""
        score = 100.0
        
        if not results.no_hardcoded_secrets:
            score -= 40.0  # Critical issue
        if not results.secrets_externalized:
            score -= 25.0
        if not results.environment_vars_configured:
            score -= 20.0
        if not results.secret_rotation_configured:
            score -= 15.0
        
        # Deduct points for errors and warnings
        score -= len(results.validation_errors) * 10.0
        score -= len(results.validation_warnings) * 5.0
        
        return max(0.0, score)
    
    def _determine_deployment_readiness(
        self,
        overall_score: float,
        k8s_results: KubernetesValidationResults,
        network_results: NetworkSecurityResults,
        secrets_results: SecretsValidationResults,
        environment: str
    ) -> bool:
        """Determine if deployment is ready based on environment and scores."""
        
        # Critical blocking conditions
        if not secrets_results.no_hardcoded_secrets:
            return False  # Never deploy with hardcoded secrets
        
        if environment == "production":
            # Production has stricter requirements
            if overall_score < 80.0:
                return False
            if not network_results.tls_configured:
                return False
            if len(secrets_results.validation_errors) > 0:
                return False
        elif environment == "staging":
            # Staging is more lenient but still requires basic security
            if overall_score < 60.0:
                return False
            if len(secrets_results.validation_errors) > 0:
                return False
        else:
            # Development environment is most lenient
            if overall_score < 40.0:
                return False
        
        return True
    
    def _generate_recommendations(
        self,
        k8s_results: KubernetesValidationResults,
        helm_results: Optional[HelmValidationResults],
        network_results: NetworkSecurityResults,
        secrets_results: SecretsValidationResults,
        environment: str
    ) -> List[str]:
        """Generate deployment recommendations."""
        recommendations = []
        
        # Kubernetes recommendations
        if not k8s_results.manifest_syntax_valid:
            recommendations.append("Fix Kubernetes manifest syntax errors before deployment")
        if not k8s_results.best_practices_followed:
            recommendations.append("Implement Kubernetes best practices (resource limits, health checks, security contexts)")
        
        # Network security recommendations
        if not network_results.tls_configured:
            recommendations.append("Configure TLS/HTTPS for secure communication")
        if not network_results.network_policies_configured:
            recommendations.append("Implement network policies for network segmentation")
        
        # Secrets management recommendations
        if not secrets_results.no_hardcoded_secrets:
            recommendations.append("CRITICAL: Remove all hardcoded secrets from codebase")
        if not secrets_results.secrets_externalized:
            recommendations.append("Use Kubernetes secrets or external secret managers")
        if not secrets_results.secret_rotation_configured:
            recommendations.append("Implement secret rotation for enhanced security")
        
        # Environment-specific recommendations
        if environment == "production":
            recommendations.append("Ensure monitoring and alerting are configured")
            recommendations.append("Verify backup and disaster recovery procedures")
            recommendations.append("Conduct security audit before production deployment")
        
        return recommendations
    
    # Helper methods for creating default/error results
    
    def _create_default_k8s_results(self) -> KubernetesValidationResults:
        """Create default Kubernetes results when validation is skipped."""
        return KubernetesValidationResults(
            manifest_syntax_valid=True,
            resource_quotas_valid=True,
            security_policies_valid=True,
            best_practices_followed=True,
            validation_warnings=[ValidationResult(
                passed=True,
                message="Kubernetes validation skipped",
                severity="info"
            )]
        )
    
    def _create_default_helm_results(self) -> HelmValidationResults:
        """Create default Helm results when validation is skipped."""
        return HelmValidationResults(
            template_syntax_valid=True,
            values_schema_valid=True,
            chart_structure_valid=True,
            dependencies_resolved=True,
            validation_warnings=[ValidationResult(
                passed=True,
                message="Helm validation skipped",
                severity="info"
            )]
        )
    
    def _create_default_network_results(self) -> NetworkSecurityResults:
        """Create default network results when validation is skipped."""
        return NetworkSecurityResults(
            network_policies_configured=False,
            least_privilege_enforced=False,
            tls_configured=False,
            ingress_security_valid=False,
            service_mesh_configured=False,
            validation_warnings=[ValidationResult(
                passed=True,
                message="Network security validation skipped",
                severity="info"
            )]
        )
    
    def _create_default_secrets_results(self) -> SecretsValidationResults:
        """Create default secrets results when validation is skipped."""
        return SecretsValidationResults(
            secrets_externalized=True,
            environment_vars_configured=True,
            no_hardcoded_secrets=True,
            secret_rotation_configured=False,
            validation_warnings=[ValidationResult(
                passed=True,
                message="Secrets validation skipped",
                severity="info"
            )]
        )
    
    def _create_docker_compose_k8s_results(self) -> KubernetesValidationResults:
        """Create Kubernetes results for docker-compose setup."""
        return KubernetesValidationResults(
            manifest_syntax_valid=True,
            resource_quotas_valid=True,
            security_policies_valid=False,
            best_practices_followed=False,
            validation_warnings=[
                ValidationResult(
                    passed=True,
                    message="Using docker-compose for local development",
                    severity="info"
                ),
                ValidationResult(
                    passed=False,
                    message="Consider implementing Kubernetes manifests for production deployment",
                    severity="warning"
                )
            ]
        )
    
    def _create_error_k8s_results(self, error: Exception) -> KubernetesValidationResults:
        """Create error Kubernetes results."""
        return KubernetesValidationResults(
            manifest_syntax_valid=False,
            resource_quotas_valid=False,
            security_policies_valid=False,
            best_practices_followed=False,
            validation_errors=[ValidationResult(
                passed=False,
                message=f"Kubernetes validation failed: {error}",
                severity="error"
            )]
        )
    
    def _create_error_helm_results(self, error: Exception) -> HelmValidationResults:
        """Create error Helm results."""
        return HelmValidationResults(
            template_syntax_valid=False,
            values_schema_valid=False,
            chart_structure_valid=False,
            dependencies_resolved=False,
            validation_errors=[ValidationResult(
                passed=False,
                message=f"Helm validation failed: {error}",
                severity="error"
            )]
        )
    
    def _create_error_network_results(self, error: Exception) -> NetworkSecurityResults:
        """Create error network results."""
        return NetworkSecurityResults(
            network_policies_configured=False,
            least_privilege_enforced=False,
            tls_configured=False,
            ingress_security_valid=False,
            service_mesh_configured=False,
            validation_errors=[ValidationResult(
                passed=False,
                message=f"Network security validation failed: {error}",
                severity="error"
            )]
        )
    
    def _create_error_secrets_results(self, error: Exception) -> SecretsValidationResults:
        """Create error secrets results."""
        return SecretsValidationResults(
            secrets_externalized=False,
            environment_vars_configured=False,
            no_hardcoded_secrets=False,
            secret_rotation_configured=False,
            validation_errors=[ValidationResult(
                passed=False,
                message=f"Secrets validation failed: {error}",
                severity="error"
            )]
        )
    
    def _create_failed_validation_results(self, environment: str, error_message: str) -> DeploymentValidationResults:
        """Create failed validation results."""
        return DeploymentValidationResults(
            kubernetes_validation=self._create_error_k8s_results(Exception(error_message)),
            helm_validation=self._create_error_helm_results(Exception(error_message)),
            network_security=self._create_error_network_results(Exception(error_message)),
            secrets_validation=self._create_error_secrets_results(Exception(error_message)),
            deployment_ready=False,
            overall_score=0.0,
            environment=environment,
            recommendations=[
                "Fix validation errors before attempting deployment",
                "Review deployment configuration and try again"
            ]
        )


# Convenience function for quick deployment validation
async def validate_deployment(
    project_root: str = ".",
    environment: str = "development",
    validate_k8s: bool = True,
    validate_helm: bool = True,
    validate_network: bool = True,
    validate_secrets: bool = True
) -> DeploymentValidationResults:
    """
    Convenience function for quick deployment validation.

    This function provides a simple interface to validate deployment readiness
    by instantiating a DeploymentValidator and running comprehensive validation.

    Args:
        project_root: Root directory of the project (default: current directory)
        environment: Target deployment environment (default: development)
        validate_k8s: Whether to validate Kubernetes manifests (default: True)
        validate_helm: Whether to validate Helm charts (default: True)
        validate_network: Whether to validate network security (default: True)
        validate_secrets: Whether to validate secrets management (default: True)

    Returns:
        DeploymentValidationResults with comprehensive validation results

    Example:
        results = await validate_deployment(
            project_root="./my-project",
            environment="staging",
            validate_helm=False
        )
        print(f"Deployment ready: {results.deployment_ready}")
        print(f"Overall score: {results.overall_score:.1f}")
    """
    validator = DeploymentValidator(project_root)
    return await validator.validate_deployment_readiness(
        environment=environment,
        validate_k8s=validate_k8s,
        validate_helm=validate_helm,
        validate_network=validate_network,
        validate_secrets=validate_secrets
    )








