import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Accessibility", () => {
  test("login page should have no critical accessibility violations", async ({ page }) => {
    await page.goto("/login");
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(results.violations.filter((v) => v.impact === "critical")).toEqual([]);
  });

  test("register page should have no critical accessibility violations", async ({ page }) => {
    await page.goto("/register");
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(results.violations.filter((v) => v.impact === "critical")).toEqual([]);
  });
});
