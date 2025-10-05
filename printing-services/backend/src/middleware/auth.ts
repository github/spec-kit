import { Request, Response, NextFunction } from 'express'
import jwt from 'jsonwebtoken'
// Using string literals instead of enums for SQLite compatibility
type UserRole = 'CUSTOMER' | 'BROKER' | 'ADMIN'

// Extend Express Request type to include user
declare global {
  namespace Express {
    interface Request {
      user?: {
        id: string
        email: string
        role: UserRole
        status: string
      }
    }
  }
}

interface JWTPayload {
  userId: string
  email: string
  role: UserRole
  status: string
  iat: number
  exp: number
}

export const authenticateToken = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const authHeader = req.headers.authorization
    const token = authHeader && authHeader.split(' ')[1] // Bearer TOKEN

    if (!token) {
      return res.status(401).json({ error: 'Access token required' })
    }

    const jwtSecret = process.env.JWT_SECRET
    if (!jwtSecret) {
      console.error('JWT_SECRET not configured')
      return res.status(500).json({ error: 'Server configuration error' })
    }

    const decoded = jwt.verify(token, jwtSecret) as JWTPayload
    
    // Check if token is expired (additional safety check)
    if (Date.now() >= decoded.exp * 1000) {
      return res.status(401).json({ error: 'Token expired' })
    }

    // Attach user info to request
    req.user = {
      id: decoded.userId,
      email: decoded.email,
      role: decoded.role,
      status: decoded.status
    }

    next()
  } catch (error) {
    if (error instanceof jwt.JsonWebTokenError) {
      return res.status(401).json({ error: 'Invalid token' })
    }
    if (error instanceof jwt.TokenExpiredError) {
      return res.status(401).json({ error: 'Token expired' })
    }
    
    console.error('Authentication error:', error)
    return res.status(500).json({ error: 'Authentication failed' })
  }
}

export const requireRole = (allowedRoles: UserRole[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' })
    }

    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Insufficient permissions' })
    }

    // Check if user is verified (except for admin)
    if (req.user.role !== 'ADMIN' && req.user.status !== 'VERIFIED') {
      return res.status(403).json({ 
        error: 'Account verification required',
        userStatus: req.user.status
      })
    }

    next()
  }
}

// Convenience middleware for common role checks
export const requireCustomer = requireRole(['CUSTOMER'])
export const requireBroker = requireRole(['BROKER'])
export const requireAdmin = requireRole(['ADMIN'])
export const requireCustomerOrBroker = requireRole(['CUSTOMER', 'BROKER'])
export const requireAnyRole = requireRole(['CUSTOMER', 'BROKER', 'ADMIN'])
