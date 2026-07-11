import axios, { AxiosError } from 'axios'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: attach access token ─────────────────────── //
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Response interceptor: handle errors + auto-refresh ───────────── //
let isRefreshing = false

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }
    const isAuthEndpoint = originalRequest?.url?.includes('/auth/login') ||
                           originalRequest?.url?.includes('/auth/register')

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !isRefreshing) {
        isRefreshing = true
        originalRequest._retry = true
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', data.access_token)
          api.defaults.headers.common.Authorization = `Bearer ${data.access_token}`
          isRefreshing = false
          return api(originalRequest)
        } catch {
          isRefreshing = false
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(error)
        }
      }
    }

    if (error.response?.status === 403) {
      toast.error('You do not have permission to perform this action.')
    } else if (error.response?.status === 404) {
      // Let individual calls handle 404
    } else if (error.response?.status === 429) {
      toast.error('Too many requests. Please slow down.')
    } else if (error.response && error.response.status >= 500) {
      toast.error('Server error. Please try again later.')
    }

    return Promise.reject(error)
  },
)

export default api
