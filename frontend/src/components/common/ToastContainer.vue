<script setup lang="ts">
import { useNotificationsStore } from "@/stores/notifications";

const notifications = useNotificationsStore();
</script>

<template>
  <div class="toast-container" aria-live="polite" aria-atomic="true">
    <div
      v-for="toast in notifications.toasts"
      :key="toast.id"
      class="toast"
      :class="toast.type"
      role="alert"
    >
      <span class="toast-message">{{ toast.message }}</span>
      <button
        class="toast-dismiss"
        type="button"
        aria-label="Dismiss notification"
        @click="notifications.dismiss(toast.id)"
      >
        &times;
      </button>
    </div>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: calc(1rem + var(--safe-area-top, 0px));
  right: 1rem;
  left: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  pointer-events: none;
}

@media (min-width: 768px) {
  .toast-container {
    left: auto;
    width: 360px;
  }
}

.toast {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  pointer-events: auto;
  animation: slideIn 0.3s ease-out;
  color: white;
  font-weight: 500;
  font-size: 0.9rem;
}

.toast.success {
  background: var(--success);
}

.toast.error {
  background: var(--error);
}

.toast.info {
  background: var(--info);
}

.toast.warning {
  background: var(--warning);
}

.toast-dismiss {
  background: none;
  border: none;
  color: white;
  font-size: 1.25rem;
  padding: 0 0.25rem;
  cursor: pointer;
  min-height: auto;
  opacity: 0.8;
}

.toast-dismiss:hover {
  opacity: 1;
}

@keyframes slideIn {
  from {
    transform: translateY(-1rem);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
