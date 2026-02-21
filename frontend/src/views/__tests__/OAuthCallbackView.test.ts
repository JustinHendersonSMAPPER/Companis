import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import OAuthCallbackView from '@/views/OAuthCallbackView.vue'

vi.mock('@/services/api', () => ({
  authApi: {
    register: vi.fn(),
    login: vi.fn(),
    getOAuthUrl: vi.fn(),
    oauthCallback: vi.fn(),
  },
  usersApi: {
    getMe: vi.fn(),
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/oauth/callback/:provider', name: 'oauth-callback', component: OAuthCallbackView },
    { path: '/', name: 'home', component: { template: '<div/>' } },
    { path: '/login', name: 'login', component: { template: '<div/>' } },
  ],
})

describe('OAuthCallbackView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls handleOAuthCallback on mount with provider and code', async () => {
    await router.push('/oauth/callback/google?code=auth123')
    await router.isReady()

    const pinia = createPinia()
    setActivePinia(pinia)

    mount(OAuthCallbackView, {
      global: { plugins: [pinia, router] },
    })

    await flushPromises()
    // The component calls authStore.handleOAuthCallback which uses authApi.oauthCallback
    const { authApi } = await import('@/services/api')
    expect(authApi.oauthCallback).toHaveBeenCalledWith('google', 'auth123')
  })

  it('renders loading state', async () => {
    await router.push('/oauth/callback/google?code=auth123')
    await router.isReady()

    const pinia = createPinia()
    setActivePinia(pinia)

    const wrapper = mount(OAuthCallbackView, {
      global: { plugins: [pinia, router] },
    })

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.loading = true
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Completing sign in...')
  })

  it('shows error message', async () => {
    await router.push('/oauth/callback/google?code=auth123')
    await router.isReady()

    const pinia = createPinia()
    setActivePinia(pinia)

    const wrapper = mount(OAuthCallbackView, {
      global: { plugins: [pinia, router] },
    })

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.error = 'OAuth failed'
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-text').text()).toBe('OAuth failed')
  })
})
