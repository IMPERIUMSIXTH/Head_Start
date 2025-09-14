import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

/**
 * Comprehensive accessibility testing helpers
 */

export interface AccessibilityTestOptions {
  skipColorContrast?: boolean
  skipKeyboardNavigation?: boolean
  skipScreenReader?: boolean
  wcagLevel?: 'A' | 'AA' | 'AAA'
}

/**
 * WCAG compliance checker
 */
export class WCAGComplianceChecker {
  private options: AccessibilityTestOptions

  constructor(options: AccessibilityTestOptions = {}) {
    this.options = {
      wcagLevel: 'AA',
      ...options,
    }
  }

  /**
   * Run comprehensive accessibility audit
   */
  async auditComponent(container: HTMLElement) {
    const results = {
      passed: true,
      violations: [] as string[],
      warnings: [] as string[],
    }

    // Check semantic HTML structure
    this.checkSemanticStructure(container, results)

    // Check ARIA attributes
    this.checkAriaAttributes(container, results)

    // Check keyboard navigation
    if (!this.options.skipKeyboardNavigation) {
      await this.checkKeyboardNavigation(container, results)
    }

    // Check color contrast
    if (!this.options.skipColorContrast) {
      this.checkColorContrast(container, results)
    }

    // Check screen reader support
    if (!this.options.skipScreenReader) {
      this.checkScreenReaderSupport(container, results)
    }

    // Check form accessibility
    this.checkFormAccessibility(container, results)

    // Check image accessibility
    this.checkImageAccessibility(container, results)

    return results
  }

  /**
   * Check semantic HTML structure
   */
  private checkSemanticStructure(container: HTMLElement, results: any) {
    // Check for proper heading hierarchy
    const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6')
    let previousLevel = 0

    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName.charAt(1))
      
      if (index === 0 && level !== 1) {
        results.warnings.push('First heading should be h1')
      }
      
      if (level > previousLevel + 1) {
        results.violations.push(`Heading level skipped: ${heading.tagName} after h${previousLevel}`)
        results.passed = false
      }
      
      previousLevel = level
    })

    // Check for landmark elements
    const landmarks = container.querySelectorAll('main, nav, aside, section, article, header, footer')
    if (landmarks.length === 0 && container.children.length > 0) {
      results.warnings.push('No landmark elements found - consider using semantic HTML5 elements')
    }

    // Check for list structure
    const listItems = container.querySelectorAll('li')
    listItems.forEach(li => {
      const parent = li.parentElement
      if (parent && !['ul', 'ol', 'menu'].includes(parent.tagName.toLowerCase())) {
        results.violations.push('List item not contained in proper list element')
        results.passed = false
      }
    })
  }

  /**
   * Check ARIA attributes
   */
  private checkAriaAttributes(container: HTMLElement, results: any) {
    // Check for required ARIA attributes
    const elementsWithRoles = container.querySelectorAll('[role]')
    
    elementsWithRoles.forEach(element => {
      const role = element.getAttribute('role')
      
      // Check role-specific requirements
      switch (role) {
        case 'button':
          if (!element.getAttribute('aria-label') && !element.textContent?.trim()) {
            results.violations.push('Button role requires accessible name')
            results.passed = false
          }
          break
        case 'dialog':
          if (!element.getAttribute('aria-labelledby') && !element.getAttribute('aria-label')) {
            results.violations.push('Dialog requires aria-labelledby or aria-label')
            results.passed = false
          }
          break
        case 'tabpanel':
          if (!element.getAttribute('aria-labelledby')) {
            results.violations.push('Tabpanel requires aria-labelledby')
            results.passed = false
          }
          break
      }
    })

    // Check for invalid ARIA attributes
    const allElements = container.querySelectorAll('*')
    allElements.forEach(element => {
      Array.from(element.attributes).forEach(attr => {
        if (attr.name.startsWith('aria-')) {
          // Validate ARIA attribute names (simplified check)
          const validAriaAttributes = [
            'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-hidden',
            'aria-expanded', 'aria-selected', 'aria-checked', 'aria-disabled',
            'aria-live', 'aria-atomic', 'aria-busy', 'aria-controls',
            'aria-owns', 'aria-current', 'aria-level', 'aria-setsize',
            'aria-posinset', 'aria-required', 'aria-invalid'
          ]
          
          if (!validAriaAttributes.includes(attr.name)) {
            results.warnings.push(`Unknown ARIA attribute: ${attr.name}`)
          }
        }
      })
    })
  }

  /**
   * Check keyboard navigation
   */
  private async checkKeyboardNavigation(container: HTMLElement, results: any) {
    const user = userEvent.setup()
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )

    // Check if focusable elements exist
    if (focusableElements.length === 0) {
      results.warnings.push('No focusable elements found')
      return
    }

    // Check tabindex values
    focusableElements.forEach(element => {
      const tabIndex = element.getAttribute('tabindex')
      if (tabIndex && parseInt(tabIndex) > 0) {
        results.warnings.push('Positive tabindex values can cause navigation issues')
      }
    })

    // Test focus visibility
    focusableElements.forEach(element => {
      const style = window.getComputedStyle(element, ':focus')
      if (style.outline === 'none' && !style.boxShadow && !style.border) {
        results.violations.push('Focusable element lacks visible focus indicator')
        results.passed = false
      }
    })
  }

  /**
   * Check color contrast (simplified)
   */
  private checkColorContrast(container: HTMLElement, results: any) {
    const textElements = container.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6, a, button, label')
    
    textElements.forEach(element => {
      const style = window.getComputedStyle(element)
      const backgroundColor = style.backgroundColor
      const color = style.color
      
      // Simplified check - in real implementation would calculate actual contrast ratio
      if (backgroundColor === color || backgroundColor === 'transparent') {
        results.warnings.push('Potential color contrast issue detected')
      }
    })
  }

  /**
   * Check screen reader support
   */
  private checkScreenReaderSupport(container: HTMLElement, results: any) {
    // Check for screen reader only content
    const srOnlyElements = container.querySelectorAll('.sr-only, .visually-hidden')
    
    // Check for proper live regions
    const liveRegions = container.querySelectorAll('[aria-live]')
    const alerts = container.querySelectorAll('[role="alert"]')
    
    // Check for descriptive text
    const images = container.querySelectorAll('img')
    images.forEach(img => {
      if (!img.getAttribute('alt') && img.getAttribute('alt') !== '') {
        results.violations.push('Image missing alt attribute')
        results.passed = false
      }
    })

    // Check for form labels
    const inputs = container.querySelectorAll('input, select, textarea')
    inputs.forEach(input => {
      const hasLabel = input.id && container.querySelector(`label[for="${input.id}"]`) ||
                      input.getAttribute('aria-label') ||
                      input.getAttribute('aria-labelledby')
      
      if (!hasLabel) {
        results.violations.push('Form control missing accessible label')
        results.passed = false
      }
    })
  }

  /**
   * Check form accessibility
   */
  private checkFormAccessibility(container: HTMLElement, results: any) {
    const forms = container.querySelectorAll('form')
    
    forms.forEach(form => {
      // Check for fieldsets with legends
      const fieldsets = form.querySelectorAll('fieldset')
      fieldsets.forEach(fieldset => {
        const legend = fieldset.querySelector('legend')
        if (!legend) {
          results.warnings.push('Fieldset missing legend')
        }
      })

      // Check for required field indicators
      const requiredFields = form.querySelectorAll('[required]')
      requiredFields.forEach(field => {
        if (!field.getAttribute('aria-required')) {
          results.warnings.push('Required field should have aria-required="true"')
        }
      })

      // Check for error message associations
      const errorMessages = form.querySelectorAll('[role="alert"], .error-message')
      errorMessages.forEach(error => {
        const associatedField = form.querySelector(`[aria-describedby="${error.id}"]`)
        if (!associatedField && error.id) {
          results.warnings.push('Error message not associated with form field')
        }
      })
    })
  }

  /**
   * Check image accessibility
   */
  private checkImageAccessibility(container: HTMLElement, results: any) {
    const images = container.querySelectorAll('img')
    
    images.forEach(img => {
      const alt = img.getAttribute('alt')
      const src = img.getAttribute('src')
      
      // Check for missing alt attribute
      if (alt === null) {
        results.violations.push('Image missing alt attribute')
        results.passed = false
      }
      
      // Check for redundant alt text
      if (alt && (alt.toLowerCase().includes('image') || alt.toLowerCase().includes('picture'))) {
        results.warnings.push('Alt text should not include "image" or "picture"')
      }
      
      // Check for decorative images
      if (alt === '' && !img.getAttribute('role')) {
        // This is correct for decorative images
      }
    })

    // Check for complex images
    const complexImages = container.querySelectorAll('img[aria-describedby]')
    complexImages.forEach(img => {
      const describedBy = img.getAttribute('aria-describedby')
      const description = container.querySelector(`#${describedBy}`)
      if (!description) {
        results.violations.push('Complex image description element not found')
        results.passed = false
      }
    })
  }
}

/**
 * Keyboard navigation tester
 */
export class KeyboardNavigationTester {
  private user = userEvent.setup()

  /**
   * Test tab navigation through component
   */
  async testTabNavigation(container: HTMLElement) {
    const focusableElements = this.getFocusableElements(container)
    const results = {
      passed: true,
      focusOrder: [] as string[],
      issues: [] as string[],
    }

    // Test forward navigation
    for (let i = 0; i < focusableElements.length; i++) {
      await this.user.tab()
      const focused = document.activeElement
      
      if (focused !== focusableElements[i]) {
        results.issues.push(`Expected focus on element ${i}, but got different element`)
        results.passed = false
      }
      
      results.focusOrder.push(this.getElementDescription(focused as HTMLElement))
    }

    return results
  }

  /**
   * Test escape key handling
   */
  async testEscapeKey(container: HTMLElement, expectedBehavior: 'close' | 'cancel' | 'none' = 'none') {
    await this.user.keyboard('{Escape}')
    
    // Check expected behavior based on component type
    switch (expectedBehavior) {
      case 'close':
        // Modal or dialog should close
        expect(container).not.toBeInTheDocument()
        break
      case 'cancel':
        // Form should reset or cancel action
        const cancelButton = container.querySelector('[data-testid="cancel"]')
        expect(cancelButton).toHaveFocus()
        break
    }
  }

  /**
   * Test arrow key navigation for lists/menus
   */
  async testArrowKeyNavigation(container: HTMLElement, direction: 'vertical' | 'horizontal' = 'vertical') {
    const navigableItems = container.querySelectorAll('[role="menuitem"], [role="option"], li')
    
    if (navigableItems.length === 0) return

    // Focus first item
    (navigableItems[0] as HTMLElement).focus()

    const key = direction === 'vertical' ? '{ArrowDown}' : '{ArrowRight}'
    
    // Navigate through items
    for (let i = 1; i < navigableItems.length; i++) {
      await this.user.keyboard(key)
      expect(navigableItems[i]).toHaveFocus()
    }

    // Test wrapping (should go back to first item)
    await this.user.keyboard(key)
    expect(navigableItems[0]).toHaveFocus()
  }

  /**
   * Get focusable elements in tab order
   */
  private getFocusableElements(container: HTMLElement): HTMLElement[] {
    const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    const elements = Array.from(container.querySelectorAll(selector)) as HTMLElement[]
    
    // Sort by tabindex
    return elements.sort((a, b) => {
      const aIndex = parseInt(a.getAttribute('tabindex') || '0')
      const bIndex = parseInt(b.getAttribute('tabindex') || '0')
      return aIndex - bIndex
    })
  }

  /**
   * Get description of element for debugging
   */
  private getElementDescription(element: HTMLElement): string {
    const tag = element.tagName.toLowerCase()
    const id = element.id ? `#${element.id}` : ''
    const className = element.className ? `.${element.className.split(' ').join('.')}` : ''
    const text = element.textContent?.slice(0, 20) || ''
    
    return `${tag}${id}${className} "${text}"`
  }
}

/**
 * Screen reader testing utilities
 */
export class ScreenReaderTester {
  /**
   * Test live region announcements
   */
  testLiveRegionAnnouncements(container: HTMLElement) {
    const liveRegions = container.querySelectorAll('[aria-live]')
    const alerts = container.querySelectorAll('[role="alert"]')
    const status = container.querySelectorAll('[role="status"]')

    return {
      polite: Array.from(container.querySelectorAll('[aria-live="polite"]')),
      assertive: Array.from(container.querySelectorAll('[aria-live="assertive"]')),
      alerts: Array.from(alerts),
      status: Array.from(status),
    }
  }

  /**
   * Test accessible names and descriptions
   */
  testAccessibleNamesAndDescriptions(container: HTMLElement) {
    const results = {
      elementsWithoutNames: [] as HTMLElement[],
      elementsWithDescriptions: [] as HTMLElement[],
    }

    const interactiveElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [role="button"], [role="link"]'
    )

    interactiveElements.forEach(element => {
      const accessibleName = this.getAccessibleName(element as HTMLElement)
      if (!accessibleName) {
        results.elementsWithoutNames.push(element as HTMLElement)
      }

      const description = element.getAttribute('aria-describedby')
      if (description) {
        results.elementsWithDescriptions.push(element as HTMLElement)
      }
    })

    return results
  }

  /**
   * Get accessible name for element
   */
  private getAccessibleName(element: HTMLElement): string {
    // Check aria-label
    const ariaLabel = element.getAttribute('aria-label')
    if (ariaLabel) return ariaLabel

    // Check aria-labelledby
    const labelledBy = element.getAttribute('aria-labelledby')
    if (labelledBy) {
      const labelElement = document.getElementById(labelledBy)
      if (labelElement) return labelElement.textContent || ''
    }

    // Check associated label
    if (element.id) {
      const label = document.querySelector(`label[for="${element.id}"]`)
      if (label) return label.textContent || ''
    }

    // Check text content for buttons
    if (element.tagName === 'BUTTON' || element.getAttribute('role') === 'button') {
      return element.textContent || ''
    }

    return ''
  }
}

// Export main accessibility testing function
export async function testAccessibility(
  container: HTMLElement,
  options: AccessibilityTestOptions = {}
) {
  const checker = new WCAGComplianceChecker(options)
  const keyboardTester = new KeyboardNavigationTester()
  const screenReaderTester = new ScreenReaderTester()

  const results = {
    wcag: await checker.auditComponent(container),
    keyboard: await keyboardTester.testTabNavigation(container),
    screenReader: screenReaderTester.testAccessibleNamesAndDescriptions(container),
  }

  return results
}