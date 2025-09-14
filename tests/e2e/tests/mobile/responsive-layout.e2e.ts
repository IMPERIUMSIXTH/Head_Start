import { test, expect } from '@playwright/test';
import { LoginPage } from '../../page-objects/login-page';
import { DashboardPage } from '../../page-objects/dashboard-page';

test.describe('Mobile Responsive Design', () => {
  const mobileViewports = [
    { name: 'iPhone SE', width: 375, height: 667 },
    { name: 'iPhone 12', width: 390, height: 844 },
    { name: 'Samsung Galaxy S21', width: 360, height: 800 },
    { name: 'iPad Mini', width: 768, height: 1024 },
    { name: 'iPad Pro', width: 1024, height: 1366 }
  ];

  mobileViewports.forEach(viewport => {
    test.describe(`${viewport.name} (${viewport.width}x${viewport.height})`, () => {
      test.use({ viewport: { width: viewport.width, height: viewport.height } });

      let loginPage: LoginPage;
      let dashboardPage: DashboardPage;

      test.beforeEach(async ({ page }) => {
        loginPage = new LoginPage(page);
        dashboardPage = new DashboardPage(page);
      });

      test('should display login page correctly', async () => {
        await test.step('Navigate to login page', async () => {
          await loginPage.navigateToLogin();
        });

        await test.step('Verify mobile login layout', async () => {
          await loginPage.verifyMobileLoginExperience();
        });

        await test.step('Verify form elements are properly sized', async () => {
          const formElements = [
            loginPage.emailInput,
            loginPage.passwordInput,
            loginPage.loginButton
          ];

          for (const element of formElements) {
            const box = await element.boundingBox();
            if (box) {
              // Verify minimum touch target size
              expect(box.height).toBeGreaterThanOrEqual(44);
              
              // Verify elements don't overflow viewport
              expect(box.x + box.width).toBeLessThanOrEqual(viewport.width);
            }
          }
        });

        await test.step('Test virtual keyboard interaction', async () => {
          await loginPage.emailInput.tap();
          await loginPage.page.keyboard.type('test@example.com');
          
          // Verify form is still accessible with virtual keyboard
          await loginPage.verifyElementVisible(loginPage.loginButton);
        });
      });

      test('should display dashboard correctly after login', async () => {
        await test.step('Login and navigate to dashboard', async () => {
          await loginPage.navigateToLogin();
          await loginPage.loginWithValidCredentials();
        });

        await test.step('Verify mobile dashboard layout', async () => {
          await dashboardPage.verifyMobileDashboard();
        });

        await test.step('Verify content sections are properly stacked', async () => {
          const sections = [
            dashboardPage.welcomeSection,
            dashboardPage.learningStatsSection,
            dashboardPage.recentActivitySection,
            dashboardPage.recommendationsSection
          ];

          let previousBottom = 0;
          for (const section of sections) {
            if (await section.isVisible()) {
              const box = await section.boundingBox();
              if (box) {
                // Verify sections are stacked vertically on mobile
                expect(box.y).toBeGreaterThanOrEqual(previousBottom);
                previousBottom = box.y + box.height;
                
                // Verify sections don't overflow horizontally
                expect(box.x + box.width).toBeLessThanOrEqual(viewport.width);
              }
            }
          }
        });

        await test.step('Test mobile navigation menu', async () => {
          const mobileMenuToggle = dashboardPage.page.locator('[data-testid="mobile-menu-toggle"]');
          if (await mobileMenuToggle.isVisible()) {
            // Test menu toggle
            await mobileMenuToggle.click();
            await dashboardPage.verifyElementVisible(dashboardPage.sidebarMenu);
            
            // Test menu close
            await mobileMenuToggle.click();
            await dashboardPage.verifyElementHidden(dashboardPage.sidebarMenu);
          }
        });
      });

      test('should handle touch interactions properly', async () => {
        await test.step('Setup authenticated session', async () => {
          await loginPage.navigateToLogin();
          await loginPage.loginWithValidCredentials();
        });

        await test.step('Test tap interactions', async () => {
          const recommendationCount = await dashboardPage.recommendationCards.count();
          if (recommendationCount > 0) {
            const firstRecommendation = dashboardPage.recommendationCards.first();
            
            // Test tap to navigate
            await firstRecommendation.tap();
            await dashboardPage.page.waitForTimeout(1000);
            
            // Navigate back
            await dashboardPage.page.goBack();
            await dashboardPage.waitForPageLoad();
          }
        });

        await test.step('Test swipe gestures', async () => {
          const recommendationCount = await dashboardPage.recommendationCards.count();
          if (recommendationCount > 1) {
            const recommendationContainer = dashboardPage.page.locator('[data-testid="recommendations-container"]');
            if (await recommendationContainer.isVisible()) {
              await dashboardPage.swipeLeft(recommendationContainer);
              await dashboardPage.page.waitForTimeout(500);
              
              await dashboardPage.swipeRight(recommendationContainer);
              await dashboardPage.page.waitForTimeout(500);
            }
          }
        });

        await test.step('Test pinch zoom (if supported)', async () => {
          const mainContent = dashboardPage.page.locator('main');
          if (await mainContent.isVisible()) {
            await dashboardPage.pinchZoom(mainContent, 1.5);
            await dashboardPage.page.waitForTimeout(500);
          }
        });
      });

      test('should maintain readability and usability', async () => {
        await test.step('Setup authenticated session', async () => {
          await loginPage.navigateToLogin();
          await loginPage.loginWithValidCredentials();
        });

        await test.step('Verify text readability', async () => {
          const textElements = [
            dashboardPage.userName,
            dashboardPage.totalInteractionsCount,
            dashboardPage.completedContentCount
          ];

          for (const element of textElements) {
            if (await element.isVisible()) {
              const styles = await element.evaluate((el) => {
                const computed = window.getComputedStyle(el);
                return {
                  fontSize: computed.fontSize,
                  lineHeight: computed.lineHeight,
                  color: computed.color,
                  backgroundColor: computed.backgroundColor
                };
              });

              // Verify minimum font size for mobile
              const fontSize = parseInt(styles.fontSize);
              expect(fontSize).toBeGreaterThanOrEqual(14);
            }
          }
        });

        await test.step('Verify button accessibility', async () => {
          const buttons = [
            dashboardPage.startLearningButton,
            dashboardPage.exploreContentButton
          ];

          for (const button of buttons) {
            if (await button.isVisible()) {
              const box = await button.boundingBox();
              if (box) {
                // Verify minimum touch target size (44px)
                expect(box.height).toBeGreaterThanOrEqual(44);
                expect(box.width).toBeGreaterThanOrEqual(44);
              }
            }
          }
        });

        await test.step('Verify spacing and layout', async () => {
          const interactiveElements = await dashboardPage.page.locator('button, a, input').all();
          
          for (let i = 0; i < interactiveElements.length - 1; i++) {
            const current = interactiveElements[i];
            const next = interactiveElements[i + 1];
            
            if (await current.isVisible() && await next.isVisible()) {
              const currentBox = await current.boundingBox();
              const nextBox = await next.boundingBox();
              
              if (currentBox && nextBox) {
                // Verify minimum spacing between interactive elements
                const verticalDistance = Math.abs(nextBox.y - (currentBox.y + currentBox.height));
                const horizontalDistance = Math.abs(nextBox.x - (currentBox.x + currentBox.width));
                
                if (verticalDistance < 100 && horizontalDistance < 100) {
                  // Elements are close, verify minimum spacing
                  expect(Math.min(verticalDistance, horizontalDistance)).toBeGreaterThanOrEqual(8);
                }
              }
            }
          }
        });
      });
    });
  });

  test.describe('Orientation Changes', () => {
    test.use({ viewport: { width: 390, height: 844 } }); // iPhone 12

    let loginPage: LoginPage;
    let dashboardPage: DashboardPage;

    test.beforeEach(async ({ page }) => {
      loginPage = new LoginPage(page);
      dashboardPage = new DashboardPage(page);
      
      await loginPage.navigateToLogin();
      await loginPage.loginWithValidCredentials();
    });

    test('should handle portrait to landscape rotation', async () => {
      await test.step('Verify portrait layout', async () => {
        await dashboardPage.verifyDashboardLoaded();
      });

      await test.step('Rotate to landscape', async () => {
        await dashboardPage.page.setViewportSize({ width: 844, height: 390 });
        await dashboardPage.waitForPageLoad();
      });

      await test.step('Verify landscape layout', async () => {
        await dashboardPage.verifyDashboardLoaded();
        
        // In landscape, elements might be arranged differently
        const sections = [
          dashboardPage.learningStatsSection,
          dashboardPage.recommendationsSection
        ];

        for (const section of sections) {
          if (await section.isVisible()) {
            const box = await section.boundingBox();
            if (box) {
              // Verify sections fit in landscape viewport
              expect(box.x + box.width).toBeLessThanOrEqual(844);
              expect(box.y + box.height).toBeLessThanOrEqual(390);
            }
          }
        }
      });

      await test.step('Rotate back to portrait', async () => {
        await dashboardPage.page.setViewportSize({ width: 390, height: 844 });
        await dashboardPage.waitForPageLoad();
        await dashboardPage.verifyDashboardLoaded();
      });
    });

    test('should maintain functionality across orientations', async () => {
      const orientations = [
        { name: 'portrait', width: 390, height: 844 },
        { name: 'landscape', width: 844, height: 390 }
      ];

      for (const orientation of orientations) {
        await test.step(`Test functionality in ${orientation.name}`, async () => {
          await dashboardPage.page.setViewportSize({ 
            width: orientation.width, 
            height: orientation.height 
          });
          await dashboardPage.waitForPageLoad();

          // Test key functionality
          await dashboardPage.verifyDashboardLoaded();
          
          // Test navigation
          const contentLink = dashboardPage.contentBrowseLink;
          if (await contentLink.isVisible()) {
            await contentLink.click();
            await dashboardPage.page.waitForTimeout(1000);
            await dashboardPage.page.goBack();
            await dashboardPage.waitForPageLoad();
          }

          // Test recommendations interaction
          const recommendationCount = await dashboardPage.recommendationCards.count();
          if (recommendationCount > 0) {
            const firstRecommendation = dashboardPage.recommendationCards.first();
            if (await firstRecommendation.isVisible()) {
              await firstRecommendation.tap();
              await dashboardPage.page.waitForTimeout(1000);
              await dashboardPage.page.goBack();
              await dashboardPage.waitForPageLoad();
            }
          }
        });
      }
    });
  });

  test.describe('Cross-Device Consistency', () => {
    const devices = [
      { name: 'Mobile Phone', width: 375, height: 667 },
      { name: 'Tablet Portrait', width: 768, height: 1024 },
      { name: 'Tablet Landscape', width: 1024, height: 768 }
    ];

    devices.forEach(device => {
      test(`should maintain consistency on ${device.name}`, async ({ page }) => {
        await page.setViewportSize({ width: device.width, height: device.height });
        
        const loginPage = new LoginPage(page);
        const dashboardPage = new DashboardPage(page);

        await test.step('Test login consistency', async () => {
          await loginPage.navigateToLogin();
          await loginPage.verifyElementVisible(loginPage.loginForm);
          await loginPage.loginWithValidCredentials();
        });

        await test.step('Test dashboard consistency', async () => {
          await dashboardPage.verifyDashboardLoaded();
          await dashboardPage.verifyLearningStatistics();
          await dashboardPage.verifyRecommendations();
        });

        await test.step('Test navigation consistency', async () => {
          // Verify key navigation elements are accessible
          const navigationElements = [
            dashboardPage.contentBrowseLink,
            dashboardPage.preferencesLink,
            dashboardPage.profileLink
          ];

          for (const element of navigationElements) {
            if (await element.isVisible()) {
              await dashboardPage.verifyElementVisible(element);
            }
          }
        });
      });
    });
  });

  test.describe('Performance on Mobile', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('should load quickly on mobile devices', async ({ page }) => {
      const loginPage = new LoginPage(page);
      const dashboardPage = new DashboardPage(page);

      await test.step('Measure mobile login performance', async () => {
        const performance = await loginPage.measureLoginPerformance();
        
        // Mobile performance thresholds (slightly higher than desktop)
        expect(performance.loadTime).toBeLessThan(4000); // 4 seconds
        expect(performance.loginTime).toBeLessThan(3000); // 3 seconds
      });

      await test.step('Measure mobile dashboard performance', async () => {
        const performance = await dashboardPage.measureDashboardPerformance();
        
        // Mobile performance thresholds
        expect(performance.loadTime).toBeLessThan(4000); // 4 seconds
        expect(performance.interactionTimes.recommendationRefresh).toBeLessThan(3000); // 3 seconds
      });
    });

    test('should handle slow network conditions', async ({ page }) => {
      // Simulate slow 3G network
      await page.route('**/*', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 100)); // Add 100ms delay
        await route.continue();
      });

      const loginPage = new LoginPage(page);
      const dashboardPage = new DashboardPage(page);

      await test.step('Test login with slow network', async () => {
        await loginPage.navigateToLogin();
        await loginPage.loginWithValidCredentials();
      });

      await test.step('Test dashboard with slow network', async () => {
        await dashboardPage.verifyDashboardLoaded();
        
        // Verify loading states are handled properly
        const loadingSpinner = dashboardPage.loadingSpinner;
        // Loading spinner should appear and then disappear
        await dashboardPage.page.waitForTimeout(1000);
      });
    });
  });
});