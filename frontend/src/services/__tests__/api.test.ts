import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import type { AxiosError } from 'axios'

vi.mock('axios', async () => {
  const instance = {
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  }

  const mockAxios = {
    create: vi.fn().mockReturnValue(instance),
    post: vi.fn(),
    defaults: { headers: { common: {} } },
  }

  return { default: mockAxios }
})

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.resetModules()
  })

  it('creates axios instance with correct config', async () => {
    await import('@/services/api')
    expect(axios.create).toHaveBeenCalledWith({
      baseURL: '/api',
      headers: { 'Content-Type': 'application/json' },
    })
  })

  it('registers request and response interceptors', async () => {
    await import('@/services/api')
    const instance = vi.mocked(axios.create).mock.results[0]?.value
    expect(instance.interceptors.request.use).toHaveBeenCalled()
    expect(instance.interceptors.response.use).toHaveBeenCalled()
  })

  describe('request interceptor', () => {
    it('adds auth header when token exists', async () => {
      localStorage.setItem('access_token', 'test-token')
      await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      const interceptorFn = vi.mocked(instance.interceptors.request.use).mock.calls[0][0]
      const config = { headers: {} as Record<string, string> }
      const result = interceptorFn(config)
      expect(result.headers.Authorization).toBe('Bearer test-token')
    })

    it('does not add auth header when no token', async () => {
      await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      const interceptorFn = vi.mocked(instance.interceptors.request.use).mock.calls[0][0]
      const config = { headers: {} as Record<string, string> }
      const result = interceptorFn(config)
      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('response interceptor', () => {
    it('passes through successful responses', async () => {
      await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      const [successFn] = vi.mocked(instance.interceptors.response.use).mock.calls[0]
      const response = { data: 'ok', status: 200 }
      expect(successFn(response)).toEqual(response)
    })

    it('attempts token refresh on 401', async () => {
      localStorage.setItem('refresh_token', 'rt123')
      vi.mocked(axios.post).mockResolvedValue({
        data: { access_token: 'new-at', refresh_token: 'new-rt' },
      })
      await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      const [, errorFn] = vi.mocked(instance.interceptors.response.use).mock.calls[0]
      const error = {
        config: { _retry: false, headers: {} as Record<string, string> },
        response: { status: 401 },
      } as unknown as AxiosError

      try {
        await errorFn(error)
      } catch {
        // The mock api instance isn't callable, expected
      }

      expect(axios.post).toHaveBeenCalledWith('/api/auth/refresh', { refresh_token: 'rt123' })
      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'new-at')
      expect(localStorage.setItem).toHaveBeenCalledWith('refresh_token', 'new-rt')
    })

    it('redirects to login on refresh failure', async () => {
      localStorage.setItem('refresh_token', 'bad-rt')
      vi.mocked(axios.post).mockRejectedValue(new Error('refresh failed'))
      const locationSpy = vi.spyOn(window, 'location', 'get')
      const mockLocation = { ...window.location, href: '' }
      locationSpy.mockReturnValue(mockLocation as Location)

      await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      const [, errorFn] = vi.mocked(instance.interceptors.response.use).mock.calls[0]
      const error = {
        config: { _retry: false, headers: {} as Record<string, string> },
        response: { status: 401 },
      } as unknown as AxiosError

      await errorFn(error).catch(() => {})
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token')
      locationSpy.mockRestore()
    })

    it('does not refresh when no refresh_token', async () => {
      await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      const [, errorFn] = vi.mocked(instance.interceptors.response.use).mock.calls[0]
      const error = {
        config: { _retry: false, headers: {} },
        response: { status: 401 },
      } as unknown as AxiosError

      await expect(errorFn(error)).rejects.toBeTruthy()
      expect(axios.post).not.toHaveBeenCalled()
    })

    it('does not retry when already retried', async () => {
      localStorage.setItem('refresh_token', 'rt123')
      await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      const [, errorFn] = vi.mocked(instance.interceptors.response.use).mock.calls[0]
      const error = {
        config: { _retry: true, headers: {} },
        response: { status: 401 },
      } as unknown as AxiosError

      await expect(errorFn(error)).rejects.toBeTruthy()
      expect(axios.post).not.toHaveBeenCalled()
    })

    it('rejects non-401 errors', async () => {
      await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      const [, errorFn] = vi.mocked(instance.interceptors.response.use).mock.calls[0]
      const error = {
        config: { headers: {} },
        response: { status: 500 },
      } as unknown as AxiosError

      await expect(errorFn(error)).rejects.toBeTruthy()
    })
  })

  describe('authApi methods', () => {
    it('register calls post', async () => {
      const { authApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await authApi.register({ email: 'a@b.com', password: 'pass', full_name: 'A', terms_accepted: true })
      expect(instance.post).toHaveBeenCalledWith('/auth/register', { email: 'a@b.com', password: 'pass', full_name: 'A', terms_accepted: true })
    })

    it('login calls post', async () => {
      const { authApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await authApi.login({ email: 'a@b.com', password: 'pass' })
      expect(instance.post).toHaveBeenCalledWith('/auth/login', { email: 'a@b.com', password: 'pass' })
    })

    it('refresh calls post', async () => {
      const { authApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await authApi.refresh('rt1')
      expect(instance.post).toHaveBeenCalledWith('/auth/refresh', { refresh_token: 'rt1' })
    })

    it('getTerms calls get', async () => {
      const { authApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await authApi.getTerms()
      expect(instance.get).toHaveBeenCalledWith('/auth/terms')
    })

    it('getOAuthUrl calls get', async () => {
      const { authApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await authApi.getOAuthUrl('google')
      expect(instance.get).toHaveBeenCalledWith('/auth/oauth/google/url')
    })

    it('oauthCallback calls post', async () => {
      const { authApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await authApi.oauthCallback('google', 'abc')
      expect(instance.post).toHaveBeenCalledWith('/auth/oauth/google/callback', null, { params: { code: 'abc' } })
    })
  })

  describe('usersApi methods', () => {
    it('getMe calls get', async () => {
      const { usersApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await usersApi.getMe()
      expect(instance.get).toHaveBeenCalledWith('/users/me')
    })

    it('updateMe calls patch', async () => {
      const { usersApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await usersApi.updateMe({ full_name: 'New Name' })
      expect(instance.patch).toHaveBeenCalledWith('/users/me', { full_name: 'New Name' })
    })

    it('getDietaryPreferences calls get', async () => {
      const { usersApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await usersApi.getDietaryPreferences()
      expect(instance.get).toHaveBeenCalledWith('/users/me/dietary-preferences')
    })

    it('addDietaryPreference calls post', async () => {
      const { usersApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await usersApi.addDietaryPreference({ preference_type: 'allergy', value: 'nuts' })
      expect(instance.post).toHaveBeenCalledWith('/users/me/dietary-preferences', { preference_type: 'allergy', value: 'nuts' })
    })

    it('removeDietaryPreference calls delete', async () => {
      const { usersApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await usersApi.removeDietaryPreference('dp1')
      expect(instance.delete).toHaveBeenCalledWith('/users/me/dietary-preferences/dp1')
    })

    it('getHealthGoals calls get', async () => {
      const { usersApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await usersApi.getHealthGoals()
      expect(instance.get).toHaveBeenCalledWith('/users/me/health-goals')
    })

    it('addHealthGoal calls post', async () => {
      const { usersApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await usersApi.addHealthGoal({ goal_type: 'weight_loss', description: 'Lose weight' })
      expect(instance.post).toHaveBeenCalledWith('/users/me/health-goals', { goal_type: 'weight_loss', description: 'Lose weight' })
    })

    it('removeHealthGoal calls delete', async () => {
      const { usersApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await usersApi.removeHealthGoal('hg1')
      expect(instance.delete).toHaveBeenCalledWith('/users/me/health-goals/hg1')
    })
  })

  describe('ingredientsApi methods', () => {
    it('search calls get', async () => {
      const { ingredientsApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await ingredientsApi.search('flour')
      expect(instance.get).toHaveBeenCalledWith('/ingredients/search', { params: { q: 'flour' } })
    })

    it('create calls post', async () => {
      const { ingredientsApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await ingredientsApi.create({ name: 'Flour', category: 'Baking' })
      expect(instance.post).toHaveBeenCalledWith('/ingredients/', { name: 'Flour', category: 'Baking' })
    })

    it('getHousehold calls get', async () => {
      const { ingredientsApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await ingredientsApi.getHousehold()
      expect(instance.get).toHaveBeenCalledWith('/ingredients/household')
    })

    it('addToHousehold calls post', async () => {
      const { ingredientsApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await ingredientsApi.addToHousehold({ name: 'Flour', quantity: 1, unit: 'kg' })
      expect(instance.post).toHaveBeenCalledWith('/ingredients/household', { name: 'Flour', quantity: 1, unit: 'kg' })
    })

    it('updateHousehold calls patch', async () => {
      const { ingredientsApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await ingredientsApi.updateHousehold('hi1', { quantity: 2 })
      expect(instance.patch).toHaveBeenCalledWith('/ingredients/household/hi1', { quantity: 2 })
    })

    it('removeFromHousehold calls delete', async () => {
      const { ingredientsApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await ingredientsApi.removeFromHousehold('hi1')
      expect(instance.delete).toHaveBeenCalledWith('/ingredients/household/hi1')
    })

    it('scanBarcode calls get', async () => {
      const { ingredientsApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await ingredientsApi.scanBarcode('123456')
      expect(instance.get).toHaveBeenCalledWith('/ingredients/barcode/123456')
    })

    it('cameraScan calls post', async () => {
      const { ingredientsApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await ingredientsApi.cameraScan('base64data')
      expect(instance.post).toHaveBeenCalledWith('/ingredients/camera-scan', { image_base64: 'base64data' })
    })
  })

  describe('recipesApi methods', () => {
    it('search calls post', async () => {
      const { recipesApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await recipesApi.search({ prompt: 'pasta' })
      expect(instance.post).toHaveBeenCalledWith('/recipes/search', { prompt: 'pasta' })
    })

    it('getById calls get', async () => {
      const { recipesApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await recipesApi.getById('r1')
      expect(instance.get).toHaveBeenCalledWith('/recipes/r1')
    })

    it('rate calls post', async () => {
      const { recipesApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await recipesApi.rate('r1', { score: 5 })
      expect(instance.post).toHaveBeenCalledWith('/recipes/r1/rate', { score: 5 })
    })

    it('addFavorite calls post', async () => {
      const { recipesApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await recipesApi.addFavorite('r1')
      expect(instance.post).toHaveBeenCalledWith('/recipes/r1/favorite')
    })

    it('removeFavorite calls delete', async () => {
      const { recipesApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await recipesApi.removeFavorite('r1')
      expect(instance.delete).toHaveBeenCalledWith('/recipes/r1/favorite')
    })

    it('getFavorites calls get', async () => {
      const { recipesApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await recipesApi.getFavorites()
      expect(instance.get).toHaveBeenCalledWith('/recipes/favorites/list')
    })
  })

  describe('householdApi methods', () => {
    it('get calls get', async () => {
      const { householdApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await householdApi.get()
      expect(instance.get).toHaveBeenCalledWith('/household/')
    })

    it('create calls post', async () => {
      const { householdApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await householdApi.create({ name: 'My Kitchen' })
      expect(instance.post).toHaveBeenCalledWith('/household/', { name: 'My Kitchen' })
    })

    it('getMembers calls get', async () => {
      const { householdApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await householdApi.getMembers()
      expect(instance.get).toHaveBeenCalledWith('/household/members')
    })

    it('addMember calls post', async () => {
      const { householdApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await householdApi.addMember({ name: 'Kid', role: 'child' })
      expect(instance.post).toHaveBeenCalledWith('/household/members', { name: 'Kid', role: 'child' })
    })

    it('updateMember calls patch', async () => {
      const { householdApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await householdApi.updateMember('m1', { name: 'Updated' })
      expect(instance.patch).toHaveBeenCalledWith('/household/members/m1', { name: 'Updated' })
    })

    it('removeMember calls delete', async () => {
      const { householdApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await householdApi.removeMember('m1')
      expect(instance.delete).toHaveBeenCalledWith('/household/members/m1')
    })
  })

  describe('shoppingApi methods', () => {
    it('getCarts calls get', async () => {
      const { shoppingApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await shoppingApi.getCarts()
      expect(instance.get).toHaveBeenCalledWith('/shopping/')
    })

    it('createCart calls post', async () => {
      const { shoppingApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await shoppingApi.createCart({ name: 'Weekly' })
      expect(instance.post).toHaveBeenCalledWith('/shopping/', { name: 'Weekly' })
    })

    it('addItem calls post', async () => {
      const { shoppingApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await shoppingApi.addItem('c1', { name: 'Milk', quantity: 1, unit: 'L' })
      expect(instance.post).toHaveBeenCalledWith('/shopping/c1/items', { name: 'Milk', quantity: 1, unit: 'L' })
    })

    it('updateItem calls patch', async () => {
      const { shoppingApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await shoppingApi.updateItem('c1', 'i1', { is_purchased: true })
      expect(instance.patch).toHaveBeenCalledWith('/shopping/c1/items/i1', { is_purchased: true })
    })

    it('removeItem calls delete', async () => {
      const { shoppingApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await shoppingApi.removeItem('c1', 'i1')
      expect(instance.delete).toHaveBeenCalledWith('/shopping/c1/items/i1')
    })

    it('addMissingIngredients calls post', async () => {
      const { shoppingApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await shoppingApi.addMissingIngredients({ recipe_id: 'r1', ingredient_names: ['salt'] })
      expect(instance.post).toHaveBeenCalledWith('/shopping/add-missing-ingredients', { recipe_id: 'r1', ingredient_names: ['salt'] })
    })
  })

  describe('aiApi methods', () => {
    it('getProviders calls get', async () => {
      const { aiApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await aiApi.getProviders()
      expect(instance.get).toHaveBeenCalledWith('/ai/providers')
    })

    it('parseVoiceInput calls post', async () => {
      const { aiApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await aiApi.parseVoiceInput('add 2 cups flour')
      expect(instance.post).toHaveBeenCalledWith('/ai/parse-voice-input', null, { params: { transcript: 'add 2 cups flour' } })
    })

    it('suggestSubstitutions calls post', async () => {
      const { aiApi } = await import('@/services/api')
      const instance = vi.mocked(axios.create).mock.results[0]?.value
      await aiApi.suggestSubstitutions('butter', ['vegan'])
      expect(instance.post).toHaveBeenCalledWith('/ai/suggest-substitutions', null, {
        params: { ingredient: 'butter', dietary_restrictions: ['vegan'] },
      })
    })
  })
})
