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
  { path: "/meal-plan", label: "Plan", icon: "📅" },
];

function isActive(path: string): boolean {
  if (path === "/") return route.path === "/";
  return route.path.startsWith(path);
}
</script>

<template>
  <nav v-if="isAuthenticated" class="bottom-nav" role="navigation" aria-label="Main navigation">
    <router-link
      v-for="item in navItems"
      :key="item.path"
      :to="item.path"
      class="nav-item"
      :class="{ active: isActive(item.path) }"
      :aria-label="item.label"
      :aria-current="isActive(item.path) ? 'page' : undefined"
    >
      <span class="nav-icon" aria-hidden="true">{{ item.icon }}</span>
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
  padding: 0.25rem 0;
  padding-bottom: calc(0.25rem + var(--safe-area-bottom));
  z-index: 100;
}

/* Hide bottom nav on desktop */
@media (min-width: 1024px) {
  .bottom-nav {
    display: none;
  }
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 0.6875rem;
  padding: 0.375rem 0.25rem;
  min-width: 44px;
  min-height: 44px;
  transition: color 0.2s;
  border-radius: 4px;
}

.nav-item:active {
  background: var(--background);
}

.nav-item.active {
  color: var(--primary);
}

.nav-icon {
  font-size: 1.25rem;
  margin-bottom: 0.125rem;
  line-height: 1;
}

.nav-label {
  font-weight: 500;
  line-height: 1;
}
</style>
