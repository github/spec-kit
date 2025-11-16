# Implementation Plan: [FEATURE]

<!-- VARIANT:sh - Run `/scripts/bash/update-agent-context.sh __AGENT__` for your AI assistant -->
<!-- VARIANT:ps - Run `/scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__` for your AI assistant -->

**Branch**: `[username/jira-123.feature-name]` OR `[username/feature-name]` | **Date**: [DATE] | **Spec**: [link]

<!-- Workspace Metadata (auto-populated in multi-repo workspaces) -->
**Workspace**: [WORKSPACE_NAME] (if workspace mode)
**Target Repository**: [REPO_NAME] (if workspace mode)
**Repository Path**: [REPO_PATH] (absolute path to implementation repo)

**Input**: Feature specification from `/specs/[feature-id]/spec.md`
**Optional Inputs**:
- docs/product-vision.md: Product strategy and context (if exists)
- docs/system-architecture.md: Existing system architecture (if exists)

## Execution Flow (/plan command scope)
```
Phase -1: Architecture Context Loading
1. Check if docs/system-architecture.md exists:
   → If exists (brownfield - extending existing system):
     - Load current architecture version (e.g., v1.2.0)
     - Load technology stack constraints (must use PostgreSQL, etc.)
     - Load architecture patterns (monolith vs microservices)
     - Load architecture evolution history
     - Determine impact level: Work Within | Extend | Refactor
   → If missing (greenfield - MVP/first feature):
     - This plan will ESTABLISH system architecture
     - Will create docs/system-architecture.md (v1.0.0)
     - Foundational decisions made here affect all future features

2. Determine Architecture Impact Level:
   → Level 1 - Work Within: Feature uses existing architecture (no new components)
   → Level 2 - Extend: Feature adds components (S3, Redis) but doesn't change structure
   → Level 3 - Refactor: Feature requires arch change (monolith→microservices) [BREAKING]

Phase 0-10: Feature Planning
3. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
4. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
   → ULTRATHINK: Analyze technical context for hidden dependencies, scaling implications,
     performance bottlenecks, security considerations, and integration complexity
3. Fill Implementation Blueprint section
   → Extract context items from spec's Context Engineering section
   → Document known patterns and gotchas
   → Run Context Completeness Gate
   → ULTRATHINK: Evaluate architectural decisions against long-term maintainability,
     system evolution, and potential failure modes
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
   → Run Design Validation Gate after each deliverable
   → If gates fail: Document issues and remediate
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Run Implementation Readiness Gate
   → If fails: ERROR "Prerequisites not met for implementation"
9. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
10. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 10. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
[Extract from feature spec: primary requirement + technical approach from research]

## LOC Budget Tracking

**Targets:**
- Implementation: 400-600 LOC
- Tests: 400-600 LOC (≥1:1 ratio, minimum 0.8:1)
- Total: ~1000 LOC (ideal 1000, acceptable 800-1200)

**Estimated Breakdown:**
| Component | Implementation LOC | Test LOC | Notes |
|-----------|-------------------|----------|-------|
| Models | | | [e.g., User + Profile entities + validation tests] |
| Services | | | [e.g., UserService CRUD + service layer tests] |
| API/CLI | | | [e.g., 4 endpoints × 20 LOC + contract tests] |
| Integration | | | [e.g., E2E test scenarios] |
| **Subtotals** | **0** | **0** | **Total: 0 LOC** |

**Status:** [Calculate totals and test ratio above]
- ✓ **Within ideal range** - Total: X (✓ 800-1200) \| Test ratio: Y:1 (✓ ≥0.8)
- ⚠️ **Review recommended** - Total 700-800 or 1200-1300 \| Test ratio 0.7-0.8 - Consider optimization
- ❌ **Outside range** - Total <700 OR Total >1300 OR Test ratio <0.7 - See justification below OR run `/decompose`

**Justification (if outside ideal range):**
[If Total <800 OR Total >1200 OR Test ratio <0.8:1, document here:
- Why this scope cannot be split further (for >1200) or why it's standalone (for <800)
- What keeps these components tightly coupled
- Why this test ratio is appropriate for the complexity
- Why splitting would harm cohesion or introduce artificial boundaries
- Approval status from tech lead]

## Technical Context
**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Implementation Blueprint *(enhanced from context engineering)*

### Context Integration
**Codebase Files to Reference**:
- List key files from spec's Context Engineering section that contain patterns to follow
- Note specific functions, classes, or patterns to extract

**Library Gotchas** (from ai_docs/library_gotchas.md):
- [Library name]: [Critical gotcha that affects this implementation]
- [Library name]: [Version-specific behavior to watch for]

**Known Implementation Patterns**:
- [Pattern name]: Used in [file/feature] for [similar use case]
- [Pattern name]: Avoid [anti-pattern] seen in [location]

### Pre-Implementation Validation Gates

**Context Completeness Gate**:
- [ ] All Context Engineering items from spec are actionable
- [ ] Required documentation accessible (URLs work, files exist)
- [ ] Library versions confirmed and gotchas documented
- [ ] Similar feature patterns identified and understood

**Design Validation Gate**:
- [ ] Data model aligns with functional requirements
- [ ] API contracts cover all user scenarios
- [ ] Integration points identified and documented
- [ ] Error handling approach defined

**Implementation Readiness Gate**:
- [ ] All external dependencies available and accessible
- [ ] Development environment requirements documented
- [ ] Testing strategy covers contract, integration, and unit levels
- [ ] Performance benchmarks established (if applicable)

## Architecture Decisions

### Architecture Impact Assessment
**Impact Level**: [Level 1: Work Within | Level 2: Extend | Level 3: Refactor]

**From Architecture Context** (Phase -1):
- Current system architecture version: [e.g., v1.2.0 or N/A if first feature]
- Existing constraints: [List technology/deployment constraints from system-architecture.md]

#### Level 1: Work Within Existing Architecture
*Feature uses existing architecture without adding new system-level components*

- Uses existing components: [List - e.g., PostgreSQL, Redis, existing APIs]
- Integrates with existing features: [List features this integrates with]
- No new system components required
- System architecture version: **No change** (stays at current version)

#### Level 2: Extend System Architecture
*Feature adds new components to system but doesn't change core structure*

- Extends existing with: [New components - e.g., S3 for storage, Elasticsearch for search]
- Rationale for extension: [Why existing components insufficient for this feature's requirements]
- Integration approach: [How new component integrates with existing system]
- System architecture version: **Minor bump** (e.g., v1.2.0 → v1.3.0)
- Impact: **Low to Medium** - Additive only, existing features unaffected but can optionally adopt

#### Level 3: Refactor System Architecture (BREAKING CHANGE)
*Feature requires fundamental architectural changes*

**⚠️ CRITICAL: Breaking changes require architecture review and migration plan**

- Breaking changes required: [What core structure/technology is changing]
- Rationale: [Why refactor necessary - what requirement can't be met with current architecture]
- New architecture pattern: [Describe new structure - e.g., monolith → microservices]
- System architecture version: **Major bump** (e.g., v1.x → v2.0.0)
- Impact: **HIGH** - Affects existing features: [List all features requiring migration]
- Migration required: **Yes** - Create migration plan document

### Feature-Specific Architecture

**Components** (new for this feature):
- [Component name]: [Purpose, responsibilities, interfaces]
- [Service class]: [What it does, dependencies]

**Integration Points** (with existing system):
- Integrates with [existing feature/component]: [How and why]
- Uses [existing component from other feature]: [What functionality it leverages]
- Extends [existing API/interface]: [What new endpoints/methods added]

### Technology Choices & Rationale

**For each technology decision, document**:

**Decision**: [Technology/library/pattern chosen]
**Satisfies Requirement**: [Link to specific requirement from spec.md - e.g., NFR-P001]
**Alternatives Considered**: [Other options evaluated]
**Rationale**: [Why this choice over alternatives]
**Alignment**: [How this aligns with or extends system architecture constraints]

**Examples**:
- **PostgreSQL for feature data**: Satisfies NFR-P001 (< 200ms response), aligns with system constraint
- **S3 for file storage**: Satisfies FR-003 (file uploads), extends system architecture (new component)
- **Redis for caching**: Satisfies NFR-P002 (1000 req/s throughput), extends system (new component)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: [#] (max 3 - e.g., api, cli, tests)
- Using framework directly? (no wrapper classes)
- Single data model? (no DTOs unless serialization differs)
- Avoiding patterns? (no Repository/UoW without proven need)

**Architecture**:
- EVERY feature as library? (no direct app code)
- Libraries listed: [name + purpose for each]
- CLI per library: [commands with --help/--version/--format]
- Library docs: llms.txt format planned?

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? (test MUST fail first)
- Git commits show tests before implementation?
- Order: Contract→Integration→E2E→Unit strictly followed?
- Real dependencies used? (actual DBs, not mocks)
- Integration tests for: new libraries, contract changes, shared schemas?
- Test quality: Context-sensitive ratios enforced (see testing-quality-check skill)
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included?
- Frontend logs → backend? (unified stream)
- Error context sufficient?

**Versioning**:
- Version number assigned? (MAJOR.MINOR.BUILD)
- BUILD increments on every change?
- Breaking changes handled? (parallel tests, migration plan)

## Project Structure

### Documentation (this feature)
```
specs/[feature-id]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: [DEFAULT to Option 1 unless Technical Context indicates web/mobile app]

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` **using UTF-8 encoding** and following format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved (UTF-8 encoded)

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md` **using UTF-8 encoding**:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements **using UTF-8 encoding**:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   VARIANT-INJECT
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file (all UTF-8 encoded)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [ ] Phase 0: Research complete (/plan command)
- [ ] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [ ] Context Completeness Gate: PASS
- [ ] Initial Constitution Check: PASS
- [ ] Design Validation Gate: PASS
- [ ] Post-Design Constitution Check: PASS
- [ ] Implementation Readiness Gate: PASS
- [ ] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

## System Architecture Update

**Action Required**: [No Update | Minor Update | Major Update | Create New]

### If This Is First Feature (MVP/Greenfield)
- [ ] CREATE `docs/system-architecture.md` from template
- [ ] Set initial version: v1.0.0
- [ ] Document foundational decisions made in this plan
- [ ] Fill in "Core Architecture Decisions" section
- [ ] Add first evolution entry (v1.0.0)

**Template Path**: `templates/system-architecture-template.md`

### If Extending Existing System (Level 2)
- [ ] UPDATE `docs/system-architecture.md`
- [ ] Add new evolution entry
- [ ] Version bump: [current] → [new] (minor increment, e.g., v1.2.0 → v1.3.0)
- [ ] Document new components added: [List components]
- [ ] Document rationale and impact: Low (additive only)

### If Refactoring Architecture (Level 3 - BREAKING)
- [ ] UPDATE `docs/system-architecture.md`
- [ ] Add breaking change evolution entry
- [ ] Version bump: [current] → [new] (major increment, e.g., v1.x → v2.0.0)
- [ ] Document breaking changes: [What's changing]
- [ ] List affected features: [All features requiring migration]
- [ ] CREATE `docs/migrations/v[new]-migration.md` with migration plan
- [ ] Document impact: HIGH - coordinated migration required

### If Working Within Existing (Level 1)
- [ ] NO UPDATE to system-architecture.md required
- [ ] Version stays: [current version]
- [ ] Note: Feature uses existing architecture without system-level changes

**Post-Update Checklist**:
- [ ] Architecture version incremented correctly (semantic versioning)
- [ ] Evolution entry includes: date, feature ID, changes, rationale, impact
- [ ] If breaking change: migration plan created
- [ ] System architecture constraints updated if new components added

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*