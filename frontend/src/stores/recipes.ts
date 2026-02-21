import { defineStore } from "pinia";
import { ref } from "vue";
import type { Recipe, RecipeSearchResponse, SubstitutionSuggestion } from "@/types";
import { recipesApi } from "@/services/api";

export const useRecipesStore = defineStore("recipes", () => {
  const searchResults = ref<Recipe[]>([]);
  const missingIngredients = ref<Record<string, string[]>>({});
  const substitutions = ref<Record<string, SubstitutionSuggestion[]>>({});
  const favorites = ref<Recipe[]>([]);
  const currentRecipe = ref<Recipe | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function searchRecipes(params: {
    prompt: string;
    max_results?: number;
    prefer_available_ingredients?: boolean;
    max_prep_time_minutes?: number;
    cuisine?: string;
    dietary_filter?: string[];
  }): Promise<RecipeSearchResponse> {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await recipesApi.search(params);
      searchResults.value = data.recipes;
      missingIngredients.value = data.missing_ingredients;
      substitutions.value = data.substitutions;
      return data;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error.value = err.response?.data?.detail ?? "Recipe search failed";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function getRecipe(id: string): Promise<Recipe> {
    loading.value = true;
    try {
      const { data } = await recipesApi.getById(id);
      currentRecipe.value = data;
      return data;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error.value = err.response?.data?.detail ?? "Failed to get recipe";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function rateRecipe(id: string, score: number, review?: string): Promise<void> {
    await recipesApi.rate(id, { score, review });
    if (currentRecipe.value?.id === id) {
      currentRecipe.value.user_rating = score;
    }
  }

  async function toggleFavorite(id: string): Promise<void> {
    const recipe = searchResults.value.find((r) => r.id === id) ?? currentRecipe.value;
    if (recipe?.is_favorite) {
      await recipesApi.removeFavorite(id);
      if (recipe) recipe.is_favorite = false;
      favorites.value = favorites.value.filter((f) => f.id !== id);
    } else {
      await recipesApi.addFavorite(id);
      if (recipe) recipe.is_favorite = true;
    }
  }

  async function fetchFavorites(): Promise<void> {
    const { data } = await recipesApi.getFavorites();
    favorites.value = data;
  }

  return {
    searchResults,
    missingIngredients,
    substitutions,
    favorites,
    currentRecipe,
    loading,
    error,
    searchRecipes,
    getRecipe,
    rateRecipe,
    toggleFavorite,
    fetchFavorites,
  };
});
