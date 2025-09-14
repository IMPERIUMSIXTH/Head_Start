/**
 * Global Jest setup for enhanced testing capabilities
 */

module.exports = async () => {
  // Set up test environment variables
  process.env.NODE_ENV = 'test'
  process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
  process.env.NEXT_PUBLIC_APP_ENV = 'test'
  
  // Initialize test database or mock services if needed
  console.log('🧪 Setting up test environment...')
  
  // Set up global test utilities
  global.testStartTime = Date.now()
  
  // Configure test timeouts based on test type
  const testType = process.env.TEST_TYPE || 'unit'
  switch (testType) {
    case 'integration':
      jest.setTimeout(30000)
      break
    case 'e2e':
      jest.setTimeout(60000)
      break
    case 'performance':
      jest.setTimeout(120000)
      break
    default:
      jest.setTimeout(15000)
  }
  
  console.log(`✅ Test environment ready (${testType} tests)`)
}