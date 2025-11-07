# Universal Adoption Plan: Auto-Discovery & Onboarding

**Goal:** Transform spec-kit from a microservices-focused tool into a universal toolkit that can automatically discover, analyze, and integrate with ANY existing codebase without modifying existing projects.

**Status:** Planning Phase
**Date:** 2025-11-07

---

## Executive Summary

This enhancement will enable spec-kit to:

1. **Auto-discover** all projects in a repository (monoliths, microservices, libraries, frontends, backends, CLIs, etc.)
2. **Recognize any technology** (Python, Node.js, Java, Go, Rust, Ruby, PHP, etc.)
3. **Non-invasively integrate** by creating parallel spec-kit structure without touching existing code
4. **Reverse-engineer specs** from existing code to bootstrap documentation
5. **Adapt to existing conventions** rather than forcing spec-kit conventions

---

## Problem Statement

### Current Limitations

**Spec-kit today assumes:**
- Greenfield development (starting from scratch)
- Users will adopt spec-kit structure from day one
- Microservices architecture (with latest enhancements)
- Manual creation of specs, plans, and tasks

**Real-world challenges:**
- Most teams have **existing codebases** (not greenfield)
- Legacy monoliths, multi-module repos, mixed architectures
- Teams can't/won't restructure existing projects
- Documentation is missing or outdated
- Multiple programming languages in same repo
- Different conventions per project/team

### Target Scenarios

**Scenario 1: Legacy Monolith**
- 5-year-old Django application
- 200+ Python files, no specs
- Want to add spec-kit for new features WITHOUT restructuring

**Scenario 2: Multi-Module Repository**
- 10 different projects in one repo (polyrepo)
- Mix of: backend API (Go), frontend (React), mobile app (React Native), shared libraries
- Each project has its own structure
- Want unified spec-kit for all

**Scenario 3: Hybrid Architecture**
- Core monolith + 5 microservices
- Some services have specs, others don't
- Want to standardize on spec-kit across all

**Scenario 4: Open Source Project**
- Mature library with contributors
- Want to use spec-kit for new features
- Can't force contributors to restructure

---

## Solution Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. DISCOVERY PHASE                                         │
│  Scan repository, detect all projects & their architectures │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│  2. ANALYSIS PHASE                                          │
│  Understand each project's structure, tech stack, patterns  │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│  3. ADAPTATION PHASE                                        │
│  Create spec-kit structure (non-invasive, parallel)        │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│  4. REVERSE-ENGINEERING PHASE                               │
│  Generate initial specs from existing code                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│  5. INTEGRATION PHASE                                       │
│  Configure, cache, and enable spec-kit workflows            │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Project Discovery System

### Detection Strategies

#### 1.1 Technology Detection

Scan for project indicators by file patterns:

| Technology | Primary Indicators | Secondary Indicators |
|------------|-------------------|---------------------|
| **Node.js** | package.json | node_modules/, yarn.lock, pnpm-lock.yaml |
| **Python** | pyproject.toml, setup.py, requirements.txt | \_\_init\_\_.py, Pipfile, poetry.lock |
| **Java** | pom.xml, build.gradle | src/main/java/, .mvn/ |
| **Go** | go.mod | main.go, cmd/, pkg/ |
| **Rust** | Cargo.toml | src/main.rs, Cargo.lock |
| **Ruby** | Gemfile | Rakefile, .gemspec |
| **PHP** | composer.json | index.php, artisan (Laravel) |
| **C#/.NET** | *.csproj, *.sln | Program.cs, appsettings.json |
| **C/C++** | CMakeLists.txt, Makefile | main.c, main.cpp |
| **Frontend** | package.json + (React/Vue/Angular) | public/, src/components/ |
| **Mobile** | android/, ios/, react-native | build.gradle, Podfile |
| **Database** | migrations/, schema.sql | alembic/, flyway/, liquibase/ |

#### 1.2 Architecture Detection

Classify projects by structure:

**Microservices:**
```
Indicators:
- Multiple deployable units (services/, apps/, microservices/)
- Each with own dependencies (separate package.json, requirements.txt)
- Shared contracts/ or proto/ directory
- docker-compose.yml with multiple services
```

**Monolith:**
```
Indicators:
- Single deployable unit
- Single dependency file at root
- Layered structure (controllers/, models/, views/)
```

**Library/Package:**
```
Indicators:
- Published to package registry (pypi, npm, cargo)
- Has setup.py, package.json with "name" field
- No server/API entry point
- Exports modules/functions
```

**Frontend Application:**
```
Indicators:
- React/Vue/Angular framework detected
- public/, dist/, build/ directories
- webpack.config.js, vite.config.js, etc.
```

**Backend API:**
```
Indicators:
- API framework (FastAPI, Express, Spring, Gin)
- routes/, controllers/, handlers/ directories
- OpenAPI/Swagger specs (if lucky!)
```

**CLI Tool:**
```
Indicators:
- Executable entry point (bin/, cli.py, main.go)
- CLI framework (click, commander, cobra)
- No web server
```

**Multi-Module/Monorepo:**
```
Indicators:
- Multiple projects in subdirectories
- workspace configuration (lerna.json, pnpm-workspace.yaml)
- Each subdir has own tech stack
```

#### 1.3 Detection Algorithm

```python
class ProjectDetector:
    def discover_projects(self, root_path: str) -> List[Project]:
        """
        Scan repository and detect all projects.
        """
        projects = []

        # 1. Look for obvious project roots
        project_roots = self._find_project_roots(root_path)

        # 2. For each root, detect technology
        for root in project_roots:
            tech_stack = self._detect_technology(root)
            architecture = self._detect_architecture(root)

            project = Project(
                path=root,
                name=self._infer_name(root),
                technology=tech_stack,
                architecture=architecture,
                entry_points=self._find_entry_points(root),
                dependencies=self._find_dependencies(root)
            )

            projects.append(project)

        # 3. Detect relationships between projects
        self._detect_dependencies_between_projects(projects)

        return projects

    def _find_project_roots(self, path: str) -> List[str]:
        """
        Find all project root directories.
        Look for: package.json, setup.py, go.mod, etc.
        """
        roots = []
        for indicator in PROJECT_INDICATORS:
            matches = glob(f"{path}/**/{indicator}", recursive=True)
            roots.extend([os.path.dirname(m) for m in matches])

        # Deduplicate and handle nested projects
        return self._resolve_nested_projects(roots)
```

### Command: `/speckit.discover`

**Purpose:** Scan repository and identify all projects

**Usage:**
```bash
# Discover all projects in repository
/speckit.discover

# Discover with specific scope
/speckit.discover --path=./services

# Show detailed analysis
/speckit.discover --verbose

# Output as JSON for tooling
/speckit.discover --format=json
```

**Output:**
```markdown
# Project Discovery Report

**Scanned:** /home/user/my-repo
**Projects Found:** 7

---

## Detected Projects

### 1. API Backend (Go)
**Path:** `services/api/`
**Type:** Backend API (Microservice)
**Technology:** Go 1.21
**Framework:** Gin
**Entry Point:** `cmd/api/main.go`
**Dependencies:**
  - External: 15 packages
  - Internal: Depends on `services/auth`
**Database:** PostgreSQL (detected migrations)
**Deployable:** Yes (Dockerfile found)
**Spec-Kit Status:** ❌ Not configured

---

### 2. User Service (Python)
**Path:** `services/user-service/`
**Type:** Backend API (Microservice)
**Technology:** Python 3.11
**Framework:** FastAPI
**Entry Point:** `src/main.py`
**Dependencies:**
  - External: 23 packages (requirements.txt)
  - Internal: None
**Database:** PostgreSQL (SQLAlchemy models found)
**Deployable:** Yes (Dockerfile found)
**Spec-Kit Status:** ⚠️  Partially configured (has specs/ but incomplete)

---

### 3. Frontend Dashboard (React)
**Path:** `frontend/`
**Type:** Frontend Application
**Technology:** Node.js 18 (TypeScript)
**Framework:** React 18 + Vite
**Entry Point:** `src/main.tsx`
**Dependencies:** 87 packages
**Build Output:** `dist/`
**Deployable:** Yes (via nginx)
**Spec-Kit Status:** ❌ Not configured

---

### 4. Legacy Monolith (Django)
**Path:** `legacy/`
**Type:** Monolithic Backend
**Technology:** Python 2.7 (!)
**Framework:** Django 1.11
**Entry Point:** `manage.py`
**Warning:** ⚠️  End-of-life Python version
**Database:** PostgreSQL + Redis
**Deployable:** Yes (legacy deployment)
**Spec-Kit Status:** ❌ Not configured

---

### 5. Shared Library (Python)
**Path:** `libs/common/`
**Type:** Library/Package
**Technology:** Python 3.11
**Published:** Yes (internal PyPI)
**Used By:** `services/user-service`, `legacy/`
**Deployable:** No (library only)
**Spec-Kit Status:** ❌ Not configured

---

### 6. Mobile App (React Native)
**Path:** `mobile/`
**Type:** Mobile Application
**Technology:** React Native 0.72
**Platforms:** iOS, Android
**Entry Point:** `index.js`
**Dependencies:** 124 packages
**Deployable:** Yes (app stores)
**Spec-Kit Status:** ❌ Not configured

---

### 7. CLI Tool (Rust)
**Path:** `cli/`
**Type:** CLI Tool
**Technology:** Rust 1.73
**Entry Point:** `src/main.rs`
**Published:** Yes (crates.io)
**Deployable:** Yes (binary distribution)
**Spec-Kit Status:** ❌ Not configured

---

## Dependency Graph

```
┌─────────────────┐
│  API Backend    │ (Go)
│  services/api/  │
└────────┬────────┘
         │
         ├──→ User Service (Python)
         ├──→ Shared Library (Python)
         └──→ Legacy Monolith (calls via HTTP)
                   │
                   └──→ Shared Library (Python)

Frontend Dashboard ─→ API Backend (HTTP)
Mobile App ─────────→ API Backend (HTTP)
CLI Tool ───────────→ API Backend (HTTP)
```

---

## Recommendations

1. **Start with User Service** - Already has partial specs
2. **Modernize Legacy Monolith** - Python 2.7 is EOL
3. **Create Shared Constitution** - 7 projects need unified principles
4. **API Contract First** - API Backend is central dependency
5. **Use Token Optimization** - Large codebase will benefit

---

## Next Steps

```bash
# Onboard all discovered projects
/speckit.onboard --all

# Onboard specific project
/speckit.onboard --project=services/user-service

# Generate specs from existing code
/speckit.reverse-engineer --project=services/api

# Create project catalog
/speckit.project-catalog
```
```

---

## Phase 2: Project Analysis System

### Deep Analysis Per Project

For each discovered project, analyze:

#### 2.1 Code Structure Analysis

```python
class ProjectAnalyzer:
    def analyze(self, project: Project) -> ProjectAnalysis:
        """
        Deep analysis of project structure and patterns.
        """
        return ProjectAnalysis(
            # Architecture
            architecture_pattern=self._detect_pattern(project),
            layers=self._identify_layers(project),

            # Entry points
            entry_points=self._find_entry_points(project),
            api_endpoints=self._extract_api_endpoints(project),

            # Data layer
            models=self._find_data_models(project),
            database_schema=self._infer_schema(project),
            migrations=self._find_migrations(project),

            # Dependencies
            internal_deps=self._find_internal_dependencies(project),
            external_deps=self._parse_dependencies(project),

            # Testing
            test_coverage=self._estimate_test_coverage(project),
            test_framework=self._detect_test_framework(project),

            # Configuration
            config_files=self._find_config_files(project),
            env_vars=self._extract_env_vars(project),

            # Deployment
            containerized=self._check_docker(project),
            ci_cd=self._detect_ci_cd(project),

            # Documentation
            existing_docs=self._find_documentation(project),
            api_specs=self._find_api_specs(project),
        )
```

#### 2.2 API Endpoint Extraction

For backend projects, extract API endpoints:

**Python (FastAPI/Flask/Django):**
```python
# Detect patterns like:
@app.get("/users/{user_id}")
@app.post("/orders")
@router.get("/api/v1/products")

# Extract:
# - HTTP method
# - Path pattern
# - Path parameters
# - Query parameters (if documented)
# - Request/response types (if typed)
```

**Node.js (Express):**
```javascript
// Detect:
app.get('/users/:id', ...)
router.post('/api/orders', ...)

// Extract similar info
```

**Go (Gin/Echo/Chi):**
```go
// Detect:
r.GET("/users/:id", ...)
r.POST("/orders", ...)
```

**Java (Spring):**
```java
// Detect:
@GetMapping("/users/{id}")
@PostMapping("/orders")
```

#### 2.3 Data Model Extraction

Extract entity definitions:

**Python (SQLAlchemy/Django ORM):**
```python
class User(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    # ...

# Extract:
# - Entity name
# - Fields and types
# - Relationships
# - Constraints
```

**TypeScript (TypeORM/Prisma):**
```typescript
@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;
}
```

**Go (GORM):**
```go
type User struct {
    gorm.Model
    Email string `gorm:"unique"`
}
```

---

## Phase 3: Non-Invasive Integration

### Parallel Structure Creation

**Key Principle:** NEVER modify existing project files

**Approach:** Create spec-kit structure ALONGSIDE existing code

#### 3.1 Directory Structure

```
my-existing-repo/
├── services/                          # EXISTING - DON'T TOUCH
│   ├── api/
│   │   ├── cmd/main.go               # Existing code
│   │   ├── handlers/                 # Existing code
│   │   └── models/                   # Existing code
│   └── user-service/
│       ├── src/                      # Existing code
│       └── tests/                    # Existing code
│
├── .speckit/                          # NEW - Spec-kit metadata
│   ├── config.json                   # Global config
│   ├── cache/                        # Analysis cache
│   │   ├── projects.json             # Discovered projects
│   │   ├── api-endpoints.json        # Extracted endpoints
│   │   └── data-models.json          # Extracted models
│   ├── metadata/
│   │   ├── services-api.json         # Project metadata
│   │   └── services-user-service.json
│   └── templates/                    # Custom templates
│
├── specs/                             # NEW - Spec-kit specs
│   ├── constitution.md               # Platform-wide principles
│   ├── projects/
│   │   ├── services-api/             # Specs for Go API
│   │   │   ├── 001-existing-code/
│   │   │   │   ├── spec.md          # Reverse-engineered spec
│   │   │   │   ├── quick-ref.md     # Quick reference
│   │   │   │   └── api-doc.md       # API documentation
│   │   │   └── 002-new-feature/     # Future features
│   │   │       ├── spec.md
│   │   │       ├── plan.md
│   │   │       └── tasks.md
│   │   └── services-user-service/
│   │       └── 001-existing-code/
│   └── shared/
│       └── contracts/                # Cross-project contracts
│
├── docs/                              # NEW or UPDATE
│   ├── PROJECT-CATALOG.md            # Auto-generated catalog
│   └── ARCHITECTURE.md               # High-level architecture
│
└── .speckit.config.json               # NEW - Project config
```

#### 3.2 Configuration Strategy

**`.speckit.config.json` (root):**
```json
{
  "version": "1.0",
  "mode": "universal",
  "discovery": {
    "enabled": true,
    "scan_paths": ["services/", "frontend/", "mobile/", "cli/"],
    "exclude_paths": ["node_modules/", "venv/", ".git/"],
    "auto_detect": true
  },
  "projects": [
    {
      "id": "services-api",
      "name": "API Backend",
      "path": "services/api",
      "type": "backend-api",
      "technology": "go",
      "framework": "gin",
      "spec_location": "specs/projects/services-api",
      "managed_by_speckit": true,
      "reverse_engineered": true
    },
    {
      "id": "services-user-service",
      "name": "User Service",
      "path": "services/user-service",
      "type": "backend-api",
      "technology": "python",
      "framework": "fastapi",
      "spec_location": "specs/projects/services-user-service",
      "managed_by_speckit": true,
      "reverse_engineered": true
    }
  ],
  "constitution": {
    "path": "specs/constitution.md",
    "auto_generated": false
  },
  "cache": {
    "enabled": true,
    "location": ".speckit/cache",
    "retention_days": 30
  },
  "analysis": {
    "incremental": true,
    "watch_for_changes": false
  },
  "validation": {
    "strict": false,
    "validate_existing_code": false,
    "validate_new_specs": true
  }
}
```

#### 3.3 Metadata Files

For each project, store metadata:

**`.speckit/metadata/services-api.json`:**
```json
{
  "project_id": "services-api",
  "discovered_at": "2025-11-07T10:30:00Z",
  "last_analyzed": "2025-11-07T10:35:00Z",
  "technology": {
    "language": "go",
    "version": "1.21",
    "framework": "gin",
    "framework_version": "1.9.1"
  },
  "structure": {
    "entry_point": "cmd/api/main.go",
    "source_dir": "handlers/",
    "models_dir": "models/",
    "tests_dir": "tests/"
  },
  "api_endpoints": {
    "count": 23,
    "extracted": true,
    "location": ".speckit/cache/api-endpoints-services-api.json"
  },
  "data_models": {
    "count": 8,
    "extracted": true,
    "location": ".speckit/cache/data-models-services-api.json"
  },
  "dependencies": {
    "internal": ["services-user-service"],
    "external_count": 15
  },
  "specs": {
    "reverse_engineered": true,
    "location": "specs/projects/services-api/001-existing-code",
    "completeness": "partial",
    "needs_review": true
  }
}
```

---

## Phase 4: Reverse Engineering Specs

### Generate Specs from Existing Code

#### 4.1 Reverse Engineering Strategy

**For Backend APIs:**
```
1. Extract all API endpoints
2. Group by domain/resource
3. Infer request/response schemas
4. Document from code comments/docstrings
5. Generate OpenAPI spec
6. Create spec.md with user scenarios
```

**For Data Models:**
```
1. Parse model definitions
2. Extract field types and constraints
3. Identify relationships (foreign keys)
4. Document in spec.md
5. Generate ER diagrams (optional)
```

**For Business Logic:**
```
1. Identify key functions/methods
2. Extract from docstrings/comments
3. Infer user scenarios from code flow
4. Create spec.md with inferred scenarios
5. Mark as "needs review" (AI can't fully understand intent)
```

#### 4.2 Command: `/speckit.reverse-engineer`

**Usage:**
```bash
# Reverse engineer all projects
/speckit.reverse-engineer --all

# Reverse engineer specific project
/speckit.reverse-engineer --project=services-api

# Reverse engineer only APIs (skip business logic)
/speckit.reverse-engineer --apis-only

# Include detailed code analysis
/speckit.reverse-engineer --project=services-api --detailed
```

**Generated Output:**

**`specs/projects/services-api/001-existing-code/spec.md`:**
```markdown
# API Backend - Existing Implementation

> ⚠️  **Auto-Generated Specification**
> This spec was reverse-engineered from existing code.
> Please review and update with actual business requirements.

## Overview

**Project:** API Backend (Go)
**Location:** `services/api/`
**Entry Point:** `cmd/api/main.go`
**Reverse Engineered:** 2025-11-07

---

## Detected API Endpoints

### User Management

#### GET /api/v1/users
**Handler:** `handlers/user.go:GetUsers()`
**Purpose:** List all users (inferred from code)
**Request:**
- Query params: page (int), limit (int)
**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "string",
      "name": "string",
      "created_at": "timestamp"
    }
  ],
  "pagination": {
    "page": 1,
    "total": 100
  }
}
```

#### POST /api/v1/users
**Handler:** `handlers/user.go:CreateUser()`
**Purpose:** Create new user
**Request:**
```json
{
  "email": "string",
  "name": "string",
  "password": "string"
}
```
**Response:** User object

[... more endpoints ...]

---

## Data Models

### User Entity
**Location:** `models/user.go`
**Database Table:** `users`

**Fields:**
- `id` (UUID, primary key)
- `email` (string, unique, not null)
- `name` (string)
- `password_hash` (string, not null)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Relationships:**
- Has many: Orders (via user_id foreign key)

---

## Dependencies

**Internal:**
- `services/user-service` - Called for user profile data

**External:**
- PostgreSQL database
- Redis cache
- JWT authentication

---

## Configuration

**Environment Variables Detected:**
- `DATABASE_URL` (required)
- `REDIS_URL` (required)
- `JWT_SECRET` (required)
- `PORT` (default: 8080)

---

## Next Steps

1. Review this auto-generated spec
2. Add missing business context
3. Document user scenarios (What problems does this solve?)
4. Add acceptance criteria
5. Move to `/speckit.plan` for new features
```

**`specs/projects/services-api/001-existing-code/quick-ref.md`:**
```markdown
# API Backend Quick Reference

**Type:** Backend API (Go + Gin)
**Path:** services/api/

**Endpoints:** 23 total
- GET /api/v1/users - List users
- POST /api/v1/users - Create user
- GET /api/v1/orders - List orders
- POST /api/v1/orders - Create order
[... truncated for brevity]

**Models:** User, Order, Product, Payment (8 total)

**Dependencies:**
- Internal: user-service
- External: PostgreSQL, Redis

**Entry:** cmd/api/main.go
**Config:** DATABASE_URL, REDIS_URL, JWT_SECRET

**Full Spec:** [spec.md](./spec.md)
```

#### 4.3 Confidence Levels

Mark reverse-engineered content with confidence:

```markdown
## User Scenarios

### ✅ High Confidence: User Registration
**Source:** Clear from code flow in `handlers/auth.go:Register()`
[...]

### ⚠️  Medium Confidence: Email Verification
**Source:** Inferred from email service calls
**Needs Review:** Unclear if verification is required or optional
[...]

### ❓ Low Confidence: Password Reset
**Source:** Endpoint exists but business logic unclear
**Action Required:** Interview team or review product docs
[...]
```

---

## Phase 5: Integration & Workflows

### Unified Workflows Across All Projects

#### 5.1 Command: `/speckit.onboard`

**Purpose:** Set up spec-kit for discovered projects

**Usage:**
```bash
# Onboard all discovered projects
/speckit.onboard --all

# Onboard specific project
/speckit.onboard --project=services-api

# Onboard with reverse engineering
/speckit.onboard --project=services-api --reverse-engineer

# Dry run (show what would be done)
/speckit.onboard --all --dry-run
```

**Process:**
1. Create `.speckit/` directory structure
2. Create `.speckit.config.json` with detected projects
3. Create `specs/projects/` for each project
4. Optionally reverse-engineer existing code
5. Generate project catalog
6. Create or update constitution.md
7. Set up git hooks (optional)

#### 5.2 Command: `/speckit.project-catalog`

**Purpose:** Generate unified catalog of all projects (not just services)

**Output:** Similar to service-catalog but includes ALL project types

```markdown
# Project Catalog

**Total Projects:** 7
**Microservices:** 2
**Monoliths:** 1
**Frontends:** 1
**Mobile Apps:** 1
**Libraries:** 1
**CLI Tools:** 1

---

## Projects by Type

### Backend APIs

#### 1. API Backend (Go)
**Path:** services/api/
**Type:** Microservice
**Tech:** Go + Gin
**Endpoints:** 23
**Dependencies:** user-service, legacy monolith
**Spec-Kit:** ✅ Configured (reverse-engineered)
**Quick Ref:** [services-api/quick-ref.md]

#### 2. User Service (Python)
**Path:** services/user-service/
**Type:** Microservice
**Tech:** Python + FastAPI
**Endpoints:** 15
**Dependencies:** None
**Spec-Kit:** ✅ Configured
**Quick Ref:** [services-user-service/quick-ref.md]

#### 3. Legacy Monolith (Django)
**Path:** legacy/
**Type:** Monolithic Application
**Tech:** Python 2.7 + Django 1.11 ⚠️
**Warning:** End-of-life technology
**Spec-Kit:** ⚠️  Partially configured
**Recommendation:** Plan migration to Python 3

### Frontend Applications

#### 4. Dashboard (React)
[...]

[... etc for all projects ...]

---

## Cross-Project Dependencies

```
API Backend (Go)
  ↓ calls
User Service (Python)

API Backend (Go)
  ↓ calls
Legacy Monolith (Django)

Frontend Dashboard
  ↓ calls
API Backend (Go)

Mobile App
  ↓ calls
API Backend (Go)

CLI Tool
  ↓ calls
API Backend (Go)
```

---

## Token Optimization

With 7 projects, traditional approach:
- Load all: 7 × 2,400 = 16,800 tokens

With quick-refs:
- Load catalog: 500 tokens
- Load quick-refs: 7 × 200 = 1,400 tokens
- Load full spec only when needed: 2,400 tokens
- Total: ~4,300 tokens (74% savings)
```

#### 5.3 Workflow Integration

**Adding New Feature to Existing Project:**
```bash
# 1. Find the project
/speckit.find "user authentication"

# Output:
# Found in project: services-api
# Quick ref: specs/projects/services-api/001-existing-code/quick-ref.md

# 2. Load quick ref (200 tokens)
# Read quick-ref.md

# 3. Create new feature spec
cd specs/projects/services-api
mkdir 002-oauth-integration

# 4. Use standard workflow
/speckit.specify
/speckit.plan
/speckit.tasks
/speckit.implement

# 5. Implementation goes in original project location
# (spec-kit knows to put code in services/api/, not in specs/)
```

**Cross-Project Feature:**
```bash
# Feature spans API Backend + Frontend
/speckit.specify --projects=services-api,frontend

# Spec-kit creates:
# - specs/projects/services-api/003-feature/
# - specs/projects/frontend/002-feature/
# - specs/shared/contracts/feature-api-contract.yaml

# Implementation respects each project's location
```

---

## Implementation Phases

### Phase 1: Core Discovery (Week 1-2)
- [ ] Project detection algorithm
- [ ] Technology identification
- [ ] Architecture classification
- [ ] Basic metadata extraction
- [ ] `/speckit.discover` command

**Deliverables:**
- Detection engine
- Project discovery command
- Discovery report format

### Phase 2: Deep Analysis (Week 3-4)
- [ ] API endpoint extraction (Python, Node, Go, Java)
- [ ] Data model extraction
- [ ] Dependency analysis
- [ ] Configuration extraction
- [ ] Caching system

**Deliverables:**
- Analysis engine for top 4 languages
- Metadata cache system
- Analysis report format

### Phase 3: Non-Invasive Integration (Week 5-6)
- [ ] Parallel structure creation
- [ ] Configuration management
- [ ] Metadata persistence
- [ ] `/speckit.onboard` command
- [ ] Git hooks (optional)

**Deliverables:**
- Onboarding command
- Config management
- Metadata storage

### Phase 4: Reverse Engineering (Week 7-9)
- [ ] Spec generation from APIs
- [ ] Spec generation from models
- [ ] Quick-ref generation
- [ ] Confidence scoring
- [ ] `/speckit.reverse-engineer` command

**Deliverables:**
- Reverse engineering engine
- Auto-generated spec templates
- Confidence indicators

### Phase 5: Unified Workflows (Week 10-12)
- [ ] Project catalog generation
- [ ] Cross-project features
- [ ] Token optimization
- [ ] `/speckit.project-catalog` command
- [ ] Workflow integration

**Deliverables:**
- Project catalog generator
- Unified workflows
- Documentation

---

## Success Criteria

1. **Discovery Success Rate:** > 95% of projects detected correctly
2. **Zero Code Modification:** Existing projects remain untouched
3. **Token Efficiency:** > 70% token savings with quick-refs
4. **Reverse Engineering Accuracy:** > 80% of APIs extracted correctly
5. **User Adoption:** Can onboard in < 5 minutes

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Complex codebases undetectable** | High | Support manual project registration |
| **Wrong architecture detection** | Medium | Allow manual override in config |
| **Reverse engineering inaccurate** | Medium | Mark with confidence levels, require review |
| **Too many projects (100+)** | Low | Selective onboarding, lazy analysis |
| **Breaking existing git workflows** | High | Make git hooks optional, non-invasive |

---

## Open Questions

1. **How to handle monorepos with 50+ projects?**
   - Option A: Selective onboarding (user chooses)
   - Option B: Hierarchical grouping
   - Option C: Lazy loading (only analyze when needed)

2. **Should we modify .gitignore?**
   - Option A: Never touch (user adds .speckit/ manually)
   - Option B: Suggest but don't auto-add
   - Option C: Add with permission

3. **Reverse engineering depth?**
   - Option A: Shallow (just APIs and models)
   - Option B: Deep (full business logic inference)
   - Option C: Configurable depth

4. **Multi-language support priority?**
   - Phase 1: Python, Node.js, Go, Java (80% coverage)
   - Phase 2: Rust, Ruby, PHP, C# (15% coverage)
   - Phase 3: Others on demand (5% coverage)

---

## Next Steps

1. **Review this plan** - Get feedback on approach
2. **Prioritize languages** - Which tech stacks first?
3. **Prototype discovery** - Build basic detector for top 3 languages
4. **Validate approach** - Test on real-world repos
5. **Implement incrementally** - Phase by phase

---

**Status:** Awaiting approval to proceed
**Estimated Timeline:** 12 weeks for full implementation
**Breaking Changes:** None (fully backward compatible)
