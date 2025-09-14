import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * Login Page Object Model
 * Handles authentication workflows and login interactions
 */
export class LoginPage extends BasePage {
  // Page locators
  get emailInput(): Locator {
    return this.page.locator('[data-testid="email-input"]');
  }

  get passwordInput(): Locator {
    return this.page.locator('[data-testid="password-input"]');
  }

  get loginButton(): Locator {
    return this.page.locator('[data-testid="login-button"]');
  }

  get registerLink(): Locator {
    return this.page.locator('[data-testid="register-link"]');
  }

  get forgotPasswordLink(): Locator {
    return this.page.locator('[data-testid="forgot-password-link"]');
  }

  get rememberMeCheckbox(): Locator {
    return this.page.locator('[data-testid="remember-me-checkbox"]');
  }

  get showPasswordButton(): Locator {
    return this.page.locator('[data-testid="show-password-button"]');
  }

  get loginForm(): Locator {
    return this.page.locator('[data-testid="login-form"]');
  }

  get emailError(): Locator {
    return this.page.locator('[data-testid="email-error"]');
  }

  get passwordError(): Locator {
    return this.page.locator('[data-testid="password-error"]');
  }

  get loginError(): Locator {
    return this.page.locator('[data-testid="login-error"]');
  }

  // OAuth buttons
  get googleLoginButton(): Locator {
    return this.page.locator('[data-testid="google-login-button"]');
  }

  get githubLoginButton(): Locator {
    return this.page.locator('[data-testid="github-login-button"]');
  }

  get oauthSection(): Locator {
    return this.page.locator('[data-testid="oauth-section"]');
  }

  // Page actions
  async navigateToLogin(): Promise<void> {
    await this.navigateTo('/login');
    await this.verifyPageTitle('Login - HeadStart');
    await this.verifyElementVisible(this.loginForm);
  }

  async login(email: string, password: string, rememberMe: boolean = false): Promise<void> {
    await this.fillFormField(this.emailInput, email);
    await this.fillFormField(this.passwordInput, password);
    
    if (rememberMe) {
      await this.rememberMeCheckbox.check();
    }
    
    await this.clickAndWaitForNavigation(this.loginButton, '**/dashboard');
  }

  async loginWithValidCredentials(): Promise<void> {
    await this.login('testuser@example.com', 'TestPassword123!');
  }

  async loginWithInvalidCredentials(): Promise<void> {
    await this.login('invalid@example.com', 'wrongpassword');
    await this.verifyElementVisible(this.loginError);
  }

  async loginAsAdmin(): Promise<void> {
    await this.login('admin@example.com', 'AdminPassword123!');
  }

  async loginAsEducator(): Promise<void> {
    await this.login('educator@example.com', 'EducatorPassword123!');
  }

  async togglePasswordVisibility(): Promise<void> {
    const isPasswordHidden = await this.passwordInput.getAttribute('type') === 'password';
    await this.showPasswordButton.click();
    
    if (isPasswordHidden) {
      await expect(this.passwordInput).toHaveAttribute('type', 'text');
    } else {
      await expect(this.passwordInput).toHaveAttribute('type', 'password');
    }
  }

  async navigateToRegister(): Promise<void> {
    await this.clickAndWaitForNavigation(this.registerLink, '**/register');
  }

  async navigateToForgotPassword(): Promise<void> {
    await this.clickAndWaitForNavigation(this.forgotPasswordLink, '**/forgot-password');
  }

  // OAuth login methods
  async loginWithGoogle(): Promise<void> {
    // Note: In real E2E tests, this would handle OAuth flow
    // For now, we'll simulate the button click and mock the response
    await this.googleLoginButton.click();
    
    // Wait for OAuth redirect (would be handled by OAuth provider in real scenario)
    await this.page.waitForTimeout(2000);
    
    // Verify successful login (assuming OAuth succeeds)
    await this.page.waitForURL('**/dashboard', { timeout: 10000 });
  }

  async loginWithGithub(): Promise<void> {
    await this.githubLoginButton.click();
    await this.page.waitForTimeout(2000);
    await this.page.waitForURL('**/dashboard', { timeout: 10000 });
  }

  // Validation methods
  async verifyEmailValidation(invalidEmail: string, expectedError: string): Promise<void> {
    await this.fillFormField(this.emailInput, invalidEmail);
    await this.passwordInput.click(); // Trigger validation
    await this.verifyFormValidation(this.emailInput, expectedError);
  }

  async verifyPasswordValidation(invalidPassword: string, expectedError: string): Promise<void> {
    await this.fillFormField(this.passwordInput, invalidPassword);
    await this.emailInput.click(); // Trigger validation
    await this.verifyFormValidation(this.passwordInput, expectedError);
  }

  async verifyLoginFormValidation(): Promise<void> {
    // Test empty form submission
    await this.loginButton.click();
    await this.verifyElementVisible(this.emailError);
    await this.verifyElementVisible(this.passwordError);

    // Test invalid email format
    await this.verifyEmailValidation('invalid-email', 'Please enter a valid email address');

    // Test short password
    await this.verifyPasswordValidation('123', 'Password must be at least 8 characters long');
  }

  async verifyOAuthButtonsVisible(): Promise<void> {
    await this.verifyElementVisible(this.oauthSection);
    await this.verifyElementVisible(this.googleLoginButton);
    await this.verifyElementVisible(this.githubLoginButton);
  }

  async verifyLoginFormAccessibility(): Promise<void> {
    // Verify form labels and ARIA attributes
    await expect(this.emailInput).toHaveAttribute('aria-label', 'Email address');
    await expect(this.passwordInput).toHaveAttribute('aria-label', 'Password');
    await expect(this.loginButton).toHaveAttribute('aria-label', 'Sign in to your account');

    // Verify form can be navigated with keyboard
    await this.emailInput.focus();
    await this.page.keyboard.press('Tab');
    await expect(this.passwordInput).toBeFocused();
    
    await this.page.keyboard.press('Tab');
    await expect(this.rememberMeCheckbox).toBeFocused();
    
    await this.page.keyboard.press('Tab');
    await expect(this.loginButton).toBeFocused();
  }

  async verifyMobileLoginExperience(): Promise<void> {
    if (await this.isMobile()) {
      // Verify mobile-specific elements
      await this.verifyElementVisible(this.loginForm);
      
      // Test touch interactions
      await this.emailInput.tap();
      await this.verifyElementAttribute(this.emailInput, 'inputmode', 'email');
      
      await this.passwordInput.tap();
      await this.verifyElementAttribute(this.passwordInput, 'type', 'password');
      
      // Verify virtual keyboard doesn't obscure form
      const formBox = await this.loginForm.boundingBox();
      const viewportHeight = this.page.viewportSize()?.height || 0;
      
      if (formBox) {
        expect(formBox.y + formBox.height).toBeLessThan(viewportHeight);
      }
    }
  }

  async performSecurityTests(): Promise<void> {
    // Test XSS prevention
    const xssPayload = '<script>alert("xss")</script>';
    await this.fillFormField(this.emailInput, xssPayload);
    await this.fillFormField(this.passwordInput, xssPayload);
    await this.loginButton.click();
    
    // Verify no script execution
    const alertDialogs = this.page.locator('dialog[role="alertdialog"]');
    await expect(alertDialogs).toHaveCount(0);

    // Test SQL injection prevention
    const sqlPayload = "'; DROP TABLE users; --";
    await this.fillFormField(this.emailInput, sqlPayload);
    await this.fillFormField(this.passwordInput, sqlPayload);
    await this.loginButton.click();
    
    // Verify appropriate error handling
    await this.verifyElementVisible(this.loginError);
  }

  async measureLoginPerformance(): Promise<{ loadTime: number; loginTime: number }> {
    const loadTime = await this.measurePageLoadTime();
    
    const loginTime = await this.measureInteractionTime(async () => {
      await this.loginWithValidCredentials();
    });
    
    return { loadTime, loginTime };
  }

  async testLoginWithKeyboard(): Promise<void> {
    // Navigate and fill form using only keyboard
    await this.emailInput.focus();
    await this.page.keyboard.type('testuser@example.com');
    
    await this.page.keyboard.press('Tab');
    await this.page.keyboard.type('TestPassword123!');
    
    await this.page.keyboard.press('Tab');
    await this.page.keyboard.press('Tab'); // Skip remember me
    await this.page.keyboard.press('Enter'); // Submit form
    
    await this.page.waitForURL('**/dashboard');
  }

  async verifyBrowserAutofillSupport(): Promise<void> {
    // Verify autocomplete attributes
    await expect(this.emailInput).toHaveAttribute('autocomplete', 'email');
    await expect(this.passwordInput).toHaveAttribute('autocomplete', 'current-password');
    
    // Verify form structure supports password managers
    await expect(this.loginForm).toHaveAttribute('method', 'post');
  }

  async testRateLimiting(): Promise<void> {
    // Attempt multiple failed logins to test rate limiting
    for (let i = 0; i < 6; i++) {
      await this.login('test@example.com', 'wrongpassword');
      await this.page.waitForTimeout(500);
    }
    
    // Verify rate limiting message appears
    const rateLimitError = this.page.locator('[data-testid="rate-limit-error"]');
    await this.verifyElementVisible(rateLimitError);
  }
}