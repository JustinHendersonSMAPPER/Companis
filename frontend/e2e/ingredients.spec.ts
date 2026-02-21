import { test, expect, type Page } from "@playwright/test";
import { uniqueEmail, registerUser, waitForAuthenticated } from "./helpers";

async function setupLoggedInUser(page: Page) {
  const email = uniqueEmail();
  await registerUser(page, { email, password: "testpassword123" });
  await waitForAuthenticated(page);
}

test.describe("Ingredients Management", () => {
  test("should navigate to ingredients page", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/ingredients");
    await expect(page).toHaveURL(/ingredients/i);
  });

  test("should display empty pantry initially", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/ingredients");
    // Should show empty state or the add ingredient form
    const addButton = page.getByRole("button", { name: /add/i });
    const emptyText = page.getByText(/no ingredients|empty|add your first/i);
    const visible =
      (await addButton.isVisible().catch(() => false)) ||
      (await emptyText.isVisible().catch(() => false));
    expect(visible).toBeTruthy();
  });

  test("should show scan option", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/scan");
    await expect(page).toHaveURL(/scan/i);
  });
});
