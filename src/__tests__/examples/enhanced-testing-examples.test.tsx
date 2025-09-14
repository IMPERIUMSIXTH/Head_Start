/**
 * Enhanced testing examples demonstrating new React Testing Library improvements
 */

import React from 'react'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  renderWithProviders,
  AccessibilityTester,
  FormTester,
  StateTester,
  PerformanceTester,
  MockUtils,
} from '../utils/component-test-utils'
import { testAccessibility, WCAGComplianceChecker, KeyboardNavigationTester } from '../utils/accessibility-helpers'
import { VisualRegressionTester, testVisualRegression } from '../utils/visual-testing'

// Mock components for testing examples
const MockButton = ({ children, onClick, disabled, ...props }: any) => (
  <button onClick={onClick} disabled={disabled} {...props}>
    {children}
  </button>
)

const MockForm = ({ onSubmit }: any) => {
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [errors, setErrors] = React.useState<Record<string, string>>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const newErrors: Record<string, string> = {}
    
    if (!email) newErrors.email = 'Email is required'
    if (!password) newErrors.password = 'Password is required'
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }
    
    onSubmit({ email, password })
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-describedby={errors.email ? 'email-error' : undefined}
        />
        {errors.email && (
          <div id="email-error" role="alert">
            {errors.email}
          </div>
        )}
      </div>
      
      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-describedby={errors.password ? 'password-error' : undefined}
        />
        {errors.password && (
          <div id="password-error" role="alert">
            {errors.password}
          </div>
        )}
      </div>
      
      <button type="submit">Submit</button>
    </form>
  )
}

const MockModal = ({ isOpen, onClose, children }: any) => {
  if (!isOpen) return null

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div>
        <h2 id="modal-title">Modal Title</h2>
        <button onClick={onClose} aria-label="Close modal">
          ×
        </button>
        {children}
      </div>
    </div>
  )
}

const MockLoadingComponent = ({ isLoading }: any) => (
  <div>
    {isLoading ? (
      <div data-testid="loading" aria-busy="true">
        Loading...
      </div>
    ) : (
      <div data-testid="content">Content loaded</div>
    )}
  </div>
)

describe('Enhanced React Testing Library Examples', () => {
  afterEach(() => {
    MockUtils.cleanup()
  })

  describe('Enhanced Custom Matchers', () => {
    test('should use enhanced accessibility matchers', () => {
      const { container } = renderWithProviders(
        <button aria-label="Save document" aria-describedby="save-help">
          Save
        </button>
      )

      const button = screen.getByRole('button')
      
      // Test enhanced matchers
      expect(button).toHaveAccessibleName('Save document')
      expect(button).toHaveCorrectAriaAttributes({
        'aria-label': 'Save document',
        'aria-describedby': 'save-help',
      })
      expect(container).toHaveKeyboardNavigation()
    })

    test('should validate form structure', () => {
      const { container } = renderWithProviders(
        <MockForm onSubmit={jest.fn()} />
      )

      expect(container).toHaveValidFormStructure()
    })

    test('should test loading states', () => {
      const { container } = renderWithProviders(
        <MockLoadingComponent isLoading={true} />
      )

      expect(container).toHaveLoadingStates(['loading'])
    })
  })

  describe('Component Interaction Testing', () => {
    test('should test form submission with validation', async () => {
      const mockSubmit = jest.fn()
      const formTester = new FormTester()

      renderWithProviders(<MockForm onSubmit={mockSubmit} />)

      // Test validation with invalid data
      await formTester.testValidation(
        { email: '', password: '' },
        { email: 'Email is required', password: 'Password is required' }
      )

      expect(mockSubmit).not.toHaveBeenCalled()

      // Test successful submission
      await formTester.testSuccessfulSubmission({
        email: 'test@example.com',
        password: 'password123',
      })

      expect(mockSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
    })

    test('should test modal interactions', async () => {
      const mockClose = jest.fn()
      const user = userEvent.setup()

      renderWithProviders(
        <MockModal isOpen={true} onClose={mockClose}>
          <p>Modal content</p>
        </MockModal>
      )

      const modal = screen.getByRole('dialog')
      expect(modal).toBeInTheDocument()

      // Test close button
      const closeButton = screen.getByLabelText('Close modal')
      await user.click(closeButton)

      expect(mockClose).toHaveBeenCalled()
    })

    test('should test keyboard navigation', async () => {
      const { container } = renderWithProviders(
        <div>
          <button>First</button>
          <button>Second</button>
          <button>Third</button>
        </div>
      )

      await AccessibilityTester.testKeyboardNavigation(container)
    })
  })

  describe('Accessibility Testing', () => {
    test('should run comprehensive accessibility audit', async () => {
      const { container } = renderWithProviders(
        <div>
          <h1>Main Title</h1>
          <button aria-label="Action button">Click me</button>
          <img src="test.jpg" alt="Test image" />
        </div>
      )

      const results = await testAccessibility(container, {
        wcagLevel: 'AA',
      })

      expect(results.wcag.passed).toBe(true)
      expect(results.wcag.violations).toHaveLength(0)
    })

    test('should test WCAG compliance', async () => {
      const { container } = renderWithProviders(
        <form>
          <label htmlFor="username">Username</label>
          <input id="username" type="text" required aria-required="true" />
          <button type="submit">Submit</button>
        </form>
      )

      const checker = new WCAGComplianceChecker({ wcagLevel: 'AA' })
      const results = await checker.auditComponent(container)

      expect(results.passed).toBe(true)
    })

    test('should test keyboard navigation patterns', async () => {
      const { container } = renderWithProviders(
        <nav role="navigation">
          <ul>
            <li><a href="#home">Home</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#contact">Contact</a></li>
          </ul>
        </nav>
      )

      const keyboardTester = new KeyboardNavigationTester()
      const results = await keyboardTester.testTabNavigation(container)

      expect(results.passed).toBe(true)
      expect(results.focusOrder).toHaveLength(3)
    })

    test('should test focus management in modals', async () => {
      const { container } = renderWithProviders(
        <MockModal isOpen={true} onClose={jest.fn()}>
          <input type="text" placeholder="First input" />
          <button>Action</button>
          <button>Cancel</button>
        </MockModal>
      )

      const modal = container.querySelector('[role="dialog"]') as HTMLElement
      await AccessibilityTester.testFocusManagement(modal)
    })
  })

  describe('State Testing', () => {
    test('should test loading states', async () => {
      let isLoading = true
      const { rerender } = renderWithProviders(
        <MockLoadingComponent isLoading={isLoading} />
      )

      // Initial loading state
      expect(screen.getByTestId('loading')).toBeInTheDocument()

      // Change to loaded state
      isLoading = false
      rerender(<MockLoadingComponent isLoading={isLoading} />)

      expect(screen.queryByTestId('loading')).not.toBeInTheDocument()
      expect(screen.getByTestId('content')).toBeInTheDocument()
    })

    test('should test error states', async () => {
      MockUtils.mockApiResponse('/api/data', { error: 'Server error' }, 500)

      const ErrorComponent = () => {
        const [error, setError] = React.useState('')

        React.useEffect(() => {
          fetch('/api/data')
            .then(res => res.json())
            .then(data => {
              if (data.error) {
                setError(data.error)
              }
            })
        }, [])

        return error ? <div role="alert">{error}</div> : <div>No error</div>
      }

      await StateTester.testErrorStates(
        <ErrorComponent />,
        async () => {
          // Error is triggered by useEffect
        },
        'Server error'
      )
    })
  })

  describe('Performance Testing', () => {
    test('should measure render performance', () => {
      const renderTime = PerformanceTester.measureRenderTime(
        <div>
          {Array.from({ length: 100 }, (_, i) => (
            <div key={i}>Item {i}</div>
          ))}
        </div>
      )

      // Render time should be reasonable (less than 100ms for this simple component)
      expect(renderTime).toBeLessThan(100)
    })

    test('should test re-render optimization', () => {
      const MemoizedComponent = React.memo(({ count }: { count: number }) => (
        <div>Count: {count}</div>
      ))

      const renderCount = PerformanceTester.testRerenderOptimization(
        <MemoizedComponent count={1} />,
        [
          { count: 1 }, // Same props, should not re-render
          { count: 2 }, // Different props, should re-render
          { count: 2 }, // Same props again, should not re-render
        ]
      )

      // Should render: initial + prop change = 2 times
      expect(renderCount).toBe(2)
    })
  })

  describe('Visual Regression Testing', () => {
    test('should test component visual states', async () => {
      const visualTester = new VisualRegressionTester()

      const results = await visualTester.testComponentStates(
        [
          { name: 'default', component: <MockButton>Default</MockButton> },
          { name: 'disabled', component: <MockButton disabled>Disabled</MockButton> },
          { name: 'loading', component: <MockButton>Loading...</MockButton> },
        ],
        'button-states'
      )

      expect(results).toHaveLength(3)
      results.forEach(result => {
        expect(result.passed).toBe(true)
      })
    })

    test('should test responsive design', async () => {
      const results = await testVisualRegression(
        <div style={{ width: '100%', padding: '1rem' }}>
          <h1>Responsive Title</h1>
          <p>This content should adapt to different screen sizes.</p>
        </div>,
        'responsive-content',
        {
          viewports: [
            { width: 375, height: 667, name: 'mobile' },
            { width: 768, height: 1024, name: 'tablet' },
            { width: 1200, height: 800, name: 'desktop' },
          ],
        }
      )

      expect(results).toHaveLength(6) // 3 viewports × 2 themes (light/dark)
    })
  })

  describe('Mock Utilities', () => {
    test('should mock API responses', async () => {
      MockUtils.mockApiResponse('/api/users', { users: [{ id: 1, name: 'John' }] })

      const response = await fetch('/api/users')
      const data = await response.json()

      expect(data.users).toHaveLength(1)
      expect(data.users[0].name).toBe('John')
    })

    test('should mock localStorage', () => {
      const localStorageMock = MockUtils.mockLocalStorage()

      localStorage.setItem('test', 'value')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('test', 'value')

      localStorageMock.getItem.mockReturnValue('value')
      expect(localStorage.getItem('test')).toBe('value')
    })

    test('should mock IntersectionObserver', () => {
      const mockObserver = MockUtils.mockIntersectionObserver()

      const observer = new IntersectionObserver(jest.fn())
      const element = document.createElement('div')

      observer.observe(element)
      expect(mockObserver().observe).toHaveBeenCalledWith(element)
    })
  })
})

// Test categorization examples
describe('Unit Tests', () => {
  test('should be categorized as unit test', () => {
    // This test would be run with: npm run test:unit
    expect(true).toBe(true)
  })
})

describe('Integration Tests', () => {
  test('should be categorized as integration test', () => {
    // This test would be run with: npm run test:integration
    expect(true).toBe(true)
  })
})

describe('Accessibility Tests', () => {
  test('should be categorized as accessibility test', () => {
    // This test would be run with: npm run test:accessibility
    expect(true).toBe(true)
  })
})

describe('Visual Tests', () => {
  test('should be categorized as visual test', () => {
    // This test would be run with: npm run test:visual
    expect(true).toBe(true)
  })
})