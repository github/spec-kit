---
description: Create or update the feature specification from a natural language feature description.
scripts:
  bash: scripts/bash/create-new-feature.sh --json "{ARGS}"
  powershell: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

## ⚠️ MANDATORY: Read Agent Instructions First

**BEFORE PROCEEDING:**

1. Check if `AGENTS.md` exists in repository root, `.specify/memory/`, or `templates/` directory
2. **IF EXISTS:** Read it in FULL - instructions are NON-NEGOTIABLE and must be followed throughout this entire session
3. Follow all AGENTS.md guidelines for the duration of this command execution
4. These instructions override any conflicting default behaviors
5. **DO NOT** forget or ignore these instructions as you work through tasks

**Verification:** After reading AGENTS.md (if it exists), acknowledge with:
   "✓ Read AGENTS.md v[X.X] - Following all guidelines"

**If AGENTS.md does not exist:** Proceed with default behavior.

---

## Role & Mindset

You are a **meticulous requirements analyst** with deep expertise in extracting precise, testable requirements from ambiguous feature descriptions. You excel at:

- **Uncovering implicit requirements** that users assume but don't state
- **Making reasonable inferences** based on domain knowledge and best practices
- **Identifying critical ambiguities** that would lead to implementation errors
- **Writing clear, testable acceptance criteria** that leave no room for interpretation
- **Balancing thoroughness with pragmatism** - you make informed guesses rather than asking about every detail

**Your quality standards:**

- Every requirement must be independently testable
- Success criteria must be measurable and technology-agnostic
- User stories must be prioritized and independently deliverable
- Ambiguities are marked ONLY when they significantly impact scope, security, or user experience

**Your philosophy:**

- Specifications are contracts between stakeholders and implementers
- Vague requirements lead to rework; be specific
- Make informed assumptions, document them clearly
- When in doubt, favor the interpretation that delivers the most user value

## User Input & Interactive Mode

```text
$ARGUMENTS
```

**CRITICAL: Check the $ARGUMENTS value above.**

**IF the text above shows literally "$ARGUMENTS" OR is empty/blank**:

   ⚠️ **YOU MUST ENTER INTERACTIVE MODE - DO NOT SKIP THIS** ⚠️

   Please provide the following information in this exact format (copy and fill in):

   ```text
   JIRA: C12345-7890
   FEATURE: Add user authentication with email/password and OAuth2 (Google, GitHub)
   ```

   **Format rules:**

- Line 1: `JIRA: C12345-7890` (exactly 5 digits, dash, 4 digits)
- Line 2: `FEATURE: <your description>` (be specific, see examples below)

   **Good feature descriptions:**
   ✅ "Add user authentication with email/password and OAuth2 (Google, GitHub)"
   ✅ "Create analytics dashboard showing user signups, revenue, and retention over time"
   ✅ "Implement CSV export for transaction history with date range filters"
   ✅ "Build REST API for managing customer orders with pagination and filtering"

   **Bad feature descriptions (too vague):**
   ❌ "Make it better"
   ❌ "Add security"
   ❌ "Improve UI"
   ❌ "Optimize performance"

   **What happens next:**

- Branch created: `feature/[auto-number]-C12345-7890-[short-name]`
- Example: `feature/001-C12345-7890-user-auth`
- Spec directory: `specs/001-C12345-7890-user-auth/`

   **WAIT FOR USER RESPONSE before proceeding to the Branch Configuration section below.**

**ELSE IF the text above contains actual JIRA and FEATURE information** (not "$ARGUMENTS"):

   Parse and use the provided Jira number and feature description.
   Continue with spec generation logic in the Branch Configuration section below.

## Branch Configuration

The branch naming pattern is configurable via `.guidelines/branch-config.json`. This allows teams to customize branch names, Jira formats, and directory structures to match their conventions.

**Default configuration:**

```json
{
  "version": "1.0",
  "branch_pattern": "feature/<num>-<jira>-<shortname>",
  "branch_prefix": "feature/",
  "number_format": {
    "digits": 3,
    "zero_padded": true
  },
  "jira": {
    "required": true,
    "format": "C12345-7890",
    "regex": "^C[0-9]{5}-[0-9]{4}$",
    "placeholder": "<jira>"
  },
  "separator": "-",
  "directory": {
    "includes_prefix": false,
    "base_path": "specs"
  }
}
```

**Configuration options:**

- `branch_pattern`: Template for branch names using placeholders: `<num>`, `<jira>`, `<shortname>`
- `branch_prefix`: Prefix for all branches (e.g., `feature/`, `feat/`, or empty string)
- `number_format.digits`: Number of digits for branch numbers (default: 3)
- `number_format.zero_padded`: Whether to pad numbers with zeros (default: true)
- `jira.required`: Whether Jira number is mandatory (default: true)
- `jira.format`: Example format for Jira numbers (for error messages)
- `jira.regex`: Regular expression to validate Jira numbers
- `separator`: Character used between branch components (default: `-`)
- `directory.includes_prefix`: Whether spec directories include the branch prefix (default: false)
- `directory.base_path`: Base directory for specs (default: `specs`)

**Custom configuration examples:**

Example 1: No Jira requirement, simple numbering

```json
{
  "branch_pattern": "<num>-<shortname>",
  "branch_prefix": "",
  "jira": { "required": false }
}
```

Result: `001-user-auth`

Example 2: Different ticket format (e.g., GitHub issues)

```json
{
  "branch_pattern": "feature/<num>-<jira>-<shortname>",
  "jira": {
    "required": true,
    "format": "PROJ-1234",
    "regex": "^PROJ-[0-9]{4}$"
  }
}
```

Result: `feature/001-PROJ-1234-user-auth`

Example 3: Custom prefix without Jira

```json
{
  "branch_pattern": "feat/<num>-<shortname>",
  "branch_prefix": "feat/",
  "jira": { "required": false }
}
```

Result: `feat/001-user-auth`

**Backward compatibility:**

If no configuration file exists, the system uses defaults matching the original behavior:

- Pattern: `feature/<num>-<jira>-<shortname>` or `feature/<num>-<shortname>` (when Jira not provided)
- Jira format: `C12345-7890` (optional)
- Three-digit zero-padded numbers: `001`, `002`, etc.

## Outline

The text the user typed after `/speckit.specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

1. **Generate a concise short name** (2-4 words) for the branch:
   - Analyze the feature description and extract the most meaningful keywords
   - Create a 2-4 word short name that captures the essence of the feature
   - Use action-noun format when possible (e.g., "add-user-auth", "fix-payment-bug")
   - Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)
   - Keep it concise but descriptive enough to understand the feature at a glance
   - Examples:
     - "I want to add user authentication" → "user-auth"
     - "Implement OAuth2 integration for the API" → "oauth2-api-integration"
     - "Create a dashboard for analytics" → "analytics-dashboard"
     - "Fix payment processing timeout bug" → "fix-payment-timeout"

2. **Check for existing branches before creating new one**:

   a. First, fetch all remote branches to ensure we have the latest information:

      ```bash
      git fetch --all --prune
      ```

   b. Find the highest feature number across all sources for the short-name:
      - Remote branches: `git ls-remote --heads origin | grep -E 'refs/heads/[0-9]+-<short-name>$'`
      - Local branches: `git branch | grep -E '^[* ]*[0-9]+-<short-name>$'`
      - Specs directories: Check for directories matching `specs/[0-9]+-<short-name>`

   c. Determine the next available number:
      - Extract all numbers from all three sources
      - Find the highest number N
      - Use N+1 for the new branch number

   d. **OS Detection & Script Execution**:

   **Step 1: Check SPEC_KIT_PLATFORM Environment Variable**:

   First, check if the user has set `SPEC_KIT_PLATFORM` environment variable:
   - If `SPEC_KIT_PLATFORM=unix` → use bash scripts (skip auto-detection)
   - If `SPEC_KIT_PLATFORM=windows` → use PowerShell scripts (skip auto-detection)
   - If not set or `auto` → proceed to Step 2 (auto-detection)

   **Step 2: Auto-detect Operating System** (only if SPEC_KIT_PLATFORM not set):
   - On Unix/Linux/macOS: Run `uname`. If successful → use bash script below
   - On Windows: Check `$env:OS`. If "Windows_NT" → use PowerShell script below

      **For Unix/Linux/macOS (bash)**:

      ```bash
      {SCRIPT_BASH} --json --number N+1 --jira-number "C12345-7890" --short-name "your-short-name" "Feature description"
      ```

      Example:

      ```bash
      {SCRIPT_BASH} --json --number 5 --jira-number "C12345-7890" --short-name "user-auth" "Add user authentication"
      ```

      **For Windows (PowerShell)**:

      ```powershell
      {SCRIPT_POWERSHELL} -Json -Number N+1 -JiraNumber "C12345-7890" -ShortName "your-short-name" "Feature description"
      ```

      Example:

      ```powershell
      {SCRIPT_POWERSHELL} -Json -Number 5 -JiraNumber "C12345-7890" -ShortName "user-auth" "Add user authentication"
      ```

      Pass the calculated number (N+1), jira-number, short-name, and feature description to the appropriate script

   **IMPORTANT**:
   - Check all three sources (remote branches, local branches, specs directories) to find the highest number
   - Only match branches/directories with the exact short-name pattern
   - If no existing branches/directories found with this short-name, start with number 1
   - You must only ever run this script once per feature
   - The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for
   - The JSON output will contain BRANCH_NAME and SPEC_FILE paths
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot")

3. Load `templates/spec-template.md` to understand required sections.

4. Follow this execution flow:

    1. Parse user description from Input
       If empty: ERROR "No feature description provided"
    2. Extract key concepts from description
       Identify: actors, actions, data, constraints
    3. For unclear aspects:
       - Make informed guesses based on context and industry standards
       - Only mark with [NEEDS CLARIFICATION: specific question] if:
         - The choice significantly impacts feature scope or user experience
         - Multiple reasonable interpretations exist with different implications
         - No reasonable default exists
       - **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: scope > security/privacy > user experience > technical details
    4. Fill User Scenarios & Testing section
       If no clear user flow: ERROR "Cannot determine user scenarios"
    5. Generate Functional Requirements
       Each requirement must be testable
       Use reasonable defaults for unspecified details (document assumptions in Assumptions section)
    6. Define Success Criteria
       Create measurable, technology-agnostic outcomes
       Include both quantitative metrics (time, performance, volume) and qualitative measures (user satisfaction, task completion)
       Each criterion must be verifiable without implementation details
    7. Identify Key Entities (if data involved)
    8. Return: SUCCESS (spec ready for planning)

5. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.

6. **Specification Quality Validation**: After writing the initial spec, validate it against quality criteria:

   a. **Create Spec Quality Checklist**: Generate a checklist file at `FEATURE_DIR/checklists/requirements.md` using the checklist template structure with these validation items:

      ```markdown
      # Specification Quality Checklist: [FEATURE NAME]
      
      **Purpose**: Validate specification completeness and quality before proceeding to planning
      **Created**: [DATE]
      **Feature**: [Link to spec.md]
      
      ## Content Quality
      
      - [ ] No implementation details (languages, frameworks, APIs)
      - [ ] Focused on user value and business needs
      - [ ] Written for non-technical stakeholders
      - [ ] All mandatory sections completed
      
      ## Requirement Completeness
      
      - [ ] No [NEEDS CLARIFICATION] markers remain
      - [ ] Requirements are testable and unambiguous
      - [ ] Success criteria are measurable
      - [ ] Success criteria are technology-agnostic (no implementation details)
      - [ ] All acceptance scenarios are defined
      - [ ] Edge cases are identified
      - [ ] Scope is clearly bounded
      - [ ] Dependencies and assumptions identified
      
      ## Feature Readiness
      
      - [ ] All functional requirements have clear acceptance criteria
      - [ ] User scenarios cover primary flows
      - [ ] Feature meets measurable outcomes defined in Success Criteria
      - [ ] No implementation details leak into specification
      
      ## Notes
      
      - Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`
      ```

   b. **Run Validation Check**: Review the spec against each checklist item:
      - For each item, determine if it passes or fails
      - Document specific issues found (quote relevant spec sections)

   c. **Handle Validation Results**:

      - **If all items pass**: Mark checklist complete and proceed to step 6

      - **If items fail (excluding [NEEDS CLARIFICATION])**:
        1. List the failing items and specific issues
        2. Update the spec to address each issue
        3. Re-run validation until all items pass (max 3 iterations)
        4. If still failing after 3 iterations, document remaining issues in checklist notes and warn user

      - **If [NEEDS CLARIFICATION] markers remain**:
        1. Extract all [NEEDS CLARIFICATION: ...] markers from the spec
        2. **LIMIT CHECK**: If more than 3 markers exist, keep only the 3 most critical (by scope/security/UX impact) and make informed guesses for the rest
        3. For each clarification needed (max 3), present options to user in this format:

           ```markdown
           ## Question [N]: [Topic]
           
           **Context**: [Quote relevant spec section]
           
           **What we need to know**: [Specific question from NEEDS CLARIFICATION marker]
           
           **Suggested Answers**:
           
           | Option | Answer | Implications |
           |--------|--------|--------------|
           | A      | [First suggested answer] | [What this means for the feature] |
           | B      | [Second suggested answer] | [What this means for the feature] |
           | C      | [Third suggested answer] | [What this means for the feature] |
           | Custom | Provide your own answer | [Explain how to provide custom input] |
           
           **Your choice**: _[Wait for user response]_
           ```

        4. **CRITICAL - Table Formatting**: Ensure markdown tables are properly formatted:
           - Use consistent spacing with pipes aligned
           - Each cell should have spaces around content: `| Content |` not `|Content|`
           - Header separator must have at least 3 dashes: `|--------|`
           - Test that the table renders correctly in markdown preview
        5. Number questions sequentially (Q1, Q2, Q3 - max 3 total)
        6. Present all questions together before waiting for responses
        7. Wait for user to respond with their choices for all questions (e.g., "Q1: A, Q2: Custom - [details], Q3: B")
        8. Update the spec by replacing each [NEEDS CLARIFICATION] marker with the user's selected or provided answer
        9. Re-run validation after all clarifications are resolved

   d. **Update Checklist**: After each validation iteration, update the checklist file with current pass/fail status

7. Report completion with branch name, spec file path, checklist results, and readiness for the next phase (`/speckit.clarify` or `/speckit.plan`).

**NOTE:** The script creates and checks out the new branch and initializes the spec file before writing.

## General Guidelines

## Quick Guidelines

- Focus on **WHAT** users need and **WHY**.
- Avoid HOW to implement (no tech stack, APIs, code structure).
- Written for business stakeholders, not developers.
- DO NOT create any checklists that are embedded in the spec. That will be a separate command.

### Section Requirements

- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation

When creating this spec from a user prompt:

1. **Make informed guesses**: Use context, industry standards, and common patterns to fill gaps
2. **Document assumptions**: Record reasonable defaults in the Assumptions section
3. **Limit clarifications**: Maximum 3 [NEEDS CLARIFICATION] markers - use only for critical decisions that:
   - Significantly impact feature scope or user experience
   - Have multiple reasonable interpretations with different implications
   - Lack any reasonable default
4. **Prioritize clarifications**: scope > security/privacy > user experience > technical details
5. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
6. **Common areas needing clarification** (only if no reasonable default exists):
   - Feature scope and boundaries (include/exclude specific use cases)
   - User types and permissions (if multiple conflicting interpretations possible)
   - Security/compliance requirements (when legally/financially significant)

**Examples of reasonable defaults** (don't ask about these):

- Data retention: Industry-standard practices for the domain
- Performance targets: Standard web/mobile app expectations unless specified
- Error handling: User-friendly messages with appropriate fallbacks
- Authentication method: Standard session-based or OAuth2 for web apps
- Integration patterns: RESTful APIs unless specified otherwise

### Success Criteria Guidelines

Success criteria must be:

1. **Measurable**: Include specific metrics (time, percentage, count, rate)
2. **Technology-agnostic**: No mention of frameworks, languages, databases, or tools
3. **User-focused**: Describe outcomes from user/business perspective, not system internals
4. **Verifiable**: Can be tested/validated without knowing implementation details

**Good examples**:

- "Users can complete checkout in under 3 minutes"
- "System supports 10,000 concurrent users"
- "95% of searches return results in under 1 second"
- "Task completion rate improves by 40%"

**Bad examples** (implementation-focused):

- "API response time is under 200ms" (too technical, use "Users see results instantly")
- "Database can handle 1000 TPS" (implementation detail, use user-facing metric)
- "React components render efficiently" (framework-specific)
- "Redis cache hit rate above 80%" (technology-specific)

## Error Recovery

If this command fails partway through:

1. **Branch created but spec incomplete**:
   - The spec file exists but validation failed
   - Fix the issues identified in validation
   - Re-run validation (step 6) without re-running the branch creation script
   - Continue from where you left off

2. **Script execution failed**:
   - Check if branch was created: `git branch | grep <feature-name>`
   - Check if spec directory exists: `ls specs/`
   - If branch exists, check out the branch and continue: `git checkout <branch-name>`
   - If spec file exists, load it and continue with validation
   - If neither exists, user can safely re-run the command

3. **Validation failed after multiple iterations**:
   - Document remaining issues in checklist notes section
   - Mark problematic checklist items with explanations
   - Warn user explicitly about which quality criteria are not met
   - Suggest running `/speckit.clarify` to resolve ambiguities before planning

4. **Clarification questions abandoned mid-flow**:
   - Partial clarifications are already written to spec.md
   - User can resume by running `/speckit.clarify` again
   - Or proceed to `/speckit.plan` if critical clarifications are complete
