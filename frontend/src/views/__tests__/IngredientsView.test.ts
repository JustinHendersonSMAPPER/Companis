import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import IngredientsView from '@/views/IngredientsView.vue'

vi.mock('@/services/api', () => ({
  ingredientsApi: {
    getHousehold: vi.fn().mockResolvedValue({ data: [] }),
    addToHousehold: vi.fn().mockResolvedValue({
      data: {
        id: 'hi1', household_id: 'h1', ingredient_id: 'i1', quantity: 1, unit: 'kg',
        expiry_date: null, source: 'manual', created_at: '',
        ingredient: {
          id: 'i1', name: 'Flour', category: 'Baking', barcode: null, brand: null,
          description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '',
        },
      },
    }),
    removeFromHousehold: vi.fn().mockResolvedValue({}),
    scanBarcode: vi.fn(),
    cameraScan: vi.fn(),
  },
  aiApi: {
    parseVoiceInput: vi.fn().mockResolvedValue({
      data: { ingredients: [{ name: 'Tomato', quantity: 3, unit: 'pcs' }] },
    }),
    getProviders: vi.fn(),
    suggestSubstitutions: vi.fn(),
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/ingredients', name: 'ingredients', component: { template: '<div/>' } }],
})

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(IngredientsView, {
    global: {
      plugins: [pinia, router],
      stubs: { VoiceInput: true },
    },
  })
}

describe('IngredientsView', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/ingredients')
    await router.isReady()
  })

  it('renders heading, add form, search, and unit selector', () => {
    const wrapper = mountView()
    expect(wrapper.find('h1').text()).toBe('My Pantry')
    expect(wrapper.text()).toContain('Manage your household ingredients')
    expect(wrapper.find('form').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="Ingredient name"]').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').text()).toContain('Add to Pantry')
    expect(wrapper.find('.search-input').exists()).toBe(true)
    expect(wrapper.find('select').exists()).toBe(true)
  })

  it('fetches ingredients on mount', async () => {
    mountView()
    await flushPromises()
    const { ingredientsApi } = await import('@/services/api')
    expect(ingredientsApi.getHousehold).toHaveBeenCalled()
  })

  it('shows empty state when no ingredients', async () => {
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.text()).toContain('No ingredients yet')
  })

  it('renders populated ingredient list', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.getHousehold).mockResolvedValueOnce({
      data: [
        {
          id: 'hi1', household_id: 'h1', ingredient_id: 'i1', quantity: 2, unit: 'kg',
          expiry_date: null, source: 'manual', created_at: '',
          ingredient: { id: 'i1', name: 'Flour', category: 'Baking', barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
        },
        {
          id: 'hi2', household_id: 'h1', ingredient_id: 'i2', quantity: 500, unit: 'g',
          expiry_date: null, source: 'barcode', created_at: '',
          ingredient: { id: 'i2', name: 'Sugar', category: 'Baking', barcode: '456', brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
        },
      ],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.empty-state').exists()).toBe(false)
    expect(wrapper.find('.ingredient-list').exists()).toBe(true)
    const items = wrapper.findAll('.ingredient-item')
    expect(items.length).toBe(2)

    expect(wrapper.text()).toContain('Flour')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('kg')
    expect(wrapper.text()).toContain('Baking')
    expect(wrapper.text()).toContain('manual')

    expect(wrapper.text()).toContain('Sugar')
    expect(wrapper.text()).toContain('barcode')
  })

  it('submits add ingredient form', async () => {
    const wrapper = mountView()
    await flushPromises()

    const nameInput = wrapper.find('input[placeholder="Ingredient name"]')
    await nameInput.setValue('Rice')

    const qtyInput = wrapper.find('input[type="number"]')
    await qtyInput.setValue(2)

    const select = wrapper.find('select')
    await select.setValue('kg')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { ingredientsApi } = await import('@/services/api')
    expect(ingredientsApi.addToHousehold).toHaveBeenCalledWith({
      name: 'Rice',
      quantity: 2,
      unit: 'kg',
      source: 'manual',
    })

    // Form fields should be cleared after add
    expect((nameInput.element as HTMLInputElement).value).toBe('')
  })

  it('empty name does not add', async () => {
    const wrapper = mountView()
    await flushPromises()

    // Submit form without setting name
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { ingredientsApi } = await import('@/services/api')
    expect(ingredientsApi.addToHousehold).not.toHaveBeenCalled()
  })

  it('whitespace-only name does not add', async () => {
    const wrapper = mountView()
    await flushPromises()

    const nameInput = wrapper.find('input[placeholder="Ingredient name"]')
    await nameInput.setValue('   ')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { ingredientsApi } = await import('@/services/api')
    expect(ingredientsApi.addToHousehold).not.toHaveBeenCalled()
  })

  it('add ingredient with no unit sends undefined', async () => {
    const wrapper = mountView()
    await flushPromises()

    const nameInput = wrapper.find('input[placeholder="Ingredient name"]')
    await nameInput.setValue('Salt')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { ingredientsApi } = await import('@/services/api')
    expect(ingredientsApi.addToHousehold).toHaveBeenCalledWith({
      name: 'Salt',
      quantity: undefined,
      unit: undefined,
      source: 'manual',
    })
  })

  it('removes ingredient on remove button click', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.getHousehold).mockResolvedValueOnce({
      data: [{
        id: 'hi1', household_id: 'h1', ingredient_id: 'i1', quantity: 2, unit: 'kg',
        expiry_date: null, source: 'manual', created_at: '',
        ingredient: { id: 'i1', name: 'Flour', category: 'Baking', barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
      }],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.findAll('.ingredient-item').length).toBe(1)

    const removeBtn = wrapper.find('.remove-btn')
    expect(removeBtn.text()).toBe('Remove')
    await removeBtn.trigger('click')
    await flushPromises()

    expect(ingredientsApi.removeFromHousehold).toHaveBeenCalledWith('hi1')

    // Ingredient should be removed from list
    expect(wrapper.findAll('.ingredient-item').length).toBe(0)
  })

  it('search filtering by ingredient name', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.getHousehold).mockResolvedValueOnce({
      data: [
        {
          id: 'hi1', household_id: 'h1', ingredient_id: 'i1', quantity: 2, unit: 'kg',
          expiry_date: null, source: 'manual', created_at: '',
          ingredient: { id: 'i1', name: 'Flour', category: 'Baking', barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
        },
        {
          id: 'hi2', household_id: 'h1', ingredient_id: 'i2', quantity: 1, unit: 'L',
          expiry_date: null, source: 'manual', created_at: '',
          ingredient: { id: 'i2', name: 'Milk', category: 'Dairy', barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
        },
      ],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    // Both items visible initially
    expect(wrapper.findAll('.ingredient-item').length).toBe(2)

    // Search for "flour"
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('flour')
    await wrapper.vm.$nextTick()

    // Only Flour should be visible
    const items = wrapper.findAll('.ingredient-item')
    expect(items.length).toBe(1)
    expect(wrapper.text()).toContain('Flour')
    expect(wrapper.text()).not.toContain('Milk')
  })

  it('search filtering by category', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.getHousehold).mockResolvedValueOnce({
      data: [
        {
          id: 'hi1', household_id: 'h1', ingredient_id: 'i1', quantity: 2, unit: 'kg',
          expiry_date: null, source: 'manual', created_at: '',
          ingredient: { id: 'i1', name: 'Flour', category: 'Baking', barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
        },
        {
          id: 'hi2', household_id: 'h1', ingredient_id: 'i2', quantity: 1, unit: 'L',
          expiry_date: null, source: 'manual', created_at: '',
          ingredient: { id: 'i2', name: 'Milk', category: 'Dairy', barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
        },
      ],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    // Search by category "Dairy"
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('dairy')
    await wrapper.vm.$nextTick()

    const items = wrapper.findAll('.ingredient-item')
    expect(items.length).toBe(1)
    expect(wrapper.text()).toContain('Milk')
    expect(wrapper.text()).not.toContain('Flour')
  })

  it('clearing search shows all ingredients', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.getHousehold).mockResolvedValueOnce({
      data: [
        {
          id: 'hi1', household_id: 'h1', ingredient_id: 'i1', quantity: 2, unit: 'kg',
          expiry_date: null, source: 'manual', created_at: '',
          ingredient: { id: 'i1', name: 'Flour', category: 'Baking', barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
        },
        {
          id: 'hi2', household_id: 'h1', ingredient_id: 'i2', quantity: 1, unit: 'L',
          expiry_date: null, source: 'manual', created_at: '',
          ingredient: { id: 'i2', name: 'Milk', category: 'Dairy', barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
        },
      ],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('flour')
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('.ingredient-item').length).toBe(1)

    // Clear search
    await searchInput.setValue('')
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('.ingredient-item').length).toBe(2)
  })

  it('search with no matches shows empty state', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.getHousehold).mockResolvedValueOnce({
      data: [{
        id: 'hi1', household_id: 'h1', ingredient_id: 'i1', quantity: 2, unit: 'kg',
        expiry_date: null, source: 'manual', created_at: '',
        ingredient: { id: 'i1', name: 'Flour', category: 'Baking', barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
      }],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('xyz')
    await wrapper.vm.$nextTick()

    expect(wrapper.findAll('.ingredient-item').length).toBe(0)
    expect(wrapper.find('.empty-state').exists()).toBe(true)
  })

  it('displays ingredients count in list header', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.getHousehold).mockResolvedValueOnce({
      data: [{
        id: 'hi1', household_id: 'h1', ingredient_id: 'i1', quantity: 2, unit: 'kg',
        expiry_date: null, source: 'manual', created_at: '',
        ingredient: { id: 'i1', name: 'Flour', category: 'Baking', barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
      }],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.list-header h2').text()).toContain('Ingredients (1)')
  })

  it('VoiceInput component is rendered', () => {
    const wrapper = mountView()
    expect(wrapper.find('.voice-section').exists()).toBe(true)
    expect(wrapper.text()).toContain('Or use voice input')
  })

  it('renders unit selector options', () => {
    const wrapper = mountView()
    const options = wrapper.findAll('select option')
    // default "Unit" + 10 unit options
    expect(options.length).toBe(11)
    expect(options[0].text()).toBe('Unit')
    expect(options[1].text()).toBe('grams')
    expect(options[2].text()).toBe('kg')
  })

  it('adding ingredient resets form fields', async () => {
    const wrapper = mountView()
    await flushPromises()

    const nameInput = wrapper.find('input[placeholder="Ingredient name"]')
    await nameInput.setValue('Flour')
    const numInput = wrapper.find('input[type="number"]')
    await numInput.setValue(2)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    // Form inputs should be cleared
    expect((nameInput.element as HTMLInputElement).value).toBe('')
  })
})
