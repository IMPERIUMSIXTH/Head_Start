import type { Preview } from '@storybook/react'
import '../styles/globals.css' // Assuming global styles exist

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    // Accessibility addon configuration
    a11y: {
      element: '#storybook-root',
      config: {
        rules: [
          {
            id: 'color-contrast',
            enabled: true,
          },
          {
            id: 'focus-order-semantics',
            enabled: true,
          },
          {
            id: 'keyboard-navigation',
            enabled: true,
          },
        ],
      },
      options: {
        checks: { 'color-contrast': { options: { noScroll: true } } },
        restoreScroll: true,
      },
    },
    // Viewport addon configuration for responsive testing
    viewport: {
      viewports: {
        mobile: {
          name: 'Mobile',
          styles: {
            width: '375px',
            height: '667px',
          },
        },
        tablet: {
          name: 'Tablet',
          styles: {
            width: '768px',
            height: '1024px',
          },
        },
        desktop: {
          name: 'Desktop',
          styles: {
            width: '1200px',
            height: '800px',
          },
        },
        largeDesktop: {
          name: 'Large Desktop',
          styles: {
            width: '1920px',
            height: '1080px',
          },
        },
      },
    },
    // Chromatic configuration for visual regression testing
    chromatic: {
      // Delay capture to ensure animations complete
      delay: 300,
      // Disable animations for consistent screenshots
      pauseAnimationAtEnd: true,
      // Configure viewports for visual testing
      viewports: [375, 768, 1200, 1920],
      // Ignore certain elements that change frequently
      ignoreSelectors: [
        '[data-chromatic="ignore"]',
        '.timestamp',
        '.random-id',
      ],
    },
    // Layout configuration
    layout: 'centered',
    // Background configuration for testing different themes
    backgrounds: {
      default: 'light',
      values: [
        {
          name: 'light',
          value: '#ffffff',
        },
        {
          name: 'dark',
          value: '#1a1a1a',
        },
        {
          name: 'gray',
          value: '#f5f5f5',
        },
      ],
    },
  },
  // Global decorators
  decorators: [
    (Story) => (
      <div style={{ padding: '1rem' }}>
        <Story />
      </div>
    ),
  ],
  // Global args
  args: {
    // Default props for all stories
  },
  // Global arg types
  argTypes: {
    // Common prop types
    className: {
      control: 'text',
      description: 'Additional CSS classes',
    },
    children: {
      control: 'text',
      description: 'Child content',
    },
  },
  // Tags for story organization
  tags: ['autodocs'],
}

export default preview