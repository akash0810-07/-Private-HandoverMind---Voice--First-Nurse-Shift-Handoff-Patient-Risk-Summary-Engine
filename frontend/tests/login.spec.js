import { test, expect } from "@playwright/test";

// These E2E tests assume a backend is running with a seeded demo nurse
// (see scripts/seed_data.py) at the URL configured via VITE_API_BASE_URL.

test("shows login page with demo notice", async ({ page }) => {
  await page.goto("/login");
  await expect(page.locator("h1")).toHaveText("HandoverMind");
  await expect(page.getByText("synthetic patient data only")).toBeVisible();
});

test("rejects invalid credentials with an error message", async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[type="email"]', "nobody@example.com");
  await page.fill('input[type="password"]', "wrongpassword");
  await page.click('button[type="submit"]');
  await expect(page.locator(".error-banner")).toBeVisible();
});

test("logs in with seeded demo nurse and reaches dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[type="email"]', "nurse.demo@handovermind.test");
  await page.fill('input[type="password"]', "DemoPass123!");
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/dashboard/);
  await expect(page.locator("h1")).toHaveText("Ward Dashboard");
});
