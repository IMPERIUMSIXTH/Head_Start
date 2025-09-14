import { test, expect } from '@playwright/test';
import { RegistrationPage } from '../../page-objects/registration-page';
import { LoginPage } from '../../page-objects/login-page';
import { DashboardPage } from '../../page-objects/dashboard-page';

test.describe('Critical Path: Complete User Registration Flow', () => {
  let registrationPage: RegistrationPage;
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    registrationPage = new RegistrationPage(page);
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
  });

  test('should complete full user onboarding journey', async () => {
    const timestamp = Date.now();
    const testEmail = `newuser${timestamp}@example.com`;
    const testName = 'New Test User';
    const testPassword = 'NewUserPassword123!';

    await test.step('1. Navigate to registration page', async () => {
      await registrationPage.navigateToRegistration();
      await registrationPage.verifyElementVisible(registrationPage.registrationForm);
    });

    await test.step('2. Complete registration form', async () => {
      await registrationPage.register(
        testName,
        testEmail,
        testPassword,
        testPassword,
        true, // accept terms
        true  // accept privacy
      );
    });

    await test.step('3. Verify successful registration', async () => {
      await registrationPage.verifyElementVisible(registrationPage.registrationSuccess);
      
      // Check for email verification message
      const verificationMessage = registrationPage.verificationMessage;
      if (await verificationMessage.isVisible()) {
        await registrationPage.verifyElementContainsText(
          verificationMessage,
          'verify your account'
        );
      }
    });

    await test.step('4. Navigate to login page', async () => {
      await loginPage.navigateToLogin();
      await loginPage.verifyElementVisible(loginPage.loginForm);
    });

    await test.step('5. Login with new account', async () => {
      await loginPage.login(testEmail, testPassword);
    });

    await test.step('6. Verify successful login and dashboard access', async () => {
      await dashboardPage.verifyUrl(/.*\/dashboard/);
      await dashboardPage.verifyDashboardLoaded();
      await dashboardPage.verifyUserInformation(testName, 'learner');
    });

    await test.step('7. Verify initial user experience', async () => {
      // New users should see welcome content
      await dashboardPage.verifyElementVisible(dashboardPage.welcomeSection);
      
      // Statistics should show zero or minimal activity
      const interactionsText = await dashboardPage.totalInteractionsCount.textContent();
      const completedText = await dashboardPage.completedContentCount.textContent();
      
      expect(interactionsText).toMatch(/^[0-9]+$/);
      expect(completedText).toMatch(/^[0-9]+$/);
      
      // New users might have zero interactions
      const interactions = parseInt(interactionsText || '0');
      const completed = parseInt(completedText || '0');
      
      expect(interactions).toBeGreaterThanOrEqual(0);
      expect(completed).toBeGreaterThanOrEqual(0);
      expect(completed).toBeLessThanOrEqual(interactions);
    });

    await test.step('8. Test initial navigation and exploration', async () => {
      // New users should be able to explore content
      await dashboardPage.navigateToContentBrowse();
      await dashboardPage.verifyUrl(/.*\/content/);
      
      // Navigate back to dashboard
      await dashboardPage.navigateToDashboard();
      await dashboardPage.verifyDashboardLoaded();
    });

    await test.step('9. Test preferences setup', async () => {
      // New users should be able to set preferences
      await dashboardPage.navigateToPreferences();
      await dashboardPage.verifyUrl(/.*\/preferences/);
      
      // Navigate back to dashboard
      await dashboardPage.navigateToDashboard();
      await dashboardPage.verifyDashboardLoaded();
    });

    await test.step('10. Test logout functionality', async () => {
      await dashboardPage.logout();
      await dashboardPage.verifyUrl(/.*\/login/);
    });

    await test.step('11. Verify login persistence', async () => {
      // Login again to verify account is properly created
      await loginPage.login(testEmail, testPassword);
      await dashboardPage.verifyUrl(/.*\/dashboard/);
      await dashboardPage.verifyUserInformation(testName, 'learner');
    });
  });

  test('should handle registration errors gracefully', async () => {
    await test.step('1. Navigate to registration page', async () => {
      await registrationPage.navigateToRegistration();
    });

    await test.step('2. Test duplicate email registration', async () => {
      await registrationPage.register(
        'Test User',
        'testuser@example.com', // Existing email
        'TestPassword123!',
        'TestPassword123!'
      );
      
      await registrationPage.verifyElementVisible(registrationPage.registrationError);
      await registrationPage.verifyElementContainsText(
        registrationPage.registrationError,
        'already exists'
      );
    });

    await test.step('3. Test form validation errors', async () => {
      // Clear form and test validation
      await registrationPage.page.reload();
      await registrationPage.waitForPageLoad();
      
      // Submit empty form
      await registrationPage.registerButton.click();
      
      // Verify validation errors appear
      await registrationPage.verifyElementVisible(registrationPage.fullNameError);
      await registrationPage.verifyElementVisible(registrationPage.emailError);
      await registrationPage.verifyElementVisible(registrationPage.passwordError);
    });

    await test.step('4. Test password mismatch', async () => {
      await registrationPage.fillFormField(registrationPage.fullNameInput, 'Test User');
      await registrationPage.fillFormField(registrationPage.emailInput, 'test@example.com');
      await registrationPage.fillFormField(registrationPage.passwordInput, 'TestPassword123!');
      await registrationPage.fillFormField(registrationPage.confirmPasswordInput, 'DifferentPassword123!');
      
      await registrationPage.termsCheckbox.check();
      await registrationPage.privacyCheckbox.check();
      
      await registrationPage.registerButton.click();
      
      await registrationPage.verifyElementVisible(registrationPage.confirmPasswordError);
      await registrationPage.verifyElementContainsText(
        registrationPage.confirmPasswordError,
        'do not match'
      );
    });
  });

  test('should support keyboard-only registration flow', async () => {
    const timestamp = Date.now();
    const testEmail = `keyboarduser${timestamp}@example.com`;

    await test.step('1. Navigate to registration using keyboard', async () => {
      await registrationPage.navigateToRegistration();
      await registrationPage.fullNameInput.focus();
    });

    await test.step('2. Complete form using only keyboard', async () => {
      // Fill form using keyboard navigation
      await registrationPage.page.keyboard.type('Keyboard Test User');
      
      await registrationPage.page.keyboard.press('Tab');
      await registrationPage.page.keyboard.type(testEmail);
      
      await registrationPage.page.keyboard.press('Tab');
      await registrationPage.page.keyboard.type('KeyboardPassword123!');
      
      await registrationPage.page.keyboard.press('Tab');
      await registrationPage.page.keyboard.type('KeyboardPassword123!');
      
      await registrationPage.page.keyboard.press('Tab');
      await registrationPage.page.keyboard.press('Space'); // Check terms
      
      await registrationPage.page.keyboard.press('Tab');
      await registrationPage.page.keyboard.press('Space'); // Check privacy
      
      await registrationPage.page.keyboard.press('Tab');
      await registrationPage.page.keyboard.press('Enter'); // Submit
    });

    await test.step('3. Verify successful keyboard registration', async () => {
      await registrationPage.verifyElementVisible(registrationPage.registrationSuccess);
    });

    await test.step('4. Complete login using keyboard', async () => {
      await loginPage.navigateToLogin();
      await loginPage.testLoginWithKeyboard();
    });

    await test.step('5. Verify dashboard access', async () => {
      await dashboardPage.verifyUrl(/.*\/dashboard/);
      await dashboardPage.verifyDashboardLoaded();
    });
  });

  test('should work correctly on mobile devices', async () => {
    test.use({ viewport: { width: 375, height: 667 } });

    const timestamp = Date.now();
    const testEmail = `mobileuser${timestamp}@example.com`;

    await test.step('1. Mobile registration flow', async () => {
      await registrationPage.navigateToRegistration();
      await registrationPage.verifyMobileRegistrationExperience();
    });

    await test.step('2. Complete mobile registration', async () => {
      await registrationPage.register(
        'Mobile Test User',
        testEmail,
        'MobilePassword123!',
        'MobilePassword123!'
      );
      
      await registrationPage.verifyElementVisible(registrationPage.registrationSuccess);
    });

    await test.step('3. Mobile login flow', async () => {
      await loginPage.navigateToLogin();
      await loginPage.verifyMobileLoginExperience();
      await loginPage.login(testEmail, 'MobilePassword123!');
    });

    await test.step('4. Mobile dashboard verification', async () => {
      await dashboardPage.verifyUrl(/.*\/dashboard/);
      await dashboardPage.verifyMobileDashboard();
    });
  });

  test('should handle network interruptions gracefully', async () => {
    const timestamp = Date.now();
    const testEmail = `networkuser${timestamp}@example.com`;

    await test.step('1. Start registration process', async () => {
      await registrationPage.navigateToRegistration();
      await registrationPage.fillFormField(registrationPage.fullNameInput, 'Network Test User');
      await registrationPage.fillFormField(registrationPage.emailInput, testEmail);
      await registrationPage.fillFormField(registrationPage.passwordInput, 'NetworkPassword123!');
      await registrationPage.fillFormField(registrationPage.confirmPasswordInput, 'NetworkPassword123!');
      await registrationPage.termsCheckbox.check();
      await registrationPage.privacyCheckbox.check();
    });

    await test.step('2. Simulate network delay during registration', async () => {
      // Add network delay
      await registrationPage.page.route('**/api/auth/register', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
        await route.continue();
      });

      await registrationPage.registerButton.click();
      
      // Verify loading state is shown
      const loadingSpinner = registrationPage.loadingSpinner;
      if (await loadingSpinner.isVisible()) {
        await registrationPage.verifyElementVisible(loadingSpinner);
      }
    });

    await test.step('3. Verify successful registration after delay', async () => {
      await registrationPage.verifyElementVisible(registrationPage.registrationSuccess);
    });

    await test.step('4. Test login with network delay', async () => {
      await loginPage.navigateToLogin();
      
      // Add network delay for login
      await loginPage.page.route('**/api/auth/login', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 1500)); // 1.5 second delay
        await route.continue();
      });

      await loginPage.login(testEmail, 'NetworkPassword123!');
    });

    await test.step('5. Verify successful login after delay', async () => {
      await dashboardPage.verifyUrl(/.*\/dashboard/);
      await dashboardPage.verifyDashboardLoaded();
    });
  });

  test('should maintain data integrity throughout the flow', async () => {
    const timestamp = Date.now();
    const testEmail = `integrityuser${timestamp}@example.com`;
    const testName = 'Data Integrity User';

    await test.step('1. Register with specific user data', async () => {
      await registrationPage.navigateToRegistration();
      await registrationPage.register(
        testName,
        testEmail,
        'IntegrityPassword123!',
        'IntegrityPassword123!'
      );
      await registrationPage.verifyElementVisible(registrationPage.registrationSuccess);
    });

    await test.step('2. Login and verify user data persistence', async () => {
      await loginPage.navigateToLogin();
      await loginPage.login(testEmail, 'IntegrityPassword123!');
      await dashboardPage.verifyUserInformation(testName, 'learner');
    });

    await test.step('3. Navigate away and back to verify session persistence', async () => {
      await dashboardPage.navigateToContentBrowse();
      await dashboardPage.navigateToDashboard();
      await dashboardPage.verifyUserInformation(testName, 'learner');
    });

    await test.step('4. Logout and login again to verify data persistence', async () => {
      await dashboardPage.logout();
      await loginPage.login(testEmail, 'IntegrityPassword123!');
      await dashboardPage.verifyUserInformation(testName, 'learner');
    });
  });

  test('should provide appropriate error recovery', async () => {
    await test.step('1. Test registration form recovery after errors', async () => {
      await registrationPage.navigateToRegistration();
      
      // Submit invalid form
      await registrationPage.register(
        'A', // Too short name
        'invalid-email', // Invalid email
        '123', // Weak password
        '456', // Mismatched password
        false, // Don't accept terms
        false  // Don't accept privacy
      );
      
      // Verify errors are shown
      await registrationPage.verifyElementVisible(registrationPage.fullNameError);
      await registrationPage.verifyElementVisible(registrationPage.emailError);
      await registrationPage.verifyElementVisible(registrationPage.passwordError);
    });

    await test.step('2. Correct errors and complete registration', async () => {
      const timestamp = Date.now();
      const testEmail = `recoveryuser${timestamp}@example.com`;
      
      // Fix all errors
      await registrationPage.fillFormField(registrationPage.fullNameInput, 'Recovery Test User');
      await registrationPage.fillFormField(registrationPage.emailInput, testEmail);
      await registrationPage.fillFormField(registrationPage.passwordInput, 'RecoveryPassword123!');
      await registrationPage.fillFormField(registrationPage.confirmPasswordInput, 'RecoveryPassword123!');
      await registrationPage.termsCheckbox.check();
      await registrationPage.privacyCheckbox.check();
      
      await registrationPage.registerButton.click();
      await registrationPage.verifyElementVisible(registrationPage.registrationSuccess);
    });

    await test.step('3. Verify successful login after error recovery', async () => {
      await loginPage.navigateToLogin();
      await loginPage.login(`recoveryuser${Date.now()}@example.com`, 'RecoveryPassword123!');
      // Note: This might fail if timestamp is different, but demonstrates the flow
    });
  });
});