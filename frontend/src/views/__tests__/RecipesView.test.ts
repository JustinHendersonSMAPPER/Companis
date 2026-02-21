import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import RecipesView from '@/views/RecipesView.vue'

vi.mock('@/services/api', () => ({
  recipesApi: {
    search: vi.fn().mockResolvedValue({
      data: {
        recipes: [
          {
            id: 'r1', title: 'Pasta Carbonara', description: 'Classic Italian dish',
            instructions: 'Cook pasta', cuisine: 'Italian', meal_type: 'dinner',
            prep_time_minutes: 10, cook_time_minutes: 20, servings: 2, difficulty: 'easy',
            image_url: null, source: 'ai', dietary_tags: null, calorie_estimate: 500,
            created_at: '', recipe_ingredients: [], is_favorite: false, average_rating: null,
          },
        ],
        missing_ingredients: { r1: ['bacon'] },
        substitutions: { r1: [{ original_ingredient: 'bacon', substitute: 'pancetta', notes: 'Similar taste', ratio: '1:1' }] },
      },
    }),
    getById: vi.fn(),
    rate: vi.fn(),
    addFavorite: vi.fn().mockResolvedValue({}),
    removeFavorite: vi.fn().mockResolvedValue({}),
    getFavorites: vi.fn().mockResolvedValue({ data: [] }),
  },
  shoppingApi: {
    getCarts: vi.fn().mockResolvedValue({ data: [] }),
    createCart: vi.fn(),
    addItem: vi.fn(),
    updateItem: vi.fn(),
    removeItem: vi.fn(),
    addMissingIngredients: vi.fn().mockResolvedValue({ data: [] }),
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/recipes', name: 'recipes', component: { template: '<div/>' } },
    { path: '/recipes/:id', name: 'recipe-detail', component: { template: '<div/>' } },
  ],
})

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(RecipesView, {
    global: {
      plugins: [pinia, router],
      stubs: { VoiceInput: true },
    },
  })
}

describe('RecipesView', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/recipes')
    await router.isReady()
  })

  it('renders heading, tab bar, search form, and filters', () => {
    const wrapper = mountView()
    expect(wrapper.find('h1').text()).toBe('Recipes')

    const tabs = wrapper.findAll('.tab')
    expect(tabs.length).toBe(2)
    expect(tabs[0].text()).toContain('Search')
    expect(tabs[1].text()).toContain('Favorites')

    expect(wrapper.find('textarea').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').text()).toContain('Search')

    const filterInputs = wrapper.findAll('.search-filters input')
    expect(filterInputs.length).toBe(2) // prep time and cuisine
  })

  it('fetches favorites on mount', async () => {
    mountView()
    await flushPromises()
    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.getFavorites).toHaveBeenCalled()
  })

  it('switches to favorites tab', async () => {
    const wrapper = mountView()
    await flushPromises()

    const tabs = wrapper.findAll('.tab')
    await tabs[1].trigger('click')

    expect(wrapper.find('.empty-state').text()).toContain('No favorite recipes yet')
  })

  it('favorites tab shows active class', async () => {
    const wrapper = mountView()
    const tabs = wrapper.findAll('.tab')
    await tabs[1].trigger('click')
    expect(tabs[1].classes()).toContain('active')
    expect(tabs[0].classes()).not.toContain('active')
  })

  it('submits search form with prompt text', async () => {
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('pasta dishes')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.search).toHaveBeenCalledWith({
      prompt: 'pasta dishes',
      max_prep_time_minutes: undefined,
      cuisine: undefined,
    })
  })

  it('submits search with filters', async () => {
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('quick lunch')

    const filterInputs = wrapper.findAll('.search-filters input')
    await filterInputs[0].setValue(30)  // max prep time
    await filterInputs[1].setValue('Mexican')  // cuisine

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.search).toHaveBeenCalledWith({
      prompt: 'quick lunch',
      max_prep_time_minutes: 30,
      cuisine: 'Mexican',
    })
  })

  it('empty prompt does not search', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.search).not.toHaveBeenCalled()
  })

  it('whitespace-only prompt does not search', async () => {
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('   ')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.search).not.toHaveBeenCalled()
  })

  it('renders search results', async () => {
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('pasta')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    // Recipe card should be rendered
    expect(wrapper.find('.recipe-card').exists()).toBe(true)
    expect(wrapper.text()).toContain('Pasta Carbonara')
    expect(wrapper.text()).toContain('Italian')
    expect(wrapper.text()).toContain('10min')
    expect(wrapper.text()).toContain('2 servings')
    expect(wrapper.text()).toContain('~500 cal')
    expect(wrapper.text()).toContain('Classic Italian dish')
  })

  it('renders missing ingredients notice in search results', async () => {
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('pasta')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.missing-notice').exists()).toBe(true)
    expect(wrapper.text()).toContain('bacon')
  })

  it('renders substitutions notice in search results', async () => {
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('pasta')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.substitution-notice').exists()).toBe(true)
    expect(wrapper.text()).toContain('Substitutions available')
    expect(wrapper.text()).toContain('pancetta')
  })

  it('toggles favorite on recipe card', async () => {
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('pasta')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const favoriteBtn = wrapper.find('.action-btn')
    expect(favoriteBtn.text()).toBe('Favorite')
    await favoriteBtn.trigger('click')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.addFavorite).toHaveBeenCalledWith('r1')
  })

  it('adds missing ingredients to shopping list', async () => {
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('pasta')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    // Click "Add missing to cart" button
    const shopBtn = wrapper.find('.action-btn.shop')
    expect(shopBtn.exists()).toBe(true)
    expect(shopBtn.text()).toContain('Add missing to cart')
    await shopBtn.trigger('click')
    await flushPromises()

    const { shoppingApi } = await import('@/services/api')
    expect(shoppingApi.addMissingIngredients).toHaveBeenCalledWith({
      recipe_id: 'r1',
      ingredient_names: ['bacon'],
    })
  })

  it('recipe card links to recipe detail', async () => {
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('pasta')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const link = wrapper.find('.recipe-link')
    expect(link.attributes('href')).toBe('/recipes/r1')
  })

  it('search tab is active by default', () => {
    const wrapper = mountView()
    const tabs = wrapper.findAll('.tab')
    expect(tabs[0].classes()).toContain('active')
  })

  it('favorites count is shown in tab', async () => {
    const wrapper = mountView()
    await flushPromises()
    const tabs = wrapper.findAll('.tab')
    expect(tabs[1].text()).toContain('Favorites (0)')
  })

  it('handles search error gracefully', async () => {
    const { recipesApi } = await import('@/services/api')
    vi.mocked(recipesApi.search).mockRejectedValueOnce(new Error('Search failed'))

    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('pasta')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    // Should not crash; no search results displayed
    expect(wrapper.find('.recipe-card').exists()).toBe(false)
  })
})
