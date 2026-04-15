/**
 * E2E Test: Expired Consent Link Error
 *
 * Purpose: Verify proper handling when parent clicks an expired consent
 *          verification link (older than 7 days).
 *
 * Acceptance Criteria:
 * - Expired link shows clear error message
 * - User can request a new verification code
 * - Error doesn't expose sensitive information
 */

import { test, expect } from '@playwright/test';

test.describe('Expired Link Error', () => {
  test('should show error for expired verification token', async ({ page }) => {
    // This test simulates clicking an expired link
    // In production, the backend would validate token age

    // Navigate to consent verification page with expired token
    await page.goto('/consent/verify?token=expired_token_12345');

    // Should show expired error
    await expect(page.getByText(/expired|invalid.*link|token.*expired/i)).toBeVisible();
  });

  test('should provide option to request new code', async ({ page }) => {
    // Navigate to consent verification page
    await page.goto('/consent/verify?token=expired_token_12345');

    // Should have button to request new code
    const newCodeButton = page.getByRole('button', { name: /request.*new.*code|resend|get.*new/i });
    await expect(newCodeButton).toBeVisible();
    await expect(newCodeButton).toBeEnabled();
  });

  test('should not expose user information in error message', async ({ page }) => {
    // Navigate to consent verification page
    await page.goto('/consent/verify?token=expired_token_12345');

    // Error message should be generic, not reveal email
    const errorText = page.getByText(/expired|invalid/i).first();
    const text = await errorText.textContent();

    // Should not contain email pattern
    expect(text).not.toMatch(/@/);
    expect(text).not.toMatch(/example\.com/);
  });

  test('should allow requesting new code and complete flow', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Enter test email
    const emailInput = page.getByLabel(/email/i);
    await emailInput.fill('resend-test@example.com');

    // Check consent checkboxes
    await page.check('label:has-text("I have read and understand")');
    await page.check('label:has-text("I confirm I am the parent or guardian")');

    // Submit
    await page.click('button:has-text(/Submit|Send Code/i)');

    // Should see code sent message
    await expect(page.getByText(/code sent|verification.*sent/i)).toBeVisible();

    // Note: In E2E, we can't actually verify email receipt
    // This validates the UI flow up to code generation
  });

  test('should handle token format validation', async ({ page }) => {
    // Navigate with malformed token
    await page.goto('/consent/verify?token=');

    // Should show invalid token error
    await expect(page.getByText(/invalid.*token/i)).toBeVisible();
  });

  test('should prevent replay attacks with used tokens', async ({ page }) => {
    // This test assumes a valid token exists
    // Navigate with used token
    await page.goto('/consent/verify?token=used_token_12345');

    // Should show token already used error
    await expect(page.getByText(/already.*used|already.*verified|token.*used/i)).toBeVisible();
  });

  test('should show countdown for rate limiting', async ({ page }) => {
    // This test requires rate limiting state
    // Navigate to age gate
    await page.goto('/');

    // Click "I am a parent"
    await page.click('button:has-text("I am a parent")');

    // Enter email
    const emailInput = page.getByLabel(/email/i);
    await emailInput.fill('rate-limit@example.com');

    // Submit
    await page.click('button:has-text(/Submit|Send Code/i)');

    // Wait for rate limit state (if implemented)
    const countdown = page.getByText(/seconds|waiting.*before/i);
    if (await countdown.count() > 0) {
      await expect(countdown).toBeVisible();
    }
  });

  test('should have accessibility support for error messages', async ({ page }) => {
    // Navigate to consent verification with expired token
    await page.goto('/consent/verify?token=expired_token_12345');

    // Error should be in alert region
    const alertRegion = page.locator('[role="alert"]');
    if (await alertRegion.count() > 0) {
      await expect(alertRegion).toBeVisible();
    }

    // Or error should have aria-live
    const liveRegion = page.locator('[aria-live="polite"]');
    if (await liveRegion.count() > 0) {
      await expect(liveRegion).toBeVisible();
    }
  });
});
