import { test, expect } from "@playwright/test";
import { uniqueEmail, registerUser, loginUser, waitForAuthenticated } from "./helpers";

test.describe("Login", () => {
  test("should display login form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /log\s*in|sign\s*in/i }),
    ).toBeVisible();
  });

  test("should login with valid credentials", async ({ page }) => {
    const email = uniqueEmail();
    const password = "testpassword123";

    // Register first via API to avoid UI complexities
    await registerUser(page, { email, password });
    await page.goto("/login");
    await loginUser(page, email, password);
    await waitForAuthenticated(page);
  });

  test("should reject invalid credentials", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("nobody@example.com");
    await page.getByLabel(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /log\s*in|sign\s*in/i }).click();

    // Should show error or stay on login page
    const error = page.getByText(/invalid|incorrect|wrong|failed/i);
    await expect(error).toBeVisible({ timeout: 5_000 });
  });

  test("should link to registration page", async ({ page }) => {
    await page.goto("/login");
    const registerLink = page.getByRole("link", {
      name: /register|sign\s*up|create/i,
    });
    if (await registerLink.isVisible()) {
      await registerLink.click();
      await expect(page).toHaveURL(/register/i);
    }
  });
});
