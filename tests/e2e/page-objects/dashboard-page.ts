import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * Dashboard Page Object Model
 * Handles user dashboard interactions and analytics
 */
export class DashboardPage extends BasePage {
  // Main dashboard sections
  get welcomeSection(): Locator {
    return this.page.locator('[data-testid="welcome-section"]');
  }

  get learningStatsSection(): Locator {
    return this.page.locator('[data-testid="learning-stats-section"]');
  }

  get recentActivitySection(): Locator {
    return this.page.locator('[data-testid="recent-activity-section"]');
  }

  get recommendationsSection(): Locator {
    return this.page.locator('[data-testid="recommendations-section"]');
  }

  get progressSection(): Locator {
    return this.page.locator('[data-testid="progress-section"]');
  }

  // User profile elements
  get userAvatar(): Locator {
    return this.page.locator('[data-testid="user-avatar"]');
  }

  get userName(): Locator {
    return this.page.locator('[data-testid="user-name"]');
  }

  get userRole(): Locator {
    return this.page.locator('[data-testid="user-role"]');
  }

  // Learning statistics
  get totalInteractionsCount(): Locator {
    return this.page.locator('[data-testid="total-interactions-count"]');
  }

  get completedContentCount(): Locator {
    return this.page.locator('[data-testid="completed-content-count"]');
  }

  get totalTimeSpent(): Locator {
    return this.page.locator('[data-testid="total-time-spent"]');
  }

  get learningStreak(): Locator {
    return this.page.locator('[data-testid="learning-streak"]');
  }

  get completionRate(): Locator {
    return this.page.locator('[data-testid="completion-rate"]');
  }

  // Recent activity
  get activityList(): Locator {
    return this.page.locator('[data-testid="activity-list"]');
  }

  get activityItems(): Locator {
    return this.page.locator('[data-testid="activity-item"]');
  }

  get viewAllActivityButton(): Locator {
    return this.page.locator('[data-testid="view-all-activity-button"]');
  }

  // Recommendations
  get recommendationCards(): Locator {
    return this.page.locator('[data-testid="recommendation-card"]');
  }

  get viewAllRecommendationsButton(): Locator {
    return this.page.locator('[data-testid="view-all-recommendations-button"]');
  }

  get refreshRecommendationsButton(): Locator {
    return this.page.locator('[data-testid="refresh-recommendations-button"]');
  }

  // Progress tracking
  get progressChart(): Locator {
    return this.page.locator('[data-testid="progress-chart"]');
  }

  get skillProgressBars(): Locator {
    return this.page.locator('[data-testid="skill-progress-bar"]');
  }

  get weeklyGoalProgress(): Locator {
    return this.page.locator('[data-testid="weekly-goal-progress"]');
  }

  // Navigation elements
  get sidebarMenu(): Locator {
    return this.page.locator('[data-testid="sidebar-menu"]');
  }

  get contentBrowseLink(): Locator {
    return this.page.locator('[data-testid="content-browse-link"]');
  }

  get preferencesLink(): Locator {
    return this.page.locator('[data-testid="preferences-link"]');
  }

  get profileLink(): Locator {
    return this.page.locator('[data-testid="profile-link"]');
  }

  // Quick actions
  get quickActionButtons(): Locator {
    return this.page.locator('[data-testid="quick-action-button"]');
  }

  get startLearningButton(): Locator {
    return this.page.locator('[data-testid="start-learning-button"]');
  }

  get exploreContentButton(): Locator {
    return this.page.locator('[data-testid="explore-content-button"]');
  }

  // Page actions
  async navigateToDashboard(): Promise<void> {
    await this.navigateTo('/dashboard');
    await this.verifyPageTitle('Dashboard - HeadStart');
    await this.verifyElementVisible(this.welcomeSection);
  }

  async verifyDashboardLoaded(): Promise<void> {
    await this.verifyElementVisible(this.welcomeSection);
    await this.verifyElementVisible(this.learningStatsSection);
    await this.verifyElementVisible(this.recentActivitySection);
    await this.verifyElementVisible(this.recommendationsSection);
  }

  async verifyUserInformation(expectedName: string, expectedRole: string): Promise<void> {
    await this.verifyElementText(this.userName, expectedName);
    await this.verifyElementText(this.userRole, expectedRole);
    await this.verifyElementVisible(this.userAvatar);
  }

  async verifyLearningStatistics(): Promise<void> {
    // Verify all statistics are displayed and contain numeric values
    await this.verifyElementVisible(this.totalInteractionsCount);
    await this.verifyElementVisible(this.completedContentCount);
    await this.verifyElementVisible(this.totalTimeSpent);
    await this.verifyElementVisible(this.learningStreak);
    await this.verifyElementVisible(this.completionRate);

    // Verify statistics contain valid numbers
    const interactionsText = await this.totalInteractionsCount.textContent();
    const completedText = await this.completedContentCount.textContent();
    const timeText = await this.totalTimeSpent.textContent();
    
    expect(interactionsText).toMatch(/\d+/);
    expect(completedText).toMatch(/\d+/);
    expect(timeText).toMatch(/\d+/);
  }

  async verifyRecentActivity(): Promise<void> {
    await this.verifyElementVisible(this.activityList);
    
    const activityCount = await this.activityItems.count();
    expect(activityCount).toBeGreaterThanOrEqual(0);
    
    if (activityCount > 0) {
      // Verify first activity item structure
      const firstActivity = this.activityItems.first();
      await this.verifyElementVisible(firstActivity);
      
      // Verify activity item contains expected elements
      const contentTitle = firstActivity.locator('[data-testid="activity-content-title"]');
      const activityType = firstActivity.locator('[data-testid="activity-type"]');
      const activityDate = firstActivity.locator('[data-testid="activity-date"]');
      
      await this.verifyElementVisible(contentTitle);
      await this.verifyElementVisible(activityType);
      await this.verifyElementVisible(activityDate);
    }
  }

  async verifyRecommendations(): Promise<void> {
    await this.verifyElementVisible(this.recommendationsSection);
    
    const recommendationCount = await this.recommendationCards.count();
    expect(recommendationCount).toBeGreaterThanOrEqual(0);
    
    if (recommendationCount > 0) {
      // Verify first recommendation card structure
      const firstRecommendation = this.recommendationCards.first();
      await this.verifyElementVisible(firstRecommendation);
      
      // Verify recommendation card contains expected elements
      const title = firstRecommendation.locator('[data-testid="recommendation-title"]');
      const description = firstRecommendation.locator('[data-testid="recommendation-description"]');
      const difficulty = firstRecommendation.locator('[data-testid="recommendation-difficulty"]');
      const duration = firstRecommendation.locator('[data-testid="recommendation-duration"]');
      
      await this.verifyElementVisible(title);
      await this.verifyElementVisible(description);
      await this.verifyElementVisible(difficulty);
      await this.verifyElementVisible(duration);
    }
  }

  async clickRecommendation(index: number = 0): Promise<void> {
    const recommendation = this.recommendationCards.nth(index);
    await this.clickAndWaitForNavigation(recommendation, '**/content/**');
  }

  async refreshRecommendations(): Promise<void> {
    await this.refreshRecommendationsButton.click();
    await this.waitForApiResponse('**/api/recommendations/**');
    await this.verifyElementVisible(this.recommendationsSection);
  }

  async navigateToContentBrowse(): Promise<void> {
    await this.clickAndWaitForNavigation(this.contentBrowseLink, '**/content');
  }

  async navigateToPreferences(): Promise<void> {
    await this.clickAndWaitForNavigation(this.preferencesLink, '**/preferences');
  }

  async navigateToProfile(): Promise<void> {
    await this.clickAndWaitForNavigation(this.profileLink, '**/profile');
  }

  async startLearningSession(): Promise<void> {
    await this.startLearningButton.click();
    // This might navigate to content selection or start a recommended item
    await this.page.waitForTimeout(1000);
  }

  async exploreContent(): Promise<void> {
    await this.clickAndWaitForNavigation(this.exploreContentButton, '**/content');
  }

  async verifyProgressTracking(): Promise<void> {
    await this.verifyElementVisible(this.progressSection);
    
    // Verify progress chart is displayed
    await this.verifyElementVisible(this.progressChart);
    
    // Verify skill progress bars
    const skillBarsCount = await this.skillProgressBars.count();
    if (skillBarsCount > 0) {
      const firstSkillBar = this.skillProgressBars.first();
      await this.verifyElementVisible(firstSkillBar);
      
      // Verify progress bar has valid percentage
      const progressValue = await firstSkillBar.getAttribute('aria-valuenow');
      if (progressValue) {
        const value = parseInt(progressValue);
        expect(value).toBeGreaterThanOrEqual(0);
        expect(value).toBeLessThanOrEqual(100);
      }
    }
    
    // Verify weekly goal progress
    await this.verifyElementVisible(this.weeklyGoalProgress);
  }

  async verifyQuickActions(): Promise<void> {
    const quickActionsCount = await this.quickActionButtons.count();
    expect(quickActionsCount).toBeGreaterThan(0);
    
    // Verify common quick actions are present
    await this.verifyElementVisible(this.startLearningButton);
    await this.verifyElementVisible(this.exploreContentButton);
  }

  async verifyMobileDashboard(): Promise<void> {
    if (await this.isMobile()) {
      // Verify mobile-specific layout
      const sidebar = this.sidebarMenu;
      
      // On mobile, sidebar might be collapsed by default
      const sidebarVisible = await sidebar.isVisible();
      
      if (!sidebarVisible) {
        // Look for mobile menu toggle
        const menuToggle = this.page.locator('[data-testid="mobile-menu-toggle"]');
        await this.verifyElementVisible(menuToggle);
        
        // Test mobile menu functionality
        await menuToggle.click();
        await this.verifyElementVisible(sidebar);
        
        // Close menu
        await menuToggle.click();
        await this.verifyElementHidden(sidebar);
      }
      
      // Verify touch-friendly elements
      const touchElements = [
        this.recommendationCards.first(),
        this.startLearningButton,
        this.exploreContentButton
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
    }
  }

  async verifyDashboardAccessibility(): Promise<void> {
    // Verify heading hierarchy
    const h1 = this.page.locator('h1');
    await expect(h1).toHaveCount(1);
    
    // Verify ARIA landmarks
    const main = this.page.locator('main[role="main"]');
    await this.verifyElementVisible(main);
    
    const navigation = this.page.locator('nav[role="navigation"]');
    await this.verifyElementVisible(navigation);
    
    // Verify skip links
    const skipLink = this.page.locator('[data-testid="skip-to-main"]');
    await this.verifyElementVisible(skipLink);
    
    // Test keyboard navigation
    await this.page.keyboard.press('Tab');
    const focusedElement = await this.page.locator(':focus').first();
    await expect(focusedElement).toBeVisible();
  }

  async measureDashboardPerformance(): Promise<{
    loadTime: number;
    interactionTimes: Record<string, number>;
  }> {
    const loadTime = await this.measurePageLoadTime();
    
    const interactionTimes: Record<string, number> = {};
    
    // Measure recommendation refresh time
    interactionTimes.recommendationRefresh = await this.measureInteractionTime(async () => {
      await this.refreshRecommendations();
    });
    
    // Measure navigation times
    interactionTimes.contentNavigation = await this.measureInteractionTime(async () => {
      await this.navigateToContentBrowse();
      await this.navigateToDashboard();
    });
    
    return { loadTime, interactionTimes };
  }

  async verifyDataRefresh(): Promise<void> {
    // Get initial statistics
    const initialInteractions = await this.totalInteractionsCount.textContent();
    
    // Trigger data refresh (if available)
    const refreshButton = this.page.locator('[data-testid="refresh-dashboard"]');
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      await this.waitForApiResponse('**/api/user/dashboard');
      
      // Verify data is refreshed (might be same values, but API call was made)
      await this.verifyElementVisible(this.totalInteractionsCount);
    }
  }

  async verifyErrorHandling(): Promise<void> {
    // Test handling of API failures
    // This would typically involve mocking API responses in a real test
    
    // Verify error states are handled gracefully
    const errorStates = [
      this.page.locator('[data-testid="stats-error"]'),
      this.page.locator('[data-testid="activity-error"]'),
      this.page.locator('[data-testid="recommendations-error"]')
    ];
    
    for (const errorState of errorStates) {
      // These should not be visible under normal circumstances
      await expect(errorState).toBeHidden();
    }
  }

  async simulateUserInteraction(): Promise<void> {
    // Simulate a typical user session on the dashboard
    
    // 1. View recommendations
    await this.verifyRecommendations();
    
    // 2. Click on a recommendation
    const recommendationCount = await this.recommendationCards.count();
    if (recommendationCount > 0) {
      await this.clickRecommendation(0);
      await this.page.goBack();
      await this.waitForPageLoad();
    }
    
    // 3. Check recent activity
    await this.verifyRecentActivity();
    
    // 4. Navigate to preferences
    await this.navigateToPreferences();
    await this.page.goBack();
    await this.waitForPageLoad();
    
    // 5. Start learning session
    await this.startLearningSession();
  }
}