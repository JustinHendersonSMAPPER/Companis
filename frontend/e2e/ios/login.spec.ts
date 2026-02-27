describe("iOS Login Flow", () => {
  it("should display the login screen", async () => {
    const contexts = await driver.getContexts();
    const webviewContext = contexts.find((c: string) => c.includes("WEBVIEW"));
    if (webviewContext) {
      await driver.switchContext(webviewContext as string);
    }

    const emailInput = await $('input[type="email"]');
    await expect(emailInput).toBeDisplayed();

    const passwordInput = await $('input[type="password"]');
    await expect(passwordInput).toBeDisplayed();
  });
});
