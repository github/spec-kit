import axios from 'axios'

// API base configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API functions
export const authAPI = {
  register: (data: RegisterData) => 
    api.post('/api/auth/register', data),
  
  login: (data: LoginData) => 
    api.post('/api/auth/login', data),
  
  verifyEmail: (token: string) => 
    api.get(`/api/auth/verify-email/${token}`),
  
  resendVerification: (email: string) => 
    api.post('/api/auth/resend-verification', { email }),
  
  getProfile: () => 
    api.get('/api/auth/profile'),
  
  updateProfile: (data: Partial<User>) => 
    api.patch('/api/auth/profile', data),
  
  logout: () => 
    api.post('/api/auth/logout'),
}

// User API functions
export const userAPI = {
  getUsers: (params?: UserQueryParams) => 
    api.get('/api/users', { params }),
  
  getUser: (id: string) => 
    api.get(`/api/users/${id}`),
  
  updateUser: (id: string, data: Partial<User>) => 
    api.patch(`/api/users/${id}`, data),
}

// Admin API functions
export const adminAPI = {
  getPendingBrokers: () => 
    api.get('/api/admin/pending-brokers'),
  
  approveBroker: (id: string) => 
    api.post(`/api/admin/approve-broker/${id}`),
  
  rejectBroker: (id: string, reason: string) => 
    api.post(`/api/admin/reject-broker/${id}`, { reason }),
  
  getStats: () => 
    api.get('/api/admin/stats'),
}

// Type definitions
export interface RegisterData {
  email: string
  password: string
  firstName: string
  lastName: string
  role: 'CUSTOMER' | 'BROKER'
  companyName?: string
  businessNumber?: string
}

export interface LoginData {
  email: string
  password: string
}

export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  role: 'CUSTOMER' | 'BROKER' | 'ADMIN'
  status: 'PENDING' | 'VERIFIED' | 'SUSPENDED' | 'BANNED'
  emailVerified: boolean
  emailVerifiedAt?: string
  phone?: string
  companyName?: string
  businessNumber?: string
  createdAt: string
  updatedAt: string
  lastLoginAt?: string
}

export interface UserQueryParams {
  role?: string
  status?: string
  search?: string
  page?: number
  limit?: number
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  error: string
  details?: string[]
}
