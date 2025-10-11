import { Router } from 'express'
import { authenticateToken } from '@/middleware/auth'

const router = Router()
router.use(authenticateToken)

router.get('/conversations', (req, res) => {
  res.json({ conversations: [] })
})

export default router
