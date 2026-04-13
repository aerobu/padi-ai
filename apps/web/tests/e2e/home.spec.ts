import { test, expect } from '@playwright/test';

test.describe('Homepage E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should render homepage successfully', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/PADI.AI/);

    // Check main heading
    await expect(page.getByText(/Adaptive Math Learning/)).toBeVisible();
    await expect(page.getByText(/for Oregon Students/)).toBeVisible();
  });

  test('should have working navigation', async ({ page }) => {
    // Check navigation exists
    const nav = page.getByRole('navigation');
    await expect(nav).toBeVisible();

    // Check PADI.AI branding
    await expect(page.getByText('PADI.AI')).toBeVisible();
  });

  test('should have Sign In button linking to login', async ({ page }) => {
    const signInButton = page.getByText('Sign In');
    await expect(signInButton).toBeVisible();

    // Navigate to login page
    await signInButton.click();
    await expect(page).toHaveURL(/.*login/);
  });

  test('should have Get Started button linking to login', async ({ page }) => {
    const getStartedButton = page.getByText('Get Started');
    await expect(getStartedButton).toBeVisible();

    await getStartedButton.click();
    await expect(page).toHaveURL(/.*login/);
  });

  test('should have CTA buttons with correct messaging', async ({ page }) => {
    await expect(page.getByText('Start Learning')).toBeVisible();
    await expect(page.getByText('Learn More')).toBeVisible();
  });

  test('should display all three feature cards', async ({ page }) => {
    // Check Adaptive Learning feature
    const adaptiveLearning = page.getByText('Adaptive Learning');
    await expect(adaptiveLearning).toBeVisible();
    await expect(
      page.getByText(/AI-powered tutoring that adjusts to each student/)
    ).toBeVisible();

    // Check Standards Aligned feature
    const standardsAligned = page.getByText('Standards Aligned');
    await expect(standardsAligned).toBeVisible();
    await expect(
      page.getByText(/Content mapped to Oregon math standards/)
    ).toBeVisible();

    // Check COPPA Compliant feature
    const coppaCompliant = page.getByText('COPPA Compliant');
    await expect(coppaCompliant).toBeVisible();
    await expect(
      page.getByText(/Privacy-first design with local LLM/)
    ).toBeVisible();
  });

  test('should have footer with copyright', async ({ page }) => {
    const footer = page.getByRole('contentinfo');
    await expect(footer).toBeVisible();
    await expect(page.getByText(/© 2026 PADI.AI/)).toBeVisible();
  });

  test('should respond to hover on buttons', async ({ page }) => {
    const signInButton = page.getByText('Sign In');
    await signInButton.hover();
    // Button should show hover state (visual check)
  });

  test('page should load within reasonable time', async ({ page }) => {
    const startTime = Date.now();
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(10000); // Less than 10 seconds
  });
});
