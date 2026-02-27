import axios from "axios";
import type {
  BarcodeScanResult,
  CameraScanResult,
  DietaryPreference,
  FamilyMember,
  HealthGoal,
  Household,
  HouseholdIngredient,
  Ingredient,
  Recipe,
  RecipeSearchResponse,
  ShoppingCart,
  ShoppingCartItem,
  TokenResponse,
  User,
  VoiceInputResult,
} from "@/types";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as { _retry?: boolean; headers: Record<string, string> };
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post<TokenResponse>("/api/auth/refresh", {
            refresh_token: refreshToken,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  },
);

// Auth
export const authApi = {
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    terms_accepted: boolean;
  }) => api.post<User>("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post<TokenResponse>("/auth/login", data),
  refresh: (refresh_token: string) =>
    api.post<TokenResponse>("/auth/refresh", { refresh_token }),
  getTerms: () => api.get<{ terms_text: string; version: string }>("/auth/terms"),
  getOAuthUrl: (provider: string) =>
    api.get<{ authorization_url: string }>(`/auth/oauth/${provider}/url`),
  oauthCallback: (provider: string, code: string) =>
    api.post<TokenResponse>(`/auth/oauth/${provider}/callback`, null, { params: { code } }),
};

// Users
export const usersApi = {
  getMe: () => api.get<User>("/users/me"),
  updateMe: (data: { full_name?: string; avatar_url?: string }) =>
    api.patch<User>("/users/me", data),
  getDietaryPreferences: () =>
    api.get<DietaryPreference[]>("/users/me/dietary-preferences"),
  addDietaryPreference: (data: { preference_type: string; value: string; notes?: string }) =>
    api.post<DietaryPreference>("/users/me/dietary-preferences", data),
  removeDietaryPreference: (id: string) =>
    api.delete(`/users/me/dietary-preferences/${id}`),
  getHealthGoals: () => api.get<HealthGoal[]>("/users/me/health-goals"),
  addHealthGoal: (data: { goal_type: string; description: string; target_value?: string }) =>
    api.post<HealthGoal>("/users/me/health-goals", data),
  removeHealthGoal: (id: string) => api.delete(`/users/me/health-goals/${id}`),
};

// Ingredients
export const ingredientsApi = {
  search: (q: string) => api.get<Ingredient[]>("/ingredients/search", { params: { q } }),
  create: (data: { name: string; category?: string; barcode?: string }) =>
    api.post<Ingredient>("/ingredients/", data),
  getHousehold: () => api.get<HouseholdIngredient[]>("/ingredients/household"),
  addToHousehold: (data: {
    ingredient_id?: string;
    name?: string;
    barcode?: string;
    quantity?: number;
    unit?: string;
    source?: string;
  }) => api.post<HouseholdIngredient>("/ingredients/household", data),
  updateHousehold: (id: string, data: { quantity?: number; unit?: string }) =>
    api.patch<HouseholdIngredient>(`/ingredients/household/${id}`, data),
  removeFromHousehold: (id: string) => api.delete(`/ingredients/household/${id}`),
  scanBarcode: (barcode: string) =>
    api.get<BarcodeScanResult>(`/ingredients/barcode/${barcode}`),
  cameraScan: (image_base64: string) =>
    api.post<CameraScanResult>("/ingredients/camera-scan", { image_base64 }),
};

// Recipes
export const recipesApi = {
  search: (data: {
    prompt: string;
    max_results?: number;
    prefer_available_ingredients?: boolean;
    max_prep_time_minutes?: number;
    cuisine?: string;
    dietary_filter?: string[];
  }) => api.post<RecipeSearchResponse>("/recipes/search", data),
  getById: (id: string) => api.get<Recipe>(`/recipes/${id}`),
  rate: (id: string, data: { score: number; review?: string }) =>
    api.post(`/recipes/${id}/rate`, data),
  addFavorite: (id: string) => api.post(`/recipes/${id}/favorite`),
  removeFavorite: (id: string) => api.delete(`/recipes/${id}/favorite`),
  getFavorites: () => api.get<Recipe[]>("/recipes/favorites/list"),
};

// Household
export const householdApi = {
  get: () => api.get<Household>("/household/"),
  create: (data: { name: string }) => api.post<Household>("/household/", data),
  getMembers: () => api.get<FamilyMember[]>("/household/members"),
  addMember: (data: { name: string; role?: string; dietary_notes?: string }) =>
    api.post<FamilyMember>("/household/members", data),
  updateMember: (id: string, data: { name?: string; role?: string; dietary_notes?: string }) =>
    api.patch<FamilyMember>(`/household/members/${id}`, data),
  removeMember: (id: string) => api.delete(`/household/members/${id}`),
};

// Shopping
export const shoppingApi = {
  getCarts: () => api.get<ShoppingCart[]>("/shopping/"),
  createCart: (data: { name?: string }) => api.post<ShoppingCart>("/shopping/", data),
  addItem: (cartId: string, data: { name: string; quantity?: number; unit?: string }) =>
    api.post<ShoppingCartItem>(`/shopping/${cartId}/items`, data),
  updateItem: (
    cartId: string,
    itemId: string,
    data: { quantity?: number; is_purchased?: boolean },
  ) => api.patch<ShoppingCartItem>(`/shopping/${cartId}/items/${itemId}`, data),
  removeItem: (cartId: string, itemId: string) =>
    api.delete(`/shopping/${cartId}/items/${itemId}`),
  addMissingIngredients: (data: { recipe_id: string; ingredient_names: string[] }) =>
    api.post<ShoppingCartItem[]>("/shopping/add-missing-ingredients", data),
};

// Meal Plan
export const mealPlanApi = {
  getEntries: (startDate: string, endDate: string) =>
    api.get("/meal-plan/", { params: { start_date: startDate, end_date: endDate } }),
  create: (data: {
    recipe_id: string;
    meal_date: string;
    meal_type: string;
    servings?: number;
    notes?: string;
  }) => api.post("/meal-plan/", data),
  update: (id: string, data: { meal_date?: string; meal_type?: string; servings?: number; notes?: string }) =>
    api.put(`/meal-plan/${id}`, data),
  remove: (id: string) => api.delete(`/meal-plan/${id}`),
  generateShoppingList: (startDate: string, endDate: string) =>
    api.post("/meal-plan/generate-shopping-list", null, {
      params: { start_date: startDate, end_date: endDate },
    }),
};

// Cooking History
export const cookingHistoryApi = {
  log: (data: { recipe_id: string; servings_made?: number; notes?: string }) =>
    api.post("/cooking-history/", data),
  getHistory: (limit = 20, offset = 0) =>
    api.get("/cooking-history/", { params: { limit, offset } }),
};

// Collections
export const collectionsApi = {
  list: () => api.get("/collections/"),
  create: (data: { name: string; description?: string }) =>
    api.post("/collections/", data),
  get: (id: string) => api.get(`/collections/${id}`),
  addRecipe: (id: string, recipeId: string) =>
    api.post(`/collections/${id}/recipes`, { recipe_id: recipeId }),
  removeRecipe: (id: string, recipeId: string) =>
    api.delete(`/collections/${id}/recipes/${recipeId}`),
  remove: (id: string) => api.delete(`/collections/${id}`),
};

// AI
export const aiApi = {
  getProviders: () => api.get<{ current_provider: string; available_providers: string[] }>("/ai/providers"),
  parseVoiceInput: (transcript: string) =>
    api.post<VoiceInputResult>("/ai/parse-voice-input", null, { params: { transcript } }),
  suggestSubstitutions: (ingredient: string, restrictions?: string[]) =>
    api.post("/ai/suggest-substitutions", null, {
      params: { ingredient, dietary_restrictions: restrictions },
    }),
};

export default api;
