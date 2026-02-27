<script setup lang="ts">
import { RouterView } from "vue-router";
import NavBar from "@/components/common/NavBar.vue";
import UserMenu from "@/components/common/UserMenu.vue";
import ToastContainer from "@/components/common/ToastContainer.vue";
import OfflineBanner from "@/components/common/OfflineBanner.vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
authStore.initialize();
</script>

<template>
  <div id="app-container">
    <header v-if="authStore.isAuthenticated" class="app-header">
      <router-link to="/" class="header-brand">Companis</router-link>
      <UserMenu />
    </header>
    <OfflineBanner />
    <NavBar />
    <main class="main-content">
      <RouterView />
    </main>
    <ToastContainer />
  </div>
</template>

<style>
:root {
  --primary: #4caf50;
  --primary-dark: #388e3c;
  --primary-light: #c8e6c9;
  --secondary: #ff9800;
  --secondary-dark: #f57c00;
  --background: #fafafa;
  --surface: #ffffff;
  --error: #f44336;
  --success: #4caf50;
  --warning: #ff9800;
  --info: #2196f3;
  --text-primary: #212121;
  --text-secondary: #616161;
  --border: #e0e0e0;
  --radius: 8px;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  --safe-area-top: env(safe-area-inset-top, 0px);
  --safe-area-bottom: env(safe-area-inset-bottom, 0px);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background-color: var(--background);
  color: var(--text-primary);
  line-height: 1.5;
  padding-top: var(--safe-area-top);
  padding-bottom: var(--safe-area-bottom);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 90;
}

.header-brand {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--primary);
  text-decoration: none;
}

.main-content {
  flex: 1;
  padding: 1rem;
  width: 100%;
  padding-bottom: calc(70px + var(--safe-area-bottom));
}

/* Tablet: 2-column layouts, wider content */
@media (min-width: 768px) {
  .main-content {
    max-width: 768px;
    margin: 0 auto;
    padding: 1.5rem;
    padding-bottom: calc(70px + var(--safe-area-bottom));
  }
}

/* Desktop: max-width container, no bottom nav padding */
@media (min-width: 1024px) {
  .main-content {
    max-width: 960px;
    padding-bottom: 2rem;
  }
}

@media (min-width: 1200px) {
  .main-content {
    max-width: 1100px;
  }
}

button {
  cursor: pointer;
  border: none;
  border-radius: var(--radius);
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
  min-height: 44px;
}

.btn-primary {
  background-color: var(--primary);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-dark);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: var(--secondary);
  color: white;
}

.btn-secondary:hover {
  background-color: var(--secondary-dark);
}

.card {
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1rem;
  margin-bottom: 1rem;
}

input,
textarea,
select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
  min-height: 44px;
}

input:focus,
textarea:focus,
select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.error-text {
  color: var(--error);
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

/* Utility: visually hidden but accessible to screen readers */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Responsive grid utility */
.grid-2col {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 768px) {
  .grid-2col {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
