import api from './api'
import type { LoginPayload, RegisterPayload, TokenPair, User } from '../types'

export const authService = {
  register: async (payload: RegisterPayload): Promise<TokenPair> => {
    const { data } = await api.post<TokenPair>('/auth/register', payload)
    return data
  },

  login: async (payload: LoginPayload): Promise<TokenPair> => {
    const { data } = await api.post<TokenPair>('/auth/login', payload)
    return data
  },

  logout: async (refreshToken: string): Promise<void> => {
    await api.post('/auth/logout', { refresh_token: refreshToken })
  },

  getMe: async (): Promise<User> => {
    const { data } = await api.get<User>('/auth/me')
    return data
  },

  storeTokens: (tokens: TokenPair): void => {
    localStorage.setItem('access_token',  tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
  },

  clearTokens: (): void => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  hasTokens: (): boolean => !!localStorage.getItem('access_token'),
}
