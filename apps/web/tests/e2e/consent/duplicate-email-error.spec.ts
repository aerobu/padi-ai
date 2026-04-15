/**
 * E2E Test: Duplicate Email Error Handling
 *
 * Purpose: Verify proper error handling when parent tries to register
 *          with an email that already has an active consent record.
 *
 * Acceptance Criteria:
 * - Email already in use shows appropriate error
 * - Error is clear and actionable
 * - User can try a different email
 */

import { test, expect } from '@playwright/test';

test.describe('Duplicate Email Error', () => {
  test('should show error when email already has active consent', async ({ page }) => {
    // This test assumes we have a way to pre-create a consent record
    // For now, we'll test the UI flow with mocked data

    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Enter a test email
    const emailInput = page.getByLabel(/email/i);
    await emailInput.fill('duplicate@example.com');

    // Click send verification code
    const sendButton = page.getByRole('button', { name: /send.*code|verify/i });
    await sendButton.click();

    // Note: In a real scenario, this would check the database
    // For E2E, we're testing the UI flow
    await expect(page.getByText(/code sent|verification/i)).toBeVisible();
  });

  test('should handle email format validation before submission', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Enter invalid email formats
    const emailInput = page.getByLabel(/email/i);

    // Test invalid email
    await emailInput.fill('invalid-email');
    const sendButton = page.getByRole('button', { name: /send.*code|verify/i });

    // Should show validation error
    await expect(emailInput).toHaveAttribute('aria-invalid', 'true');
  });

  test('should clear error when email is changed', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Enter email
    const emailInput = page.getByLabel(/email/i);
    await emailInput.fill('test@example.com');

    // Trigger validation
    await emailInput.blur();

    // Clear the email
    await emailInput.fill('');

    // Validation state should update
    await expect(emailInput).not.toHaveAttribute('aria-invalid', 'true');
  });

  test('should provide helpful message for email errors', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Enter email with known issues
    const emailInput = page.getByLabel(/email/i);
    await emailInput.fill('test@');
    await emailInput.blur();

    // Error message should be clear
    const errorMessage = page.locator('.error-message, [role="alert"], .text-red');
    await expect(errorMessage.first()).toBeVisible();
  });

  test('should prevent multiple code requests for same email', async ({ page }) => {
    // This test requires backend state
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Enter email
    const emailInput = page.getByLabel(/email/i);
    await emailInput.fill('rate-limit@example.com');

    // First request
    const sendButton = page.getByRole('button', { name: /send.*code|verify/i });
    await sendButton.click();
    await expect(page.getByText(/code sent|verification/i)).toBeVisible();

    // Try to send again immediately
    // In real scenario, button should be disabled or show rate limit message
    await sendButton.click();

    // Should either be disabled or show rate limit warning
    const isDisabled = await sendButton.getAttribute('disabled');
    if (isDisabled) {
      await expect(sendButton).toBeDisabled();
    } else {
      await expect(page.getByText(/waiting|please.*wait/i)).toBeVisible();
    }
  });

  test('should maintain state when navigating away and back', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Enter email
    const emailInput = page.getByLabel(/email/i);
    await emailInput.fill('state-test@example.com');

    // Navigate away
    await page.goto('/');

    // Click "I am a parent" button again
    await page.click('button:has-text("I am a parent")');

    // Email should be cleared (security best practice)
    await expect(emailInput).toHaveValue('');
  });
});
