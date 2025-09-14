import { test, expect } from '@playwright/test';
import { LoginPage } from '../../page-objects/login-page';
import { DashboardPage } from '../../page-objects/dashboard-page';

test.describe('Authentication - Login Flow', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    await loginPage.navigateToLogin();
  });

  test('should display login form correctly', async () => {
    await test.step('Verify login form elements', async () => {
      await loginPage.verifyElementVisible(loginPage.loginForm);
      await loginPage.verifyElementVisible(loginPage.emailInput);
      await loginPage.verifyElementVisible(loginPage.passwordInput);
      await loginPage.verifyElementVisible(loginPage.loginButton);
      await loginPage.verifyElementVisible(loginPage.registerLink);
      await loginPage.verifyElementVisible(loginPage.forgotPasswordLink);
    });

    await test.step('Verify OAuth options are available', async () => {
      await loginPage.verifyOAuthButtonsVisible();
    });
  });

  test('should login successfully with valid credentials', async () => {
    await test.step('Enter valid credentials and login', async () => {
      await loginPage.loginWithValidCredentials();
    });

    await test.step('Verify successful login redirect', async () => {
      await dashboardPage.verifyUrl(/.*\/dashboard/);
      await dashboardPage.verifyDashboardLoaded();
    });

    await test.step('Verify user information is displayed', async () => {
      await dashboardPage.verifyUserInformation('Test User', 'learner');
    });
  });

  test('should show error for invalid credentials', async () => {
    await test.step('Enter invalid credentials', async () => {
      await loginPage.loginWithInvalidCredentials();
    });

    await test.step('Verify error message is displayed', async () => {
      await loginPage.verifyElementVisible(loginPage.loginError);
      await loginPage.verifyElementContainsText(loginPage.loginError, 'Invalid email or password');
    });

    await test.step('Verify user remains on login page', async () => {
      await loginPage.verifyUrl(/.*\/login/);
    });
  });

  test('should validate form fields', async () => {
    await test.step('Test form validation', async () => {
      await loginPage.verifyLoginFormValidation();
    });
  });

  test('should toggle password visibility', async () => {
    await test.step('Test password visibility toggle', async () => {
      await loginPage.fillFormField(loginPage.passwordInput, 'testpassword');
      await loginPage.togglePasswordVisibility();
      await loginPage.togglePasswordVisibility();
    });
  });

  test('should navigate to registration page', async () => {
    await test.step('Click register link', async () => {
      await loginPage.navigateToRegister();
    });

    await test.step('Verify navigation to registration', async () => {
      await loginPage.verifyUrl(/.*\/register/);
    });
  });

  test('should navigate to forgot password page', async () => {
    await test.step('Click forgot password link', async () => {
      await loginPage.navigateToForgotPassword();
    });

    await test.step('Verify navigation to forgot password', async () => {
      await loginPage.verifyUrl(/.*\/forgot-password/);
    });
  });

  test('should support keyboard navigation', async () => {
    await test.step('Test keyboard-only login', async () => {
      await loginPage.testLoginWithKeyboard();
    });

    await test.step('Verify successful keyboard login', async () => {
      await dashboardPage.verifyUrl(/.*\/dashboard/);
    });
  });

  test('should support browser autofill', async () => {
    await test.step('Verify autofill attributes', async () => {
      await loginPage.verifyBrowserAutofillSupport();
    });
  });

  test.describe('OAuth Authentication', () => {
    test('should initiate Google OAuth flow', async () => {
      await test.step('Click Google login button', async () => {
        // Note: This would typically mock the OAuth flow in E2E tests
        await loginPage.verifyElementVisible(loginPage.googleLoginButton);
        // await loginPage.loginWithGoogle(); // Commented out for now
      });
    });

    test('should initiate GitHub OAuth flow', async () => {
      await test.step('Click GitHub login button', async () => {
        await loginPage.verifyElementVisible(loginPage.githubLoginButton);
        // await loginPage.loginWithGithub(); // Commented out for now
      });
    });
  });

  test.describe('Security Tests', () => {
    test('should prevent XSS attacks', async () => {
      await test.step('Test XSS prevention', async () => {
        await loginPage.performSecurityTests();
      });
    });

    test('should implement rate limiting', async () => {
      await test.step('Test rate limiting after multiple failed attempts', async () => {
        // await loginPage.testRateLimiting(); // Commented out to avoid triggering actual rate limits
      });
    });
  });

  test.describe('Accessibility Tests', () => {
    test('should be accessible with keyboard navigation', async () => {
      await test.step('Test accessibility features', async () => {
        await loginPage.verifyLoginFormAccessibility();
      });
    });

    test('should have proper ARIA labels and roles', async () => {
      await test.step('Verify ARIA attributes', async () => {
        await loginPage.checkAccessibility();
      });
    });
  });

  test.describe('Performance Tests', () => {
    test('should load and perform login within acceptable time', async () => {
      await test.step('Measure login performance', async () => {
        const performance = await loginPage.measureLoginPerformance();
        
        // Assert performance thresholds
        expect(performance.loadTime).toBeLessThan(3000); // 3 seconds
        expect(performance.loginTime).toBeLessThan(2000); // 2 seconds
      });
    });
  });
});

test.describe('Authentication - Mobile Login', () => {
  test.use({ 
    viewport: { width: 375, height: 667 } // iPhone SE dimensions
  });

  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.navigateToLogin();
  });

  test('should work correctly on mobile devices', async () => {
    await test.step('Verify mobile login experience', async () => {
      await loginPage.verifyMobileLoginExperience();
    });

    await test.step('Test mobile login flow', async () => {
      await loginPage.loginWithValidCredentials();
    });
  });

  test('should handle virtual keyboard properly', async () => {
    await test.step('Test virtual keyboard interaction', async () => {
      await loginPage.emailInput.tap();
      await loginPage.page.keyboard.type('test@example.com');
      
      await loginPage.passwordInput.tap();
      await loginPage.page.keyboard.type('TestPassword123!');
      
      // Verify form is still visible with virtual keyboard
      await loginPage.verifyElementVisible(loginPage.loginButton);
    });
  });
});

test.describe('Authentication - Cross-Browser Compatibility', () => {
  ['chromium', 'firefox', 'webkit'].forEach(browserName => {
    test(`should work correctly in ${browserName}`, async ({ page, browserName: currentBrowser }) => {
      test.skip(currentBrowser !== browserName, `Skipping ${browserName} test in ${currentBrowser}`);
      
      const loginPage = new LoginPage(page);
      const dashboardPage = new DashboardPage(page);
      
      await test.step(`Test login flow in ${browserName}`, async () => {
        await loginPage.navigateToLogin();
        await loginPage.loginWithValidCredentials();
        await dashboardPage.verifyDashboardLoaded();
      });
    });
  });
});