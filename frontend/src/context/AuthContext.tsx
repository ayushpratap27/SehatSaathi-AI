import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authService } from '../services/authService'
import type { LoginPayload, RegisterPayload, User } from '../types'

interface AuthState {
  user:        User | null
  isLoading:   boolean
  isAuthenticated: boolean
}

interface AuthContextValue extends AuthState {
  login:    (payload: LoginPayload)    => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout:   () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const [state, setState] = useState<AuthState>({
    user:            null,
    isLoading:       true,
    isAuthenticated: false,
  })

  const refreshUser = useCallback(async () => {
    if (!authService.hasTokens()) {
      setState({ user: null, isLoading: false, isAuthenticated: false })
      return
    }
    try {
      const user = await authService.getMe()
      setState({ user, isLoading: false, isAuthenticated: true })
    } catch {
      authService.clearTokens()
      setState({ user: null, isLoading: false, isAuthenticated: false })
    }
  }, [])

  useEffect(() => { refreshUser() }, [refreshUser])

  const login = useCallback(async (payload: LoginPayload) => {
    const tokens = await authService.login(payload)
    authService.storeTokens(tokens)
    const user = await authService.getMe()
    setState({ user, isLoading: false, isAuthenticated: true })
    toast.success(`Welcome back, ${user.username}!`)
    navigate('/dashboard')
  }, [navigate])

  const register = useCallback(async (payload: RegisterPayload) => {
    const tokens = await authService.register(payload)
    authService.storeTokens(tokens)
    const user = await authService.getMe()
    setState({ user, isLoading: false, isAuthenticated: true })
    toast.success('Account created! Welcome to SehatSaathi-AI.')
    navigate('/dashboard')
  }, [navigate])

  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem('refresh_token') ?? ''
    try { await authService.logout(refreshToken) } catch { /* ignore */ }
    authService.clearTokens()
    setState({ user: null, isLoading: false, isAuthenticated: false })
    toast.success('Logged out successfully.')
    navigate('/login')
  }, [navigate])

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
