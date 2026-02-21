<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useRecipesStore } from "@/stores/recipes";
import { useIngredientsStore } from "@/stores/ingredients";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import VoiceInput from "@/components/common/VoiceInput.vue";

const authStore = useAuthStore();
const recipesStore = useRecipesStore();
const ingredientsStore = useIngredientsStore();

const prompt = ref("");
const maxPrepTime = ref<number | undefined>(undefined);
const cuisine = ref("");
const searching = ref(false);

onMounted(() => {
  void ingredientsStore.fetchHouseholdIngredients();
});

async function searchRecipes(): Promise<void> {
  if (!prompt.value.trim()) return;
  searching.value = true;
  try {
    await recipesStore.searchRecipes({
      prompt: prompt.value,
      max_prep_time_minutes: maxPrepTime.value,
      cuisine: cuisine.value || undefined,
    });
  } catch {
    // Error handled by store
  } finally {
    searching.value = false;
  }
}

function handleVoiceTranscript(transcript: string): void {
  prompt.value = transcript;
  void searchRecipes();
}
</script>

<template>
  <div class="home">
    <header class="home-header">
      <h1>Hello, {{ authStore.user?.full_name?.split(" ")[0] ?? "Chef" }}!</h1>
      <p class="subtitle">What would you like to cook today?</p>
    </header>

    <div class="search-section card">
      <form @submit.prevent="searchRecipes">
        <div class="form-group">
          <textarea
            v-model="prompt"
            placeholder="Describe what you're in the mood for... e.g., 'Help me find a thai recipe I can cook in less than 30 minutes'"
            rows="3"
          />
        </div>
        <div class="search-filters">
          <div class="form-group" style="flex: 1">
            <input
              v-model.number="maxPrepTime"
              type="number"
              placeholder="Max prep (min)"
              min="1"
            />
          </div>
          <div class="form-group" style="flex: 1">
            <input v-model="cuisine" type="text" placeholder="Cuisine type" />
          </div>
        </div>
        <div class="search-actions">
          <button class="btn-primary" type="submit" :disabled="searching" style="flex: 1">
            {{ searching ? "Finding recipes..." : "Find Recipes" }}
          </button>
          <VoiceInput @transcript="handleVoiceTranscript" />
        </div>
      </form>
    </div>

    <div v-if="searching" class="loading-section">
      <LoadingSpinner message="AI is finding the perfect recipes for you..." />
    </div>

    <div v-if="recipesStore.searchResults.length > 0" class="results-section">
      <h2>Recipe Suggestions</h2>
      <div v-for="recipe in recipesStore.searchResults" :key="recipe.id" class="recipe-card card">
        <router-link :to="`/recipes/${recipe.id}`" class="recipe-link">
          <h3>{{ recipe.title }}</h3>
          <p class="recipe-meta">
            <span v-if="recipe.cuisine">{{ recipe.cuisine }}</span>
            <span v-if="recipe.prep_time_minutes">{{ recipe.prep_time_minutes }} min prep</span>
            <span v-if="recipe.difficulty">{{ recipe.difficulty }}</span>
          </p>
          <p v-if="recipe.description" class="recipe-desc">{{ recipe.description }}</p>
        </router-link>

        <div v-if="recipesStore.missingIngredients[recipe.id]?.length" class="missing-section">
          <p class="missing-label">Missing ingredients:</p>
          <div class="missing-chips">
            <span
              v-for="ing in recipesStore.missingIngredients[recipe.id]"
              :key="ing"
              class="chip missing"
            >
              {{ ing }}
            </span>
          </div>
        </div>

        <div v-if="recipesStore.substitutions[recipe.id]?.length" class="sub-section">
          <p class="sub-label">Substitutions available:</p>
          <div
            v-for="sub in recipesStore.substitutions[recipe.id]"
            :key="sub.original_ingredient"
            class="sub-item"
          >
            {{ sub.original_ingredient }} → {{ sub.substitute }}
          </div>
        </div>
      </div>
    </div>

    <div class="quick-stats">
      <div class="stat card">
        <span class="stat-number">{{ ingredientsStore.householdIngredients.length }}</span>
        <span class="stat-label">Items in pantry</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-header {
  margin-bottom: 1.5rem;
}

.home-header h1 {
  font-size: 1.75rem;
}

.subtitle {
  color: var(--text-secondary);
}

.search-filters {
  display: flex;
  gap: 0.5rem;
}

.search-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.full-width {
  width: 100%;
}

.results-section {
  margin-top: 1.5rem;
}

.results-section h2 {
  margin-bottom: 1rem;
}

.recipe-card {
  cursor: pointer;
}

.recipe-link {
  text-decoration: none;
  color: inherit;
}

.recipe-link h3 {
  color: var(--primary-dark);
  margin-bottom: 0.5rem;
}

.recipe-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.recipe-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.missing-section,
.sub-section {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border);
}

.missing-label,
.sub-label {
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.missing-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.chip {
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
}

.chip.missing {
  background: #ffebee;
  color: var(--error);
}

.sub-item {
  font-size: 0.8rem;
  color: var(--secondary);
  padding: 0.125rem 0;
}

.quick-stats {
  margin-top: 1.5rem;
  display: flex;
  gap: 1rem;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary);
}

.stat-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.loading-section {
  margin-top: 2rem;
}
</style>
