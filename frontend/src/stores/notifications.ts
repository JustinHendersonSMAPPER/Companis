import { defineStore } from "pinia";
import { ref } from "vue";

export interface Toast {
  id: number;
  message: string;
  type: "success" | "error" | "info" | "warning";
}

let nextId = 0;

export const useNotificationsStore = defineStore("notifications", () => {
  const toasts = ref<Toast[]>([]);

  function show(message: string, type: Toast["type"] = "info"): void {
    const id = nextId++;
    toasts.value.push({ id, message, type });
    setTimeout(() => dismiss(id), 3000);
  }

  function success(message: string): void {
    show(message, "success");
  }

  function error(message: string): void {
    show(message, "error");
  }

  function dismiss(id: number): void {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }

  return { toasts, show, success, error, dismiss };
});
