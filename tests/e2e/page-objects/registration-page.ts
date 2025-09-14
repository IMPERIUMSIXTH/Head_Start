import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * Registration Page Object Model
 * Handles user registration workflows and form validation
 */
export class RegistrationPage extends BasePage {
  // Form elements
  get registrationForm(): Locator {
    return this.page.locator('[data-testid="registration-form"]');
  }

  get fullNameInput(): Locator {
    return this.page.locator('[data-testid="full-name-input"]');
  }

  get emailInput(): Locator {
    return this.page.locator('[data-testid="email-input"]');
  }

  get passwordInput(): Locator {
    return this.page.locator('[data-testid="password-input"]');
  }

  get confirmPasswordInput(): Locator {
    return this.page.locator('[data-testid="confirm-password-input"]');
  }

  get registerButton(): Locator {
    return this.page.locator('[data-testid="register-button"]');
  }

  get loginLink(): Locator {
    return this.page.locator('[data-testid="login-link"]');
  }

  // Terms and privacy
  get termsCheckbox(): Locator {
    return this.page.locator('[data-testid="terms-checkbox"]');
  }

  get privacyCheckbox(): Locator {
    return this.page.locator('[data-testid="privacy-checkbox"]');
  }

  get termsLink(): Locator {
    return this.page.locator('[data-testid="terms-link"]');
  }

  get privacyLink(): Locator {
    return this.page.locator('[data-testid="privacy-link"]');
  }

  // Password strength indicator
  get passwordStrengthIndicator(): Locator {
    return this.page.locator('[data-testid="password-strength-indicator"]');
  }

  get passwordRequirements(): Locator {
    return this.page.locator('[data-testid="password-requirements"]');
  }

  // Error messages
  get fullNameError(): Locator {
    return this.page.locator('[data-testid="full-name-error"]');
  }

  get emailError(): Locator {
    return this.page.locator('[data-testid="email-error"]');
  }

  get passwordError(): Locator {
    return this.page.locator('[data-testid="password-error"]');
  }

  get confirmPasswordError(): Locator {
    return this.page.locator('[data-testid="confirm-password-error"]');
  }

  get registrationError(): Locator {
    return this.page.locator('[data-testid="registration-error"]');
  }

  // Success elements
  get registrationSuccess(): Locator {
    return this.page.locator('[data-testid="registration-success"]');
  }

  get verificationMessage(): Locator {
    return this.page.locator('[data-testid="verification-message"]');
  }

  // Page actions
  async navigateToRegistration(): Promise<void> {
    await this.navigateTo('/register');
    await this.verifyPageTitle('Register - HeadStart');
    await this.verifyElementVisible(this.registrationForm);
  }

  async register(
    fullName: string,
    email: string,
    password: string,
    confirmPassword: string,
    acceptTerms: boolean = true,
    acceptPrivacy: boolean = true
  ): Promise<void> {
    await this.fillFormField(this.fullNameInput, fullName);
    await this.fillFormField(this.emailInput, email);
    await this.fillFormField(this.passwordInput, password);
    await this.fillFormField(this.confirmPasswordInput, confirmPassword);

    if (acceptTerms) {
      await this.termsCheckbox.check();
    }

    if (acceptPrivacy) {
      await this.privacyCheckbox.check();
    }

    await this.registerButton.click();
  }

  async registerValidUser(): Promise<void> {
    const timestamp = Date.now();
    await this.register(
      'Test User',
      `testuser${timestamp}@example.com`,
      'TestPassword123!',
      'TestPassword123!'
    );
    
    // Wait for successful registration
    await this.verifyElementVisible(this.registrationSuccess);
  }

  async registerWithExistingEmail(): Promise<void> {
    await this.register(
      'Test User',
      'testuser@example.com', // Existing email
      'TestPassword123!',
      'TestPassword123!'
    );
    
    await this.verifyElementVisible(this.registrationError);
    await this.verifyElementContainsText(this.registrationError, 'already exists');
  }

  async navigateToLogin(): Promise<void> {
    await this.clickAndWaitForNavigation(this.loginLink, '**/login');
  }

  // Validation methods
  async verifyFullNameValidation(): Promise<void> {
    // Test empty full name
    await this.fillFormField(this.fullNameInput, '');
    await this.emailInput.click();
    await this.verifyFormValidation(this.fullNameInput, 'Full name is required');

    // Test short full name
    await this.fillFormField(this.fullNameInput, 'A');
    await this.emailInput.click();
    await this.verifyFormValidation(this.fullNameInput, 'Full name must be at least 2 characters');

    // Test valid full name
    await this.fillFormField(this.fullNameInput, 'John Doe');
    await this.emailInput.click();
    await this.verifyElementHidden(this.fullNameError);
  }

  async verifyEmailValidation(): Promise<void> {
    // Test empty email
    await this.fillFormField(this.emailInput, '');
    await this.passwordInput.click();
    await this.verifyFormValidation(this.emailInput, 'Email is required');

    // Test invalid email format
    await this.fillFormField(this.emailInput, 'invalid-email');
    await this.passwordInput.click();
    await this.verifyFormValidation(this.emailInput, 'Please enter a valid email address');

    // Test valid email
    await this.fillFormField(this.emailInput, 'test@example.com');
    await this.passwordInput.click();
    await this.verifyElementHidden(this.emailError);
  }

  async verifyPasswordValidation(): Promise<void> {
    // Test empty password
    await this.fillFormField(this.passwordInput, '');
    await this.confirmPasswordInput.click();
    await this.verifyFormValidation(this.passwordInput, 'Password is required');

    // Test short password
    await this.fillFormField(this.passwordInput, '123');
    await this.confirmPasswordInput.click();
    await this.verifyFormValidation(this.passwordInput, 'Password must be at least 8 characters');

    // Test password without uppercase
    await this.fillFormField(this.passwordInput, 'password123!');
    await this.confirmPasswordInput.click();
    await this.verifyFormValidation(this.passwordInput, 'Password must contain at least one uppercase letter');

    // Test password without lowercase
    await this.fillFormField(this.passwordInput, 'PASSWORD123!');
    await this.confirmPasswordInput.click();
    await this.verifyFormValidation(this.passwordInput, 'Password must contain at least one lowercase letter');

    // Test password without number
    await this.fillFormField(this.passwordInput, 'Password!');
    await this.confirmPasswordInput.click();
    await this.verifyFormValidation(this.passwordInput, 'Password must contain at least one digit');

    // Test valid password
    await this.fillFormField(this.passwordInput, 'TestPassword123!');
    await this.confirmPasswordInput.click();
    await this.verifyElementHidden(this.passwordError);
  }

  async verifyPasswordConfirmationValidation(): Promise<void> {
    await this.fillFormField(this.passwordInput, 'TestPassword123!');
    
    // Test empty confirmation
    await this.fillFormField(this.confirmPasswordInput, '');
    await this.fullNameInput.click();
    await this.verifyFormValidation(this.confirmPasswordInput, 'Please confirm your password');

    // Test mismatched passwords
    await this.fillFormField(this.confirmPasswordInput, 'DifferentPassword123!');
    await this.fullNameInput.click();
    await this.verifyFormValidation(this.confirmPasswordInput, 'Passwords do not match');

    // Test matching passwords
    await this.fillFormField(this.confirmPasswordInput, 'TestPassword123!');
    await this.fullNameInput.click();
    await this.verifyElementHidden(this.confirmPasswordError);
  }

  async verifyPasswordStrengthIndicator(): Promise<void> {
    await this.verifyElementVisible(this.passwordStrengthIndicator);
    await this.verifyElementVisible(this.passwordRequirements);

    // Test weak password
    await this.fillFormField(this.passwordInput, '123');
    await this.verifyElementContainsText(this.passwordStrengthIndicator, 'Weak');

    // Test medium password
    await this.fillFormField(this.passwordInput, 'password123');
    await this.verifyElementContainsText(this.passwordStrengthIndicator, 'Medium');

    // Test strong password
    await this.fillFormField(this.passwordInput, 'TestPassword123!');
    await this.verifyElementContainsText(this.passwordStrengthIndicator, 'Strong');
  }

  async verifyTermsAndPrivacyValidation(): Promise<void> {
    // Fill valid form data
    await this.fillFormField(this.fullNameInput, 'Test User');
    await this.fillFormField(this.emailInput, 'test@example.com');
    await this.fillFormField(this.passwordInput, 'TestPassword123!');
    await this.fillFormField(this.confirmPasswordInput, 'TestPassword123!');

    // Try to submit without accepting terms
    await this.termsCheckbox.uncheck();
    await this.privacyCheckbox.check();
    await this.registerButton.click();

    const termsError = this.page.locator('[data-testid="terms-error"]');
    await this.verifyElementVisible(termsError);

    // Try to submit without accepting privacy
    await this.termsCheckbox.check();
    await this.privacyCheckbox.uncheck();
    await this.registerButton.click();

    const privacyError = this.page.locator('[data-testid="privacy-error"]');
    await this.verifyElementVisible(privacyError);
  }

  async verifyTermsAndPrivacyLinks(): Promise<void> {
    // Test terms link opens in new tab
    const [termsPage] = await Promise.all([
      this.page.waitForEvent('popup'),
      this.termsLink.click()
    ]);
    
    await termsPage.waitForLoadState();
    expect(termsPage.url()).toContain('/terms');
    await termsPage.close();

    // Test privacy link opens in new tab
    const [privacyPage] = await Promise.all([
      this.page.waitForEvent('popup'),
      this.privacyLink.click()
    ]);
    
    await privacyPage.waitForLoadState();
    expect(privacyPage.url()).toContain('/privacy');
    await privacyPage.close();
  }

  async verifyRegistrationFormAccessibility(): Promise<void> {
    // Verify form labels and ARIA attributes
    await expect(this.fullNameInput).toHaveAttribute('aria-label', 'Full name');
    await expect(this.emailInput).toHaveAttribute('aria-label', 'Email address');
    await expect(this.passwordInput).toHaveAttribute('aria-label', 'Password');
    await expect(this.confirmPasswordInput).toHaveAttribute('aria-label', 'Confirm password');

    // Verify form can be navigated with keyboard
    await this.fullNameInput.focus();
    await this.page.keyboard.press('Tab');
    await expect(this.emailInput).toBeFocused();
    
    await this.page.keyboard.press('Tab');
    await expect(this.passwordInput).toBeFocused();
    
    await this.page.keyboard.press('Tab');
    await expect(this.confirmPasswordInput).toBeFocused();
    
    await this.page.keyboard.press('Tab');
    await expect(this.termsCheckbox).toBeFocused();
    
    await this.page.keyboard.press('Tab');
    await expect(this.privacyCheckbox).toBeFocused();
    
    await this.page.keyboard.press('Tab');
    await expect(this.registerButton).toBeFocused();
  }

  async verifyMobileRegistrationExperience(): Promise<void> {
    if (await this.isMobile()) {
      // Verify mobile-specific elements
      await this.verifyElementVisible(this.registrationForm);
      
      // Test touch interactions
      await this.fullNameInput.tap();
      await this.verifyElementAttribute(this.fullNameInput, 'inputmode', 'text');
      
      await this.emailInput.tap();
      await this.verifyElementAttribute(this.emailInput, 'inputmode', 'email');
      
      // Verify virtual keyboard doesn't obscure form
      const formBox = await this.registrationForm.boundingBox();
      const viewportHeight = this.page.viewportSize()?.height || 0;
      
      if (formBox) {
        expect(formBox.y + formBox.height).toBeLessThan(viewportHeight);
      }
    }
  }

  async testRegistrationWithKeyboard(): Promise<void> {
    // Navigate and fill form using only keyboard
    await this.fullNameInput.focus();
    await this.page.keyboard.type('Test User');
    
    await this.page.keyboard.press('Tab');
    await this.page.keyboard.type('test@example.com');
    
    await this.page.keyboard.press('Tab');
    await this.page.keyboard.type('TestPassword123!');
    
    await this.page.keyboard.press('Tab');
    await this.page.keyboard.type('TestPassword123!');
    
    await this.page.keyboard.press('Tab');
    await this.page.keyboard.press('Space'); // Check terms
    
    await this.page.keyboard.press('Tab');
    await this.page.keyboard.press('Space'); // Check privacy
    
    await this.page.keyboard.press('Tab');
    await this.page.keyboard.press('Enter'); // Submit form
    
    await this.verifyElementVisible(this.registrationSuccess);
  }

  async measureRegistrationPerformance(): Promise<{
    loadTime: number;
    registrationTime: number;
    validationTime: number;
  }> {
    const loadTime = await this.measurePageLoadTime();
    
    const validationTime = await this.measureInteractionTime(async () => {
      await this.verifyFullNameValidation();
      await this.verifyEmailValidation();
      await this.verifyPasswordValidation();
    });
    
    const registrationTime = await this.measureInteractionTime(async () => {
      await this.registerValidUser();
    });
    
    return { loadTime, registrationTime, validationTime };
  }

  async verifySecurityFeatures(): Promise<void> {
    // Test XSS prevention in form fields
    const xssPayload = '<script>alert("xss")</script>';
    await this.fillFormField(this.fullNameInput, xssPayload);
    await this.fillFormField(this.emailInput, xssPayload);
    
    // Verify no script execution
    const alertDialogs = this.page.locator('dialog[role="alertdialog"]');
    await expect(alertDialogs).toHaveCount(0);

    // Verify password field security
    await expect(this.passwordInput).toHaveAttribute('type', 'password');
    await expect(this.confirmPasswordInput).toHaveAttribute('type', 'password');
    
    // Verify autocomplete attributes for security
    await expect(this.passwordInput).toHaveAttribute('autocomplete', 'new-password');
    await expect(this.confirmPasswordInput).toHaveAttribute('autocomplete', 'new-password');
  }

  async verifyEmailVerificationFlow(): Promise<void> {
    await this.registerValidUser();
    
    // Verify verification message is displayed
    await this.verifyElementVisible(this.verificationMessage);
    await this.verifyElementContainsText(
      this.verificationMessage, 
      'Please check your email to verify your account'
    );
    
    // Verify user is redirected to appropriate page
    await this.page.waitForURL('**/verify-email');
  }
}