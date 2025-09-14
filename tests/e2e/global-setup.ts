import { chromium, FullConfig } from '@playwright/test';
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

/**
 * Global setup for Playwright E2E tests
 * Handles database setup, test data creation, and environment preparation
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E test environment setup...');
  
  try {
    // Ensure test results directory exists
    const testResultsDir = path.join(__dirname, 'test-results');
    if (!fs.existsSync(testResultsDir)) {
      fs.mkdirSync(testResultsDir, { recursive: true });
    }

    // Wait for backend to be ready
    console.log('⏳ Waiting for backend service...');
    await waitForService('http://localhost:8000/health', 60000);
    
    // Wait for frontend to be ready
    console.log('⏳ Waiting for frontend service...');
    await waitForService('http://localhost:3000', 60000);
    
    console.log('✅ E2E test environment setup complete!');
    
  } catch (error) {
    console.error('❌ E2E test environment setup failed:', error);
    throw error;
  }
}

/**
 * Wait for a service to be available
 */
async function waitForService(url: string, timeout: number): Promise<void> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
    } catch (error) {
      // Service not ready yet
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  throw new Error(`Service at ${url} not available after ${timeout}ms`);
}

export default globalSetup;