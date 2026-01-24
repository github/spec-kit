---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
semantic_anchors:
  - Clean Architecture    # Dependency rule, use cases, entities, Robert C. Martin
  - Hexagonal Architecture  # Ports and Adapters, domain isolation, Alistair Cockburn
  - ADR                   # Architecture Decision Records - Context, Decision, Consequences
  - C4 Model              # Context → Containers → Components → Code, Simon Brown
  - DRY                   # Don't Repeat Yourself - identify reuse opportunities first
  - arc42                 # Architecture documentation template, 12 sections
handoffs: 
  - label: Create Tasks
    agent: speckit.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Create Checklist
    agent: speckit.checklist
    prompt: Create a checklist for the following domain...
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template (already copied).

3. **Load source idea (CRITICAL)**: Extract the SOURCE IDEA from spec.md header or locate it:
   - Check spec.md for `**Source**:` or `**Parent Idea**:` links
   - If found, load the linked idea.md file
   - If not found, search `ideas/` directory for matching idea by feature name
   - Extract **Technical Hints** section from idea (if present)
   - Extract any technical details from:
     - "Constraints & Assumptions" → technical constraints
     - "Discovery Notes" → technical decisions made during exploration
     - Feature files → "Technical Hints" or "Notes" sections
   - Store these as IDEA_TECHNICAL_CONSTRAINTS for validation in step 6

4. **Load Architecture Registry (CRITICAL for consistency)**:

   > **Apply**: DRY - reuse before creating. ADR for understanding past decisions. Clean/Hexagonal Architecture for layer constraints.

   BEFORE exploring the codebase, load the architecture registry to understand established patterns:

   a. **Check if registry exists**:
      - Look for `/memory/architecture-registry.md`
      - If exists, read and extract:
        * **Established Patterns**: Patterns that MUST be reused
        * **Technology Decisions**: Tech choices that MUST be followed
        * **Component Conventions**: Standard locations and naming
        * **Anti-Patterns**: Approaches to AVOID
        * **Cross-Feature Dependencies**: Shared components to leverage

   b. **Create ARCHITECTURE_CONSTRAINTS list**:
      ```markdown
      ## Architecture Constraints (from registry)

      ### Must Use Patterns
      - [Pattern]: [When to apply] → [File reference]

      ### Must Use Technologies
      - [Category]: [Technology] (not [alternatives])

      ### Component Locations
      - [Type] → [Location] with [Naming]

      ### Must Avoid
      - [Anti-pattern]: [What to do instead]
      ```

   c. **If no registry exists**:
      - Log: "⚠️ No architecture registry found - this is the first feature or registry not initialized"
      - Recommend running `/speckit.extract-patterns` after this feature to initialize registry
      - Proceed without constraints (but document all decisions for later extraction)

   **CRITICAL PRINCIPLE**: New features MUST align with established patterns. Divergence requires explicit justification.

5. **Explore existing codebase (CRITICAL for reuse, guided by registry)**:

   BEFORE designing any new solution, thoroughly explore what already exists in the codebase:

   a. **Identify reusable components**:
      - Search for existing services, utilities, helpers that could fulfill part of the requirements
      - Look for similar patterns in other features (e.g., "how does feature X handle authentication?")
      - Check for shared libraries, base classes, or abstractions that should be extended
      - Identify existing data models that could be reused or extended

   b. **Analyze existing architecture**:
      - Understand the project structure and conventions
      - Identify established patterns (repository pattern, service layer, etc.)
      - Find configuration mechanisms already in place
      - Check for existing error handling, logging, and monitoring patterns

   c. **Search strategies**:
      ```
      For each capability in the spec:
        1. Search for similar functionality: grep/glob for keywords
        2. Check existing services: src/services/, lib/, utils/
        3. Look at related features: how do similar use cases work?
        4. Review shared infrastructure: middleware, decorators, base classes
      ```

   d. **Document findings in research.md** (Existing Codebase section):
      ```markdown
      ## Existing Codebase Analysis

      ### Reusable Components Found

      | Component | Location | Can Reuse For | Needs Refactoring? |
      |-----------|----------|---------------|-------------------|
      | [component] | [path] | [which requirement] | Yes/No - [what] |

      ### Existing Patterns to Follow

      | Pattern | Example Location | Apply To |
      |---------|------------------|----------|
      | [pattern name] | [file path] | [where to apply] |

      ### Potential Conflicts

      | Existing | New Requirement | Resolution |
      |----------|-----------------|------------|
      | [what exists] | [what we need] | [extend/refactor/new] |
      ```

   e. **Reuse decision matrix**:
      - ✅ **REUSE**: Component exists and fits → use directly
      - 🔧 **EXTEND**: Component exists but needs extension → add capabilities
      - ♻️ **REFACTOR**: Component exists but needs redesign → refactor for broader use
      - 🆕 **NEW**: No suitable component exists → create new (document why)

   **CRITICAL PRINCIPLE**: Default to reuse. Only create new implementations when:
   - No existing component serves the purpose
   - Refactoring existing code would be more costly than creating new
   - The new solution would benefit multiple features (justify in research.md)

6. **Validate Architecture Alignment (CRITICAL - prevents drift)**:

   BEFORE proceeding to design, validate that planned approach aligns with ARCHITECTURE_CONSTRAINTS:

   a. **For each capability in the spec**, check against registry:

      ```
      Capability: [what we need to build]

      Registry Check:
      - Established Pattern? → [Yes: use it | No: new pattern needed]
      - Technology Decision? → [Yes: use specified tech | No: make decision and document]
      - Component Convention? → [Yes: follow location/naming | No: establish new convention]
      - Anti-Pattern Risk? → [Yes: avoid this approach | No: proceed]
      ```

   b. **Create Architecture Alignment Report** (in plan.md):

      ```markdown
      ## Architecture Alignment

      ### Patterns Applied
      | Pattern | From Registry | Applied To | Status |
      |---------|---------------|------------|--------|
      | [pattern] | Yes/No | [component] | ✅ Aligned / ⚠️ Divergent |

      ### Technology Alignment
      | Category | Registry Says | Plan Uses | Status |
      |----------|---------------|-----------|--------|
      | [category] | [tech] | [tech] | ✅ / ⚠️ |

      ### New Patterns Introduced
      | Pattern | Justification | Registry Update Needed |
      |---------|---------------|------------------------|
      | [pattern] | [why new] | Yes - add after implementation |

      ### Divergences (REQUIRES JUSTIFICATION)
      | From | To | Reason | Approved |
      |------|----|--------|----------|
      | [established] | [proposed] | [why change] | ⏳ Pending |
      ```

   c. **If divergences detected**:
      - **STOP** and display divergences to user
      - Ask: "Plan diverges from established patterns. Approve divergence? (yes/no/modify)"
      - If "no": Revise plan to align with registry
      - If "yes": Document approval and proceed
      - If "modify": Discuss alternatives with user

   d. **If no registry exists**:
      - Mark all decisions as "New Pattern - to be registered"
      - Proceed with explicit documentation

   **HARD RULE**: Undocumented divergence = architectural drift = rejected plan

7. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (include Existing Codebase Analysis from step 5)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design
   - **Prefer extending existing components over creating new ones**
   - **Ensure Architecture Alignment section is included in plan.md**

8. **Validate alignment with source idea (CRITICAL)**:

   Before finalizing, verify that the plan respects IDEA_TECHNICAL_CONSTRAINTS:

   a. **Extract technical requirements from idea**:
      - Commands or scripts that must be executed
      - Specific tools, libraries, or versions mentioned
      - Execution order or sequencing requirements
      - Technical patterns or approaches specified
      - Integration points with specific instructions

   b. **Cross-check with plan.md**:
      - For each technical constraint in the idea:
        - ✅ ALIGNED: Plan explicitly addresses it
        - ⚠️ DIVERGENT: Plan uses different approach → requires justification
        - ❌ MISSING: Plan doesn't address it → add to plan

   c. **Create alignment report** in plan.md:

      ```markdown
      ## Idea Technical Alignment

      **Source Idea**: [path to idea.md]

      ### Technical Constraints from Idea

      | Constraint | Status | Plan Reference |
      |------------|--------|----------------|
      | [constraint from idea] | ✅/⚠️/❌ | [section in plan] |

      ### Divergences (if any)

      | Idea Specified | Plan Proposes | Justification |
      |----------------|---------------|---------------|
      | [original] | [different approach] | [why change is better] |
      ```

   d. **STOP and report if critical divergences**:
      - If plan contradicts explicit technical instructions from idea
      - Ask user to confirm before proceeding
      - Document the decision in research.md

9. **Stop and report**: Command ends after Phase 2 planning. Report:
   - Branch and IMPL_PLAN path
   - Generated artifacts
   - **Architecture alignment status** (patterns followed, divergences approved)
   - **Alignment status with source idea**
   - **Reuse summary**: Components reused vs. new code created
   - **Registry updates needed**: New patterns to register after implementation

## Phases

### Phase 0: Outline & Research

1. **Include Existing Codebase Analysis** (from step 5):
   - Copy the findings from step 5 into research.md
   - Include Architecture Constraints from step 4
   - This MUST be the first section of research.md
   - All subsequent decisions should reference this analysis and registry constraints

2. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

3. **Generate and dispatch research agents**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   CRITICAL - For each capability:
     Task: "Search codebase for existing implementation of {capability}"
   ```

4. **Consolidate findings** in `research.md` using format:

   ```markdown
   ## Existing Codebase Analysis
   [From step 4 - reusable components, patterns, conflicts]

   ## Technical Decisions

   ### Decision 1: [Topic]
   - **Decision**: [what was chosen]
   - **Existing code considered**: [what was evaluated from codebase]
   - **Reuse approach**: REUSE / EXTEND / REFACTOR / NEW
   - **Rationale**: [why this approach, especially if NEW]
   - **Alternatives considered**: [what else evaluated]
   ```

**Output**: research.md with:
- Existing codebase analysis
- All NEEDS CLARIFICATION resolved
- Reuse decisions justified

### Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete (with Existing Codebase Analysis)

1. **Extract entities from feature spec** → `data-model.md`:
   - **First check**: Do any of these entities already exist in the codebase?
   - If entity exists: Reference it, note if extension needed
   - If entity is new: Define entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable
   - **Mark each entity**: EXISTING / EXTENDED / NEW

2. **Generate API contracts** from functional requirements:
   - **First check**: Do similar endpoints already exist?
   - If similar endpoint exists: Consider extending or reusing patterns
   - For each user action → endpoint
   - Use existing patterns from codebase (discovered in step 5) and registry (step 4)
   - Output OpenAPI/GraphQL schema to `/contracts/`
   - **Mark each endpoint**: EXISTING / MODIFIED / NEW

3. **Agent context update**:
   - Run `{AGENT_SCRIPT}`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: data-model.md, /contracts/*, quickstart.md, agent-specific file

**CRITICAL**: Each artifact should clearly indicate what is reused vs. new

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
- **REGISTRY FIRST**: Load architecture registry before exploring codebase
- **ALIGN OR JUSTIFY**: Follow established patterns or document divergence with approval
- **REUSE FIRST**: Always explore existing code before designing new solutions
- **JUSTIFY NEW CODE**: Every new component must explain why existing code couldn't be used
- **EXTEND > CREATE**: Prefer extending existing components over creating new ones
- **DOCUMENT DECISIONS**: Every reuse/new decision must be documented in research.md
- **FLAG NEW PATTERNS**: Mark new patterns for registry update after implementation
