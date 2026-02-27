export const config = {
  runner: "local",
  port: 4723,
  specs: ["./e2e/ios/**/*.spec.ts"],
  maxInstances: 1,
  capabilities: [
    {
      platformName: "iOS",
      "appium:automationName": "XCUITest",
      "appium:deviceName": "iPhone 15",
      "appium:platformVersion": "17.0",
      "appium:app": "./ios/App/build/Build/Products/Debug-iphonesimulator/App.app",
      "appium:bundleId": "com.companis.app",
      "appium:newCommandTimeout": 240,
      "appium:autoAcceptAlerts": true,
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
