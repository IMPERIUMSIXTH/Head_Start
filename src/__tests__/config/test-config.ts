/**
 * Comprehensive test configuration for enhanced React Testing Library setup
 */

export interface TestConfig {
  accessibility: AccessibilityConfig
  visual: VisualConfig
  performance: PerformanceConfig
  coverage: CoverageConfig
  reporting: ReportingConfig
}

export interface AccessibilityConfig {
  wcagLevel: 'A' | 'AA' | 'AAA'
  enableColorContrastCheck: boolean
  enableKeyboardNavigationCheck: boolean
  enableScreenReaderCheck: boolean
  customRules: Array<{
    id: string
    enabled: boolean
    options?: Record<string, any>
  }>
}

export interface VisualConfig {
  viewports: Array<{
    name: string
    width: number
    height: number
  }>
  themes: string[]
  delay: number
  enableAnimations: boolean
  chromatic: {
    projectToken?: string
    threshold: number
    diffThreshold: number
    ignoreSelectors: string[]
  }
}

export interface PerformanceConfig {
  renderTimeThreshold: number
  memoryUsageThreshold: number
  enableRenderProfiling: boolean
  enableMemoryProfiling: boolean
}

export interface CoverageConfig {
  thresholds: {
    global: {
      branches: number
      functions: number
      lines: number
      statements: number
    }
    components: {
      branches: number
      functions: number
      lines: number
      statements: number
    }
    pages: {
      branches: number
      functions: number
      lines: number
      statements: number
    }
  }
  collectFrom: string[]
  exclude: string[]
}

export interface ReportingConfig {
  formats: Array<'html' | 'json' | 'lcov' | 'text' | 'junit'>
  outputDirectory: string
  includeTimestamps: boolean
  includeEnvironmentInfo: boolean
}

/**
 * Default test configuration
 */
export const defaultTestConfig: TestConfig = {
  accessibility: {
    wcagLevel: 'AA',
    enableColorContrastCheck: true,
    enableKeyboardNavigationCheck: true,
    enableScreenReaderCheck: true,
    customRules: [
      { id: 'color-contrast', enabled: true },
      { id: 'keyboard-navigation', enabled: true },
      { id: 'focus-order-semantics', enabled: true },
      { id: 'button-name', enabled: true },
      { id: 'link-name', enabled: true },
      { id: 'image-alt', enabled: true },
      { id: 'form-field-multiple-labels', enabled: true },
      { id: 'aria-valid-attr', enabled: true },
      { id: 'aria-required-attr', enabled: true },
    ],
  },
  visual: {
    viewports: [
      { name: 'mobile', width: 375, height: 667 },
      { name: 'tablet', width: 768, height: 1024 },
      { name: 'desktop', width: 1200, height: 800 },
      { name: 'large-desktop', width: 1920, height: 1080 },
    ],
    themes: ['light', 'dark', 'high-contrast'],
    delay: 300,
    enableAnimations: false,
    chromatic: {
      threshold: 0.2,
      diffThreshold: 0.063,
      ignoreSelectors: [
        '[data-chromatic="ignore"]',
        '.timestamp',
        '.random-id',
        '[data-testid="dynamic-content"]',
        '.loading-spinner',
        '.animated-element',
      ],
    },
  },
  performance: {
    renderTimeThreshold: 100, // milliseconds
    memoryUsageThreshold: 50, // MB
    enableRenderProfiling: true,
    enableMemoryProfiling: false, // Disabled by default as it can be resource intensive
  },
  coverage: {
    thresholds: {
      global: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80,
      },
      components: {
        branches: 85,
        functions: 85,
        lines: 85,
        statements: 85,
      },
      pages: {
        branches: 75,
        functions: 75,
        lines: 75,
        statements: 75,
      },
    },
    collectFrom: [
      'components/**/*.{js,jsx,ts,tsx}',
      'pages/**/*.{js,jsx,ts,tsx}',
      'hooks/**/*.{js,jsx,ts,tsx}',
      'utils/**/*.{js,jsx,ts,tsx}',
    ],
    exclude: [
      '**/*.d.ts',
      '**/*.stories.{js,jsx,ts,tsx}',
      '**/*.test.{js,jsx,ts,tsx}',
      '**/*.spec.{js,jsx,ts,tsx}',
      '**/node_modules/**',
      '**/.next/**',
      '**/coverage/**',
      '**/storybook-static/**',
    ],
  },
  reporting: {
    formats: ['html', 'json', 'lcov', 'junit'],
    outputDirectory: 'coverage',
    includeTimestamps: true,
    includeEnvironmentInfo: true,
  },
}

/**
 * Environment-specific configurations
 */
export const testConfigs = {
  development: {
    ...defaultTestConfig,
    performance: {
      ...defaultTestConfig.performance,
      enableRenderProfiling: true,
      enableMemoryProfiling: true,
    },
    reporting: {
      ...defaultTestConfig.reporting,
      formats: ['html', 'json'],
    },
  },
  ci: {
    ...defaultTestConfig,
    visual: {
      ...defaultTestConfig.visual,
      delay: 500, // Longer delay for CI environment
    },
    performance: {
      ...defaultTestConfig.performance,
      renderTimeThreshold: 200, // More lenient in CI
      enableMemoryProfiling: false,
    },
    reporting: {
      ...defaultTestConfig.reporting,
      formats: ['json', 'junit', 'lcov'],
    },
  },
  production: {
    ...defaultTestConfig,
    accessibility: {
      ...defaultTestConfig.accessibility,
      wcagLevel: 'AAA' as const,
    },
    coverage: {
      ...defaultTestConfig.coverage,
      thresholds: {
        global: {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90,
        },
        components: {
          branches: 95,
          functions: 95,
          lines: 95,
          statements: 95,
        },
        pages: {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85,
        },
      },
    },
  },
}

/**
 * Get configuration based on environment
 */
export function getTestConfig(environment: keyof typeof testConfigs = 'development'): TestConfig {
  return testConfigs[environment] || defaultTestConfig
}

/**
 * Test categories and their configurations
 */
export const testCategories = {
  unit: {
    testMatch: ['**/__tests__/**/*.(test|spec).{js,jsx,ts,tsx}'],
    testPathIgnorePatterns: ['/integration/', '/e2e/', '/visual/', '/accessibility/'],
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
    testTimeout: 5000,
  },
  integration: {
    testMatch: ['**/__tests__/integration/**/*.(test|spec).{js,jsx,ts,tsx}'],
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js', '<rootDir>/jest.integration-setup.js'],
    testTimeout: 15000,
  },
  accessibility: {
    testMatch: ['**/__tests__/accessibility/**/*.(test|spec).{js,jsx,ts,tsx}'],
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js', '<rootDir>/jest.accessibility-setup.js'],
    testTimeout: 10000,
  },
  visual: {
    testMatch: ['**/__tests__/visual/**/*.(test|spec).{js,jsx,ts,tsx}'],
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js', '<rootDir>/jest.visual-setup.js'],
    testTimeout: 30000,
  },
  performance: {
    testMatch: ['**/__tests__/performance/**/*.(test|spec).{js,jsx,ts,tsx}'],
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js', '<rootDir>/jest.performance-setup.js'],
    testTimeout: 60000,
  },
}

/**
 * Quality gate thresholds
 */
export const qualityGates = {
  accessibility: {
    maxViolations: {
      critical: 0,
      serious: 0,
      moderate: 5,
      minor: 10,
    },
    wcagCompliance: 'AA',
  },
  performance: {
    maxRenderTime: 100, // milliseconds
    maxMemoryUsage: 50, // MB
    maxBundleSize: 500, // KB
  },
  coverage: {
    minimum: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  visual: {
    maxPixelDifference: 0.2, // 20% pixel difference threshold
    maxLayoutShift: 0.1, // Cumulative Layout Shift threshold
  },
}

/**
 * Test utilities configuration
 */
export const testUtilsConfig = {
  mockApi: {
    baseUrl: 'http://localhost:8000',
    timeout: 5000,
    retries: 3,
  },
  mockData: {
    generateRealistic: true,
    seedValue: 12345, // For consistent test data
    locale: 'en-US',
  },
  cleanup: {
    clearMocksAfterEach: true,
    restoreConsoleAfterEach: true,
    clearTimersAfterEach: true,
  },
}

/**
 * Export configuration based on NODE_ENV
 */
const environment = process.env.NODE_ENV as keyof typeof testConfigs
export const currentTestConfig = getTestConfig(environment)

export default currentTestConfig