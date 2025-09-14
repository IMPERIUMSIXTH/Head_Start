import { FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';

/**
 * Global teardown for Playwright E2E tests
 * Cleanup test data and environment
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting E2E test environment cleanup...');
  
  try {
    // Clean up auth state files
    const authStatePath = path.join(__dirname, 'auth-state.json');
    const adminAuthStatePath = path.join(__dirname, 'admin-auth-state.json');
    
    if (fs.existsSync(authStatePath)) {
      fs.unlinkSync(authStatePath);
    }
    
    if (fs.existsSync(adminAuthStatePath)) {
      fs.unlinkSync(adminAuthStatePath);
    }
    
    console.log('✅ E2E test environment cleanup complete!');
    
  } catch (error) {
    console.error('❌ E2E test environment cleanup failed:', error);
    // Don't throw error in teardown to avoid masking test failures
  }
}

export default globalTeardown;