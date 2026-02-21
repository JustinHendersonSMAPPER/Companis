<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const authStore = useAuthStore();

onMounted(() => {
  const provider = route.params.provider as string;
  const code = route.query.code as string;
  if (provider && code) {
    void authStore.handleOAuthCallback(provider, code);
  }
});
</script>

<template>
  <div class="callback-container">
    <div class="card" style="text-align: center; padding: 2rem">
      <p v-if="authStore.loading">Completing sign in...</p>
      <p v-if="authStore.error" class="error-text">{{ authStore.error }}</p>
    </div>
  </div>
</template>

<style scoped>
.callback-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
}
</style>
