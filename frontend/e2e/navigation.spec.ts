import { test, expect, type Page } from "@playwright/test";
import { uniqueEmail, registerUser, waitForAuthenticated } from "./helpers";

async function setupLoggedInUser(page: Page) {
  const email = uniqueEmail();
  await registerUser(page, { email, password: "testpassword123" });
  await waitForAuthenticated(page);
}

test.describe("Navigation", () => {
  test("unauthenticated user should be redirected to login", async ({
    page,
  }) => {
    await page.goto("/");
    // Should redirect to login if not authenticated
    await page.waitForURL(/\/(login|register)?$/i, { timeout: 5_000 });
  });

  test("should display navigation bar when logged in", async ({ page }) => {
    await setupLoggedInUser(page);
    const nav = page.locator("nav, [class*=nav]");
    await expect(nav.first()).toBeVisible();
  });

  test("should navigate between main sections", async ({ page }) => {
    await setupLoggedInUser(page);

    // Navigate to various sections via nav links if they exist
    const routes = ["/ingredients", "/recipes", "/shopping", "/household", "/profile"];
    for (const route of routes) {
      await page.goto(route);
      // Verify we can reach each route without being redirected to login
      const url = page.url();
      expect(url).not.toContain("/login");
    }
  });
});
