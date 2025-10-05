import { Server as SocketIOServer, Socket } from 'socket.io'
import { Server as HTTPServer } from 'http'
import jwt from 'jsonwebtoken'
import { prisma } from '@/lib/database'

const onlineUsers = new Map<number, string>()

interface AuthSocket extends Socket {
  userId?: number
  userEmail?: string
  userRole?: string
}

export function initSocketServer(httpServer: HTTPServer): SocketIOServer {
  const io = new SocketIOServer(httpServer, {
    cors: {
      origin: process.env.FRONTEND_URL || 'http://localhost:3000',
      methods: ['GET', 'POST'],
      credentials: true
    }
  })

  io.use(async (socket: AuthSocket, next) => {
    try {
      const token = socket.handshake.auth.token
      if (!token) return next(new Error('Auth required'))
      
      const decoded = jwt.verify(token, process.env.JWT_SECRET!) as any
      socket.userId = parseInt(decoded.userId)
      next()
    } catch {
      next(new Error('Auth failed'))
    }
  })

  io.on('connection', async (socket: AuthSocket) => {
    console.log(`?? User ${socket.userId} connected`)
    onlineUsers.set(socket.userId!, socket.id)
    
    socket.on('disconnect', () => {
      onlineUsers.delete(socket.userId!)
    })
  })

  return io
}

export { onlineUsers }

