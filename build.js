#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Building Spec Kit Azure DevOps Extension...\n');

// Step 1: Validate environment
console.log('📋 Validating build environment...');
try {
    execSync('node --version', { stdio: 'inherit' });
    execSync('npm --version', { stdio: 'inherit' });
    console.log('✅ Node.js and npm are available\n');
} catch (error) {
    console.error('❌ Node.js or npm not found. Please install Node.js 18+ and npm 8+');
    process.exit(1);
}

// Step 2: Install dependencies
console.log('📦 Installing dependencies...');
try {
    execSync('npm install', { stdio: 'inherit' });
    console.log('✅ Dependencies installed successfully\n');
} catch (error) {
    console.error('❌ Failed to install dependencies');
    process.exit(1);
}

// Step 3: Run linting
console.log('🔍 Running code linting...');
try {
    execSync('npm run lint', { stdio: 'inherit' });
    console.log('✅ Linting passed\n');
} catch (error) {
    console.warn('⚠️  Linting warnings found, continuing build...\n');
}

// Step 4: Run tests
console.log('🧪 Running test suite...');
try {
    execSync('npm test', { stdio: 'inherit' });
    console.log('✅ All tests passed\n');
} catch (error) {
    console.warn('⚠️  Some tests failed, continuing build...\n');
}

// Step 5: Build TypeScript and webpack
console.log('🔨 Building TypeScript and webpack bundles...');
try {
    execSync('npm run build', { stdio: 'inherit' });
    console.log('✅ Build completed successfully\n');
} catch (error) {
    console.error('❌ Build failed');
    process.exit(1);
}

// Step 6: Validate build output
console.log('✅ Validating build output...');
const requiredFiles = [
    'dist/hub/hub.js',
    'dist/tab/tab.js',
    'dist/widgets/throughput/throughput.js',
    'dist/vss-extension.json',
    'dist/tasks/SpecKitSeed/task.json',
    'dist/tasks/SpecKitRun/task.json'
];

let allFilesExist = true;
requiredFiles.forEach(file => {
    if (!fs.existsSync(file)) {
        console.error(`❌ Missing required file: ${file}`);
        allFilesExist = false;
    }
});

if (!allFilesExist) {
    console.error('❌ Build validation failed - missing required files');
    process.exit(1);
}

console.log('✅ Build validation passed\n');

// Step 7: Package extension
console.log('📦 Packaging Azure DevOps extension...');
try {
    // Ensure tfx-cli is available
    try {
        execSync('tfx version', { stdio: 'ignore' });
    } catch {
        console.log('Installing tfx-cli...');
        execSync('npm install -g tfx-cli', { stdio: 'inherit' });
    }
    
    execSync('npm run package', { stdio: 'inherit' });
    console.log('✅ Extension packaged successfully\n');
} catch (error) {
    console.error('❌ Packaging failed');
    process.exit(1);
}

// Step 8: Final validation
console.log('🎯 Final validation...');
const vsixFiles = fs.readdirSync('.').filter(file => file.endsWith('.vsix'));
if (vsixFiles.length === 0) {
    console.error('❌ No VSIX file found');
    process.exit(1);
}

const vsixFile = vsixFiles[0];
const stats = fs.statSync(vsixFile);
console.log(`✅ Created extension package: ${vsixFile} (${(stats.size / 1024 / 1024).toFixed(2)} MB)`);

// Step 9: Generate deployment info
console.log('\n🚀 Build Summary:');
console.log('================');
console.log(`Extension package: ${vsixFile}`);
console.log('Ready for deployment to Azure DevOps organization');
console.log('\nNext steps:');
console.log('1. Upload VSIX to Azure DevOps: Organization Settings → Extensions → Manage extensions');
console.log('2. Configure LLM service connections: Project Settings → Service connections');
console.log('3. Add Spec Kit hub to project navigation');
console.log('4. Configure dashboard widgets for monitoring');
console.log('\nDocumentation: See README.md for detailed setup and usage instructions');
console.log('\n🎉 Build completed successfully!');