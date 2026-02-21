import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { User } from "@/types";
import { authApi, usersApi } from "@/services/api";
import router from "@/router";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => !!user.value);

  async function initialize(): Promise<void> {
    const token = localStorage.getItem("access_token");
    if (token) {
      try {
        const { data } = await usersApi.getMe();
        user.value = data;
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
    }
  }

  async function register(email: string, password: string, fullName: string): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      await authApi.register({ email, password, full_name: fullName, terms_accepted: true });
      await login(email, password);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error.value = err.response?.data?.detail ?? "Registration failed";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function login(email: string, password: string): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await authApi.login({ email, password });
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      const userResp = await usersApi.getMe();
      user.value = userResp.data;
      await router.push("/");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error.value = err.response?.data?.detail ?? "Login failed";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function loginWithOAuth(provider: string): Promise<void> {
    try {
      const { data } = await authApi.getOAuthUrl(provider);
      window.location.href = data.authorization_url;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error.value = err.response?.data?.detail ?? `OAuth login failed for ${provider}`;
    }
  }

  async function handleOAuthCallback(provider: string, code: string): Promise<void> {
    loading.value = true;
    try {
      const { data } = await authApi.oauthCallback(provider, code);
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      const userResp = await usersApi.getMe();
      user.value = userResp.data;
      await router.push("/");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error.value = err.response?.data?.detail ?? "OAuth callback failed";
    } finally {
      loading.value = false;
    }
  }

  function logout(): void {
    user.value = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    void router.push("/login");
  }

  return {
    user,
    loading,
    error,
    isAuthenticated,
    initialize,
    register,
    login,
    loginWithOAuth,
    handleOAuthCallback,
    logout,
  };
});
