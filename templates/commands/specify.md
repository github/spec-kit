---
description: Create or update the feature specification from a natural language feature description.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Spec Number Option

Users can optionally specify a custom spec number when creating a feature by including it in their command. This is particularly useful for matching issue tracker numbers (GitHub issues, Jira tickets, etc.).

**How to recognize spec number in user input:**

- `--number <number>` or `-SpecNumber <number>` format
- Keywords like "issue #42", "ticket 123", "for issue 1234"
- Direct number references: "spec 42", "number 99"
- **Natural language patterns combining prefix and number:**
  
  **Detection algorithm (use in order):**
  
  1. **First, look for adjacent prefix + number** (most common):
     - Pattern: `[prefix_keyword] [number]` appearing together
     - Examples: "feature 303", "bugfix 666", "hotfix 42", "fix 123"
     - If found: Extract both prefix and number, done.
  
  2. **If not found, scan the entire input more broadly**:
     - Search **anywhere** in the input for prefix keywords:
       - "feature" or "features" → `feature/`
       - "bugfix" or "bug fix" or "fix" → `bugfix/`
       - "hotfix" or "hot fix" → `hotfix/`
       - "chore" → `chore/`
       - "refactor" or "refactoring" → `refactor/`
     - Search **anywhere** in the input for number patterns: "#221", "221", "issue 221", "ticket 221", "spec 221", "number 221"
     - If BOTH prefix keyword AND number found: Combine them
     - If only number found: Extract just the number (auto-prefix from config)
     - If only prefix keyword found: Ignore (not enough information)
  
  3. **Handle conflicts** (if multiple prefix keywords found):
     - Use the keyword that appears closest to the number
     - If equidistant, prefer more specific: "bugfix" > "fix"
     - If still tied, use first occurrence (left to right)
  
  **This handles all these patterns:**
  - "feature 303 add cart" ✓ (adjacent)
  - "This is feature 221" ✓ (adjacent within sentence)
  - "For issue #221, make it a feature" ✓ (separated, closest keyword)
  - "#221 feature" ✓ (separated, number first)
  - "issue #221" ✓ (just number)
  - "Add shopping cart feature 303" ✓ (adjacent but later in sentence)

**Examples of user input with spec number:**

- "Add user authentication --number 42" (explicit parameter)
- "Fix login timeout for issue #123" (extract `123` only)
- "Implement payment API as spec 1234" (extract `1234` only)
- "Add search feature --number 99 --branch-prefix feature/" (explicit parameters)
- "feature 303 add shopping cart" (extract `feature/` and `303` - adjacent pattern)
- "bugfix 666 fix payment timeout" (extract `bugfix/` and `666` - adjacent pattern)
- "This is feature 221" (extract `feature/` and `221` - adjacent pattern in sentence)
- "For issue #221, make it a feature" (extract `feature/` and `221` - separated, keyword closest to number)
- "Add hotfix 42 for critical bug" (extract `hotfix/` and `42` - adjacent pattern)
- "#999 chore cleanup old files" (extract `chore/` and `999` - number first, then keyword)

**If spec number is specified:**

1. **Scan and extract** using the detection algorithm above:
   - Look for adjacent patterns first (e.g., "feature 303")
   - If not found, scan entire input for separated keywords and numbers
   - Extract both prefix type and number if found together
   
2. **Process extracted values:**
   - Normalize "fix" to "bugfix/" for consistency
   - Normalize "bug fix" to "bugfix/" for consistency  
   - Normalize "hot fix" to "hotfix/" for consistency
   - Add trailing slash to create proper prefix (e.g., "feature" → "feature/")
   - Validate the number is a positive integer
   
3. **Clean the feature description:**
   - Remove the spec number from the description (e.g., "221" or "#221" or "issue 221")
   - Remove the prefix keyword if it was used as a branch type indicator (e.g., remove "feature" from "This is feature 221" to get "This is")
   - Clean up any resulting double spaces or hanging prepositions
   
4. **Pass to script:**
   - Bash: `--number 42` and optionally `--branch-prefix "feature/"`
   - PowerShell: `-SpecNumber 42` and optionally `-BranchPrefix "feature/"`

**If no spec number is specified:** The script will auto-increment from the highest existing spec number (default behavior).

**Priority order:**
1. `--number` CLI parameter (highest priority)
2. `SPECIFY_SPEC_NUMBER` environment variable
3. Auto-increment (default)

**Recognized prefix types for natural language patterns:**
- `feature` or `features` → `feature/`
- `bugfix` or `bug fix` → `bugfix/`
- `fix` → `bugfix/` (normalized, lower priority if "bugfix" also present)
- `hotfix` or `hot fix` → `hotfix/`
- `chore` → `chore/`
- `refactor` or `refactoring` → `refactor/`

**Key principle:** Scan the ENTIRE user input for these keywords and numbers. They don't need to be adjacent or in any particular order. The algorithm will find them wherever they appear.

## Branch Prefix Option

Users can optionally specify a branch prefix when creating a feature by including it in their command. Look for these patterns in the user input:

- `--branch-prefix <prefix>` or `-BranchPrefix <prefix>` format
- Keywords like "use prefix", "with prefix", "as a feature branch", "as a bugfix", etc.
- **Natural language patterns** (also extracts spec number if present):
  - Scan the entire input for prefix keywords: "feature", "bugfix", "hotfix", "chore", "refactor"
  - These keywords can appear anywhere in the sentence, not just adjacent to a number
  - Examples:
    - "feature 303" → prefix `feature/` and number `303` (adjacent)
    - "This is feature 221" → prefix `feature/` and number `221` (adjacent in sentence)
    - "bugfix 666 fix timeout" → prefix `bugfix/` and number `666` (adjacent)
    - "For issue #42, make it a hotfix" → prefix `hotfix/` and number `42` (separated)
    - "#999 chore task" → prefix `chore/` and number `999` (number first)

  **Key:** The reference to prefix and number may come anywhere in the prompt - scan the entire input.

**Common prefix patterns:**

- `feature/` - For feature branches
- `bugfix/` or `fix/` - For bug fixes
- `hotfix/` - For urgent production fixes
- `refactor/` - For refactoring work
- `chore/` - For maintenance tasks

**Examples of user input with branch prefix:**

- "Add user authentication --branch-prefix feature/" (explicit parameter)
- "Fix login timeout as a bugfix" (infer `bugfix/` prefix from keyword)
- "Update payment API with prefix hotfix/" (explicit mention of prefix)
- "feature 303 implement shopping cart" (extract `feature/` and `303` - adjacent)
- "This is feature 221 for auth" (extract `feature/` and `221` - adjacent in sentence)
- "bugfix 666 resolve payment issue" (extract `bugfix/` and `666` - adjacent)
- "For issue #42, create hotfix branch" (extract `hotfix/` and `42` - separated)
- "Make #100 a chore task" (extract `chore/` and `100` - separated)

**If branch prefix is specified:**

1. Extract the prefix from the user input
2. **If using natural language pattern** (e.g., "feature 303"):
   - The spec number will also be extracted (see "Spec Number Option" above)
   - Both prefix and number are removed from the feature description before processing
3. Remove the prefix specification from the feature description before processing
4. Pass the prefix to the script using the appropriate parameter:
   - Bash: `--branch-prefix "prefix-value"`
   - PowerShell: `-BranchPrefix "prefix-value"`

**If no prefix is specified:** The script will use the default from configuration (`.specify/config.json`) or environment variable.

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
   
   d. Run the script `{SCRIPT}` with the calculated number and short-name:
      - Pass `--number N+1` and `--short-name "your-short-name"` along with the feature description
      - Bash example: `{SCRIPT} --json --number 5 --short-name "user-auth" "Add user authentication"`
      - PowerShell example: `{SCRIPT} -Json -Number 5 -ShortName "user-auth" "Add user authentication"`   

   **IMPORTANT**:

   - Check all three sources (remote branches, local branches, specs directories) to find the highest number
   - Only match branches/directories with the exact short-name pattern
   - If no existing branches/directories found with this short-name, start with number 1
   - Append the short-name argument to the `{SCRIPT}` command with the 2-4 word short name you created in step 1. Keep the feature description as the final argument.
   - If a spec number was specified (see "Spec Number Option" above), include it as a parameter
   - If a branch prefix was specified (see "Branch Prefix Option" above), include it as a parameter
   - **Note:** Natural language patterns like "feature 303" or "bugfix 666" provide BOTH prefix and number - extract and pass both parameters
   - Bash examples: 
     - `--short-name "your-generated-short-name" "Feature description here"`
     - `--short-name "user-auth" "Add user authentication"`
     - `--number 42 --short-name "payment-api" "Add payment processing"`
     - `--number 1234 --short-name "user-auth" --branch-prefix "feature/" "Add user authentication"`
     - `--number 303 --branch-prefix "feature/" --short-name "shopping-cart" "Add shopping cart"` (from "feature 303 add shopping cart")
     - `--number 666 --branch-prefix "bugfix/" --short-name "payment-timeout" "Fix payment timeout"` (from "bugfix 666 fix payment timeout")
   - PowerShell examples:
     - `-ShortName "your-generated-short-name" "Feature description here"`
     - `-ShortName "user-auth" "Add user authentication"`
     - `-SpecNumber 42 -ShortName "payment-api" "Add payment processing"`
     - `-SpecNumber 1234 -ShortName "user-auth" -BranchPrefix "feature/" "Add user authentication"`
     - `-SpecNumber 303 -BranchPrefix "feature/" -ShortName "shopping-cart" "Add shopping cart"` (from "feature 303 add shopping cart")
     - `-SpecNumber 666 -BranchPrefix "bugfix/" -ShortName "payment-timeout" "Fix payment timeout"` (from "bugfix 666 fix payment timeout")
   - The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for
   - The JSON output will contain BRANCH_NAME and SPEC_FILE paths
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot")
   - You must only ever run this script once per feature

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
