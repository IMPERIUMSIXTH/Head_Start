# Enhanced Frontend Testing Framework

This directory contains the enhanced React Testing Library setup with comprehensive testing capabilities including accessibility testing, visual regression testing, component interaction testing, and performance testing.

## 🚀 Features

### Enhanced Jest Configuration
- **Custom Matchers**: Extended Jest matchers for accessibility, form validation, loading states, and more
- **Test Categorization**: Organized tests by type (unit, integration, accessibility, visual, performance)
- **Global Setup/Teardown**: Automated test environment management
- **Enhanced Reporting**: JUnit XML reports, coverage thresholds, and detailed test results

### Accessibility Testing
- **WCAG Compliance**: Automated WCAG 2.1 AA/AAA compliance checking
- **Keyboard Navigation**: Comprehensive keyboard navigation testing
- **Screen Reader Support**: Accessible name and description validation
- **Color Contrast**: Automated color contrast ratio checking
- **Focus Management**: Focus trap and focus order validation

### Visual Regression Testing
- **Chromatic Integration**: Automated visual regression testing with Chromatic
- **Multi-Viewport Testing**: Test across mobile, tablet, desktop, and large desktop viewports
- **Theme Testing**: Light mode, dark mode, and high contrast theme validation
- **Responsive Design**: Automated responsive design testing
- **Component State Testing**: Visual testing of different component states

### Component Interaction Testing
- **Form Testing**: Comprehensive form validation and submission testing
- **Modal/Dialog Testing**: Focus management and interaction testing
- **Drag & Drop**: Drag and drop interaction testing
- **Infinite Scroll**: Pagination and infinite scroll testing
- **Search/Filter**: Search and filter functionality testing

### Performance Testing
- **Render Performance**: Component render time measurement
- **Re-render Optimization**: Test component re-render optimization
- **Memory Usage**: Memory leak detection and monitoring
- **Bundle Size**: Bundle size impact analysis

## 📁 Directory Structure

```
src/__tests__/
├── config/
│   └── test-config.ts          # Comprehensive test configuration
├── examples/
│   ├── enhanced-testing-examples.test.tsx  # Example tests demonstrating all features
│   └── example-component.stories.tsx       # Storybook stories for visual testing
├── utils/
│   ├── accessibility-helpers.ts            # Accessibility testing utilities
│   ├── component-test-utils.ts             # Enhanced component testing utilities
│   ├── testing-patterns.ts                 # Component interaction testing patterns
│   └── visual-testing.ts                   # Visual regression testing utilities
└── README.md                               # This file
```

## 🛠️ Setup and Configuration

### Prerequisites

```bash
npm install --save-dev \
  jest \
  jest-junit \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  jest-environment-jsdom \
  @storybook/react \
  @storybook/addon-a11y \
  @storybook/addon-viewport \
  @storybook/addon-interactions \
  chromatic \
  puppeteer \
  @axe-core/playwright
```

### Environment Variables

Create a `.env.test` file:

```bash
NODE_ENV=test
NEXT_PUBLIC_API_URL=http://localhost:8000
CHROMATIC_PROJECT_TOKEN=your_chromatic_token_here
```

### Jest Configuration

The enhanced Jest configuration includes:

- Custom matchers for accessibility and component testing
- Test categorization and filtering
- Enhanced coverage reporting
- Global setup and teardown

### Storybook Configuration

Enhanced Storybook setup with:

- Accessibility addon (a11y)
- Viewport addon for responsive testing
- Interactions addon for interaction testing
- Chromatic integration for visual regression testing

## 🧪 Running Tests

### All Tests
```bash
npm test
```

### Test Categories
```bash
npm run test:unit           # Unit tests only
npm run test:integration    # Integration tests only
npm run test:accessibility  # Accessibility tests only
npm run test:visual         # Visual regression tests only
```

### Coverage Reports
```bash
npm run test:coverage       # Generate coverage report
```

### Visual Testing
```bash
npm run visual-test         # Run Chromatic visual tests
npm run chromatic          # Run Chromatic with current changes
npm run chromatic:ci       # Run Chromatic in CI mode
```

### Storybook
```bash
npm run storybook          # Start Storybook development server
npm run build-storybook    # Build Storybook for production
```

## 📝 Writing Tests

### Basic Component Test

```typescript
import { renderWithProviders, screen } from '../utils/component-test-utils'
import { MyComponent } from '../../components/MyComponent'

describe('MyComponent', () => {
  test('should render correctly', () => {
    renderWithProviders(<MyComponent title="Test" />)
    
    expect(screen.getByText('Test')).toBeInTheDocument()
  })
})
```

### Accessibility Test

```typescript
import { testAccessibility } from '../utils/accessibility-helpers'
import { renderWithProviders } from '../utils/component-test-utils'

test('should be accessible', async () => {
  const { container } = renderWithProviders(<MyComponent />)
  
  const results = await testAccessibility(container, {
    wcagLevel: 'AA'
  })
  
  expect(results.wcag.passed).toBe(true)
  expect(results.wcag.violations).toHaveLength(0)
})
```

### Form Testing

```typescript
import { FormTester } from '../utils/component-test-utils'

test('should handle form submission', async () => {
  const mockSubmit = jest.fn()
  const formTester = new FormTester()
  
  renderWithProviders(<MyForm onSubmit={mockSubmit} />)
  
  await formTester.testSuccessfulSubmission({
    email: 'test@example.com',
    password: 'password123'
  })
  
  expect(mockSubmit).toHaveBeenCalledWith({
    email: 'test@example.com',
    password: 'password123'
  })
})
```

### Visual Regression Test

```typescript
import { testVisualRegression } from '../utils/visual-testing'

test('should match visual snapshot', async () => {
  const results = await testVisualRegression(
    <MyComponent variant="primary" />,
    'my-component-primary',
    {
      viewports: [
        { width: 375, height: 667, name: 'mobile' },
        { width: 1200, height: 800, name: 'desktop' }
      ]
    }
  )
  
  expect(results.every(r => r.passed)).toBe(true)
})
```

### Performance Test

```typescript
import { PerformanceTester } from '../utils/component-test-utils'

test('should render within performance threshold', () => {
  const renderTime = PerformanceTester.measureRenderTime(
    <MyComponent />
  )
  
  expect(renderTime).toBeLessThan(100) // 100ms threshold
})
```

## 📊 Custom Matchers

### Accessibility Matchers

```typescript
expect(element).toHaveAccessibleName('Button label')
expect(element).toHaveCorrectAriaAttributes({
  'aria-label': 'Close dialog',
  'aria-expanded': 'false'
})
expect(container).toHaveKeyboardNavigation()
expect(element).toHaveColorContrast(4.5)
```

### Component State Matchers

```typescript
expect(element).toBeLoadingState()
expect(element).toHaveValidationError('Email is required')
expect(container).toHaveValidFormStructure()
expect(element).toBeResponsive()
```

## 🎨 Storybook Stories

### Basic Story

```typescript
export const Default: Story = {
  args: {
    title: 'Default Component'
  }
}
```

### Accessibility Story

```typescript
export const AccessibilityTest: Story = {
  parameters: {
    a11y: {
      config: {
        rules: [
          { id: 'color-contrast', enabled: true },
          { id: 'keyboard-navigation', enabled: true }
        ]
      }
    }
  }
}
```

### Visual Regression Story

```typescript
export const VisualRegression: Story = {
  parameters: {
    chromatic: {
      viewports: [375, 768, 1200, 1920],
      delay: 300
    }
  }
}
```

### Interaction Story

```typescript
export const WithInteraction: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const button = canvas.getByRole('button')
    
    await userEvent.click(button)
    await expect(canvas.getByText('Clicked!')).toBeInTheDocument()
  }
}
```

## 🔧 Configuration

### Test Configuration

The test configuration is managed in `config/test-config.ts` and includes:

- Accessibility testing settings (WCAG level, rules)
- Visual testing settings (viewports, themes, delays)
- Performance testing thresholds
- Coverage requirements
- Reporting formats

### Environment-Specific Configs

```typescript
import { getTestConfig } from './config/test-config'

const config = getTestConfig('ci') // 'development', 'ci', 'production'
```

## 🚨 Quality Gates

The testing framework enforces quality gates:

### Accessibility
- Zero critical accessibility violations
- WCAG AA compliance minimum
- Keyboard navigation support required

### Performance
- Maximum render time: 100ms
- Maximum memory usage: 50MB
- Bundle size impact monitoring

### Coverage
- Minimum 80% code coverage
- Component coverage: 85%
- Critical path coverage: 95%

### Visual
- Maximum 20% pixel difference
- Layout shift threshold: 0.1

## 🔍 Debugging

### Test Debugging

```bash
# Run tests in debug mode
npm test -- --verbose --no-cache

# Run specific test file
npm test MyComponent.test.tsx

# Run tests in watch mode
npm run test:watch
```

### Visual Debugging

```bash
# Run Chromatic with debug info
npm run chromatic -- --debug

# Build Storybook locally for inspection
npm run build-storybook
npx http-server storybook-static
```

## 📈 Continuous Integration

### GitHub Actions Integration

```yaml
- name: Run Tests
  run: |
    npm run test:coverage
    npm run test:accessibility
    npm run chromatic:ci

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage/lcov.info
```

### Quality Gate Enforcement

The CI pipeline enforces all quality gates and blocks deployment if:
- Test coverage falls below thresholds
- Accessibility violations are found
- Performance regressions are detected
- Visual regressions are not approved

## 🤝 Contributing

When adding new tests:

1. Follow the established patterns in `examples/`
2. Add appropriate accessibility tests
3. Include visual regression tests for UI components
4. Ensure performance tests for complex components
5. Update this README if adding new utilities

## 📚 Resources

- [React Testing Library Documentation](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Storybook Documentation](https://storybook.js.org/docs/react/get-started/introduction)
- [Chromatic Documentation](https://www.chromatic.com/docs/)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)