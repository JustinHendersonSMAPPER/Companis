<script setup lang="ts">
import { ref } from "vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const isOpen = ref(false);

function toggle(): void {
  isOpen.value = !isOpen.value;
}

function close(): void {
  isOpen.value = false;
}
</script>

<template>
  <div class="user-menu" @focusout="close">
    <button
      class="user-menu-trigger"
      type="button"
      :aria-expanded="isOpen"
      aria-haspopup="true"
      aria-label="User menu"
      @click="toggle"
    >
      <span class="user-avatar" aria-hidden="true">
        {{ authStore.user?.full_name?.charAt(0)?.toUpperCase() ?? "U" }}
      </span>
      <span class="user-name">{{ authStore.user?.full_name?.split(" ")[0] ?? "Account" }}</span>
    </button>
    <div v-if="isOpen" class="user-menu-dropdown" role="menu">
      <router-link to="/profile" class="menu-item" role="menuitem" @click="close">
        Profile & Preferences
      </router-link>
      <router-link to="/household" class="menu-item" role="menuitem" @click="close">
        Household & Family
      </router-link>
      <button class="menu-item logout" type="button" role="menuitem" @click="authStore.logout()">
        Sign Out
      </button>
    </div>
  </div>
</template>

<style scoped>
.user-menu {
  position: relative;
}

.user-menu-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius);
  min-height: 44px;
}

.user-menu-trigger:hover {
  background: var(--background);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.875rem;
}

.user-name {
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 500;
}

@media (max-width: 400px) {
  .user-name {
    display: none;
  }
}

.user-menu-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  z-index: 200;
  overflow: hidden;
  margin-top: 0.25rem;
}

.menu-item {
  display: block;
  width: 100%;
  padding: 0.75rem 1rem;
  text-align: left;
  text-decoration: none;
  color: var(--text-primary);
  font-size: 0.9rem;
  background: none;
  border: none;
  border-radius: 0;
  min-height: 44px;
  cursor: pointer;
}

.menu-item:hover {
  background: var(--background);
}

.menu-item.logout {
  color: var(--error);
  border-top: 1px solid var(--border);
}
</style>
