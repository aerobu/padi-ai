/**
 * E2E Test: Consent Checkbox Validation
 *
 * Purpose: Verify COPPA consent form requires both checkboxes to be checked
 *          before submission is allowed.
 *
 * Acceptance Criteria:
 * - Unchecked first checkbox shows error message
 * - Unchecked second checkbox shows error message
 * - Both checked allows form submission
 * - Error messages clear when checkboxes are checked
 */

import { test, expect } from '@playwright/test';

test.describe('Consent Checkbox Validation', () => {
  test('should show error when first checkbox is unchecked', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Wait for consent form to appear
    await expect(page.getByText('COPPA Compliance')).toBeVisible();

    // Check second box but not first
    await page.check('label:has-text("I confirm I am the parent or guardian")');

    // Try to submit
    const submitButton = page.getByRole('button', { name: /submit|send/i });
    await submitButton.click();

    // Error message should appear for unchecked first box
    await expect(page.getByText(/required|must.*acknowledge/i)).toBeVisible();
  });

  test('should show error when second checkbox is unchecked', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Check first box but not second
    await page.check('label:has-text("I have read and understand")');

    // Try to submit
    const submitButton = page.getByRole('button', { name: /submit|send/i });
    await submitButton.click();

    // Error message should appear for unchecked second box
    await expect(page.getByText(/parent.*guardian|must.*confirm/i)).toBeVisible();
  });

  test('should allow submission when both checkboxes are checked', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Check both boxes
    await page.check('label:has-text("I have read and understand")');
    await page.check('label:has-text("I confirm I am the parent or guardian")');

    // Submit should succeed
    const submitButton = page.getByRole('button', { name: /submit|send/i });
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // Should proceed to email verification
    await expect(page.getByText(/email|verification/i)).toBeVisible();
  });

  test('should clear error messages when checkboxes are checked', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Try to submit with no checkboxes checked
    const submitButton = page.getByRole('button', { name: /submit|send/i });
    await submitButton.click();

    // Error should be visible
    await expect(page.getByText(/required/i)).toBeVisible();

    // Check both boxes
    await page.check('label:has-text("I have read and understand")');
    await page.check('label:has-text("I confirm I am the parent or guardian")');

    // Error should disappear
    await expect(page.getByText(/required/i)).not.toBeVisible();
  });

  test('should prevent form submission with keyboard only', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Tab through to first checkbox and check it
    await page.keyboard.press('Tab');
    await page.keyboard.press('Space');

    // Tab to second checkbox
    await page.keyboard.press('Tab');
    await page.keyboard.press('Space');

    // Tab to submit button
    await page.keyboard.press('Tab');

    // Submit should be enabled
    const submitButton = page.getByRole('button', { name: /submit|send/i });
    await expect(submitButton).toBeEnabled();

    // Press Enter to submit
    await page.keyboard.press('Enter');

    // Should proceed to email verification
    await expect(page.getByText(/email|verification/i)).toBeVisible();
  });

  test('should have proper focus indicators on checkboxes', async ({ page }) => {
    // Navigate to age gate page
    await page.goto('/');

    // Click "I am a parent" button
    await page.click('button:has-text("I am a parent")');

    // Tab to first checkbox
    await page.keyboard.press('Tab');

    // First checkbox should have focus
    const firstCheckbox = page.locator('label:has-text("I have read and understand")');
    await expect(firstCheckbox).toBeFocused();

    // Press Tab to move to second checkbox
    await page.keyboard.press('Tab');

    // Focus should move to second checkbox
    const secondCheckbox = page.locator('label:has-text("I confirm I am the parent or guardian")');
    await expect(secondCheckbox).toBeFocused();
  });
});
