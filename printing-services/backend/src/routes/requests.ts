import { Router } from 'express'
import {
  createRequest,
  getRequests,
  getRequest,
  createProposal,
  acceptProposal,
  createRequestValidation,
  createProposalValidation
} from '../controllers/requestController'
import { authenticateToken, requireCustomer, requireBroker, requireAnyRole } from '../middleware/auth'

const router = Router()

// Request routes
router.post('/requests', 
  authenticateToken, 
  requireCustomer, 
  createRequestValidation, 
  createRequest
)

router.get('/requests', 
  authenticateToken, 
  requireAnyRole, 
  getRequests
)

router.get('/requests/:id', 
  authenticateToken, 
  requireAnyRole, 
  getRequest
)

// Proposal routes
router.post('/proposals', 
  authenticateToken, 
  requireBroker, 
  createProposalValidation, 
  createProposal
)

router.patch('/proposals/:id/accept', 
  authenticateToken, 
  requireCustomer, 
  acceptProposal
)

// Health check for requests service
router.get('/health', (req, res) => {
  res.json({
    service: 'Printing Requests',
    status: 'OK',
    timestamp: new Date().toISOString(),
    endpoints: {
      createRequest: 'POST /api/requests (customer only)',
      getRequests: 'GET /api/requests (role-based)',
      getRequest: 'GET /api/requests/:id',
      createProposal: 'POST /api/proposals (broker only)',
      acceptProposal: 'PATCH /api/proposals/:id/accept (customer only)'
    }
  })
})

export default router
