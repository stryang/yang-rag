import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/lib/api'
import { authApi } from '@/lib/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.login({ username, password })
          const { access_token, user } = response

          localStorage.setItem('access_token', access_token)
          localStorage.setItem('user', JSON.stringify(user))

          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error: unknown) {
          const errorMessage =
            error instanceof Error && 'response' in error
              ? ((error as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
                  'Login failed')
              : 'Login failed'
          set({ isLoading: false, error: errorMessage })
          throw error
        }
      },

      logout: async () => {
        try {
          await authApi.logout()
        } catch {
          // Ignore logout errors
        } finally {
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          })
        }
      },

      checkAuth: async () => {
        const token = localStorage.getItem('access_token')
        const userStr = localStorage.getItem('user')

        if (!token || !userStr) {
          set({ isAuthenticated: false })
          return
        }

        try {
          const user = JSON.parse(userStr) as User
          set({ user, token, isAuthenticated: true })
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          set({ isAuthenticated: false })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
