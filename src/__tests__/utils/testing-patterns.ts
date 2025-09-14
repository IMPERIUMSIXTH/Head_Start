import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReactElement } from 'react'

/**
 * Enhanced testing patterns for React components
 */

export interface InteractionTestOptions {
  timeout?: number
  skipA11yCheck?: boolean
  mockTimers?: boolean
}

/**
 * Test component interaction patterns
 */
export class ComponentInteractionTester {
  private user = userEvent.setup()

  /**
   * Test form submission with validation
   */
  async testFormSubmission(
    component: ReactElement,
    formData: Record<string, string>,
    options: InteractionTestOptions = {}
  ) {
    const { timeout = 5000 } = options
    
    render(component)
    
    // Fill form fields
    for (const [fieldName, value] of Object.entries(formData)) {
      const field = screen.getByLabelText(new RegExp(fieldName, 'i'))
      await this.user.clear(field)
      await this.user.type(field, value)
    }
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: /submit|save|create/i })
    await this.user.click(submitButton)
    
    // Wait for submission to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading|submitting/i)).not.toBeInTheDocument()
    }, { timeout })
    
    return screen
  }

  /**
   * Test dropdown/select interactions
   */
  async testDropdownSelection(
    component: ReactElement,
    dropdownLabel: string,
    optionText: string
  ) {
    render(component)
    
    // Open dropdown
    const dropdown = screen.getByLabelText(new RegExp(dropdownLabel, 'i'))
    await this.user.click(dropdown)
    
    // Wait for options to appear
    await waitFor(() => {
      expect(screen.getByRole('listbox')).toBeInTheDocument()
    })
    
    // Select option
    const option = screen.getByRole('option', { name: new RegExp(optionText, 'i') })
    await this.user.click(option)
    
    // Verify selection
    expect(dropdown).toHaveValue(optionText)
    
    return screen
  }

  /**
   * Test modal/dialog interactions
   */
  async testModalInteraction(
    component: ReactElement,
    triggerText: string,
    modalTestId?: string
  ) {
    render(component)
    
    // Open modal
    const trigger = screen.getByRole('button', { name: new RegExp(triggerText, 'i') })
    await this.user.click(trigger)
    
    // Wait for modal to appear
    const modal = modalTestId 
      ? await screen.findByTestId(modalTestId)
      : await screen.findByRole('dialog')
    
    expect(modal).toBeInTheDocument()
    
    // Test focus management
    expect(modal).toHaveFocus()
    
    return { modal, screen }
  }

  /**
   * Test keyboard navigation
   */
  async testKeyboardNavigation(
    component: ReactElement,
    navigableElements: string[]
  ) {
    render(component)
    
    // Test Tab navigation
    for (const elementText of navigableElements) {
      await this.user.tab()
      const focusedElement = screen.getByText(new RegExp(elementText, 'i'))
      expect(focusedElement).toHaveFocus()
    }
    
    // Test Shift+Tab navigation
    for (let i = navigableElements.length - 1; i >= 0; i--) {
      await this.user.tab({ shift: true })
      const focusedElement = screen.getByText(new RegExp(navigableElements[i], 'i'))
      expect(focusedElement).toHaveFocus()
    }
    
    return screen
  }

  /**
   * Test drag and drop interactions
   */
  async testDragAndDrop(
    component: ReactElement,
    sourceTestId: string,
    targetTestId: string
  ) {
    render(component)
    
    const source = screen.getByTestId(sourceTestId)
    const target = screen.getByTestId(targetTestId)
    
    // Simulate drag and drop
    fireEvent.dragStart(source)
    fireEvent.dragEnter(target)
    fireEvent.dragOver(target)
    fireEvent.drop(target)
    fireEvent.dragEnd(source)
    
    return { source, target, screen }
  }

  /**
   * Test infinite scroll or pagination
   */
  async testInfiniteScroll(
    component: ReactElement,
    scrollContainerTestId: string,
    expectedNewItems: number
  ) {
    render(component)
    
    const scrollContainer = screen.getByTestId(scrollContainerTestId)
    const initialItems = within(scrollContainer).getAllByRole('listitem').length
    
    // Simulate scroll to bottom
    fireEvent.scroll(scrollContainer, { target: { scrollTop: scrollContainer.scrollHeight } })
    
    // Wait for new items to load
    await waitFor(() => {
      const currentItems = within(scrollContainer).getAllByRole('listitem').length
      expect(currentItems).toBe(initialItems + expectedNewItems)
    })
    
    return screen
  }

  /**
   * Test search/filter functionality
   */
  async testSearchFilter(
    component: ReactElement,
    searchTerm: string,
    expectedResultCount: number
  ) {
    render(component)
    
    const searchInput = screen.getByRole('searchbox') || screen.getByLabelText(/search/i)
    
    // Enter search term
    await this.user.type(searchInput, searchTerm)
    
    // Wait for results to update
    await waitFor(() => {
      const results = screen.getAllByRole('listitem')
      expect(results).toHaveLength(expectedResultCount)
    })
    
    return screen
  }

  /**
   * Test component state changes
   */
  async testStateChange(
    component: ReactElement,
    triggerAction: () => Promise<void>,
    expectedStateSelector: string,
    expectedState: string
  ) {
    render(component)
    
    // Perform action that should change state
    await triggerAction()
    
    // Verify state change
    await waitFor(() => {
      const stateElement = screen.getByTestId(expectedStateSelector)
      expect(stateElement).toHaveTextContent(expectedState)
    })
    
    return screen
  }
}

/**
 * Utility functions for common testing scenarios
 */
export const testingUtils = {
  /**
   * Wait for element to appear and be stable
   */
  async waitForStableElement(selector: string, timeout = 3000) {
    const element = await screen.findByTestId(selector, {}, { timeout })
    
    // Wait for element to be stable (no more changes)
    await waitFor(() => {
      expect(element).toBeInTheDocument()
    }, { timeout: 1000 })
    
    return element
  },

  /**
   * Simulate network delay
   */
  async simulateNetworkDelay(ms = 1000) {
    await new Promise(resolve => setTimeout(resolve, ms))
  },

  /**
   * Mock API responses for testing
   */
  mockApiResponse(url: string, response: any, status = 200) {
    global.fetch = jest.fn().mockImplementation((requestUrl) => {
      if (requestUrl.includes(url)) {
        return Promise.resolve({
          ok: status >= 200 && status < 300,
          status,
          json: () => Promise.resolve(response),
        })
      }
      return Promise.reject(new Error('Unhandled request'))
    })
  },

  /**
   * Clean up mocks after tests
   */
  cleanupMocks() {
    jest.restoreAllMocks()
    if (global.fetch && typeof global.fetch.mockRestore === 'function') {
      global.fetch.mockRestore()
    }
  }
}

export default ComponentInteractionTester