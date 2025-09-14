import { Page, Locator, expect } from '@playwright/test';

/**
 * Base Page Object Model
 * Common functionality and patterns for all page objects
 */
export abstract class BasePage {
  protected page: Page;
  protected baseUrl: string;

  constructor(page: Page) {
    this.page = page;
    this.baseUrl = process.env.E2E_BASE_URL || 'http://localhost:3000';
  }

  // Common locators
  get loadingSpinner(): Locator {
    return this.page.locator('[data-testid="loading-spinner"]');
  }

  get errorMessage(): Locator {
    return this.page.locator('[data-testid="error-message"]');
  }

  get successMessage(): Locator {
    return this.page.locator('[data-testid="success-message"]');
  }

  get navigationMenu(): Locator {
    return this.page.locator('[data-testid="navigation-menu"]');
  }

  get userMenu(): Locator {
    return this.page.locator('[data-testid="user-menu"]');
  }

  get logoutButton(): Locator {
    return this.page.locator('[data-testid="logout-button"]');
  }

  // Common actions
  async navigateTo(path: string): Promise<void> {
    await this.page.goto(`${this.baseUrl}${path}`);
    await this.waitForPageLoad();
  }

  async waitForPageLoad(): Promise<void> {
    // Wait for network to be idle
    await this.page.waitForLoadState('networkidle');
    
    // Wait for loading spinner to disappear if present
    try {
      await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 5000 });
    } catch {
      // Loading spinner might not be present, continue
    }
  }

  async waitForApiResponse(urlPattern: string | RegExp): Promise<void> {
    await this.page.waitForResponse(urlPattern);
  }

  async clickAndWaitForNavigation(locator: Locator, expectedUrl?: string): Promise<void> {
    await Promise.all([
      this.page.waitForURL(expectedUrl || '**/*'),
      locator.click()
    ]);
    await this.waitForPageLoad();
  }

  async fillFormField(locator: Locator, value: string): Promise<void> {
    await locator.clear();
    await locator.fill(value);
    await locator.blur(); // Trigger validation
  }

  async selectDropdownOption(dropdownLocator: Locator, optionText: string): Promise<void> {
    await dropdownLocator.click();
    await this.page.locator(`text=${optionText}`).click();
  }

  async uploadFile(fileInputLocator: Locator, filePath: string): Promise<void> {
    await fileInputLocator.setInputFiles(filePath);
  }

  async scrollToElement(locator: Locator): Promise<void> {
    await locator.scrollIntoViewIfNeeded();
  }

  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}-${Date.now()}.png`,
      fullPage: true 
    });
  }

  async checkAccessibility(): Promise<void> {
    // This would integrate with @axe-core/playwright
    // await injectAxe(this.page);
    // const results = await checkA11y(this.page);
    // expect(results.violations).toHaveLength(0);
  }

  async verifyPageTitle(expectedTitle: string): Promise<void> {
    await expect(this.page).toHaveTitle(expectedTitle);
  }

  async verifyUrl(expectedUrl: string | RegExp): Promise<void> {
    await expect(this.page).toHaveURL(expectedUrl);
  }

  async verifyElementVisible(locator: Locator): Promise<void> {
    await expect(locator).toBeVisible();
  }

  async verifyElementHidden(locator: Locator): Promise<void> {
    await expect(locator).toBeHidden();
  }

  async verifyElementText(locator: Locator, expectedText: string): Promise<void> {
    await expect(locator).toHaveText(expectedText);
  }

  async verifyElementContainsText(locator: Locator, expectedText: string): Promise<void> {
    await expect(locator).toContainText(expectedText);
  }

  async verifyElementAttribute(locator: Locator, attribute: string, expectedValue: string): Promise<void> {
    await expect(locator).toHaveAttribute(attribute, expectedValue);
  }

  async verifyElementCount(locator: Locator, expectedCount: number): Promise<void> {
    await expect(locator).toHaveCount(expectedCount);
  }

  async verifyFormValidation(fieldLocator: Locator, errorMessage: string): Promise<void> {
    const errorLocator = this.page.locator(`[data-testid="${await fieldLocator.getAttribute('data-testid')}-error"]`);
    await expect(errorLocator).toContainText(errorMessage);
  }

  async logout(): Promise<void> {
    await this.userMenu.click();
    await this.logoutButton.click();
    await this.page.waitForURL('**/login');
  }

  // Mobile-specific helpers
  async isMobile(): Promise<boolean> {
    const viewport = this.page.viewportSize();
    return viewport ? viewport.width < 768 : false;
  }

  async swipeLeft(locator: Locator): Promise<void> {
    const box = await locator.boundingBox();
    if (box) {
      await this.page.mouse.move(box.x + box.width * 0.8, box.y + box.height / 2);
      await this.page.mouse.down();
      await this.page.mouse.move(box.x + box.width * 0.2, box.y + box.height / 2);
      await this.page.mouse.up();
    }
  }

  async swipeRight(locator: Locator): Promise<void> {
    const box = await locator.boundingBox();
    if (box) {
      await this.page.mouse.move(box.x + box.width * 0.2, box.y + box.height / 2);
      await this.page.mouse.down();
      await this.page.mouse.move(box.x + box.width * 0.8, box.y + box.height / 2);
      await this.page.mouse.up();
    }
  }

  async pinchZoom(locator: Locator, scale: number): Promise<void> {
    const box = await locator.boundingBox();
    if (box) {
      const centerX = box.x + box.width / 2;
      const centerY = box.y + box.height / 2;
      
      // Simulate pinch gesture
      await this.page.touchscreen.tap(centerX - 50, centerY);
      await this.page.touchscreen.tap(centerX + 50, centerY);
    }
  }

  // Performance monitoring helpers
  async measurePageLoadTime(): Promise<number> {
    const startTime = Date.now();
    await this.waitForPageLoad();
    return Date.now() - startTime;
  }

  async measureInteractionTime(action: () => Promise<void>): Promise<number> {
    const startTime = Date.now();
    await action();
    return Date.now() - startTime;
  }

  // Error handling helpers
  async handleUnexpectedError(): Promise<void> {
    const errorVisible = await this.errorMessage.isVisible();
    if (errorVisible) {
      const errorText = await this.errorMessage.textContent();
      console.warn(`Unexpected error encountered: ${errorText}`);
      await this.takeScreenshot('unexpected-error');
    }
  }

  async retryAction(action: () => Promise<void>, maxRetries: number = 3): Promise<void> {
    let lastError: Error | null = null;
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        await action();
        return;
      } catch (error) {
        lastError = error as Error;
        console.warn(`Action failed (attempt ${i + 1}/${maxRetries}):`, error);
        
        if (i < maxRetries - 1) {
          await this.page.waitForTimeout(1000 * (i + 1)); // Exponential backoff
        }
      }
    }
    
    throw lastError;
  }
}