import { useState, useEffect, createContext, useContext, ReactNode } from 'react'
import { User, authAPI } from '@/services/api'
import toast from 'react-hot-toast'

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  updateUser: (userData: Partial<User>) => void
}

interface RegisterData {
  email: string
  password: string
  firstName: string
  lastName: string
  role: 'CUSTOMER' | 'BROKER'
  companyName?: string
  businessNumber?: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user && !!token

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem('token')
        const storedUser = localStorage.getItem('user')

        if (storedToken && storedUser) {
          setToken(storedToken)
          setUser(JSON.parse(storedUser))
          
          // Verify token is still valid by fetching fresh user data
          try {
            const response = await authAPI.getProfile()
            setUser(response.data.user)
            localStorage.setItem('user', JSON.stringify(response.data.user))
          } catch (error) {
            // Token is invalid, clear auth state
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            setToken(null)
            setUser(null)
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true)
      const response = await authAPI.login({ email, password })
      const { token: newToken, user: userData } = response.data

      setToken(newToken)
      setUser(userData)
      
      localStorage.setItem('token', newToken)
      localStorage.setItem('user', JSON.stringify(userData))
      
      toast.success('Login successful!')
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Login failed'
      toast.error(errorMessage)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (data: RegisterData) => {
    try {
      setIsLoading(true)
      const response = await authAPI.register(data)
      
      // Registration successful, but user needs to verify email
      toast.success('Registration successful! Please check your email for verification.')
      
      // Don't auto-login, redirect to verification page
      return response.data
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Registration failed'
      toast.error(errorMessage)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    
    // Call logout API to invalidate token on server (optional)
    authAPI.logout().catch(console.error)
    
    toast.success('Logged out successfully')
  }

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData }
      setUser(updatedUser)
      localStorage.setItem('user', JSON.stringify(updatedUser))
    }
  }

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    updateUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// Hook for protected routes
export const useRequireAuth = (requiredRoles?: string[]) => {
  const { user, isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      window.location.href = '/login'
      return
    }

    if (user && requiredRoles && !requiredRoles.includes(user.role)) {
      toast.error('Access denied: Insufficient permissions')
      window.location.href = '/'
      return
    }

    if (user && user.status !== 'VERIFIED' && user.role !== 'ADMIN') {
      toast.error('Please verify your account to access this feature')
      window.location.href = '/verify-account'
      return
    }
  }, [user, isAuthenticated, isLoading, requiredRoles])

  return { user, isAuthenticated, isLoading }
}
