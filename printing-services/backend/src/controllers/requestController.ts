import { Request, Response } from 'express'
import { body, validationResult } from 'express-validator'
import { prisma } from '../lib/database'

// Extend Express Request to include user from auth middleware
interface AuthRequest extends Request {
  user?: {
    id: string
    email: string
    role: string
    status: string
  }
}

// Validation rules for request creation
export const createRequestValidation = [
  body('title').trim().isLength({ min: 1 }).withMessage('Title is required'),
  body('description').optional().trim(),
  body('specs').isObject().withMessage('Specifications must be an object'),
  body('specs.type').isIn(['business-cards', 'flyers', 'banners', 'brochures', 'other']).withMessage('Invalid print type'),
  body('specs.quantity').isInt({ min: 1 }).withMessage('Quantity must be at least 1'),
]

// Create printing request (Customer only)
export const createRequest = async (req: AuthRequest, res: Response) => {
  try {
    // Check validation errors
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      })
    }

    // Ensure user is customer
    if (req.user?.role !== 'CUSTOMER') {
      return res.status(403).json({
        error: 'Only customers can create requests'
      })
    }

    const { title, description, specs } = req.body

    // Create the request
    const request = await prisma.printingRequest.create({
      data: {
        title,
        description,
        specs,
        status: 'PENDING',
        userId: req.user.id
      },
      include: {
        user: {
          select: { id: true, email: true, role: true }
        },
        proposals: {
          include: {
            broker: {
              select: { id: true, email: true, companyName: true }
            }
          }
        }
      }
    })

    res.status(201).json({
      message: 'Request created successfully',
      request
    })

  } catch (error) {
    console.error('Create request error:', error)
    res.status(500).json({
      error: 'Failed to create request'
    })
  }
}

// Get requests (role-based access)
export const getRequests = async (req: AuthRequest, res: Response) => {
  try {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' })
    }

    let whereClause = {}

    // Role-based filtering
    switch (req.user.role) {
      case 'CUSTOMER':
        // Customers see only their own requests
        whereClause = { userId: req.user.id }
        break
      case 'BROKER':
        // Brokers see only PENDING requests (available jobs)
        whereClause = { status: 'PENDING' }
        break
      case 'ADMIN':
        // Admins see all requests
        whereClause = {}
        break
      default:
        return res.status(403).json({ error: 'Invalid user role' })
    }

    const requests = await prisma.printingRequest.findMany({
      where: whereClause,
      include: {
        user: {
          select: { id: true, email: true, role: true }
        },
        proposals: {
          include: {
            broker: {
              select: { id: true, email: true, companyName: true }
            }
          },
          orderBy: { createdAt: 'desc' }
        }
      },
      orderBy: { createdAt: 'desc' }
    })

    res.json({
      requests,
      count: requests.length
    })

  } catch (error) {
    console.error('Get requests error:', error)
    res.status(500).json({
      error: 'Failed to fetch requests'
    })
  }
}

// Get single request with details
export const getRequest = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params
    const requestId = parseInt(id)

    if (isNaN(requestId)) {
      return res.status(400).json({ error: 'Invalid request ID' })
    }

    const request = await prisma.printingRequest.findUnique({
      where: { id: requestId },
      include: {
        user: {
          select: { id: true, email: true, role: true }
        },
        proposals: {
          include: {
            broker: {
              select: { id: true, email: true, companyName: true }
            }
          },
          orderBy: { createdAt: 'desc' }
        }
      }
    })

    if (!request) {
      return res.status(404).json({ error: 'Request not found' })
    }

    // Access control
    if (req.user?.role === 'CUSTOMER' && request.userId !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' })
    }

    res.json({ request })

  } catch (error) {
    console.error('Get request error:', error)
    res.status(500).json({
      error: 'Failed to fetch request'
    })
  }
}

// Validation rules for proposal creation
export const createProposalValidation = [
  body('requestId').isInt({ min: 1 }).withMessage('Valid request ID required'),
  body('price').isFloat({ min: 0.01 }).withMessage('Price must be greater than 0'),
  body('timeline').trim().isLength({ min: 1 }).withMessage('Timeline is required'),
  body('details').optional().trim()
]

// Create proposal (Broker only)
export const createProposal = async (req: AuthRequest, res: Response) => {
  try {
    // Check validation errors
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      })
    }

    // Ensure user is broker
    if (req.user?.role !== 'BROKER') {
      return res.status(403).json({
        error: 'Only brokers can submit proposals'
      })
    }

    const { requestId, price, timeline, details } = req.body

    // Check if request exists and is available for proposals
    const request = await prisma.printingRequest.findUnique({
      where: { id: requestId }
    })

    if (!request) {
      return res.status(404).json({ error: 'Request not found' })
    }

    if (request.status !== 'PENDING') {
      return res.status(400).json({
        error: 'This request is no longer accepting proposals'
      })
    }

    // Check if broker already has a proposal for this request
    const existingProposal = await prisma.proposal.findUnique({
      where: {
        requestId_brokerId: {
          requestId: requestId,
          brokerId: req.user.id
        }
      }
    })

    if (existingProposal) {
      return res.status(409).json({
        error: 'You have already submitted a proposal for this request'
      })
    }

    // Create the proposal
    const proposal = await prisma.proposal.create({
      data: {
        requestId,
        brokerId: req.user.id,
        price,
        timeline,
        details
      },
      include: {
        broker: {
          select: { id: true, email: true, companyName: true }
        },
        request: {
          select: { id: true, title: true, status: true }
        }
      }
    })

    // Update request status to PROPOSED
    await prisma.printingRequest.update({
      where: { id: requestId },
      data: { status: 'PROPOSED' }
    })

    res.status(201).json({
      message: 'Proposal submitted successfully',
      proposal
    })

  } catch (error) {
    console.error('Create proposal error:', error)
    res.status(500).json({
      error: 'Failed to create proposal'
    })
  }
}

// Accept proposal (Customer only)
export const acceptProposal = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params
    const proposalId = parseInt(id)

    if (isNaN(proposalId)) {
      return res.status(400).json({ error: 'Invalid proposal ID' })
    }

    // Ensure user is customer
    if (req.user?.role !== 'CUSTOMER') {
      return res.status(403).json({
        error: 'Only customers can accept proposals'
      })
    }

    // Get proposal with request details
    const proposal = await prisma.proposal.findUnique({
      where: { id: proposalId },
      include: {
        request: true,
        broker: {
          select: { id: true, email: true, companyName: true }
        }
      }
    })

    if (!proposal) {
      return res.status(404).json({ error: 'Proposal not found' })
    }

    // Ensure customer owns the request
    if (proposal.request.userId !== req.user.id) {
      return res.status(403).json({
        error: 'You can only accept proposals for your own requests'
      })
    }

    // Check if request is in valid state for acceptance
    if (proposal.request.status !== 'PROPOSED') {
      return res.status(400).json({
        error: 'Request is not in a state that allows proposal acceptance'
      })
    }

    // Accept the proposal and update request status
    const updatedProposal = await prisma.proposal.update({
      where: { id: proposalId },
      data: { isAccepted: true },
      include: {
        broker: {
          select: { id: true, email: true, companyName: true }
        },
        request: true
      }
    })

    // Update request status to APPROVED
    await prisma.printingRequest.update({
      where: { id: proposal.requestId },
      data: { status: 'APPROVED' }
    })

    res.json({
      message: 'Proposal accepted successfully! Next steps will be communicated via email.',
      proposal: updatedProposal
    })

  } catch (error) {
    console.error('Accept proposal error:', error)
    res.status(500).json({
      error: 'Failed to accept proposal'
    })
  }
}

