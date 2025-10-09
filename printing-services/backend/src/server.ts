import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import dotenv from 'dotenv'
import { createServer } from 'http'
import rateLimit from 'express-rate-limit'
import { connectDatabase } from '@/lib/database'
import { initSocketServer } from '@/services/websocketService'
import authRoutes from '@/routes/auth'
// import analyticsRoutes from './routes/analytics'
// import messageRoutes from './routes/messages'
// import reviewRoutes from './routes/reviews'
// import requestRoutes from './routes/requests'

// Load environment variables
dotenv.config()

const app = express()
const PORT = process.env.PORT || 5000

// Create HTTP server for Socket.IO
const httpServer = createServer(app)

// Security middleware
app.use(helmet())
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:5173'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}))

// Rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000'), // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100'), // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
})
app.use(limiter)

// Body parsing middleware
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true, limit: '10mb' }))

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'OK', 
    message: 'Printing Services API is running',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development'
  })
})

// API routes
app.get('/api', (req, res) => {
  res.json({ 
    message: 'Welcome to Printing Services Marketplace API',
    version: '1.0.0',
    status: 'operational',
    features: ['auth', 'requests', 'payments', 'files', 'messaging', 'reviews', 'analytics'],
    endpoints: {
      health: '/health',
      auth: '/api/auth',
      requests: '/api/requests',
      proposals: '/api/proposals',
      analytics: '/api/analytics',
      messages: '/api/conversations',
      reviews: '/api/reviews'
    }
  })
})

// Mount all API routes
app.use('/api/auth', authRoutes)
// app.use('/api', analyticsRoutes)
// app.use('/api', messageRoutes)
// app.use('/api', reviewRoutes)
// app.use('/api', requestRoutes)

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ 
    error: 'Route not found',
    path: req.originalUrl,
    method: req.method
  })
})

// Global error handler
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err)
  
  // Don't leak error details in production
  const isDevelopment = process.env.NODE_ENV === 'development'
  
  res.status(err.status || 500).json({
    error: isDevelopment ? err.message : 'Internal server error',
    ...(isDevelopment && { stack: err.stack })
  })
})

// Start server
async function startServer() {
  try {
    // Connect to database
    await connectDatabase()
    
    // Initialize WebSocket server
    const io = initSocketServer(httpServer)
    app.set('io', io) // Make io available to routes
    
    httpServer.listen(PORT, () => {
      console.log(`ðŸš€ Server running on port ${PORT}`)
      console.log(`ðŸ“Š Health check: http://localhost:${PORT}/health`)
      console.log(`ðŸ”§ Environment: ${process.env.NODE_ENV || 'development'}`)
      console.log(`ðŸ—„ï¸  Database: Connected`)
      console.log(`ðŸ”Œ WebSocket: initialized`)
      console.log(`ðŸ“ˆ Analytics: http://localhost:${PORT}/api/analytics-health`)
      console.log(`ðŸ’¬ Messages: WebSocket + REST ready`)
      console.log(`â­ Reviews: Rating system active`)
    })
  } catch (error) {
    console.error('âŒ Failed to start server:', error)
    process.exit(1)
  }
}

startServer()










