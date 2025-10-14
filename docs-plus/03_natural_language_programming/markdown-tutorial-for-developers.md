# Markdown for Developers: The Complete AI-Era Tutorial

## From Code Writer to Specification Engineer

**October 2025**

---

## Introduction: Why This Tutorial Exists

You know how to code. You've written thousands of lines in Python, JavaScript, Go, or whatever your language of choice is. You might even be pretty good at it.

But in the AI era, **writing code is becoming optional**. Writing clear specifications in Markdown is becoming essential.

This tutorial teaches you how to write Markdown that:
- **AI agents understand perfectly** and can compile to code
- **Humans read naturally** without needing to "render" it
- **Teams can collaborate on** through Git workflows
- **Organizations can standardize** with constitutions and templates

**By the end of this tutorial, you'll be able to:**
- Write production-ready specifications in Markdown
- Create AGENTS.md files that guide AI agents effectively
- Build organizational constitutions that enforce standards
- Compile Markdown specs to working code in any language
- Debug when AI-generated code doesn't match your intent

**Prerequisites:**
- Basic command line knowledge
- Familiarity with Git (helpful but not required)
- Experience with at least one programming language
- An AI coding agent (Claude Code, GitHub Copilot, Gemini CLI, etc.)

Let's begin.

---

## Part 1: Markdown Fundamentals (or: What You Probably Already Know But We'll Cover Anyway)

### 1.1 The Philosophy

Markdown is designed to be:
- **Readable as plain text** (without rendering)
- **Simple to write** (minimal syntax)
- **Unambiguous when rendered** (consistent output)

**Example - This Markdown:**
```markdown
# Main Heading

This is a paragraph with **bold text** and *italic text*.

- First item
- Second item
- Third item
```

**Looks like this when rendered:**

# Main Heading

This is a paragraph with **bold text** and *italic text*.

- First item
- Second item
- Third item

**But crucially**: It's readable even as plain text. That's the magic.

### 1.2 Headers

```markdown
# H1 - Top-level header
## H2 - Section header
### H3 - Subsection header
#### H4 - Minor section
##### H5 - Rarely used
###### H6 - Almost never used
```

**Best practices for AI specs:**
- Use H1 (#) for document title only
- Use H2 (##) for major sections
- Use H3 (###) for subsections
- Don't skip levels (don't go from H2 to H4)
- Keep headers short and descriptive

**Good:**
```markdown
## User Authentication
### Login Flow
### Password Reset
```

**Bad:**
```markdown
## This is a really long header that tries to explain everything in the header itself instead of using the body text below
#### Skipped H3 and went straight to H4
```

### 1.3 Text Formatting

```markdown
**Bold text** or __also bold__
*Italic text* or _also italic_
***Bold and italic*** or ___also both___
~~Strikethrough~~
`Inline code`
```

**Rendered:**

**Bold text** or __also bold__  
*Italic text* or _also italic_  
***Bold and italic*** or ___also both___  
~~Strikethrough~~  
`Inline code`

**For AI specs, use:**
- **Bold** for emphasis on requirements ("password **must** be hashed")
- *Italic* for notes or less critical information
- `Inline code` for variable names, function names, file paths

### 1.4 Lists

**Unordered lists:**
```markdown
- First item
- Second item
  - Nested item
  - Another nested item
- Third item
```

**Ordered lists:**
```markdown
1. First step
2. Second step
   1. Sub-step
   2. Another sub-step
3. Third step
```

**For AI specs:**
- Use **unordered lists** for features, requirements, options
- Use **ordered lists** for sequential steps, algorithms, workflows

### 1.5 Code Blocks

**Inline code:**
```markdown
Use the `requests` library to make HTTP calls.
```

**Code blocks:**
````markdown
```python
def hello_world():
    print("Hello, World!")
```
````

**Rendered:**
```python
def hello_world():
    print("Hello, World!")
```

**Specify language for syntax highlighting:**
- `python`, `javascript`, `go`, `rust`, `sql`, `bash`, etc.
- Use `markdown` for nested Markdown examples (like this tutorial)

### 1.6 Links

```markdown
[Link text](https://example.com)
[Link with title](https://example.com "Hover text")

<!-- Reference-style links -->
[Link text][reference]

[reference]: https://example.com
```

**For AI specs, link to:**
- Related specs
- External documentation
- Design mockups
- Architecture diagrams

### 1.7 Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

**Rendered:**

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

**Alignment:**
```markdown
| Left | Center | Right |
|:-----|:------:|------:|
| L1   |   C1   |    R1 |
| L2   |   C2   |    R2 |
```

**For AI specs, use tables for:**
- Data models (columns: field name, type, constraints)
- API endpoints (columns: method, path, description)
- Comparison matrices
- Configuration options

### 1.8 Blockquotes

```markdown
> This is a blockquote.
> It can span multiple lines.
>
> > Nested blockquote
```

**Rendered:**

> This is a blockquote.
> It can span multiple lines.
>
> > Nested blockquote

**For AI specs, use blockquotes for:**
- Important warnings
- Quotes from requirements documents
- Context from stakeholders

### 1.9 Horizontal Rules

```markdown
---
or
***
or
___
```

**Use sparingly** to separate major sections.

---

## Part 2: Writing Markdown for AI Agents

Now we move beyond basic syntax to the art of writing Markdown that AI agents can reliably translate into correct code.

### 2.1 The Golden Rules

**Rule 1: Be Explicit**

❌ **Bad:**
```markdown
Users should be able to log in securely.
```

✅ **Good:**
```markdown
## User Authentication

Users can log in using:
- Email and password
- OAuth (Google, GitHub)

### Security Requirements
- Passwords must be hashed using bcrypt with 12 rounds
- Failed login attempts rate limited: 5 attempts per 15 minutes
- Sessions expire after 24 hours (access token) and 7 days (refresh token)
- All authentication endpoints require HTTPS
```

**Rule 2: Structure Information Hierarchically**

❌ **Bad:**
```markdown
The system needs to handle user registration, email verification, 
password reset, and login. We should use PostgreSQL for storage and 
Redis for sessions. Make sure to add rate limiting and logging.
```

✅ **Good:**
```markdown
## User Management System

### Features
- User registration
- Email verification
- Password reset
- Login/logout

### Data Storage
- **Primary Database**: PostgreSQL 15+
- **Session Storage**: Redis 7+

### Cross-Cutting Concerns
- **Rate Limiting**: 5 requests/second per user
- **Logging**: All authentication events logged with user ID and timestamp
```

**Rule 3: Separate "What" from "How"**

❌ **Bad (too much implementation detail):**
```markdown
Create a function called authenticate_user that takes email and password 
as parameters and returns a JWT token after checking the database.
```

✅ **Good (focus on behavior):**
```markdown
## Authentication

### Login Endpoint
**Behavior**: Accept email and password, return authentication token if valid

**Inputs**:
- Email address (string, validated format)
- Password (string, plain text - will be compared to hashed version)

**Outputs**:
- Success: JWT token (24-hour expiry)
- Failure: Error message ("Invalid credentials" - don't reveal if email exists)

**Side Effects**:
- Log successful login with timestamp
- Update user's last_login_at field
- If 5th failed attempt in 15 minutes, lock account for 15 minutes
```

### 2.2 Writing Specifications

A specification describes **what** the system should do, not **how** to implement it.

**Template:**
```markdown
## [Feature Name]

### Purpose
[Why this feature exists, what problem it solves]

### User Stories
- As a [user type], I want to [action], so that [benefit]
- [Additional user stories...]

### Functional Requirements
1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

### Non-Functional Requirements
- **Performance**: [Response time, throughput targets]
- **Security**: [Security constraints]
- **Scalability**: [Expected load, growth projections]
- **Reliability**: [Uptime requirements, error handling]

### Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

### Out of Scope
- [Things explicitly NOT included in this feature]
```

**Example - User Registration:**

```markdown
## User Registration

### Purpose
Allow new users to create accounts so they can access the platform's features.

### User Stories
- As a visitor, I want to create an account with my email, so that I can save my preferences
- As a new user, I want to verify my email, so that the system knows my email is valid
- As an administrator, I want users to agree to terms of service, so that we have legal protection

### Functional Requirements

1. **Registration Form**
   - Collects: email, password, first name, last name
   - Validates email format before submission
   - Validates password strength (8+ chars, uppercase, lowercase, number, symbol)
   - Requires explicit agreement to terms of service

2. **Email Verification**
   - Sends verification email immediately after registration
   - Email contains unique verification link (expires in 24 hours)
   - User can resend verification email if needed
   - Unverified users cannot access protected features

3. **Account Creation**
   - Email must be unique (case-insensitive)
   - Password hashed with bcrypt (12 rounds) before storage
   - User account created in "unverified" state
   - Verification token stored securely (hashed)

### Non-Functional Requirements

- **Performance**: Registration completes in < 2 seconds
- **Security**: 
  - All passwords hashed with bcrypt (12 rounds minimum)
  - Verification tokens single-use and time-limited
  - HTTPS required for all registration endpoints
  - CAPTCHA on registration form to prevent bots
- **Scalability**: Support 1,000 registrations per hour
- **Reliability**: 99.9% uptime for registration endpoint

### Acceptance Criteria

- [ ] User can register with valid email and password
- [ ] Registration fails with clear errors for invalid inputs
- [ ] Verification email received within 30 seconds
- [ ] Clicking verification link activates account
- [ ] Expired verification links show appropriate error
- [ ] Duplicate email registration shows user-friendly error
- [ ] All registration events logged for audit

### Out of Scope

- Social login (OAuth) - separate feature
- Phone number registration - future consideration
- Account deletion during registration - post-MVP
```

### 2.3 Writing Technical Plans

A plan describes **how** to implement the specification.

**Template:**
```markdown
## Technical Plan: [Feature Name]

### Architecture Overview
[High-level description of how the system works]

### Components
- **[Component 1]**: [Purpose and responsibility]
- **[Component 2]**: [Purpose and responsibility]

### Data Models
[Database schemas, data structures]

### API Design
[Endpoints, request/response formats]

### Technology Choices
- **[Category 1]**: [Technology] - [Rationale]
- **[Category 2]**: [Technology] - [Rationale]

### Implementation Approach
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Testing Strategy
[How to verify correctness]

### Security Considerations
[Security measures and potential vulnerabilities]

### Performance Considerations
[Optimization strategies, bottlenecks]

### Deployment Plan
[How to roll out this feature]
```

**Example - User Registration Implementation:**

```markdown
## Technical Plan: User Registration

### Architecture Overview

User registration follows a standard web application pattern:
1. Frontend form submits to REST API
2. API validates input and creates user record
3. Background job sends verification email
4. User clicks link, API verifies token and activates account

### Components

- **Registration API** (`/api/auth/register`): Handles user creation
- **Email Service**: Sends verification emails via SendGrid
- **Token Generator**: Creates secure verification tokens
- **User Model**: Represents user in database

### Data Models

**Users Table**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(LOWER(email));
```

**Verification Tokens Table**
```sql
CREATE TABLE verification_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_verification_tokens_hash ON verification_tokens(token_hash);
CREATE INDEX idx_verification_tokens_user ON verification_tokens(user_id);
```

### API Design

**POST /api/auth/register**

Request:
```json
{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "Jane",
    "last_name": "Doe",
    "terms_accepted": true
}
```

Response (Success - 201):
```json
{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "message": "Registration successful. Please check your email to verify your account."
}
```

Response (Error - 400):
```json
{
    "error": "validation_failed",
    "details": {
        "email": "Email is already registered",
        "password": "Password must contain at least one uppercase letter"
    }
}
```

**POST /api/auth/verify**

Request:
```json
{
    "token": "abc123def456..."
}
```

Response (Success - 200):
```json
{
    "message": "Email verified successfully. You can now log in."
}
```

### Technology Choices

- **Backend Framework**: FastAPI (Python 3.11+)
  - Rationale: Fast, modern, excellent async support, automatic API docs
- **Database**: PostgreSQL 15+
  - Rationale: Strong ACID guarantees, excellent UUID support, mature
- **Password Hashing**: bcrypt
  - Rationale: Industry standard, resistant to rainbow tables and brute force
- **Email Service**: SendGrid API
  - Rationale: Reliable delivery, good free tier, detailed analytics
- **Token Generation**: secrets module (Python stdlib)
  - Rationale: Cryptographically secure, no external dependencies

### Implementation Approach

1. **Database Setup**
   - Create users and verification_tokens tables
   - Add indexes for performance
   - Set up Alembic migrations

2. **User Model Implementation**
   - Define SQLAlchemy models
   - Add password hashing methods
   - Implement email normalization (lowercase)

3. **Registration Endpoint**
   - Input validation with Pydantic
   - Check for duplicate emails
   - Hash password with bcrypt
   - Create user record (unverified state)
   - Generate verification token
   - Queue email sending job
   - Return success response

4. **Email Service**
   - Create SendGrid email template
   - Implement async email sending
   - Handle send failures with retry logic
   - Log all email attempts

5. **Verification Endpoint**
   - Validate token format
   - Look up token in database
   - Check expiration and usage status
   - Mark user as verified
   - Mark token as used
   - Return success response

### Testing Strategy

**Unit Tests**
- Password hashing and validation
- Email format validation
- Token generation and verification
- Model methods (create_user, verify_email)

**Integration Tests**
- Full registration flow end-to-end
- Email sending (with mock SendGrid)
- Database constraints (unique email)
- Token expiration behavior

**Manual Testing Checklist**
- [ ] Register with valid data
- [ ] Try duplicate email (should fail)
- [ ] Verify email with valid token
- [ ] Try expired token (should fail)
- [ ] Try used token twice (second should fail)
- [ ] Check verification email format
- [ ] Test with invalid email formats
- [ ] Test with weak passwords

### Security Considerations

1. **Password Storage**
   - Use bcrypt with cost factor 12
   - Never log or expose passwords
   - Validate password strength before hashing

2. **Verification Tokens**
   - Generate 32 bytes of randomness
   - Hash tokens before storage (SHA-256)
   - Single-use only
   - 24-hour expiration
   - Delete expired tokens daily (cleanup job)

3. **Email Enumeration Prevention**
   - Return same response for existing/non-existing emails
   - Use timing-safe comparisons
   - Rate limit registration endpoint (10/hour per IP)

4. **Input Validation**
   - Validate all inputs with Pydantic
   - Sanitize email (lowercase, trim whitespace)
   - Check against email blacklist domains
   - CAPTCHA to prevent bot registrations

5. **HTTPS Requirement**
   - All registration endpoints require HTTPS
   - Set secure cookie flags
   - HSTS headers enabled

### Performance Considerations

1. **Database Optimization**
   - Index on email (case-insensitive) for fast duplicate checks
   - Index on token_hash for fast verification lookups
   - Regular VACUUM on PostgreSQL

2. **Email Sending**
   - Async/background job (don't block API response)
   - Retry failed sends (exponential backoff)
   - Queue emails in Redis for reliability

3. **Caching**
   - Cache email blacklist in Redis (update hourly)
   - No user data caching (privacy concern)

4. **Scalability**
   - Stateless API (can scale horizontally)
   - Database connection pooling
   - Rate limiting via Redis

### Deployment Plan

**Phase 1: Development**
- Implement all components
- Write comprehensive tests
- Manual testing in dev environment

**Phase 2: Staging**
- Deploy to staging environment
- Run automated test suite
- Security audit
- Load testing (simulate 100 concurrent registrations)

**Phase 3: Production**
- Feature flag: disable existing registration
- Deploy new registration system
- Enable feature flag for 5% of traffic
- Monitor error rates and performance
- Gradually increase to 100%
- Remove old registration code after 1 week

**Rollback Plan**
- Keep old registration code for 1 week
- If issues detected, flip feature flag back
- Have database migration rollback script ready
```

### 2.4 Common Mistakes and How to Fix Them

**Mistake 1: Vague Requirements**

❌ **Bad:**
```markdown
The system should be fast and secure.
```

✅ **Good:**
```markdown
### Performance Requirements
- API response time: < 200ms (p95)
- Database queries: < 50ms (p95)
- Page load time: < 2 seconds (p95)

### Security Requirements
- All passwords hashed with bcrypt (12 rounds)
- HTTPS required for all endpoints
- JWT tokens expire after 24 hours
- Rate limiting: 100 requests/minute per user
```

**Mistake 2: Implementation Details in Specs**

❌ **Bad (spec should not dictate implementation):**
```markdown
## User Search

Use Elasticsearch to index users. Create a search function that takes a 
query string and returns matching users using a fuzzy match with fuzziness=2.
```

✅ **Good (spec describes behavior):**
```markdown
## User Search

### Functionality
Users can search for other users by name, email, or username.

### Requirements
- Search is case-insensitive
- Search matches partial strings ("john" matches "John Doe")
- Search handles typos (1-2 character differences)
- Results ranked by relevance
- Maximum 50 results returned
- Search completes in < 500ms

### Example Behavior
Query: "john d"
Results: 
- John Doe (exact match)
- Jonathan Davis (partial match)
- Jon Dudley (partial match, typo tolerance)
```

**Mistake 3: Mixing Concerns**

❌ **Bad:**
```markdown
## User Profile

Users have profiles with name, email, and avatar. We need to store this 
in PostgreSQL. The API endpoint is /api/profile. Make sure to add logging.
```

✅ **Good:**
```markdown
## User Profile

### Data Model
Users have:
- First name (required, max 100 characters)
- Last name (required, max 100 characters)
- Email (required, must be valid format)
- Avatar URL (optional, must be valid URL)
- Bio (optional, max 500 characters)

### API Endpoints

**GET /api/profile/:user_id**
Returns user profile

**PUT /api/profile/:user_id**
Updates user profile (authenticated users can only update their own)

### Technical Notes
- Store in PostgreSQL users table
- Log all profile updates for audit trail
- Validate avatar URL is accessible before saving
```

**Mistake 4: No Examples**

❌ **Bad:**
```markdown
## Date Formatting

Dates should be formatted consistently.
```

✅ **Good:**
```markdown
## Date Formatting

### Standards
- **ISO 8601 format**: `YYYY-MM-DDTHH:mm:ss.sssZ`
- **UTC timezone**: All dates stored in UTC, converted to user timezone for display

### Examples
- Database: `2025-10-12T14:30:00.000Z`
- API response: `2025-10-12T14:30:00.000Z`
- UI display: `October 12, 2025 at 2:30 PM` (in user's local time)

### Implementation
- Use Python's `datetime.utcnow()` for timestamps
- Never use `datetime.now()` without timezone
- Frontend converts to local time using moment.js
```

---

## Part 3: AGENTS.md - Documentation for Machines

### 3.1 What is AGENTS.md?

AGENTS.md is to AI agents what README.md is to human developers.

**README.md**: "Here's what this project does and how humans can use it"  
**AGENTS.md**: "Here's how this project works and how AI agents should interact with it"

### 3.2 AGENTS.md Structure

```markdown
# AGENTS.md

## Project Overview
[One-paragraph description of what this project does]

## Project Structure
[How code is organized]

## Setup Instructions
[Exact commands to set up development environment]

## Build and Run Commands
[How to build, test, and run the project]

## Development Workflow
[How to make changes and test them]

## Code Style and Conventions
[Coding standards to follow]

## Architecture Notes
[Important architectural decisions]

## Testing Strategy
[How to test changes]

## Deployment
[How to deploy changes]

## Common Tasks
[Frequent operations with exact commands]

## Gotchas and Known Issues
[Things that might trip up an agent]

## Permissions and Safety
[What the agent can do without asking]
```

### 3.3 Example: AGENTS.md for a Web Application

```markdown
# AGENTS.md

## Project Overview
This is a task management web application built with FastAPI (backend) and React (frontend). Users can create, organize, and track tasks across projects.

## Project Structure
```
task-app/
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── api/          # API route handlers
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/     # Business logic
│   │   └── utils/        # Helper functions
│   ├── tests/            # Backend tests
│   └── requirements.txt
├── frontend/             # React application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API client
│   │   └── utils/        # Helper functions
│   └── package.json
└── docker-compose.yml    # Local development stack
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL 15+ (via Docker)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Database Setup
```bash
# Start PostgreSQL via Docker
docker-compose up -d postgres

# Run migrations
cd backend
alembic upgrade head

# Seed test data (optional)
python scripts/seed_db.py
```

## Build and Run Commands

### Backend
```bash
cd backend
source venv/bin/activate

# Development server (auto-reload)
uvicorn app.main:app --reload --port 8000

# Run tests
pytest                           # All tests
pytest tests/api/                # Specific directory
pytest -v -s                     # Verbose with print statements
pytest --cov=app tests/          # With coverage report

# Type checking
mypy app/

# Linting
black app/ tests/                # Format code
isort app/ tests/                # Sort imports
flake8 app/ tests/               # Lint
```

### Frontend
```bash
cd frontend

# Development server
npm run dev                      # Runs on localhost:3000

# Build
npm run build                    # Production build
npm run preview                  # Preview production build

# Tests
npm test                         # Run tests
npm run test:watch              # Watch mode
npm run test:coverage           # With coverage

# Linting
npm run lint                     # ESLint
npm run format                   # Prettier
npm run type-check              # TypeScript
```

## Development Workflow

### Making Changes

1. **Create feature branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make changes**
   - Backend: Edit files in `backend/app/`
   - Frontend: Edit files in `frontend/src/`

3. **Run tests locally**
   ```bash
   # Backend
   cd backend && pytest
   
   # Frontend
   cd frontend && npm test
   ```

4. **Commit with conventional commits format**
   ```bash
   git commit -m "feat: add task filtering by status"
   git commit -m "fix: correct date formatting in task list"
   git commit -m "docs: update API documentation"
   ```

5. **Push and create PR**
   ```bash
   git push origin feat/your-feature-name
   ```

## Code Style and Conventions

### Backend (Python)
- **Formatter**: Black (line length 100)
- **Import sorting**: isort
- **Type hints**: Required for all functions
- **Docstrings**: Google style for all public functions
- **Naming**:
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`

### Frontend (TypeScript)
- **Formatter**: Prettier
- **Linter**: ESLint (Airbnb config)
- **Type safety**: Strict TypeScript mode
- **Naming**:
  - Components: `PascalCase.tsx`
  - Hooks: `useSomething.ts`
  - Utils: `camelCase.ts`
- **Component structure**: Functional components with hooks only

### Git Commits
- Follow Conventional Commits: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- Keep commits atomic and focused

## Architecture Notes

### Backend Architecture
- **Pattern**: Clean Architecture / Onion Architecture
- **Layers**: 
  - `api/` - HTTP handlers (thin, just validation and response formatting)
  - `services/` - Business logic (where the real work happens)
  - `models/` - Database models (SQLAlchemy)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic (auto-generated from model changes)
- **API Documentation**: Auto-generated OpenAPI/Swagger at `/docs`

### Frontend Architecture
- **State Management**: React Context + useReducer (no Redux)
- **Routing**: React Router v6
- **API Calls**: Axios with interceptors for auth
- **Styling**: Tailwind CSS (utility-first)
- **Forms**: React Hook Form + Zod validation

### Authentication
- **Tokens**: JWT (24-hour access token, 7-day refresh token)
- **Storage**: httpOnly cookies (not localStorage - security)
- **Flow**: Standard OAuth 2.0 authorization code flow

## Testing Strategy

### Backend Testing
- **Unit tests**: All service layer functions
- **Integration tests**: All API endpoints
- **Fixtures**: Use pytest fixtures for database setup
- **Mocking**: Mock external services (email, payment gateway)
- **Coverage target**: 80% minimum

### Frontend Testing
- **Component tests**: React Testing Library
- **Hook tests**: @testing-library/react-hooks
- **E2E tests**: Playwright (in `e2e/` directory)
- **Coverage target**: 70% minimum

### Test Data
- Use factories for test data (backend: factory_boy, frontend: faker)
- Never use production data in tests
- Clean database after each test (automatic with fixtures)

## Deployment

### Environments
- **Development**: Local with Docker Compose
- **Staging**: Heroku (auto-deploy from `main` branch)
- **Production**: AWS ECS (manual promotion from staging)

### Deployment Process
1. Merge PR to `main` branch
2. CI/CD runs all tests (GitHub Actions)
3. Auto-deploy to staging if tests pass
4. Manual QA on staging
5. Promote to production via GitHub Actions workflow

### Environment Variables
See `.env.example` for required variables. Never commit real `.env` files.

## Common Tasks

### Add a new API endpoint

1. **Create route handler** in `backend/app/api/v1/`
   ```python
   @router.post("/tasks", response_model=TaskResponse)
   async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
       # Implementation here
   ```

2. **Add service method** in `backend/app/services/`
   ```python
   def create_task(db: Session, task: TaskCreate) -> Task:
       # Business logic here
   ```

3. **Write tests** in `backend/tests/api/`
   ```python
   def test_create_task():
       # Test implementation
   ```

### Add a new database table

1. **Update model** in `backend/app/models/`
2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "add new table"
   ```
3. **Review migration** in `backend/alembic/versions/`
4. **Apply migration**:
   ```bash
   alembic upgrade head
   ```

### Add a new React component

1. **Create component** in `frontend/src/components/`
   ```typescript
   export const TaskCard: React.FC<TaskCardProps> = ({ task }) => {
       // Implementation
   };
   ```

2. **Write tests** in `frontend/src/components/__tests__/`
   ```typescript
   test('renders task card with title', () => {
       // Test implementation
   });
   ```

3. **Export** from `frontend/src/components/index.ts`

## Gotchas and Known Issues

### Backend Gotchas
- **SQLAlchemy session management**: Always use `db: Session = Depends(get_db)` dependency injection. Never create sessions manually.
- **Async vs sync**: Some SQLAlchemy operations are sync. Use `run_in_executor` for blocking calls in async endpoints.
- **Alembic migrations**: Review auto-generated migrations carefully. Alembic sometimes misses changes.
- **CORS**: Configured for localhost:3000 in development. Update for production domains.

### Frontend Gotchs
- **Re-renders**: Use `React.memo` and `useMemo` carefully. Profile before optimizing.
- **API calls**: All calls go through `frontend/src/services/api.ts` for consistent error handling.
- **Tailwind**: Use `@apply` in component CSS modules sparingly. Prefer utility classes.
- **Date handling**: Always use `date-fns` for date manipulation. Don't use native Date methods.

### Known Issues
- Task list pagination has a bug with filters applied (Issue #123)
- Email notifications sometimes delayed in development (use MailHog for testing)
- Docker Compose on M1 Macs sometimes needs `platform: linux/amd64` (known Docker issue)

## Permissions and Safety

### Allowed without asking
- Read any file in the repository
- Run linters: `black`, `isort`, `flake8`, `eslint`, `prettier`
- Run type checkers: `mypy`, `tsc`
- Run tests: `pytest`, `npm test`
- View git history: `git log`, `git diff`
- Create new files in appropriate directories

### Ask first
- Install dependencies: `pip install`, `npm install`
- Make git commits: `git commit`
- Push to remote: `git push`
- Delete files or directories
- Modify configuration files: `.env`, `docker-compose.yml`, `package.json`
- Run database migrations: `alembic upgrade`
- Modify CI/CD workflows: `.github/workflows/`
- Run end-to-end tests (they take 10+ minutes)

### Never do without explicit approval
- Deploy to production
- Modify production database
- Delete production resources
- Change security settings
- Modify authentication logic
- Expose secrets or credentials
```

### 3.4 Tips for Great AGENTS.md Files

**1. Be exhaustively specific about commands**
```markdown
❌ Bad: Install dependencies
✅ Good: pip install -r requirements.txt
```

**2. Include expected outputs**
```markdown
### Running Tests
```bash
pytest

# Expected output:
# ======================== test session starts =========================
# collected 47 items
# 
# tests/test_api.py .......                                      [ 14%]
# tests/test_models.py ..........                                [ 35%]
# tests/test_services.py ...........................             [100%]
# 
# ======================== 47 passed in 2.34s ==========================
```
```

**3. Document common error messages**
```markdown
### Common Errors

**Error: "ModuleNotFoundError: No module named 'app'"**
- Cause: Virtual environment not activated
- Solution: Run `source venv/bin/activate`

**Error: "FATAL: database does not exist"**
- Cause: PostgreSQL database not created
- Solution: Run `docker-compose up -d postgres` first
```

**4. Be explicit about file paths**
```markdown
❌ Bad: Edit the config file
✅ Good: Edit `backend/app/config.py`
```

**5. Include version numbers**
```markdown
### Prerequisites
- Python 3.11+ (tested with 3.11.4)
- Node.js 18+ (tested with 18.16.0)
- PostgreSQL 15+ (tested with 15.3)
```

---

## Part 4: constitution.md - Organizational Standards

### 4.1 What is constitution.md?

A constitution defines non-negotiable principles that apply to ALL projects in your organization. It's the "law of the land" for your engineering team.

Think of it as:
- AGENTS.md = project-specific instructions
- constitution.md = organization-wide standards

### 4.2 Constitution Structure

```markdown
# Engineering Constitution

## Technology Standards
[Approved tech stack]

## Security Requirements
[Mandatory security practices]

## Code Quality Standards
[Coding conventions and quality bars]

## Testing Requirements
[Test coverage and strategies]

## Documentation Standards
[What must be documented]

## Review Process
[Code review requirements]

## Deployment Standards
[How code gets to production]

## Monitoring and Observability
[Required logging, metrics, alerts]
```

### 4.3 Example: Full Constitution

```markdown
# Engineering Constitution v2.1

**Last Updated**: October 12, 2025  
**Applies To**: All engineering projects  
**Exceptions**: Require CTO approval

---

## Technology Standards

### Backend
- **Language**: Python 3.11+ or Go 1.21+
- **Web Framework**: FastAPI (Python) or Chi (Go)
- **Database**: PostgreSQL 15+ (primary data)
- **Cache**: Redis 7+ (sessions, short-term cache)
- **Message Queue**: RabbitMQ 3.12+ or AWS SQS
- **API Format**: REST with OpenAPI 3.0 specification

### Frontend
- **Language**: TypeScript 5+ (strict mode enabled)
- **Framework**: React 18+ with functional components only
- **Build Tool**: Vite 4+
- **Styling**: Tailwind CSS 3+
- **State Management**: React Context + useReducer (no Redux unless approved)
- **HTTP Client**: Axios with interceptors

### Infrastructure
- **Cloud Provider**: AWS (no other clouds without approval)
- **Container Runtime**: Docker
- **Orchestration**: Kubernetes (EKS) for production
- **CI/CD**: GitHub Actions
- **Infrastructure as Code**: Terraform
- **Secrets Management**: AWS Secrets Manager

### Prohibited Technologies
- PHP (legacy exception: Project X)
- MongoDB (use PostgreSQL with JSONB instead)
- jQuery (use React)
- Bootstrap (use Tailwind)

---

## Security Requirements

### Authentication & Authorization
- **Password Storage**: bcrypt with cost factor 12 minimum
- **Session Management**: JWT access tokens (15 min expiry) + refresh tokens (7 day expiry)
- **Token Storage**: httpOnly cookies (never localStorage)
- **MFA**: Required for production access and admin accounts
- **OAuth**: Use authorization code flow with PKCE

### Data Protection
- **Encryption at Rest**: All databases must use encryption at rest
- **Encryption in Transit**: HTTPS/TLS 1.3 for all external communications
- **PII Handling**: 
  - Never log PII (names, emails, SSNs, etc.)
  - Encrypt PII fields in database
  - Anonymize PII in non-production environments
- **SQL Injection Prevention**: Always use parameterized queries, never string concatenation

### API Security
- **Rate Limiting**: 100 requests/minute per user, 1000/minute per IP
- **CORS**: Explicitly whitelist allowed origins (no `*`)
- **Input Validation**: Validate all inputs at API boundary
- **Output Encoding**: Sanitize all outputs to prevent XSS
- **CSRF Protection**: Required for state-changing operations

### Dependency Management
- **Vulnerability Scanning**: Snyk runs on every PR
- **Dependency Updates**: Renovate bot for automated updates
- **Critical CVEs**: Must be patched within 48 hours
- **License Compliance**: Only approved licenses (MIT, Apache 2.0, BSD)

### Security Reviews
- **Authentication/Authorization changes**: Security team review required
- **Payment processing**: PCI compliance review required
- **Third-party integrations**: Security assessment required

---

## Code Quality Standards

### Python Standards
- **Formatter**: Black (line length 100, target Python 3.11)
- **Import Sorting**: isort (profile=black)
- **Linting**: Flake8 with plugins (flake8-bugbear, flake8-comprehensions)
- **Type Checking**: mypy in strict mode
- **Type Hints**: Required for all function signatures and class attributes
- **Docstrings**: Required for all public functions, classes, and modules (Google style)

**Example:**
```python
from typing import List, Optional

def calculate_total(prices: List[float], discount: Optional[float] = None) -> float:
    """Calculate total price with optional discount.
    
    Args:
        prices: List of item prices
        discount: Discount percentage (0-100), if applicable
        
    Returns:
        Total price after discount
        
    Raises:
        ValueError: If discount is negative or > 100
    """
    if discount is not None and (discount < 0 or discount > 100):
        raise ValueError("Discount must be between 0 and 100")
    
    total = sum(prices)
    if discount:
        total *= (1 - discount / 100)
    return total
```

### TypeScript Standards
- **Config**: Strict TypeScript mode enabled
- **Linting**: ESLint with Airbnb config + TypeScript plugin
- **Formatting**: Prettier (semi: true, singleQuote: true, tabWidth: 2)
- **Naming Conventions**:
  - Components: PascalCase (e.g., `TaskCard.tsx`)
  - Hooks: camelCase starting with `use` (e.g., `useTaskFilter.ts`)
  - Utils: camelCase (e.g., `formatDate.ts`)
  - Constants: UPPER_SNAKE_CASE
- **Prohibited**: 
  - `any` type (use `unknown` if truly unknown)
  - `@ts-ignore` comments (fix the type instead)
  - Default exports (use named exports)

**Example:**
```typescript
interface Task {
    id: string;
    title: string;
    completed: boolean;
    dueDate: Date | null;
}

export const sortTasksByDueDate = (tasks: Task[]): Task[] => {
    return [...tasks].sort((a, b) => {
        if (!a.dueDate) return 1;
        if (!b.dueDate) return -1;
        return a.dueDate.getTime() - b.dueDate.getTime();
    });
};
```

### General Principles
- **Cyclomatic Complexity**: Max 10 per function
- **Function Length**: Max 50 lines (extract helpers if needed)
- **File Length**: Max 500 lines (split into modules if needed)
- **DRY**: Don't repeat yourself - extract common logic
- **YAGNI**: You aren't gonna need it - don't add speculative features
- **SOLID**: Follow SOLID principles for OOP code

---

## Testing Requirements

### Coverage Requirements
- **Backend**: 80% minimum code coverage
- **Frontend**: 70% minimum code coverage
- **Critical paths**: 100% coverage (auth, payments, data mutations)

### Test Types

**Backend (Python)**
```python
# Unit tests (fast, isolated)
def test_calculate_total():
    assert calculate_total([10.0, 20.0, 30.0]) == 60.0
    assert calculate_total([10.0, 20.0], discount=10) == 27.0

# Integration tests (database, external services)
def test_create_user_endpoint(client, db):
    response = client.post("/api/users", json={"email": "test@example.com"})
    assert response.status_code == 201
    assert db.query(User).filter_by(email="test@example.com").first() is not None
```

**Frontend (TypeScript)**
```typescript
// Component tests
test('TaskCard renders task title', () => {
    const task = { id: '1', title: 'Test Task', completed: false };
    render(<TaskCard task={task} />);
    expect(screen.getByText('Test Task')).toBeInTheDocument();
});

// Hook tests
test('useTaskFilter filters completed tasks', () => {
    const { result } = renderHook(() => useTaskFilter(tasks, 'completed'));
    expect(result.current).toHaveLength(5);
});
```

### Test Organization
- **File naming**: `test_*.py` (Python), `*.test.tsx` (TypeScript)
- **Test structure**: Arrange-Act-Assert pattern
- **Fixtures**: Use pytest fixtures (Python) or factory functions (TypeScript)
- **Mocking**: Mock external dependencies, never mock code under test

### Test Performance
- **Unit test suite**: < 30 seconds
- **Integration test suite**: < 5 minutes
- **E2E test suite**: < 15 minutes
- **Flaky tests**: Fix or remove immediately (no "usually passes")

---

## Documentation Standards

### Required Documentation

**Every Repository Must Have:**
- `README.md` - Human-readable project overview
- `AGENTS.md` - AI agent instructions
- `CHANGELOG.md` - Version history
- `CONTRIBUTING.md` - How to contribute
- `.env.example` - Environment variables template

**Every API Endpoint Must Have:**
- OpenAPI/Swagger documentation
- Request/response examples
- Error response documentation
- Authentication requirements

**Every Database Migration Must Have:**
- Description of what changed and why
- Rollback procedure
- Data migration strategy (if applicable)

### Code Documentation

**Functions/Methods:**
```python
def process_payment(
    amount: Decimal,
    payment_method: PaymentMethod,
    idempotency_key: str
) -> PaymentResult:
    """Process a payment transaction.
    
    This function charges the payment method and creates a payment record.
    It's idempotent - calling with the same idempotency_key returns the
    original result without charging again.
    
    Args:
        amount: Amount to charge (must be positive)
        payment_method: Validated payment method
        idempotency_key: Unique key for this transaction (for retry safety)
        
    Returns:
        PaymentResult with transaction ID and status
        
    Raises:
        PaymentError: If payment processing fails
        ValueError: If amount is negative or zero
        
    Example:
        >>> result = process_payment(
        ...     amount=Decimal("99.99"),
        ...     payment_method=user.default_payment_method,
        ...     idempotency_key=f"order-{order_id}"
        ... )
        >>> print(result.status)
        'succeeded'
    """
```

**Complex Logic:**
```python
# Complex algorithm - explain the approach
def find_optimal_route(start: Point, end: Point, obstacles: List[Polygon]) -> Path:
    """Find optimal path avoiding obstacles using A* algorithm.
    
    Uses A* with Euclidean distance heuristic. Obstacles are treated as
    impassable regions - the path will go around them.
    
    Time complexity: O(n log n) where n is number of waypoints
    Space complexity: O(n) for the priority queue
    """
    # Initialize priority queue with start point
    # [implementation]
```

---

## Review Process

### Pull Request Requirements

**Before Opening PR:**
- [ ] All tests passing locally
- [ ] Code formatted and linted
- [ ] No linter warnings
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

**PR Description Must Include:**
- What changed and why
- Testing instructions
- Screenshots (if UI changes)
- Breaking changes (if any)
- Related issue/ticket number

**PR Title Format:**
```
type(scope): description

Examples:
feat(auth): add password reset functionality
fix(api): correct date parsing in task endpoint
docs(readme): update setup instructions
refactor(db): optimize user query performance
```

### Review Requirements
- **Minimum 1 approval** for all PRs
- **2 approvals** for:
  - Changes to authentication/authorization
  - Database schema changes
  - Payment processing
  - Security-related changes
- **Architecture review** for:
  - New services or major features
  - Changes affecting multiple services
  - Performance-critical code
  
### Review Guidelines

**Reviewers Should Check:**
- [ ] Code follows style guide
- [ ] Tests adequately cover changes
- [ ] No obvious security vulnerabilities
- [ ] Error handling is appropriate
- [ ] Performance implications considered
- [ ] Documentation is clear and accurate

**Review Responses Should:**
- Be respectful and constructive
- Focus on code, not the person
- Explain the "why" for requested changes
- Offer alternatives when possible

---

## Deployment Standards

### Environments

**Development**
- Purpose: Local development
- Access: All engineers
- Data: Synthetic/seeded data
- Infrastructure: Docker Compose

**Staging**
- Purpose: Integration testing and QA
- Access: All engineers + QA team
- Data: Anonymized production copy (monthly refresh)
- Infrastructure: Kubernetes (smaller instance sizes)
- Auto-deploys: From `main` branch after tests pass

**Production**
- Purpose: Live customer traffic
- Access: Senior engineers + SRE team
- Data: Real customer data
- Infrastructure: Kubernetes (production-sized)
- Deploys: Manual promotion from staging

### Deployment Process

**1. Development → Staging (Automated)**
```
PR merged to main
    ↓
GitHub Actions runs
    ↓
All tests pass
    ↓
Docker image built
    ↓
Auto-deploy to staging
    ↓
Smoke tests run
    ↓
Slack notification sent
```

**2. Staging → Production (Manual)**
```
Manual trigger in GitHub Actions
    ↓
Approval from on-call engineer
    ↓
Production deploy (blue-green)
    ↓
Health checks pass
    ↓
Traffic switched to new version
    ↓
Old version kept for 1 hour (for rollback)
    ↓
Slack notification sent
```

### Deployment Safety

**Feature Flags**
- Use LaunchDarkly for feature toggles
- All new features behind flags initially
- Gradual rollout: 5% → 25% → 100%
- Kill switch available for instant disable

**Rollback Procedure**
- Automated rollback if health checks fail
- Manual rollback available via GitHub Actions
- Database migrations must be backward compatible
- Keep previous version running for 1 hour

**Deployment Windows**
- **Allowed**: Monday-Thursday, 10 AM - 4 PM
- **Restricted**: Fridays (emergency only)
- **Forbidden**: Weekends, holidays, before/after major events

---

## Monitoring and Observability

### Required Metrics

**Application Metrics**
- Request rate (requests/second)
- Error rate (errors/second, percentage)
- Request duration (p50, p95, p99)
- Active users (concurrent connections)

**Infrastructure Metrics**
- CPU usage (percentage)
- Memory usage (percentage, absolute)
- Disk I/O (reads/writes per second)
- Network I/O (bytes in/out)

**Business Metrics**
- User registrations (count)
- Task completions (count)
- Payment successes/failures (count, amount)
- Feature usage (events per feature)

### Logging Standards

**Log Levels:**
- **DEBUG**: Detailed diagnostic info (disabled in production)
- **INFO**: General informational messages
- **WARNING**: Warning messages (potential issues)
- **ERROR**: Error messages (handled errors)
- **CRITICAL**: Critical errors (system instability)

**Structured Logging:**
```python
logger.info(
    "User logged in",
    extra={
        "user_id": user.id,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

**What to Log:**
- ✅ Authentication events (login, logout, failures)
- ✅ API requests (method, path, status, duration)
- ✅ Database queries (slow queries only)
- ✅ External API calls (service, duration, status)
- ✅ Errors and exceptions (with stack traces)
- ❌ Passwords or tokens (NEVER)
- ❌ Full credit card numbers (NEVER)
- ❌ User PII (names, emails - unless required for audit)

### Alerting

**Critical Alerts** (Page on-call immediately)
- Error rate > 5% for 2 minutes
- Response time p95 > 2 seconds for 5 minutes
- Database connection pool exhausted
- Any 5xx error on payment endpoint
- Disk usage > 90%

**Warning Alerts** (Slack notification)
- Error rate > 2% for 5 minutes
- Response time p95 > 1 second for 10 minutes
- Unusual traffic spike (>200% of baseline)
- Failed background job rate > 10%

**Alert Fatigue Prevention**
- Only alert on actionable items
- Include runbook link in every alert
- Auto-resolve when issue clears
- Weekly review of noisy alerts

---

## Exceptions and Waivers

Exceptions to this constitution require:
- Written justification (why existing standards don't work)
- Risk assessment (what could go wrong)
- Mitigation plan (how to reduce risk)
- Approval from CTO

**Recent Approved Exceptions:**
- Project X: Continue using PHP (legacy codebase, migration planned)
- Team Data: Use Python for data science (R and Julia also approved)
- Mobile Team: Use React Native (alternative to separate iOS/Android)

---

## Version History

**v2.1 (October 2025)**
- Added TypeScript strict mode requirement
- Updated Python to 3.11+
- Added feature flag requirement for new features

**v2.0 (June 2025)**
- Major rewrite for AI-first development
- Added AGENTS.md requirement
- Removed legacy Java standards

**v1.5 (January 2025)**
- Added Tailwind CSS as standard
- Deprecated Bootstrap
- Updated deployment windows
```

### 4.4 Tips for Effective Constitutions

**1. Be Opinionated**

Don't say "consider using X or Y." Pick one.

❌ Bad: "Use either PostgreSQL or MySQL for databases"
✅ Good: "Use PostgreSQL 15+ for all databases"

**2. Explain the "Why"**

```markdown
### Password Storage
**Standard**: bcrypt with cost factor 12

**Rationale**: Bcrypt is deliberately slow, making brute-force attacks 
impractical. Cost factor 12 provides good security (2^12 iterations) 
while keeping login time under 200ms on modern hardware.
```

**3. Make It Searchable**

Use consistent headers so people can Ctrl+F:

```markdown
## [Category] Standards
### [Technology]
**Standard**: [What to use]
**Rationale**: [Why]
**Exceptions**: [When deviation is allowed]
```

**4. Keep It Living**

```markdown
**Last Updated**: October 12, 2025  
**Next Review**: January 12, 2026  
**Owner**: Engineering Leadership Team
```

Update quarterly. Remove obsolete standards. Add new ones as tech evolves.

**5. Version It**

```markdown
**Version**: 2.1  
**Changes from 2.0**:
- Added TypeScript strict mode requirement
- Updated PostgreSQL to version 15+
```

Track versions so teams know when standards changed.

---

## Part 5: Writing Specifications That Compile to Code

Now we get to the most important skill: writing Markdown specifications that AI agents can reliably translate into correct, working code.

### 5.1 The Specification Template

```markdown
# [Feature Name] Specification

**Version**: 1.0  
**Author**: [Your name]  
**Date**: [Date]  
**Status**: [Draft | Review | Approved | Implemented]

## Overview
[2-3 sentence description of what this feature does and why it exists]

## User Stories
- As a [user type], I want to [action], so that [benefit]
- [Additional stories...]

## Functional Requirements

### [Requirement Category 1]
[Detailed description of behavior]

### [Requirement Category 2]
[Detailed description of behavior]

## Data Models

### [Model Name 1]
[Fields, types, constraints]

### [Model Name 2]
[Fields, types, constraints]

## API Specification

### [Endpoint 1]
[Method, path, request/response format, behavior]

### [Endpoint 2]
[Method, path, request/response format, behavior]

## Business Logic

### [Logic Component 1]
[Algorithms, rules, calculations]

### [Logic Component 2]
[Algorithms, rules, calculations]

## Security Requirements
[Authentication, authorization, data protection]

## Performance Requirements
[Response times, throughput, scalability]

## Error Handling
[Error scenarios and responses]

## Testing Requirements
[What must be tested and how]

## Dependencies
[External services, libraries, other features]

## Out of Scope
[Explicitly list what this feature does NOT include]
```

### 5.2 Real Example: Task Management Feature

Let me show you a complete, production-ready specification:

```markdown
# Task Assignment and Delegation Specification

**Version**: 1.0  
**Author**: Jane Developer  
**Date**: October 12, 2025  
**Status**: Approved

## Overview

Users can assign tasks to other team members and delegate tasks they've been assigned. This enables collaborative work and workload distribution across teams. Assignments are tracked with notification and audit trail.

## User Stories

- As a project manager, I want to assign tasks to team members, so that work is distributed and I can track progress
- As a team member, I want to delegate tasks I can't complete, so that work doesn't get blocked
- As a team member, I want to be notified when I'm assigned a task, so that I don't miss important work
- As an admin, I want to see assignment history, so that I can audit workload distribution

## Functional Requirements

### Task Assignment

1. **Who Can Assign**
   - Task creator can assign to anyone in the same workspace
   - Task assignee can reassign to anyone in the same workspace
   - Workspace admin can assign any task to anyone

2. **Assignment Flow**
   - User selects task
   - User searches for assignee by name or email
   - User optionally adds assignment note
   - User clicks "Assign"
   - Assignee receives notification
   - Task shows "Assigned to [Name]" in UI
   - Assignment recorded in audit log

3. **Assignment Constraints**
   - Cannot assign to users outside workspace
   - Cannot assign to deactivated users
   - Cannot assign completed tasks
   - Cannot assign archived tasks
   - Maximum 5 assignments per task (prevent assignment loops)

### Task Delegation

1. **Who Can Delegate**
   - Current assignee only
   - Cannot delegate if you're not the assignee

2. **Delegation Flow**
   - Assignee clicks "Delegate" on their assigned task
   - Selects new assignee
   - Optionally adds delegation reason
   - Confirms delegation
   - New assignee receives notification
   - Original assignee remains in history
   - Delegation recorded in audit log

3. **Delegation Rules**
   - Delegation removes current assignee
   - Only one active assignee at a time
   - Delegation count tracked (max 5)
   - Delegation creates audit entry

### Notifications

1. **Assignment Notifications**
   - **In-app**: Bell icon badge, notification panel entry
   - **Email**: Sent immediately (can disable in settings)
   - **Slack**: If integration enabled (optional)

2. **Notification Content**
   - Who assigned the task
   - Task title and description
   - Due date (if set)
   - Project name
   - Direct link to task
   - Assignment note (if provided)

3. **Notification Preferences**
   - Users can disable email notifications
   - Users can disable Slack notifications
   - Cannot disable in-app notifications
   - Settings page under "Notifications"

### Assignment History

1. **What's Tracked**
   - Original assignor and assignee
   - Timestamp of assignment
   - Assignment note (if provided)
   - All subsequent reassignments/delegations
   - Timestamp of each change
   - Who initiated each change

2. **Where It's Displayed**
   - Task detail page, "History" tab
   - Shows chronological list
   - Each entry shows: timestamp, action, from user, to user, note
   - Paginated (20 entries per page)

3. **Who Can View**
   - Anyone who can view the task
   - History cannot be deleted or modified

## Data Models

### Task (existing model, add fields)

```typescript
interface Task {
    // ... existing fields ...
    
    assigned_to: string | null;        // User ID of current assignee
    assigned_by: string | null;        // User ID who made assignment
    assigned_at: Date | null;          // Timestamp of assignment
    assignment_count: number;          // How many times assigned (prevent loops)
}
```

### TaskAssignment (new model)

```typescript
interface TaskAssignment {
    id: string;                        // UUID
    task_id: string;                   // Reference to task
    from_user_id: string | null;      // Who assigned (null for original)
    to_user_id: string;                // Who was assigned
    action: 'assigned' | 'delegated' | 'reassigned';
    note: string | null;               // Optional assignment note
    created_at: Date;                  // When assignment happened
}
```

Database schema:

```sql
-- Add to tasks table
ALTER TABLE tasks ADD COLUMN assigned_to UUID REFERENCES users(id);
ALTER TABLE tasks ADD COLUMN assigned_by UUID REFERENCES users(id);
ALTER TABLE tasks ADD COLUMN assigned_at TIMESTAMP;
ALTER TABLE tasks ADD COLUMN assignment_count INTEGER DEFAULT 0;

CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);

-- Create task_assignments table
CREATE TABLE task_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    from_user_id UUID REFERENCES users(id),
    to_user_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(20) NOT NULL CHECK (action IN ('assigned', 'delegated', 'reassigned')),
    note TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_task_assignments_task ON task_assignments(task_id);
CREATE INDEX idx_task_assignments_to_user ON task_assignments(to_user_id);
```

## API Specification

### POST /api/tasks/:task_id/assign

**Description**: Assign task to a user

**Authentication**: Required

**Authorization**: 
- Must have access to task
- Must be task creator, current assignee, or workspace admin

**Request Body**:
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "note": "You have expertise in this area"
}
```

**Validation**:
- `user_id`: Required, must be valid UUID, user must exist, user must be in workspace
- `note`: Optional, max 500 characters

**Success Response (200)**:
```json
{
    "task": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Implement search feature",
        "assigned_to": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "John Doe",
            "email": "john@example.com",
            "avatar_url": "https://..."
        },
        "assigned_by": {
            "id": "660e8400-e29b-41d4-a716-446655440000",
            "name": "Jane Smith",
            "email": "jane@example.com"
        },
        "assigned_at": "2025-10-12T14:30:00Z",
        "assignment_count": 1
    },
    "message": "Task assigned successfully"
}
```

**Error Responses**:

```json
// 400 - User not in workspace
{
    "error": "invalid_user",
    "message": "Cannot assign to user outside workspace"
}

// 400 - Too many assignments
{
    "error": "assignment_limit_exceeded",
    "message": "Task has been assigned 5 times. Cannot assign further."
}

// 403 - Not authorized
{
    "error": "forbidden",
    "message": "You don't have permission to assign this task"
}

// 404 - Task not found
{
    "error": "not_found",
    "message": "Task not found"
}
```

**Side Effects**:
- Creates task_assignments record
- Updates task assigned_to, assigned_by, assigned_at, assignment_count
- Sends notification to new assignee
- Logs event in audit log

### POST /api/tasks/:task_id/delegate

**Description**: Delegate task to another user

**Authentication**: Required

**Authorization**: 
- Must be the current assignee of the task

**Request Body**:
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "note": "Better suited for your skillset"
}
```

**Validation**: Same as /assign

**Success Response (200)**: Same format as /assign

**Error Responses**: 
- Same as /assign, plus:

```json
// 403 - Not current assignee
{
    "error": "forbidden",
    "message": "Only the current assignee can delegate this task"
}
```

**Side Effects**: Same as /assign

### GET /api/tasks/:task_id/assignments

**Description**: Get assignment history for a task

**Authentication**: Required

**Authorization**: Must have access to view the task

**Query Parameters**:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

**Success Response (200)**:
```json
{
    "assignments": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "action": "assigned",
            "from_user": null,
            "to_user": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "John Doe",
                "email": "john@example.com"
            },
            "note": null,
            "created_at": "2025-10-10T10:00:00Z"
        },
        {
            "id": "223e4567-e89b-12d3-a456-426614174000",
            "action": "delegated",
            "from_user": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "John Doe",
                "email": "john@example.com"
            },
            "to_user": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "name": "Jane Smith",
                "email": "jane@example.com"
            },
            "note": "Better suited for your skillset",
            "created_at": "2025-10-12T14:30:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 2,
        "total_pages": 1
    }
}
```

**Error Responses**:
```json
// 404 - Task not found
{
    "error": "not_found",
    "message": "Task not found"
}
```

## Business Logic

### Assignment Validation

```python
def can_assign_task(user: User, task: Task, assignee: User) -> tuple[bool, str]:
    """Check if user can assign task to assignee.
    
    Returns:
        (can_assign, error_message)
    """
    # Check task status
    if task.status == TaskStatus.COMPLETED:
        return False, "Cannot assign completed tasks"
    
    if task.status == TaskStatus.ARCHIVED:
        return False, "Cannot assign archived tasks"
    
    # Check user permission
    is_creator = task.created_by_id == user.id
    is_current_assignee = task.assigned_to == user.id
    is_admin = user.role == UserRole.ADMIN
    
    if not (is_creator or is_current_assignee or is_admin):
        return False, "You don't have permission to assign this task"
    
    # Check assignee is in workspace
    if assignee.workspace_id != task.workspace_id:
        return False, "Cannot assign to user outside workspace"
    
    # Check assignee is active
    if not assignee.is_active:
        return False, "Cannot assign to deactivated user"
    
    # Check assignment limit
    if task.assignment_count >= 5:
        return False, "Task has been assigned too many times"
    
    return True, ""
```

### Notification Logic

```python
async def send_assignment_notification(
    task: Task,
    assignee: User,
    assigner: User,
    note: Optional[str]
):
    """Send notifications for task assignment."""
    
    # In-app notification (always sent)
    await create_notification(
        user_id=assignee.id,
        type=NotificationType.TASK_ASSIGNED,
        title=f"{assigner.name} assigned you a task",
        message=f'"{task.title}"',
        link=f"/tasks/{task.id}",
        data={
            "task_id": task.id,
            "assigner_id": assigner.id,
            "note": note
        }
    )
    
    # Email notification (if enabled)
    if assignee.notification_preferences.email_task_assigned:
        await send_email(
            to=assignee.email,
            subject=f"Task assigned: {task.title}",
            template="task_assigned",
            context={
                "assignee_name": assignee.name,
                "task_title": task.title,
                "task_description": task.description,
                "task_due_date": task.due_date,
                "assigner_name": assigner.name,
                "assignment_note": note,
                "task_url": f"{BASE_URL}/tasks/{task.id}"
            }
        )
    
    # Slack notification (if integration enabled)
    if assignee.integrations.slack_enabled:
        await send_slack_message(
            user_id=assignee.slack_user_id,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{assigner.name}* assigned you a task"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{task.title}*\n{task.description[:200]}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Task"},
                            "url": f"{BASE_URL}/tasks/{task.id}"
                        }
                    ]
                }
            ]
        )
```

## Security Requirements

1. **Authorization**
   - All endpoints require authentication
   - Users can only assign tasks they have access to
   - Users can only assign to members of the same workspace
   - Admins have override permissions

2. **Input Validation**
   - Validate all user IDs exist and are in workspace
   - Sanitize assignment notes (prevent XSS)
   - Limit note length to prevent abuse
   - Validate task exists and user has access

3. **Rate Limiting**
   - 20 assignments per minute per user
   - Prevents bulk assignment attacks
   - Returns 429 Too Many Requests if exceeded

4. **Audit Logging**
   - Log all assignment actions with:
     - Task ID
     - User who performed action
     - Target assignee
     - Timestamp
     - IP address
     - User agent

## Performance Requirements

1. **Response Times**
   - Assignment endpoint: < 200ms (p95)
   - Get assignments history: < 100ms (p95)
   - Notification delivery: < 5 seconds

2. **Database Performance**
   - Index on tasks.assigned_to for filtering
   - Index on task_assignments.task_id for history queries
   - Pagination for assignment history (never load all)

3. **Notification Performance**
   - Notifications sent asynchronously (don't block API response)
   - Queue notifications in Redis for reliability
   - Batch email sends (max 1 email per minute per user)

4. **Scalability**
   - Support 1000 assignments per minute across all users
   - Assignment history queries scale with pagination
   - Notification queue can handle 10,000 pending notifications

## Error Handling

### Client Errors (4xx)

**400 Bad Request**
- Invalid user ID format
- Assignment note too long
- Invalid request body

**403 Forbidden**
- User not authorized to assign task
- Not current assignee (for delegation)
- Cannot assign to user outside workspace

**404 Not Found**
- Task doesn't exist
- Assignee user doesn't exist

**409 Conflict**
- Task already assigned to that user
- Assignment would exceed limit

**429 Too Many Requests**
- Rate limit exceeded

### Server Errors (5xx)

**500 Internal Server Error**
- Database connection failed
- Unexpected error

**503 Service Unavailable**
- Notification service unavailable
- Email service unavailable

**Error Response Format**:
```json
{
    "error": "error_code",
    "message": "Human-readable message",
    "details": {
        "field": "specific field error"
    }
}
```

## Testing Requirements

### Unit Tests

```python
# Test assignment validation
def test_can_assign_task_when_creator():
    assert can_assign_task(creator, task, assignee) == (True, "")

def test_cannot_assign_completed_task():
    task.status = TaskStatus.COMPLETED
    assert can_assign_task(creator, task, assignee) == (False, "Cannot assign completed tasks")

def test_cannot_assign_outside_workspace():
    assignee.workspace_id = "different-workspace"
    assert can_assign_task(creator, task, assignee) == (False, "Cannot assign to user outside workspace")

# Test assignment limit
def test_assignment_limit_enforced():
    task.assignment_count = 5
    can_assign, error = can_assign_task(creator, task, assignee)
    assert not can_assign
    assert "too many times" in error
```

### Integration Tests

```python
# Test full assignment flow
async def test_assign_task_endpoint(client, db):
    # Create test task
    task = create_test_task(db)
    assignee = create_test_user(db)
    
    # Assign task
    response = await client.post(
        f"/api/tasks/{task.id}/assign",
        json={"user_id": assignee.id, "note": "Test assignment"}
    )
    
    assert response.status_code == 200
    assert response.json()["task"]["assigned_to"]["id"] == assignee.id
    
    # Verify database updated
    db.refresh(task)
    assert task.assigned_to == assignee.id
    assert task.assignment_count == 1
    
    # Verify assignment record created
    assignment = db.query(TaskAssignment).filter_by(task_id=task.id).first()
    assert assignment is not None
    assert assignment.to_user_id == assignee.id
    assert assignment.note == "Test assignment"
    
    # Verify notification created
    notification = db.query(Notification).filter_by(user_id=assignee.id).first()
    assert notification is not None
    assert "assigned you a task" in notification.title
```

### Manual Testing Checklist

- [ ] Assign task as creator → Success
- [ ] Assign task as non-creator → Error
- [ ] Assign to user outside workspace → Error
- [ ] Assign completed task → Error
- [ ] Assign same task 5 times → 5th succeeds, 6th fails
- [ ] Delegate task as assignee → Success
- [ ] Delegate task as non-assignee → Error
- [ ] Verify in-app notification appears
- [ ] Verify email sent (check inbox)
- [ ] Verify Slack message sent (check Slack)
- [ ] View assignment history → Correct chronological order
- [ ] Assignment history paginated correctly
- [ ] Rate limit triggers after 20 assignments

## Dependencies

### Internal Dependencies
- User management system (for user validation)
- Notification system (for sending notifications)
- Workspace management (for workspace membership)
- Audit logging system

### External Dependencies
- Email service (SendGrid API) for email notifications
- Slack API (if integration enabled) for Slack notifications
- None for core assignment functionality (works offline)

### Database
- Requires migration to add task fields and task_assignments table
- Migration must be backward compatible (reversible)

## Out of Scope

The following are explicitly NOT included in this feature:

- **Bulk assignment**: Assigning multiple tasks at once
- **Team assignment**: Assigning to teams rather than individuals
- **Assignment templates**: Saved assignment patterns
- **Assignment rules**: Automatic assignment based on criteria
- **Workload balancing**: Automatic distribution based on capacity
- **Assignment analytics**: Reports on assignment patterns
- **Calendar integration**: Syncing assigned tasks to calendar
- **Mobile push notifications**: Only in-app, email, and Slack

These may be considered for future iterations.

---

**End of Specification**
```

### 5.3 What Makes This Spec Great

This specification demonstrates all the best practices:

✅ **Explicit and detailed** - No ambiguity about behavior  
✅ **Structured hierarchically** - Easy to navigate and understand  
✅ **Separates what from how** - Describes behavior, not implementation  
✅ **Includes data models** - Clear database schema  
✅ **Complete API specification** - Request/response formats, errors  
✅ **Business logic documented** - Algorithms and rules explained  
✅ **Security considered** - Authorization and validation covered  
✅ **Performance targets** - Measurable requirements  
✅ **Error handling specified** - All error scenarios documented  
✅ **Testing requirements** - What to test and how  
✅ **Examples throughout** - Concrete examples of behavior  
✅ **Out of scope section** - Explicit boundaries

An AI agent reading this specification would have everything needed to generate a complete, correct implementation.

---

## Part 6: Compilation: From Markdown to Code

### 6.1 The Compilation Command

With a complete specification, you can now compile it to code.

**Basic compilation:**
```bash
specify compile feature-spec.md --output src/
```

**With specific agent:**
```bash
specify compile feature-spec.md \
  --agent claude-sonnet-4.5 \
  --target python \
  --output src/
```

**With constitution:**
```bash
specify compile feature-spec.md \
  --constitution constitution.md \
  --agent gemini-cli \
  --target typescript \
  --output src/
```

### 6.2 What Happens During Compilation

1. **Spec parsing**: AI reads and understands the specification
2. **Context loading**: Constitution and AGENTS.md loaded
3. **Architecture planning**: AI determines file structure
4. **Code generation**: Implementation code written
5. **Test generation**: Unit and integration tests created
6. **Documentation generation**: Code comments and docs
7. **Validation**: AI checks implementation matches spec

### 6.3 Reviewing Generated Code

After compilation, review the output:

```bash
# Check what was generated
ls -R src/

# Review a specific file
cat src/api/assignment.py

# Run tests
pytest src/

# Check code quality
black --check src/
mypy src/
```

**What to look for:**
- Does implementation match spec?
- Are all edge cases handled?
- Is error handling comprehensive?
- Are tests thorough?
- Does code follow constitution standards?

### 6.4 Iterating on Specs

If generated code isn't correct, **fix the spec, not the code**:

1. Identify the issue in generated code
2. Determine what was ambiguous or missing in spec
3. Update the specification
4. Recompile
5. Review again

**Example:**

**Generated code (incorrect):**
```python
def assign_task(task_id, user_id):
    task = db.query(Task).filter_by(id=task_id).first()
    task.assigned_to = user_id
    db.commit()
```

**Problem**: No validation, no error handling, no authorization check

**Fix the spec (not the code):**

```markdown
## Assignment Logic

Before assigning:
1. Validate task exists → 404 if not found
2. Validate user exists → 400 if not found
3. Check authorization → 403 if not authorized
4. Verify user in workspace → 400 if not
5. Check assignment limit → 409 if exceeded

Then:
1. Update task fields
2. Create assignment record
3. Send notification
4. Commit transaction

Error handling:
- Wrap in try/except
- Rollback on any error
- Log all errors
- Return appropriate HTTP status
```

**Recompile**, and the generated code will be correct.

---

## Part 7: Advanced Techniques

### 7.1 Using Comments and Annotations

Add AI-specific hints to your Markdown:

```markdown
<!-- AI:CRITICAL -->
## Security Requirements
Password hashing MUST use bcrypt with cost factor 12 minimum.
This is non-negotiable for security compliance.
<!-- /AI:CRITICAL -->

<!-- AI:OPTIONAL -->
## Nice-to-Have Features
- Email notifications (implement if time permits)
- Slack integration (low priority)
<!-- /AI:OPTIONAL -->

<!-- AI:VERIFY -->
## Complex Business Logic
This calculation is complex. Please ask clarifying questions
before implementing to ensure correctness.
<!-- /AI:VERIFY -->
```

### 7.2 Providing Examples

Examples dramatically improve AI understanding:

```markdown
## Date Range Filtering

Users can filter tasks by date range.

### Examples

**Example 1: This week**
- Input: Date range = "this week"
- Behavior: Show tasks with due date from Monday to Sunday of current week
- Result: 5 tasks shown

**Example 2: Custom range**
- Input: Start date = Oct 1, End date = Oct 15
- Behavior: Show tasks with due date between Oct 1 and Oct 15 (inclusive)
- Result: 12 tasks shown

**Example 3: No due date**
- Input: Include tasks without due date = true
- Behavior: Also show tasks where due_date is null
- Result: 5 tasks with dates + 3 tasks without dates = 8 tasks total

**Example 4: Invalid range**
- Input: Start date = Oct 15, End date = Oct 1
- Behavior: Return error "Start date must be before end date"
- Result: 400 Bad Request
```

### 7.3 Linking Between Specs

For complex projects, split specs and link them:

```markdown
## Authentication

This feature depends on the User Management system.
See [User Management Spec](./user-management-spec.md) for:
- User data model
- User validation rules
- User permissions

## Authorization

Users require the `task:assign` permission to assign tasks.
See [Permissions Spec](./permissions-spec.md) for:
- Permission model
- Permission checking
- Role-based access control
```

### 7.4 Version Control for Specs

Treat specs like code:

```bash
# Create feature branch
git checkout -b feat/task-assignment

# Write spec
vim specs/task-assignment.md

# Commit spec for review
git add specs/task-assignment.md
git commit -m "feat: add task assignment specification"

# Push for review
git push origin feat/task-assignment

# Create PR (spec review before implementation)
```

**Review process:**
1. Team reviews specification
2. Product manager approves requirements
3. Architect approves technical approach
4. Security reviews security requirements
5. Only after approval: compile to code

---

## Part 8: Common Problems and Solutions

### Problem 1: AI Generates Wrong Code

**Symptoms**: Generated code doesn't match what you wanted

**Causes**:
- Spec was ambiguous
- Spec had contradictions
- Spec was incomplete

**Solution**: Improve spec clarity

```markdown
❌ Bad (ambiguous):
Users can filter tasks by status.

✅ Good (explicit):
Users can filter tasks by status using a dropdown menu.

Available statuses:
- "All" (default) - shows all tasks
- "Todo" - shows tasks with status = 'todo'
- "In Progress" - shows tasks with status = 'in_progress'
- "Completed" - shows tasks with status = 'completed'

Behavior:
- Selecting a status immediately filters the task list
- Filter persists across page reloads (saved in localStorage)
- URL updates with ?status=todo parameter
- Shows count of filtered tasks: "Showing 5 of 20 tasks"
```

### Problem 2: AI Skips Requirements

**Symptoms**: Some features from spec missing in code

**Causes**:
- Requirements buried in paragraphs
- No explicit feature list
- Unclear priority

**Solution**: Use clear lists and hierarchies

```markdown
❌ Bad:
The system should handle authentication and also needs to support
password reset. Don't forget about email verification too.

✅ Good:
## Core Features

1. **Authentication** [Required]
   - User login with email/password
   - Session management with JWT tokens
   - Logout functionality

2. **Password Reset** [Required]
   - Request password reset via email
   - Reset token (expires in 1 hour)
   - Set new password

3. **Email Verification** [Required]
   - Verification email on registration
   - Verification link (expires in 24 hours)
   - Resend verification email option
```

### Problem 3: Code Doesn't Follow Standards

**Symptoms**: Generated code doesn't match your coding style

**Causes**:
- No constitution.md
- Constitution not loaded during compilation
- Constitution too vague

**Solution**: Create detailed constitution

```markdown
## Python Code Standards

### Formatting
- Black with line length 100: `black --line-length 100`
- Import sorting with isort: `isort --profile black`

### Type Hints
Required for ALL functions:
```python
# Good
def calculate_total(prices: List[float], discount: float = 0.0) -> float:
    pass

# Bad - missing type hints
def calculate_total(prices, discount=0.0):
    pass
```

### Docstrings
Google style for all public functions:
```python
def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email to a recipient.
    
    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content (plain text)
        
    Returns:
        True if email sent successfully, False otherwise
        
    Raises:
        ValueError: If 'to' is not a valid email address
    """
```
```

### Problem 4: Tests Are Inadequate

**Symptoms**: Generated tests don't cover edge cases

**Causes**:
- Test requirements not in spec
- No examples of edge cases
- Acceptance criteria too vague

**Solution**: Specify test requirements explicitly

```markdown
## Testing Requirements

### Unit Tests Required

1. **Happy path**: Normal successful operation
2. **Edge cases**:
   - Empty inputs
   - Null/None values
   - Maximum length inputs
   - Boundary values
3. **Error cases**:
   - Invalid inputs
   - Authorization failures
   - Database errors
4. **State transitions**:
   - From each valid state to each other valid state
   - Invalid state transitions

### Example Test Cases

```python
# Happy path
def test_assign_task_success():
    """User with permission assigns task to valid user."""
    pass

# Edge cases
def test_assign_task_to_self():
    """User assigns task to themselves."""
    pass

def test_assign_already_assigned_task():
    """Reassigning a task updates the assignee."""
    pass

# Error cases
def test_assign_task_without_permission():
    """User without permission gets 403 error."""
    pass

def test_assign_to_nonexistent_user():
    """Assigning to invalid user ID gets 404 error."""
    pass

def test_assign_to_deactivated_user():
    """Assigning to deactivated user gets 400 error."""
    pass
```

### Coverage Requirements
- Line coverage: 80% minimum
- Branch coverage: 70% minimum
- All error paths must be tested
```

---

## Part 9: Exercises

Time to practice! Here are exercises to build your Markdown-for-AI skills.

### Exercise 1: Write AGENTS.md

For a hypothetical project, write a complete AGENTS.md file.

**Project**: A simple blog application
- Backend: Python/Django
- Frontend: React
- Database: PostgreSQL

**Your task**: Write the AGENTS.md file covering:
- Setup instructions
- Build and run commands
- Code style
- Common tasks
- Permissions

### Exercise 2: Fix Ambiguous Specs

Here's a vague spec. Rewrite it with proper structure and detail:

```markdown
## User Profile

Users have profiles with their information. They can edit
their profile and upload a profile picture. The profile
should be visible to other users.
```

**Your task**: Rewrite this into a proper specification with:
- Functional requirements
- Data model
- API endpoints
- Validation rules
- Security considerations

### Exercise 3: Write a Complete Feature Spec

Choose one of these features and write a complete specification:

**Option A**: Comment system (users can comment on blog posts)  
**Option B**: Search functionality (users can search for content)  
**Option C**: Notification system (users get notified of events)

**Your specification must include**:
- Overview
- User stories
- Functional requirements
- Data models
- API specification
- Business logic
- Security requirements
- Testing requirements
- Out of scope section

### Exercise 4: Create a Constitution

For a hypothetical 10-person startup, create an engineering constitution covering:
- Technology standards
- Security requirements
- Code quality standards
- Testing requirements
- Review process

---

## Part 10: Quick Reference

### Markdown Syntax Cheat Sheet

```markdown
# H1 Header
## H2 Header
### H3 Header

**Bold** and *italic* and `code`

- Unordered list
- Another item

1. Ordered list
2. Another item

[Link text](https://url.com)

| Table | Header |
|-------|--------|
| Cell  | Cell   |

```code block```

> Blockquote

---

Horizontal rule
```

### Spec Template Checklist

- [ ] Title and metadata (version, author, date, status)
- [ ] Overview (2-3 sentences)
- [ ] User stories (As a X, I want Y, so that Z)
- [ ] Functional requirements (detailed behavior)
- [ ] Data models (fields, types, constraints)
- [ ] API specification (endpoints, request/response)
- [ ] Business logic (algorithms, rules)
- [ ] Security requirements (auth, validation, protection)
- [ ] Performance requirements (response times, throughput)
- [ ] Error handling (all error scenarios)
- [ ] Testing requirements (what and how to test)
- [ ] Dependencies (internal and external)
- [ ] Out of scope (what's NOT included)

### Writing for AI: Do's and Don'ts

**✅ DO:**
- Be explicit and detailed
- Use hierarchical structure
- Provide concrete examples
- Separate "what" from "how"
- Include error scenarios
- Define edge cases
- Use tables for structured data
- Link to related specs

**❌ DON'T:**
- Use vague language ("should be fast")
- Bury requirements in paragraphs
- Skip error handling
- Assume AI will "figure it out"
- Mix requirements with implementation
- Forget to specify validations
- Leave acceptance criteria implicit

---

## Conclusion: Your New Workflow

You've now learned how to write Markdown that AI agents can compile into production-ready code. Here's your new development workflow:

**1. Start with the Spec (Not the Code)**
```bash
vim specs/new-feature.md
```

**2. Review the Spec (Before Any Code)**
- Get product manager approval
- Get architect review
- Get security review (if needed)

**3. Compile to Code**
```bash
specify compile specs/new-feature.md \
  --constitution constitution.md \
  --output src/
```

**4. Review Generated Code**
- Does it match the spec?
- Are tests comprehensive?
- Does it follow standards?

**5. If Issues, Fix the Spec (Not the Code)**
```bash
vim specs/new-feature.md
specify compile specs/new-feature.md --output src/
```

**6. Merge Spec and Code Together**
```bash
git add specs/new-feature.md src/
git commit -m "feat: implement new feature"
```

**Remember:**
- Specs are now your primary artifact
- Code is generated output
- When bugs found, fix the spec and recompile
- Markdown is your programming language

Welcome to the AI era of software development. You're now a **Specification Engineer**.

---

## Additional Resources

### Official Documentation
- **Markdown Guide**: [markdownguide.org](https://markdownguide.org)
- **GitHub Spec Kit**: [github.com/github/spec-kit](https://github.com/github/spec-kit)
- **AGENTS.md**: [agents.md](https://agents.md)
- **CommonMark Spec**: [commonmark.org](https://commonmark.org)

### Tools
- **Spec Kit CLI**: `pip install specify`
- **Markdown Linters**: markdownlint, spec-lint
- **Editors**: VS Code, Obsidian, Typora

### Community
- Spec-Driven Development Discord
- r/SpecDrivenDev (Reddit)
- Stack Overflow (tag: spec-driven-development)

---

**Tutorial Version 1.0 • October 2025**

*May your specifications be clear and your code be correct.*
