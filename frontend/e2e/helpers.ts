import { type Page } from "@playwright/test";

/** Unique email suffix based on timestamp to avoid collisions between tests. */
export function uniqueEmail(prefix = "testuser"): string {
  return `${prefix}-${Date.now()}@example.com`;
}

/** Register a new user and return the credentials. */
export async function registerUser(
  page: Page,
  options?: { email?: string; password?: string; fullName?: string },
) {
  const email = options?.email ?? uniqueEmail();
  const password = options?.password ?? "testpassword123";
  const fullName = options?.fullName ?? "Test User";

  await page.goto("/register");
  await page.getByLabel(/full name/i).fill(fullName);
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);

  // Open and accept terms
  const termsLink = page.getByText(/terms and conditions/i);
  if (await termsLink.isVisible()) {
    await termsLink.click();
    // Wait for modal and scroll terms
    const termsModal = page.locator(".terms-modal, [class*=terms], dialog");
    if (await termsModal.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Scroll to bottom of terms
      await termsModal.evaluate((el) => (el.scrollTop = el.scrollHeight));
    }
  }

  // Check terms acceptance checkbox
  const checkbox = page.getByLabel(/accept|agree|terms/i);
  if (await checkbox.isVisible()) {
    await checkbox.check();
  }

  await page.getByRole("button", { name: /register|sign up|create/i }).click();

  return { email, password, fullName };
}

/** Log in an existing user. */
export async function loginUser(
  page: Page,
  email: string,
  password: string,
) {
  await page.goto("/login");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /log\s*in|sign\s*in/i }).click();
}

/** Wait for the app to be in an authenticated state (e.g., nav shows user menu). */
export async function waitForAuthenticated(page: Page) {
  // Wait for either the home page or a nav element that shows the user is logged in
  await page.waitForURL(/\/(home|recipes|ingredients|profile)?$/i, {
    timeout: 10_000,
  });
}

/** Register and then log in a user, returning credentials. */
export async function registerAndLogin(
  page: Page,
  options?: { email?: string; password?: string; fullName?: string },
) {
  const creds = await registerUser(page, options);
  await waitForAuthenticated(page);
  return creds;
}
