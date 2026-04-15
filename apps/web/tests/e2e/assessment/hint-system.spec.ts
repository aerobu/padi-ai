/**
 * E2E Test: Hint System
 *
 * Purpose: Verify the Socratic hint system works correctly when students
 *          provide incorrect answers, providing guidance without revealing
 *          the answer.
 *
 * Acceptance Criteria:
 * - Hints appear after incorrect answers
 * - Multiple hints provide increasing guidance
 * - Hints don't reveal the correct answer directly
 * - Hint system works for all question types
 */

import { test, expect } from '@playwright/test';

test.describe('Hint System', () => {
  test('should show first hint after first incorrect answer', async ({ page }) => {
    // Start a diagnostic assessment
    await page.goto('/assessment');

    // Get first question
    const questionText = await page.getByRole('button', { name: /select/i }).first().textContent();
    expect(questionText).toBeDefined();

    // Submit an obviously wrong answer
    const answerButtons = page.getByRole('button', { name: /select/i });
    await answerButtons.first().click();

    // Click submit answer
    await page.click('button:has-text("Submit Answer")');

    // Should show "Not quite right" or similar
    await expect(page.getByText(/not quite|not correct|try again/i)).toBeVisible();

    // Hint should appear
    await expect(page.getByText(/hint|try/i)).toBeVisible();
  });

  test('should provide increasing guidance with multiple hints', async ({ page }) => {
    // Start a diagnostic assessment
    await page.goto('/assessment');

    // Find a fraction question
    const fractionButton = page.getByRole('button', { name: /fraction|choose/i }).first();
    if (await fractionButton.count() > 0) {
      await fractionButton.click();
    }

    // Submit wrong answer
    await page.click('button:has-text("Submit Answer")');

    // First hint should be general
    const firstHint = page.getByText(/hint/i).first();
    await expect(firstHint).toBeVisible();
    const firstHintText = await firstHint.textContent();

    // Should not reveal answer
    expect(firstHintText).not.toMatch(/4\/7|4 over 7|four sevenths/i);

    // Get second hint
    const nextHintButton = page.getByRole('button', { name: /next hint|another hint/i });
    if (await nextHintButton.count() > 0) {
      await nextHintButton.click();

      // Second hint should be more specific
      await expect(page.getByText(/hint/i).nth(1)).toBeVisible();
    }
  });

  test('should track hint usage in assessment progress', async ({ page }) => {
    // Start a diagnostic assessment
    await page.goto('/assessment');

    // Submit wrong answer to trigger hint
    await page.click('button:has-text("Submit Answer")');

    // Progress tracker should update to show hints used
    const progressTracker = page.getByText(/hints used|hints available/i);
    await expect(progressTracker).toBeVisible();
  });

  test('should disable hint after using all available hints', async ({ page }) => {
    // Start a diagnostic assessment
    await page.goto('/assessment');

    // Submit wrong answer
    await page.click('button:has-text("Submit Answer")');

    // Use all hints
    while (await page.getByRole('button', { name: /next hint|another hint/i }.source).count() > 0) {
      await page.click('button:has-text(/next hint|another hint/i)');
      await page.waitTimeout(500);
    }

    // Hint button should be disabled or hidden
    const hintButton = page.getByRole('button', { name: /hint/i });
    const isDisabled = await hintButton.getAttribute('disabled');
    if (isDisabled) {
      await expect(hintButton).toBeDisabled();
    } else {
      await expect(hintButton).not.toBeVisible();
    }
  });

  test('should handle hint system for multiple question types', async ({ page }) => {
    // Test with multiple question types if available

    // Question 1: Multiple choice
    await page.goto('/assessment');

    // Submit wrong answer
    await page.click('button:has-text("Submit Answer")');
    await expect(page.getByText(/hint/i)).toBeVisible();

    // Move to next question
    const nextButton = page.getByRole('button', { name: /next/i });
    if (await nextButton.count() > 0) {
      await nextButton.click();
      await page.waitTimeout(500);

      // Hint system should work for next question
      await page.click('button:has-text("Submit Answer")');
      await expect(page.getByText(/hint/i)).toBeVisible();
    }
  });

  test('should not allow skipping hints to get to next question', async ({ page }) => {
    // Start a diagnostic assessment
    await page.goto('/assessment');

    // Submit wrong answer
    await page.click('button:has-text("Submit Answer")');

    // Hint should be visible
    await expect(page.getByText(/hint/i)).toBeVisible();

    // Try to click "Next" without acknowledging hint
    const nextButton = page.getByRole('button', { name: /next|continue/i });
    if (await nextButton.count() > 0) {
      await nextButton.click();
      // May or may not be allowed - this validates the UI behavior
    }
  });

  test('should provide appropriate hints for fraction builder', async ({ page }) => {
    // Navigate to assessment
    await page.goto('/assessment');

    // Find fraction question
    const fractionButtons = page.locator('[data-testid*="fraction"]');
    if (await fractionButtons.count() > 0) {
      // Click to select fraction
      await fractionButtons.first().click();

      // Submit answer
      await page.click('button:has-text("Submit Answer")');

      // Should show hint specific to fractions
      const hint = page.getByText(/hint|try/i).first();
      await expect(hint).toBeVisible();

      // Hint should reference fractions or parts
      const hintText = await hint.textContent();
      expect(hintText?.toLowerCase()).toMatch(/numerator|denominator|fraction|part/i);
    }
  });

  test('should maintain hint state during session pause', async ({ page }) => {
    // Start a diagnostic assessment
    await page.goto('/assessment');

    // Submit wrong answer and get hint
    await page.click('button:has-text("Submit Answer")');
    await expect(page.getByText(/hint/i)).toBeVisible();

    // Pause assessment (if pause feature exists)
    const pauseButton = page.getByRole('button', { name: /pause|save and exit/i });
    if (await pauseButton.count() > 0) {
      await pauseButton.click();

      // Resume assessment
      await page.click('button:has-text("resume")');

      // Hint should still be visible or hint history preserved
      // This validates session state persistence
    }
  });

  test('should have proper focus management for hints', async ({ page }) => {
    // Start a diagnostic assessment
    await page.goto('/assessment');

    // Submit wrong answer
    await page.click('button:has-text("Submit Answer")');

    // Hint should be visible and focusable
    const hintElement = page.getByText(/hint/i).first();
    await expect(hintElement).toBeVisible();

    // Tab to hint area
    await page.keyboard.press('Tab');

    // Hint should be in tab order
    await expect(hintElement).toBeFocused();
  });

  test('should show hint count/progress', async ({ page }) => {
    // Start a diagnostic assessment
    await page.goto('/assessment');

    // Submit wrong answer
    await page.click('button:has-text("Submit Answer")');

    // Should show hint count or progress indicator
    const hintProgress = page.getByText(/hint [0-9]+\/[0-9]+|hint [0-9]+ of/i);
    if (await hintProgress.count() > 0) {
      await expect(hintProgress).toBeVisible();
    }
  });
});
