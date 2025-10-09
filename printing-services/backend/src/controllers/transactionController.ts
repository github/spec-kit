import { Request, Response } from 'express'
import { prisma } from '../lib/database'
import { handleStripeWebhook, getTransactionBySessionId, retryPayment } from '../services/stripeService'

// Extend Express Request to include user from auth middleware
interface AuthRequest extends Request {
  user?: {
    id: string
    email: string
    role: string
    status: string
  }
}

// Get transactions (role-based access)
export const getTransactions = async (req: AuthRequest, res: Response) => {
  try {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' })
    }

    let whereClause = {}

    // Role-based filtering
    switch (req.user.role) {
      case 'CUSTOMER':
        // Customers see their own transactions
        whereClause = {
          proposal: {
            request: {
              userId: req.user.id
            }
          }
        }
        break
      case 'BROKER':
        // Brokers see transactions for their proposals
        whereClause = {
          proposal: {
            brokerId: req.user.id
          }
        }
        break
      case 'ADMIN':
        // Admins see all transactions
        whereClause = {}
        break
      default:
        return res.status(403).json({ error: 'Invalid user role' })
    }

    const transactions = await prisma.transaction.findMany({
      where: whereClause,
      include: {
        proposal: {
          include: {
            request: {
              select: { id: true, title: true, userId: true }
            },
            broker: {
              select: { id: true, email: true, companyName: true }
            }
          }
        }
      },
      orderBy: { createdAt: 'desc' }
    })

    res.json({
      transactions,
      count: transactions.length
    })

  } catch (error) {
    console.error('Get transactions error:', error)
    res.status(500).json({
      error: 'Failed to fetch transactions'
    })
  }
}

// Get single transaction
export const getTransaction = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params
    const transactionId = parseInt(id)

    if (isNaN(transactionId)) {
      return res.status(400).json({ error: 'Invalid transaction ID' })
    }

    const transaction = await prisma.transaction.findUnique({
      where: { id: transactionId },
      include: {
        proposal: {
          include: {
            request: {
              include: { user: true }
            },
            broker: true
          }
        }
      }
    })

    if (!transaction) {
      return res.status(404).json({ error: 'Transaction not found' })
    }

    // Access control
    const isCustomer = req.user?.role === 'CUSTOMER' && transaction.proposal.request.userId === req.user.id
    const isBroker = req.user?.role === 'BROKER' && transaction.proposal.brokerId === req.user.id
    const isAdmin = req.user?.role === 'ADMIN'

    if (!isCustomer && !isBroker && !isAdmin) {
      return res.status(403).json({ error: 'Access denied' })
    }

    res.json({ transaction })

  } catch (error) {
    console.error('Get transaction error:', error)
    res.status(500).json({
      error: 'Failed to fetch transaction'
    })
  }
}

// Handle Stripe webhook
export const handleWebhook = async (req: Request, res: Response) => {
  try {
    const signature = req.headers['stripe-signature'] as string
    
    if (!signature) {
      return res.status(400).json({ error: 'Missing Stripe signature' })
    }

    const result = await handleStripeWebhook(signature, req.body)
    
    res.json(result)

  } catch (error) {
    console.error('Webhook error:', error)
    res.status(400).json({ error: 'Webhook processing failed' })
  }
}

// Get payment status by session ID
export const getPaymentStatus = async (req: Request, res: Response) => {
  try {
    const { sessionId } = req.params

    if (!sessionId) {
      return res.status(400).json({ error: 'Session ID required' })
    }

    const transaction = await getTransactionBySessionId(sessionId)

    if (!transaction) {
      return res.status(404).json({ error: 'Transaction not found' })
    }

    res.json({
      status: transaction.status,
      amount: transaction.amount,
      currency: transaction.currency,
      paidAt: transaction.paidAt,
      receiptUrl: transaction.receiptUrl,
      proposal: {
        id: transaction.proposal.id,
        timeline: transaction.proposal.timeline,
        request: {
          title: transaction.proposal.request.title,
          status: transaction.proposal.request.status
        }
      }
    })

  } catch (error) {
    console.error('Get payment status error:', error)
    res.status(500).json({
      error: 'Failed to get payment status'
    })
  }
}

// Retry failed payment
export const retryFailedPayment = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params
    const transactionId = parseInt(id)

    if (isNaN(transactionId)) {
      return res.status(400).json({ error: 'Invalid transaction ID' })
    }

    if (req.user?.role !== 'CUSTOMER') {
      return res.status(403).json({
        error: 'Only customers can retry payments'
      })
    }

    const session = await retryPayment(transactionId, req.user.email)

    res.json({
      message: 'New payment session created',
      paymentUrl: session.url,
      sessionId: session.id
    })

  } catch (error) {
    console.error('Retry payment error:', error)
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to retry payment'
    })
  }
}

// Get transaction statistics (Admin only)
export const getTransactionStats = async (req: AuthRequest, res: Response) => {
  try {
    if (req.user?.role !== 'ADMIN') {
      return res.status(403).json({
        error: 'Admin access required'
      })
    }

    const stats = await prisma.transaction.groupBy({
      by: ['status'],
      _count: {
        id: true
      },
      _sum: {
        amount: true
      }
    })

    const totalTransactions = await prisma.transaction.count()
    const totalRevenue = await prisma.transaction.aggregate({
      where: { status: 'PAID' },
      _sum: { amount: true }
    })

    const recentTransactions = await prisma.transaction.findMany({
      take: 10,
      orderBy: { createdAt: 'desc' },
      include: {
        proposal: {
          include: {
            request: { select: { title: true } },
            broker: { select: { companyName: true, email: true } }
          }
        }
      }
    })

    res.json({
      stats,
      totalTransactions,
      totalRevenue: totalRevenue._sum.amount || 0,
      recentTransactions
    })

  } catch (error) {
    console.error('Get transaction stats error:', error)
    res.status(500).json({
      error: 'Failed to fetch transaction statistics'
    })
  }
}

