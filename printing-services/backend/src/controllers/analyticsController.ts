import { Request, Response } from 'express'
import { prisma } from '../lib/database'
import { sendUserNotification } from '../services/websocketService'
import { format, startOfMonth, endOfMonth, subMonths } from 'date-fns'

// Extend Express Request to include user from auth middleware
interface AuthRequest extends Request {
  user?: {
    id: number
    email: string
    role: string
    status: string
  }
}

// Helper function to parse date range from query parameters
const parseDateRange = (req: Request) => {
  const { startDate, endDate, period = '30d' } = req.query
  
  if (startDate && endDate) {
    return {
      gte: new Date(startDate as string),
      lte: new Date(endDate as string)
    }
  }
  
  const now = new Date()
  switch (period) {
    case '7d':
      return { gte: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000), lte: now }
    case '90d':
      return { gte: new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000), lte: now }
    case '1y':
      return { gte: new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000), lte: now }
    default: // 30d
      return { gte: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000), lte: now }
  }
}

// Helper function to extract category from request specs
const extractCategory = (specs: any): string => {
  try {
    const parsed = typeof specs === 'string' ? JSON.parse(specs) : specs
    return parsed?.type || 'other'
  } catch {
    return 'other'
  }
}

// Get comprehensive analytics data
export const getAnalytics = async (req: AuthRequest, res: Response) => {
  try {
    const { role, id: userId } = req.user!
    
    if (!['ADMIN', 'BROKER'].includes(role)) {
      return res.status(403).json({ error: 'Analytics access denied' })
    }

    const { gte, lte } = parseDateRange(req)
    const dateFilter = { createdAt: { gte, lte } }

    let analytics: any = {
      period: {
        start: format(gte, 'yyyy-MM-dd'),
        end: format(lte, 'yyyy-MM-dd')
      }
    }

    if (role === 'ADMIN') {
      // Platform-wide analytics for admins
      
      // Revenue analytics
      const revenueData = await prisma.transaction.aggregate({
        where: { 
          ...dateFilter, 
          status: 'PAID' 
        },
        _sum: { amount: true },
        _count: true,
        _avg: { amount: true }
      })

      analytics.revenue = {
        total: revenueData._sum.amount || 0,
        transactions: revenueData._count || 0,
        average: Math.round((revenueData._avg.amount || 0) * 100) / 100
      }

      // Request analytics by status
      analytics.requestsByStatus = await prisma.printingRequest.groupBy({
        by: ['status'],
        where: dateFilter,
        _count: { id: true }
      })

      // Top performing brokers
      const topBrokers = await prisma.proposal.groupBy({
        by: ['brokerId'],
        where: { 
          ...dateFilter, 
          isAccepted: true 
        },
        _count: { id: true },
        orderBy: { _count: { id: 'desc' } },
        take: 10
      })

      // Get broker details for top performers
      const brokerIds = topBrokers.map(b => b.brokerId)
      const brokerDetails = await prisma.user.findMany({
        where: { id: { in: brokerIds } },
        select: { 
          id: true, 
          email: true, 
          companyName: true, 
          averageRating: true,
          totalReviews: true 
        }
      })

      analytics.topBrokers = topBrokers.map(broker => {
        const details = brokerDetails.find(d => d.id === broker.brokerId)
        return {
          brokerId: broker.brokerId,
          jobsWon: broker._count.id,
          companyName: details?.companyName || 'Unknown',
          email: details?.email ? `${details.email.charAt(0)}***@${details.email.split('@')[1]}` : 'Unknown',
          averageRating: details?.averageRating || 0,
          totalReviews: details?.totalReviews || 0
        }
      })

      // Category breakdown
      const requests = await prisma.printingRequest.findMany({
        where: dateFilter,
        select: { specs: true }
      })

      const categoryBreakdown = requests.reduce((acc: Record<string, number>, request) => {
        const category = extractCategory(request.specs)
        acc[category] = (acc[category] || 0) + 1
        return acc
      }, {})

      analytics.categoryBreakdown = Object.entries(categoryBreakdown).map(([name, count]) => ({
        name,
        value: count
      }))

      // Monthly trends
      const monthlyRevenue = await prisma.transaction.groupBy({
        by: ['createdAt'],
        where: { 
          status: 'PAID',
          createdAt: { gte: subMonths(lte, 12), lte }
        },
        _sum: { amount: true },
        _count: true
      })

      // Group by month
      const monthlyData = monthlyRevenue.reduce((acc: Record<string, any>, transaction) => {
        const month = format(transaction.createdAt, 'yyyy-MM')
        if (!acc[month]) {
          acc[month] = { month, revenue: 0, transactions: 0 }
        }
        acc[month].revenue += transaction._sum.amount || 0
        acc[month].transactions += transaction._count || 0
        return acc
      }, {})

      analytics.monthlyTrends = Object.values(monthlyData).sort((a: any, b: any) => 
        a.month.localeCompare(b.month)
      )

      // Platform statistics
      analytics.platformStats = {
        totalUsers: await prisma.user.count(),
        totalRequests: await prisma.printingRequest.count(),
        totalReviews: await prisma.review.count(),
        averageRating: await prisma.review.aggregate({
          _avg: { stars: true }
        }).then(result => Math.round((result._avg.stars || 0) * 10) / 10)
      }

    } else if (role === 'BROKER') {
      // Broker-specific analytics
      
      // Earnings and job statistics
      const earnings = await prisma.transaction.aggregate({
        where: {
          ...dateFilter,
          proposal: { brokerId: userId },
          status: 'PAID'
        },
        _sum: { amount: true },
        _count: true
      })

      analytics.earnings = {
        total: earnings._sum.amount || 0,
        transactions: earnings._count || 0
      }

      // Proposal statistics
      const proposalStats = await prisma.proposal.aggregate({
        where: {
          brokerId: userId,
          ...dateFilter
        },
        _count: true
      })

      const acceptedProposals = await prisma.proposal.count({
        where: {
          brokerId: userId,
          isAccepted: true,
          ...dateFilter
        }
      })

      analytics.proposals = {
        total: proposalStats._count || 0,
        accepted: acceptedProposals,
        acceptanceRate: proposalStats._count > 0 
          ? Math.round((acceptedProposals / proposalStats._count) * 100) 
          : 0
      }

      // Review statistics
      const reviewStats = await prisma.review.aggregate({
        where: { brokerId: userId },
        _avg: { stars: true },
        _count: true
      })

      analytics.reviews = {
        averageRating: Math.round((reviewStats._avg.stars || 0) * 10) / 10,
        totalReviews: reviewStats._count || 0
      }

      // Monthly performance
      const monthlyJobs = await prisma.printingRequest.groupBy({
        by: ['createdAt'],
        where: {
          proposals: {
            some: {
              brokerId: userId,
              isAccepted: true
            }
          },
          status: 'COMPLETED',
          createdAt: { gte: subMonths(lte, 12), lte }
        },
        _count: { id: true }
      })

      const monthlyPerformance = monthlyJobs.reduce((acc: Record<string, any>, job) => {
        const month = format(job.createdAt, 'yyyy-MM')
        if (!acc[month]) {
          acc[month] = { month, completedJobs: 0 }
        }
        acc[month].completedJobs += job._count.id
        return acc
      }, {})

      analytics.monthlyPerformance = Object.values(monthlyPerformance).sort((a: any, b: any) => 
        a.month.localeCompare(b.month)
      )

      // Performance comparison (if available)
      const marketplaceAverage = await prisma.review.aggregate({
        _avg: { stars: true }
      })

      analytics.comparison = {
        marketplaceAverageRating: Math.round((marketplaceAverage._avg.stars || 0) * 10) / 10
      }
    }

    res.json(analytics)

  } catch (error) {
    console.error('Analytics error:', error)
    res.status(500).json({
      error: 'Failed to load analytics data'
    })
  }
}

// Export analytics data as CSV
export const exportAnalyticsCSV = async (req: AuthRequest, res: Response) => {
  try {
    const { role, id: userId } = req.user!
    
    if (!['ADMIN', 'BROKER'].includes(role)) {
      return res.status(403).json({ error: 'Export access denied' })
    }

    const { gte, lte } = parseDateRange(req)
    const dateFilter = { createdAt: { gte, lte } }

    let csvData: any[] = []
    let filename = 'analytics-export.csv'

    if (role === 'ADMIN') {
      // Export platform-wide data
      const transactions = await prisma.transaction.findMany({
        where: { 
          ...dateFilter, 
          status: 'PAID' 
        },
        include: {
          proposal: {
            include: {
              request: {
                select: { title: true, specs: true }
              }
            }
          }
        },
        orderBy: { createdAt: 'desc' }
      })

      csvData = transactions.map(transaction => ({
        Date: format(transaction.createdAt, 'yyyy-MM-dd'),
        Amount: transaction.amount,
        Currency: transaction.currency,
        RequestTitle: transaction.proposal.request.title,
        Category: extractCategory(transaction.proposal.request.specs),
        Status: transaction.status
      }))

      filename = `platform-analytics-${format(gte, 'yyyy-MM-dd')}-to-${format(lte, 'yyyy-MM-dd')}.csv`

    } else if (role === 'BROKER') {
      // Export broker-specific data
      const brokerTransactions = await prisma.transaction.findMany({
        where: {
          ...dateFilter,
          proposal: { brokerId: userId },
          status: 'PAID'
        },
        include: {
          proposal: {
            include: {
              request: {
                select: { title: true, specs: true }
              }
            }
          }
        },
        orderBy: { createdAt: 'desc' }
      })

      csvData = brokerTransactions.map(transaction => ({
        Date: format(transaction.createdAt, 'yyyy-MM-dd'),
        Amount: transaction.amount,
        RequestTitle: transaction.proposal.request.title,
        Category: extractCategory(transaction.proposal.request.specs),
        Status: transaction.status
      }))

      filename = `broker-analytics-${userId}-${format(gte, 'yyyy-MM-dd')}-to-${format(lte, 'yyyy-MM-dd')}.csv`
    }

    // Convert to CSV format
    if (csvData.length === 0) {
      return res.status(404).json({ error: 'No data available for export' })
    }

    const headers = Object.keys(csvData[0])
    const csvContent = [
      headers.join(','),
      ...csvData.map(row => 
        headers.map(header => 
          typeof row[header] === 'string' && row[header].includes(',') 
            ? `"${row[header]}"` 
            : row[header]
        ).join(',')
      )
    ].join('\n')

    res.setHeader('Content-Type', 'text/csv')
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`)
    res.send(csvContent)

  } catch (error) {
    console.error('Export error:', error)
    res.status(500).json({
      error: 'Failed to export analytics data'
    })
  }
}

// Get real-time analytics summary
export const getAnalyticsSummary = async (req: AuthRequest, res: Response) => {
  try {
    const { role, id: userId } = req.user!
    
    if (!['ADMIN', 'BROKER'].includes(role)) {
      return res.status(403).json({ error: 'Access denied' })
    }

    const today = new Date()
    const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())

    let summary: any = {}

    if (role === 'ADMIN') {
      const todayRevenue = await prisma.transaction.aggregate({
        where: {
          createdAt: { gte: todayStart },
          status: 'PAID'
        },
        _sum: { amount: true },
        _count: true
      })

      const todayRequests = await prisma.printingRequest.count({
        where: { createdAt: { gte: todayStart } }
      })

      summary = {
        todayRevenue: todayRevenue._sum.amount || 0,
        todayTransactions: todayRevenue._count || 0,
        todayRequests,
        timestamp: new Date().toISOString()
      }

    } else if (role === 'BROKER') {
      const todayEarnings = await prisma.transaction.aggregate({
        where: {
          createdAt: { gte: todayStart },
          proposal: { brokerId: userId },
          status: 'PAID'
        },
        _sum: { amount: true },
        _count: true
      })

      const todayProposals = await prisma.proposal.count({
        where: {
          brokerId: userId,
          createdAt: { gte: todayStart }
        }
      })

      summary = {
        todayEarnings: todayEarnings._sum.amount || 0,
        todayTransactions: todayEarnings._count || 0,
        todayProposals,
        timestamp: new Date().toISOString()
      }
    }

    res.json(summary)

  } catch (error) {
    console.error('Analytics summary error:', error)
    res.status(500).json({
      error: 'Failed to load analytics summary'
    })
  }
}
