import { describe, it, expect } from 'vitest'
import { authService } from '../services/authService'

describe('authService', () => {
  it('storeTokens and hasTokens work correctly', () => {
    authService.storeTokens({ access_token: 'at', refresh_token: 'rt', token_type: 'bearer' })
    expect(authService.hasTokens()).toBe(true)
    authService.clearTokens()
    expect(authService.hasTokens()).toBe(false)
  })
})
