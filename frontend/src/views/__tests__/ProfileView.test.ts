import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import ProfileView from '@/views/ProfileView.vue'

vi.mock('@/services/api', () => ({
  authApi: { register: vi.fn(), login: vi.fn(), getOAuthUrl: vi.fn(), oauthCallback: vi.fn() },
  usersApi: {
    getMe: vi.fn(),
    getDietaryPreferences: vi.fn().mockResolvedValue({ data: [] }),
    getHealthGoals: vi.fn().mockResolvedValue({ data: [] }),
    addDietaryPreference: vi.fn().mockResolvedValue({
      data: {
        id: 'dp1', preference_type: 'allergy', value: 'nuts',
        notes: null, created_at: '',
      },
    }),
    removeDietaryPreference: vi.fn().mockResolvedValue({}),
    addHealthGoal: vi.fn().mockResolvedValue({
      data: {
        id: 'hg1', goal_type: 'weight_loss', description: 'Lose weight',
        target_value: null, created_at: '',
      },
    }),
    removeHealthGoal: vi.fn().mockResolvedValue({}),
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/profile', name: 'profile', component: { template: '<div/>' } },
    { path: '/household', name: 'household', component: { template: '<div/>' } },
    { path: '/login', name: 'login', component: { template: '<div/>' } },
  ],
})

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(ProfileView, {
    global: { plugins: [pinia, router] },
  })
}

describe('ProfileView', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/profile')
    await router.isReady()
  })

  it('renders heading', () => {
    const wrapper = mountView()
    expect(wrapper.find('h1').text()).toBe('My Profile')
  })

  it('loads preferences and goals on mount', async () => {
    mountView()
    await flushPromises()

    const { usersApi } = await import('@/services/api')
    expect(usersApi.getDietaryPreferences).toHaveBeenCalled()
    expect(usersApi.getHealthGoals).toHaveBeenCalled()
  })

  it('shows user info when authenticated', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(ProfileView, {
      global: { plugins: [pinia, router] },
    })

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.user = {
      id: 'u1', email: 'test@example.com', full_name: 'Test User',
      avatar_url: null, auth_provider: 'local', is_active: true, is_verified: false, created_at: '',
    }
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Test User')
    expect(wrapper.text()).toContain('test@example.com')
  })

  it('renders preference form', () => {
    const wrapper = mountView()
    const selects = wrapper.findAll('select')
    expect(selects.length).toBeGreaterThanOrEqual(2) // pref type + goal type
  })

  it('renders household link', () => {
    const wrapper = mountView()
    expect(wrapper.find('.household-link').text()).toContain('Manage Household')
  })

  it('renders sign out button', () => {
    const wrapper = mountView()
    expect(wrapper.find('.btn-secondary').text()).toBe('Sign Out')
  })

  it('adds a dietary preference via form submission', async () => {
    const wrapper = mountView()
    await flushPromises()

    // Find the preference form (first .add-form)
    const addForms = wrapper.findAll('.add-form')
    const prefForm = addForms[0]

    // Set the select and input values
    await prefForm.find('select').setValue('allergy')
    await prefForm.find('input').setValue('nuts')
    await prefForm.trigger('submit')
    await flushPromises()

    const { usersApi } = await import('@/services/api')
    expect(usersApi.addDietaryPreference).toHaveBeenCalledWith({
      preference_type: 'allergy',
      value: 'nuts',
    })

    // The added preference should appear in the list
    expect(wrapper.text()).toContain('allergy')
    expect(wrapper.text()).toContain('nuts')
  })

  it('removes a dietary preference when remove button is clicked', async () => {
    const { usersApi } = await import('@/services/api')
    vi.mocked(usersApi.getDietaryPreferences).mockResolvedValueOnce({
      data: [
        { id: 'dp1', preference_type: 'allergy', value: 'nuts', notes: null, created_at: '' },
      ],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    // Verify the preference is displayed
    expect(wrapper.text()).toContain('nuts')

    // Find and click the remove button for the preference
    const removeBtn = wrapper.find('.pref-item .remove-btn')
    await removeBtn.trigger('click')
    await flushPromises()

    expect(usersApi.removeDietaryPreference).toHaveBeenCalledWith('dp1')

    // The preference should be removed from the list
    expect(wrapper.findAll('.pref-item').length).toBe(0)
  })

  it('adds a health goal via form submission', async () => {
    const wrapper = mountView()
    await flushPromises()

    // Find the goal form (second .add-form)
    const addForms = wrapper.findAll('.add-form')
    const goalForm = addForms[1]

    await goalForm.find('select').setValue('weight_loss')
    await goalForm.find('input').setValue('Lose weight')
    await goalForm.trigger('submit')
    await flushPromises()

    const { usersApi } = await import('@/services/api')
    expect(usersApi.addHealthGoal).toHaveBeenCalledWith({
      goal_type: 'weight_loss',
      description: 'Lose weight',
    })

    // The added goal should appear in the list
    expect(wrapper.text()).toContain('weight loss')
    expect(wrapper.text()).toContain('Lose weight')
  })

  it('removes a health goal when remove button is clicked', async () => {
    const { usersApi } = await import('@/services/api')
    vi.mocked(usersApi.getHealthGoals).mockResolvedValueOnce({
      data: [
        { id: 'hg1', goal_type: 'weight_loss', description: 'Lose weight', target_value: null, created_at: '' },
      ],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    // Verify the goal is displayed
    expect(wrapper.text()).toContain('Lose weight')

    // Find and click the remove button for the goal
    const removeBtn = wrapper.find('.goal-item .remove-btn')
    await removeBtn.trigger('click')
    await flushPromises()

    expect(usersApi.removeHealthGoal).toHaveBeenCalledWith('hg1')

    // The goal should be removed from the list
    expect(wrapper.findAll('.goal-item').length).toBe(0)
  })

  it('shows error when addPreference fails', async () => {
    const { usersApi } = await import('@/services/api')
    vi.mocked(usersApi.addDietaryPreference).mockRejectedValueOnce(new Error('Server error'))

    const wrapper = mountView()
    await flushPromises()

    const addForms = wrapper.findAll('.add-form')
    const prefForm = addForms[0]

    await prefForm.find('select').setValue('allergy')
    await prefForm.find('input').setValue('peanuts')
    await prefForm.trigger('submit')
    await flushPromises()

    expect(wrapper.find('.error-text').text()).toBe('Failed to add preference')
  })

  it('shows error when addGoal fails', async () => {
    const { usersApi } = await import('@/services/api')
    vi.mocked(usersApi.addHealthGoal).mockRejectedValueOnce(new Error('Server error'))

    const wrapper = mountView()
    await flushPromises()

    const addForms = wrapper.findAll('.add-form')
    const goalForm = addForms[1]

    await goalForm.find('select').setValue('weight_loss')
    await goalForm.find('input').setValue('Some goal')
    await goalForm.trigger('submit')
    await flushPromises()

    expect(wrapper.find('.error-text').text()).toBe('Failed to add goal')
  })

  it('does not add preference when type is empty', async () => {
    const wrapper = mountView()
    await flushPromises()

    const addForms = wrapper.findAll('.add-form')
    const prefForm = addForms[0]

    // Leave select at default empty value, but set input
    await prefForm.find('input').setValue('nuts')
    await prefForm.trigger('submit')
    await flushPromises()

    const { usersApi } = await import('@/services/api')
    expect(usersApi.addDietaryPreference).not.toHaveBeenCalled()
  })

  it('does not add goal when type is empty', async () => {
    const wrapper = mountView()
    await flushPromises()

    const addForms = wrapper.findAll('.add-form')
    const goalForm = addForms[1]

    // Leave select at default empty value, but set input
    await goalForm.find('input').setValue('Some goal')
    await goalForm.trigger('submit')
    await flushPromises()

    const { usersApi } = await import('@/services/api')
    expect(usersApi.addHealthGoal).not.toHaveBeenCalled()
  })

  it('shows auth provider info', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(ProfileView, {
      global: { plugins: [pinia, router] },
    })

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.user = {
      id: 'u1', email: 'test@example.com', full_name: 'Test User',
      avatar_url: null, auth_provider: 'google', is_active: true, is_verified: false, created_at: '',
    }
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.provider').text()).toContain('google')
  })

  it('displays loaded preferences on mount', async () => {
    const { usersApi } = await import('@/services/api')
    vi.mocked(usersApi.getDietaryPreferences).mockResolvedValueOnce({
      data: [
        { id: 'dp1', preference_type: 'allergy', value: 'shellfish', notes: null, created_at: '' },
        { id: 'dp2', preference_type: 'diet', value: 'vegetarian', notes: null, created_at: '' },
      ],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('shellfish')
    expect(wrapper.text()).toContain('vegetarian')
    expect(wrapper.findAll('.pref-item').length).toBe(2)
  })

  it('displays loaded goals on mount', async () => {
    const { usersApi } = await import('@/services/api')
    vi.mocked(usersApi.getHealthGoals).mockResolvedValueOnce({
      data: [
        { id: 'hg1', goal_type: 'increase_protein', description: 'Eat more protein', target_value: null, created_at: '' },
      ],
    } as never)

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('Eat more protein')
    expect(wrapper.findAll('.goal-item').length).toBe(1)
  })

  it('calls authStore.logout when sign out button is clicked', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(ProfileView, {
      global: { plugins: [pinia, router] },
    })
    await flushPromises()

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    const logoutSpy = vi.spyOn(authStore, 'logout')

    await wrapper.find('.btn-secondary').trigger('click')
    expect(logoutSpy).toHaveBeenCalled()
  })
})
