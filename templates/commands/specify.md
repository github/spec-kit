---
description: Create or update the feature specification from a natural language feature description.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

Given the feature description provided as an argument, do this:

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
