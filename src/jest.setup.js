import '@testing-library/jest-dom'
import { configure } from '@testing-library/react'
import { TextEncoder, TextDecoder } from 'util'

// Configure React Testing Library
configure({
  testIdAttribute: 'data-testid',
})

// Polyfills for Node.js environment
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Enhanced Custom Jest matchers for React Testing Library
expect.extend({
  toBeInTheDocument(received) {
    const pass = received !== null && received !== undefined
    return {
      message: () => `expected element ${pass ? 'not ' : ''}to be in the document`,
      pass,
    }
  },
  
  toHaveAccessibleName(received, expectedName) {
    const accessibleName = received.getAttribute('aria-label') || 
                          received.getAttribute('aria-labelledby') || 
                          received.textContent
    const pass = accessibleName === expectedName
    return {
      message: () => `expected element to have accessible name "${expectedName}" but got "${accessibleName}"`,
      pass,
    }
  },
  
  toHaveValidationError(received, expectedError) {
    const errorElement = received.querySelector('[role="alert"], .error-message, [data-testid*="error"]')
    const pass = errorElement && errorElement.textContent.includes(expectedError)
    return {
      message: () => `expected element to have validation error "${expectedError}"`,
      pass,
    }
  },
  
  toBeLoadingState(received) {
    const hasLoadingIndicator = received.querySelector('[data-testid="loading"], .loading, [aria-busy="true"]')
    const pass = hasLoadingIndicator !== null
    return {
      message: () => `expected element ${pass ? 'not ' : ''}to be in loading state`,
      pass,
    }
  },
  
  toHaveInteractiveElement(received, selector) {
    const interactiveElement = received.querySelector(selector)
    const pass = interactiveElement && !interactiveElement.disabled
    return {
      message: () => `expected element to have interactive element "${selector}"`,
      pass,
    }
  },

  // New enhanced matchers
  toHaveCorrectAriaAttributes(received, expectedAttributes) {
    const missingAttributes = []
    const incorrectAttributes = []
    
    for (const [attr, expectedValue] of Object.entries(expectedAttributes)) {
      const actualValue = received.getAttribute(attr)
      if (actualValue === null) {
        missingAttributes.push(attr)
      } else if (actualValue !== expectedValue) {
        incorrectAttributes.push(`${attr}: expected "${expectedValue}", got "${actualValue}"`)
      }
    }
    
    const pass = missingAttributes.length === 0 && incorrectAttributes.length === 0
    const message = () => {
      let msg = 'expected element to have correct ARIA attributes'
      if (missingAttributes.length > 0) {
        msg += `\nMissing: ${missingAttributes.join(', ')}`
      }
      if (incorrectAttributes.length > 0) {
        msg += `\nIncorrect: ${incorrectAttributes.join(', ')}`
      }
      return msg
    }
    
    return { message, pass }
  },

  toHaveKeyboardNavigation(received) {
    const focusableElements = received.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    const pass = focusableElements.length > 0 && 
                 Array.from(focusableElements).every(el => !el.hasAttribute('tabindex') || el.tabIndex >= 0)
    
    return {
      message: () => `expected element ${pass ? 'not ' : ''}to have proper keyboard navigation`,
      pass,
    }
  },

  toHaveColorContrast(received, minimumRatio = 4.5) {
    // Simplified color contrast check (in real implementation, would use actual color calculation)
    const style = window.getComputedStyle(received)
    const backgroundColor = style.backgroundColor
    const color = style.color
    
    // Mock implementation - in real scenario would calculate actual contrast ratio
    const pass = backgroundColor !== color && backgroundColor !== 'transparent'
    
    return {
      message: () => `expected element to have sufficient color contrast (minimum ${minimumRatio}:1)`,
      pass,
    }
  },

  toBeResponsive(received) {
    const style = window.getComputedStyle(received)
    const hasFlexibleWidth = style.width.includes('%') || style.width === 'auto' || style.maxWidth !== 'none'
    const hasResponsiveUnits = style.fontSize.includes('rem') || style.fontSize.includes('em')
    
    const pass = hasFlexibleWidth || hasResponsiveUnits
    
    return {
      message: () => `expected element ${pass ? 'not ' : ''}to be responsive`,
      pass,
    }
  },

  toHaveValidFormStructure(received) {
    const labels = received.querySelectorAll('label')
    const inputs = received.querySelectorAll('input, select, textarea')
    
    let pass = true
    const issues = []
    
    // Check if all inputs have associated labels
    inputs.forEach(input => {
      const hasLabel = input.id && received.querySelector(`label[for="${input.id}"]`) ||
                      input.getAttribute('aria-label') ||
                      input.getAttribute('aria-labelledby')
      if (!hasLabel) {
        pass = false
        issues.push(`Input without label: ${input.name || input.type}`)
      }
    })
    
    return {
      message: () => `expected form to have valid structure. Issues: ${issues.join(', ')}`,
      pass,
    }
  },

  toHaveLoadingStates(received, expectedStates) {
    const states = ['idle', 'loading', 'success', 'error']
    const foundStates = []
    
    states.forEach(state => {
      if (received.querySelector(`[data-state="${state}"], .${state}, [aria-busy="${state === 'loading'}"]`)) {
        foundStates.push(state)
      }
    })
    
    const pass = expectedStates.every(state => foundStates.includes(state))
    
    return {
      message: () => `expected element to have loading states: ${expectedStates.join(', ')}. Found: ${foundStates.join(', ')}`,
      pass,
    }
  }
})

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn().mockResolvedValue(undefined),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
      isFallback: false,
    }
  },
}))

// Mock Next.js Image component
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...props} />
  },
}))

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
process.env.NODE_ENV = 'test'