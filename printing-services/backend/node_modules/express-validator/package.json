{
  "name": "express-validator",
  "description": "Express middleware for the validator module.",
  "author": "Christoph Tavan <dev@tavan.de>",
  "contributors": [
    "Rusty Bailey <rustylbailey@gmail.com>",
    "Gustavo Henke <guhenke@gmail.com>",
    "Federico Ciardi <fed.ciardi@gmail.com>"
  ],
  "version": "7.2.1",
  "homepage": "https://express-validator.github.io",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "git://github.com/express-validator/express-validator.git"
  },
  "main": "./lib/index.js",
  "types": "./lib/index.d.ts",
  "files": [
    "lib",
    "!src",
    "!website",
    "!docs"
  ],
  "scripts": {
    "build": "tsc",
    "clean": "git clean -Xf lib",
    "docs:build": "npm --prefix ./website run build",
    "docs:publish": "USE_SSH=true DEPLOYMENT_BRANCH=master npm --prefix ./website run publish-gh-pages",
    "docs:regenerate-api": "npm --prefix ./website run regenerate-api",
    "docs:serve": "npm --prefix ./website run serve",
    "docs:start": "npm --prefix ./website start",
    "docs:version": "npm --prefix ./website run version",
    "prepublishOnly": "tsc",
    "postpublish": "npm run docs:publish",
    "test": "jest",
    "lint": "eslint --ignore-path .gitignore 'src/**/*.ts' && prettier -c ."
  },
  "engines": {
    "node": ">= 8.0.0"
  },
  "dependencies": {
    "lodash": "^4.17.21",
    "validator": "~13.12.0"
  },
  "devDependencies": {
    "@docusaurus/core": "^3.1.0",
    "@docusaurus/plugin-client-redirects": "^3.1.0",
    "@docusaurus/preset-classic": "^3.1.0",
    "@types/jest": "^26.0.20",
    "@types/lodash": "^4.14.168",
    "@typescript-eslint/eslint-plugin": "^7.18.0",
    "@typescript-eslint/parser": "^7.18.0",
    "eslint": "^8.30.0",
    "eslint-config-prettier": "^8.5.0",
    "eslint-plugin-import": "^2.26.0",
    "eslint-plugin-prettier": "^4.2.1",
    "jest": "^29.7.0",
    "prettier": "^2.8.1",
    "ts-jest": "^29.1.5",
    "typescript": "^5.7.2"
  },
  "keywords": [
    "express",
    "validator",
    "validation",
    "validate",
    "sanitize",
    "sanitization",
    "xss"
  ]
}
