# Microservices Example: E-Commerce Platform

This example demonstrates how to use spec-kit in a microservices architecture for an e-commerce platform.

## Scenario

We're building a simple e-commerce platform with these services:
- **auth-service**: User authentication and authorization
- **user-service**: User profile management
- **order-service**: Order processing
- **notification-service**: Send order confirmation emails

## Project Structure

```
ecommerce-platform/
├── constitution.md                      # Platform-wide principles
├── .speckit.config.json                 # Spec-kit configuration
├── services/
│   ├── auth-service/
│   │   ├── specs/
│   │   │   └── 001-jwt-authentication/
│   │   │       ├── spec.md              # Service specification
│   │   │       ├── plan.md              # Technical plan
│   │   │       ├── tasks.md             # Implementation tasks
│   │   │       ├── quick-ref.md         # Quick reference
│   │   │       └── ai-doc.md            # Full AI documentation
│   │   ├── contracts/
│   │   │   └── api-spec.yaml            # OpenAPI specification
│   │   └── src/                         # Implementation
│   ├── user-service/
│   │   ├── specs/001-user-profile/
│   │   ├── contracts/
│   │   │   ├── api-spec.yaml
│   │   │   └── events/
│   │   │       └── user-events.json     # Event schemas
│   │   └── src/
│   ├── order-service/
│   │   ├── specs/001-order-management/
│   │   ├── contracts/
│   │   └── src/
│   └── notification-service/
│       ├── specs/001-email-notifications/
│       ├── contracts/
│       └── src/
├── shared/
│   └── contracts/
│       └── events/
│           └── common-events.json       # Shared event schemas
└── docs/
    ├── SERVICE-CATALOG.md               # Auto-generated service catalog
    └── ARCHITECTURE.md                  # High-level architecture
```

## Step-by-Step Workflow

### Phase 0: Platform Setup (One-Time)

#### 1. Initialize the Platform

```bash
# Create project directory
mkdir ecommerce-platform
cd ecommerce-platform

# Initialize spec-kit
specify init . --ai claude

# Create platform constitution
/speckit.constitution
```

**Sample constitution.md content:**
```markdown
# E-Commerce Platform Constitution

## Core Principles
- Each service owns its data (no shared databases)
- Asynchronous communication via events preferred
- All services must expose health checks
- API-first design (OpenAPI specs required)

## Technology Stack
- Language: Python (FastAPI)
- Database: PostgreSQL per service
- Message Bus: RabbitMQ
- API Gateway: Kong
- Authentication: JWT tokens

## Standards
- REST API versioning: /api/v1/
- Event naming: domain.entity.action
- Error format: RFC 7807 Problem Details

[See full template in templates/microservices/constitution-microservices.md]
```

#### 2. Configure Spec-Kit

Create `.speckit.config.json`:
```json
{
  "cache": {
    "enabled": true,
    "retention_days": 30
  },
  "analysis": {
    "default_mode": "incremental"
  },
  "validation": {
    "strict": true,
    "auto_validate": true
  },
  "documentation": {
    "auto_generate_quick_ref": true,
    "token_target": 200
  }
}
```

---

### Phase 1: First Service (auth-service)

#### 1. Create Service Specification

```bash
# Navigate to auth service
cd services/auth-service
mkdir -p specs/001-jwt-authentication

# Create specification
/speckit.specify
```

**Prompt to AI:** "Create a JWT-based authentication service specification"

**AI generates** `specs/001-jwt-authentication/spec.md`:
```markdown
# JWT Authentication Service Specification

## Service Overview

### Service Name
auth-service

### Service Boundary
**Responsible for:**
- User authentication (login/logout)
- JWT token generation and validation
- Token refresh mechanism

**NOT responsible for:**
- User profile management (user-service owns this)
- Password reset emails (notification-service handles this)

## User Scenarios

### P1: User Login
**Given** a registered user with email and password
**When** user submits login credentials
**Then** system returns JWT access token (15 min) and refresh token (7 days)
**And** user can make authenticated requests

### P2: Token Validation
**Given** a request with JWT token
**When** service validates token
**Then** returns user ID and roles if valid
**Or** returns 401 if expired/invalid

[... rest of spec ...]
```

#### 2. Define API Contract

Create `contracts/api-spec.yaml`:
```yaml
openapi: 3.0.0
info:
  title: Authentication Service API
  version: v1
paths:
  /api/v1/auth/login:
    post:
      summary: User login
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: object
                    properties:
                      accessToken:
                        type: string
                      refreshToken:
                        type: string
                      expiresIn:
                        type: integer
        '401':
          description: Invalid credentials

  /api/v1/auth/validate:
    post:
      summary: Validate JWT token
      # ... [similar structure]
```

#### 3. Validate Specification

```bash
/speckit.validate --spec

# Output:
# ✅ spec.md: All required sections present
# ✅ No TODO/TBD placeholders found
# ✅ Sufficient content (2,340 bytes)
# Ready to proceed to planning phase
```

#### 4. Create Technical Plan

```bash
/speckit.plan
```

**AI generates** `plan.md` with:
- FastAPI framework
- JWT library (PyJWT)
- PostgreSQL for user credentials
- Redis for token blacklist
- bcrypt for password hashing

#### 5. Generate Tasks

```bash
/speckit.tasks
```

**AI generates** `tasks.md`:
```markdown
# Implementation Tasks: JWT Authentication Service

## Phase 1: Foundation

### Task 1.1: Project Setup
- File: pyproject.toml, requirements.txt
- Dependencies: fastapi, uvicorn, pyjwt, bcrypt, sqlalchemy, redis
- Type: Configuration
- Acceptance: Can run `uvicorn app:app`

### Task 1.2: Database Models
- File: src/models/user.py
- Dependencies: None
- Type: [Test] → Implementation
- Acceptance: User model with email, password_hash, created_at

[... more tasks ...]

## Phase 4: Deployment

### Task 4.1: Dockerfile
- File: Dockerfile
- Dependencies: All implementation complete
- Type: Configuration
- Acceptance: Can build and run container

### Task 4.2: Health Check Endpoint
- File: src/api/health.py
- Dependencies: Task 4.1
- Type: Implementation
- Acceptance: GET /health returns service status
```

#### 6. Implement Service

```bash
/speckit.implement

# AI will:
# 1. Work through each task sequentially
# 2. Write tests first (when marked [Test])
# 3. Implement functionality
# 4. Validate each task completion
# 5. Create checkpoint files for resume capability
```

#### 7. Generate Documentation

```bash
/speckit.document

# Generates:
# - quick-ref.md (200 tokens summary)
# - ai-doc.md (comprehensive documentation)
```

**Sample quick-ref.md**:
```markdown
# auth-service Quick Reference

**Endpoints:**
- POST /api/v1/auth/login - User login
- POST /api/v1/auth/validate - Validate token
- POST /api/v1/auth/refresh - Refresh token

**Key Files:**
- src/api/auth.py - Authentication endpoints
- src/services/jwt_service.py - JWT operations
- src/models/user.py - User model

**Environment:**
- DATABASE_URL - PostgreSQL connection
- JWT_SECRET - Token signing key
- REDIS_URL - Token blacklist

**Integration:**
- Called by: All services for token validation
- Database: auth_db (PostgreSQL)
```

---

### Phase 2: Second Service with Dependencies (user-service)

#### 1. Create Specification with Dependencies

```bash
cd ../user-service
mkdir -p specs/001-user-profile
/speckit.specify
```

**Prompt:** "Create user profile service that depends on auth-service for authentication"

**Key section in spec.md**:
```markdown
## Service Dependencies

### Upstream Services
| Service | Purpose | Failure Mode |
|---------|---------|--------------|
| auth-service | Token validation | Return 401, don't cache |

### Downstream Services
| Service | What They Use |
|---------|---------------|
| order-service | User details for orders |
```

#### 2. Define Events Published

Create `contracts/events/user-events.json`:
```json
{
  "events": [
    {
      "eventType": "user.profile.created",
      "version": "v1",
      "description": "Published when new user profile is created",
      "schema": {
        "type": "object",
        "required": ["eventId", "eventType", "timestamp", "data"],
        "properties": {
          "eventId": {"type": "string", "format": "uuid"},
          "eventType": {"type": "string", "const": "user.profile.created"},
          "eventVersion": {"type": "string", "const": "v1"},
          "timestamp": {"type": "string", "format": "date-time"},
          "data": {
            "type": "object",
            "properties": {
              "userId": {"type": "string", "format": "uuid"},
              "email": {"type": "string", "format": "email"},
              "firstName": {"type": "string"},
              "lastName": {"type": "string"}
            }
          }
        }
      },
      "consumers": ["order-service", "notification-service"]
    },
    {
      "eventType": "user.profile.updated",
      "version": "v1",
      "description": "Published when user profile is updated",
      "consumers": ["order-service"]
    }
  ]
}
```

#### 3. Validate Contracts

```bash
/speckit.validate-contracts --service=user-service

# Output:
# ✅ API spec complete and valid
# ✅ Event schemas well-defined
# ✅ All dependencies exist (auth-service found)
# ⚠️  order-service listed as consumer but not yet implemented
```

#### 4. Proceed with Plan → Tasks → Implement

(Same workflow as auth-service)

---

### Phase 3: Event Consumer (order-service)

#### 1. Create Specification

```bash
cd ../order-service
mkdir -p specs/001-order-management
/speckit.specify
```

**Key section in spec.md**:
```markdown
## Events Consumed

### Event: user.profile.created
**From:** user-service
**Topic:** events.user.profile.created
**Action:** Create user cache entry for faster order lookups
**Idempotency:** Check if userId already in cache before adding
**Error Handling:** Retry 3 times, then DLQ
```

#### 2. Define Events Published

```markdown
## Events Published

### Event: order.created
**Topic:** events.order.created
**Trigger:** When user places an order
**Payload:**
- orderId
- userId
- items[]
- totalAmount
- orderDate
**Consumers:** notification-service, inventory-service
```

---

### Phase 4: Cross-Service Validation

#### 1. Generate Service Catalog

```bash
cd ../../  # Back to root
/speckit.service-catalog
```

**Output:** `docs/SERVICE-CATALOG.md`
```markdown
# Microservices Catalog

## Service List

### 1. auth-service
**Type:** API Service
**Endpoints:** 3 (login, validate, refresh)
**Events Published:** None
**Dependencies:** None
**Dependents:** ↓ user-service, ↓ order-service

### 2. user-service
**Type:** API Service
**Endpoints:** 4 (CRUD operations)
**Events Published:** user.profile.created, user.profile.updated
**Dependencies:** ↑ auth-service
**Dependents:** ↓ order-service

[... more services ...]

## Dependency Graph
```
         ┌─────────────┐
         │ auth-service│
         └──────┬──────┘
                │ (validate)
       ┌────────┴────────┐
       │                 │
┌──────▼──────┐  ┌──────▼─────────┐
│ user-service│  │ order-service  │
└──────┬──────┘  └────────┬───────┘
       │ (events)          │ (events)
       │                   │
       └───────────┬───────┘
                   │
       ┌───────────▼──────────┐
       │ notification-service │
       └──────────────────────┘
```
```

#### 2. Validate All Contracts

```bash
/speckit.validate-contracts

# Output:
# ✅ All API specs valid
# ✅ All event schemas defined
# ✅ No circular dependencies
# ✅ All declared consumers exist
# ⚠️  order-service not yet implemented
#
# Recommendation: Implement order-service to complete dependency chain
```

---

### Phase 5: Making Changes

#### Scenario: Adding New Endpoint to user-service

```bash
cd services/user-service

# Find existing spec
/speckit.find "user profile"

# Output:
# Found in:
# - specs/001-user-profile/spec.md (relevance: 95%)
# - specs/001-user-profile/quick-ref.md (relevance: 90%)

# Load quick-ref first (200 tokens vs 2,400)
# Decide if you need full spec

# Update spec with new requirement
# (Edit spec.md to add new user scenario)

# Re-validate
/speckit.validate --spec

# Update plan and tasks
/speckit.plan
/speckit.tasks

# Implement
/speckit.implement

# Update contract
# (Edit contracts/api-spec.yaml)

# Validate contract changes
/speckit.validate-contracts --service=user-service --breaking-changes-only

# Output:
# ⚠️  Breaking change detected:
#     Endpoint: POST /api/v1/users/{id}/avatar
#     Change: New required field 'imageFormat'
#     Consumers affected: order-service
#
#     Recommendation: Make field optional or bump version to v2
```

---

## Token Optimization in Practice

### Scenario: Working on order-service (5 services in system)

**Traditional approach (without spec-kit optimizations):**
```
1. Load all service docs: 5 × 2,400 = 12,000 tokens
2. Load all contracts: 8,000 tokens
3. Understand dependencies: Manual reading
4. Make changes: 20,000 tokens
Total: ~40,000 tokens
```

**Optimized approach with spec-kit:**
```
1. /speckit.service-catalog (read cached): 500 tokens
2. /speckit.find "order processing": 300 tokens
3. Load quick-refs for related services: 4 × 200 = 800 tokens
4. Load only order-service full spec: 2,400 tokens
5. /speckit.budget (check token usage): 100 tokens
6. Make changes: 8,000 tokens (with prune)
Total: ~12,000 tokens (70% savings)
```

**With aggressive optimization:**
```
1. Use /speckit.prune after initial exploration: -40,000 tokens saved
2. Use quick-refs exclusively: 85% reduction
3. Incremental analysis: Only analyze changed files
Result: ~5,000-7,000 tokens total (85% savings)
```

---

## Common Workflows

### Adding New Feature to Existing Service
```bash
cd services/user-service
/speckit.find "related feature"  # Check for existing related work
# Edit specs/001-user-profile/spec.md (add new scenario)
/speckit.validate --spec
/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.document --update
```

### Creating New Service
```bash
mkdir services/new-service
cd services/new-service
# Copy template
cp ../../templates/microservices/service-spec-template.md specs/001-feature/spec.md
# Fill in service details
/speckit.validate --spec
/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.validate-contracts --service=new-service
/speckit.service-catalog --regenerate
```

### Investigating Cross-Service Issue
```bash
/speckit.find "error message or symptom"
/speckit.service-catalog  # See which services involved
# Load quick-refs for involved services
/speckit.error-context "error details"  # AI-assisted debugging
```

### Before Deployment
```bash
/speckit.validate-contracts  # Ensure no breaking changes
/speckit.service-catalog --regenerate  # Update documentation
# Review dependency graph for impacts
```

---

## Best Practices Learned

1. **Start with constitution:** Define principles before first service
2. **Use quick-refs religiously:** 90% token savings
3. **Validate contracts early:** Catch breaking changes before code
4. **Keep service catalog updated:** Run after each service change
5. **Use /speckit.find liberally:** Avoid duplicate work
6. **Prune sessions regularly:** Keep token usage low
7. **Contract tests are critical:** Spec-kit generates specs, you validate them

---

## Next Steps

1. Implement remaining services (notification-service, inventory-service)
2. Add integration tests using contract tests
3. Set up CI/CD pipeline with contract validation
4. Configure service mesh (Istio/Linkerd)
5. Add observability (Prometheus, Grafana, Jaeger)

---

## Files in This Example

```
examples/microservices/
├── README.md (this file)
├── sample-constitution.md
├── sample-auth-service/
│   ├── spec.md
│   ├── plan.md
│   ├── tasks.md
│   ├── quick-ref.md
│   └── contracts/
│       └── api-spec.yaml
├── sample-user-service/
│   ├── spec.md
│   └── contracts/
│       ├── api-spec.yaml
│       └── events/
│           └── user-events.json
└── sample-service-catalog.md
```

See individual files for complete examples.
