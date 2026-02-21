import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import ShoppingView from '@/views/ShoppingView.vue'

vi.mock('@/services/api', () => ({
  shoppingApi: {
    getCarts: vi.fn().mockResolvedValue({ data: [] }),
    createCart: vi.fn().mockResolvedValue({
      data: { id: 'c1', household_id: 'h1', name: 'Shopping List', is_active: true, created_at: '', items: [] },
    }),
    addItem: vi.fn().mockResolvedValue({
      data: { id: 'item1', name: 'Eggs', quantity: 12, unit: 'pcs', notes: null, is_purchased: false, added_from_recipe_id: null, created_at: '' },
    }),
    updateItem: vi.fn().mockResolvedValue({
      data: { id: 'i1', name: 'Milk', quantity: 1, unit: 'L', notes: null, is_purchased: true, added_from_recipe_id: null, created_at: '' },
    }),
    removeItem: vi.fn().mockResolvedValue({}),
    addMissingIngredients: vi.fn().mockResolvedValue({ data: [] }),
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/shopping', name: 'shopping', component: { template: '<div/>' } },
  ],
})

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(ShoppingView, {
    global: { plugins: [pinia, router] },
  })
}

describe('ShoppingView', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/shopping')
    await router.isReady()
  })

  it('renders heading', () => {
    const wrapper = mountView()
    expect(wrapper.find('h1').text()).toBe('Shopping Lists')
  })

  it('fetches carts on mount', async () => {
    mountView()
    await flushPromises()
    const { shoppingApi } = await import('@/services/api')
    expect(shoppingApi.getCarts).toHaveBeenCalled()
  })

  it('shows empty state when no carts', async () => {
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.text()).toContain('No shopping lists yet')
  })

  it('creates cart when clicking Create Shopping List button', async () => {
    const wrapper = mountView()
    await flushPromises()

    const btn = wrapper.find('.empty-state .btn-primary')
    expect(btn.text()).toContain('Create Shopping List')
    await btn.trigger('click')
    await flushPromises()

    const { shoppingApi } = await import('@/services/api')
    expect(shoppingApi.createCart).toHaveBeenCalledWith({ name: 'Shopping List' })

    // After creation, the cart should be rendered
    expect(wrapper.find('.cart-section').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toBe('Shopping List')
  })

  it('renders cart items when cart exists', async () => {
    const { shoppingApi } = await import('@/services/api')
    vi.mocked(shoppingApi.getCarts).mockResolvedValueOnce({
      data: [{
        id: 'c1', household_id: 'h1', name: 'Weekly', is_active: true, created_at: '',
        items: [
          { id: 'i1', name: 'Milk', quantity: 1, unit: 'L', notes: null, is_purchased: false, added_from_recipe_id: null, created_at: '' },
          { id: 'i2', name: 'Bread', quantity: 2, unit: null, notes: 'whole wheat', is_purchased: true, added_from_recipe_id: null, created_at: '' },
        ],
      }],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.cart-section').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toBe('Weekly')
    expect(wrapper.find('.add-item-form').exists()).toBe(true)

    const items = wrapper.findAll('.cart-item')
    expect(items.length).toBe(2)

    // First item - not purchased
    expect(items[0].find('.item-name').text()).toBe('Milk')
    expect(items[0].find('.item-qty').text()).toContain('1')
    expect(items[0].find('.check-btn').text()).toBe('[ ]')

    // Second item - purchased
    expect(items[1].find('.item-name').text()).toBe('Bread')
    expect(items[1].find('.check-btn').text()).toBe('[x]')
    expect(items[1].classes()).toContain('purchased')
    expect(items[1].find('.item-notes').text()).toBe('whole wheat')
  })

  it('submits add item form', async () => {
    const { shoppingApi } = await import('@/services/api')
    vi.mocked(shoppingApi.getCarts).mockResolvedValueOnce({
      data: [{
        id: 'c1', household_id: 'h1', name: 'Weekly', is_active: true, created_at: '',
        items: [],
      }],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    const form = wrapper.find('.add-item-form')
    const inputs = form.findAll('input')
    // First input is item name, second is quantity
    await inputs[0].setValue('Eggs')
    await inputs[1].setValue(12)
    await form.trigger('submit')
    await flushPromises()

    expect(shoppingApi.addItem).toHaveBeenCalledWith('c1', {
      name: 'Eggs',
      quantity: 12,
      unit: undefined,
    })

    // Inputs should be cleared after add
    expect((inputs[0].element as HTMLInputElement).value).toBe('')
  })

  it('add item does nothing when name is empty', async () => {
    const { shoppingApi } = await import('@/services/api')
    vi.mocked(shoppingApi.getCarts).mockResolvedValueOnce({
      data: [{
        id: 'c1', household_id: 'h1', name: 'Weekly', is_active: true, created_at: '',
        items: [],
      }],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    // Submit form without setting name
    await wrapper.find('.add-item-form').trigger('submit')
    await flushPromises()

    expect(shoppingApi.addItem).not.toHaveBeenCalled()
  })

  it('toggles item purchased on check button click', async () => {
    const { shoppingApi } = await import('@/services/api')
    vi.mocked(shoppingApi.getCarts).mockResolvedValueOnce({
      data: [{
        id: 'c1', household_id: 'h1', name: 'Weekly', is_active: true, created_at: '',
        items: [
          { id: 'i1', name: 'Milk', quantity: 1, unit: 'L', notes: null, is_purchased: false, added_from_recipe_id: null, created_at: '' },
        ],
      }],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    const checkBtn = wrapper.find('.check-btn')
    expect(checkBtn.text()).toBe('[ ]')
    await checkBtn.trigger('click')
    await flushPromises()

    expect(shoppingApi.updateItem).toHaveBeenCalledWith('c1', 'i1', { is_purchased: true })
  })

  it('removes item on remove button click', async () => {
    const { shoppingApi } = await import('@/services/api')
    vi.mocked(shoppingApi.getCarts).mockResolvedValueOnce({
      data: [{
        id: 'c1', household_id: 'h1', name: 'Weekly', is_active: true, created_at: '',
        items: [
          { id: 'i1', name: 'Milk', quantity: 1, unit: 'L', notes: null, is_purchased: false, added_from_recipe_id: null, created_at: '' },
        ],
      }],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    const removeBtn = wrapper.find('.remove-btn')
    await removeBtn.trigger('click')
    await flushPromises()

    expect(shoppingApi.removeItem).toHaveBeenCalledWith('c1', 'i1')

    // Item should be removed from the list
    expect(wrapper.findAll('.cart-item').length).toBe(0)
  })

  it('shows empty cart message when cart has no items', async () => {
    const { shoppingApi } = await import('@/services/api')
    vi.mocked(shoppingApi.getCarts).mockResolvedValueOnce({
      data: [{
        id: 'c1', household_id: 'h1', name: 'Weekly', is_active: true, created_at: '',
        items: [],
      }],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.empty-cart').exists()).toBe(true)
    expect(wrapper.text()).toContain('No items in this list yet')
  })

  it('add item clears all form fields after submission', async () => {
    const { shoppingApi } = await import('@/services/api')
    vi.mocked(shoppingApi.getCarts).mockResolvedValueOnce({
      data: [{
        id: 'c1', household_id: 'h1', name: 'Weekly', is_active: true, created_at: '',
        items: [],
      }],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    const form = wrapper.find('.add-item-form')
    const inputs = form.findAll('input')
    await inputs[0].setValue('Sugar')
    await inputs[1].setValue(5)
    await form.trigger('submit')
    await flushPromises()

    // All fields cleared
    expect((inputs[0].element as HTMLInputElement).value).toBe('')
    expect((inputs[1].element as HTMLInputElement).value).toBe('')
  })
})
