import { render, screen, fireEvent, waitFor, within, RenderOptions } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReactElement, ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

/**
 * Enhanced component testing utilities
 */

export interface TestWrapperProps {
  children: ReactNode
  queryClient?: QueryClient
  initialEntries?: string[]
}

/**
 * Test wrapper component with providers
 */
export function TestWrapper({ children, queryClient, initialEntries = ['/'] }: TestWrapperProps) {
  const testQueryClient = queryClient || new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })

  return (
    <QueryClientProvider client={testQueryClient}>
      {children}
    </QueryClientProvider>
  )
}

/**
 * Enhanced render function with providers
 */
export function renderWithProviders(
  ui: ReactElement,
  options: RenderOptions & {
    queryClient?: QueryClient
    initialEntries?: string[]
  } = {}
) {
  const { queryClient, initialEntries, ...renderOptions } = options

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <TestWrapper queryClient={queryClient} initialEntries={initialEntries}>
      {children}
    </TestWrapper>
  )

  return {
    user: userEvent.setup(),
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  }
}

/**
 * Accessibility testing utilities
 */
export class AccessibilityTester {
  /**
   * Test keyboard navigation through focusable elements
   */
  static async testKeyboardNavigation(container: HTMLElement) {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )

    const user = userEvent.setup()
    
    // Test Tab navigation forward
    for (let i = 0; i < focusableElements.length; i++) {
      await user.tab()
      expect(focusableElements[i]).toHaveFocus()
    }

    // Test Shift+Tab navigation backward
    for (let i = focusableElements.length - 1; i >= 0; i--) {
      await user.tab({ shift: true })
      expect(focusableElements[i]).toHaveFocus()
    }
  }

  /**
   * Test ARIA attributes and roles
   */
  static testAriaCompliance(element: HTMLElement, expectedAttributes: Record<string, string>) {
    Object.entries(expectedAttributes).forEach(([attr, expectedValue]) => {
      expect(element).toHaveAttribute(attr, expectedValue)
    })
  }

  /**
   * Test screen reader announcements
   */
  static testScreenReaderAnnouncements(container: HTMLElement) {
    const liveRegions = container.querySelectorAll('[aria-live]')
    const alerts = container.querySelectorAll('[role="alert"]')
    const status = container.querySelectorAll('[role="status"]')

    return {
      liveRegions: Array.from(liveRegions),
      alerts: Array.from(alerts),
      status: Array.from(status),
    }
  }

  /**
   * Test color contrast (simplified check)
   */
  static testColorContrast(element: HTMLElement, minimumRatio = 4.5) {
    const style = window.getComputedStyle(element)
    const backgroundColor = style.backgroundColor
    const color = style.color

    // In a real implementation, you would calculate the actual contrast ratio
    // This is a simplified check
    expect(backgroundColor).not.toBe(color)
    expect(backgroundColor).not.toBe('transparent')
  }

  /**
   * Test focus management in modals/dialogs
   */
  static async testFocusManagement(modalElement: HTMLElement) {
    const user = userEvent.setup()
    
    // Test that focus is trapped within modal
    const focusableElements = modalElement.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )

    if (focusableElements.length > 0) {
      // Focus should be on first focusable element
      expect(focusableElements[0]).toHaveFocus()

      // Tab to last element
      for (let i = 1; i < focusableElements.length; i++) {
        await user.tab()
      }

      // Tab from last element should go to first
      await user.tab()
      expect(focusableElements[0]).toHaveFocus()
    }
  }
}

/**
 * Form testing utilities
 */
export class FormTester {
  private user = userEvent.setup()

  /**
   * Fill form with data and validate
   */
  async fillForm(formData: Record<string, string | boolean | number>) {
    for (const [fieldName, value] of Object.entries(formData)) {
      const field = screen.getByLabelText(new RegExp(fieldName, 'i'))
      
      if (field.type === 'checkbox' || field.type === 'radio') {
        if (value) {
          await this.user.click(field)
        }
      } else {
        await this.user.clear(field)
        await this.user.type(field, String(value))
      }
    }
  }

  /**
   * Test form validation
   */
  async testValidation(
    invalidData: Record<string, string>,
    expectedErrors: Record<string, string>
  ) {
    await this.fillForm(invalidData)
    
    const submitButton = screen.getByRole('button', { name: /submit|save|create/i })
    await this.user.click(submitButton)

    // Check for validation errors
    for (const [fieldName, expectedError] of Object.entries(expectedErrors)) {
      await waitFor(() => {
        const errorElement = screen.getByText(new RegExp(expectedError, 'i'))
        expect(errorElement).toBeInTheDocument()
      })
    }
  }

  /**
   * Test successful form submission
   */
  async testSuccessfulSubmission(
    validData: Record<string, string | boolean | number>,
    expectedSuccessMessage?: string
  ) {
    await this.fillForm(validData)
    
    const submitButton = screen.getByRole('button', { name: /submit|save|create/i })
    await this.user.click(submitButton)

    if (expectedSuccessMessage) {
      await waitFor(() => {
        const successElement = screen.getByText(new RegExp(expectedSuccessMessage, 'i'))
        expect(successElement).toBeInTheDocument()
      })
    }
  }
}

/**
 * Component state testing utilities
 */
export class StateTester {
  /**
   * Test loading states
   */
  static async testLoadingStates(
    component: ReactElement,
    triggerAction: () => Promise<void>
  ) {
    const { user } = renderWithProviders(component)
    
    // Initial state should not be loading
    expect(screen.queryByTestId('loading')).not.toBeInTheDocument()
    
    // Trigger action that causes loading
    await triggerAction()
    
    // Should show loading state
    expect(screen.getByTestId('loading')).toBeInTheDocument()
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByTestId('loading')).not.toBeInTheDocument()
    })
  }

  /**
   * Test error states
   */
  static async testErrorStates(
    component: ReactElement,
    triggerError: () => Promise<void>,
    expectedErrorMessage: string
  ) {
    renderWithProviders(component)
    
    await triggerError()
    
    await waitFor(() => {
      const errorElement = screen.getByRole('alert')
      expect(errorElement).toHaveTextContent(expectedErrorMessage)
    })
  }

  /**
   * Test empty states
   */
  static testEmptyState(component: ReactElement, emptyStateMessage: string) {
    renderWithProviders(component)
    
    const emptyStateElement = screen.getByText(new RegExp(emptyStateMessage, 'i'))
    expect(emptyStateElement).toBeInTheDocument()
  }
}

/**
 * Performance testing utilities
 */
export class PerformanceTester {
  /**
   * Measure component render time
   */
  static measureRenderTime(component: ReactElement): number {
    const startTime = performance.now()
    renderWithProviders(component)
    const endTime = performance.now()
    
    return endTime - startTime
  }

  /**
   * Test component re-render optimization
   */
  static testRerenderOptimization(
    component: ReactElement,
    propsChanges: Array<Record<string, any>>
  ) {
    let renderCount = 0
    
    const TestComponent = (props: any) => {
      renderCount++
      return component
    }

    const { rerender } = renderWithProviders(<TestComponent />)
    
    propsChanges.forEach(props => {
      rerender(<TestComponent {...props} />)
    })

    return renderCount
  }
}

/**
 * Mock utilities for testing
 */
export class MockUtils {
  /**
   * Mock API responses
   */
  static mockApiResponse(url: string, response: any, status = 200, delay = 0) {
    global.fetch = jest.fn().mockImplementation((requestUrl) => {
      if (requestUrl.includes(url)) {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve({
              ok: status >= 200 && status < 300,
              status,
              json: () => Promise.resolve(response),
              text: () => Promise.resolve(JSON.stringify(response)),
            })
          }, delay)
        })
      }
      return Promise.reject(new Error(`Unhandled request: ${requestUrl}`))
    })
  }

  /**
   * Mock localStorage
   */
  static mockLocalStorage() {
    const localStorageMock = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    }
    
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
    })
    
    return localStorageMock
  }

  /**
   * Mock IntersectionObserver for lazy loading tests
   */
  static mockIntersectionObserver() {
    const mockIntersectionObserver = jest.fn()
    mockIntersectionObserver.mockReturnValue({
      observe: jest.fn(),
      unobserve: jest.fn(),
      disconnect: jest.fn(),
    })
    
    window.IntersectionObserver = mockIntersectionObserver
    
    return mockIntersectionObserver
  }

  /**
   * Clean up all mocks
   */
  static cleanup() {
    jest.restoreAllMocks()
    if (global.fetch && typeof global.fetch.mockRestore === 'function') {
      global.fetch.mockRestore()
    }
  }
}

// Export commonly used testing utilities
export {
  screen,
  fireEvent,
  waitFor,
  within,
  userEvent,
}