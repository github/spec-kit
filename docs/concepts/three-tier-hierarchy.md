# The Three-Tier Hierarchy

Spec-Driven Development operates across three distinct layers, each serving a specific purpose while feeding into the next level.

## Overview

```
Tier 1: Product Vision
    ↓ (informs)
Tier 2: Feature Specification
    ↓ (informs)
Tier 3: Implementation Plan
```

Each tier increases in technical detail while remaining focused on its specific concern.

## Tier 1: Product Vision (Strategic Layer)

**Purpose**: Define the strategic direction, market opportunity, and product-wide requirements.

**Scope**: Entire product (one per product)

**File**: `docs/product-vision.md`

**When to Create**:
- Complex products with multiple features
- 0-to-1 development
- Multi-team projects requiring strategic alignment

**When to Skip**:
- Single features
- Quick prototypes
- Brownfield additions to established systems

### What It Contains

- **Problem Statement** - What problem does this product solve?
- **Market Opportunity** - Who are the users and what's the opportunity?
- **User Personas** - Who are we building for?
- **Product Goals** - What success looks like
- **Success Metrics & KPIs** - How we measure success
- **Business Constraints** - Timeline, budget, resources
- **Product-Wide Non-Functional Requirements** - Performance targets, security standards, compliance needs
- **Risk Analysis** - What could go wrong?

### What It Excludes

- Technical decisions (architecture, technologies, design patterns)
- System design (API design, data models)
- Feature specifications (specific functional requirements)

### Example

```
Product Vision for Photo Sharing App

Problem: Families separated by distance struggle to stay connected
through photos. Current solutions are cluttered, invasive, or require
technical expertise to set up.

Market: 2 billion smartphone users globally, 85% share photos regularly

Personas:
- Grandparents (tech-hesitant, motivated by family)
- Parents (busy, want simple sharing)
- Young adults (heavy content creators)

Success Metrics:
- 100k active users in year 1
- Average session 15+ minutes
- 80% photo sharing completion rate
- 4.5+ star rating

Product NFRs:
- Performance: Load times <2s, 99.9% uptime
- Security: End-to-end encryption, GDPR compliant
- Scale: 1M concurrent users by year 2
- Privacy: No ads, no tracking
```

## Tier 2: Feature Specification (Requirements Layer)

**Purpose**: Define functional and non-functional requirements for a specific feature.

**Scope**: Single feature (many per product)

**File**: `specs/[feature-id]/spec.md`

**Command**: `/specify`

### What It Contains

- **Functional Requirements** - What the feature must do
- **Non-Functional Requirements** - Performance, security, scale targets
- **Technical Constraints** - What exists that must be integrated with
- **User Stories** - How users interact with the feature
- **Acceptance Criteria** - Testable conditions for success
- **Use Cases** - Specific scenarios and flows
- **Edge Cases** - What happens in unusual situations
- **Dependencies** - What else needs to be in place

### Key Principle: Requirements vs Decisions

✅ **Capture requirements** (belongs in Tier 2):
- "Must handle 1000 requests/second"
- "Must store photos indefinitely without data loss"
- "Must integrate with existing PostgreSQL database"
- "Must support offline mode with sync when reconnected"

❌ **Don't capture decisions** (belongs in Tier 3):
- "Use Redis for caching"
- "Implement with Node.js"
- "Store in PostgreSQL with sharding"
- "Use WebSockets for real-time sync"

The distinction is critical: requirements describe what you need, decisions describe how you'll achieve it. If requirements change, you might choose different decisions. If decisions are captured in specs, changing them means updating specs (painful). If requirements are captured, you can evolve decisions freely.

### Reads From

If a Product Vision exists, the feature spec inherits:
- Personas (for user story context)
- Product goals (for alignment)
- Product NFRs (as baselines)
- Success metrics (for feature-level targets)

### Example Specification

```
Feature: Real-Time Photo Sharing

Functional Requirements:
- Users can upload photos to a shared album
- Users can invite others to view/contribute
- Photos display in chronological order
- Users receive notifications when new photos added
- Users can add captions and comments

Non-Functional Requirements:
- Photos must display within 2 seconds
- Support 10,000 concurrent users
- 99.9% uptime SLA
- All data encrypted in transit and at rest

Technical Constraints:
- Must use existing user authentication system
- Must store in existing PostgreSQL database
- Must work with current frontend framework

Acceptance Criteria:
- User uploads photo → visible to all invited users within 2 seconds
- 10,000 simultaneous uploads → no degradation
- Offline upload → syncs when reconnected
- Deleted photo → removed from all clients within 5 seconds
```

## Tier 3: Implementation Plan (Architecture Layer)

**Purpose**: Make architecture decisions and create detailed implementation blueprints.

**Scope**: Single feature + system architecture evolution

**File**: `specs/[feature-id]/plan.md` + `docs/system-architecture.md`

**Command**: `/plan`

### What It Contains

- **Architecture Diagram** - System components and interactions
- **Technology Choices** - Selected technologies with rationale
- **Data Model** - Database schema and structure
- **API Design** - Endpoints and contracts
- **System Integration** - How this connects to existing systems
- **Implementation Approach** - Step-by-step build strategy
- **Testing Strategy** - How we validate correctness
- **Deployment Plan** - How we roll out safely
- **Security Implementation** - How requirements become secure design

### Makes Decisions

Transforms requirements into technical solutions:

| Requirement | Decision | Rationale |
|-------------|----------|-----------|
| "1000 req/s" | Add Redis caching layer | Reduces DB load, meets latency |
| "Existing PostgreSQL" | Add photo metadata table | Minimal schema changes |
| "Offline support" | SQLite locally + sync queue | Works offline, eventual consistency |
| "Real-time updates" | WebSockets + event bus | Low latency, scales horizontally |

### Dual Responsibility

The plan handles two concerns:

1. **Feature-Specific**: How to build this specific feature
2. **System-Wide**: How this feature impacts overall architecture

### Architecture Evolution

The system architecture grows as features are added:

**First feature (v1.0.0)**: Establishes foundational architecture
```
Simple monolith:
- Node.js + Express API
- PostgreSQL database
- React frontend
- No caching layer
```

**Subsequent features** (v1.1.0, v1.2.0, etc):

**Level 1 - Work Within**: Use existing architecture
```
"/plan Real-time notifications"
→ Uses existing WebSocket pattern
→ Architecture stays v1.0.0
```

**Level 2 - Extend**: Add new components (minor version)
```
"/plan Photo sharing with 10k concurrent users"
→ Adds Redis caching layer
→ Architecture becomes v1.1.0
```

**Level 3 - Refactor**: Change core structure (major version)
```
"/plan Support 1M users and video streaming"
→ Migrates to microservices
→ Adds CDN and message queue
→ Architecture becomes v2.0.0 (breaking change)
```

### When Plans Conflict

If a new feature's plan would conflict with existing architecture:

```
/plan should mention:
- Why existing architecture insufficient
- What architectural changes needed
- Whether this is Level 2 (extend) or Level 3 (refactor)
- Migration path from old to new
```

## Workflow Integration

The three tiers work together:

### Greenfield (New Product)

```
1. /product-vision → Strategic direction established
2. /specify proj-1 → MVP feature requirements defined
3. /plan proj-1 → Architecture v1.0.0 established + implementation plan
4. /specify proj-2 → Second feature requirements (reads product vision)
5. /plan proj-2 → Architecture v1.1.0 (extends v1.0.0) + implementation plan
6. /specify proj-3, /plan proj-3, etc.
```

### Brownfield (Existing Product)

```
[Existing product-vision.md and system-architecture.md v1.2.0]
1. /specify proj-N → New feature requirements (reads existing context)
2. /plan proj-N → Works within OR extends architecture
```

### Architecture Evolution

```
[After 9 features at v1.9.0]
/specify proj-10 → Video calling feature
/plan proj-10 → Determines microservices needed
         → Updates system-architecture.md to v2.0.0
         → Documents breaking changes
         → Provides migration strategy
```

## Separation of Concerns

This three-tier structure ensures:

| Tier | Owned By | Changes When | Stable Until |
|------|----------|-------------|--------------|
| Vision | Product leadership | Product strategy shifts | Product pivot |
| Spec | Product + domain experts | Requirements change | Feature complete |
| Plan | Tech leads + architects | Tech landscape evolves | Architecture refactor |

This separation allows:
- **Product team** to update specs without touching architecture
- **Technical team** to optimize architecture without changing what users see
- **Teams to scale** without constant synchronization

## Inheritance & Context

Each tier provides context for the next:

```
Product Vision
├─ Personas → used by Specifications
├─ Product goals → used by Planning
├─ NFR baselines → used by Planning
└─ Success metrics → used by Specifications

Feature Specs
├─ Requirements → used by Planning
├─ Constraints → used by Planning
└─ User stories → used by Planning

Implementation Plans
└─ Architecture → Used for next feature's constraints
```

## When to Create Each Tier

| Tier | Create When | Skip When |
|------|------------|-----------|
| Product Vision | 0-to-1 product, multiple features, multi-team | Single feature, clear product already exists |
| Feature Spec | Every new feature | Tiny bug fix (<200 LOC) |
| Implementation Plan | After spec is solid | Trivial changes |

## Example: Building a Complete System

**Product**: Collaborative document editor

```
TIER 1: Product Vision
├─ Target: Teams needing real-time collaboration
├─ Personas: Designers, product managers, engineers
├─ Goals: Primary collaboration tool for 100k teams
└─ NFRs: <100ms latency, 99.95% uptime

TIER 2: Feature Specifications
├─ Spec 1: Rich text editing
│   └─ Requirements: Bold, italic, code, formatting
├─ Spec 2: Real-time collaboration
│   └─ Requirements: Multiple users, operational transform
├─ Spec 3: Comments & suggestions
│   └─ Requirements: Async feedback, resolution workflow
└─ Spec 4: Version history
    └─ Requirements: Snapshots, restore, branching

TIER 3: Implementation Plans
├─ Plan 1: Editor core (v1.0.0 architecture)
├─ Plan 2: Collaboration layer
├─ Plan 3: Comments system
└─ Plan 4: Version control
```

Each spec clearly states "what", each plan clearly states "how".

## Next Steps

- **See it in action**: [Development Workflow](./development-workflow.md)
- **Learn the phases**: [Phase 1: Specification](./phase-specification.md), [Phase 2: Planning](./phase-planning.md)
- **Get started**: [Getting Started Tutorials](../getting-started/)
