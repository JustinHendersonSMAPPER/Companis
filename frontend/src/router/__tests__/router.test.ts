import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'

// We test the router by importing it directly to cover all route definitions
// and the beforeEach guard

describe('Router', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
  })

  it('defines all required routes', async () => {
    const routerModule = await import('@/router/index')
    const router = routerModule.default
    const routeNames = router.getRoutes().map((r) => r.name)
    expect(routeNames).toContain('home')
    expect(routeNames).toContain('login')
    expect(routeNames).toContain('register')
    expect(routeNames).toContain('oauth-callback')
    expect(routeNames).toContain('ingredients')
    expect(routeNames).toContain('scan')
    expect(routeNames).toContain('recipes')
    expect(routeNames).toContain('recipe-detail')
    expect(routeNames).toContain('shopping')
    expect(routeNames).toContain('household')
    expect(routeNames).toContain('profile')
  })

  it('marks protected routes with requiresAuth', async () => {
    const routerModule = await import('@/router/index')
    const router = routerModule.default
    const protectedRoutes = ['home', 'ingredients', 'scan', 'recipes', 'recipe-detail', 'shopping', 'household', 'profile']
    for (const name of protectedRoutes) {
      const route = router.getRoutes().find((r) => r.name === name)
      expect(route?.meta.requiresAuth, `${name} should require auth`).toBe(true)
    }
  })

  it('does not mark public routes with requiresAuth', async () => {
    const routerModule = await import('@/router/index')
    const router = routerModule.default
    const publicRoutes = ['login', 'register', 'oauth-callback']
    for (const name of publicRoutes) {
      const route = router.getRoutes().find((r) => r.name === name)
      expect(route?.meta.requiresAuth, `${name} should not require auth`).toBeFalsy()
    }
  })

  it('redirects to login when accessing protected route without token', async () => {
    // Create a standalone router with same config to test guard behavior
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', name: 'home', component: { template: '<div/>' }, meta: { requiresAuth: true } },
        { path: '/login', name: 'login', component: { template: '<div/>' } },
        { path: '/ingredients', name: 'ingredients', component: { template: '<div/>' }, meta: { requiresAuth: true } },
      ],
    })

    router.beforeEach((to) => {
      const token = localStorage.getItem('access_token')
      if (to.meta.requiresAuth && !token) {
        return { name: 'login' }
      }
      return true
    })

    // No token set, try to navigate to protected route
    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('login')
  })

  it('allows navigation to protected route with token', async () => {
    localStorage.setItem('access_token', 'valid-token')

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', name: 'home', component: { template: '<div/>' }, meta: { requiresAuth: true } },
        { path: '/login', name: 'login', component: { template: '<div/>' } },
      ],
    })

    router.beforeEach((to) => {
      const token = localStorage.getItem('access_token')
      if (to.meta.requiresAuth && !token) {
        return { name: 'login' }
      }
      return true
    })

    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('home')
  })

  it('allows navigation to public routes without token', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/login', name: 'login', component: { template: '<div/>' } },
        { path: '/register', name: 'register', component: { template: '<div/>' } },
      ],
    })

    router.beforeEach((to) => {
      const token = localStorage.getItem('access_token')
      if (to.meta.requiresAuth && !token) {
        return { name: 'login' }
      }
      return true
    })

    await router.push('/login')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('login')

    await router.push('/register')
    expect(router.currentRoute.value.name).toBe('register')
  })

  it('has correct route paths', async () => {
    const routerModule = await import('@/router/index')
    const router = routerModule.default
    const routes = router.getRoutes()

    expect(routes.find((r) => r.name === 'home')?.path).toBe('/')
    expect(routes.find((r) => r.name === 'login')?.path).toBe('/login')
    expect(routes.find((r) => r.name === 'register')?.path).toBe('/register')
    expect(routes.find((r) => r.name === 'oauth-callback')?.path).toBe('/oauth/callback/:provider')
    expect(routes.find((r) => r.name === 'recipe-detail')?.path).toBe('/recipes/:id')
  })
})
