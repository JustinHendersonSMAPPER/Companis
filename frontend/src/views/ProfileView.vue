<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import type { DietaryPreference, HealthGoal } from "@/types";
import { usersApi } from "@/services/api";

const authStore = useAuthStore();

const dietaryPreferences = ref<DietaryPreference[]>([]);
const healthGoals = ref<HealthGoal[]>([]);

const newPrefType = ref("");
const newPrefValue = ref("");
const newGoalType = ref("");
const newGoalDescription = ref("");
const error = ref<string | null>(null);

const prefTypes = [
  "allergy",
  "intolerance",
  "diet",
  "dislike",
  "religious",
];

const goalTypes = [
  "weight_loss",
  "weight_gain",
  "lower_cholesterol",
  "reduce_sodium",
  "increase_protein",
  "increase_fiber",
  "general_health",
];

onMounted(() => {
  void loadPreferences();
  void loadGoals();
});

async function loadPreferences(): Promise<void> {
  const { data } = await usersApi.getDietaryPreferences();
  dietaryPreferences.value = data;
}

async function loadGoals(): Promise<void> {
  const { data } = await usersApi.getHealthGoals();
  healthGoals.value = data;
}

async function addPreference(): Promise<void> {
  if (!newPrefType.value || !newPrefValue.value.trim()) return;
  try {
    const { data } = await usersApi.addDietaryPreference({
      preference_type: newPrefType.value,
      value: newPrefValue.value.trim(),
    });
    dietaryPreferences.value.push(data);
    newPrefType.value = "";
    newPrefValue.value = "";
  } catch {
    error.value = "Failed to add preference";
  }
}

async function removePreference(id: string): Promise<void> {
  await usersApi.removeDietaryPreference(id);
  dietaryPreferences.value = dietaryPreferences.value.filter((p) => p.id !== id);
}

async function addGoal(): Promise<void> {
  if (!newGoalType.value || !newGoalDescription.value.trim()) return;
  try {
    const { data } = await usersApi.addHealthGoal({
      goal_type: newGoalType.value,
      description: newGoalDescription.value.trim(),
    });
    healthGoals.value.push(data);
    newGoalType.value = "";
    newGoalDescription.value = "";
  } catch {
    error.value = "Failed to add goal";
  }
}

async function removeGoal(id: string): Promise<void> {
  await usersApi.removeHealthGoal(id);
  healthGoals.value = healthGoals.value.filter((g) => g.id !== id);
}
</script>

<template>
  <div class="profile-view">
    <h1>My Profile</h1>

    <div class="user-section card">
      <h2>{{ authStore.user?.full_name }}</h2>
      <p class="email">{{ authStore.user?.email }}</p>
      <p class="provider">
        Signed in via {{ authStore.user?.auth_provider ?? "local" }}
      </p>
      <button class="btn-secondary" type="button" @click="authStore.logout()">Sign Out</button>
    </div>

    <!-- Dietary Preferences -->
    <div class="section card">
      <h3>Dietary Preferences & Restrictions</h3>
      <div class="pref-list">
        <div v-for="pref in dietaryPreferences" :key="pref.id" class="pref-item">
          <div>
            <span class="pref-type">{{ pref.preference_type }}</span>
            <span class="pref-value">{{ pref.value }}</span>
          </div>
          <button class="remove-btn" type="button" @click="removePreference(pref.id)">x</button>
        </div>
      </div>
      <form class="add-form" @submit.prevent="addPreference">
        <select v-model="newPrefType" required>
          <option value="">Type...</option>
          <option v-for="t in prefTypes" :key="t" :value="t">{{ t }}</option>
        </select>
        <input v-model="newPrefValue" type="text" placeholder="e.g., nuts, gluten, vegan" required />
        <button class="btn-primary" type="submit">Add</button>
      </form>
    </div>

    <!-- Health Goals -->
    <div class="section card">
      <h3>Health Goals</h3>
      <div class="goal-list">
        <div v-for="goal in healthGoals" :key="goal.id" class="goal-item">
          <div>
            <span class="goal-type">{{ goal.goal_type.replace("_", " ") }}</span>
            <span class="goal-desc">{{ goal.description }}</span>
          </div>
          <button class="remove-btn" type="button" @click="removeGoal(goal.id)">x</button>
        </div>
      </div>
      <form class="add-form" @submit.prevent="addGoal">
        <select v-model="newGoalType" required>
          <option value="">Goal type...</option>
          <option v-for="t in goalTypes" :key="t" :value="t">{{ t.replace("_", " ") }}</option>
        </select>
        <input v-model="newGoalDescription" type="text" placeholder="Describe your goal" required />
        <button class="btn-primary" type="submit">Add</button>
      </form>
    </div>

    <router-link to="/household" class="household-link card">
      Manage Household & Family Members →
    </router-link>

    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>

<style scoped>
.user-section {
  margin-bottom: 1rem;
}

.user-section h2 {
  margin-bottom: 0.25rem;
}

.email {
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.provider {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
  text-transform: capitalize;
}

.section h3 {
  margin-bottom: 0.75rem;
}

.pref-item,
.goal-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}

.pref-type,
.goal-type {
  display: inline-block;
  background: var(--primary);
  color: white;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  margin-right: 0.5rem;
  text-transform: capitalize;
}

.pref-value,
.goal-desc {
  font-size: 0.9rem;
}

.add-form {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.add-form select {
  flex: 1;
}

.add-form input {
  flex: 2;
}

.remove-btn {
  background: none;
  color: var(--error);
  font-size: 1.25rem;
  padding: 0.25rem 0.5rem;
}

.household-link {
  display: block;
  text-align: center;
  text-decoration: none;
  color: var(--primary);
  font-weight: 500;
  padding: 1rem;
  margin-top: 1rem;
}
</style>
