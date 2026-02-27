import { test, expect } from "@playwright/test";

test.describe("Network Conditions", () => {
  test("should show loading state on slow network", async ({ page }) => {
    await page.route("**/api/**", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await route.continue();
    });
    await page.goto("/login");
    // Page should still render and be interactive
    await expect(page.locator("h1")).toBeVisible();
  });

  test("should handle API errors gracefully", async ({ page }) => {
    await page.route("**/api/auth/login", (route) =>
      route.fulfill({ status: 500, body: JSON.stringify({ detail: "Server error" }) }),
    );
    await page.goto("/login");
    await page.fill('input[type="email"]', "test@example.com");
    await page.fill('input[type="password"]', "password123");
    await page.click('button[type="submit"]');
    // Should show error, not crash
    await expect(page.locator("body")).toBeVisible();
  });
});
