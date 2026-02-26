import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'

vi.mock('@/services/api', () => ({
  authApi: {
    register: vi.fn(),
    login: vi.fn().mockResolvedValue({
      data: { access_token: 'tok', refresh_token: 'ref', token_type: 'bearer' },
    }),
    getOAuthUrl: vi.fn().mockResolvedValue({
      data: { authorization_url: 'https://accounts.google.com/o/oauth2' },
    }),
    oauthCallback: vi.fn(),
  },
  usersApi: {
    getMe: vi.fn().mockResolvedValue({
      data: {
        id: 'u1', email: 'test@example.com', full_name: 'Test User',
        avatar_url: null, auth_provider: 'local', is_active: true,
        is_verified: false, created_at: '',
      },
    }),
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/login', name: 'login', component: { template: '<div/>' } },
    { path: '/register', name: 'register', component: { template: '<div/>' } },
    { path: '/', name: 'home', component: { template: '<div/>' } },
  ],
})

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(LoginView, {
    global: { plugins: [pinia, router] },
  })
}

describe('LoginView', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/login')
    await router.isReady()
  })

  it('renders login form with email and password fields', () => {
    const wrapper = mountView()
    expect(wrapper.find('h1').text()).toBe('Companis')
    expect(wrapper.find('#email').exists()).toBe(true)
    expect(wrapper.find('#password').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').text()).toBe('Sign In')
  })

  it('renders OAuth buttons', () => {
    const wrapper = mountView()
    expect(wrapper.find('.oauth-btn.google').text()).toBe('Google')
    expect(wrapper.find('.oauth-btn.facebook').text()).toBe('Facebook')
  })

  it('renders register link', () => {
    const wrapper = mountView()
    expect(wrapper.find('.auth-link').text()).toContain("Don't have an account?")
    expect(wrapper.find('.auth-link a').attributes('href')).toBe('/register')
  })

  it('submits form and calls authStore.login with email and password', async () => {
    const wrapper = mountView()

    await wrapper.find('#email').setValue('test@example.com')
    await wrapper.find('#password').setValue('password123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { authApi, usersApi } = await import('@/services/api')
    expect(authApi.login).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    })
    expect(usersApi.getMe).toHaveBeenCalled()
  })

  it('clicks Google button and triggers loginWithOAuth', async () => {
    const wrapper = mountView()

    const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
      ...window.location,
      href: '',
      set href(_url: string) { /* noop */ },
    } as Location)

    await wrapper.find('.oauth-btn.google').trigger('click')
    await flushPromises()

    const { authApi } = await import('@/services/api')
    expect(authApi.getOAuthUrl).toHaveBeenCalledWith('google')

    locationSpy.mockRestore()
  })

  it('clicks Facebook button and triggers loginWithOAuth', async () => {
    const wrapper = mountView()

    const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
      ...window.location,
      href: '',
      set href(_url: string) { /* noop */ },
    } as Location)

    await wrapper.find('.oauth-btn.facebook').trigger('click')
    await flushPromises()

    const { authApi } = await import('@/services/api')
    expect(authApi.getOAuthUrl).toHaveBeenCalledWith('facebook')

    locationSpy.mockRestore()
  })

  it('shows error when authStore has error', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(LoginView, {
      global: { plugins: [pinia, router] },
    })

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.error = 'Invalid credentials'

    await wrapper.vm.$nextTick()
    expect(wrapper.find('.error-text').exists()).toBe(true)
    expect(wrapper.find('.error-text').text()).toBe('Invalid credentials')
  })

  it('disables submit button when loading', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(LoginView, {
      global: { plugins: [pinia, router] },
    })

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.loading = true

    await wrapper.vm.$nextTick()
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.attributes('disabled')).toBeDefined()
    expect(btn.text()).toBe('Signing in...')
  })

  it('renders subtitle text', () => {
    const wrapper = mountView()
    expect(wrapper.find('.auth-subtitle').text()).toBe('Pull up a chair.')
  })

  it('renders divider with "or continue with" text', () => {
    const wrapper = mountView()
    expect(wrapper.find('.divider').text()).toContain('or continue with')
  })

  it('displays login error when authApi.login rejects', async () => {
    const { authApi } = await import('@/services/api')
    vi.mocked(authApi.login).mockRejectedValueOnce({
      response: { data: { detail: 'Bad credentials' } },
    })

    const wrapper = mountView()

    await wrapper.find('#email').setValue('bad@example.com')
    await wrapper.find('#password').setValue('wrongpass')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    expect(authStore.error).toBe('Bad credentials')
    expect(wrapper.find('.error-text').text()).toBe('Bad credentials')
  })

  it('has correct input types for email and password', () => {
    const wrapper = mountView()
    expect(wrapper.find('#email').attributes('type')).toBe('email')
    expect(wrapper.find('#password').attributes('type')).toBe('password')
  })

  it('has required attribute on email and password inputs', () => {
    const wrapper = mountView()
    expect(wrapper.find('#email').attributes('required')).toBeDefined()
    expect(wrapper.find('#password').attributes('required')).toBeDefined()
  })
})
