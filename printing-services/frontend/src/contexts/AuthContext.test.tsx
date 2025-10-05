import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '../contexts/AuthContext'
import { BrowserRouter } from 'react-router-dom'

describe('AuthContext', () => {
  it('should provide auth context', () => {
    const wrapper = ({ children }: any) => (
      <BrowserRouter>
        <AuthProvider>{children}</AuthProvider>
      </BrowserRouter>
    )
    
    const { result } = renderHook(() => useAuth(), { wrapper })
    
    expect(result.current).toBeDefined()
    expect(result.current.user).toBeNull()
    expect(result.current.isLoading).toBe(false)
  })
})
