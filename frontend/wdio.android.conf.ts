export const config = {
  runner: "local",
  port: 4723,
  specs: ["./e2e/android/**/*.spec.ts"],
  maxInstances: 1,
  capabilities: [
    {
      platformName: "Android",
      "appium:automationName": "UiAutomator2",
      "appium:deviceName": "Pixel_5_API_34",
      "appium:app": "./android/app/build/outputs/apk/debug/app-debug.apk",
      "appium:appPackage": "com.companis.app",
      "appium:appActivity": ".MainActivity",
      "appium:newCommandTimeout": 240,
      "appium:autoGrantPermissions": true,
    },
  ],
  framework: "mocha",
  mochaOpts: {
    timeout: 60000,
  },
  logLevel: "info",
  waitforTimeout: 10000,
  connectionRetryTimeout: 120000,
  connectionRetryCount: 3,
};
