# HeadStart E2E Testing Framework

A comprehensive End-to-End testing framework for the HeadStart AI-Powered Learning Recommendation Platform using Playwright.

## Overview

This E2E testing framework provides comprehensive coverage across multiple testing layers:

- **Authentication Workflows**: Login, registration, OAuth flows
- **User Workflows**: Dashboard, preferences, content interaction
- **Mobile Responsive Design**: Cross-device compatibility testing
- **Accessibility Compliance**: WCAG 2.1 AA compliance validation
- **Performance Testing**: Page load times and interaction performance
- **Cross-Browser Testing**: Chrome, Firefox, Safari, Edge compatibility
- **Critical User Paths**: Complete user journey validation

## Architecture

### Test Structure

```
tests/e2e/
├── playwright.config.ts          # Main Playwright configuration
├── global-setup.ts              # Global test setup and data preparation
├── global-teardown.ts           # Global test cleanup
├── e2e_test_runner.py           # Python test orchestration runner
├── package.json                 # Node.js dependencies and scripts
├── page-objects/                # Page Object Model implementations
│   ├── base-page.ts            # Base page with common functionality
│   ├── login-page.ts           # Login page interactions
│   ├── dashboard-page.ts       # Dashboard page interactions
│   └── registration-page.ts    # Registration page interactions
├── tests/                       # Test specifications
│   ├── auth/                   # Authentication tests
│   ├── user/                   # User workflow tests
│   ├── mobile/                 # Mobile responsive tests
│   ├── accessibility/          # Accessibility compliance tests
│   ├── performance/            # Performance validation tests
│   └── critical/               # Critical user path tests
└── test-results/               # Test execution results and artifacts
```

### Key Components

#### 1. E2ETestRunner (Python)
- Orchestrates test execution across multiple browsers and devices
- Manages test data setup and cleanup
- Generates comprehensive reports
- Handles parallel test execution

#### 2. Page Object Model
- Encapsulates page interactions and element locators
- Provides reusable methods for common actions
- Includes accessibility and mobile-specific helpers
- Implements error handling and retry logic

#### 3. Test Suites
- **Authentication**: Login, registration, OAuth, password reset
- **User Workflows**: Dashboard, preferences, profile management
- **Content Management**: Browse, search, interaction workflows
- **Admin Workflows**: User management, content approval, analytics
- **Accessibility**: WCAG compliance, keyboard navigation, screen reader support
- **Performance**: Page load times, interaction timing, resource usage

## Installation and Setup

### Prerequisites

- Node.js 18+ 
- Python 3.8+
- Docker (for backend services)

### Installation

1. **Install Node.js dependencies:**
```bash
cd tests/e2e
npm install
```

2. **Install Playwright browsers:**
```bash
npm run install-browsers
```

3. **Install Python dependencies:**
```bash
pip install -r ../../requirements.txt
```

4. **Start backend services:**
```bash
cd ../..
docker-compose up -d
```

5. **Start frontend development server:**
```bash
cd src
npm run dev
```

## Running Tests

### Quick Start

```bash
# Run all E2E tests
npm test

# Run tests with UI mode
npm run test:ui

# Run specific test suite
npm run test:auth
npm run test:user
npm run test:mobile-responsive
npm run test:accessibility

# Run critical path tests only
npm run test:critical

# Run tests on specific browsers
npm run test:desktop  # Chrome, Firefox, Safari
npm run test:mobile   # Mobile Chrome, Mobile Safari
```

### Using Python Test Runner

```bash
# Run all test suites
python e2e_test_runner.py

# Run specific suite
python e2e_test_runner.py --suite authentication

# Run critical path tests
python e2e_test_runner.py --critical

# Run mobile responsive tests
python e2e_test_runner.py --mobile
```

### Advanced Options

```bash
# Run with debugging
npm run test:debug

# Run with trace collection
npm run test:trace

# Run with video recording
npm run test:video

# Run tests in parallel
npm run test:parallel

# Run with retries
npm run test:retry

# Generate HTML report
npm run test:reporter-html
```

## Test Configuration

### Playwright Configuration

The `playwright.config.ts` file contains:

- **Browser Projects**: Chrome, Firefox, Safari, Edge
- **Mobile Devices**: iPhone, Android, iPad
- **Test Timeouts**: 60 seconds default
- **Retry Logic**: 2 retries on CI
- **Reporters**: HTML, JSON, JUnit
- **Global Setup/Teardown**: Database and test data management

### Environment Variables

```bash
# Test environment configuration
E2E_BASE_URL=http://localhost:3000
E2E_API_URL=http://localhost:8000
E2E_TEST_USER_EMAIL=testuser@example.com
E2E_TEST_USER_PASSWORD=TestPassword123!
E2E_ADMIN_EMAIL=admin@example.com
E2E_ADMIN_PASSWORD=AdminPassword123!

# Browser configuration
HEADLESS=true
SLOW_MO=0
TIMEOUT=60000

# Test data configuration
CREATE_TEST_DATA=true
CLEANUP_TEST_DATA=true
```

## Writing Tests

### Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../page-objects/login-page';

test.describe('Feature Name', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
  });

  test('should perform specific action', async () => {
    await test.step('Step 1: Setup', async () => {
      await loginPage.navigateToLogin();
    });

    await test.step('Step 2: Action', async () => {
      await loginPage.loginWithValidCredentials();
    });

    await test.step('Step 3: Verification', async () => {
      await loginPage.verifyUrl(/.*\/dashboard/);
    });
  });
});
```

### Page Object Pattern

```typescript
export class ExamplePage extends BasePage {
  // Locators
  get submitButton(): Locator {
    return this.page.locator('[data-testid="submit-button"]');
  }

  // Actions
  async performAction(): Promise<void> {
    await this.submitButton.click();
    await this.waitForPageLoad();
  }

  // Verifications
  async verifyResult(): Promise<void> {
    await this.verifyElementVisible(this.submitButton);
  }
}
```

### Mobile Testing

```typescript
test.describe('Mobile Tests', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should work on mobile', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.verifyMobileLoginExperience();
  });
});
```

### Accessibility Testing

```typescript
test('should be accessible', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigateToLogin();
  await loginPage.verifyLoginFormAccessibility();
  await loginPage.checkAccessibility(); // Runs axe-core
});
```

## Test Data Management

### Test User Accounts

The framework automatically creates test users:

- **Regular User**: `testuser@example.com` / `TestPassword123!`
- **Admin User**: `admin@example.com` / `AdminPassword123!`
- **Educator User**: `educator@example.com` / `EducatorPassword123!`

### Test Content

Sample content items are created for testing:
- Machine Learning course (beginner level)
- Python programming tutorial (advanced level)
- Various content types and difficulty levels

### Database Management

- Tests run against a clean database state
- Test data is created before each test run
- Database is cleaned up after test completion
- Isolated test environments prevent data conflicts

## Reporting and Analysis

### HTML Reports

```bash
npm run show-report
```

Generates comprehensive HTML reports with:
- Test execution summary
- Browser compatibility matrix
- Mobile device test results
- Screenshots and videos for failures
- Performance metrics
- Accessibility compliance results

### JSON Reports

Machine-readable reports for CI/CD integration:
- Test results and timing
- Error details and stack traces
- Browser and device coverage
- Performance benchmarks

### Python Test Runner Reports

The Python runner generates additional reports:
- Cross-browser compatibility analysis
- Mobile responsiveness summary
- Performance regression detection
- Quality gate validation results

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd tests/e2e
          npm ci
          npm run install-browsers
      - name: Run E2E tests
        run: |
          cd tests/e2e
          npm test
      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: e2e-test-results
          path: tests/e2e/test-results/
```

### Quality Gates

The framework enforces quality gates:
- **Test Coverage**: Minimum 80% critical path coverage
- **Performance**: Page load times under 3 seconds
- **Accessibility**: Zero WCAG AA violations
- **Cross-Browser**: 95% compatibility across target browsers
- **Mobile**: 100% responsive design compliance

## Troubleshooting

### Common Issues

1. **Browser Installation Failures**
```bash
# Reinstall browsers with dependencies
npm run install-browsers
```

2. **Test Timeouts**
```bash
# Increase timeout for slow environments
npm run test:timeout
```

3. **Flaky Tests**
```bash
# Run with retries
npm run test:retry
```

4. **Debug Mode**
```bash
# Run in debug mode with browser visible
npm run test:debug
```

### Performance Issues

- Use `--workers=1` for serial execution on resource-constrained environments
- Increase timeouts for slow networks
- Use `--headed` mode sparingly to avoid performance overhead

### Test Data Issues

- Verify backend services are running
- Check database connectivity
- Ensure test data creation scripts execute successfully

## Best Practices

### Test Design

1. **Use Page Object Model**: Encapsulate page interactions
2. **Implement Proper Waits**: Use explicit waits for dynamic content
3. **Handle Flaky Elements**: Implement retry logic for unstable elements
4. **Test Real User Scenarios**: Focus on actual user workflows
5. **Maintain Test Independence**: Each test should be self-contained

### Performance

1. **Parallel Execution**: Use multiple workers when possible
2. **Selective Testing**: Run relevant test suites for specific changes
3. **Resource Management**: Clean up test data and browser instances
4. **Efficient Selectors**: Use data-testid attributes for reliable element selection

### Maintenance

1. **Regular Updates**: Keep Playwright and dependencies updated
2. **Test Review**: Regularly review and refactor test code
3. **Documentation**: Maintain up-to-date test documentation
4. **Monitoring**: Track test execution metrics and failure patterns

## Contributing

### Adding New Tests

1. Create test files in appropriate directories
2. Follow existing naming conventions
3. Use Page Object Model for new pages
4. Include accessibility and mobile tests
5. Add performance assertions where relevant

### Extending Page Objects

1. Inherit from `BasePage` for common functionality
2. Use descriptive locator names
3. Implement error handling and retries
4. Add mobile-specific methods when needed
5. Include accessibility verification methods

### Test Data

1. Use factory patterns for test data creation
2. Ensure data cleanup after tests
3. Avoid hardcoded test data in tests
4. Use environment variables for configuration

## Support

For issues and questions:
- Check the troubleshooting section
- Review existing test patterns
- Consult Playwright documentation
- Contact the HeadStart development team

## License

This E2E testing framework is part of the HeadStart project and follows the same licensing terms.