import { test, expect } from "@playwright/test";

async function login(page) {
  await page.goto("/login");
  await page.fill('input[type="email"]', "nurse.demo@handovermind.test");
  await page.fill('input[type="password"]', "DemoPass123!");
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/dashboard/);
}

test("start handoff page requests microphone and shows controls", async ({ page, context }) => {
  await context.grantPermissions(["microphone"]);
  await login(page);
  await page.click('a[href="/record"]');
  await expect(page.locator("h1")).toHaveText("Start Handoff");
  await expect(page.getByRole("button", { name: "Start Recording" })).toBeVisible();
});

test("editing and confirming a summary updates review status", async ({ page }) => {
  await login(page);
  // Assumes seed data has produced at least one pending-review summary
  // reachable from the dashboard's flagged patients list.
  await page.click("text=Review / Edit >> nth=0");
  await expect(page.locator("h1")).toHaveText("Review & Confirm Summary");

  await page.fill('.review-form input:below(:text("Patient name"))', "Edited Patient Name");
  await page.click('button:has-text("Confirm summary")');

  await expect(page.locator(".review-pill.confirmed")).toBeVisible();
});
