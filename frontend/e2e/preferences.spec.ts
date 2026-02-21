import { test, expect, type Page } from "@playwright/test";
import { uniqueEmail, registerUser, loginUser, waitForAuthenticated } from "./helpers";

async function setupLoggedInUser(page: Page) {
  const email = uniqueEmail();
  const password = "testpassword123";
  await registerUser(page, { email, password, fullName: "Pref User" });
  await waitForAuthenticated(page);
  return { email, password };
}

test.describe("Dietary Preferences", () => {
  test("should navigate to profile page", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/profile");
    await expect(page).toHaveURL(/profile/i);
  });

  test("should display dietary preferences section", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/profile");
    await expect(page.getByText(/dietary|preference|allerg/i)).toBeVisible({
      timeout: 5_000,
    });
  });

  test("should display health goals section", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/profile");
    await expect(page.getByText(/health|goal/i)).toBeVisible({
      timeout: 5_000,
    });
  });
});
