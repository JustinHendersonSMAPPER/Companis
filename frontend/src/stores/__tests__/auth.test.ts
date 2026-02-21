import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

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

vi.mock('@/router', () => ({
  default: { push: vi.fn() },
}))

import { authApi, usersApi } from '@/services/api'
import router from '@/router'

const mockUser = {
  id: 'u1',
  email: 'test@example.com',
  full_name: 'Test User',
  avatar_url: null,
  auth_provider: 'local',
  is_active: true,
  is_verified: false,
  created_at: '2024-01-01',
}

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('has correct initial state', () => {
    const store = useAuthStore()
    expect(store.user).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  describe('initialize', () => {
    it('fetches user when token exists', async () => {
      localStorage.setItem('access_token', 'tok123')
      vi.mocked(usersApi.getMe).mockResolvedValue({ data: mockUser } as never)

      const store = useAuthStore()
      await store.initialize()

      expect(usersApi.getMe).toHaveBeenCalled()
      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
    })

    it('does nothing when no token', async () => {
      const store = useAuthStore()
      await store.initialize()
      expect(usersApi.getMe).not.toHaveBeenCalled()
      expect(store.user).toBeNull()
    })

    it('clears tokens on failed initialization', async () => {
      localStorage.setItem('access_token', 'bad-token')
      vi.mocked(usersApi.getMe).mockRejectedValue(new Error('401'))

      const store = useAuthStore()
      await store.initialize()

      expect(store.user).toBeNull()
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token')
    })
  })

  describe('login', () => {
    it('stores tokens and fetches user on success', async () => {
      vi.mocked(authApi.login).mockResolvedValue({
        data: { access_token: 'at', refresh_token: 'rt', token_type: 'bearer' },
      } as never)
      vi.mocked(usersApi.getMe).mockResolvedValue({ data: mockUser } as never)

      const store = useAuthStore()
      await store.login('test@example.com', 'password123')

      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'at')
      expect(localStorage.setItem).toHaveBeenCalledWith('refresh_token', 'rt')
      expect(store.user).toEqual(mockUser)
      expect(router.push).toHaveBeenCalledWith('/')
      expect(store.loading).toBe(false)
    })

    it('sets error on failure', async () => {
      vi.mocked(authApi.login).mockRejectedValue({
        response: { data: { detail: 'Invalid credentials' } },
      })

      const store = useAuthStore()
      await expect(store.login('bad@example.com', 'wrong')).rejects.toBeTruthy()

      expect(store.error).toBe('Invalid credentials')
      expect(store.loading).toBe(false)
    })

    it('uses fallback error message', async () => {
      vi.mocked(authApi.login).mockRejectedValue(new Error('Network error'))

      const store = useAuthStore()
      await expect(store.login('test@example.com', 'pass')).rejects.toBeTruthy()

      expect(store.error).toBe('Login failed')
    })
  })

  describe('register', () => {
    it('registers then logs in', async () => {
      vi.mocked(authApi.register).mockResolvedValue({ data: mockUser } as never)
      vi.mocked(authApi.login).mockResolvedValue({
        data: { access_token: 'at', refresh_token: 'rt', token_type: 'bearer' },
      } as never)
      vi.mocked(usersApi.getMe).mockResolvedValue({ data: mockUser } as never)

      const store = useAuthStore()
      await store.register('test@example.com', 'password123', 'Test User')

      expect(authApi.register).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        full_name: 'Test User',
        terms_accepted: true,
      })
      expect(store.loading).toBe(false)
    })

    it('sets error on registration failure', async () => {
      vi.mocked(authApi.register).mockRejectedValue({
        response: { data: { detail: 'Email taken' } },
      })

      const store = useAuthStore()
      await expect(store.register('taken@example.com', 'pass', 'Test')).rejects.toBeTruthy()

      expect(store.error).toBe('Email taken')
    })
  })

  describe('loginWithOAuth', () => {
    it('redirects to OAuth URL', async () => {
      vi.mocked(authApi.getOAuthUrl).mockResolvedValue({
        data: { authorization_url: 'https://oauth.example.com/auth' },
      } as never)

      // Mock window.location
      const locationSpy = vi.spyOn(window, 'location', 'get')
      const mockLocation = { ...window.location, href: '' }
      locationSpy.mockReturnValue(mockLocation as Location)

      const store = useAuthStore()
      await store.loginWithOAuth('google')

      expect(authApi.getOAuthUrl).toHaveBeenCalledWith('google')
      expect(mockLocation.href).toBe('https://oauth.example.com/auth')

      locationSpy.mockRestore()
    })

    it('sets error on OAuth URL failure', async () => {
      vi.mocked(authApi.getOAuthUrl).mockRejectedValue({
        response: { data: { detail: 'Not configured' } },
      })

      const store = useAuthStore()
      await store.loginWithOAuth('google')

      expect(store.error).toBe('Not configured')
    })
  })

  describe('handleOAuthCallback', () => {
    it('exchanges code for tokens and fetches user', async () => {
      vi.mocked(authApi.oauthCallback).mockResolvedValue({
        data: { access_token: 'oat', refresh_token: 'ort', token_type: 'bearer' },
      } as never)
      vi.mocked(usersApi.getMe).mockResolvedValue({ data: mockUser } as never)

      const store = useAuthStore()
      await store.handleOAuthCallback('google', 'auth-code')

      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'oat')
      expect(store.user).toEqual(mockUser)
      expect(router.push).toHaveBeenCalledWith('/')
      expect(store.loading).toBe(false)
    })

    it('sets error on callback failure', async () => {
      vi.mocked(authApi.oauthCallback).mockRejectedValue(new Error('fail'))

      const store = useAuthStore()
      await store.handleOAuthCallback('google', 'bad-code')

      expect(store.error).toBe('OAuth callback failed')
      expect(store.loading).toBe(false)
    })
  })

  describe('logout', () => {
    it('clears state and redirects', () => {
      const store = useAuthStore()
      store.user = mockUser

      store.logout()

      expect(store.user).toBeNull()
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token')
      expect(router.push).toHaveBeenCalledWith('/login')
    })
  })
})
