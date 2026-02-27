<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { usersApi } from "@/services/api";
import { useNotificationsStore } from "@/stores/notifications";

const router = useRouter();
const notifications = useNotificationsStore();
const currentStep = ref(0);

const totalSteps = 5;

// Step 1: Dietary restrictions
const dietaryPresets = [
  { type: "diet", value: "Vegetarian" },
  { type: "diet", value: "Vegan" },
  { type: "diet", value: "Keto" },
  { type: "diet", value: "Paleo" },
  { type: "diet", value: "Mediterranean" },
  { type: "diet", value: "Pescatarian" },
  { type: "allergy", value: "Peanuts" },
  { type: "allergy", value: "Tree Nuts" },
  { type: "allergy", value: "Dairy" },
  { type: "allergy", value: "Eggs" },
  { type: "allergy", value: "Gluten" },
  { type: "allergy", value: "Shellfish" },
  { type: "allergy", value: "Soy" },
  { type: "intolerance", value: "Lactose" },
  { type: "religious", value: "Halal" },
  { type: "religious", value: "Kosher" },
];
const selectedDietary = ref<Set<string>>(new Set());

function toggleDietary(key: string): void {
  if (selectedDietary.value.has(key)) {
    selectedDietary.value.delete(key);
  } else {
    selectedDietary.value.add(key);
  }
}

// Step 2: Health goals
const healthGoalPresets = [
  { type: "weight_loss", label: "Lose weight" },
  { type: "weight_gain", label: "Gain weight" },
  { type: "lower_cholesterol", label: "Lower cholesterol" },
  { type: "reduce_sodium", label: "Reduce sodium" },
  { type: "increase_protein", label: "More protein" },
  { type: "increase_fiber", label: "More fiber" },
  { type: "general_health", label: "General health" },
];
const selectedGoals = ref<Set<string>>(new Set());

function toggleGoal(type: string): void {
  if (selectedGoals.value.has(type)) {
    selectedGoals.value.delete(type);
  } else {
    selectedGoals.value.add(type);
  }
}

// Step 3: Household info
const householdMembers = ref<string[]>([]);
const newMemberName = ref("");

function addMember(): void {
  const name = newMemberName.value.trim();
  if (name) {
    householdMembers.value.push(name);
    newMemberName.value = "";
  }
}

function removeMember(index: number): void {
  householdMembers.value.splice(index, 1);
}

// Navigation
const saving = ref(false);

async function nextStep(): Promise<void> {
  if (currentStep.value < totalSteps - 1) {
    currentStep.value++;
  }
}

function prevStep(): void {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
}

async function finishOnboarding(): Promise<void> {
  saving.value = true;
  try {
    // Save dietary preferences
    for (const key of selectedDietary.value) {
      const preset = dietaryPresets.find((p) => `${p.type}:${p.value}` === key);
      if (preset) {
        await usersApi.addDietaryPreference({
          preference_type: preset.type,
          value: preset.value,
        });
      }
    }

    // Save health goals
    for (const type of selectedGoals.value) {
      const preset = healthGoalPresets.find((g) => g.type === type);
      if (preset) {
        await usersApi.addHealthGoal({
          goal_type: type,
          description: preset.label,
        });
      }
    }

    notifications.success("Profile set up successfully!");
    await router.push("/");
  } catch {
    notifications.error("Some preferences could not be saved. You can update them later in Profile.");
    await router.push("/");
  } finally {
    saving.value = false;
  }
}

async function skip(): Promise<void> {
  await router.push("/");
}
</script>

<template>
  <div class="onboarding">
    <!-- Progress bar -->
    <div class="progress-bar" role="progressbar" :aria-valuenow="currentStep + 1" :aria-valuemax="totalSteps">
      <div class="progress-fill" :style="{ width: `${((currentStep + 1) / totalSteps) * 100}%` }" />
    </div>
    <p class="step-indicator">Step {{ currentStep + 1 }} of {{ totalSteps }}</p>

    <!-- Step 0: Welcome -->
    <div v-if="currentStep === 0" class="step">
      <h1>Welcome to Companis!</h1>
      <p class="step-desc">
        Let's set up your eating profile so we can recommend recipes tailored to you.
        This only takes a minute, and you can always change these later.
      </p>
      <div class="step-actions">
        <button class="btn-primary" type="button" @click="nextStep">Get Started</button>
        <button class="skip-btn" type="button" @click="skip">Skip for now</button>
      </div>
    </div>

    <!-- Step 1: Dietary restrictions -->
    <div v-if="currentStep === 1" class="step">
      <h2>Dietary Preferences & Restrictions</h2>
      <p class="step-desc">Select any that apply to you. This helps us filter recipes and warn about allergens.</p>
      <div class="chip-grid">
        <button
          v-for="preset in dietaryPresets"
          :key="`${preset.type}:${preset.value}`"
          type="button"
          class="chip-btn"
          :class="{
            selected: selectedDietary.has(`${preset.type}:${preset.value}`),
            allergy: preset.type === 'allergy',
          }"
          :aria-pressed="selectedDietary.has(`${preset.type}:${preset.value}`)"
          @click="toggleDietary(`${preset.type}:${preset.value}`)"
        >
          {{ preset.value }}
          <span class="chip-type">{{ preset.type }}</span>
        </button>
      </div>
    </div>

    <!-- Step 2: Health goals -->
    <div v-if="currentStep === 2" class="step">
      <h2>Health Goals</h2>
      <p class="step-desc">What are you working towards? We'll prioritize recipes that support your goals.</p>
      <div class="chip-grid">
        <button
          v-for="goal in healthGoalPresets"
          :key="goal.type"
          type="button"
          class="chip-btn"
          :class="{ selected: selectedGoals.has(goal.type) }"
          :aria-pressed="selectedGoals.has(goal.type)"
          @click="toggleGoal(goal.type)"
        >
          {{ goal.label }}
        </button>
      </div>
    </div>

    <!-- Step 3: Household -->
    <div v-if="currentStep === 3" class="step">
      <h2>Your Household</h2>
      <p class="step-desc">
        Add family members so you can share pantry items and plan meals together. You can also add them later.
      </p>
      <form class="member-form" @submit.prevent="addMember">
        <input
          v-model="newMemberName"
          type="text"
          placeholder="Family member name"
          autocomplete="off"
        />
        <button class="btn-primary" type="submit" :disabled="!newMemberName.trim()">Add</button>
      </form>
      <div v-if="householdMembers.length" class="member-list">
        <div v-for="(member, i) in householdMembers" :key="i" class="member-item">
          <span>{{ member }}</span>
          <button type="button" class="remove-btn" aria-label="Remove member" @click="removeMember(i)">&times;</button>
        </div>
      </div>
      <p v-else class="empty-hint">No additional members added yet.</p>
    </div>

    <!-- Step 4: Finish -->
    <div v-if="currentStep === 4" class="step">
      <h2>All Set!</h2>
      <p class="step-desc">
        Here's a summary of your profile. You can always update these in your Profile settings.
      </p>
      <div class="summary card">
        <div v-if="selectedDietary.size" class="summary-section">
          <strong>Dietary:</strong>
          <span v-for="key in selectedDietary" :key="key" class="summary-chip">
            {{ key.split(":")[1] }}
          </span>
        </div>
        <div v-if="selectedGoals.size" class="summary-section">
          <strong>Goals:</strong>
          <span v-for="type in selectedGoals" :key="type" class="summary-chip">
            {{ healthGoalPresets.find((g) => g.type === type)?.label }}
          </span>
        </div>
        <div v-if="householdMembers.length" class="summary-section">
          <strong>Household:</strong>
          <span v-for="m in householdMembers" :key="m" class="summary-chip">{{ m }}</span>
        </div>
        <p v-if="!selectedDietary.size && !selectedGoals.size && !householdMembers.length" class="empty-hint">
          No preferences set. You can add them anytime from your Profile.
        </p>
      </div>
      <div class="step-actions">
        <button class="btn-primary" type="button" :disabled="saving" @click="finishOnboarding">
          {{ saving ? "Saving..." : "Start Cooking!" }}
        </button>
      </div>
    </div>

    <!-- Navigation buttons (steps 1-3) -->
    <div v-if="currentStep > 0 && currentStep < 4" class="nav-actions">
      <button class="nav-btn" type="button" @click="prevStep">Back</button>
      <button class="btn-primary" type="button" @click="nextStep">
        {{ currentStep === 3 ? "Review" : "Next" }}
      </button>
      <button class="skip-btn" type="button" @click="skip">Skip all</button>
    </div>
  </div>
</template>

<style scoped>
.onboarding {
  max-width: 500px;
  margin: 0 auto;
  padding: 1rem;
}

.progress-bar {
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: var(--primary);
  transition: width 0.3s ease;
}

.step-indicator {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 1.5rem;
}

.step h1 {
  font-size: 1.75rem;
  color: var(--primary);
  margin-bottom: 0.75rem;
}

.step h2 {
  font-size: 1.375rem;
  margin-bottom: 0.5rem;
}

.step-desc {
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.chip-btn {
  padding: 0.5rem 1rem;
  border: 2px solid var(--border);
  border-radius: 20px;
  background: var(--surface);
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-primary);
  min-height: 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.125rem;
}

.chip-btn .chip-type {
  font-size: 0.6875rem;
  color: var(--text-secondary);
  text-transform: capitalize;
}

.chip-btn.selected {
  border-color: var(--primary);
  background: var(--primary-light);
  color: var(--primary-dark);
}

.chip-btn.allergy.selected {
  border-color: var(--error);
  background: #ffebee;
  color: var(--error);
}

.member-form {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.member-form input {
  flex: 1;
}

.member-list {
  margin-bottom: 1rem;
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
}

.remove-btn {
  background: none;
  color: var(--error);
  font-size: 1.5rem;
  padding: 0.25rem 0.5rem;
  min-height: 44px;
  min-width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-hint {
  color: var(--text-secondary);
  font-size: 0.875rem;
  text-align: center;
  padding: 1rem;
}

.summary-section {
  margin-bottom: 0.75rem;
}

.summary-section strong {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.summary-chip {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: var(--primary-light);
  color: var(--primary-dark);
  border-radius: 12px;
  font-size: 0.8125rem;
  margin: 0.125rem;
}

.step-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1rem;
}

.step-actions .btn-primary {
  width: 100%;
}

.nav-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1.5rem;
  align-items: center;
}

.nav-actions .btn-primary {
  flex: 1;
}

.nav-btn {
  padding: 0.75rem 1.25rem;
  background: var(--surface);
  border: 1px solid var(--border);
  font-weight: 500;
  min-height: 44px;
}

.skip-btn {
  background: none;
  color: var(--text-secondary);
  font-size: 0.875rem;
  text-decoration: underline;
  padding: 0.5rem;
  min-height: 44px;
}
</style>
