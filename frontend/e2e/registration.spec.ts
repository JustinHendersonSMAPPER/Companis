import { test, expect } from "@playwright/test";
import { uniqueEmail, registerUser, loginUser } from "./helpers";

test.describe("Registration", () => {
  test("should display registration form", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByLabel(/full name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /register|sign up|create/i }),
    ).toBeVisible();
  });

  test("should show terms and conditions link", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByText(/terms/i)).toBeVisible();
  });

  test("should successfully register a new user", async ({ page }) => {
    const creds = await registerUser(page);
    // After registration, user should be redirected to home or login
    await page.waitForURL(/\/(home|login|recipes)?$/i, { timeout: 10_000 });
  });

  test("should reject registration with short password", async ({ page }) => {
    await page.goto("/register");
    await page.getByLabel(/full name/i).fill("Test User");
    await page.getByLabel(/email/i).fill(uniqueEmail());
    await page.getByLabel(/password/i).fill("short");

    const checkbox = page.getByLabel(/accept|agree|terms/i);
    if (await checkbox.isVisible()) {
      await checkbox.check();
    }

    await page.getByRole("button", { name: /register|sign up|create/i }).click();
    // Should show error or stay on register page
    await expect(page).toHaveURL(/register/i);
  });

  test("should reject duplicate email registration", async ({ page }) => {
    const email = uniqueEmail();
    await registerUser(page, { email });

    // Navigate back to register
    await page.goto("/register");
    await registerUser(page, { email });

    // Should show an error about email already being registered
    const errorText = page.getByText(/already|exists|duplicate/i);
    await expect(errorText).toBeVisible({ timeout: 5_000 });
  });

  test("should link to login page", async ({ page }) => {
    await page.goto("/register");
    const loginLink = page.getByRole("link", { name: /log\s*in|sign\s*in/i });
    if (await loginLink.isVisible()) {
      await loginLink.click();
      await expect(page).toHaveURL(/login/i);
    }
  });
});
