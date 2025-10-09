{
  "name": "performance-now",
  "description": "Implements performance.now (based on process.hrtime).",
  "keywords": [],
  "version": "2.1.0",
  "author": "Braveg1rl <braveg1rl@outlook.com>",
  "license": "MIT",
  "homepage": "https://github.com/braveg1rl/performance-now",
  "bugs": "https://github.com/braveg1rl/performance-now/issues",
  "repository": {
    "type": "git",
    "url": "git://github.com/braveg1rl/performance-now.git"
  },
  "private": false,
  "dependencies": {},
  "devDependencies": {
    "bluebird": "^3.4.7",
    "call-delayed": "^1.0.0",
    "chai": "^3.5.0",
    "chai-increasing": "^1.2.0",
    "coffee-script": "~1.12.2",
    "mocha": "~3.2.0",
    "pre-commit": "^1.2.2"
  },
  "optionalDependencies": {},
  "main": "lib/performance-now.js",
  "scripts": {
    "build": "mkdir -p lib && rm -rf lib/* && node_modules/.bin/coffee --compile -m --output lib/ src/",
    "prepublish": "npm test",
    "pretest": "npm run build",
    "test": "node_modules/.bin/mocha",
    "watch": "node_modules/.bin/coffee --watch --compile --output lib/ src/"
  },
  "typings": "src/index.d.ts"
}
