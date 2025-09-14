import { test, expect } from '@playwright/test';
import { LoginPage } from '../../page-objects/login-page';
import { DashboardPage } from '../../page-objects/dashboard-page';

test.describe('User Dashboard', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    
    // Login before each test
    await loginPage.navigateToLogin();
    await loginPage.loginWithValidCredentials();
  });

  test('should display dashboard correctly after login', async () => {
    await test.step('Verify dashboard loads properly', async () => {
      await dashboardPage.verifyDashboardLoaded();
    });

    await test.step('Verify user information is displayed', async () => {
      await dashboardPage.verifyUserInformation('Test User', 'learner');
    });

    await test.step('Verify all dashboard sections are present', async () => {
      await dashboardPage.verifyElementVisible(dashboardPage.welcomeSection);
      await dashboardPage.verifyElementVisible(dashboardPage.learningStatsSection);
      await dashboardPage.verifyElementVisible(dashboardPage.recentActivitySection);
      await dashboardPage.verifyElementVisible(dashboardPage.recommendationsSection);
      await dashboardPage.verifyElementVisible(dashboardPage.progressSection);
    });
  });

  test('should display learning statistics correctly', async () => {
    await test.step('Verify learning statistics are shown', async () => {
      await dashboardPage.verifyLearningStatistics();
    });

    await test.step('Verify statistics contain valid data', async () => {
      // Check that statistics show reasonable values
      const interactionsText = await dashboardPage.totalInteractionsCount.textContent();
      const completedText = await dashboardPage.completedContentCount.textContent();
      
      expect(interactionsText).toMatch(/^\d+$/);
      expect(completedText).toMatch(/^\d+$/);
    });
  });

  test('should display recent activity', async () => {
    await test.step('Verify recent activity section', async () => {
      await dashboardPage.verifyRecentActivity();
    });

    await test.step('Test view all activity functionality', async () => {
      const viewAllButton = dashboardPage.viewAllActivityButton;
      if (await viewAllButton.isVisible()) {
        await dashboardPage.clickAndWaitForNavigation(viewAllButton, '**/activity');
        await dashboardPage.page.goBack();
        await dashboardPage.waitForPageLoad();
      }
    });
  });

  test('should display and interact with recommendations', async () => {
    await test.step('Verify recommendations are displayed', async () => {
      await dashboardPage.verifyRecommendations();
    });

    await test.step('Test recommendation interaction', async () => {
      const recommendationCount = await dashboardPage.recommendationCards.count();
      if (recommendationCount > 0) {
        await dashboardPage.clickRecommendation(0);
        await dashboardPage.page.goBack();
        await dashboardPage.waitForPageLoad();
      }
    });

    await test.step('Test refresh recommendations', async () => {
      await dashboardPage.refreshRecommendations();
    });

    await test.step('Test view all recommendations', async () => {
      const viewAllButton = dashboardPage.viewAllRecommendationsButton;
      if (await viewAllButton.isVisible()) {
        await dashboardPage.clickAndWaitForNavigation(viewAllButton, '**/recommendations');
        await dashboardPage.page.goBack();
        await dashboardPage.waitForPageLoad();
      }
    });
  });

  test('should display progress tracking', async () => {
    await test.step('Verify progress tracking elements', async () => {
      await dashboardPage.verifyProgressTracking();
    });

    await test.step('Verify progress data is meaningful', async () => {
      const skillBarsCount = await dashboardPage.skillProgressBars.count();
      
      if (skillBarsCount > 0) {
        const firstSkillBar = dashboardPage.skillProgressBars.first();
        const progressValue = await firstSkillBar.getAttribute('aria-valuenow');
        
        if (progressValue) {
          const value = parseInt(progressValue);
          expect(value).toBeGreaterThanOrEqual(0);
          expect(value).toBeLessThanOrEqual(100);
        }
      }
    });
  });

  test('should provide working navigation', async () => {
    await test.step('Test navigation to content browse', async () => {
      await dashboardPage.navigateToContentBrowse();
      await dashboardPage.verifyUrl(/.*\/content/);
      await dashboardPage.page.goBack();
      await dashboardPage.waitForPageLoad();
    });

    await test.step('Test navigation to preferences', async () => {
      await dashboardPage.navigateToPreferences();
      await dashboardPage.verifyUrl(/.*\/preferences/);
      await dashboardPage.page.goBack();
      await dashboardPage.waitForPageLoad();
    });

    await test.step('Test navigation to profile', async () => {
      await dashboardPage.navigateToProfile();
      await dashboardPage.verifyUrl(/.*\/profile/);
      await dashboardPage.page.goBack();
      await dashboardPage.waitForPageLoad();
    });
  });

  test('should provide quick actions', async () => {
    await test.step('Verify quick actions are available', async () => {
      await dashboardPage.verifyQuickActions();
    });

    await test.step('Test start learning action', async () => {
      await dashboardPage.startLearningSession();
    });

    await test.step('Test explore content action', async () => {
      await dashboardPage.exploreContent();
      await dashboardPage.verifyUrl(/.*\/content/);
      await dashboardPage.page.goBack();
      await dashboardPage.waitForPageLoad();
    });
  });

  test('should handle data refresh correctly', async () => {
    await test.step('Test dashboard data refresh', async () => {
      await dashboardPage.verifyDataRefresh();
    });
  });

  test('should handle errors gracefully', async () => {
    await test.step('Verify error handling', async () => {
      await dashboardPage.verifyErrorHandling();
    });
  });

  test.describe('Dashboard Accessibility', () => {
    test('should be accessible with keyboard navigation', async () => {
      await test.step('Test accessibility features', async () => {
        await dashboardPage.verifyDashboardAccessibility();
      });
    });

    test('should have proper ARIA labels and roles', async () => {
      await test.step('Verify ARIA attributes', async () => {
        await dashboardPage.checkAccessibility();
      });
    });

    test('should support screen readers', async () => {
      await test.step('Verify screen reader support', async () => {
        // Verify heading structure
        const h1Count = await dashboardPage.page.locator('h1').count();
        expect(h1Count).toBe(1);

        // Verify landmark regions
        await dashboardPage.verifyElementVisible(
          dashboardPage.page.locator('main[role="main"]')
        );
        await dashboardPage.verifyElementVisible(
          dashboardPage.page.locator('nav[role="navigation"]')
        );
      });
    });
  });

  test.describe('Dashboard Performance', () => {
    test('should load within acceptable time limits', async () => {
      await test.step('Measure dashboard performance', async () => {
        const performance = await dashboardPage.measureDashboardPerformance();
        
        // Assert performance thresholds
        expect(performance.loadTime).toBeLessThan(3000); // 3 seconds
        expect(performance.interactionTimes.recommendationRefresh).toBeLessThan(2000); // 2 seconds
        expect(performance.interactionTimes.contentNavigation).toBeLessThan(1500); // 1.5 seconds
      });
    });

    test('should handle concurrent data loading', async () => {
      await test.step('Test concurrent API calls', async () => {
        // Refresh page to trigger all API calls simultaneously
        await dashboardPage.page.reload();
        await dashboardPage.waitForPageLoad();
        
        // Verify all sections load correctly
        await dashboardPage.verifyDashboardLoaded();
        await dashboardPage.verifyLearningStatistics();
        await dashboardPage.verifyRecentActivity();
        await dashboardPage.verifyRecommendations();
      });
    });
  });

  test.describe('Dashboard User Interaction', () => {
    test('should support complete user workflow', async () => {
      await test.step('Simulate typical user session', async () => {
        await dashboardPage.simulateUserInteraction();
      });
    });

    test('should maintain state during navigation', async () => {
      await test.step('Test state persistence', async () => {
        // Navigate away and back
        await dashboardPage.navigateToContentBrowse();
        await dashboardPage.page.goBack();
        await dashboardPage.waitForPageLoad();
        
        // Verify dashboard state is maintained
        await dashboardPage.verifyDashboardLoaded();
      });
    });
  });
});

test.describe('Dashboard - Mobile Experience', () => {
  test.use({ 
    viewport: { width: 375, height: 667 } // iPhone SE dimensions
  });

  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    
    await loginPage.navigateToLogin();
    await loginPage.loginWithValidCredentials();
  });

  test('should work correctly on mobile devices', async () => {
    await test.step('Verify mobile dashboard layout', async () => {
      await dashboardPage.verifyMobileDashboard();
    });

    await test.step('Test mobile navigation', async () => {
      // Test mobile menu if present
      const mobileMenuToggle = dashboardPage.page.locator('[data-testid="mobile-menu-toggle"]');
      if (await mobileMenuToggle.isVisible()) {
        await mobileMenuToggle.click();
        await dashboardPage.verifyElementVisible(dashboardPage.sidebarMenu);
        await mobileMenuToggle.click();
      }
    });

    await test.step('Test touch interactions', async () => {
      // Test swipe gestures on recommendation cards
      const recommendationCount = await dashboardPage.recommendationCards.count();
      if (recommendationCount > 0) {
        const firstRecommendation = dashboardPage.recommendationCards.first();
        await dashboardPage.swipeLeft(firstRecommendation);
        await dashboardPage.page.waitForTimeout(500);
      }
    });
  });

  test('should have touch-friendly elements', async () => {
    await test.step('Verify touch target sizes', async () => {
      const touchElements = [
        dashboardPage.startLearningButton,
        dashboardPage.exploreContentButton,
        dashboardPage.refreshRecommendationsButton
      ];

      for (const element of touchElements) {
        if (await element.isVisible()) {
          const box = await element.boundingBox();
          if (box) {
            // Verify minimum touch target size (44px)
            expect(box.height).toBeGreaterThanOrEqual(44);
            expect(box.width).toBeGreaterThanOrEqual(44);
          }
        }
      }
    });
  });

  test('should handle orientation changes', async () => {
    await test.step('Test landscape orientation', async () => {
      // Rotate to landscape
      await dashboardPage.page.setViewportSize({ width: 667, height: 375 });
      await dashboardPage.waitForPageLoad();
      
      // Verify dashboard still works
      await dashboardPage.verifyDashboardLoaded();
      
      // Rotate back to portrait
      await dashboardPage.page.setViewportSize({ width: 375, height: 667 });
      await dashboardPage.waitForPageLoad();
      
      await dashboardPage.verifyDashboardLoaded();
    });
  });
});

test.describe('Dashboard - Admin User', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    
    // Login as admin user
    await loginPage.navigateToLogin();
    await loginPage.loginAsAdmin();
  });

  test('should display admin-specific features', async () => {
    await test.step('Verify admin dashboard elements', async () => {
      await dashboardPage.verifyUserInformation('Admin User', 'admin');
    });

    await test.step('Verify admin navigation options', async () => {
      // Admin users might have additional navigation options
      const adminPanel = dashboardPage.page.locator('[data-testid="admin-panel-link"]');
      if (await adminPanel.isVisible()) {
        await dashboardPage.verifyElementVisible(adminPanel);
      }
    });
  });

  test('should have access to admin analytics', async () => {
    await test.step('Test admin analytics access', async () => {
      const analyticsSection = dashboardPage.page.locator('[data-testid="admin-analytics"]');
      if (await analyticsSection.isVisible()) {
        await dashboardPage.verifyElementVisible(analyticsSection);
      }
    });
  });
});