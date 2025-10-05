import { Router } from 'express'
import {
  register,
  login,
  verifyEmail,
  resendVerification,
  logout,
  getProfile,
  registerValidation,
  loginValidation
} from '@/controllers/authController'
import { authenticateToken } from '@/middleware/auth'

const router = Router()

// Public routes
router.post('/register', registerValidation, register)
router.post('/login', loginValidation, login)
router.get('/verify-email/:token', verifyEmail)
router.post('/resend-verification', resendVerification)
router.post('/logout', logout)

// Protected routes
router.get('/profile', authenticateToken, getProfile)

// Health check for auth service
router.get('/health', (req, res) => {
  res.json({
    service: 'Authentication',
    status: 'OK',
    timestamp: new Date().toISOString(),
    endpoints: {
      register: 'POST /api/auth/register',
      login: 'POST /api/auth/login',
      verifyEmail: 'GET /api/auth/verify-email/:token',
      resendVerification: 'POST /api/auth/resend-verification',
      logout: 'POST /api/auth/logout',
      profile: 'GET /api/auth/profile (protected)'
    }
  })
})

export default router
