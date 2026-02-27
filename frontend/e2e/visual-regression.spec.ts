import { test, expect } from "@playwright/test";

test.describe("Visual Regression", () => {
  test("login page matches baseline", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("login-page.png", {
      maxDiffPixelRatio: 0.01,
    });
  });

  test("register page matches baseline", async ({ page }) => {
    await page.goto("/register");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("register-page.png", {
      maxDiffPixelRatio: 0.01,
    });
  });
});
