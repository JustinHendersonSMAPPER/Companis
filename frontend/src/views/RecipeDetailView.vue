<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useRecipesStore } from "@/stores/recipes";
import { useShoppingStore } from "@/stores/shopping";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";

const route = useRoute();
const recipesStore = useRecipesStore();
const shoppingStore = useShoppingStore();

const ratingScore = ref(0);
const ratingReview = ref("");

onMounted(() => {
  const id = route.params.id as string;
  void recipesStore.getRecipe(id);
});

async function submitRating(): Promise<void> {
  if (!recipesStore.currentRecipe || ratingScore.value === 0) return;
  await recipesStore.rateRecipe(
    recipesStore.currentRecipe.id,
    ratingScore.value,
    ratingReview.value || undefined,
  );
}

async function toggleFavorite(): Promise<void> {
  if (!recipesStore.currentRecipe) return;
  await recipesStore.toggleFavorite(recipesStore.currentRecipe.id);
}

async function addMissingToCart(): Promise<void> {
  if (!recipesStore.currentRecipe) return;
  const missing = recipesStore.currentRecipe.recipe_ingredients
    .filter((i) => i.is_available === false && !i.has_substitution)
    .map((i) => i.name);
  if (missing.length > 0) {
    await shoppingStore.addMissingIngredients(recipesStore.currentRecipe.id, missing);
  }
}

function setRating(score: number): void {
  ratingScore.value = score;
}
</script>

<template>
  <div class="recipe-detail">
    <LoadingSpinner v-if="recipesStore.loading" message="Loading recipe..." />

    <template v-else-if="recipesStore.currentRecipe">
      <div class="recipe-header">
        <h1>{{ recipesStore.currentRecipe.title }}</h1>
        <div class="recipe-meta">
          <span v-if="recipesStore.currentRecipe.cuisine">
            {{ recipesStore.currentRecipe.cuisine }}
          </span>
          <span v-if="recipesStore.currentRecipe.prep_time_minutes">
            {{ recipesStore.currentRecipe.prep_time_minutes }}min prep
          </span>
          <span v-if="recipesStore.currentRecipe.cook_time_minutes">
            {{ recipesStore.currentRecipe.cook_time_minutes }}min cook
          </span>
          <span v-if="recipesStore.currentRecipe.servings">
            {{ recipesStore.currentRecipe.servings }} servings
          </span>
          <span v-if="recipesStore.currentRecipe.difficulty">
            {{ recipesStore.currentRecipe.difficulty }}
          </span>
        </div>
        <div class="header-actions">
          <button class="action-btn" type="button" @click="toggleFavorite">
            {{ recipesStore.currentRecipe.is_favorite ? "Remove Favorite" : "Add to Favorites" }}
          </button>
        </div>
      </div>

      <p v-if="recipesStore.currentRecipe.description" class="description">
        {{ recipesStore.currentRecipe.description }}
      </p>

      <!-- Ingredients -->
      <div class="section card">
        <h2>Ingredients</h2>
        <ul class="ingredient-list">
          <li
            v-for="ing in recipesStore.currentRecipe.recipe_ingredients"
            :key="ing.name"
            class="ingredient-item"
            :class="{
              available: ing.is_available,
              missing: ing.is_available === false && !ing.has_substitution,
              substituted: ing.has_substitution,
            }"
          >
            <span>
              {{ ing.quantity ?? "" }} {{ ing.unit ?? "" }} {{ ing.name }}
              <em v-if="ing.is_optional"> (optional)</em>
            </span>
            <span v-if="ing.is_available" class="status-badge available">Have it</span>
            <span v-else-if="ing.has_substitution" class="status-badge sub">
              Sub: {{ ing.substitution_notes }}
            </span>
            <span v-else-if="ing.is_available === false" class="status-badge missing">
              Missing
            </span>
          </li>
        </ul>
        <button
          v-if="
            recipesStore.currentRecipe.recipe_ingredients.some(
              (i) => i.is_available === false && !i.has_substitution,
            )
          "
          class="btn-secondary"
          type="button"
          style="margin-top: 0.75rem"
          @click="addMissingToCart"
        >
          Add missing to shopping cart
        </button>
      </div>

      <!-- Instructions -->
      <div class="section card">
        <h2>Instructions</h2>
        <div class="instructions" v-text="recipesStore.currentRecipe.instructions" />
      </div>

      <!-- Rating -->
      <div class="section card">
        <h2>Rate This Recipe</h2>
        <div v-if="recipesStore.currentRecipe.average_rating" class="avg-rating">
          Average: {{ recipesStore.currentRecipe.average_rating.toFixed(1) }} / 5
        </div>
        <div class="star-rating">
          <button
            v-for="n in 5"
            :key="n"
            class="star"
            :class="{ active: n <= ratingScore }"
            type="button"
            @click="setRating(n)"
          >
            {{ n <= ratingScore ? "★" : "☆" }}
          </button>
        </div>
        <div class="form-group">
          <textarea v-model="ratingReview" placeholder="Leave a review (optional)" rows="2" />
        </div>
        <button
          class="btn-primary"
          type="button"
          :disabled="ratingScore === 0"
          @click="submitRating"
        >
          Submit Rating
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.recipe-header h1 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.recipe-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
}

.header-actions {
  margin-bottom: 1rem;
}

.action-btn {
  padding: 0.5rem 1rem;
  background: var(--border);
  font-weight: 500;
}

.description {
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.section {
  padding: 1rem;
}

.section h2 {
  margin-bottom: 0.75rem;
  font-size: 1.25rem;
}

.ingredient-list {
  list-style: none;
}

.ingredient-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}

.status-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.status-badge.available {
  background: #e8f5e9;
  color: var(--primary-dark);
}

.status-badge.missing {
  background: #ffebee;
  color: var(--error);
}

.status-badge.sub {
  background: #fff3e0;
  color: #e65100;
}

.instructions {
  white-space: pre-wrap;
  line-height: 1.6;
}

.avg-rating {
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.star-rating {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.star {
  font-size: 2rem;
  background: none;
  padding: 0;
  color: var(--border);
}

.star.active {
  color: var(--secondary);
}
</style>
