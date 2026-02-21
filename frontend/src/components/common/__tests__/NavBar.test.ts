import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import NavBar from '@/components/common/NavBar.vue'

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
    { path: '/ingredients', name: 'ingredients', component: { template: '<div>Ingredients</div>' } },
    { path: '/scan', name: 'scan', component: { template: '<div>Scan</div>' } },
    { path: '/recipes', name: 'recipes', component: { template: '<div>Recipes</div>' } },
    { path: '/shopping', name: 'shopping', component: { template: '<div>Shopping</div>' } },
    { path: '/login', name: 'login', component: { template: '<div>Login</div>' } },
  ],
})

describe('NavBar', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('does not render when not authenticated', async () => {
    await router.push('/')
    await router.isReady()

    const wrapper = mount(NavBar, {
      global: {
        plugins: [createPinia(), router],
      },
    })

    expect(wrapper.find('.bottom-nav').exists()).toBe(false)
  })

  it('renders nav items when authenticated', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    await router.push('/')
    await router.isReady()

    const wrapper = mount(NavBar, {
      global: {
        plugins: [pinia, router],
      },
    })

    // Set auth state after mount
    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.user = {
      id: 'u1',
      email: 'test@example.com',
      full_name: 'Test',
      avatar_url: null,
      auth_provider: 'local',
      is_active: true,
      is_verified: false,
      created_at: '2024-01-01',
    }

    await wrapper.vm.$nextTick()

    expect(wrapper.find('.bottom-nav').exists()).toBe(true)
    const navItems = wrapper.findAll('.nav-item')
    expect(navItems.length).toBe(5) // Home, Pantry, Scan, Recipes, Shop
  })

  it('shows correct navigation labels', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    await router.push('/')
    await router.isReady()

    const wrapper = mount(NavBar, {
      global: {
        plugins: [pinia, router],
      },
    })

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.user = {
      id: 'u1',
      email: 'test@example.com',
      full_name: 'Test',
      avatar_url: null,
      auth_provider: 'local',
      is_active: true,
      is_verified: false,
      created_at: '2024-01-01',
    }

    await wrapper.vm.$nextTick()

    const labels = wrapper.findAll('.nav-label').map((el) => el.text())
    expect(labels).toContain('Home')
    expect(labels).toContain('Pantry')
    expect(labels).toContain('Scan')
    expect(labels).toContain('Recipes')
    expect(labels).toContain('Shop')
  })

  it('marks active route', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    await router.push('/recipes')
    await router.isReady()

    const wrapper = mount(NavBar, {
      global: {
        plugins: [pinia, router],
      },
    })

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    authStore.user = {
      id: 'u1',
      email: 'test@example.com',
      full_name: 'Test',
      avatar_url: null,
      auth_provider: 'local',
      is_active: true,
      is_verified: false,
      created_at: '2024-01-01',
    }

    await wrapper.vm.$nextTick()

    const activeItems = wrapper.findAll('.nav-item.active')
    expect(activeItems.length).toBe(1)
    expect(activeItems[0].find('.nav-label').text()).toBe('Recipes')
  })
})
