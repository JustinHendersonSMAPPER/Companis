export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url: string | null;
  auth_provider: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface DietaryPreference {
  id: string;
  preference_type: string;
  value: string;
  notes: string | null;
  created_at: string;
}

export interface HealthGoal {
  id: string;
  goal_type: string;
  description: string;
  target_value: string | null;
  created_at: string;
}

export interface Ingredient {
  id: string;
  name: string;
  category: string | null;
  barcode: string | null;
  brand: string | null;
  description: string | null;
  image_url: string | null;
  nutrition_info: string | null;
  common_allergens: string | null;
  created_at: string;
}

export interface HouseholdIngredient {
  id: string;
  household_id: string;
  ingredient_id: string;
  quantity: number | null;
  unit: string | null;
  expiry_date: string | null;
  source: string;
  created_at: string;
  ingredient: Ingredient;
}

export interface RecipeIngredient {
  name: string;
  quantity: number | null;
  unit: string | null;
  is_optional: boolean;
  substitution_notes: string | null;
  is_available?: boolean | null;
  has_substitution?: boolean | null;
}

export interface Recipe {
  id: string;
  title: string;
  description: string | null;
  instructions: string;
  cuisine: string | null;
  meal_type: string | null;
  prep_time_minutes: number | null;
  cook_time_minutes: number | null;
  servings: number | null;
  difficulty: string | null;
  image_url: string | null;
  source: string;
  dietary_tags: string | null;
  calorie_estimate: number | null;
  created_at: string;
  recipe_ingredients: RecipeIngredient[];
  average_rating?: number | null;
  user_rating?: number | null;
  is_favorite: boolean;
}

export interface RecipeSearchResponse {
  recipes: Recipe[];
  missing_ingredients: Record<string, string[]>;
  substitutions: Record<string, SubstitutionSuggestion[]>;
}

export interface SubstitutionSuggestion {
  original_ingredient: string;
  substitute: string;
  notes: string | null;
  ratio: string | null;
}

export interface Household {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
}

export interface FamilyMember {
  id: string;
  household_id: string;
  user_id: string | null;
  name: string;
  role: string;
  dietary_notes: string | null;
  created_at: string;
}

export interface ShoppingCart {
  id: string;
  household_id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  items: ShoppingCartItem[];
}

export interface ShoppingCartItem {
  id: string;
  name: string;
  quantity: number | null;
  unit: string | null;
  notes: string | null;
  is_purchased: boolean;
  added_from_recipe_id: string | null;
  created_at: string;
}

export interface BarcodeScanResult {
  barcode: string;
  ingredient: Ingredient | null;
  product_name: string | null;
  brand: string | null;
  found: boolean;
}

export interface CameraScanResult {
  detected_ingredients: string[];
  confidence_scores: Record<string, number>;
}

export interface ParsedIngredient {
  name: string;
  quantity: number | null;
  unit: string | null;
}

export interface VoiceInputResult {
  ingredients: ParsedIngredient[];
}

export interface MealPlanEntry {
  id: string;
  household_id: string;
  recipe_id: string;
  recipe_title?: string;
  meal_date: string;
  meal_type: string;
  servings: number;
  notes: string | null;
  created_by_user_id: string | null;
  created_at: string;
}

export interface CookingHistoryEntry {
  id: string;
  user_id: string;
  recipe_id: string;
  household_id: string;
  servings_made: number | null;
  notes: string | null;
  cooked_at: string;
  created_at: string;
}

export interface RecipeCollection {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface RecipeCollectionItem {
  id: string;
  collection_id: string;
  recipe_id: string;
  added_at: string;
}
