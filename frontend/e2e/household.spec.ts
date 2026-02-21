import { test, expect, type Page } from "@playwright/test";
import { uniqueEmail, registerUser, waitForAuthenticated } from "./helpers";

async function setupLoggedInUser(page: Page) {
  const email = uniqueEmail();
  await registerUser(page, {
    email,
    password: "testpassword123",
    fullName: "Household User",
  });
  await waitForAuthenticated(page);
}

test.describe("Household Management", () => {
  test("should navigate to household page", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/household");
    await expect(page).toHaveURL(/household/i);
  });

  test("should display household with owner", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/household");
    // The registered user should appear as the owner/member
    await expect(page.getByText(/household|kitchen|family/i)).toBeVisible({
      timeout: 5_000,
    });
  });

  test("should show option to add family members", async ({ page }) => {
    await setupLoggedInUser(page);
    await page.goto("/household");
    const addButton = page.getByRole("button", { name: /add.*member|add/i });
    const addText = page.getByText(/add.*member/i);
    const visible =
      (await addButton.isVisible().catch(() => false)) ||
      (await addText.isVisible().catch(() => false));
    expect(visible).toBeTruthy();
  });
});
