# Node.js Corporate Guidelines

**Tech Stack**: Node.js, Express, TypeScript, Backend Services, APIs

**Auto-detected from**: `package.json` with backend-focused dependencies (express, fastify, koa, etc.)

## 1. Scaffolding

**Corporate Command**:

```bash
npx @YOUR_ORG/create-node-service <service-name> --template express-ts
```

**Example**:

```bash
npx @acmecorp/create-node-service user-service --template express-ts
```

**Templates**:

- `express-ts` - Express with TypeScript
- `fastify-ts` - Fastify with TypeScript
- `minimal-api` - Minimal Express API
- `microservice` - Microservice with service discovery

**DO NOT USE**: `npm init`, `npx express-generator` (bypass corporate config)

## 2. Package Registry

**Configuration** (`.npmrc`):

```text
registry=https://artifactory.acmecorp.com/artifactory/api/npm/npm-virtual/
@acmecorp:registry=https://artifactory.acmecorp.com/artifactory/api/npm/npm-local/
//artifactory.acmecorp.com/artifactory/api/npm/:_auth=${NPM_AUTH_TOKEN}
```

## 3. Mandatory Libraries

### Corporate Express Starter

**MUST USE**:

```bash
npm install @YOUR_ORG/express-starter
```

**Includes**: Security middleware, logging, metrics, error handling, CORS

**Usage** (`src/index.ts`):

```typescript
import { createApp, AcmecorpConfig } from '@acmecorp/express-starter';
import { usersRouter } from './routes/users';

const config: AcmecorpConfig = {
  serviceName: 'user-service',
  port: process.env.PORT || 3000,
  auth: {
    jwtIssuer: 'https://auth.acmecorp.com',
    jwtAudience: 'acmecorp-services',
  },
};

const app = createApp(config);

// Your routes
app.use('/api/users', usersRouter);

app.listen(config.port);
```

### Security & Authentication

**MUST USE**:

```bash
npm install @YOUR_ORG/auth-middleware
```

**Usage**:

```typescript
import { authMiddleware, authorize } from '@acmecorp/auth-middleware';

// Apply to all routes
app.use(authMiddleware());

// Protect specific routes
router.get('/users', authorize(['user', 'admin']), async (req, res) => {
  const currentUser = req.user;  // Populated by authMiddleware
  const users = await userService.getUsers(currentUser);
  res.json(users);
});
```

### API Client

**MUST USE**:

```bash
npm install @YOUR_ORG/api-client
```

**Usage**:

```typescript
import { createApiClient } from '@acmecorp/api-client';

const orderClient = createApiClient({
  baseURL: process.env.ORDER_SERVICE_URL,
  timeout: 5000,
  retry: { attempts: 3, delay: 1000 },
  circuitBreaker: { threshold: 5, timeout: 30000 },
});

const orders = await orderClient.get('/api/orders', { params: { userId } });
```

### Database (MongoDB)

**MUST USE**: Mongoose with corporate conventions

```bash
npm install mongoose
npm install @YOUR_ORG/mongoose-plugins
```

**Schema**:

```typescript
import mongoose from 'mongoose';
import { auditPlugin } from '@acmecorp/mongoose-plugins';

const userSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  passwordHash: { type: String, required: true },
  status: { type: String, enum: ['active', 'inactive'], default: 'active' },
});

userSchema.plugin(auditPlugin);  // Adds createdAt, updatedAt, createdBy, updatedBy

export const User = mongoose.model('User', userSchema);
```

### Database (PostgreSQL)

**MUST USE**: Prisma or TypeORM

```bash
npm install @prisma/client
npm install prisma --save-dev
```

**Prisma schema**:

```prisma
model User {
  id           Int      @id @default(autoincrement())
  email        String   @unique
  passwordHash String
  status       String   @default("active")
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  @@index([email])
}
```

### Logging

**MUST USE**:

```bash
npm install @YOUR_ORG/logger
```

**Usage**:

```typescript
import { logger } from '@acmecorp/logger';

logger.info('User created', { userId: user.id, email: user.email });
logger.error('Failed to create user', { error, email });
```

**Structured JSON output** - automatic context injection (service, trace ID, user ID).

### Validation

**MUST USE**: Zod or Joi

```bash
npm install zod
```

**Usage**:

```typescript
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(12),
  firstName: z.string().max(100),
  lastName: z.string().max(100),
});

router.post('/users', async (req, res) => {
  const validated = createUserSchema.parse(req.body);  // Throws if invalid
  const user = await userService.createUser(validated);
  res.status(201).json(user);
});
```

### Testing

**MUST USE**: Jest + Supertest

```bash
npm install --save-dev jest @types/jest ts-jest supertest @types/supertest
```

**Test example**:

```typescript
import request from 'supertest';
import { app } from '../src/app';

describe('POST /api/users', () => {
  it('should create user with valid data', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({
        email: 'user@example.com',
        password: 'SecurePass123!',
        firstName: 'John',
        lastName: 'Doe',
      })
      .expect(201);

    expect(response.body.email).toBe('user@example.com');
  });
});
```

## 4. Banned Libraries

❌ **BANNED**:

- `express-jwt` (use `@YOUR_ORG/auth-middleware`)
- `axios` without corporate wrapper (use `@YOUR_ORG/api-client`)
- `winston` (use `@YOUR_ORG/logger`)

## 5. Architecture

**Structure**:

```text
src/
├── index.ts
├── app.ts
├── routes/
│   ├── users.ts
│   └── orders.ts
├── controllers/
│   └── userController.ts
├── services/
│   └── userService.ts
├── models/
│   └── user.ts
├── middleware/
│   └── errorHandler.ts
└── utils/
```

**Layers**: Routes → Controllers → Services → Models/Repositories

## 6. Security

- **Secrets**: Use environment variables, never hardcode
- **Validation**: Validate all inputs with Zod/Joi
- **SQL Injection**: Use parameterized queries (ORM handles this)
- **Rate Limiting**: Use `@YOUR_ORG/rate-limiter`
- **HTTPS**: Always use HTTPS in production

## 7. Coding Standards

- **TypeScript**: MUST use TypeScript
- **Async/Await**: Use async/await (not callbacks)
- **Error Handling**: Use try/catch, centralized error middleware
- **Naming**: camelCase for functions/variables, PascalCase for classes

**tsconfig.json**:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "./dist"
  }
}
```

## 8. Build & Deployment

**Build**:

```bash
npm run build  # tsc
npm start      # node dist/index.js
```

**Docker**:

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY package*.json ./
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

## 9. Performance

- Use connection pooling for databases
- Implement caching (Redis)
- Use streaming for large responses
- Optimize database queries (indexes, pagination)

## 10. Observability

**MUST** include:

- Health endpoint (`/health`)
- Metrics (`/metrics` - Prometheus)
- Distributed tracing (OpenTelemetry)
- Structured logging

**Included** in corporate Express starter.

## See Also

- `README.md` - Guidelines overview
- `reactjs-guidelines.md` - For frontend Node.js apps
- Internal developer portal
