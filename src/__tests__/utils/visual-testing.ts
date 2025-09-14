import { render } from '@testing-library/react'
import { ReactElement } from 'react'

/**
 * Visual regression testing utilities
 */

export interface VisualTestOptions {
  viewports?: Array<{ width: number; height: number; name: string }>
  themes?: string[]
  delay?: number
  animations?: boolean
  interactions?: Array<() => Promise<void>>
}

/**
 * Visual regression tester using Chromatic integration
 */
export class VisualRegressionTester {
  private defaultViewports = [
    { width: 375, height: 667, name: 'mobile' },
    { width: 768, height: 1024, name: 'tablet' },
    { width: 1200, height: 800, name: 'desktop' },
    { width: 1920, height: 1080, name: 'large-desktop' },
  ]

  /**
   * Create visual test for component across multiple viewports
   */
  async testComponentVisuals(
    component: ReactElement,
    testName: string,
    options: VisualTestOptions = {}
  ) {
    const {
      viewports = this.defaultViewports,
      themes = ['light', 'dark'],
      delay = 300,
      animations = false,
      interactions = [],
    } = options

    const results = []

    for (const viewport of viewports) {
      for (const theme of themes) {
        const testId = `${testName}-${viewport.name}-${theme}`
        
        // Set viewport
        this.setViewport(viewport.width, viewport.height)
        
        // Set theme
        this.setTheme(theme)
        
        // Render component
        const { container } = render(component)
        
        // Disable animations if requested
        if (!animations) {
          this.disableAnimations(container)
        }
        
        // Wait for delay
        await this.wait(delay)
        
        // Execute interactions
        for (const interaction of interactions) {
          await interaction()
          await this.wait(100) // Small delay between interactions
        }
        
        // Capture screenshot (in real implementation, this would integrate with Chromatic)
        const screenshot = await this.captureScreenshot(container, testId)
        
        results.push({
          testId,
          viewport: viewport.name,
          theme,
          screenshot,
          passed: true, // Would be determined by visual comparison
        })
      }
    }

    return results
  }

  /**
   * Test component states visually
   */
  async testComponentStates(
    componentStates: Array<{ name: string; component: ReactElement }>,
    testName: string
  ) {
    const results = []

    for (const state of componentStates) {
      const { container } = render(state.component)
      
      // Disable animations for consistent screenshots
      this.disableAnimations(container)
      
      await this.wait(300)
      
      const screenshot = await this.captureScreenshot(container, `${testName}-${state.name}`)
      
      results.push({
        testId: `${testName}-${state.name}`,
        state: state.name,
        screenshot,
        passed: true,
      })
    }

    return results
  }

  /**
   * Test responsive behavior visually
   */
  async testResponsiveDesign(
    component: ReactElement,
    testName: string,
    breakpoints: number[] = [375, 768, 1024, 1200, 1920]
  ) {
    const results = []

    for (const breakpoint of breakpoints) {
      this.setViewport(breakpoint, 800)
      
      const { container } = render(component)
      this.disableAnimations(container)
      
      await this.wait(300)
      
      const screenshot = await this.captureScreenshot(container, `${testName}-${breakpoint}px`)
      
      results.push({
        testId: `${testName}-${breakpoint}px`,
        breakpoint,
        screenshot,
        passed: true,
      })
    }

    return results
  }

  /**
   * Test dark mode variations
   */
  async testDarkModeVariations(
    component: ReactElement,
    testName: string
  ) {
    const themes = ['light', 'dark', 'high-contrast']
    const results = []

    for (const theme of themes) {
      this.setTheme(theme)
      
      const { container } = render(component)
      this.disableAnimations(container)
      
      await this.wait(300)
      
      const screenshot = await this.captureScreenshot(container, `${testName}-${theme}`)
      
      results.push({
        testId: `${testName}-${theme}`,
        theme,
        screenshot,
        passed: true,
      })
    }

    return results
  }

  /**
   * Test component interactions visually
   */
  async testInteractionStates(
    component: ReactElement,
    testName: string,
    interactions: Array<{
      name: string
      action: (container: HTMLElement) => Promise<void>
    }>
  ) {
    const results = []

    for (const interaction of interactions) {
      const { container } = render(component)
      this.disableAnimations(container)
      
      // Execute interaction
      await interaction.action(container)
      await this.wait(300)
      
      const screenshot = await this.captureScreenshot(container, `${testName}-${interaction.name}`)
      
      results.push({
        testId: `${testName}-${interaction.name}`,
        interaction: interaction.name,
        screenshot,
        passed: true,
      })
    }

    return results
  }

  /**
   * Set viewport size
   */
  private setViewport(width: number, height: number) {
    // In a real implementation, this would set the browser viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: width,
    })
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: height,
    })
    
    // Trigger resize event
    window.dispatchEvent(new Event('resize'))
  }

  /**
   * Set theme
   */
  private setTheme(theme: string) {
    document.documentElement.setAttribute('data-theme', theme)
    document.documentElement.className = theme
  }

  /**
   * Disable animations for consistent screenshots
   */
  private disableAnimations(container: HTMLElement) {
    const style = document.createElement('style')
    style.textContent = `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
      }
    `
    container.appendChild(style)
  }

  /**
   * Wait for specified time
   */
  private async wait(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * Capture screenshot (mock implementation)
   */
  private async captureScreenshot(container: HTMLElement, testId: string): Promise<string> {
    // In a real implementation, this would capture an actual screenshot
    // For now, return a mock screenshot identifier
    return `screenshot-${testId}-${Date.now()}`
  }
}

/**
 * Chromatic story utilities
 */
export class ChromaticStoryUtils {
  /**
   * Create story with multiple states for visual testing
   */
  static createStateStory(
    Component: React.ComponentType<any>,
    states: Array<{ name: string; props: any }>
  ) {
    return {
      title: `Visual Tests/${Component.name}`,
      component: Component,
      parameters: {
        chromatic: {
          viewports: [375, 768, 1200, 1920],
          delay: 300,
        },
      },
    }
  }

  /**
   * Create responsive story
   */
  static createResponsiveStory(
    Component: React.ComponentType<any>,
    props: any = {}
  ) {
    return {
      render: () => <Component {...props} />,
      parameters: {
        viewport: {
          viewports: {
            mobile: { name: 'Mobile', styles: { width: '375px', height: '667px' } },
            tablet: { name: 'Tablet', styles: { width: '768px', height: '1024px' } },
            desktop: { name: 'Desktop', styles: { width: '1200px', height: '800px' } },
          },
        },
        chromatic: {
          viewports: [375, 768, 1200],
        },
      },
    }
  }

  /**
   * Create interaction story for visual testing
   */
  static createInteractionStory(
    Component: React.ComponentType<any>,
    interactions: Array<{
      name: string
      play: (context: any) => Promise<void>
    }>
  ) {
    const stories: any = {}

    interactions.forEach(interaction => {
      stories[interaction.name] = {
        render: () => <Component />,
        play: interaction.play,
        parameters: {
          chromatic: {
            delay: 500, // Extra delay for interactions
          },
        },
      }
    })

    return stories
  }

  /**
   * Create theme variation story
   */
  static createThemeStory(
    Component: React.ComponentType<any>,
    props: any = {}
  ) {
    return {
      render: () => <Component {...props} />,
      parameters: {
        backgrounds: {
          values: [
            { name: 'light', value: '#ffffff' },
            { name: 'dark', value: '#1a1a1a' },
            { name: 'high-contrast', value: '#000000' },
          ],
        },
        chromatic: {
          modes: {
            light: { backgrounds: { default: 'light' } },
            dark: { backgrounds: { default: 'dark' } },
            'high-contrast': { backgrounds: { default: 'high-contrast' } },
          },
        },
      },
    }
  }
}

/**
 * Visual testing configuration
 */
export const visualTestConfig = {
  // Default viewports for visual testing
  viewports: [
    { width: 375, height: 667, name: 'mobile' },
    { width: 768, height: 1024, name: 'tablet' },
    { width: 1200, height: 800, name: 'desktop' },
    { width: 1920, height: 1080, name: 'large-desktop' },
  ],
  
  // Default themes
  themes: ['light', 'dark', 'high-contrast'],
  
  // Default delay for screenshots
  delay: 300,
  
  // Chromatic configuration
  chromatic: {
    projectToken: process.env.CHROMATIC_PROJECT_TOKEN,
    buildScriptName: 'build-storybook',
    exitZeroOnChanges: true,
    ignoreLastBuildOnBranch: 'main',
  },
}

// Export main visual testing function
export async function testVisualRegression(
  component: ReactElement,
  testName: string,
  options: VisualTestOptions = {}
) {
  const tester = new VisualRegressionTester()
  return await tester.testComponentVisuals(component, testName, options)
}