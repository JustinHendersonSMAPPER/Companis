import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import router from "./router";
import { initializeNativePlugins, setupLifecycleHandlers } from "./services/platform";

const app = createApp(App);

app.use(createPinia());
app.use(router);

app.mount("#app");

// Initialize Capacitor native plugins (no-op on web)
void initializeNativePlugins();

// Set up mobile lifecycle handlers
void setupLifecycleHandlers(() => {
  // Android back button handler
  if (router.currentRoute.value.path !== "/") {
    router.back();
  }
});
