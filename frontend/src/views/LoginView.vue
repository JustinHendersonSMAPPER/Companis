<script setup lang="ts">
import { ref } from "vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const email = ref("");
const password = ref("");

async function handleLogin(): Promise<void> {
  try {
    await authStore.login(email.value, password.value);
  } catch {
    // Error handled by store
  }
}

function loginWithGoogle(): void {
  void authStore.loginWithOAuth("google");
}

function loginWithFacebook(): void {
  void authStore.loginWithOAuth("facebook");
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card card">
      <h1 class="auth-title">Companis</h1>
      <p class="auth-subtitle">Pull up a chair.</p>

      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="email">Email</label>
          <input id="email" v-model="email" type="email" placeholder="you@example.com" required autocomplete="email" aria-required="true" />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="Your password"
            required
            autocomplete="current-password"
            aria-required="true"
          />
        </div>
        <p v-if="authStore.error" class="error-text" role="alert" aria-live="polite">{{ authStore.error }}</p>
        <button class="btn-primary full-width" type="submit" :disabled="authStore.loading">
          {{ authStore.loading ? "Signing in..." : "Sign In" }}
        </button>
      </form>

      <div class="divider"><span>or continue with</span></div>

      <div class="oauth-buttons">
        <button class="oauth-btn google" type="button" @click="loginWithGoogle">Google</button>
        <button class="oauth-btn facebook" type="button" @click="loginWithFacebook">
          Facebook
        </button>
      </div>

      <p class="auth-link">
        Don't have an account? <router-link to="/register">Sign up</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
}

.auth-title {
  text-align: center;
  color: var(--primary);
  font-size: 2rem;
  margin-bottom: 0.25rem;
}

.auth-subtitle {
  text-align: center;
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.auth-form {
  margin-bottom: 1.5rem;
}

.full-width {
  width: 100%;
}

.divider {
  display: flex;
  align-items: center;
  margin: 1.5rem 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.divider::before,
.divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border);
}

.divider span {
  padding: 0 1rem;
}

.oauth-buttons {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.oauth-btn {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  font-weight: 500;
}

.oauth-btn.google:hover {
  border-color: #4285f4;
  color: #4285f4;
}

.oauth-btn.facebook:hover {
  border-color: #1877f2;
  color: #1877f2;
}

.auth-link {
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.auth-link a {
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
}
</style>
