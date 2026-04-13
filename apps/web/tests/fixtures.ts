import { test as base, Page } from '@playwright/test';
import { expect } from '@playwright/test';

export const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
export const FRONTEND_BASE_URL = process.env.FRONTEND_BASE_URL || 'http://localhost:3000';

export interface TestUser {
  email: string;
  password: string;
}

export const test = base.extend<{
  homePage: Page;
  loginPage: Page;
}>({
  homePage: async ({ page }, use) => {
    await page.goto(FRONTEND_BASE_URL);
    await expect(page).toHaveURL(new RegExp(`${FRONTEND_BASE_URL}`));
    await use(page);
  },
  loginPage: async ({ page }, use) => {
    await page.goto(`${FRONTEND_BASE_URL}/(auth)/login`);
    await expect(page).toHaveURL(new RegExp(`${FRONTEND_BASE_URL}/.*login`));
    await use(page);
  },
});

export { expect };
