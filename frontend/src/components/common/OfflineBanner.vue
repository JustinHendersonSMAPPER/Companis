<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";

const isOffline = ref(!navigator.onLine);

function handleOnline(): void {
  isOffline.value = false;
}

function handleOffline(): void {
  isOffline.value = true;
}

onMounted(() => {
  window.addEventListener("online", handleOnline);
  window.addEventListener("offline", handleOffline);
});

onUnmounted(() => {
  window.removeEventListener("online", handleOnline);
  window.removeEventListener("offline", handleOffline);
});
</script>

<template>
  <div v-if="isOffline" class="offline-banner" role="alert">
    You are offline. Some features may be unavailable.
  </div>
</template>

<style scoped>
.offline-banner {
  background: var(--warning);
  color: white;
  text-align: center;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
}
</style>
