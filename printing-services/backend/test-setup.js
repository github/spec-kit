// Simple test script to verify setup
const fs = require('fs')
const path = require('path')

console.log('🧪 Testing Backend Setup...\n')

// Check if required files exist
const requiredFiles = [
  'package.json',
  'tsconfig.json',
  '.env.example',
  'prisma/schema.prisma',
  'src/server.ts',
  'src/lib/database.ts',
  'src/middleware/auth.ts',
  'src/utils/auth.ts',
  'src/controllers/authController.ts',
  'src/routes/auth.ts'
]

let allFilesExist = true

requiredFiles.forEach(file => {
  const filePath = path.join(__dirname, file)
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file}`)
  } else {
    console.log(`❌ ${file} - MISSING`)
    allFilesExist = false
  }
})

console.log('\n📋 Next Steps:')
console.log('1. Copy .env.example to .env and configure DATABASE_URL')
console.log('2. Run: npm install')
console.log('3. Run: npm run prisma:generate')
console.log('4. Run: npm run prisma:migrate')
console.log('5. Run: npm run prisma:seed')
console.log('6. Run: npm run dev')

console.log('\n🎯 Expected API Endpoints:')
console.log('- POST /api/auth/register')
console.log('- POST /api/auth/login') 
console.log('- GET /api/auth/verify-email/:token')
console.log('- GET /api/auth/profile')
console.log('- GET /health')

if (allFilesExist) {
  console.log('\n🎉 All required files are present!')
} else {
  console.log('\n⚠️  Some files are missing. Please check the setup.')
}
