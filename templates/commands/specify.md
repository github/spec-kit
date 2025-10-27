---
description: Create or update the feature specification from a natural language feature description.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

Given the feature description provided as an argument, do this:

## Mode Detection & Adaptive Workflow

**Before creating specification, determine appropriate depth level:**

### Quick Assessment Questions

Ask the user to clarify (if not obvious from description):

1. **Is this a new feature from scratch or modifying existing code?**
   - New feature → Continue to complexity assessment
   - Modification → Consider lightweight or quick mode

2. **Estimated total LOC (implementation + tests)?**
   - <200 LOC → **QUICK mode** (minimal spec, proposal + tasks only)
   - 200-800 LOC → **LIGHTWEIGHT mode** (compact spec, essential plan + tasks)
   - 800-1000 LOC → **FULL mode** (comprehensive spec, detailed plan - current default)
   - >1000 LOC → **FULL mode** + recommend `/decompose` after spec complete

### Mode Behaviors

**QUICK Mode (<200 LOC total):**
- Skip: research phase, product-vision check, system-architecture check
- Use: `templates/spec-template-quick.md`
- Generate: Minimal spec (purpose, requirements, acceptance criteria only)
- Use case: Bug fixes, small tweaks, config changes
- Next step: `/tasks` directly (no `/plan` needed)

**LIGHTWEIGHT Mode (200-800 LOC total):**
- Skip: research phase (codebase + external)
- Simplify: product-vision and system-architecture checks (reference only, don't analyze deeply)
- Use: `templates/spec-template-lightweight.md`
- Generate: Compact spec (essential sections, less detail)
- Use case: Simple features, brownfield modifications
- Next step: `/plan` with `templates/plan-template-lightweight.md`

**FULL Mode (800+ LOC total - DEFAULT):**
- Include: All research phases, comprehensive context gathering
- Use: `templates/spec-template.md` (current comprehensive template)
- Generate: Complete spec with context engineering, research, full detail
- Use case: Complex features, greenfield development
- Next step: `/plan` with full `templates/plan-template.md`

### Mode Selection Logic

**User can explicitly specify mode:**
```bash
/specify "description" --mode quick
/specify "description" --mode lightweight
/specify "description" --mode full
```

**If no mode specified, AI determines from description:**
- Keywords like "fix", "bug", "tweak", "adjust" → Suggest quick
- Keywords like "add feature", "modify", "enhance" → Suggest lightweight
- Keywords like "build", "create system", "implement" → Use full
- When uncertain → Ask user clarifying questions above

**Override safety:** If estimated LOC significantly differs from selected mode, warn user and suggest mode change.

## Enhanced Specification Process

### Phase 0: Context Loading
**Before research, check for existing product and architecture context:**

**Product Context Check**:
1. Check if `docs/product-vision.md` exists in the repository
   → If exists: Read and extract the following
     - Target personas (use these to inform feature user stories)
     - Product-wide non-functional requirements (inherit into this feature)
     - Success metrics (align this feature with product goals)
     - Market context (skip market research if already done at product level)
   → If missing: Proceed without product context (standalone feature or no product vision created)

**System Architecture Check**:
2. Check if `docs/system-architecture.md` exists in the repository
   → If exists: Read and extract the following
     - Technology stack constraints (PostgreSQL, Node.js, etc. - note what MUST be used)
     - Integration requirements (existing APIs, auth systems - note what MUST integrate with)
     - Architecture version (understand current system state)
     - Architectural patterns (monolith vs microservices, deployment model)
   → If missing: No architectural constraints (likely first feature/MVP - this /specify will inform first /plan)

**Context Summary**:
- Document what context was found and will be used
- If product vision exists: Note that market research can be skipped
- If system architecture exists: Note constraints that will appear in Technical Constraints section

### Phase 1: Research & Context Gathering
**After loading existing context, conduct additional research:**

**ULTRATHINK**: Before proceeding with research, deeply analyze the feature description to identify:
- Hidden complexity that isn't immediately apparent
- Potential architectural implications and system-wide impacts
- Critical assumptions that need validation
- Similar features that failed or succeeded and why
- Long-term maintenance and evolution considerations
- User experience implications beyond the obvious requirements

1. **Codebase Research**:
   - Search for similar features in the codebase using patterns from the feature description
   - Identify existing libraries, services, or components that might be relevant
   - Document patterns that could be reused or should be avoided
   - Note any architectural constraints or opportunities

2. **External Research** (use Task tool to spawn research agents):
   - **If product vision does NOT exist**: Research market, competitors, user needs
   - **If product vision exists**: Skip market research, extract context from product-vision.md
   - Research best practices for the type of feature being specified
   - Find authoritative documentation and implementation examples
   - Identify common pitfalls and gotchas for this feature type
   - Look for performance and security considerations
   - Save critical findings to ai_docs/ if they'll be referenced frequently

3. **Context Engineering Preparation**:
   - Identify what documentation will be needed for implementation
   - Note which files contain patterns that should be followed
   - List library-specific gotchas from ai_docs/library_gotchas.md
   - Prepare YAML references for the Context Engineering section

### Phase 2: Specification Creation

4. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and SPEC_FILE. All file paths must be absolute.

**Workspace Mode & Jira Keys**:
- In workspace mode, target repository is determined by convention-based routing
- Some repos require Jira keys based on their GitHub host (e.g., `github.marqeta.com`)
- Script will prompt for Jira key if needed: `"Target repo 'X' requires JIRA key"`
- Convention matching strips Jira keys: `proj-123.backend-api` → matches `backend-` rule
- Full spec ID (with Jira key) is preserved for directories and branches
- If Jira key is provided or prompted, the SPEC_FILE path will include it

**Examples**:
```bash
# Without Jira key (allowed for github.com repos)
/specify backend-api
# → SPEC_FILE: specs/backend-api/spec.md
# → BRANCH_NAME: username/backend-api

# With Jira key (required for github.marqeta.com repos)
/specify proj-123.backend-api
# → SPEC_FILE: specs/proj-123.backend-api/spec.md
# → BRANCH_NAME: username/proj-123.backend-api
# → Routes to backend repo (matches "backend-" after stripping Jira key)

# Workspace mode with prompt (if Jira key forgot to provide)
/specify backend-api
# → Prompts: "Enter JIRA issue key (e.g., proj-123): "
# → User enters: proj-456
# → SPEC_FILE: specs/proj-456.backend-api/spec.md
# → BRANCH_NAME: username/proj-456.backend-api
```

5. Load `templates/spec-template.md` to understand required sections, paying special attention to the enhanced Context Engineering section.

6. Write the specification to SPEC_FILE **using UTF-8 encoding** and following the template structure, ensuring:
   - **Context Engineering section is thoroughly populated** with research findings
   - All [NEEDS CLARIFICATION] markers are used appropriately for genuine unknowns
   - Similar features and patterns from codebase research are referenced
   - External research findings are integrated into relevant sections
   - YAML documentation references are complete and actionable

7. **Quality Assurance**:
   - Run Context Completeness Check: "If someone knew nothing about this codebase, would they have everything needed to implement this successfully?"
   - Ensure research phase findings are properly integrated
   - Verify no implementation details leaked into the specification
   - Confirm all user scenarios are testable and unambiguous

8. Report completion with branch name, spec file path, research summary, and readiness for the next phase.

## Next Steps After Specification

**Option 1: Direct Implementation (Simple Features)**
- If feature is naturally small (estimated <1000 LOC total):
  - Proceed directly to `/plan` for implementation
  - Target: 400-800 LOC total (200-400 impl + 200-400 tests)
  - Skip decomposition step

**Option 2: Capability Decomposition (Complex Features)**
- If feature is large or complex (estimated >1200 LOC total):
  - Run `/decompose` to break into atomic capabilities
  - Each capability: ~1000 LOC total (400-600 impl + 400-600 tests, 800-1200 acceptable)
  - Then run `/plan --capability cap-001` for each capability

**Decision Criteria:**
- **Use `/decompose` if:**
  - Feature has >5 functional requirements
  - Multiple entities or bounded contexts
  - Estimated >1000 LOC total (implementation + tests)
  - Multiple developers working in parallel
  - Want atomic PRs (400-800 LOC ideal)

- **Skip `/decompose` if:**
  - Simple CRUD or single entity
  - <5 functional requirements
  - Estimated <1000 LOC total (implementation + tests)
  - Single developer working sequentially

## Research Integration Guidelines

**Context Engineering Population**:
- Every URL reference should include specific section anchors when possible
- File references should note exact patterns, functions, or classes to follow
- Gotchas should be specific and actionable, not generic warnings
- Similar features should explain what to reuse vs. what to improve upon

**Research Documentation**:
- If research reveals library-specific patterns worth preserving, consider adding to ai_docs/
- Document any new gotchas discovered during research in appropriate ai_docs/ files
- Note architectural decisions that might impact future features

**Quality Gates**:
- Research phase should identify at least 2-3 similar patterns in existing codebase
- External research should find at least 1-2 authoritative sources
- Context Engineering section should pass the "No Prior Knowledge" test
- No [NEEDS CLARIFICATION] markers should remain for items that could be researched

Note: The script creates and checks out the new branch and initializes the spec file before writing. The enhanced research process ensures specifications are informed by both internal patterns and external best practices.
