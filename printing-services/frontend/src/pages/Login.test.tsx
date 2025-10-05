import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Login from '../pages/Login'
import { AuthProvider } from '../contexts/AuthContext'

describe('Login Page', () => {
  it('renders login form', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </BrowserRouter>
    )
    
    expect(screen.getByText('PrintMarket')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })
  
  it('validates email input', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </BrowserRouter>
    )
    
    const emailInput = screen.getByPlaceholderText('you@example.com')
    expect(emailInput).toHaveAttribute('type', 'email')
    expect(emailInput).toBeRequired()
  })
})
