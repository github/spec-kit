import { Router } from 'express'
import {
  getAnalytics,
  exportAnalyticsCSV,
  getAnalyticsSummary
} from '../controllers/analyticsController'
import { authenticateToken, requireAnyRole, requireAdmin } from '../middleware/auth'

const router = Router()

// Analytics data endpoints
router.get('/analytics',
  authenticateToken,
  requireAnyRole, // Both ADMIN and BROKER can access analytics
  getAnalytics
)

// Real-time analytics summary
router.get('/analytics/summary',
  authenticateToken,
  requireAnyRole,
  getAnalyticsSummary
)

// CSV export functionality
router.get('/analytics/export',
  authenticateToken,
  requireAnyRole, // Role-based filtering handled in controller
  exportAnalyticsCSV
)

// Health check for analytics service
router.get('/analytics-health', (req, res) => {
  res.json({
    service: 'Analytics & Business Intelligence',
    status: 'OK',
    timestamp: new Date().toISOString(),
    features: {
      platformAnalytics: 'Admin access to marketplace-wide insights',
      brokerAnalytics: 'Personal performance metrics and trends',
      revenueTracking: 'Real-time financial analytics',
      performanceMetrics: 'Job completion and rating analytics',
      dataExport: 'CSV export with role-based filtering',
      realTimeUpdates: 'Live dashboard updates via WebSocket'
    },
    endpoints: {
      getAnalytics: 'GET /api/analytics?period=30d&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD',
      getSummary: 'GET /api/analytics/summary (real-time daily metrics)',
      exportCSV: 'GET /api/analytics/export?period=30d&format=csv',
      healthCheck: 'GET /api/analytics-health'
    },
    queryParameters: {
      period: 'Time period filter (7d, 30d, 90d, 1y)',
      startDate: 'Custom start date (YYYY-MM-DD format)',
      endDate: 'Custom end date (YYYY-MM-DD format)',
      format: 'Export format (csv)'
    },
    roleAccess: {
      ADMIN: [
        'Platform-wide revenue analytics',
        'All user activity metrics',
        'Top broker performance data',
        'Category breakdown and trends',
        'Monthly revenue and growth metrics',
        'Complete transaction export'
      ],
      BROKER: [
        'Personal earnings and job statistics',
        'Proposal acceptance rates',
        'Review ratings and feedback',
        'Monthly performance trends',
        'Marketplace comparison metrics',
        'Personal transaction export'
      ],
      CUSTOMER: ['No analytics access']
    },
    dataPrivacy: {
      anonymization: 'Customer and broker names anonymized in admin views',
      roleFiltering: 'Users only see data appropriate to their role',
      noPersonalData: 'No PII exposed in analytics aggregations',
      auditLogging: 'All analytics access logged for compliance'
    },
    performance: {
      responseTime: '< 500ms for standard queries',
      caching: 'Expensive calculations cached for performance',
      pagination: 'Large datasets paginated for optimal loading',
      realTimeUpdates: 'Live metrics updated via WebSocket events'
    },
    integrations: {
      transactions: 'Revenue data from Stripe payment processing',
      requests: 'Job volume and category analytics',
      reviews: 'Rating and feedback analytics',
      proposals: 'Broker performance and acceptance rates',
      realTime: 'WebSocket notifications for live updates'
    }
  })
})

export default router
