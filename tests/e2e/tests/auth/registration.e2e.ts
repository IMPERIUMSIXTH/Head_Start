import { test, expect } from '@playwright/test';
import { RegistrationPage } from '../../page-objects/registration-page';
import { LoginPage } from '../../page-objects/login-page';

test.describe('Authentication - Registration Flow', () => {
  let registrationPage: RegistrationPage;
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    registrationPage = new RegistrationPage(page);
    loginPage = new LoginPage(page);
    await registrationPage.navigateToRegistration();
  });

  test('should display registration form correctly', async () => {
    await test.step('Verify registration form elements', async () => {
      await registrationPage.verifyElementVisible(registrationPage.registrationForm);
      await registrationPage.verifyElementVisible(registrationPage.fullNameInput);
      await registrationPage.verifyElementVisible(registrationPage.emailInput);
      await registrationPage.verifyElementVisible(registrationPage.passwordInput);
      await registrationPage.verifyElementVisible(registrationPage.confirmPasswordInput);
      await registrationPage.verifyElementVisible(registrationPage.termsCheckbox);
      await registrationPage.verifyElementVisible(registrationPage.privacyCheckbox);
      await registrationPage.verifyElementVisible(registrationPage.registerButton);
      await registrationPage.verifyElementVisible(registrationPage.loginLink);
    });

    await test.step('Verify password strength indicator', async () => {
      await registrationPage.verifyElementVisible(registrationPage.passwordStrengthIndicator);
      await registrationPage.verifyElementVisible(registrationPage.passwordRequirements);
    });
  });

  test('should register successfully with valid data', async () => {
    await test.step('Fill registration form with valid data', async () => {
      await registrationPage.registerValidUser();
    });

    await test.step('Verify successful registration', async () => {
      await registrationPage.verifyElementVisible(registrationPage.registrationSuccess);
    });

    await test.step('Verify email verification flow', async () => {
      await registrationPage.verifyEmailVerificationFlow();
    });
  });

  test('should show error for existing email', async () => {
    await test.step('Try to register with existing email', async () => {
      await registrationPage.registerWithExistingEmail();
    });

    await test.step('Verify error message', async () => {
      await registrationPage.verifyElementVisible(registrationPage.registrationError);
      await registrationPage.verifyElementContainsText(
        registrationPage.registrationError, 
        'already exists'
      );
    });
  });

  test('should validate full name field', async () => {
    await test.step('Test full name validation', async () => {
      await registrationPage.verifyFullNameValidation();
    });
  });

  test('should validate email field', async () => {
    await test.step('Test email validation', async () => {
      await registrationPage.verifyEmailValidation();
    });
  });

  test('should validate password field', async () => {
    await test.step('Test password validation', async () => {
      await registrationPage.verifyPasswordValidation();
    });
  });

  test('should validate password confirmation', async () => {
    await test.step('Test password confirmation validation', async () => {
      await registrationPage.verifyPasswordConfirmationValidation();
    });
  });

  test('should show password strength indicator', async () => {
    await test.step('Test password strength indicator', async () => {
      await registrationPage.verifyPasswordStrengthIndicator();
    });
  });

  test('should validate terms and privacy acceptance', async () => {
    await test.step('Test terms and privacy validation', async () => {
      await registrationPage.verifyTermsAndPrivacyValidation();
    });
  });

  test('should open terms and privacy links', async () => {
    await test.step('Test terms and privacy links', async () => {
      await registrationPage.verifyTermsAndPrivacyLinks();
    });
  });

  test('should navigate to login page', async () => {
    await test.step('Click login link', async () => {
      await registrationPage.navigateToLogin();
    });

    await test.step('Verify navigation to login', async () => {
      await registrationPage.verifyUrl(/.*\/login/);
    });
  });

  test('should support keyboard navigation', async () => {
    await test.step('Test keyboard-only registration', async () => {
      await registrationPage.testRegistrationWithKeyboard();
    });
  });

  test.describe('Security Tests', () => {
    test('should prevent XSS attacks in form fields', async () => {
      await test.step('Test XSS prevention', async () => {
        await registrationPage.verifySecurityFeatures();
      });
    });

    test('should have secure password fields', async () => {
      await test.step('Verify password field security', async () => {
        await expect(registrationPage.passwordInput).toHaveAttribute('type', 'password');
        await expect(registrationPage.confirmPasswordInput).toHaveAttribute('type', 'password');
      });
    });
  });

  test.describe('Accessibility Tests', () => {
    test('should be accessible with keyboard navigation', async () => {
      await test.step('Test accessibility features', async () => {
        await registrationPage.verifyRegistrationFormAccessibility();
      });
    });

    test('should have proper ARIA labels and roles', async () => {
      await test.step('Verify ARIA attributes', async () => {
        await registrationPage.checkAccessibility();
      });
    });
  });

  test.describe('Performance Tests', () => {
    test('should load and perform registration within acceptable time', async () => {
      await test.step('Measure registration performance', async () => {
        const performance = await registrationPage.measureRegistrationPerformance();
        
        // Assert performance thresholds
        expect(performance.loadTime).toBeLessThan(3000); // 3 seconds
        expect(performance.registrationTime).toBeLessThan(3000); // 3 seconds
        expect(performance.validationTime).toBeLessThan(2000); // 2 seconds
      });
    });
  });
});

test.describe('Authentication - Mobile Registration', () => {
  test.use({ 
    viewport: { width: 375, height: 667 } // iPhone SE dimensions
  });

  let registrationPage: RegistrationPage;

  test.beforeEach(async ({ page }) => {
    registrationPage = new RegistrationPage(page);
    await registrationPage.navigateToRegistration();
  });

  test('should work correctly on mobile devices', async () => {
    await test.step('Verify mobile registration experience', async () => {
      await registrationPage.verifyMobileRegistrationExperience();
    });

    await test.step('Test mobile registration flow', async () => {
      await registrationPage.registerValidUser();
    });
  });

  test('should handle virtual keyboard properly', async () => {
    await test.step('Test virtual keyboard interaction', async () => {
      await registrationPage.fullNameInput.tap();
      await registrationPage.page.keyboard.type('Test User');
      
      await registrationPage.emailInput.tap();
      await registrationPage.page.keyboard.type('test@example.com');
      
      await registrationPage.passwordInput.tap();
      await registrationPage.page.keyboard.type('TestPassword123!');
      
      // Verify form is still visible with virtual keyboard
      await registrationPage.verifyElementVisible(registrationPage.registerButton);
    });
  });

  test('should have touch-friendly form elements', async () => {
    await test.step('Verify touch target sizes', async () => {
      const touchElements = [
        registrationPage.fullNameInput,
        registrationPage.emailInput,
        registrationPage.passwordInput,
        registrationPage.confirmPasswordInput,
        registrationPage.termsCheckbox,
        registrationPage.privacyCheckbox,
        registrationPage.registerButton
      ];

      for (const element of touchElements) {
        const box = await element.boundingBox();
        if (box) {
          // Verify minimum touch target size (44px)
          expect(box.height).toBeGreaterThanOrEqual(44);
          expect(box.width).toBeGreaterThanOrEqual(44);
        }
      }
    });
  });
});

test.describe('Registration - Form Validation Edge Cases', () => {
  let registrationPage: RegistrationPage;

  test.beforeEach(async ({ page }) => {
    registrationPage = new RegistrationPage(page);
    await registrationPage.navigateToRegistration();
  });

  test('should handle special characters in full name', async () => {
    await test.step('Test special characters in name', async () => {
      const specialNames = [
        "José María",
        "O'Connor",
        "Jean-Pierre",
        "李小明",
        "محمد"
      ];

      for (const name of specialNames) {
        await registrationPage.fillFormField(registrationPage.fullNameInput, name);
        await registrationPage.emailInput.click();
        await registrationPage.verifyElementHidden(registrationPage.fullNameError);
      }
    });
  });

  test('should handle various email formats', async () => {
    await test.step('Test valid email formats', async () => {
      const validEmails = [
        "test@example.com",
        "user.name@example.com",
        "user+tag@example.com",
        "user123@example-domain.com",
        "test@subdomain.example.com"
      ];

      for (const email of validEmails) {
        await registrationPage.fillFormField(registrationPage.emailInput, email);
        await registrationPage.passwordInput.click();
        await registrationPage.verifyElementHidden(registrationPage.emailError);
      }
    });

    await test.step('Test invalid email formats', async () => {
      const invalidEmails = [
        "invalid-email",
        "@example.com",
        "test@",
        "test..test@example.com",
        "test@example",
        ""
      ];

      for (const email of invalidEmails) {
        await registrationPage.fillFormField(registrationPage.emailInput, email);
        await registrationPage.passwordInput.click();
        await registrationPage.verifyElementVisible(registrationPage.emailError);
      }
    });
  });

  test('should handle password complexity requirements', async () => {
    await test.step('Test various password combinations', async () => {
      const passwordTests = [
        { password: "short", shouldFail: true, reason: "too short" },
        { password: "alllowercase123!", shouldFail: true, reason: "no uppercase" },
        { password: "ALLUPPERCASE123!", shouldFail: true, reason: "no lowercase" },
        { password: "NoNumbers!", shouldFail: true, reason: "no numbers" },
        { password: "ValidPassword123!", shouldFail: false, reason: "valid" }
      ];

      for (const test of passwordTests) {
        await registrationPage.fillFormField(registrationPage.passwordInput, test.password);
        await registrationPage.confirmPasswordInput.click();
        
        if (test.shouldFail) {
          await registrationPage.verifyElementVisible(registrationPage.passwordError);
        } else {
          await registrationPage.verifyElementHidden(registrationPage.passwordError);
        }
      }
    });
  });
});

test.describe('Registration - Integration Tests', () => {
  let registrationPage: RegistrationPage;
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    registrationPage = new RegistrationPage(page);
    loginPage = new LoginPage(page);
  });

  test('should complete full registration and login flow', async () => {
    await test.step('Register new user', async () => {
      await registrationPage.navigateToRegistration();
      await registrationPage.registerValidUser();
    });

    await test.step('Navigate to login and authenticate', async () => {
      await registrationPage.navigateToLogin();
      await loginPage.loginWithValidCredentials();
    });

    await test.step('Verify successful authentication', async () => {
      await loginPage.verifyUrl(/.*\/dashboard/);
    });
  });
});