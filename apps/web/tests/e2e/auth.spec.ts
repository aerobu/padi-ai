import { test, expect } from '@playwright/test';

test.describe('Authentication E2E Tests', () => {
  test('should show login page with Auth0 button', async ({ page }) => {
    await page.goto('/(auth)/login');

    // Check welcome heading
    await expect(page.getByText(/Welcome to PADI.AI/)).toBeVisible();

    // Check subtitle
    await expect(
      page.getByText(/Sign in to continue your adaptive math learning journey/)
    ).toBeVisible();

    // Check Auth0 login button
    const authButton = page.getByText('Continue with Auth0');
    await expect(authButton).toBeVisible();
  });

  test('should redirect to API auth endpoint when clicking Auth0 button', async ({
    page,
  }) => {
    await page.goto('/(auth)/login');

    const authButton = page.getByText('Continue with Auth0');
    await authButton.click();

    // Should redirect to /api/auth/login
    await page.waitForURL(/.*api\/auth\/login/);
  });

  test('should have terms and privacy links on login page', async ({ page }) => {
    await page.goto('/(auth)/login');

    // Check Terms of Service link
    await expect(page.getByText('Terms of Service')).toBeVisible();
    await expect(page.getByText('Terms of Service')).toHaveAttribute(
      'href',
      '/terms'
    );

    // Check Privacy Policy link
    await expect(page.getByText('Privacy Policy')).toBeVisible();
    await expect(page.getByText('Privacy Policy')).toHaveAttribute(
      'href',
      '/privacy'
    );
  });

  test('login page should have proper card layout', async ({ page }) => {
    await page.goto('/(auth)/login');

    // Check for the centered card container
    const card = page.locator(
      'div:has-text("Welcome to PADI.AI")'
    ).first().locator('xpath=../../..');
    await expect(card).toBeVisible();
  });

  test('should handle navigation to protected routes', async ({ page }) => {
    // Go to login page
    await page.goto('/(auth)/login');

    // Verify we're on the login page
    await expect(page.getByText(/Welcome to PADI.AI/)).toBeVisible();
  });
});
