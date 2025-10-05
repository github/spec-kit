// Sprint 1 Validation Test Script
import { PrismaClient } from '@prisma/client'
import jwt from 'jsonwebtoken'
import bcrypt from 'bcryptjs'
import dotenv from 'dotenv'

dotenv.config()

const prisma = new PrismaClient()
const JWT_SECRET = process.env.JWT_SECRET || 'test-secret-key-for-development'

async function testSprint1() {
  console.log('🧪 Testing Sprint 1: Foundation & Authentication\n')

  try {
    // Test 1: Database Connection
    console.log('1️⃣ Testing Database Connection...')
    await prisma.$connect()
    console.log('✅ Database connected successfully\n')

    // Test 2: Prisma Client Generation
    console.log('2️⃣ Testing Prisma Client...')
    const userCount = await prisma.user.count()
    console.log(`✅ Prisma client working - Found ${userCount} users\n`)

    // Test 3: Password Hashing
    console.log('3️⃣ Testing Password Security...')
    const testPassword = 'TestPassword123'
    const hashed = await bcrypt.hash(testPassword, 12)
    const isValid = await bcrypt.compare(testPassword, hashed)
    console.log(`✅ Password hashing: ${isValid ? 'PASS' : 'FAIL'}`)
    console.log(`   Hash length: ${hashed.length} characters\n`)

    // Test 4: JWT Token Generation
    console.log('4️⃣ Testing JWT Authentication...')
    const testUser = {
      id: 'test-user-id',
      email: 'test@example.com',
      role: 'CUSTOMER' as const,
      status: 'VERIFIED'
    }
    
    const token = jwt.sign(
      {
        userId: testUser.id,
        email: testUser.email,
        role: testUser.role,
        status: testUser.status
      },
      JWT_SECRET,
      { expiresIn: '7d' }
    )
    
    const decoded = jwt.verify(token, JWT_SECRET) as any
    console.log(`✅ JWT generation and verification: PASS`)
    console.log(`   Token payload: ${JSON.stringify({ userId: decoded.userId, role: decoded.role })}\n`)

    // Test 5: Database Schema Validation
    console.log('5️⃣ Testing Database Schema...')
    
    // Check if all required tables exist by trying to query them
    const tables = [
      { name: 'users', query: () => prisma.user.findMany({ take: 1 }) },
      { name: 'printing_requests', query: () => prisma.printingRequest.findMany({ take: 1 }) },
      { name: 'proposals', query: () => prisma.proposal.findMany({ take: 1 }) },
      { name: 'samples', query: () => prisma.sample.findMany({ take: 1 }) },
      { name: 'transactions', query: () => prisma.transaction.findMany({ take: 1 }) },
      { name: 'messages', query: () => prisma.message.findMany({ take: 1 }) },
      { name: 'reviews', query: () => prisma.review.findMany({ take: 1 }) }
    ]

    for (const table of tables) {
      try {
        await table.query()
        console.log(`✅ Table '${table.name}' exists and accessible`)
      } catch (error) {
        console.log(`❌ Table '${table.name}' error: ${error}`)
      }
    }

    console.log('\n🎉 Sprint 1 Foundation Tests Complete!')
    console.log('\n📋 Ready for Sprint 2:')
    console.log('   - User registration forms (customer vs broker)')
    console.log('   - Email verification system')
    console.log('   - User profile pages')
    console.log('   - Role-based dashboards')

  } catch (error) {
    console.error('❌ Test failed:', error)
  } finally {
    await prisma.$disconnect()
  }
}

// Run the test
testSprint1().catch(console.error)
