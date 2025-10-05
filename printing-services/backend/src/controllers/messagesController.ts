import { Request, Response } from 'express'

export const getConversations = async (req: Request, res: Response) => {
  res.json({ conversations: [] })
}
