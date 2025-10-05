import bcrypt from 'bcryptjs'
import jwt from 'jsonwebtoken'
import { UserRole } from '@prisma/client'

// Password validation rules
export const validatePassword = (password: string): { isValid: boolean; errors: string[] } => {
  const errors: string[] = []
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters')
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain uppercase letter')
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain lowercase letter')
  }
  
  if (!/\d/.test(password)) {
    errors.push('Password must contain number')
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
}

// Hash password with bcrypt
export const hashPassword = async (password: string): Promise<string> => {
  const saltRounds = parseInt(process.env.BCRYPT_ROUNDS || '12')
  return bcrypt.hash(password, saltRounds)
}

// Verify password against hash
export const verifyPassword = async (password: string, hash: string): Promise<boolean> => {
  return bcrypt.compare(password, hash)
}

// Generate JWT token
export const generateToken = (user: {
  id: string
  email: string
  role: UserRole
  status: string
}): string => {
  const jwtSecret = process.env.JWT_SECRET
  if (!jwtSecret) {
    throw new Error('JWT_SECRET not configured')
  }

  const expiresIn = process.env.JWT_EXPIRES_IN || '7d'
  
  return jwt.sign(
    {
      userId: user.id,
      email: user.email,
      role: user.role,
      status: user.status
    },
    jwtSecret,
    { expiresIn }
  )
}

// Verify JWT token
export const verifyToken = (token: string): any => {
  const jwtSecret = process.env.JWT_SECRET
  if (!jwtSecret) {
    throw new Error('JWT_SECRET not configured')
  }

  return jwt.verify(token, jwtSecret)
}

// Generate email verification token
export const generateVerificationToken = (userId: string): string => {
  const jwtSecret = process.env.JWT_SECRET
  if (!jwtSecret) {
    throw new Error('JWT_SECRET not configured')
  }

  return jwt.sign(
    { userId, type: 'email_verification' },
    jwtSecret,
    { expiresIn: '24h' }
  )
}

// Verify email verification token
export const verifyEmailToken = (token: string): { userId: string } => {
  const jwtSecret = process.env.JWT_SECRET
  if (!jwtSecret) {
    throw new Error('JWT_SECRET not configured')
  }

  const decoded = jwt.verify(token, jwtSecret) as any
  
  if (decoded.type !== 'email_verification') {
    throw new Error('Invalid token type')
  }

  return { userId: decoded.userId }
}

// Sanitize user data for response (remove sensitive fields)
export const sanitizeUser = (user: any) => {
  const { passwordHash, ...sanitizedUser } = user
  return sanitizedUser
}

// Email validation
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}
