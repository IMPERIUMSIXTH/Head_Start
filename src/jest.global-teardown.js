/**
 * Global Jest teardown for cleanup
 */

module.exports = async () => {
  // Clean up test environment
  console.log('🧹 Cleaning up test environment...')
  
  // Calculate test execution time
  if (global.testStartTime) {
    const executionTime = Date.now() - global.testStartTime
    console.log(`⏱️  Total test execution time: ${executionTime}ms`)
  }
  
  // Clean up any global mocks or test data
  if (global.fetch && typeof global.fetch.mockRestore === 'function') {
    global.fetch.mockRestore()
  }
  
  // Clear any timers
  if (global.clearAllTimers) {
    global.clearAllTimers()
  }
  
  console.log('✅ Test cleanup complete')
}