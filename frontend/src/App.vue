<script setup lang="ts">
import { RouterView } from "vue-router";
import NavBar from "@/components/common/NavBar.vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
authStore.initialize();
</script>

<template>
  <div id="app-container">
    <NavBar />
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style>
:root {
  --primary: #4caf50;
  --primary-dark: #388e3c;
  --secondary: #ff9800;
  --background: #fafafa;
  --surface: #ffffff;
  --error: #f44336;
  --text-primary: #212121;
  --text-secondary: #757575;
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
  padding-top: var(--safe-area-top);
  padding-bottom: var(--safe-area-bottom);
}

#app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding-bottom: calc(60px + var(--safe-area-bottom));
}

button {
  cursor: pointer;
  border: none;
  border-radius: var(--radius);
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background-color: var(--primary);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-dark);
}

.btn-secondary {
  background-color: var(--secondary);
  color: white;
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
}

input:focus,
textarea:focus,
select:focus {
  border-color: var(--primary);
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
</style>
