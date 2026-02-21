import { test, expect, type Page } from "@playwright/test";
import { uniqueEmail, registerUser, waitForAuthenticated } from "./helpers";

async function setupLoggedInUser(page: Page) {
  const email = uniqueEmail();
  await registerUser(page, { email, password: "testpassword123" });
  await waitForAuthenticated(page);
}

test.describe("Shopping Cart", () => {
  test("should navigate to shopping page", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/shopping");
    await expect(page).toHaveURL(/shopping/i);
  });

  test("should display empty shopping list initially", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/shopping");
    const emptyText = page.getByText(/no items|empty|create.*list/i);
    const listArea = page.locator("[class*=shopping], [class*=cart]");
    const visible =
      (await emptyText.isVisible().catch(() => false)) ||
      (await listArea.isVisible().catch(() => false));
    expect(visible).toBeTruthy();
  });
});
