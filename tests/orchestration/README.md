# Testing Orchestration Framework

A comprehensive testing orchestration framework that coordinates multiple testing layers, manages test dependencies, and enforces quality gates for deployment validation.

## Overview

This framework provides:

- **Test Orchestration**: Coordinates execution of unit, integration, E2E, security, accessibility, and performance tests
- **Quality Gates**: Enforces configurable thresholds for coverage, security, and accessibility
- **Comprehensive Reporting**: Generates HTML, JSON, and markdown reports
- **Configuration Management**: Flexible configuration system with environment-specific settings
- **Parallel Execution**: Optimized test execution with dependency management

## Architecture

### Core Components

1. **TestOrchestrator** (`orchestrator.py`): Main coordination class that manages the test execution pipeline
2. **TestRunner** (`runner.py`): Executes different types of tests and collects results
3. **TestReporter** (`reporter.py`): Generates comprehensive reports in multiple formats
4. **QualityGateValidator** (`quality_gates.py`): Validates test results against quality thresholds
5. **ConfigurationManager** (`config.py`): Manages configuration loading and validation
6. **Data Models** (`models.py`): Defines data structures for test results and configuration

### Test Execution Flow

```
Configuration Loading → Test Context Creation → Test Pipeline Execution → Quality Gate Validation → Report Generation
```

## Usage

### Basic Usage

```python
from tests.orchestration import TestOrchestrator, TestContext, TestConfiguration

# Create configuration
config = TestConfiguration(
    run_unit_tests=True,
    run_integration_tests=True,
    min_unit_test_coverage=80.0,
    max_critical_vulnerabilities=0
)

# Create test context
context = TestContext(
    branch="main",
    commit_sha="abc123",
    environment="test",
    test_config=config
)

# Run orchestration
orchestrator = TestOrchestrator(context)
results = await orchestrator.execute_test_pipeline()
quality_passed = await orchestrator.validate_quality_gates(results)
reports = await orchestrator.generate_reports(results)
```

### CLI Usage

```bash
# Run with default settings
python -m tests.orchestration.cli

# Run with custom parameters
python -m tests.orchestration.cli --branch feature/new --commit def456 --environment staging

# Create sample configuration
python -m tests.orchestration.cli --create-sample-config
```

## Configuration

### Configuration Files

The framework supports YAML and JSON configuration files:

- `config.yaml` - Base configuration
- `config.{environment}.yaml` - Environment-specific configuration
- `config.json` - JSON format configuration

### Environment Variables

Configuration can be overridden using environment variables:

- `TEST_MAX_WORKERS` - Maximum parallel workers
- `TEST_MIN_UNIT_COVERAGE` - Minimum unit test coverage
- `TEST_RUN_E2E_TESTS` - Enable/disable E2E tests
- `TEST_MAX_CRITICAL_VULNS` - Maximum critical vulnerabilities

### Sample Configuration

```yaml
# General settings
parallel_execution: true
max_workers: 4
timeout_seconds: 3600

# Test type enablement
run_unit_tests: true
run_integration_tests: true
run_e2e_tests: true
run_security_tests: true
run_accessibility_tests: true
run_performance_tests: true

# Quality gate thresholds
min_unit_test_coverage: 80.0
max_critical_vulnerabilities: 0
max_high_vulnerabilities: 5
max_accessibility_violations: 0

# Reporting settings
generate_html_reports: true
generate_json_reports: true
report_output_dir: test_reports
```

## Quality Gates

The framework enforces the following quality gates:

### Blocking Gates (Prevent Deployment)
- **Unit Test Coverage**: Minimum coverage percentage
- **Critical Security Vulnerabilities**: Maximum allowed critical vulnerabilities
- **High Security Vulnerabilities**: Maximum allowed high vulnerabilities
- **Unit Test Pass Rate**: Minimum percentage of passing unit tests
- **Integration Test Execution**: Integration tests must execute successfully
- **Accessibility Violations**: Maximum critical accessibility violations

### Warning Gates (Non-blocking)
- **Performance Regression**: Maximum allowed performance degradation
- **E2E Test Execution**: E2E tests should execute but failures may not block
- **Response Time Thresholds**: Performance benchmarks

## Test Types

### Unit Tests
- Fast, isolated tests
- Coverage reporting
- Pytest-based execution
- Configurable coverage thresholds

### Integration Tests
- Database and API integration
- Service-to-service communication
- External dependency testing

### End-to-End Tests
- Full user journey testing
- Multi-browser support
- UI interaction validation

### Security Tests
- Static code analysis (Bandit)
- Vulnerability scanning
- Dependency security checks
- Compliance validation

### Accessibility Tests
- WCAG compliance checking
- Screen reader compatibility
- Keyboard navigation testing

### Performance Tests
- Response time measurement
- Throughput testing
- Resource utilization monitoring
- Baseline comparison

## Reporting

### Report Types

1. **JSON Report**: Machine-readable comprehensive results
2. **HTML Report**: Visual dashboard with charts and metrics
3. **Markdown Summary**: Human-readable summary for documentation
4. **Quality Gate Report**: Detailed quality gate analysis

### Report Contents

- Test execution summary
- Coverage metrics
- Security vulnerability details
- Performance benchmarks
- Quality gate results
- Trend analysis (when baseline data available)

## Dependencies

The framework requires the following dependencies:

```
pytest>=7.4.3
pytest-asyncio>=0.21.1
pytest-cov>=4.1.0
pytest-json-report>=1.5.0
jinja2>=3.1.2
pyyaml>=6.0.1
bandit>=1.7.5
```

## Testing

Run the framework's own tests:

```bash
# Run all orchestration tests
python -m pytest tests/test_orchestration.py -v

# Run with coverage
python -m pytest tests/test_orchestration.py --cov=tests.orchestration --cov-report=html

# Run specific test class
python -m pytest tests/test_orchestration.py::TestTestOrchestrator -v
```

## Examples

See `examples/test_orchestration_example.py` for comprehensive usage examples including:

- Basic orchestration setup
- Configuration management
- Quality gate validation scenarios
- Custom test scenarios

## Integration

### CI/CD Integration

The framework is designed for CI/CD integration:

```yaml
# GitHub Actions example
- name: Run Test Orchestration
  run: |
    python -m tests.orchestration.cli \
      --branch ${{ github.ref_name }} \
      --commit ${{ github.sha }} \
      --environment staging
```

### Docker Integration

```dockerfile
# Add to Dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt

# Run tests
CMD ["python", "-m", "tests.orchestration.cli"]
```

## Extending the Framework

### Adding New Test Types

1. Extend `TestRunner` with new test execution methods
2. Add result models to `models.py`
3. Update `TestOrchestrator` to include new test type
4. Add quality gates in `QualityGateValidator`

### Custom Quality Gates

```python
# Add custom quality gate
validator = QualityGateValidator(config)
custom_result = await validator.validate_custom_gate(
    gate_name="Custom Metric",
    threshold=95.0,
    actual_value=98.5,
    blocking=True
)
```

### Custom Reporters

Extend `TestReporter` to add new report formats:

```python
class CustomReporter(TestReporter):
    async def generate_custom_report(self, results):
        # Custom report logic
        pass
```

## Troubleshooting

### Common Issues

1. **Configuration Validation Errors**: Check configuration file syntax and value ranges
2. **Test Execution Timeouts**: Increase `timeout_seconds` in configuration
3. **Quality Gate Failures**: Review thresholds and actual test results
4. **Report Generation Errors**: Ensure output directory permissions and disk space

### Debug Mode

Enable verbose logging:

```bash
python -m tests.orchestration.cli --verbose
```

### Log Analysis

The framework uses structured logging. Key log messages include:

- Test execution start/completion
- Quality gate validation results
- Report generation status
- Configuration loading details

## Contributing

When contributing to the orchestration framework:

1. Add unit tests for new functionality
2. Update documentation and examples
3. Follow existing code patterns and naming conventions
4. Ensure backward compatibility for configuration changes
5. Test with multiple Python versions and environments

## License

This framework is part of the larger testing infrastructure and follows the same licensing terms as the parent project.