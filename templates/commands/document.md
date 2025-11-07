---
description: Generate AI-focused documentation for an implemented feature to facilitate AI comprehension and future modifications.
scripts:
  sh: scripts/bash/setup-ai-doc.sh --json "{ARGS}"
  ps: scripts/powershell/setup-ai-doc.ps1 -Json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The `/speckit.document` command generates comprehensive AI-focused documentation for an **already implemented** feature. This documentation helps AI agents (and developers) quickly understand the implementation for future modifications.

### Prerequisites

Before running this command:

1. The feature **must be implemented** (code exists)
2. Feature spec should exist at `.specify/specs/###-feature-name/spec.md`
3. Tests should be written and passing
4. You should be on the feature branch

### Execution Flow

1. **Determine the Feature**:

   a. If the user provided a feature name/number in `{ARGS}`:
      - Use that to locate the feature directory
      - Example: `/speckit.document user-auth` or `/speckit.document 5`

   b. If no arguments provided:
      - Check the current git branch name
      - Extract feature number and name from branch (format: `###-feature-name`)
      - If not on a feature branch: ERROR "Not on a feature branch. Please specify feature name/number."

   c. Verify feature directory exists:
      - Check `.specify/specs/###-feature-name/` exists
      - If not found: ERROR "Feature directory not found. Ensure feature exists."

2. **Run Setup Script**:

   Execute `{SCRIPT}` with the feature identifier:
   - Bash: `{SCRIPT} --json "feature-identifier"`
   - PowerShell: `{SCRIPT} -Json "feature-identifier"`

   **IMPORTANT**:
   - The script creates the `ai-doc.md` file from the template
   - The JSON output contains the `AI_DOC_FILE` path
   - Only run the script once per invocation

3. **Load Required Information**:

   a. Load `templates/ai-doc-template.md` to understand the structure

   b. Read existing documentation:
      - `.specify/specs/###-feature-name/spec.md` - Requirements
      - `.specify/specs/###-feature-name/plan.md` - Architecture plan
      - `.specify/specs/###-feature-name/tasks.md` - Implementation tasks (if exists)

   c. Identify implementation files:
      - Search the codebase for files related to this feature
      - Focus on files mentioned in tasks.md
      - Look for recent commits on the feature branch: `git log --name-only --oneline`
      - Identify test files related to the feature

4. **Analyze the Implementation**:

   **CRITICAL**: This is an **analysis phase**, not a guessing phase. You must:

   a. **Read the actual code**:
      - Read key implementation files identified in step 3
      - Understand how components interact
      - Trace data flow through the system
      - Identify entry points and public interfaces

   b. **Map the architecture**:
      - Create a component diagram based on actual code structure
      - Document actual dependencies (not planned dependencies)
      - Identify integration points with existing code

   c. **Analyze data flow**:
      - Trace how data moves through the implementation
      - Document state management approach
      - Identify data transformations

   d. **Examine tests**:
      - Read test files to understand coverage
      - Document how to run tests
      - Identify test patterns and fixtures used

   e. **Find non-obvious details**:
      - Look for complex logic, edge cases, workarounds
      - Identify performance considerations
      - Document security/privacy implementations

5. **Generate the AI Documentation**:

   Fill in the `AI_DOC_FILE` using the template structure:

   a. **Feature Overview**:
      - Extract purpose from spec.md
      - Summarize key capabilities from implementation
      - Describe actual user impact

   b. **Code Map**:
      - List all implementation files with descriptions
      - Document entry points with file:line references
      - List public APIs/interfaces

   c. **Architecture Snapshot**:
      - Create ASCII diagram of component relationships
      - Document each component's responsibilities
      - Map dependencies based on actual code

   d. **Data Flow**:
      - Document the primary data flow path
      - Describe data transformations
      - Explain state management

   e. **Key Components Deep Dive**:
      - For each major component:
        - Location (file:line)
        - Purpose and responsibilities
        - Key methods/functions
        - Dependencies
        - Usage examples from actual code

   f. **Integration Points**:
      - Document external dependencies (libraries used)
      - Map internal system connections
      - Describe data storage approach
      - List external APIs/services

   g. **Testing Guide**:
      - List test files and coverage
      - Provide commands to run tests
      - Document manual testing steps
      - List test data requirements

   h. **Modification Guide**:
      - Document common modification patterns
      - Explain code patterns used
      - List configuration options

   i. **Implementation Gotchas**:
      - Document non-obvious behaviors
      - Describe edge cases
      - Note performance considerations
      - List security/privacy concerns

   j. **AI Agent Guidance**:
      - Provide pre-modification checklist
      - List invariants that must be preserved
      - Identify safe-to-change areas
      - Document common issues and fixes

6. **Validate Documentation Quality**:

   a. **Completeness Check**:
      - All major sections filled (not just placeholders)
      - All code references include file:line numbers
      - All components documented
      - All integration points mapped

   b. **Accuracy Check**:
      - Code references are correct
      - Component relationships match implementation
      - Data flow matches actual code
      - Test instructions work

   c. **Usefulness Check**:
      - An AI agent could modify the feature using only this doc
      - Non-obvious details are documented
      - Common modifications are explained
      - Debugging guidance is actionable

   d. If validation fails:
      - Re-read relevant code sections
      - Update documentation to fix issues
      - Re-run validation (max 2 iterations)

7. **Report Completion**:

   Provide summary:
   - Feature name and number
   - AI documentation file path
   - Key components documented (count)
   - Integration points identified (count)
   - Test coverage status
   - Any warnings or limitations

## Important Guidelines

### Analysis Requirements

**DO:**
- ✅ Read actual implementation files
- ✅ Trace code execution paths
- ✅ Document what you observe in the code
- ✅ Include specific file:line references
- ✅ Quote actual code when relevant
- ✅ Test commands before documenting them

**DON'T:**
- ❌ Guess at implementation details
- ❌ Copy from plan.md without verifying
- ❌ Skip reading actual code files
- ❌ Document ideal architecture vs actual architecture
- ❌ Leave template placeholders unfilled
- ❌ Provide vague references ("somewhere in src/")

### Code Reference Format

Always use `file:line` format for code references:
- ✅ `src/auth/login.py:45` - The authenticate() function
- ❌ "The authenticate function in the auth module"

### Section Prioritization

If time/context is limited, prioritize:

1. **Critical**: Code Map, Key Components, Integration Points
2. **High**: Architecture Snapshot, Data Flow, Testing Guide
3. **Medium**: Modification Guide, Implementation Gotchas
4. **Nice-to-have**: AI Agent Guidance, Appendix

### When Implementation is Incomplete

If the feature is partially implemented:
- Document what exists, mark missing pieces clearly
- Add note at top: "⚠️ Feature partially implemented"
- List completed vs remaining functionality
- Still provide value by documenting what's there

### Handling Large Features

For features with many files (>10):
- Focus on core components (the 20% that does 80% of work)
- Group related files into logical modules
- Provide "Entry Points" section as navigation guide
- Link to external docs for dependencies

### AI Agent Context

Remember this documentation will be used by:
- Future AI agents modifying the feature
- AI agents debugging issues
- AI agents adding related features
- Developers unfamiliar with the code

Therefore:
- Be explicit, not implicit
- Assume no prior knowledge of the code
- Explain WHY things are done certain ways
- Highlight non-obvious relationships
- Document the "tribal knowledge"

## Quality Standards

The AI documentation must meet these criteria:

1. **Navigable**: An AI agent can find any component quickly
2. **Accurate**: All references and descriptions match actual code
3. **Complete**: All major components and integration points documented
4. **Actionable**: Provides enough detail for modifications
5. **Maintained**: Includes change history structure for updates

## Example Workflow

```bash
# After implementing a feature on branch 5-user-auth

# Option 1: Let command detect feature from current branch
/speckit.document

# Option 2: Specify feature explicitly
/speckit.document user-auth
/speckit.document 5
/speckit.document 5-user-auth
```

The command will:
1. Detect feature is "5-user-auth"
2. Verify implementation exists
3. Read spec.md, plan.md, tasks.md
4. Analyze actual implementation code
5. Generate comprehensive AI documentation
6. Save to `.specify/specs/5-user-auth/ai-doc.md`

## Common Use Cases

**Use Case 1: Post-Implementation Documentation**
- Feature just completed
- Tests passing
- Want to document for future maintenance
- Run: `/speckit.document`

**Use Case 2: Legacy Code Documentation**
- Old feature lacks documentation
- Need to understand for modifications
- Create spec directory if needed
- Run: `/speckit.document feature-name`

**Use Case 3: Onboarding Aid**
- New AI agent needs to understand feature
- Read ai-doc.md for quick comprehension
- Use Code Map to navigate implementation
- Follow Modification Guide for changes

**Use Case 4: Debugging Reference**
- Issue in production feature
- Need to understand implementation quickly
- Check Implementation Gotchas
- Use Debugging Tips section
