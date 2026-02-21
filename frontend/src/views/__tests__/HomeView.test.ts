import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

vi.mock('@/services/api', () => ({
  authApi: { register: vi.fn(), login: vi.fn(), getOAuthUrl: vi.fn(), oauthCallback: vi.fn() },
  usersApi: { getMe: vi.fn() },
  ingredientsApi: {
    getHousehold: vi.fn().mockResolvedValue({ data: [] }),
    addToHousehold: vi.fn(),
    removeFromHousehold: vi.fn(),
    scanBarcode: vi.fn(),
    cameraScan: vi.fn(),
  },
  recipesApi: {
    search: vi.fn().mockResolvedValue({
      data: {
        recipes: [
          {
            id: 'r1', title: 'Thai Curry', description: 'Delicious curry',
            instructions: 'Cook it', cuisine: 'Thai', meal_type: 'dinner',
            prep_time_minutes: 25, cook_time_minutes: 30, servings: 4,
            difficulty: 'medium', image_url: null, source: 'ai',
            dietary_tags: null, calorie_estimate: null, created_at: '',
            recipe_ingredients: [], is_favorite: false,
          },
        ],
        missing_ingredients: { r1: ['coconut milk'] },
        substitutions: {
          r1: [{ original_ingredient: 'coconut milk', substitute: 'heavy cream', notes: null, ratio: '1:1' }],
        },
      },
    }),
    getById: vi.fn(),
    rate: vi.fn(),
    addFavorite: vi.fn(),
    removeFavorite: vi.fn(),
    getFavorites: vi.fn(),
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', name: 'home', component: { template: '<div/>' } },
    { path: '/recipes/:id', name: 'recipe-detail', component: { template: '<div/>' } },
  ],
})

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(HomeView, {
    global: {
      plugins: [pinia, router],
      stubs: { VoiceInput: true },
    },
  })
}

describe('HomeView', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/')
    await router.isReady()
  })

  it('renders greeting', () => {
    const wrapper = mountView()
    expect(wrapper.find('h1').text()).toContain('Hello')
  })

  it('renders greeting with user name when authenticated', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.user = {
      id: 'u1', email: 'chef@example.com', full_name: 'Gordon Ramsay',
      avatar_url: null, auth_provider: 'local', is_active: true,
      is_verified: false, created_at: '',
    }

    const wrapper = mount(HomeView, {
      global: {
        plugins: [pinia, router],
        stubs: { VoiceInput: true },
      },
    })

    expect(wrapper.find('h1').text()).toContain('Gordon')
  })

  it('renders search form', () => {
    const wrapper = mountView()
    expect(wrapper.find('textarea').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').text()).toContain('Find Recipes')
  })

  it('renders pantry stats', () => {
    const wrapper = mountView()
    expect(wrapper.find('.stat-label').text()).toContain('Items in pantry')
  })

  it('fetches ingredients on mount', async () => {
    mountView()
    await flushPromises()
    const { ingredientsApi } = await import('@/services/api')
    expect(ingredientsApi.getHousehold).toHaveBeenCalled()
  })

  it('renders search filters', () => {
    const wrapper = mountView()
    const inputs = wrapper.findAll('input')
    expect(inputs.length).toBeGreaterThanOrEqual(2) // prep time + cuisine
  })

  it('submits search form with prompt text', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('textarea').setValue('Quick Thai dinner')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.search).toHaveBeenCalledWith({
      prompt: 'Quick Thai dinner',
      max_prep_time_minutes: undefined,
      cuisine: undefined,
    })
  })

  it('does not search when prompt is empty', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('textarea').setValue('')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.search).not.toHaveBeenCalled()
  })

  it('does not search when prompt is only whitespace', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('textarea').setValue('   ')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.search).not.toHaveBeenCalled()
  })

  it('displays search results after successful search', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('textarea').setValue('Thai food')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Recipe Suggestions')
    expect(wrapper.text()).toContain('Thai Curry')
    expect(wrapper.text()).toContain('Thai')
    expect(wrapper.text()).toContain('25 min prep')
    expect(wrapper.text()).toContain('medium')
  })

  it('displays missing ingredients for search results', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('textarea').setValue('Thai food')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Missing ingredients')
    expect(wrapper.text()).toContain('coconut milk')
  })

  it('displays substitution suggestions for search results', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('textarea').setValue('Thai food')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Substitutions available')
    expect(wrapper.text()).toContain('heavy cream')
  })

  it('passes cuisine filter to search', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('textarea').setValue('Dinner')
    const inputs = wrapper.findAll('input')
    // The cuisine input is the second input (after prep time)
    const cuisineInput = inputs.find(i => i.attributes('placeholder') === 'Cuisine type')
    await cuisineInput!.setValue('Italian')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.search).toHaveBeenCalledWith({
      prompt: 'Dinner',
      max_prep_time_minutes: undefined,
      cuisine: 'Italian',
    })
  })

  it('renders subtitle text', () => {
    const wrapper = mountView()
    expect(wrapper.find('.subtitle').text()).toBe('What would you like to cook today?')
  })

  it('shows pantry count from ingredients store', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    const { useIngredientsStore } = await import('@/stores/ingredients')
    const ingredientsStore = useIngredientsStore()
    ingredientsStore.householdIngredients = [
      {
        id: 'hi1', household_id: 'h1', ingredient_id: 'i1',
        quantity: 2, unit: 'kg', expiry_date: null, source: 'manual', created_at: '',
        ingredient: { id: 'i1', name: 'Rice', category: null, barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
      },
      {
        id: 'hi2', household_id: 'h1', ingredient_id: 'i2',
        quantity: 1, unit: 'bottle', expiry_date: null, source: 'manual', created_at: '',
        ingredient: { id: 'i2', name: 'Soy Sauce', category: null, barcode: null, brand: null, description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
      },
    ] as never

    const wrapper = mount(HomeView, {
      global: {
        plugins: [pinia, router],
        stubs: { VoiceInput: true },
      },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.stat-number').text()).toBe('2')
  })
})
