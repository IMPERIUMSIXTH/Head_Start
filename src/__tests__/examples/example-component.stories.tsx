import type { Meta, StoryObj } from '@storybook/react'
import { within, userEvent, expect } from '@storybook/test'
import { ChromaticStoryUtils } from '../utils/visual-testing'

// Example component for demonstration
const ExampleButton = ({ 
  variant = 'primary', 
  size = 'medium', 
  disabled = false, 
  loading = false,
  children,
  onClick,
  ...props 
}: any) => {
  const baseClasses = 'px-4 py-2 rounded font-medium transition-colors'
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  }
  const sizeClasses = {
    small: 'px-2 py-1 text-sm',
    medium: 'px-4 py-2',
    large: 'px-6 py-3 text-lg',
  }

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      }`}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </button>
  )
}

const meta: Meta<typeof ExampleButton> = {
  title: 'Example/Button',
  component: ExampleButton,
  parameters: {
    layout: 'centered',
    // Chromatic configuration for visual testing
    chromatic: {
      viewports: [375, 768, 1200],
      delay: 300,
    },
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'danger'],
    },
    size: {
      control: { type: 'select' },
      options: ['small', 'medium', 'large'],
    },
    disabled: {
      control: 'boolean',
    },
    loading: {
      control: 'boolean',
    },
  },
}

export default meta
type Story = StoryObj<typeof meta>

// Basic stories
export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary Button',
  },
}

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary Button',
  },
}

export const Danger: Story = {
  args: {
    variant: 'danger',
    children: 'Danger Button',
  },
}

// Size variations
export const Small: Story = {
  args: {
    size: 'small',
    children: 'Small Button',
  },
}

export const Large: Story = {
  args: {
    size: 'large',
    children: 'Large Button',
  },
}

// State variations
export const Disabled: Story = {
  args: {
    disabled: true,
    children: 'Disabled Button',
  },
}

export const Loading: Story = {
  args: {
    loading: true,
    children: 'Loading Button',
  },
}

// Visual regression testing - all variants
export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
      <ExampleButton variant="primary">Primary</ExampleButton>
      <ExampleButton variant="secondary">Secondary</ExampleButton>
      <ExampleButton variant="danger">Danger</ExampleButton>
      <ExampleButton disabled>Disabled</ExampleButton>
      <ExampleButton loading>Loading</ExampleButton>
    </div>
  ),
  parameters: {
    chromatic: {
      viewports: [375, 768, 1200, 1920],
    },
  },
}

// Size comparison
export const SizeComparison: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
      <ExampleButton size="small">Small</ExampleButton>
      <ExampleButton size="medium">Medium</ExampleButton>
      <ExampleButton size="large">Large</ExampleButton>
    </div>
  ),
}

// Interaction testing
export const WithInteraction: Story = {
  args: {
    children: 'Click me',
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const button = canvas.getByRole('button')
    
    // Test hover state
    await userEvent.hover(button)
    await expect(button).toBeInTheDocument()
    
    // Test click
    await userEvent.click(button)
  },
}

// Accessibility testing story
export const AccessibilityTest: Story = {
  args: {
    children: 'Accessible Button',
    'aria-label': 'Perform action',
    'aria-describedby': 'button-help',
  },
  render: (args) => (
    <div>
      <ExampleButton {...args} />
      <div id="button-help" style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
        This button performs an important action
      </div>
    </div>
  ),
  parameters: {
    a11y: {
      config: {
        rules: [
          {
            id: 'color-contrast',
            enabled: true,
          },
          {
            id: 'button-name',
            enabled: true,
          },
        ],
      },
    },
  },
}

// Responsive testing
export const ResponsiveTest: Story = {
  render: () => (
    <div style={{ width: '100%', padding: '1rem' }}>
      <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <ExampleButton variant="primary">Responsive Button 1</ExampleButton>
        <ExampleButton variant="secondary">Responsive Button 2</ExampleButton>
        <ExampleButton variant="danger">Responsive Button 3</ExampleButton>
      </div>
    </div>
  ),
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

// Dark mode testing
export const DarkModeTest: Story = {
  args: {
    children: 'Dark Mode Button',
  },
  parameters: {
    backgrounds: {
      default: 'dark',
      values: [
        { name: 'light', value: '#ffffff' },
        { name: 'dark', value: '#1a1a1a' },
      ],
    },
    chromatic: {
      modes: {
        light: { backgrounds: { default: 'light' } },
        dark: { backgrounds: { default: 'dark' } },
      },
    },
  },
}

// Focus testing
export const FocusTest: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '1rem' }}>
      <ExampleButton>First Button</ExampleButton>
      <ExampleButton>Second Button</ExampleButton>
      <ExampleButton>Third Button</ExampleButton>
    </div>
  ),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const buttons = canvas.getAllByRole('button')
    
    // Test keyboard navigation
    buttons[0].focus()
    await expect(buttons[0]).toHaveFocus()
    
    // Simulate tab navigation
    await userEvent.tab()
    await expect(buttons[1]).toHaveFocus()
    
    await userEvent.tab()
    await expect(buttons[2]).toHaveFocus()
  },
  parameters: {
    chromatic: {
      delay: 500, // Extra delay for focus states
    },
  },
}

// Error state testing
export const ErrorState: Story = {
  render: () => (
    <div>
      <ExampleButton variant="danger" aria-describedby="error-message">
        Error Action
      </ExampleButton>
      <div id="error-message" role="alert" style={{ color: 'red', marginTop: '0.5rem' }}>
        This action will cause an error
      </div>
    </div>
  ),
}

// Loading state with animation
export const LoadingWithAnimation: Story = {
  render: () => {
    const [loading, setLoading] = React.useState(false)
    
    return (
      <div>
        <ExampleButton 
          loading={loading}
          onClick={() => {
            setLoading(true)
            setTimeout(() => setLoading(false), 2000)
          }}
        >
          {loading ? 'Processing...' : 'Start Process'}
        </ExampleButton>
      </div>
    )
  },
  parameters: {
    chromatic: {
      delay: 1000, // Wait for potential animations
      pauseAnimationAtEnd: true,
    },
  },
}

// Performance testing story
export const PerformanceTest: Story = {
  render: () => (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: '0.5rem' }}>
      {Array.from({ length: 100 }, (_, i) => (
        <ExampleButton key={i} size="small">
          {i + 1}
        </ExampleButton>
      ))}
    </div>
  ),
  parameters: {
    chromatic: {
      delay: 1000, // Extra time for rendering many components
    },
  },
}