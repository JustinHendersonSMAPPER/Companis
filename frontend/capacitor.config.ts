import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.companis.app",
  appName: "Companis",
  webDir: "dist",
  server: {
    androidScheme: "https",
  },
  plugins: {
    Camera: {
      permissions: ["camera", "photos"],
    },
  },
};

export default config;
