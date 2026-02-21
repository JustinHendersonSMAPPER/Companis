import { describe, it, expect } from 'vitest'
import type {
  User,
  TokenResponse,
  DietaryPreference,
  HealthGoal,
  Ingredient,
  HouseholdIngredient,
  Recipe,
  RecipeSearchResponse,
  Household,
  FamilyMember,
  ShoppingCart,
  ShoppingCartItem,
  BarcodeScanResult,
  CameraScanResult,
  VoiceInputResult,
} from '@/types'

describe('test setup', () => {
  it('works', () => {
    expect(1 + 1).toBe(2)
  })

  it('localStorage mock works', () => {
    localStorage.setItem('key', 'value')
    expect(localStorage.getItem('key')).toBe('value')
    localStorage.removeItem('key')
    expect(localStorage.getItem('key')).toBeNull()
  })
})

describe('TypeScript interfaces', () => {
  it('User interface is correct', () => {
    const user: User = {
      id: 'u1',
      email: 'test@example.com',
      full_name: 'Test',
      avatar_url: null,
      auth_provider: 'local',
      is_active: true,
      is_verified: false,
      created_at: '2024-01-01',
    }
    expect(user.id).toBe('u1')
    expect(user.is_active).toBe(true)
  })

  it('TokenResponse interface is correct', () => {
    const token: TokenResponse = {
      access_token: 'at',
      refresh_token: 'rt',
      token_type: 'bearer',
    }
    expect(token.token_type).toBe('bearer')
  })

  it('Recipe interface is correct', () => {
    const recipe: Recipe = {
      id: 'r1',
      title: 'Pasta',
      description: null,
      instructions: 'Cook',
      cuisine: null,
      meal_type: null,
      prep_time_minutes: null,
      cook_time_minutes: null,
      servings: null,
      difficulty: null,
      image_url: null,
      source: 'ai',
      dietary_tags: null,
      calorie_estimate: null,
      created_at: '2024-01-01',
      recipe_ingredients: [],
      is_favorite: false,
    }
    expect(recipe.title).toBe('Pasta')
  })

  it('RecipeSearchResponse interface is correct', () => {
    const response: RecipeSearchResponse = {
      recipes: [],
      missing_ingredients: {},
      substitutions: {},
    }
    expect(response.recipes).toEqual([])
  })

  it('ShoppingCart interface is correct', () => {
    const cart: ShoppingCart = {
      id: 'c1',
      household_id: 'h1',
      name: 'Shopping',
      is_active: true,
      created_at: '2024-01-01',
      items: [],
    }
    expect(cart.is_active).toBe(true)
  })

  it('BarcodeScanResult interface is correct', () => {
    const result: BarcodeScanResult = {
      barcode: '123',
      ingredient: null,
      product_name: null,
      brand: null,
      found: false,
    }
    expect(result.found).toBe(false)
  })

  it('CameraScanResult interface is correct', () => {
    const result: CameraScanResult = {
      detected_ingredients: ['tomato'],
      confidence_scores: { tomato: 0.9 },
    }
    expect(result.detected_ingredients).toContain('tomato')
  })

  it('VoiceInputResult interface is correct', () => {
    const result: VoiceInputResult = {
      ingredients: [{ name: 'flour', quantity: 2, unit: 'cups' }],
    }
    expect(result.ingredients).toHaveLength(1)
  })

  it('HouseholdIngredient interface is correct', () => {
    const item: HouseholdIngredient = {
      id: 'hi1',
      household_id: 'h1',
      ingredient_id: 'i1',
      quantity: 1,
      unit: 'kg',
      expiry_date: null,
      source: 'manual',
      created_at: '2024-01-01',
      ingredient: {
        id: 'i1',
        name: 'Flour',
        category: null,
        barcode: null,
        brand: null,
        description: null,
        image_url: null,
        nutrition_info: null,
        common_allergens: null,
        created_at: '2024-01-01',
      },
    }
    expect(item.ingredient.name).toBe('Flour')
  })

  it('DietaryPreference interface is correct', () => {
    const pref: DietaryPreference = {
      id: 'dp1',
      preference_type: 'allergy',
      value: 'gluten',
      notes: null,
      created_at: '2024-01-01',
    }
    expect(pref.value).toBe('gluten')
  })

  it('Household and FamilyMember interfaces are correct', () => {
    const household: Household = {
      id: 'h1',
      name: 'Test Kitchen',
      owner_id: 'u1',
      created_at: '2024-01-01',
    }
    const member: FamilyMember = {
      id: 'fm1',
      household_id: 'h1',
      user_id: 'u1',
      name: 'Test',
      role: 'owner',
      dietary_notes: null,
      created_at: '2024-01-01',
    }
    expect(household.name).toBe('Test Kitchen')
    expect(member.role).toBe('owner')
  })

  it('HealthGoal and ShoppingCartItem interfaces are correct', () => {
    const goal: HealthGoal = {
      id: 'hg1',
      goal_type: 'weight_loss',
      description: 'Lose weight',
      target_value: '70kg',
      created_at: '2024-01-01',
    }
    const item: ShoppingCartItem = {
      id: 'si1',
      name: 'Milk',
      quantity: 1,
      unit: 'L',
      notes: null,
      is_purchased: false,
      added_from_recipe_id: null,
      created_at: '2024-01-01',
    }
    expect(goal.goal_type).toBe('weight_loss')
    expect(item.is_purchased).toBe(false)
  })
})
