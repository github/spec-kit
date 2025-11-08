# Node.js Corporate Guidelines

**Tech Stack**: Node.js, Express, TypeScript, Backend Services, APIs

**Auto-detected from**: `package.json` with backend dependencies (express, fastify, koa)

## Scaffolding

**MUST** use corporate command:

```bash
npx @YOUR_ORG/create-node-service <service-name> --template express-ts
```

Templates: `express-ts`, `fastify-ts`, `minimal-api`, `microservice`

**DO NOT** use: `npm init`, `npx express-generator`

## Package Registry

Configure `.npmrc`:

```text
registry=https://artifactory.YOUR_DOMAIN.com/artifactory/api/npm/npm-virtual/
@YOUR_ORG:registry=https://artifactory.YOUR_DOMAIN.com/artifactory/api/npm/npm-local/
```

## Mandatory Libraries

### Express Starter

**MUST** use corporate Express starter:

```bash
npm install @YOUR_ORG/express-starter
```

```typescript
import { createApp, AcmecorpConfig } from '@YOUR_ORG/express-starter';

const config: AcmecorpConfig = {
  serviceName: 'user-service',
  port: 3000,
  auth: { jwtIssuer: 'https://auth.example.com' }
};

const app = createApp(config);
app.use('/api/users', usersRouter);
```

Includes: Security middleware, logging, metrics, error handling, CORS

### Authentication

**MUST** use corporate auth middleware:

```bash
npm install @YOUR_ORG/auth-middleware
```

```typescript
import { authMiddleware, authorize } from '@YOUR_ORG/auth-middleware';

app.use(authMiddleware());
router.get('/users', authorize(['user', 'admin']), async (req, res) => {
  const currentUser = req.user;
  // ...
});
```

### API Client

**MUST** use corporate API client:

```bash
npm install @YOUR_ORG/api-client
```

```typescript
import { createApiClient } from '@YOUR_ORG/api-client';

const orderClient = createApiClient({
  baseURL: process.env.ORDER_SERVICE_URL,
  timeout: 5000,
  retry: { attempts: 3 }
});
```

### Database (MongoDB)

**MUST** use Mongoose with corporate plugins:

```bash
npm install mongoose @YOUR_ORG/mongoose-plugins
```

```typescript
import { auditPlugin } from '@YOUR_ORG/mongoose-plugins';

const userSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true }
});

userSchema.plugin(auditPlugin);  // Adds createdAt, updatedAt
```

### Database (PostgreSQL)

**MUST** use Prisma or TypeORM:

```bash
npm install @prisma/client prisma
```

### Logging

**MUST** use corporate logger:

```bash
npm install @YOUR_ORG/logger
```

```typescript
import { logger } from '@YOUR_ORG/logger';

logger.info('User created', { userId: user.id });
logger.error('Failed to create user', { error });
```

### Validation

**MUST** use Zod or Joi:

```bash
npm install zod
```

```typescript
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(12)
});

router.post('/users', async (req, res) => {
  const validated = createUserSchema.parse(req.body);
  // ...
});
```

## Banned Libraries

**DO NOT USE**:

- `express-jwt` → use `@YOUR_ORG/auth-middleware`
- `axios` without wrapper → use `@YOUR_ORG/api-client`
- `winston` → use `@YOUR_ORG/logger`

## Architecture

**Structure**:

```text
src/
├── index.ts
├── app.ts
├── routes/
├── controllers/
├── services/
├── models/
└── middleware/
```

Layers: Routes → Controllers → Services → Models

## Security

- **Secrets**: Environment variables only, never hardcode
- **Validation**: Validate all inputs with Zod/Joi
- **SQL Injection**: Use parameterized queries (ORM handles)
- **Rate Limiting**: Use `@YOUR_ORG/rate-limiter`
- **HTTPS**: Always in production

## Coding Standards

**MUST** use TypeScript:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "strict": true,
    "esModuleInterop": true
  }
}
```

**Use**:

- Async/await (not callbacks)
- Centralized error middleware
- Naming: camelCase for functions, PascalCase for classes

## Build & Deployment

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
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

## Observability

**MUST** include:

- Health endpoint (`/health`)
- Metrics (`/metrics` - Prometheus)
- Distributed tracing
- Structured logging

Included in corporate Express starter.
