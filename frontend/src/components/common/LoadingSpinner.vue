<script setup lang="ts">
defineProps<{
  size?: string;
  message?: string;
}>();
</script>

<template>
  <div class="loading-container">
    <div class="spinner" :style="{ width: size ?? '40px', height: size ?? '40px' }" />
    <p v-if="message" class="loading-message">{{ message }}</p>
  </div>
</template>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.spinner {
  border: 3px solid var(--border);
  border-top: 3px solid var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-message {
  margin-top: 1rem;
  color: var(--text-secondary);
}
</style>
