# Module 09 – Architecture Decision Records (ADR)

**ADR** is a short, permanent note that captures a **significant technical decision**, the **context** in which you made it, the **options** you considered, the **choice** you made, and the **consequences** (trade-offs). Think of it as a timestamped “why we did it this way” so future you (and teammates) don’t have to reverse-engineer your thinking.

> **The strategic decision layer for SDD: How to capture and document major architectural choices that guide your feature development.**

## 🎯 **What ADR Actually Is**

**ADR is the strategic decision layer that works alongside SDD:**

- **ADR**: Captures major architectural decisions (frameworks, patterns, technology choices)
- **SDD**: Implements features using those architectural decisions

**ADR is NOT:**
- A replacement for SDD
- A detailed implementation process
- A way to document every small decision
- A competing methodology

## 🔄 **ADR vs SDD: Strategic vs Tactical**

### **ADR (Architecture Decision Records)**
**For:** Strategic architectural decisions
**Captures:** Framework choices, patterns, technology stack, security decisions
**Focus:** "Why did we choose this architecture?"

**Example:**
```markdown
# ADR-0001: Use FastAPI for API Development
- **Status:** Accepted
- **Context:** Need modern Python API with async support for AI workflows
- **Decision:** Choose FastAPI over Flask
- **Consequences:** Better type safety, auto-docs, async support
```

### **SDD (Spec-Driven Development)**
**For:** Feature development and implementation
**Captures:** Requirements, plans, tasks, implementation process
**Focus:** "How do we build features using our architecture?"

**Example:**
```markdown
# Spec: Build Chat Endpoint
- **Architecture Reference:** ADR-0001 (FastAPI)
- **Requirements:** Real-time chat with AI agents
- **Implementation:** Use FastAPI + WebSockets per ADR-0001
```

## 🏛️ **Constitution vs ADR: The Key Difference**

### **Constitution = HOW you work (Process & Standards)**
- **Quality standards** (80% test coverage, TypeScript strict mode)
- **Development practices** (TDD, minimal dependencies)
- **UX principles** (clear error messages, consistent design)
- **Team behaviors** (code review requirements, documentation standards)

### **ADR = WHAT you choose (Technical Decisions)**
- **Technology choices** (FastAPI vs Flask, PostgreSQL vs MongoDB)
- **Architecture patterns** (microservices vs monolith, REST vs GraphQL)
- **Infrastructure decisions** (AWS vs Azure, Docker vs Kubernetes)
- **Integration choices** (OpenAI vs Anthropic, payment processors)

## 🔄 **How They Work Together in Enhanced SDD**

```
Constitution (Standards) → ADR (Decisions) → Spec (Requirements) → Plan (Implementation)
```

### **Example Workflow:**

**1. Constitution Sets the Standards:**
```markdown
# Constitution
- All APIs must have 80% test coverage
- Use TypeScript strict mode
- Implement comprehensive error handling
- Document all public interfaces
```

**2. ADR Makes the Decisions:**
```markdown
# ADR-0001: Choose FastAPI for API Development
Context: Need modern Python API with async support
Decision: FastAPI over Flask
Consequences: Better performance, auto-docs, type safety
```

**3. Spec References Both:**
```markdown
# Feature Spec: User Authentication
## Architecture References
- ADR-0001: FastAPI framework choice
- Constitution: 80% test coverage requirement

## Requirements
- User registration/login endpoint
- JWT token management
- Comprehensive error handling (per Constitution)
```

## 🎯 **Why You Need Both**

### **Constitution Without ADR = Vague Standards**
```markdown
# Constitution only
- "Use modern frameworks"
- "Implement good error handling"
- "Choose reliable databases"
```
**Problem:** No specific guidance on which technologies to use.

### **ADR Without Constitution = Inconsistent Quality**
```markdown
# ADR only
- "Choose FastAPI"
- "Use PostgreSQL"
- "Implement Redis caching"
```
**Problem:** No quality standards for how to implement these choices.

### **Constitution + ADR = Complete Guidance**
```markdown
# Constitution
- 80% test coverage required
- TypeScript strict mode
- Comprehensive error handling

# ADR-0001
- Choose FastAPI (with Constitution's quality standards)
- Choose PostgreSQL (with Constitution's testing requirements)
- Choose Redis (with Constitution's error handling standards)
```

## 🛠️ **Practical Example: AI Tutor Application**

### **Constitution (Process Standards):**
```markdown
# Project Constitution
- All code must have 80% test coverage
- Use Python type hints everywhere
- Implement comprehensive error handling
- Document all API endpoints
- Use async/await patterns
- Follow RESTful API design
```

### **ADRs (Technical Decisions):**
```markdown
# ADR-0001: FastAPI for API Development
Context: Need modern Python API with async support
Decision: FastAPI over Flask
Consequences: Better performance, auto-docs, type safety

# ADR-0002: PostgreSQL for Data Storage
Context: Need reliable database for user data
Decision: PostgreSQL over MongoDB
Consequences: ACID compliance, mature ecosystem

# ADR-0003: OpenAI Agents for AI Features
Context: Need sophisticated AI tutoring capabilities
Decision: OpenAI Agents SDK over custom implementation
Consequences: Advanced AI features, vendor lock-in
```

### **Spec References Both:**
```markdown
# AI Tutor Chat System Spec
## Architecture References
- ADR-0001: FastAPI framework choice
- ADR-0002: PostgreSQL database choice
- ADR-0003: OpenAI Agents for AI features

## Quality Requirements (from Constitution)
- 80% test coverage for all endpoints
- Comprehensive error handling
- Type hints for all functions
- Async/await patterns throughout

## Implementation Requirements
- Real-time chat with AI tutor
- User authentication and session management
- Chat history storage and retrieval
```

## 🔄 **The Complete Enhanced SDD Flow**

```
1. Constitution → Sets quality standards and development practices
2. ADR → Makes specific technology and architecture decisions
3. Spec → Defines requirements referencing both Constitution and ADRs
4. Plan → Creates implementation plan following Constitution standards
5. Tasks → Breaks down into actionable items
6. TDD/EDD → Implements with Constitution's testing requirements
7. PHR → Documents the process
```

## 💡 **Key Insight**

**Constitution is your "quality DNA" - it defines HOW you build everything.**
**ADR is your "decision history" - it defines WHAT you chose and why.**

Without Constitution, your ADRs might lead to inconsistent quality.
Without ADRs, your Constitution has no specific technical direction.

**Together, they create a complete framework for building high-quality, well-architected applications.**

The Constitution ensures every implementation follows your quality standards, while ADRs ensure you make informed, documented technology choices that align with those standards.

## 🤝 **How ADR and SDD Work Together**

**The Complete Workflow:**
```
ADR → Spec → Plan → Tasks → Implement → PHR
```

**1. ADR Phase**: Make strategic architectural decisions
**2. SDD Phase**: Implement features using those decisions
**3. Integration**: Reference ADRs in specs, link PHRs to ADRs

### **Why This Works**

**ADR provides the "why":**
- Why did we choose FastAPI?
- Why did we use microservices?
- Why did we pick this database?

**SDD provides the "how":**
- How do we build features with FastAPI?
- How do we implement microservice communication?
- How do we use this database effectively?

## 🎯 **When to Write an ADR**

**Write ADRs for strategic decisions:**
- Framework/SDK choices (FastAPI vs Flask, React vs Vue)
- Architecture patterns (microservices vs monolith)
- Technology stack decisions (PostgreSQL vs MongoDB)
- Security and compliance choices (OAuth vs JWT)
- Infrastructure decisions (AWS vs Azure, Docker vs Kubernetes)

**Don't write ADRs for:**
- Implementation details (use PHRs instead)
- Small feature decisions (use specs instead)
- Temporary choices (use comments instead)
- Code refactoring (use PHRs instead)

## 📝 **ADR Template**

**Keep it 1–2 pages and focused on strategic decisions:**

```markdown
# ADR-0001: Use FastAPI for API Development

- **Status:** Proposed | Accepted | Superseded | Deprecated
- **Date:** YYYY-MM-DD

## Context
What problem/constraints led to this decision?

## Options
- **A)** Option A (pros/cons)
- **B)** Option B (pros/cons)
- **C)** Option C (pros/cons)

## Decision
The chosen option and why

## Consequences
- **Positive:** Benefits and advantages
- **Negative:** Costs, trade-offs, and risks

## References
- Links to docs, issues, benchmarks, POCs
- Related ADRs: ADR-0002, ADR-0003
```

## 🎯 **Real-World Examples**

### **ADR-0001: Use FastAPI for API Development**
- **Status:** Accepted — 2025-01-15
- **Context:** Need modern Python API with async support for AI workflows
- **Options:**
  - **A)** FastAPI: Type safety, auto-docs, async support, modern
  - **B)** Flask: Simple, familiar, but limited async support
  - **C)** Django REST: Full-featured but heavyweight for our needs
- **Decision:** Choose **FastAPI** for modern async support and type safety
- **Consequences:**
  - ✅ Better performance, auto-documentation, type safety
  - ⚠️ Learning curve for team, more complex than Flask

### **ADR-0002: Use PostgreSQL for Primary Database**
- **Status:** Accepted — 2025-01-15
- **Context:** Need reliable, ACID-compliant database for financial data
- **Options:**
  - **A)** PostgreSQL: ACID, JSON support, mature ecosystem
  - **B)** MongoDB: Document-based, but eventual consistency
  - **C)** SQLite: Simple, but not suitable for production
- **Decision:** Choose **PostgreSQL** for ACID compliance and reliability
- **Consequences:**
  - ✅ ACID compliance, mature ecosystem, JSON support
  - ⚠️ More complex than NoSQL, requires schema management

## 🔗 **Integration with SDD**

### **Reference ADRs in Specs**
```markdown
# Spec: Build Chat Endpoint

## Architecture References
- ADR-0001: FastAPI framework choice
- ADR-0002: PostgreSQL database choice
- ADR-0003: WebSocket for real-time communication

## Requirements
- Real-time chat with AI agents
- Use FastAPI per ADR-0001
- Store chat history in PostgreSQL per ADR-0002
```

### **Link PHRs to ADRs**
```markdown
# PHR-0005: Implement Chat Endpoint

links:
  adr: docs/adr/0001-fastapi-choice.md
```

## 💡 **Best Practices**

**Do:**
- Keep ADRs **small and specific** (one decision per ADR)
- Use **numbered files** like `docs/adr/0001-*.md`
- Update **Status** when decisions change
- Reference ADR IDs in specs and PHRs
- Link related ADRs together

**Don't:**
- Write ADRs for implementation details
- Mix multiple decisions in one ADR
- Forget to update status when superseded
- Write ADRs for temporary choices

## 🚀 **Integration with SDD Workflow**

### **Complete Development Process**

**1. ADR Phase** - Strategic Decisions
```bash
# Create ADR for major architectural choices
/adr --title "Choose FastAPI for API Development"
```

**2. SDD Phase** - Feature Development
```bash
# Use ADRs to guide feature development
/spec --feature chat --adr 0001
/plan --feature chat
/tasks --feature chat
/edd --feature chat
/phr --feature chat
```

### **Cross-Reference Everything**

**ADRs inform Specs:**
```markdown
# Spec: Build Chat Endpoint
## Architecture References
- ADR-0001: FastAPI framework choice
- ADR-0002: PostgreSQL database choice
```

**PHRs link to ADRs:**
```markdown
# PHR-0005: Implement Chat Endpoint
links:
  adr: docs/adr/0001-fastapi-choice.md
  previous_prompt: 0004
  next_prompt: 0006
```

## 🎯 **Summary**

**ADR is the strategic decision layer that works alongside SDD:**

- **ADR**: Captures major architectural decisions (frameworks, patterns, technology choices)
- **SDD**: Implements features using those architectural decisions
- **Integration**: ADRs inform specs, PHRs reference ADRs

**Key principles:**
- Write ADRs for strategic decisions, not implementation details
- Reference ADRs in specs to guide feature development
- Link PHRs to ADRs for complete traceability
- Keep ADRs focused and specific (one decision per ADR)

**The complete workflow:**
```
ADR → Spec → Plan → Tasks → Implement → PHR
```

**Remember: ADR provides the "why" (strategic decisions), SDD provides the "how" (feature implementation). Both are essential for building reliable, well-architected applications.**


