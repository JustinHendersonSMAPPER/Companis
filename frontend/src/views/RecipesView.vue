<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRecipesStore } from "@/stores/recipes";
import { useShoppingStore } from "@/stores/shopping";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import VoiceInput from "@/components/common/VoiceInput.vue";

const recipesStore = useRecipesStore();
const shoppingStore = useShoppingStore();

const activeTab = ref<"search" | "favorites">("search");
const prompt = ref("");
const maxPrepTime = ref<number | undefined>(undefined);
const cuisine = ref("");

onMounted(() => {
  void recipesStore.fetchFavorites();
});

async function searchRecipes(): Promise<void> {
  if (!prompt.value.trim()) return;
  try {
    await recipesStore.searchRecipes({
      prompt: prompt.value,
      max_prep_time_minutes: maxPrepTime.value,
      cuisine: cuisine.value || undefined,
    });
  } catch {
    // Error handled by store
  }
}

function handleVoiceTranscript(transcript: string): void {
  prompt.value = transcript;
  void searchRecipes();
}

async function addToShoppingList(recipeId: string): Promise<void> {
  const missing = recipesStore.missingIngredients[recipeId];
  if (missing?.length) {
    await shoppingStore.addMissingIngredients(recipeId, missing);
  }
}
</script>

<template>
  <div class="recipes-view">
    <h1>Recipes</h1>

    <div class="tab-bar" role="tablist" aria-label="Recipe tabs">
      <button
        class="tab"
        :class="{ active: activeTab === 'search' }"
        type="button"
        role="tab"
        :aria-selected="activeTab === 'search'"
        @click="activeTab = 'search'"
      >
        Search
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'favorites' }"
        type="button"
        role="tab"
        :aria-selected="activeTab === 'favorites'"
        @click="activeTab = 'favorites'"
      >
        Favorites ({{ recipesStore.favorites.length }})
      </button>
    </div>

    <!-- Search Tab -->
    <div v-if="activeTab === 'search'">
      <div class="search-card card">
        <form @submit.prevent="searchRecipes">
          <div class="form-group">
            <textarea
              v-model="prompt"
              placeholder="What are you in the mood for? Type or use voice input..."
              rows="3"
            />
          </div>
          <div class="search-filters">
            <input
              v-model.number="maxPrepTime"
              type="number"
              placeholder="Max prep (min)"
              min="1"
            />
            <input v-model="cuisine" type="text" placeholder="Cuisine" />
          </div>
          <div class="search-actions">
            <button
              class="btn-primary"
              type="submit"
              :disabled="recipesStore.loading"
              style="flex: 1"
            >
              {{ recipesStore.loading ? "Searching..." : "Search" }}
            </button>
            <VoiceInput @transcript="handleVoiceTranscript" />
          </div>
        </form>
      </div>

      <LoadingSpinner v-if="recipesStore.loading" message="Finding recipes..." />

      <div
        v-for="recipe in recipesStore.searchResults"
        :key="recipe.id"
        class="recipe-card card"
      >
        <router-link :to="`/recipes/${recipe.id}`" class="recipe-link">
          <h3>{{ recipe.title }}</h3>
          <div class="recipe-meta">
            <span v-if="recipe.cuisine">{{ recipe.cuisine }}</span>
            <span v-if="recipe.prep_time_minutes">{{ recipe.prep_time_minutes }}min</span>
            <span v-if="recipe.servings">{{ recipe.servings }} servings</span>
            <span v-if="recipe.calorie_estimate">~{{ recipe.calorie_estimate }} cal</span>
          </div>
          <p v-if="recipe.description" class="recipe-desc">{{ recipe.description }}</p>
        </router-link>

        <div class="recipe-actions">
          <button
            class="action-btn"
            type="button"
            @click="recipesStore.toggleFavorite(recipe.id)"
          >
            {{ recipe.is_favorite ? "Unfavorite" : "Favorite" }}
          </button>
          <button
            v-if="recipesStore.missingIngredients[recipe.id]?.length"
            class="action-btn shop"
            type="button"
            @click="addToShoppingList(recipe.id)"
          >
            Add missing to cart
          </button>
        </div>

        <div v-if="recipesStore.substitutions[recipe.id]?.length" class="substitution-notice">
          <strong>Substitutions available:</strong>
          <ul>
            <li v-for="sub in recipesStore.substitutions[recipe.id]" :key="sub.original_ingredient">
              {{ sub.original_ingredient }} → {{ sub.substitute }}
              <span v-if="sub.notes"> ({{ sub.notes }})</span>
            </li>
          </ul>
        </div>

        <div v-if="recipesStore.missingIngredients[recipe.id]?.length" class="missing-notice">
          <strong>Missing ingredients:</strong>
          {{ recipesStore.missingIngredients[recipe.id]?.join(", ") }}
        </div>
      </div>
    </div>

    <!-- Favorites Tab -->
    <div v-if="activeTab === 'favorites'">
      <div v-if="recipesStore.favorites.length === 0" class="empty-state">
        <p>No favorite recipes yet. Search for recipes and save your favorites!</p>
      </div>
      <div
        v-for="recipe in recipesStore.favorites"
        :key="recipe.id"
        class="recipe-card card"
      >
        <router-link :to="`/recipes/${recipe.id}`" class="recipe-link">
          <h3>{{ recipe.title }}</h3>
          <div class="recipe-meta">
            <span v-if="recipe.cuisine">{{ recipe.cuisine }}</span>
            <span v-if="recipe.prep_time_minutes">{{ recipe.prep_time_minutes }}min</span>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tab-bar {
  display: flex;
  gap: 0.5rem;
  margin: 1rem 0;
}

.tab {
  flex: 1;
  padding: 0.75rem;
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  font-weight: 500;
  color: var(--text-secondary);
}

.tab.active {
  border-color: var(--primary);
  color: var(--primary);
}

.search-filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.search-filters input {
  flex: 1;
}

.search-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.recipe-card {
  padding: 1rem;
}

.recipe-link {
  text-decoration: none;
  color: inherit;
}

.recipe-link h3 {
  color: var(--primary-dark);
  margin-bottom: 0.25rem;
}

.recipe-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.recipe-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.recipe-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.action-btn {
  padding: 0.5rem 0.75rem;
  background: var(--border);
  font-size: 0.8125rem;
  font-weight: 500;
  min-height: 44px;
}

.action-btn.shop {
  background: var(--secondary);
  color: white;
}

.substitution-notice {
  margin-top: 0.75rem;
  padding: 0.5rem;
  background: #fff3e0;
  border-radius: var(--radius);
  font-size: 0.8125rem;
}

.substitution-notice ul {
  margin-top: 0.25rem;
  padding-left: 1.5rem;
}

.missing-notice {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #ffebee;
  border-radius: var(--radius);
  font-size: 0.8125rem;
  color: var(--error);
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}
</style>
