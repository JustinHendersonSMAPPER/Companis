<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useRecipesStore } from "@/stores/recipes";
import { useShoppingStore } from "@/stores/shopping";
import { useNotificationsStore } from "@/stores/notifications";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";

const route = useRoute();
const router = useRouter();
const recipesStore = useRecipesStore();
const shoppingStore = useShoppingStore();
const notifications = useNotificationsStore();

const ratingScore = ref(0);
const ratingReview = ref("");

onMounted(() => {
  const id = route.params.id as string;
  void recipesStore.getRecipe(id);
});

const recipe = computed(() => recipesStore.currentRecipe);

const instructionSteps = computed(() => {
  if (!recipe.value?.instructions) return [];
  return recipe.value.instructions
    .split(/\n+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .map((s) => s.replace(/^\d+[\.\)]\s*/, ""));
});

const completedSteps = ref<Set<number>>(new Set());

function toggleStep(index: number): void {
  if (completedSteps.value.has(index)) {
    completedSteps.value.delete(index);
  } else {
    completedSteps.value.add(index);
  }
}

async function submitRating(): Promise<void> {
  if (!recipe.value || ratingScore.value === 0) return;
  await recipesStore.rateRecipe(recipe.value.id, ratingScore.value, ratingReview.value || undefined);
  notifications.success("Rating submitted!");
}

async function toggleFavorite(): Promise<void> {
  if (!recipe.value) return;
  await recipesStore.toggleFavorite(recipe.value.id);
  notifications.success(recipe.value.is_favorite ? "Added to favorites" : "Removed from favorites");
}

async function addMissingToCart(): Promise<void> {
  if (!recipe.value) return;
  const missing = recipe.value.recipe_ingredients
    .filter((i) => i.is_available === false && !i.has_substitution)
    .map((i) => i.name);
  if (missing.length > 0) {
    await shoppingStore.addMissingIngredients(recipe.value.id, missing);
    notifications.success(`${missing.length} item(s) added to shopping cart`);
  }
}

function setRating(score: number): void {
  ratingScore.value = score;
}

function goBack(): void {
  router.back();
}
</script>

<template>
  <div class="recipe-detail">
    <button class="back-btn" type="button" aria-label="Go back" @click="goBack">
      &larr; Back
    </button>

    <LoadingSpinner v-if="recipesStore.loading" message="Loading recipe..." />

    <template v-else-if="recipe">
      <!-- Recipe Image -->
      <div v-if="recipe.image_url" class="recipe-image-container">
        <img :src="recipe.image_url" :alt="recipe.title" class="recipe-image" loading="lazy" />
      </div>

      <div class="recipe-header">
        <h1>{{ recipe.title }}</h1>
        <div class="recipe-meta">
          <span v-if="recipe.cuisine" class="meta-tag">{{ recipe.cuisine }}</span>
          <span v-if="recipe.prep_time_minutes" class="meta-tag">{{ recipe.prep_time_minutes }}min prep</span>
          <span v-if="recipe.cook_time_minutes" class="meta-tag">{{ recipe.cook_time_minutes }}min cook</span>
          <span v-if="recipe.servings" class="meta-tag">{{ recipe.servings }} servings</span>
          <span v-if="recipe.difficulty" class="meta-tag">{{ recipe.difficulty }}</span>
        </div>
        <div class="header-actions">
          <button
            class="action-btn"
            :class="{ favorited: recipe.is_favorite }"
            type="button"
            :aria-label="recipe.is_favorite ? 'Remove from favorites' : 'Add to favorites'"
            @click="toggleFavorite"
          >
            {{ recipe.is_favorite ? "★ Favorited" : "☆ Favorite" }}
          </button>
        </div>
      </div>

      <p v-if="recipe.description" class="description">{{ recipe.description }}</p>

      <!-- Nutrition summary -->
      <div v-if="recipe.calorie_estimate" class="nutrition-bar card">
        <span class="nutrition-label">Estimated calories:</span>
        <span class="nutrition-value">{{ recipe.calorie_estimate }} kcal per serving</span>
      </div>

      <!-- Ingredients -->
      <div class="section card">
        <h2>Ingredients</h2>
        <ul class="ingredient-list" role="list">
          <li
            v-for="ing in recipe.recipe_ingredients"
            :key="ing.name"
            class="ingredient-item"
            :class="{
              available: ing.is_available,
              missing: ing.is_available === false && !ing.has_substitution,
              substituted: ing.has_substitution,
            }"
          >
            <span class="ingredient-text">
              {{ ing.quantity ?? "" }} {{ ing.unit ?? "" }} {{ ing.name }}
              <em v-if="ing.is_optional"> (optional)</em>
            </span>
            <span v-if="ing.is_available" class="status-badge available" aria-label="Available in pantry">
              ✓ Have it
            </span>
            <span v-else-if="ing.has_substitution" class="status-badge sub" aria-label="Substitution available">
              ↔ Sub: {{ ing.substitution_notes }}
            </span>
            <span v-else-if="ing.is_available === false" class="status-badge missing" aria-label="Missing ingredient">
              ✕ Missing
            </span>
          </li>
        </ul>
        <button
          v-if="recipe.recipe_ingredients.some((i) => i.is_available === false && !i.has_substitution)"
          class="btn-secondary"
          type="button"
          style="margin-top: 0.75rem; width: 100%"
          @click="addMissingToCart"
        >
          Add missing to shopping cart
        </button>
      </div>

      <!-- Instructions -->
      <div class="section card">
        <h2>Instructions</h2>
        <ol v-if="instructionSteps.length > 1" class="instruction-steps" role="list">
          <li
            v-for="(step, i) in instructionSteps"
            :key="i"
            class="instruction-step"
            :class="{ completed: completedSteps.has(i) }"
          >
            <button
              type="button"
              class="step-check"
              :aria-label="`Mark step ${i + 1} as ${completedSteps.has(i) ? 'incomplete' : 'complete'}`"
              :aria-pressed="completedSteps.has(i)"
              @click="toggleStep(i)"
            >
              <span class="step-number">{{ completedSteps.has(i) ? "✓" : i + 1 }}</span>
            </button>
            <span class="step-text">{{ step }}</span>
          </li>
        </ol>
        <div v-else class="instructions-plain" v-text="recipe.instructions" />
      </div>

      <!-- Rating -->
      <div class="section card">
        <h2>Rate This Recipe</h2>
        <div v-if="recipe.average_rating" class="avg-rating">
          Average: {{ recipe.average_rating.toFixed(1) }} / 5
        </div>
        <div v-if="recipe.user_rating" class="user-rating-info">
          Your rating: {{ recipe.user_rating }} / 5
        </div>
        <div class="star-rating" role="group" aria-label="Rating">
          <button
            v-for="n in 5"
            :key="n"
            class="star"
            :class="{ active: n <= ratingScore }"
            type="button"
            :aria-label="`Rate ${n} out of 5 stars`"
            @click="setRating(n)"
          >
            {{ n <= ratingScore ? "★" : "☆" }}
          </button>
        </div>
        <div class="form-group">
          <textarea
            v-model="ratingReview"
            placeholder="Leave a review (optional)"
            rows="2"
            aria-label="Review text"
          />
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
.back-btn {
  background: none;
  color: var(--primary);
  padding: 0.5rem 0;
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 0.75rem;
  min-height: 44px;
}

.recipe-image-container {
  margin: 0 -1rem 1rem;
  overflow: hidden;
  border-radius: 0 0 var(--radius) var(--radius);
}

.recipe-image {
  width: 100%;
  height: auto;
  max-height: 280px;
  object-fit: cover;
  display: block;
}

@media (min-width: 768px) {
  .recipe-image-container {
    margin: 0 0 1rem;
    border-radius: var(--radius);
  }

  .recipe-image {
    max-height: 400px;
  }
}

.recipe-header h1 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.recipe-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.meta-tag {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  background: var(--background);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.header-actions {
  margin-bottom: 1rem;
}

.action-btn {
  padding: 0.5rem 1rem;
  background: var(--border);
  font-weight: 500;
  min-height: 44px;
}

.action-btn.favorited {
  background: var(--primary-light);
  color: var(--primary-dark);
}

.description {
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.nutrition-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #e8f5e9;
}

.nutrition-label {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.nutrition-value {
  font-weight: 600;
  color: var(--primary-dark);
  font-size: 0.9rem;
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
  gap: 0.5rem;
}

.ingredient-text {
  flex: 1;
}

.status-badge {
  font-size: 0.8125rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
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
  font-size: 0.75rem;
}

.instruction-steps {
  list-style: none;
  counter-reset: none;
}

.instruction-step {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border);
  align-items: flex-start;
}

.instruction-step.completed .step-text {
  text-decoration: line-through;
  color: var(--text-secondary);
}

.step-check {
  background: var(--background);
  border: 2px solid var(--border);
  border-radius: 50%;
  min-width: 32px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  min-height: auto;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.instruction-step.completed .step-check {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.step-number {
  font-size: 0.8125rem;
  font-weight: 600;
}

.step-text {
  line-height: 1.6;
}

.instructions-plain {
  white-space: pre-wrap;
  line-height: 1.6;
}

.avg-rating {
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.user-rating-info {
  color: var(--primary);
  font-weight: 500;
  font-size: 0.875rem;
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
  min-height: 44px;
  min-width: 44px;
}

.star.active {
  color: var(--secondary);
}
</style>
