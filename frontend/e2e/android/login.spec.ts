describe("Android Login Flow", () => {
  it("should display the login screen", async () => {
    // Wait for WebView to load
    const contexts = await driver.getContexts();
    const webviewContext = contexts.find((c: string) => c.includes("WEBVIEW"));
    if (webviewContext) {
      await driver.switchContext(webviewContext as string);
    }

    const emailInput = await $('input[type="email"]');
    await expect(emailInput).toBeDisplayed();

    const passwordInput = await $('input[type="password"]');
    await expect(passwordInput).toBeDisplayed();

    const loginButton = await $('button[type="submit"]');
    await expect(loginButton).toBeDisplayed();
  });

  it("should handle login form submission", async () => {
    const emailInput = await $('input[type="email"]');
    await emailInput.setValue("test@example.com");

    const passwordInput = await $('input[type="password"]');
    await passwordInput.setValue("TestPassword123");

    const loginButton = await $('button[type="submit"]');
    await loginButton.click();

    // Wait for navigation or error
    await driver.pause(2000);
  });
});
