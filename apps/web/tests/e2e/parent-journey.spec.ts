import { test, expect } from '@playwright/test';

test.describe('Parent Journey E2E Tests', () => {
  test.describe('Parent Registration Flow', () => {
    test('should navigate from homepage to login', async ({ page }) => {
      await page.goto('/');

      // Click Get Started button
      const getStartedButton = page.getByText('Get Started');
      await getStartedButton.click();

      // Should be on login page
      await expect(page).toHaveURL(/.*login/);
      await expect(page.getByText(/Welcome to PADI.AI/)).toBeVisible();
    });

    test('should navigate from homepage to login via Sign In', async ({
      page,
    }) => {
      await page.goto('/');

      // Click Sign In button
      const signInButton = page.getByText('Sign In');
      await signInButton.click();

      // Should be on login page
      await expect(page).toHaveURL(/.*login/);
    });

    test('should have consistent navigation throughout site', async ({
      page,
    }) => {
      await page.goto('/');

      // Get PADI.AI branding
      const padiLogo = page.getByText('PADI.AI');
      await expect(padiLogo).toBeVisible();

      // Should be able to navigate to login from homepage
      await page.getByText('Sign In').click();
      await expect(page).toHaveURL(/.*login/);
    });

    test('should display feature information on homepage', async ({ page }) => {
      await page.goto('/');

      // Verify key value propositions are visible
      await expect(
        page.getByText(/Adaptive Learning/)
      ).toBeVisible();
      await expect(page.getByText(/Standards Aligned/)).toBeVisible();
      await expect(page.getByText(/COPPA Compliant/)).toBeVisible();

      // Verify descriptions
      await expect(
        page.getByText(/AI-powered tutoring/)
      ).toBeVisible();
      await expect(
        page.getByText(/Oregon math standards/)
      ).toBeVisible();
      await expect(
        page.getByText(/local LLM processing/)
      ).toBeVisible();
    });

    test('should show CTA buttons in hero section', async ({ page }) => {
      await page.goto('/');

      // Check hero CTA buttons
      await expect(page.getByText('Start Learning')).toBeVisible();
      await expect(page.getByText('Learn More')).toBeVisible();
    });

    test('should have responsive layout indicators', async ({ page }) => {
      await page.goto('/');

      // Check that the page uses responsive containers
      const mainContainer = page.locator(
        '.max-w-7xl.mx-auto.px-4.sm\\:px-6.lg\\:px-8'
      );
      await expect(mainContainer).toBeVisible();
    });
  });
});
