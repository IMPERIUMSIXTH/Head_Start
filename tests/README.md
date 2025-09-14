# Enhanced Unit Testing Framework

This directory contains the enhanced unit testing framework with advanced capabilities including property-based testing, async patterns, mutation testing, and comprehensive test fixtures.

## 🚀 Features

### 1. Property-Based Testing with Hypothesis
- **File**: `property_tests.py`
- **Purpose**: Tests system properties and invariants across a wide range of inputs
- **Key Features**:
  - Password hashing consistency tests
  - Security validation property tests
  - Input sanitization property tests
  - Stateful testing for user management

### 2. Async Testing Patterns
- **File**: `async_tests.py`
- **Purpose**: Tests asynchronous functionality with proper async/await patterns
- **Key Features**:
  - Async content processing tests
  - Celery task testing patterns
  - Async error handling and retry patterns
  - Concurrency and performance testing

### 3. Enhanced Test Fixtures
- **File**: `fixtures/complex_fixtures.py`
- **Purpose**: Sophisticated test data and mock configurations
- **Key Features**:
  - Factory classes for generating test data
  - Complex learning scenarios
  - Authentication scenarios with various user states
  - Mock external services

### 4. Mutation Testing
- **File**: `mutmut_config.py`
- **Purpose**: Test quality validation through mutation testing
- **Key Features**:
  - Custom mutation operators
  - Quality gate enforcement
  - Critical function identification
  - Comprehensive reporting

### 5. Test Categorization and Tagging
- **Configuration**: `pytest.ini`, `conftest.py`
- **Purpose**: Organized test execution with custom markers
- **Markers**:
  - `@pytest.mark.unit`: Unit tests (fast, isolated)
  - `@pytest.mark.integration`: Integration tests
  - `@pytest.mark.async`: Asynchronous tests
  - `@pytest.mark.property`: Property-based tests
  - `@pytest.mark.security`: Security-related tests
  - `@pytest.mark.performance`: Performance tests
  - `@pytest.mark.mutation`: Mutation testing validation

## 📁 File Structure

```
tests/
├── README.md                    # This file
├── conftest.py                  # Enhanced pytest configuration
├── property_tests.py            # Property-based tests
├── async_tests.py              # Async testing patterns
├── enhanced_unit_tests.py      # Enhanced unit tests
├── fixtures/
│   └── complex_fixtures.py     # Complex test fixtures
├── unit/                       # Original unit tests
│   ├── test_auth.py
│   ├── test_models.py
│   └── test_user_api.py
├── test_authentication.py      # Authentication tests
└── test_content_processing.py  # Content processing tests
```

## 🛠️ Setup and Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The enhanced testing framework requires these additional packages:
- `pytest-cov`: Coverage reporting
- `pytest-xdist`: Parallel test execution
- `pytest-html`: HTML test reports
- `pytest-benchmark`: Performance benchmarking
- `hypothesis`: Property-based testing
- `mutmut`: Mutation testing
- `factory-boy`: Test data factories
- `faker`: Fake data generation

### 2. Configure Environment

Set environment variables for testing:
```bash
export TESTING=1
export HYPOTHESIS_PROFILE=dev  # or 'ci' for CI/CD
```

## 🧪 Running Tests

### Basic Test Execution

```bash
# Run all unit tests
pytest tests/unit/ -m unit

# Run property-based tests
pytest tests/property_tests.py -m property

# Run async tests
pytest tests/async_tests.py -m async

# Run security tests
pytest -m security

# Run with coverage
pytest --cov=services --cov=api --cov-report=html
```

### Enhanced Test Runner

Use the enhanced test runner for comprehensive testing:

```bash
# Run all test types
python scripts/run_enhanced_tests.py

# Run specific test types
python scripts/run_enhanced_tests.py --types unit property async

# Generate comprehensive report
python scripts/run_enhanced_tests.py --output comprehensive_report.html

# Check quality gates
python scripts/run_enhanced_tests.py --check-gates
```

### Mutation Testing

```bash
# Run mutation tests
python scripts/run_mutation_tests.py

# Run on specific paths
python scripts/run_mutation_tests.py --paths services/auth.py services/security.py

# Check quality gates
python scripts/run_mutation_tests.py --check-gates
```

## 📊 Test Categories and Markers

### Unit Tests (`@pytest.mark.unit`)
- Fast, isolated tests
- Mock external dependencies
- Test individual functions and classes
- High coverage, quick feedback

### Property-Based Tests (`@pytest.mark.property`)
- Test system properties across many inputs
- Use Hypothesis for input generation
- Catch edge cases and invariant violations
- Validate assumptions about system behavior

### Async Tests (`@pytest.mark.async`)
- Test asynchronous operations
- Celery task testing
- Concurrent operation validation
- Async error handling patterns

### Security Tests (`@pytest.mark.security`)
- SQL injection detection
- XSS prevention validation
- Authentication security
- Input sanitization testing

### Performance Tests (`@pytest.mark.performance`)
- Benchmark critical operations
- Load testing patterns
- Memory usage validation
- Concurrency performance

### Integration Tests (`@pytest.mark.integration`)
- Database integration
- External API integration
- Service-to-service communication
- End-to-end workflows

## 🔧 Configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery settings
- Coverage configuration
- Custom markers
- Async test configuration
- Logging and reporting settings

### Hypothesis Configuration
- Profile-based settings (dev, ci, default)
- Example limits and timeouts
- Verbosity levels
- Health check suppression

### Mutation Testing Configuration (`mutmut_config.py`)
- Paths to mutate
- Test commands
- Quality gate thresholds
- Custom mutation operators

## 🏗️ Complex Fixtures

### User Factory
```python
def test_user_creation(sample_user_factory):
    user = sample_user_factory(
        email="test@example.com",
        role="learner",
        is_active=True
    )
    assert user.email == "test@example.com"
```

### Learning Scenarios
```python
def test_recommendation_system(learning_scenario_advanced):
    scenario = learning_scenario_advanced
    users = scenario['users']
    content = scenario['content_items']
    # Test recommendation logic
```

### Mock External Services
```python
def test_content_processing(mock_external_apis):
    # YouTube API, arXiv API, OpenAI API all mocked
    processor = ContentProcessor()
    # Test with mocked responses
```

## 📈 Quality Gates

### Coverage Requirements
- Unit tests: 80% minimum coverage
- Integration tests: 70% minimum coverage
- Critical functions: 90% coverage

### Mutation Testing Thresholds
- Overall mutation score: 75% minimum
- Critical functions: 90% minimum
- Security functions: 85% minimum

### Performance Benchmarks
- Password hashing: < 5 seconds
- API responses: < 200ms (P95)
- Database queries: < 100ms (P95)

## 🚨 Error Handling and Debugging

### Test Failures
1. Check test output for specific failure reasons
2. Use `--tb=long` for detailed tracebacks
3. Run individual tests with `-v` for verbose output
4. Check fixture setup and teardown

### Property Test Failures
1. Hypothesis will show minimal failing examples
2. Use `@example()` decorator to add specific test cases
3. Adjust `assume()` statements to filter invalid inputs
4. Check invariants and properties

### Async Test Issues
1. Ensure proper `await` usage
2. Check event loop configuration
3. Verify mock setup for async operations
4. Use `pytest.mark.asyncio` decorator

### Mutation Test Failures
1. Review survived mutants in the report
2. Add specific test cases for uncaught mutations
3. Improve assertion quality
4. Consider boundary condition testing

## 📚 Best Practices

### Writing Property-Based Tests
1. Focus on invariants and properties
2. Use `assume()` to filter invalid inputs
3. Keep properties simple and focused
4. Add specific examples with `@example()`

### Async Testing
1. Always use `async def` for async tests
2. Properly mock async dependencies
3. Test both success and failure scenarios
4. Consider timeout and retry patterns

### Test Data Management
1. Use factories for consistent test data
2. Clean up test data after tests
3. Avoid hardcoded test values
4. Use realistic but safe test data

### Security Testing
1. Test both positive and negative cases
2. Use realistic attack vectors
3. Validate all input sanitization
4. Test authentication edge cases

## 🔄 CI/CD Integration

### GitHub Actions Integration
```yaml
- name: Run Enhanced Tests
  run: |
    python scripts/run_enhanced_tests.py --check-gates
    
- name: Upload Coverage Reports
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    
- name: Upload Test Reports
  uses: actions/upload-artifact@v3
  with:
    name: test-reports
    path: |
      test_report.html
      htmlcov/
      mutation_report.html
```

### Quality Gate Enforcement
- All tests must pass
- Coverage thresholds must be met
- Mutation score must exceed minimum
- Security tests must pass
- Performance benchmarks must be met

## 📞 Support and Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Database Issues**: Check test database configuration
3. **Async Errors**: Verify event loop setup
4. **Fixture Errors**: Check fixture dependencies and scopes

### Getting Help

1. Check test output and logs
2. Review this documentation
3. Examine example tests
4. Check pytest and Hypothesis documentation

### Contributing

1. Follow existing test patterns
2. Add appropriate markers
3. Include docstrings
4. Update this documentation
5. Ensure quality gates pass