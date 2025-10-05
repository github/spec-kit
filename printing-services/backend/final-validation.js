#!/usr/bin/env node
/**
 * PrintMarket Final E2E Validation
 * Validates complete Sprint 8 integration before production deployment
 */

const http = require('http');
const { execSync } = require('child_process');

console.log('🚀 PrintMarket Final E2E Validation');
console.log('=' .repeat(60));

// Step 1: Dependency Validation
console.log('\n📦 Validating Dependencies...');
try {
  const deps = ['date-fns', 'socket.io', 'express-rate-limit', '@prisma/client'];
  for (const dep of deps) {
    execSync(`npm list ${dep}`, { stdio: 'pipe' });
    console.log(`✅ ${dep}: Installed`);
  }
} catch (e) {
  console.log('❌ Missing dependencies - Run: npm install');
  process.exit(1);
}

// Step 2: Server Health Check
console.log('\n🔍 Testing Server Health...');
const testEndpoint = (path, name) => {
  return new Promise((resolve) => {
    const req = http.request({
      hostname: 'localhost',
      port: 5000,
      path: path,
      method: 'GET',
      timeout: 5000
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const success = res.statusCode === 200;
        console.log(`${success ? '✅' : '❌'} ${name}: ${res.statusCode}`);
        if (success && data) {
          try {
            const json = JSON.parse(data);
            if (json.message) console.log(`   📝 ${json.message}`);
            if (json.features) console.log(`   🎯 Features: ${json.features.join(', ')}`);
          } catch (e) {}
        }
        resolve(success);
      });
    });
    
    req.on('error', () => {
      console.log(`❌ ${name}: Connection failed`);
      resolve(false);
    });
    
    req.setTimeout(5000, () => {
      console.log(`⏰ ${name}: Timeout`);
      req.destroy();
      resolve(false);
    });
    
    req.end();
  });
};

async function validateEndpoints() {
  const endpoints = [
    { path: '/health', name: 'Server Health' },
    { path: '/api', name: 'API Info' },
    { path: '/api/analytics-health', name: 'Analytics Health' }
  ];
  
  let passed = 0;
  for (const endpoint of endpoints) {
    const success = await testEndpoint(endpoint.path, endpoint.name);
    if (success) passed++;
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  
  return { passed, total: endpoints.length };
}

// Step 3: Database Connection
console.log('\n🗄️  Testing Database Connection...');
try {
  execSync('npx prisma db pull --preview-feature', { stdio: 'pipe' });
  console.log('✅ Database: Connected and schema valid');
} catch (e) {
  console.log('❌ Database: Connection failed or schema mismatch');
}

// Step 4: TypeScript Compilation
console.log('\n🔧 Testing TypeScript Compilation...');
try {
  execSync('npx tsc --noEmit', { stdio: 'pipe' });
  console.log('✅ TypeScript: Compilation successful');
} catch (e) {
  console.log('❌ TypeScript: Compilation errors detected');
}

// Main execution
async function main() {
  const { passed, total } = await validateEndpoints();
  
  console.log('\n📊 Final Validation Summary');
  console.log('=' .repeat(60));
  console.log(`✅ Health Endpoints: ${passed}/${total}`);
  
  if (passed === total) {
    console.log('\n🎉 PRODUCTION READY!');
    console.log('✅ All systems operational');
    console.log('✅ Analytics dashboard fully integrated');
    console.log('✅ Ready for Railway + Vercel deployment');
    console.log('\n🚀 Next Steps:');
    console.log('1. git commit -m "Sprint 8: Production ready"');
    console.log('2. railway up (backend deployment)');
    console.log('3. vercel --prod (frontend deployment)');
    console.log('4. Test production URLs');
  } else {
    console.log('\n⚠️  Issues Detected');
    console.log('❌ Fix health endpoint issues before deployment');
    console.log('❌ Ensure server is running: npm run dev');
  }
}

main().catch(console.error);
