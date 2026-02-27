describe("Android Navigation", () => {
  it("should navigate using bottom tabs", async () => {
    const contexts = await driver.getContexts();
    const webviewContext = contexts.find((c: string) => c.includes("WEBVIEW"));
    if (webviewContext) {
      await driver.switchContext(webviewContext as string);
    }

    // Check bottom navigation is present
    const navItems = await $$(".nav-item");
    await expect(navItems.length).toBeGreaterThanOrEqual(5);
  });

  it("should handle Android back button", async () => {
    await driver.back();
    // App should navigate back, not exit
    await driver.pause(500);
    const body = await $("body");
    await expect(body).toBeDisplayed();
  });
});
