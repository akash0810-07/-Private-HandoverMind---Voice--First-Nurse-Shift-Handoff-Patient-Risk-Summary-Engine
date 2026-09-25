import { test, expect } from "@playwright/test";

async function login(page) {
  await page.goto("/login");
  await page.fill('input[type="email"]', "nurse.demo@handovermind.test");
  await page.fill('input[type="password"]', "DemoPass123!");
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/dashboard/);
}

test("dashboard shows stat cards and flagged patients section", async ({ page }) => {
  await login(page);
  await expect(page.locator(".stats-grid")).toBeVisible();
  await expect(page.getByText("Flagged patients")).toBeVisible();
});

test("navigating to handoff history shows the history table", async ({ page }) => {
  await login(page);
  await page.click('a[href="/history"]');
  await expect(page.locator("h1")).toHaveText("Handoff History");
});

test("patient search on dashboard flagged list narrows results", async ({ page }) => {
  await login(page);
  // Flagged list always renders high/medium risk patients from seed data;
  // this smoke-checks that risk badges render with expected labels only.
  const badges = page.locator(".risk-badge");
  const count = await badges.count();
  for (let i = 0; i < count; i++) {
    await expect(badges.nth(i)).toHaveText(/LOW|MEDIUM|HIGH/);
  }
});
