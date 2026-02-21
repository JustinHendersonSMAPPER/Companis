import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import RecipeDetailView from '@/views/RecipeDetailView.vue'

vi.mock('@/services/api', () => ({
  recipesApi: {
    search: vi.fn(),
    getById: vi.fn().mockResolvedValue({
      data: {
        id: 'r1', title: 'Test Pasta', description: 'Delicious',
        instructions: 'Step 1\nStep 2', cuisine: 'Italian', meal_type: 'dinner',
        prep_time_minutes: 15, cook_time_minutes: 20, servings: 4, difficulty: 'easy',
        image_url: null, source: 'ai', dietary_tags: null, calorie_estimate: 400, created_at: '',
        recipe_ingredients: [
          { name: 'pasta', quantity: 200, unit: 'g', is_optional: false, substitution_notes: null, is_available: true, has_substitution: false },
          { name: 'sauce', quantity: 1, unit: 'cup', is_optional: false, substitution_notes: null, is_available: false, has_substitution: false },
        ],
        is_favorite: false, average_rating: 4.5,
      },
    }),
    rate: vi.fn().mockResolvedValue({}),
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
    { path: '/recipes/:id', name: 'recipe-detail', component: RecipeDetailView },
    { path: '/', name: 'home', component: { template: '<div/>' } },
  ],
})

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(RecipeDetailView, {
    global: { plugins: [pinia, router] },
  })
}

describe('RecipeDetailView', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/recipes/r1')
    await router.isReady()
  })

  it('fetches recipe on mount', async () => {
    mountView()
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.getById).toHaveBeenCalledWith('r1')
  })

  it('renders recipe title', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('h1').text()).toBe('Test Pasta')
  })

  it('renders recipe metadata', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('Italian')
    expect(wrapper.text()).toContain('15min prep')
    expect(wrapper.text()).toContain('20min cook')
    expect(wrapper.text()).toContain('4 servings')
    expect(wrapper.text()).toContain('easy')
  })

  it('renders description', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.description').text()).toBe('Delicious')
  })

  it('renders ingredients list', async () => {
    const wrapper = mountView()
    await flushPromises()

    const ingredients = wrapper.findAll('.ingredient-item')
    expect(ingredients.length).toBe(2)
    expect(wrapper.text()).toContain('pasta')
    expect(wrapper.text()).toContain('200')
    expect(wrapper.text()).toContain('sauce')
    expect(wrapper.text()).toContain('1')
    expect(wrapper.text()).toContain('cup')
  })

  it('renders ingredient availability badges', async () => {
    const wrapper = mountView()
    await flushPromises()

    const badges = wrapper.findAll('.status-badge')
    // pasta is available, sauce is missing
    const badgeTexts = badges.map((b) => b.text())
    expect(badgeTexts).toContain('Have it')
    expect(badgeTexts).toContain('Missing')
  })

  it('renders instructions', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.instructions').text()).toContain('Step 1')
    expect(wrapper.find('.instructions').text()).toContain('Step 2')
  })

  it('shows favorite toggle button and clicks it', async () => {
    const wrapper = mountView()
    await flushPromises()

    const favBtn = wrapper.find('.action-btn')
    expect(favBtn.text()).toContain('Add to Favorites')

    await favBtn.trigger('click')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.addFavorite).toHaveBeenCalledWith('r1')

    // After toggling, text should change
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.action-btn').text()).toContain('Remove Favorite')
  })

  it('renders star rating section with 5 stars', async () => {
    const wrapper = mountView()
    await flushPromises()

    const stars = wrapper.findAll('.star')
    expect(stars.length).toBe(5)
  })

  it('clicking a star sets the rating', async () => {
    const wrapper = mountView()
    await flushPromises()

    const stars = wrapper.findAll('.star')
    // Click star 4 (index 3 for the 4th star)
    await stars[3].trigger('click')
    await wrapper.vm.$nextTick()

    // Stars 1-4 should be active
    expect(stars[0].classes()).toContain('active')
    expect(stars[1].classes()).toContain('active')
    expect(stars[2].classes()).toContain('active')
    expect(stars[3].classes()).toContain('active')
    expect(stars[4].classes()).not.toContain('active')
  })

  it('shows average rating', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.avg-rating').text()).toContain('4.5')
    expect(wrapper.text()).toContain('/ 5')
  })

  it('submits rating after clicking star and submit button', async () => {
    const wrapper = mountView()
    await flushPromises()

    // Click star 5
    const stars = wrapper.findAll('.star')
    await stars[4].trigger('click')
    await wrapper.vm.$nextTick()

    // Optionally fill review
    const reviewTextarea = wrapper.find('textarea')
    await reviewTextarea.setValue('Great recipe!')

    // Click Submit Rating button
    const submitBtn = wrapper.findAll('.btn-primary').find((b) => b.text().includes('Submit Rating'))
    expect(submitBtn).toBeDefined()
    await submitBtn!.trigger('click')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.rate).toHaveBeenCalledWith('r1', { score: 5, review: 'Great recipe!' })
  })

  it('submit rating does nothing when score is 0', async () => {
    const wrapper = mountView()
    await flushPromises()

    // Don't click any star - score stays 0
    const submitBtn = wrapper.findAll('.btn-primary').find((b) => b.text().includes('Submit Rating'))
    expect(submitBtn!.attributes('disabled')).toBeDefined()

    // Try clicking anyway via the vm method
    const vm = wrapper.vm as unknown as { submitRating: () => Promise<void> }
    await vm.submitRating()
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.rate).not.toHaveBeenCalled()
  })

  it('submit rating sends undefined review when empty', async () => {
    const wrapper = mountView()
    await flushPromises()

    const stars = wrapper.findAll('.star')
    await stars[2].trigger('click') // rating = 3
    await wrapper.vm.$nextTick()

    const submitBtn = wrapper.findAll('.btn-primary').find((b) => b.text().includes('Submit Rating'))
    await submitBtn!.trigger('click')
    await flushPromises()

    const { recipesApi } = await import('@/services/api')
    expect(recipesApi.rate).toHaveBeenCalledWith('r1', { score: 3, review: undefined })
  })

  it('clicks "Add missing to shopping cart" button', async () => {
    const wrapper = mountView()
    await flushPromises()

    // The button should be visible since sauce is_available=false and has_substitution=false
    const addMissingBtn = wrapper.find('.btn-secondary')
    expect(addMissingBtn.text()).toContain('Add missing to shopping cart')
    await addMissingBtn.trigger('click')
    await flushPromises()

    const { shoppingApi } = await import('@/services/api')
    expect(shoppingApi.addMissingIngredients).toHaveBeenCalledWith({
      recipe_id: 'r1',
      ingredient_names: ['sauce'],
    })
  })

  it('does not show add missing button when all ingredients are available', async () => {
    const { recipesApi } = await import('@/services/api')
    vi.mocked(recipesApi.getById).mockResolvedValueOnce({
      data: {
        id: 'r2', title: 'Simple Salad', description: 'Easy',
        instructions: 'Mix all', cuisine: null, meal_type: 'lunch',
        prep_time_minutes: 5, cook_time_minutes: null, servings: 1, difficulty: null,
        image_url: null, source: 'ai', dietary_tags: null, calorie_estimate: null, created_at: '',
        recipe_ingredients: [
          { name: 'lettuce', quantity: 1, unit: 'head', is_optional: false, substitution_notes: null, is_available: true, has_substitution: false },
        ],
        is_favorite: false, average_rating: null,
      },
    } as never)

    const wrapper = mountView()
    await flushPromises()

    // No "Add missing to shopping cart" button
    const btns = wrapper.findAll('.btn-secondary')
    const addMissingBtn = btns.filter((b) => b.text().includes('Add missing'))
    expect(addMissingBtn.length).toBe(0)
  })

  it('unfavorites a recipe that is already favorite', async () => {
    const { recipesApi } = await import('@/services/api')
    vi.mocked(recipesApi.getById).mockResolvedValueOnce({
      data: {
        id: 'r1', title: 'Test Pasta', description: 'Delicious',
        instructions: 'Step 1', cuisine: 'Italian', meal_type: 'dinner',
        prep_time_minutes: 15, cook_time_minutes: 20, servings: 4, difficulty: 'easy',
        image_url: null, source: 'ai', dietary_tags: null, calorie_estimate: 400, created_at: '',
        recipe_ingredients: [],
        is_favorite: true, average_rating: null,
      },
    } as never)

    const wrapper = mountView()
    await flushPromises()

    const favBtn = wrapper.find('.action-btn')
    expect(favBtn.text()).toContain('Remove Favorite')

    await favBtn.trigger('click')
    await flushPromises()

    expect(recipesApi.removeFavorite).toHaveBeenCalledWith('r1')
  })

  it('renders the recipe detail heading section', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.recipe-header').exists()).toBe(true)
    expect(wrapper.find('.recipe-meta').exists()).toBe(true)
    expect(wrapper.find('.header-actions').exists()).toBe(true)
  })
})
