import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRecipesStore } from '@/stores/recipes'

vi.mock('@/services/api', () => ({
  recipesApi: {
    search: vi.fn(),
    getById: vi.fn(),
    rate: vi.fn(),
    addFavorite: vi.fn(),
    removeFavorite: vi.fn(),
    getFavorites: vi.fn(),
  },
}))

import { recipesApi } from '@/services/api'

const mockRecipe = {
  id: 'r1',
  title: 'Test Pasta',
  description: 'Delicious pasta',
  instructions: 'Cook it',
  cuisine: 'Italian',
  meal_type: 'dinner',
  prep_time_minutes: 15,
  cook_time_minutes: 20,
  servings: 4,
  difficulty: 'easy',
  image_url: null,
  source: 'ai_generated',
  dietary_tags: 'vegetarian',
  calorie_estimate: 400,
  created_at: '2024-01-01',
  recipe_ingredients: [
    { name: 'pasta', quantity: 200, unit: 'g', is_optional: false, substitution_notes: null },
  ],
  is_favorite: false,
}

const mockSearchResponse = {
  recipes: [mockRecipe],
  missing_ingredients: { r1: ['olive oil'] },
  substitutions: {},
}

describe('useRecipesStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('has correct initial state', () => {
    const store = useRecipesStore()
    expect(store.searchResults).toEqual([])
    expect(store.missingIngredients).toEqual({})
    expect(store.substitutions).toEqual({})
    expect(store.favorites).toEqual([])
    expect(store.currentRecipe).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  describe('searchRecipes', () => {
    it('searches and stores results', async () => {
      vi.mocked(recipesApi.search).mockResolvedValue({ data: mockSearchResponse } as never)

      const store = useRecipesStore()
      const result = await store.searchRecipes({ prompt: 'pasta recipe' })

      expect(result).toEqual(mockSearchResponse)
      expect(store.searchResults).toEqual([mockRecipe])
      expect(store.missingIngredients).toEqual({ r1: ['olive oil'] })
      expect(store.loading).toBe(false)
    })

    it('sets error on failure', async () => {
      vi.mocked(recipesApi.search).mockRejectedValue({
        response: { data: { detail: 'AI unavailable' } },
      })

      const store = useRecipesStore()
      await expect(store.searchRecipes({ prompt: 'test' })).rejects.toBeTruthy()

      expect(store.error).toBe('AI unavailable')
      expect(store.loading).toBe(false)
    })

    it('uses fallback error message', async () => {
      vi.mocked(recipesApi.search).mockRejectedValue(new Error('network'))

      const store = useRecipesStore()
      await expect(store.searchRecipes({ prompt: 'test' })).rejects.toBeTruthy()

      expect(store.error).toBe('Recipe search failed')
    })
  })

  describe('getRecipe', () => {
    it('fetches and sets current recipe', async () => {
      vi.mocked(recipesApi.getById).mockResolvedValue({ data: mockRecipe } as never)

      const store = useRecipesStore()
      const result = await store.getRecipe('r1')

      expect(result).toEqual(mockRecipe)
      expect(store.currentRecipe).toEqual(mockRecipe)
      expect(store.loading).toBe(false)
    })

    it('sets error on failure', async () => {
      vi.mocked(recipesApi.getById).mockRejectedValue({
        response: { data: { detail: 'Not found' } },
      })

      const store = useRecipesStore()
      await expect(store.getRecipe('bad-id')).rejects.toBeTruthy()

      expect(store.error).toBe('Not found')
    })
  })

  describe('rateRecipe', () => {
    it('rates recipe and updates current recipe', async () => {
      vi.mocked(recipesApi.rate).mockResolvedValue({} as never)

      const store = useRecipesStore()
      store.currentRecipe = { ...mockRecipe }
      await store.rateRecipe('r1', 5, 'Great!')

      expect(recipesApi.rate).toHaveBeenCalledWith('r1', { score: 5, review: 'Great!' })
      expect(store.currentRecipe!.user_rating).toBe(5)
    })

    it('rates recipe without updating when no current recipe matches', async () => {
      vi.mocked(recipesApi.rate).mockResolvedValue({} as never)

      const store = useRecipesStore()
      store.currentRecipe = { ...mockRecipe, id: 'other' }
      await store.rateRecipe('r1', 4)

      expect(recipesApi.rate).toHaveBeenCalledWith('r1', { score: 4, review: undefined })
      expect(store.currentRecipe!.user_rating).toBeUndefined()
    })
  })

  describe('toggleFavorite', () => {
    it('removes favorite when already favorited', async () => {
      vi.mocked(recipesApi.removeFavorite).mockResolvedValue({} as never)

      const store = useRecipesStore()
      const favRecipe = { ...mockRecipe, is_favorite: true }
      store.searchResults = [favRecipe]
      store.favorites = [favRecipe]
      await store.toggleFavorite('r1')

      expect(recipesApi.removeFavorite).toHaveBeenCalledWith('r1')
      expect(favRecipe.is_favorite).toBe(false)
      expect(store.favorites).toHaveLength(0)
    })

    it('adds favorite when not favorited', async () => {
      vi.mocked(recipesApi.addFavorite).mockResolvedValue({} as never)

      const store = useRecipesStore()
      const recipe = { ...mockRecipe, is_favorite: false }
      store.searchResults = [recipe]
      await store.toggleFavorite('r1')

      expect(recipesApi.addFavorite).toHaveBeenCalledWith('r1')
      expect(recipe.is_favorite).toBe(true)
    })

    it('uses currentRecipe when not in search results', async () => {
      vi.mocked(recipesApi.addFavorite).mockResolvedValue({} as never)

      const store = useRecipesStore()
      store.currentRecipe = { ...mockRecipe, is_favorite: false }
      store.searchResults = []
      await store.toggleFavorite('r1')

      expect(recipesApi.addFavorite).toHaveBeenCalledWith('r1')
      expect(store.currentRecipe!.is_favorite).toBe(true)
    })
  })

  describe('fetchFavorites', () => {
    it('fetches and sets favorites list', async () => {
      vi.mocked(recipesApi.getFavorites).mockResolvedValue({
        data: [mockRecipe],
      } as never)

      const store = useRecipesStore()
      await store.fetchFavorites()

      expect(store.favorites).toEqual([mockRecipe])
    })
  })
})
