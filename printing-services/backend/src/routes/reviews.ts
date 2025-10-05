import { Router } from 'express'
import {
  submitReview,
  submitReviewValidation,
  getBrokerReviews,
  checkReviewEligibility,
  getReviewStats
} from '../controllers/reviewController'
import { authenticateToken, requireAnyRole, requireAdmin } from '../middleware/auth'

const router = Router()

// Review submission routes
router.post('/reviews',
  authenticateToken,
  requireAnyRole,
  submitReviewValidation,
  submitReview
)

// Review eligibility check
router.get('/reviews/eligibility/:requestId',
  authenticateToken,
  requireAnyRole,
  checkReviewEligibility
)

// Broker review routes
router.get('/brokers/:brokerId/reviews',
  getBrokerReviews // Public endpoint - no auth required for viewing reviews
)

// Admin statistics
router.get('/reviews/stats',
  authenticateToken,
  requireAdmin,
  getReviewStats
)

// Health check for review service
router.get('/reviews-health', (req, res) => {
  res.json({
    service: 'Review & Rating System',
    status: 'OK',
    timestamp: new Date().toISOString(),
    features: {
      reviewSubmission: 'Active',
      ratingCalculation: 'Cached',
      eligibilityCheck: 'Validated',
      brokerProfiles: 'Public',
      realTimeNotifications: 'WebSocket Enabled',
      moderation: 'Auto-Approved'
    },
    endpoints: {
      submitReview: 'POST /api/reviews',
      checkEligibility: 'GET /api/reviews/eligibility/:requestId',
      getBrokerReviews: 'GET /api/brokers/:brokerId/reviews',
      getReviewStats: 'GET /api/reviews/stats (admin only)'
    },
    validation: {
      starsRange: '1-5 integer',
      commentMaxLength: '500 characters',
      eligibilityRequirements: [
        'Customer role only',
        'Request status: COMPLETED',
        'Payment confirmed',
        'No existing review',
        'Accepted proposal exists'
      ]
    },
    integration: {
      realTimeNotifications: 'Broker receives instant notification',
      systemMessages: 'Auto-posted to conversation',
      ratingCache: 'Updated on broker profile',
      anonymization: 'Customer names protected'
    }
  })
})

export default router
