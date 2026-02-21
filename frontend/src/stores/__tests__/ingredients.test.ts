import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIngredientsStore } from '@/stores/ingredients'

vi.mock('@/services/api', () => ({
  ingredientsApi: {
    getHousehold: vi.fn(),
    addToHousehold: vi.fn(),
    removeFromHousehold: vi.fn(),
    scanBarcode: vi.fn(),
    cameraScan: vi.fn(),
  },
}))

import { ingredientsApi } from '@/services/api'

const mockIngredient = {
  id: 'hi-1',
  household_id: 'h1',
  ingredient_id: 'i1',
  quantity: 2,
  unit: 'kg',
  expiry_date: null,
  source: 'manual',
  created_at: '2024-01-01',
  ingredient: {
    id: 'i1',
    name: 'Flour',
    category: 'Baking',
    barcode: null,
    brand: null,
    description: null,
    image_url: null,
    nutrition_info: null,
    common_allergens: 'gluten',
    created_at: '2024-01-01',
  },
}

describe('useIngredientsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('has correct initial state', () => {
    const store = useIngredientsStore()
    expect(store.householdIngredients).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  describe('fetchHouseholdIngredients', () => {
    it('fetches and sets ingredients', async () => {
      vi.mocked(ingredientsApi.getHousehold).mockResolvedValue({
        data: [mockIngredient],
      } as never)

      const store = useIngredientsStore()
      await store.fetchHouseholdIngredients()

      expect(store.householdIngredients).toEqual([mockIngredient])
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error on failure', async () => {
      vi.mocked(ingredientsApi.getHousehold).mockRejectedValue({
        response: { data: { detail: 'Server error' } },
      })

      const store = useIngredientsStore()
      await store.fetchHouseholdIngredients()

      expect(store.error).toBe('Server error')
      expect(store.loading).toBe(false)
    })

    it('uses fallback error message', async () => {
      vi.mocked(ingredientsApi.getHousehold).mockRejectedValue(new Error('network'))

      const store = useIngredientsStore()
      await store.fetchHouseholdIngredients()

      expect(store.error).toBe('Failed to fetch ingredients')
    })
  })

  describe('addIngredient', () => {
    it('adds ingredient to list', async () => {
      vi.mocked(ingredientsApi.addToHousehold).mockResolvedValue({
        data: mockIngredient,
      } as never)

      const store = useIngredientsStore()
      await store.addIngredient({ name: 'Flour', quantity: 2, unit: 'kg' })

      expect(store.householdIngredients).toHaveLength(1)
      expect(store.householdIngredients[0]).toEqual(mockIngredient)
      expect(store.loading).toBe(false)
    })

    it('sets error and rethrows on failure', async () => {
      vi.mocked(ingredientsApi.addToHousehold).mockRejectedValue({
        response: { data: { detail: 'Bad request' } },
      })

      const store = useIngredientsStore()
      await expect(store.addIngredient({ name: 'X' })).rejects.toBeTruthy()

      expect(store.error).toBe('Bad request')
      expect(store.loading).toBe(false)
    })
  })

  describe('removeIngredient', () => {
    it('removes ingredient from list', async () => {
      vi.mocked(ingredientsApi.removeFromHousehold).mockResolvedValue({} as never)

      const store = useIngredientsStore()
      store.householdIngredients = [mockIngredient]
      await store.removeIngredient('hi-1')

      expect(store.householdIngredients).toHaveLength(0)
    })

    it('sets error on removal failure', async () => {
      vi.mocked(ingredientsApi.removeFromHousehold).mockRejectedValue({
        response: { data: { detail: 'Not found' } },
      })

      const store = useIngredientsStore()
      store.householdIngredients = [mockIngredient]
      await store.removeIngredient('hi-1')

      expect(store.error).toBe('Not found')
      // List unchanged on error
      expect(store.householdIngredients).toHaveLength(1)
    })
  })

  describe('scanBarcode', () => {
    it('returns barcode scan result', async () => {
      const scanResult = {
        barcode: '123456',
        ingredient: null,
        product_name: 'Test Product',
        brand: 'Brand',
        found: true,
      }
      vi.mocked(ingredientsApi.scanBarcode).mockResolvedValue({ data: scanResult } as never)

      const store = useIngredientsStore()
      const result = await store.scanBarcode('123456')

      expect(result).toEqual(scanResult)
      expect(ingredientsApi.scanBarcode).toHaveBeenCalledWith('123456')
    })
  })

  describe('cameraScan', () => {
    it('returns camera scan result', async () => {
      const scanResult = {
        detected_ingredients: ['tomato', 'onion'],
        confidence_scores: { tomato: 0.9, onion: 0.85 },
      }
      vi.mocked(ingredientsApi.cameraScan).mockResolvedValue({ data: scanResult } as never)

      const store = useIngredientsStore()
      const result = await store.cameraScan('base64data')

      expect(result).toEqual(scanResult)
      expect(ingredientsApi.cameraScan).toHaveBeenCalledWith('base64data')
    })
  })
})
