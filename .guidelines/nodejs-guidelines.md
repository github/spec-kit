# Node.js Corporate Guidelines

**Tech Stack**: Node.js, Express, TypeScript, Backend Services, APIs
**Auto-detected from**: `package.json` with backend dependencies (express, fastify, koa)
**Version**: 1.0

---

## Scaffolding

**MUST**:

- Use corporate scaffolding command (`@YOUR_ORG/create-node-service`)
- Choose appropriate template (express-ts, fastify-ts, minimal-api, microservice)

**NEVER**:

- Use `npm init` or `npx express-generator` directly

**Rationale**: Corporate scaffolding includes security, logging, monitoring, compliance from day one

---

## Package Registry

**MUST**:

- Configure `.npmrc` with corporate npm registry (Artifactory/Nexus)
- All dependencies resolved through corporate registry only

**NEVER**:

- Install packages from public npmjs.org directly

---

## Mandatory Libraries

### Framework Starter

**MUST** use: `@YOUR_ORG/express-starter` or equivalent for chosen framework
**Includes**: Security middleware, logging, metrics, error handling, CORS
**Integration**: Use `createApp()` factory function with corporate configuration

### Authentication

**MUST** use: `@YOUR_ORG/auth-middleware` package
**Requirements**:

- Apply `authMiddleware()` globally or per-route
- Use `authorize([roles])` middleware for role-based access control
- Extract authenticated user via `req.user` property

### API Client

**MUST** use: `@YOUR_ORG/api-client` package
**Requirements**:

- Use `createApiClient()` factory for external service calls
- Configure timeout, retry attempts, base URL
- Never use raw `axios`, `node-fetch`, or `got` directly

**Features**: Automatic retry, timeout handling, distributed tracing, circuit breaking

### Database (MongoDB)

**SHOULD** use: Mongoose with `@YOUR_ORG/mongoose-plugins`
**Requirements**:

- Apply `auditPlugin` to schemas for automatic timestamps
- Define schemas with TypeScript types
- Use connection pooling and retry logic

### Database (PostgreSQL/MySQL)

**SHOULD** use: Prisma or TypeORM
**Requirements**:

- Define schema in Prisma schema file or TypeORM entities
- Use migrations for schema changes
- Apply migrations on deployment

### Logging

**MUST** use: `@YOUR_ORG/logger` package
**Requirements**:

- Use structured logging with JSON format
- Include correlation ID in all log statements
- Never log PII, secrets, passwords, or tokens

**NEVER**:

- Use `console.log()` for logging

### Validation

**MUST** use: Zod or Joi for request validation
**Requirements**:

- Define validation schemas for all API requests
- Validate inputs in middleware or route handlers
- Return 400 Bad Request for validation failures

---

## Banned Libraries

**NEVER** use:

- `express-jwt` → Use `@YOUR_ORG/auth-middleware`
- Raw `axios` or `node-fetch` → Use `@YOUR_ORG/api-client`
- `winston` or `pino` directly → Use `@YOUR_ORG/logger`
- `console.log()` → Use proper logging

**Rationale**: Corporate libraries enforce security, observability, compliance

---

## Architecture

### Project Structure

**MUST** follow: Layered architecture (Routes → Controllers → Services → Models)

- **Routes**: Endpoint definitions and route registration
- **Controllers**: Request/response handling and validation
- **Services**: Business logic layer
- **Models**: Database schemas and entities

### Separation of Concerns

**MUST**:

- Keep route handlers thin (routing only)
- Keep controllers thin (validation, serialization)
- Put business logic in service layer
- Use models/repositories for database access

### Type Safety

**MUST**:

- Use TypeScript for all new code
- Define types for request/response bodies, database models
- Enable strict mode in `tsconfig.json`

### Error Handling

**MUST**:

- Use centralized error handling middleware
- Return generic error messages to clients (no internal details)
- Log full error details server-side with stack traces

---

## Security

### Input Validation

**MUST**:

- Validate all API inputs using Zod or Joi
- Return 400 Bad Request for validation failures
- Sanitize user inputs before processing

### SQL/NoSQL Injection Prevention

**MUST**:

- Use ORM/ODM (Prisma, TypeORM, Mongoose) for parameterized queries
- Never concatenate strings for database queries
- Use query parameters for all dynamic values

### Secrets Management

**MUST**:

- Store secrets in environment variables or corporate secrets manager
- Load secrets via `process.env` (never hardcode)
- Use `.env` files for local development (gitignored)

**NEVER**:

- Hardcode secrets in code or configuration files
- Commit secrets to source control

### Rate Limiting

**SHOULD**:

- Use `@YOUR_ORG/rate-limiter` middleware for public endpoints
- Configure limits based on user tier or IP address
- Return 429 Too Many Requests when limits exceeded

### HTTPS Only

**MUST**:

- Use HTTPS in production environments
- All external API calls must use HTTPS protocol

---

## Coding Standards

### Node.js & TypeScript Version

**MUST**:

- Use Node.js 18+ LTS (prefer latest LTS version)
- Use TypeScript 5+ with strict mode enabled

### Code Style

**MUST**:

- Use ESLint for linting (with corporate config)
- Use Prettier for formatting
- Follow Airbnb or Google TypeScript style guide

### Naming Conventions

**MUST** follow:

- Functions, variables: `camelCase`
- Classes, Interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: `kebab-case.ts` or `camelCase.ts` (be consistent)

### Async/Await

**MUST**:

- Use async/await for all asynchronous operations (no callbacks)
- Handle promise rejections with try/catch
- Never use callback-style APIs for new code

### Code Quality

**SHOULD**:

- Keep functions under 50 lines
- Limit cyclomatic complexity (< 10 per function)
- Write meaningful names (no abbreviations, no single letters except loops)
- Use functional programming patterns where appropriate

---

## Dependency Management

**MUST**:

- Use `package-lock.json` or `yarn.lock` for deterministic installs
- Pin versions for production dependencies
- Use `npm ci` in CI/CD (not `npm install`)

**SHOULD**:

- Keep dependencies up to date (security patches)
- Audit dependencies regularly (`npm audit`)

---

## Testing

**MUST**:

- Write unit tests with Jest or Vitest
- Write integration tests for API endpoints
- Aim for 80%+ coverage on critical paths

**SHOULD**:

- Use Supertest for HTTP endpoint testing
- Mock external dependencies (APIs, databases)
- Use test containers for integration tests with databases

---

## Build & Deployment

### Build Process

**MUST**:

- Use TypeScript compiler (`tsc`) for build
- Run tests before deployment (`npm test`)
- Run linters before deployment (`npm run lint`)

### Docker

**MUST**:

- Use multi-stage builds (build dependencies in build stage)
- Use official Node.js Alpine base images (e.g., `node:18-alpine`)
- Run as non-root user in container
- Copy only necessary files (use .dockerignore)

**SHOULD**:

- Keep container images small (< 150MB for simple services)
- Use layer caching for faster builds

---

## Observability

**MUST** include:

- Health checks endpoint (`/health`) for readiness/liveness probes
- Metrics endpoint (`/metrics`) for monitoring (Prometheus format)
- Distributed tracing with correlation IDs
- Structured logging with JSON format

**Note**: Corporate Express/Fastify starter includes all observability features by default

---

## Non-Compliance

If corporate library unavailable or causes blocking issue:

1. Document violation in `.guidelines-todo.md` with justification
2. Create ticket to resolve (target: next sprint)
3. Proceed with alternative, mark with `// TODO: GUIDELINE-VIOLATION` comment for tracking
