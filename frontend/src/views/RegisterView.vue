<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import { authApi } from "@/services/api";

const authStore = useAuthStore();
const fullName = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const termsAccepted = ref(false);
const showTerms = ref(false);
const termsText = ref("");
const validationError = ref<string | null>(null);

onMounted(async () => {
  try {
    const { data } = await authApi.getTerms();
    termsText.value = data.terms_text;
  } catch {
    termsText.value = "Unable to load terms. Please try again later.";
  }
});

async function handleRegister(): Promise<void> {
  validationError.value = null;
  if (password.value !== confirmPassword.value) {
    validationError.value = "Passwords do not match";
    return;
  }
  if (password.value.length < 8) {
    validationError.value = "Password must be at least 8 characters";
    return;
  }
  if (!termsAccepted.value) {
    validationError.value = "You must accept the terms and conditions";
    return;
  }
  try {
    await authStore.register(email.value, password.value, fullName.value);
  } catch {
    // Error handled by store
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card card">
      <h1 class="auth-title">Create Account</h1>
      <p class="auth-subtitle">Pull up a chair.</p>

      <form class="auth-form" @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="fullName">Full Name</label>
          <input id="fullName" v-model="fullName" type="text" placeholder="Your name" required />
        </div>
        <div class="form-group">
          <label for="email">Email</label>
          <input id="email" v-model="email" type="email" placeholder="you@example.com" required />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="At least 8 characters"
            required
          />
        </div>
        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="Confirm your password"
            required
          />
        </div>

        <div class="terms-section">
          <button type="button" class="terms-toggle" @click="showTerms = !showTerms">
            {{ showTerms ? "Hide" : "View" }} Terms & Conditions
          </button>
          <div v-if="showTerms" class="terms-content">
            <pre class="terms-text">{{ termsText }}</pre>
          </div>
          <label class="terms-checkbox">
            <input v-model="termsAccepted" type="checkbox" />
            <span>
              I have read and agree to the
              <button type="button" class="link-btn" @click="showTerms = true">
                Terms & Conditions
              </button>
              including the AI disclaimer, allergy warning, and liability limitations
            </span>
          </label>
        </div>

        <p v-if="validationError || authStore.error" class="error-text">
          {{ validationError ?? authStore.error }}
        </p>
        <button class="btn-primary full-width" type="submit" :disabled="authStore.loading">
          {{ authStore.loading ? "Creating account..." : "Create Account" }}
        </button>
      </form>

      <p class="auth-link">
        Already have an account? <router-link to="/login">Sign in</router-link>
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
  max-width: 500px;
  padding: 2rem;
}

.auth-title {
  text-align: center;
  color: var(--primary);
  font-size: 1.75rem;
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

.terms-section {
  margin: 1rem 0;
}

.terms-toggle {
  background: none;
  color: var(--primary);
  font-size: 0.875rem;
  padding: 0;
  text-decoration: underline;
  cursor: pointer;
  margin-bottom: 0.5rem;
}

.terms-content {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.75rem;
  margin-bottom: 0.75rem;
  background: var(--background);
}

.terms-text {
  font-size: 0.7rem;
  white-space: pre-wrap;
  font-family: inherit;
  line-height: 1.4;
}

.terms-checkbox {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
  font-size: 0.8rem;
  cursor: pointer;
}

.terms-checkbox input[type="checkbox"] {
  width: auto;
  margin-top: 0.2rem;
}

.link-btn {
  background: none;
  color: var(--primary);
  padding: 0;
  font-size: inherit;
  text-decoration: underline;
  display: inline;
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
