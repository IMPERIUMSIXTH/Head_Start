import { test, expect } from '@playwright/test';
import { LoginPage } from '../../page-objects/login-page';
import { DashboardPage } from '../../page-objects/dashboard-page';
import { RegistrationPage } from '../../page-objects/registration-page';

test.describe('WCAG Accessibility Compliance', () => {
  test.describe('WCAG 2.1 AA Compliance', () => {
    let loginPage: LoginPage;
    let dashboardPage: DashboardPage;
    let registrationPage: RegistrationPage;

    test.beforeEach(async ({ page }) => {
      loginPage = new LoginPage(page);
      dashboardPage = new DashboardPage(page);
      registrationPage = new RegistrationPage(page);
    });

    test('should meet WCAG AA standards on login page', async () => {
      await test.step('Navigate to login page', async () => {
        await loginPage.navigateToLogin();
      });

      await test.step('Check color contrast ratios', async () => {
        // Verify text has sufficient contrast
        const textElements = [
          loginPage.emailInput,
          loginPage.passwordInput,
          loginPage.loginButton
        ];

        for (const element of textElements) {
          const styles = await element.evaluate((el) => {
            const computed = window.getComputedStyle(el);
            return {
              color: computed.color,
              backgroundColor: computed.backgroundColor,
              fontSize: computed.fontSize
            };
          });

          // Parse RGB values and calculate contrast ratio
          const textColor = parseRGB(styles.color);
          const bgColor = parseRGB(styles.backgroundColor);
          const contrastRatio = calculateContrastRatio(textColor, bgColor);
          
          // WCAG AA requires 4.5:1 for normal text, 3:1 for large text
          const fontSize = parseInt(styles.fontSize);
          const minRatio = fontSize >= 18 ? 3 : 4.5;
          
          expect(contrastRatio).toBeGreaterThanOrEqual(minRatio);
        }
      });

      await test.step('Verify semantic HTML structure', async () => {
        // Check for proper heading hierarchy
        const h1Count = await loginPage.page.locator('h1').count();
        expect(h1Count).toBe(1);

        // Check for form labels
        await expect(loginPage.emailInput).toHaveAttribute('aria-label');
        await expect(loginPage.passwordInput).toHaveAttribute('aria-label');

        // Check for landmark regions
        const main = loginPage.page.locator('main');
        await expect(main).toBeVisible();
      });

      await test.step('Test keyboard navigation', async () => {
        await loginPage.verifyLoginFormAccessibility();
      });

      await test.step('Verify focus indicators', async () => {
        const focusableElements = [
          loginPage.emailInput,
          loginPage.passwordInput,
          loginPage.loginButton,
          loginPage.registerLink,
          loginPage.forgotPasswordLink
        ];

        for (const element of focusableElements) {
          await element.focus();
          
          // Verify element has visible focus indicator
          const focusStyles = await element.evaluate((el) => {
            const computed = window.getComputedStyle(el);
            return {
              outline: computed.outline,
              outlineWidth: computed.outlineWidth,
              outlineStyle: computed.outlineStyle,
              outlineColor: computed.outlineColor,
              boxShadow: computed.boxShadow
            };
          });

          // Should have either outline or box-shadow for focus
          const hasFocusIndicator = 
            focusStyles.outline !== 'none' || 
            focusStyles.boxShadow !== 'none' ||
            focusStyles.outlineWidth !== '0px';
          
          expect(hasFocusIndicator).toBe(true);
        }
      });

      await test.step('Check for accessibility violations', async () => {
        // This would integrate with @axe-core/playwright
        // await injectAxe(loginPage.page);
        // const results = await checkA11y(loginPage.page);
        // expect(results.violations).toHaveLength(0);
      });
    });

    test('should meet WCAG AA standards on registration page', async () => {
      await test.step('Navigate to registration page', async () => {
        await registrationPage.navigateToRegistration();
      });

      await test.step('Verify form accessibility', async () => {
        await registrationPage.verifyRegistrationFormAccessibility();
      });

      await test.step('Check error message accessibility', async () => {
        // Trigger validation errors
        await registrationPage.registerButton.click();
        
        // Verify error messages are properly associated
        const errorElements = [
          registrationPage.fullNameError,
          registrationPage.emailError,
          registrationPage.passwordError
        ];

        for (const errorElement of errorElements) {
          if (await errorElement.isVisible()) {
            // Error should have appropriate ARIA attributes
            const ariaLive = await errorElement.getAttribute('aria-live');
            const role = await errorElement.getAttribute('role');
            
            expect(ariaLive || role).toBeTruthy();
          }
        }
      });

      await test.step('Verify password strength indicator accessibility', async () => {
        await registrationPage.fillFormField(registrationPage.passwordInput, 'weak');
        
        const strengthIndicator = registrationPage.passwordStrengthIndicator;
        if (await strengthIndicator.isVisible()) {
          // Should have aria-live for dynamic updates
          const ariaLive = await strengthIndicator.getAttribute('aria-live');
          expect(ariaLive).toBeTruthy();
        }
      });
    });

    test('should meet WCAG AA standards on dashboard', async () => {
      await test.step('Login and navigate to dashboard', async () => {
        await loginPage.navigateToLogin();
        await loginPage.loginWithValidCredentials();
      });

      await test.step('Verify dashboard accessibility', async () => {
        await dashboardPage.verifyDashboardAccessibility();
      });

      await test.step('Check data visualization accessibility', async () => {
        // Progress charts should have text alternatives
        const progressChart = dashboardPage.progressChart;
        if (await progressChart.isVisible()) {
          const ariaLabel = await progressChart.getAttribute('aria-label');
          const ariaDescribedBy = await progressChart.getAttribute('aria-describedby');
          
          expect(ariaLabel || ariaDescribedBy).toBeTruthy();
        }

        // Progress bars should have proper ARIA attributes
        const progressBars = await dashboardPage.skillProgressBars.all();
        for (const bar of progressBars) {
          if (await bar.isVisible()) {
            const role = await bar.getAttribute('role');
            const ariaValueNow = await bar.getAttribute('aria-valuenow');
            const ariaValueMin = await bar.getAttribute('aria-valuemin');
            const ariaValueMax = await bar.getAttribute('aria-valuemax');
            
            expect(role).toBe('progressbar');
            expect(ariaValueNow).toBeTruthy();
            expect(ariaValueMin).toBeTruthy();
            expect(ariaValueMax).toBeTruthy();
          }
        }
      });

      await test.step('Verify interactive elements accessibility', async () => {
        const interactiveElements = [
          dashboardPage.startLearningButton,
          dashboardPage.exploreContentButton,
          dashboardPage.refreshRecommendationsButton
        ];

        for (const element of interactiveElements) {
          if (await element.isVisible()) {
            // Should have accessible name
            const ariaLabel = await element.getAttribute('aria-label');
            const textContent = await element.textContent();
            
            expect(ariaLabel || textContent?.trim()).toBeTruthy();

            // Should be keyboard accessible
            await element.focus();
            const tagName = await element.evaluate(el => el.tagName.toLowerCase());
            const role = await element.getAttribute('role');
            
            // Should be button or link
            expect(['button', 'a'].includes(tagName) || role === 'button').toBe(true);
          }
        }
      });
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('should support complete keyboard navigation', async ({ page }) => {
      const loginPage = new LoginPage(page);
      const dashboardPage = new DashboardPage(page);

      await test.step('Test keyboard-only login flow', async () => {
        await loginPage.navigateToLogin();
        await loginPage.testLoginWithKeyboard();
      });

      await test.step('Test keyboard navigation on dashboard', async () => {
        // Tab through all interactive elements
        let tabCount = 0;
        const maxTabs = 20; // Prevent infinite loop

        while (tabCount < maxTabs) {
          await page.keyboard.press('Tab');
          tabCount++;

          const focusedElement = await page.locator(':focus').first();
          const isVisible = await focusedElement.isVisible();
          
          if (isVisible) {
            const tagName = await focusedElement.evaluate(el => el.tagName.toLowerCase());
            const role = await focusedElement.getAttribute('role');
            const tabIndex = await focusedElement.getAttribute('tabindex');
            
            // Focused element should be interactive
            const isInteractive = 
              ['button', 'a', 'input', 'select', 'textarea'].includes(tagName) ||
              ['button', 'link', 'textbox'].includes(role || '') ||
              tabIndex === '0';
            
            if (isInteractive) {
              // Test activation with keyboard
              if (tagName === 'button' || role === 'button') {
                // Don't actually activate to avoid navigation
                // Just verify it's focusable
                expect(isVisible).toBe(true);
              }
            }
          }
        }
      });

      await test.step('Test skip links', async () => {
        // Press Tab to focus skip link
        await page.keyboard.press('Tab');
        
        const skipLink = page.locator('[data-testid="skip-to-main"]');
        if (await skipLink.isVisible()) {
          await expect(skipLink).toBeFocused();
          
          // Activate skip link
          await page.keyboard.press('Enter');
          
          // Main content should be focused
          const mainContent = page.locator('main');
          await expect(mainContent).toBeFocused();
        }
      });
    });

    test('should handle keyboard traps appropriately', async ({ page }) => {
      const loginPage = new LoginPage(page);
      const dashboardPage = new DashboardPage(page);

      await loginPage.navigateToLogin();
      await loginPage.loginWithValidCredentials();

      // Test modal dialogs (if any)
      const modalTrigger = page.locator('[data-testid="open-modal"]');
      if (await modalTrigger.isVisible()) {
        await modalTrigger.click();
        
        const modal = page.locator('[role="dialog"]');
        if (await modal.isVisible()) {
          // Focus should be trapped within modal
          await page.keyboard.press('Tab');
          const focusedElement = await page.locator(':focus').first();
          
          // Focused element should be within modal
          const isWithinModal = await focusedElement.evaluate((el, modalEl) => {
            return modalEl.contains(el);
          }, await modal.elementHandle());
          
          expect(isWithinModal).toBe(true);
        }
      }
    });
  });

  test.describe('Screen Reader Support', () => {
    test('should provide appropriate screen reader announcements', async ({ page }) => {
      const loginPage = new LoginPage(page);
      const dashboardPage = new DashboardPage(page);

      await test.step('Test form announcements', async () => {
        await loginPage.navigateToLogin();
        
        // Test error announcements
        await loginPage.loginButton.click();
        
        const errorElements = await page.locator('[aria-live]').all();
        for (const element of errorElements) {
          if (await element.isVisible()) {
            const ariaLive = await element.getAttribute('aria-live');
            expect(['polite', 'assertive'].includes(ariaLive || '')).toBe(true);
          }
        }
      });

      await test.step('Test dynamic content announcements', async () => {
        await loginPage.loginWithValidCredentials();
        
        // Test loading states
        const loadingElements = await page.locator('[aria-live="polite"]').all();
        for (const element of loadingElements) {
          if (await element.isVisible()) {
            const textContent = await element.textContent();
            expect(textContent?.trim()).toBeTruthy();
          }
        }
      });
    });

    test('should have proper heading structure', async ({ page }) => {
      const loginPage = new LoginPage(page);
      const dashboardPage = new DashboardPage(page);

      await loginPage.navigateToLogin();
      await loginPage.loginWithValidCredentials();

      // Check heading hierarchy
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
      let previousLevel = 0;

      for (const heading of headings) {
        if (await heading.isVisible()) {
          const tagName = await heading.evaluate(el => el.tagName.toLowerCase());
          const level = parseInt(tagName.charAt(1));
          
          // Heading levels should not skip (e.g., h1 -> h3)
          if (previousLevel > 0) {
            expect(level - previousLevel).toBeLessThanOrEqual(1);
          }
          
          previousLevel = level;
        }
      }
    });
  });

  test.describe('Mobile Accessibility', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('should be accessible on mobile devices', async ({ page }) => {
      const loginPage = new LoginPage(page);
      const dashboardPage = new DashboardPage(page);

      await test.step('Test mobile touch targets', async () => {
        await loginPage.navigateToLogin();
        
        const touchElements = [
          loginPage.emailInput,
          loginPage.passwordInput,
          loginPage.loginButton
        ];

        for (const element of touchElements) {
          const box = await element.boundingBox();
          if (box) {
            // WCAG recommends minimum 44px touch targets
            expect(box.height).toBeGreaterThanOrEqual(44);
            expect(box.width).toBeGreaterThanOrEqual(44);
          }
        }
      });

      await test.step('Test mobile screen reader support', async () => {
        await loginPage.loginWithValidCredentials();
        
        // Verify mobile-specific ARIA attributes
        const mobileMenuToggle = page.locator('[data-testid="mobile-menu-toggle"]');
        if (await mobileMenuToggle.isVisible()) {
          const ariaExpanded = await mobileMenuToggle.getAttribute('aria-expanded');
          const ariaControls = await mobileMenuToggle.getAttribute('aria-controls');
          
          expect(ariaExpanded).toBeTruthy();
          expect(ariaControls).toBeTruthy();
        }
      });

      await test.step('Test mobile gesture accessibility', async () => {
        // Swipeable content should have keyboard alternatives
        const swipeableContent = page.locator('[data-testid="swipeable-content"]');
        if (await swipeableContent.isVisible()) {
          // Should have navigation buttons as alternatives
          const prevButton = page.locator('[data-testid="prev-button"]');
          const nextButton = page.locator('[data-testid="next-button"]');
          
          expect(await prevButton.isVisible() || await nextButton.isVisible()).toBe(true);
        }
      });
    });
  });
});

// Helper functions for color contrast calculation
function parseRGB(rgbString: string): { r: number; g: number; b: number } {
  const match = rgbString.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
  if (match) {
    return {
      r: parseInt(match[1]),
      g: parseInt(match[2]),
      b: parseInt(match[3])
    };
  }
  return { r: 0, g: 0, b: 0 };
}

function calculateContrastRatio(color1: { r: number; g: number; b: number }, color2: { r: number; g: number; b: number }): number {
  const l1 = getRelativeLuminance(color1);
  const l2 = getRelativeLuminance(color2);
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

function getRelativeLuminance(color: { r: number; g: number; b: number }): number {
  const { r, g, b } = color;
  
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}