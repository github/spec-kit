---
description: Create or update the feature specification from a natural language feature description.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

Given the feature description provided as an argument, do this:

## Enhanced Specification Process

### Phase 1: Research & Context Gathering
**Before creating the specification, conduct systematic research to ensure comprehensive context:**

1. **Codebase Research**:
   - Search for similar features in the codebase using patterns from the feature description
   - Identify existing libraries, services, or components that might be relevant
   - Document patterns that could be reused or should be avoided
   - Note any architectural constraints or opportunities

2. **External Research** (use Task tool to spawn research agents):
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

6. Write the specification to SPEC_FILE using the template structure, ensuring:
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
