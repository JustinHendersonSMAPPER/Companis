import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.companis.app",
  appName: "Companis",
  webDir: "dist",
  server: {
    androidScheme: "https",
  },
  ios: {
    preferredContentMode: "mobile",
  },
  plugins: {
    Camera: {
      permissions: ["camera", "photos"],
    },
    Keyboard: {
      resize: "native",
      resizeOnFullScreen: true,
    },
    StatusBar: {
      style: "light",
      backgroundColor: "#4caf50",
    },
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 2000,
      backgroundColor: "#fafafa",
    },
  },
};

export default config;
