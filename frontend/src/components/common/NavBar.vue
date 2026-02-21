<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { computed } from "vue";
import { useRoute } from "vue-router";

const authStore = useAuthStore();
const route = useRoute();

const isAuthenticated = computed(() => authStore.isAuthenticated);

const navItems = [
  { path: "/", label: "Home", icon: "🏠" },
  { path: "/ingredients", label: "Pantry", icon: "🥘" },
  { path: "/scan", label: "Scan", icon: "📷" },
  { path: "/recipes", label: "Recipes", icon: "📖" },
  { path: "/shopping", label: "Shop", icon: "🛒" },
];

function isActive(path: string): boolean {
  return route.path === path;
}
</script>

<template>
  <nav v-if="isAuthenticated" class="bottom-nav">
    <router-link
      v-for="item in navItems"
      :key="item.path"
      :to="item.path"
      class="nav-item"
      :class="{ active: isActive(item.path) }"
    >
      <span class="nav-icon">{{ item.icon }}</span>
      <span class="nav-label">{{ item.label }}</span>
    </router-link>
  </nav>
</template>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  background: var(--surface);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  padding: 0.5rem 0;
  padding-bottom: calc(0.5rem + var(--safe-area-bottom));
  z-index: 100;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  transition: color 0.2s;
}

.nav-item.active {
  color: var(--primary);
}

.nav-icon {
  font-size: 1.5rem;
  margin-bottom: 0.125rem;
}

.nav-label {
  font-weight: 500;
}
</style>
