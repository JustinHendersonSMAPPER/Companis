import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import RegisterView from '@/views/RegisterView.vue'

vi.mock('@/services/api', () => ({
  authApi: {
    register: vi.fn().mockResolvedValue({
      data: {
        id: 'u1', email: 'new@example.com', full_name: 'New User',
        avatar_url: null, auth_provider: 'local', is_active: true,
        is_verified: false, created_at: '',
      },
    }),
    login: vi.fn().mockResolvedValue({
      data: { access_token: 'tok', refresh_token: 'ref', token_type: 'bearer' },
    }),
    getTerms: vi.fn().mockResolvedValue({ data: { terms_text: 'Test terms content' } }),
    getOAuthUrl: vi.fn(),
    oauthCallback: vi.fn(),
  },
  usersApi: {
    getMe: vi.fn().mockResolvedValue({
      data: {
        id: 'u1', email: 'new@example.com', full_name: 'New User',
        avatar_url: null, auth_provider: 'local', is_active: true,
        is_verified: false, created_at: '',
      },
    }),
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/register', name: 'register', component: { template: '<div/>' } },
    { path: '/login', name: 'login', component: { template: '<div/>' } },
    { path: '/', name: 'home', component: { template: '<div/>' } },
  ],
})

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(RegisterView, {
    global: { plugins: [pinia, router] },
  })
}

describe('RegisterView', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/register')
    await router.isReady()
  })

  it('renders registration form with all fields', () => {
    const wrapper = mountView()
    expect(wrapper.find('h1').text()).toBe('Create Account')
    expect(wrapper.find('#fullName').exists()).toBe(true)
    expect(wrapper.find('#email').exists()).toBe(true)
    expect(wrapper.find('#password').exists()).toBe(true)
    expect(wrapper.find('#confirmPassword').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').text()).toBe('Create Account')
  })

  it('loads terms on mount', async () => {
    const wrapper = mountView()
    await flushPromises()

    const { authApi } = await import('@/services/api')
    expect(authApi.getTerms).toHaveBeenCalled()

    // Toggle terms to verify loaded content
    await wrapper.find('.terms-toggle').trigger('click')
    expect(wrapper.find('.terms-text').text()).toBe('Test terms content')
  })

  it('toggles terms visibility', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.terms-content').exists()).toBe(false)
    expect(wrapper.find('.terms-toggle').text()).toContain('View')

    await wrapper.find('.terms-toggle').trigger('click')
    expect(wrapper.find('.terms-content').exists()).toBe(true)
    expect(wrapper.find('.terms-toggle').text()).toContain('Hide')

    await wrapper.find('.terms-toggle').trigger('click')
    expect(wrapper.find('.terms-content').exists()).toBe(false)
  })

  it('shows password mismatch validation error', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('#fullName').setValue('Test User')
    await wrapper.find('#email').setValue('test@example.com')
    await wrapper.find('#password').setValue('password123')
    await wrapper.find('#confirmPassword').setValue('differentpassword')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.error-text').text()).toBe('Passwords do not match')

    const { authApi } = await import('@/services/api')
    expect(authApi.register).not.toHaveBeenCalled()
  })

  it('shows password too short validation error', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('#fullName').setValue('Test User')
    await wrapper.find('#email').setValue('test@example.com')
    await wrapper.find('#password').setValue('short')
    await wrapper.find('#confirmPassword').setValue('short')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.error-text').text()).toBe('Password must be at least 8 characters')

    const { authApi } = await import('@/services/api')
    expect(authApi.register).not.toHaveBeenCalled()
  })

  it('shows terms not accepted validation error', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('#fullName').setValue('Test User')
    await wrapper.find('#email').setValue('test@example.com')
    await wrapper.find('#password').setValue('password123')
    await wrapper.find('#confirmPassword').setValue('password123')
    // Do NOT check the terms checkbox

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.error-text').text()).toBe('You must accept the terms and conditions')

    const { authApi } = await import('@/services/api')
    expect(authApi.register).not.toHaveBeenCalled()
  })

  it('submits form successfully when all validations pass', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('#fullName').setValue('New User')
    await wrapper.find('#email').setValue('new@example.com')
    await wrapper.find('#password').setValue('password123')
    await wrapper.find('#confirmPassword').setValue('password123')
    await wrapper.find('.terms-checkbox input[type="checkbox"]').setValue(true)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { authApi } = await import('@/services/api')
    expect(authApi.register).toHaveBeenCalledWith({
      email: 'new@example.com',
      password: 'password123',
      full_name: 'New User',
      terms_accepted: true,
    })
  })

  it('renders login link', () => {
    const wrapper = mountView()
    expect(wrapper.find('.auth-link').text()).toContain('Already have an account?')
    expect(wrapper.find('.auth-link a').attributes('href')).toBe('/login')
  })

  it('renders terms checkbox label', () => {
    const wrapper = mountView()
    expect(wrapper.find('.terms-checkbox').exists()).toBe(true)
    expect(wrapper.find('.terms-checkbox').text()).toContain('I have read and agree')
  })

  it('renders subtitle text', () => {
    const wrapper = mountView()
    expect(wrapper.find('.auth-subtitle').text()).toBe('Pull up a chair.')
  })

  it('clears validation error on subsequent valid submit', async () => {
    const wrapper = mountView()
    await flushPromises()

    // First: trigger password mismatch
    await wrapper.find('#fullName').setValue('Test User')
    await wrapper.find('#email').setValue('test@example.com')
    await wrapper.find('#password').setValue('password123')
    await wrapper.find('#confirmPassword').setValue('different')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('.error-text').text()).toBe('Passwords do not match')

    // Now fix and submit again with matching passwords but no terms
    await wrapper.find('#password').setValue('password123')
    await wrapper.find('#confirmPassword').setValue('password123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    // validationError is now the terms error (previous mismatch was cleared)
    expect(wrapper.find('.error-text').text()).toBe('You must accept the terms and conditions')
  })

  it('shows fallback text when getTerms fails', async () => {
    const { authApi } = await import('@/services/api')
    vi.mocked(authApi.getTerms).mockRejectedValueOnce(new Error('Network error'))

    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('.terms-toggle').trigger('click')
    expect(wrapper.find('.terms-text').text()).toBe('Unable to load terms. Please try again later.')
  })

  it('clicking link-btn inside checkbox label shows terms', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.terms-content').exists()).toBe(false)
    await wrapper.find('.link-btn').trigger('click')
    expect(wrapper.find('.terms-content').exists()).toBe(true)
  })

  it('disables submit button when loading', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(RegisterView, {
      global: { plugins: [pinia, router] },
    })
    await flushPromises()

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.loading = true

    await wrapper.vm.$nextTick()
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.attributes('disabled')).toBeDefined()
    expect(btn.text()).toBe('Creating account...')
  })

  it('calls login after successful registration', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('#fullName').setValue('New User')
    await wrapper.find('#email').setValue('new@example.com')
    await wrapper.find('#password').setValue('password123')
    await wrapper.find('#confirmPassword').setValue('password123')
    await wrapper.find('.terms-checkbox input[type="checkbox"]').setValue(true)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { authApi } = await import('@/services/api')
    // The auth store's register method calls register then login
    expect(authApi.register).toHaveBeenCalled()
    expect(authApi.login).toHaveBeenCalledWith({
      email: 'new@example.com',
      password: 'password123',
    })
  })
})
