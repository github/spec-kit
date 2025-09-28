# Context Engineering Workflow

## Purpose
A systematic approach to clarify tasks, gather context, research solutions, and create implementation plans with full end-to-end coverage across frontend, backend, database, API, tests, and documentation.

## Workflow Phases

### Phase 1: Task Clarification
**Goal:** Clarify the task fully before planning or coding

**Process:**
1. Analyze the user request for ambiguity or missing details
2. Ask specific questions to understand requirements
3. Confirm scope and boundaries
4. Get explicit user confirmation before proceeding

**Rule:** Never proceed without explicit user confirmation

**Output:** Clear, confirmed task definition

---

### Phase 2: Project Context Gathering
**Goal:** Gather project context and code structure

**Process:**
1. Examine current codebase structure
2. Identify files and modules that might be impacted
3. Map dependencies between frontend, backend, database, and APIs
4. Understand existing patterns and conventions
5. Assess current architecture and tech stack

**Checklist:**
- [ ] Identify files and modules that might be impacted
- [ ] Highlight dependencies between frontend, backend, database, and APIs
- [ ] Document existing patterns and conventions
- [ ] Map current architecture

**Output:** Comprehensive project context analysis

---

### Phase 3: Research Preparation
**Goal:** Determine which research tools and sources to use

**Process:**
1. Ask which tools to use for research:
   - Archon MCP (for documentation and code examples)
   - DeepWiki MCP (for GitHub repository documentation)
   - Web search (for current best practices)
   - Local documentation
   - Other relevant sources

2. Prioritize research areas based on task complexity

**Output:** Research strategy and tool selection

---

### Phase 4: Research Execution
**Goal:** Perform comprehensive research for the clarified task

**Process:**
1. Execute research using chosen tools
2. Gather implementation patterns and best practices
3. Collect relevant code examples
4. Document technical requirements and constraints
5. Identify potential challenges and solutions

**Deliverable:** Research notes + patterns for implementation + Task-specific Research docs

**Research Areas:**
- Technical implementation approaches
- Best practices and conventions
- Security considerations
- Performance implications
- Integration requirements
- Testing strategies
- code examples


**Output:** Complete research documentation

---

### Phase 5: Implementation Planning
**Goal:** Create comprehensive implementation plan with full system coverage

**Process:**
1. Identify which layers are impacted:
   - Frontend (components, forms, UI state)
   - Backend (services, controllers, business logic)
   - Database (schemas, migrations, seeds)
   - API (routes, contracts, clients)
   - Tests (unit, integration, E2E)
   - Documentation (API reference, guides, changelogs)

2. Create detailed implementation plan for each layer

3. Include **Full Implementation Checklist**

4. Plan integration points and dependencies

5. Identify potential risks and mitigation strategies

**Full Implementation Checklist:**
- [ ] Frontend changes (components, forms, UI state)
- [ ] Backend changes (services, controllers, logic)
- [ ] Database changes (schemas, migrations, seeds)
- [ ] API changes (routes, contracts, clients)
- [ ] Test updates (unit, integration, E2E)
- [ ] Documentation updates (API reference, guides, changelogs)

**Output:** Comprehensive implementation plan

---

## Workflow Rules

### Core Principles
1. **Never stop at surface-level implementation** - Always consider system-wide impacts
2. **Always check for cross-layer impacts** - Ensure all affected components are identified
3. **Always produce research + plan before implementation** - No coding without proper preparation
4. **Every plan must include the Full Implementation Checklist** - Ensure complete coverage

### Quality Gates
- **Clarification Gate:** User must explicitly confirm task understanding
- **Context Gate:** All impacted areas must be identified
- **Research Gate:** Sufficient research must be completed
- **Planning Gate:** Full implementation checklist must be completed

### Success Criteria
- Task is clearly defined and confirmed
- All system impacts are identified
- Research provides sufficient implementation guidance
- Implementation plan covers all affected layers
- No partial implementations or missed dependencies

---

## Execution Guidelines

### When to Use This Workflow
- Complex features that span multiple system layers
- New functionality with unclear requirements
- Refactoring that might have wide-reaching impacts
- Integration tasks involving multiple components
- Any task where full system impact is unclear

### Workflow Outputs
1. **Clarified Task Document** - Confirmed requirements and scope
2. **Task Context File** - Comprehensive project context, current state, and impacted areas analysis
3. **Research Documentation** - Patterns, best practices, and examples
4. **Implementation Plan** - Detailed plan with full system coverage

### Quality Assurance
- Each phase must be completed before moving to the next
- All checklists must be fully completed
- User confirmation required at key decision points
- Full system coverage must be demonstrated

---

## Enforcement

**Mandatory Requirements:**
- Every implementation plan must contain the Full Implementation Checklist
- All cross-layer impacts must be identified and planned
- Research must be completed before implementation planning
- User confirmation required before proceeding from clarification phase

**Goal:** Ensure no partial implementations — always maintain system-wide awareness and comprehensive coverage.