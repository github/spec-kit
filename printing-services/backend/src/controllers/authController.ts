import { Request, Response } from 'express'
import { body, validationResult } from 'express-validator'
import { prisma } from '../lib/database'
import {
  validatePassword,
  hashPassword,
  verifyPassword,
  generateToken,
  generateVerificationToken,
  verifyEmailToken,
  sanitizeUser,
  validateEmail
} from '../utils/auth'
import { sendVerificationEmail } from '../services/emailService'

// Validation rules
export const registerValidation = [
  body('email').isEmail().normalizeEmail().withMessage('Valid email required'),
  body('password').isLength({ min: 8 }).withMessage('Password must be at least 8 characters'),
  body('firstName').trim().isLength({ min: 1 }).withMessage('First name required'),
  body('lastName').trim().isLength({ min: 1 }).withMessage('Last name required'),
  body('role').isIn(['CUSTOMER', 'BROKER']).withMessage('Role must be CUSTOMER or BROKER'),
  body('companyName').optional().trim()
]

export const loginValidation = [
  body('email').isEmail().normalizeEmail().withMessage('Valid email required'),
  body('password').notEmpty().withMessage('Password required')
]

// Register new user
export const register = async (req: Request, res: Response) => {
  try {
    // Check validation errors
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      })
    }

    const { email, password, firstName, lastName, role, companyName } = req.body

    // Additional password validation
    const passwordValidation = validatePassword(password)
    if (!passwordValidation.isValid) {
      return res.status(400).json({
        error: 'Password validation failed',
        details: passwordValidation.errors
      })
    }

    // Check if email already exists
    const existingUser = await prisma.user.findUnique({
      where: { email }
    })

    if (existingUser) {
      return res.status(409).json({
        error: 'Email already registered'
      })
    }

    // Validate broker requirements
    if (role === 'BROKER' && !companyName) {
      return res.status(400).json({
        error: 'Company name required for brokers'
      })
    }

    // Hash password
    const passwordHash = await hashPassword(password)

    // Create user
    const user = await prisma.user.create({
      data: {
        email,
        passwordHash,
        firstName,
        lastName,
        role: role,
        status: 'PENDING',
        companyName: role === 'BROKER' ? companyName : undefined
      }
    })

    // Generate verification token
    const verificationToken = generateVerificationToken(user.id)

    // Send verification email
    try {
      await sendVerificationEmail(email, firstName, user.id)
    } catch (emailError) {
      console.error('Failed to send verification email:', emailError)
      // Continue with registration even if email fails
    }

    res.status(201).json({
      message: 'Registration successful. Please check your email for verification.',
      user: sanitizeUser(user)
    })

  } catch (error) {
    console.error('Registration error:', error)
    res.status(500).json({
      error: 'Registration failed'
    })
  }
}

// Login user
export const login = async (req: Request, res: Response) => {
  try {
    // Check validation errors
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      })
    }

    const { email, password } = req.body

    // Find user by email
    const user = await prisma.user.findUnique({
      where: { email }
    })

    if (!user) {
      return res.status(401).json({
        error: 'Invalid credentials'
      })
    }

    // Verify password
    const isValidPassword = await verifyPassword(password, user.passwordHash)
    if (!isValidPassword) {
      return res.status(401).json({
        error: 'Invalid credentials'
      })
    }

    // Check if email is verified
    if (!user.emailVerified) {
      return res.status(403).json({
        error: 'Please verify your email before logging in',
        canResendVerification: true
      })
    }

    // Update last login
    await prisma.user.update({
      where: { id: user.id },
      data: { lastLoginAt: new Date() }
    })

    // Generate JWT token
    const token = generateToken({
      id: user.id,
      email: user.email,
      role: user.role,
      status: user.status
    })

    // Set secure cookie (in production)
    if (process.env.NODE_ENV === 'production') {
      res.cookie('token', token, {
        httpOnly: true,
        secure: true,
        sameSite: 'strict',
        maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
      })
    }

    res.json({
      message: 'Login successful',
      token,
      user: sanitizeUser(user)
    })

  } catch (error) {
    console.error('Login error:', error)
    res.status(500).json({
      error: 'Login failed'
    })
  }
}

// Verify email
export const verifyEmail = async (req: Request, res: Response) => {
  try {
    const { token } = req.params

    if (!token) {
      return res.status(400).json({
        error: 'Verification token required'
      })
    }

    // Verify token
    const { userId } = verifyEmailToken(token)

    // Update user
    const user = await prisma.user.update({
      where: { id: userId },
      data: {
        emailVerified: true,
        emailVerifiedAt: new Date(),
        status: 'VERIFIED' // Auto-verify customers, brokers need manual approval
      }
    })

    res.json({
      message: 'Email verified successfully',
      user: sanitizeUser(user)
    })

  } catch (error) {
    console.error('Email verification error:', error)
    
    if (error instanceof Error && error.message.includes('jwt')) {
      return res.status(400).json({
        error: 'Invalid or expired verification token'
      })
    }

    res.status(500).json({
      error: 'Email verification failed'
    })
  }
}

// Resend verification email
export const resendVerification = async (req: Request, res: Response) => {
  try {
    const { email } = req.body

    if (!validateEmail(email)) {
      return res.status(400).json({
        error: 'Valid email required'
      })
    }

    const user = await prisma.user.findUnique({
      where: { email }
    })

    if (!user) {
      // Don't reveal if email exists
      return res.json({
        message: 'If the email exists, a verification link has been sent'
      })
    }

    if (user.emailVerified) {
      return res.status(400).json({
        error: 'Email already verified'
      })
    }

    // Generate new verification token
    const verificationToken = generateVerificationToken(user.id)

    // TODO: Send verification email
    console.log(`New verification token for ${email}: ${verificationToken}`)

    res.json({
      message: 'Verification email sent'
    })

  } catch (error) {
    console.error('Resend verification error:', error)
    res.status(500).json({
      error: 'Failed to resend verification email'
    })
  }
}

// Logout user
export const logout = async (req: Request, res: Response) => {
  try {
    // Clear cookie
    res.clearCookie('token')

    res.json({
      message: 'Logout successful'
    })

  } catch (error) {
    console.error('Logout error:', error)
    res.status(500).json({
      error: 'Logout failed'
    })
  }
}

// Get current user profile
export const getProfile = async (req: Request, res: Response) => {
  try {
    if (!req.user) {
      return res.status(401).json({
        error: 'Authentication required'
      })
    }

    const user = await prisma.user.findUnique({
      where: { id: req.user.id }
    })

    if (!user) {
      return res.status(404).json({
        error: 'User not found'
      })
    }

    res.json({
      user: sanitizeUser(user)
    })

  } catch (error) {
    console.error('Get profile error:', error)
    res.status(500).json({
      error: 'Failed to get profile'
    })
  }
}

