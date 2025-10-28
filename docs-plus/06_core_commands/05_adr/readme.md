# Module 05: Architecture Decision Records (ADR) - Post-Planning Review

> **After `/plan` completes, you'll see a suggestion to review for architectural decisions. Run `/adr` to capture significant technical choices before implementation.**

## The Problem: Undocumented Decisions

Teams make critical architectural decisions during planning—database choices, API patterns, security models—but these decisions often live only in chat history or planning docs. When revisited months later:

- **Why questions** have no documented answers
- **Tradeoffs** are forgotten
- **Alternatives** that were considered are lost
- **Context** that influenced the decision is missing

## The Solution: Explicit ADR Review After Planning

ADRs (Architecture Decision Records) capture **why** technical decisions were made, not just **what** was decided. In Spec Kit, ADRs are created **after planning** when you have full context.

### When ADRs Happen

```
/constitution → /specify → /plan
                              ↓
                   📋 Suggestion appears: "Review for architectural decisions? Run /adr"
                              ↓
                         (You run /adr)
                              ↓
                   ADRs created in history/adr/
                              ↓
                         /tasks → /implement
```

**Key flow:**

1. Complete planning with `/plan`
2. **PHR automatically created** (planning session documented)
3. **ADR suggestion appears** (automatic reminder)
4. **You explicitly run `/adr`** when ready
5. ADRs created for significant decisions

### Why Explicit, Not Automatic?

ADR creation requires **careful analysis and judgment**. You might need to:

- Discuss decisions with the team first
- Review existing ADRs before creating new ones
- Decide if decisions are truly architecturally significant

The suggestion ensures you don't forget, but you control when it happens.

---

## What Makes a Decision "Architecturally Significant"?

The `/adr` command uses three criteria (ALL must be true):

### 1. Impacts How Software is Structured

Does this decision change how engineers write, organize, or architect code?

✅ **Yes:** Choosing REST vs GraphQL API  
❌ **No:** Which HTTP client library to use

### 2. Has Notable Tradeoffs or Alternatives

Were alternatives considered? Are there consequences to understand?

✅ **Yes:** PostgreSQL vs MongoDB (different data models, query patterns)  
❌ **No:** Using prettier for formatting (no architectural tradeoff)

### 3. Will Be Questioned or Revisited Later

Will someone ask "why did we do this?" in 6 months?

✅ **Yes:** Microservices vs monolith architecture  
❌ **No:** Naming a helper function

### Examples

**Architecturally Significant (Create ADR):**

- Database choice: PostgreSQL vs MongoDB
- Auth strategy: JWT vs sessions
- API pattern: REST vs GraphQL vs RPC
- Deployment: Serverless vs containers
- State management: Redux vs Context API
- Testing strategy: Unit vs integration focus

**NOT Architecturally Significant (Skip ADR):**

- Variable naming conventions
- Code formatting rules
- Which linter to use
- Specific library versions
- File organization preferences
- Comment style guidelines

---

## ADR Granularity: Clusters vs Atomic Decisions

### ✅ CORRECT: Document Decision Clusters

Group related technologies that work together as an integrated solution:

**Good Example - Frontend Stack:**

```
ADR-0001: Frontend Technology Stack
- Framework: Next.js 14 (App Router)
- Styling: Tailwind CSS v3
- Deployment: Vercel
- State: React Context

Alternatives: Remix + styled-components + Cloudflare
```

**Why this works:**

- These technologies are chosen **together** for integration benefits
- They would likely **change together** if requirements shift
- ONE decision: "Modern React stack optimized for Vercel"

### ❌ INCORRECT: Atomic Technology Choices

Don't create separate ADRs for each technology in an integrated solution:

**Bad Example:**

```
ADR-0001: Use Next.js Framework
ADR-0002: Use Tailwind CSS
ADR-0003: Deploy on Vercel
ADR-0004: Use React Context
```

**Problems:**

- Over-documentation (4 ADRs instead of 1)
- Loses integration story (why these work together)
- Makes decisions seem independent when they're not

### Clustering Rules

**Cluster together when:**

- Technologies are chosen for integration benefits
- They would change together (coupled lifecycle)
- One decision explains why all components fit

**Separate ADRs when:**

- Decisions are independent (frontend vs backend stacks)
- Could evolve separately (API protocol vs database choice)
- Different teams own different parts

### Real-World Examples

| Scenario            | Number of ADRs         | Titles                                                         |
| ------------------- | ---------------------- | -------------------------------------------------------------- |
| Frontend + Backend  | **2 ADRs**             | "Frontend Stack", "Backend Stack"                              |
| Auth approach       | **1 ADR**              | "Authentication Architecture" (JWT + Auth0 + session strategy) |
| Data layer          | **1 ADR**              | "Data Architecture" (PostgreSQL + Redis + migration tools)     |
| Deployment          | **1 ADR**              | "Deployment Platform" (Vercel + GitHub Actions + monitoring)   |
| Microservices split | **1 ADR per boundary** | "User Service Boundary", "Payment Service Boundary"            |

### Industry Standards

This follows **Michael Nygard's ADR pattern** (2011) and **ThoughtWorks' recommendation**:

- ADRs document **architectural decisions**, not technology inventories
- Focus on **why**, not just **what**
- Cluster related choices that share context and tradeoffs

**References:**

- [Michael Nygard: Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ThoughtWorks Tech Radar: Lightweight ADRs](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)

---

## How It Works

### Step 1: Complete Planning

```bash
/plan  # Design your feature architecture
```

You create:

- `specs/001-auth/plan.md` - Main planning document
- `specs/001-auth/research.md` - Research notes (optional)
- `specs/001-auth/data-model.md` - Data models (optional)
- `specs/001-auth/contracts/` - API contracts (optional)

### Step 2: See ADR Suggestion

After `/plan` completes, you see:

```
📋 Planning complete! Review for architectural decisions? Run /adr
```

This happens automatically—no action needed yet.

### Step 3: Run /adr When Ready

When you're ready to review (immediately, or after team discussion):

```bash
/adr  # Analyzes planning artifacts
```

### Step 4: ADR Analysis Workflow

The `/adr` command:

1. **Loads planning context**

   - Reads plan.md, research.md, data-model.md, contracts/
   - Understands the feature requirements

2. **Extracts decisions**

   - Identifies technical choices made during planning
   - Examples: "Using PostgreSQL", "JWT authentication", "REST API"

3. **Checks existing ADRs**

   - Reads history/adr/ to find related decisions
   - Avoids duplicates or superseded decisions

4. **Applies significance test**

   - For each decision, checks all 3 criteria
   - Only proceeds if decision is architecturally significant

5. **Creates ADR files**

   - Generates history/adr/NNNN-decision-title.md
   - Sequential numbering (0001, 0002, 0003, etc.)
   - Complete ADR template with context, decision, consequences

6. **Shows report**
   - Lists created ADRs
   - Lists referenced ADRs
   - Confirms readiness for /tasks

### Step 5: Review and Proceed

You now have:

- ✅ Planning docs (plan.md, research.md, etc.)
- ✅ PHR of planning session (automatic)
- ✅ ADRs for architectural decisions (explicit via /adr)

Ready for `/tasks` to break down implementation!

---

## What Each ADR Contains

ADRs are created in `history/adr/` with sequential numbering:

```
docs/
└── adr/
    ├── 0001-use-postgresql-database.md
    ├── 0002-jwt-authentication-strategy.md
    └── 0003-rest-api-architecture.md
```

Each ADR file contains:

```markdown
# ADR-0002: JWT Authentication Strategy

## Status

Accepted

## Context

We need secure, stateless authentication for our API...

## Decision

We will use JWT (JSON Web Tokens) for authentication...

## Consequences

### Positive

- Stateless authentication (no server-side sessions)
- Works well with microservices
- Industry standard with good library support

### Negative

- Token revocation is complex
- Must manage token refresh carefully
- Token size larger than session IDs

## Alternatives Considered

- Session-based auth (rejected: requires sticky sessions)
- OAuth2 (rejected: overkill for our use case)

## Related

- Spec: specs/001-auth/spec.md
- Plan: specs/001-auth/plan.md
```

---

## Integrated Workflow

### Full SDD Flow with ADRs

```
1. /sp.constitution
   └─→ PHR created (automatic)

2. /sp.specify
   └─→ PHR created (automatic)

3. /sp.plan
   └─→ PHR created (automatic)
   └─→ 📋 "Review for architectural decisions? Run /adr"

4. /sp.adr  ← YOU RUN THIS
   └─→ ADRs created in history/adr/
   └─→ Shows report

5. /sp.tasks
   └─→ PHR created (automatic)

6. /sp.implement
   └─→ PHR created (automatic)
```

### ADRs Link Planning to Implementation

- **Spec** (specs/001-auth/spec.md) - WHAT we're building
- **Plan** (specs/001-auth/plan.md) - HOW we'll build it
- **ADR** (history/adr/0002-jwt-auth.md) - WHY we made key decisions
- **Tasks** (specs/001-auth/tasks.md) - Work breakdown
- **Implementation** - Actual code

ADRs provide the critical **WHY** context that specs and plans don't fully capture.

---

## Common Scenarios

### Scenario 1: Simple Feature (No ADRs Needed)

```bash
/plan  # Design simple CRUD endpoint
# → 📋 Suggestion: "Run /adr"

/adr  # Analyzes planning artifacts
# → "No architecturally significant decisions found. Proceed to /tasks."
```

**Result:** No ADRs created (implementation details don't need ADRs)

### Scenario 2: Complex Feature (Multiple ADRs)

```bash
/plan  # Design new microservice with database and API
# → 📋 Suggestion: "Run /adr"

/adr  # Analyzes planning artifacts
# → Creates:
#    - history/adr/0005-use-event-sourcing.md
#    - history/adr/0006-kafka-message-broker.md
#    - history/adr/0007-graphql-api.md
# → "3 ADRs created. Proceed to /tasks."
```

**Result:** Multiple ADRs for significant architectural choices

### Scenario 3: References Existing ADR

```bash
/plan  # Design feature using existing patterns
# → 📋 Suggestion: "Run /adr"

/adr  # Analyzes planning artifacts
# → "Referenced existing ADRs:
#    - history/adr/0002-jwt-authentication.md
#    - history/adr/0003-rest-api-pattern.md
#    No new ADRs needed. Proceed to /tasks."
```

**Result:** No new ADRs (reusing established patterns)

---

## Troubleshooting

### "No plan.md found"

**Cause:** Running `/adr` before `/plan`  
**Solution:** Complete planning first: `/plan Design the feature`

### "No architecturally significant decisions found"

**Cause:** Planning contains only implementation details  
**Solution:** Normal! Not every feature needs ADRs. Proceed to `/tasks`

### Too Many ADRs Created

**Cause:** Including implementation details in planning  
**Solution:** Focus planning on architecture, not code-level decisions

### ADR Duplicates Existing ADR

**Cause:** Didn't reference existing patterns  
**Solution:** Review history/adr/ before planning new features

---

## Best Practices

### Do Create ADRs For:

✅ Technology choices (databases, frameworks, platforms)  
✅ Architectural patterns (microservices, event-driven, layered)  
✅ Security models (auth strategies, encryption approaches)  
✅ API contracts (REST vs GraphQL, versioning strategies)  
✅ Data models (normalization, schema design)  
✅ Infrastructure decisions (deployment patterns, scaling strategies)

### Don't Create ADRs For:

❌ Code style and formatting  
❌ Library choices (unless architectural impact)  
❌ Variable/function naming  
❌ Implementation algorithms  
❌ Testing implementation details  
❌ Documentation formats

### When in Doubt:

Ask: "Will someone question this decision in 6 months?"

- **Yes** → Create ADR
- **No** → Skip ADR

---

## Summary

ADRs capture the **why** behind architectural decisions:

✅ **Automatic suggestion** after `/plan` - Never forget to review  
✅ **Explicit execution** via `/adr` - You control timing  
✅ **Significance test** - Only creates ADRs for important decisions  
✅ **Sequential numbering** - Consistent IDs (0001, 0002, 0003, etc.)  
✅ **Location** - All ADRs in history/adr/ (centralized)  
✅ **Full context** - Links to specs, plans, alternatives, consequences  
✅ **Team alignment** - Documented decisions reduce debate

### Key Workflow:

1. Complete `/plan` → Suggestion appears
2. Run `/adr` when ready → ADRs created (if significant)
3. Proceed to `/tasks` → Implementation breakdown

**Remember:** ADRs are for architecture, not implementation. Focus on decisions that:

- Change how code is structured
- Have notable tradeoffs
- Will be questioned later

Start creating ADRs today to document the **why** behind your technical choices! 🚀
