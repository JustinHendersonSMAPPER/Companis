import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useShoppingStore } from '@/stores/shopping'

vi.mock('@/services/api', () => ({
  shoppingApi: {
    getCarts: vi.fn(),
    createCart: vi.fn(),
    addItem: vi.fn(),
    updateItem: vi.fn(),
    removeItem: vi.fn(),
    addMissingIngredients: vi.fn(),
  },
}))

import { shoppingApi } from '@/services/api'

const mockItem = {
  id: 'item-1',
  name: 'Milk',
  quantity: 1,
  unit: 'L',
  notes: null,
  is_purchased: false,
  added_from_recipe_id: null,
  created_at: '2024-01-01',
}

const mockCart = {
  id: 'cart-1',
  household_id: 'h1',
  name: 'Weekly Shopping',
  is_active: true,
  created_at: '2024-01-01',
  items: [mockItem],
}

describe('useShoppingStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('has correct initial state', () => {
    const store = useShoppingStore()
    expect(store.carts).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  describe('fetchCarts', () => {
    it('fetches and sets carts', async () => {
      vi.mocked(shoppingApi.getCarts).mockResolvedValue({ data: [mockCart] } as never)

      const store = useShoppingStore()
      await store.fetchCarts()

      expect(store.carts).toEqual([mockCart])
      expect(store.loading).toBe(false)
    })

    it('sets error on failure', async () => {
      vi.mocked(shoppingApi.getCarts).mockRejectedValue({
        response: { data: { detail: 'Server error' } },
      })

      const store = useShoppingStore()
      await store.fetchCarts()

      expect(store.error).toBe('Server error')
      expect(store.loading).toBe(false)
    })

    it('uses fallback error', async () => {
      vi.mocked(shoppingApi.getCarts).mockRejectedValue(new Error('net'))

      const store = useShoppingStore()
      await store.fetchCarts()

      expect(store.error).toBe('Failed to fetch shopping carts')
    })
  })

  describe('createCart', () => {
    it('creates cart and appends to list', async () => {
      vi.mocked(shoppingApi.createCart).mockResolvedValue({ data: mockCart } as never)

      const store = useShoppingStore()
      await store.createCart('Weekly Shopping')

      expect(shoppingApi.createCart).toHaveBeenCalledWith({ name: 'Weekly Shopping' })
      expect(store.carts).toHaveLength(1)
    })
  })

  describe('addItem', () => {
    it('adds item to cart', async () => {
      const newItem = { ...mockItem, id: 'item-2', name: 'Eggs' }
      vi.mocked(shoppingApi.addItem).mockResolvedValue({ data: newItem } as never)

      const store = useShoppingStore()
      store.carts = [{ ...mockCart, items: [...mockCart.items] }]
      await store.addItem('cart-1', { name: 'Eggs' })

      expect(shoppingApi.addItem).toHaveBeenCalledWith('cart-1', { name: 'Eggs' })
      expect(store.carts[0].items).toHaveLength(2)
    })

    it('does not add to non-existent cart', async () => {
      const newItem = { ...mockItem, id: 'item-2', name: 'Eggs' }
      vi.mocked(shoppingApi.addItem).mockResolvedValue({ data: newItem } as never)

      const store = useShoppingStore()
      store.carts = []
      await store.addItem('nonexistent', { name: 'Eggs' })

      expect(shoppingApi.addItem).toHaveBeenCalled()
    })
  })

  describe('togglePurchased', () => {
    it('toggles item purchased status', async () => {
      const updatedItem = { ...mockItem, is_purchased: true }
      vi.mocked(shoppingApi.updateItem).mockResolvedValue({ data: updatedItem } as never)

      const store = useShoppingStore()
      store.carts = [{ ...mockCart, items: [{ ...mockItem }] }]
      await store.togglePurchased('cart-1', 'item-1')

      expect(shoppingApi.updateItem).toHaveBeenCalledWith('cart-1', 'item-1', {
        is_purchased: true,
      })
    })

    it('does nothing for non-existent item', async () => {
      const store = useShoppingStore()
      store.carts = [{ ...mockCart, items: [] }]
      await store.togglePurchased('cart-1', 'nonexistent')

      expect(shoppingApi.updateItem).not.toHaveBeenCalled()
    })
  })

  describe('removeItem', () => {
    it('removes item from cart', async () => {
      vi.mocked(shoppingApi.removeItem).mockResolvedValue({} as never)

      const store = useShoppingStore()
      store.carts = [{ ...mockCart, items: [{ ...mockItem }] }]
      await store.removeItem('cart-1', 'item-1')

      expect(shoppingApi.removeItem).toHaveBeenCalledWith('cart-1', 'item-1')
      expect(store.carts[0].items).toHaveLength(0)
    })

    it('handles removing from non-existent cart gracefully', async () => {
      vi.mocked(shoppingApi.removeItem).mockResolvedValue({} as never)

      const store = useShoppingStore()
      store.carts = []
      await store.removeItem('nonexistent', 'item-1')

      expect(shoppingApi.removeItem).toHaveBeenCalled()
    })
  })

  describe('addMissingIngredients', () => {
    it('adds missing ingredients and refetches carts', async () => {
      vi.mocked(shoppingApi.addMissingIngredients).mockResolvedValue({ data: [] } as never)
      vi.mocked(shoppingApi.getCarts).mockResolvedValue({ data: [mockCart] } as never)

      const store = useShoppingStore()
      await store.addMissingIngredients('r1', ['flour', 'sugar'])

      expect(shoppingApi.addMissingIngredients).toHaveBeenCalledWith({
        recipe_id: 'r1',
        ingredient_names: ['flour', 'sugar'],
      })
      expect(shoppingApi.getCarts).toHaveBeenCalled()
    })
  })
})
