---
description: Create or update the feature specification from a natural language feature description or existing idea document.
semantic_anchors:
  - EARS Syntax           # Requirements patterns: Ubiquitous, Event-driven, State-driven
  - INVEST Criteria       # Story quality: Independent, Negotiable, Valuable, Estimable, Small, Testable
  - Specification by Example  # Concrete examples as specs, Gojko Adzic
  - Jobs-to-Be-Done       # Outcome-focused: situation → motivation → outcome
  - BDD Gherkin           # Given-When-Then acceptance scenarios
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
  - label: Explore Idea First
    agent: speckit.idea
    prompt: Let me explore this idea before creating a formal specification
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/speckit.specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

### Step 0: Detect Input Type and Load Context

The input can be one of:
- A feature description (plain text)
- A feature file path (`features/01-feature-name.md`)
- A feature number (`01`, `1`, `feature 1`)
- An idea.md path

#### 0.1 Parse Input Type

```
IF input matches "features/##-*.md" OR "##" OR "feature ##":
    → Feature file mode (load specific feature)
ELSE IF input matches "idea.md" or path contains "idea.md":
    → Idea mode (load idea for simple spec)
ELSE:
    → Description mode (plain text feature description)
```

#### 0.2 Load Context Based on Mode

**Feature File Mode** (decomposed idea):

1. Locate the feature file:
   - If path provided: use directly
   - If number provided: find `specs/*/features/##-*.md`

2. Load the feature file as PRIMARY source:
   - Summary → Feature description
   - Use Cases → User scenarios
   - Scope → Requirements boundaries
   - Dependencies → Technical constraints

3. Load the PARENT idea.md for CONTEXT:
   - Vision → Overall project context
   - Target Users → Personas (cross-reference with feature)
   - Goals → Success metrics context
   - Features Overview → Understand where this feature fits
   - **Constraints & Assumptions** → Technical constraints to preserve
   - **Discovery Notes** → Technical decisions made during exploration

4. **Extract Technical Hints (CRITICAL for downstream alignment)**:
   - From idea.md "Constraints & Assumptions" section → extract technical constraints
   - From idea.md "Discovery Notes" section → extract technical decisions/commands
   - From feature file "Technical Hints" or "Notes" sections → extract implementation guidance
   - These hints will be preserved in the spec for the /plan command to use

5. Add source links in spec header:
   ```markdown
   **Source**: [Feature ##](./features/##-feature-name.md)
   **Parent Idea**: [idea.md](./idea.md)
   ```

**Idea Mode** (simple idea, no decomposition):

1. Load `idea.md` as the primary source
2. Use Vision, Problem Statement, Target Users, Goals, Scope, and Use Cases
3. Cross-reference Discovery Notes for clarifications
4. **Extract Technical Hints** from Constraints & Assumptions and Discovery Notes
5. Add source link: `**Source**: [idea.md](./idea.md)`

**Description Mode** (no idea document):

1. Use the plain text as the feature description
2. Check if an idea.md exists in the target directory:
   - If found, load it for additional context
   - Suggest `/speckit.idea` first if description is very vague (< 20 words)

#### 0.3 Load Existing Documentation for Consistency (CRITICAL)

Before creating the specification, load existing project documentation to ensure consistency:

1. **Check if `/docs` directory exists**:
   - If `/docs/README.md` exists → project has consolidated documentation
   - Scan `/docs/*/spec.md` to list existing domains

2. **Identify relevant domain(s)**:
   - Infer domain from feature description (auth, payments, dashboard, etc.)
   - Load `/docs/{domain}/spec.md` if domain exists
   - If new domain → note for later creation during merge

3. **Load domain context** from `/docs/{domain}/spec.md`:
   - Extract existing features in this domain
   - Identify entities already defined
   - Understand business rules established
   - Extract API patterns used

4. **Create DOCUMENTATION_CONTEXT**:
   ```markdown
   ## Existing Documentation Context

   ### Target Domain
   - **Domain**: {domain}
   - **Existing**: Yes/No
   - **Related Features**: [list from domain spec]

   ### Existing Entities (from domain)
   | Entity | Description | Reuse Opportunity |
   |--------|-------------|-------------------|
   | [entity] | [what it is] | [extend/reuse as-is] |

   ### Domain Business Rules
   - [rule]: [description from domain spec]

   ### Domain Terminology
   - [term]: [definition from domain spec]
   ```

5. **Use DOCUMENTATION_CONTEXT during specification**:
   - Reuse existing entity names and definitions from domain
   - Follow domain's established patterns
   - Reference related features within same domain
   - Ensure terminology consistency with domain spec

#### 0.4 Feature File Status Update

After successfully creating a specification from a feature file:

1. Update the feature file's status:
   ```markdown
   **Status**: Specified
   ```

2. Update the Specification Status section:
   ```markdown
   | Field | Value |
   |-------|-------|
   | Specified | Yes |
   | Spec File | [spec.md](../spec.md) or [##-spec.md](../##-spec.md) |
   | Plan File | - |
   | Tasks File | - |
   | Implementation | Not Started |
   ```

3. Update the parent idea.md Features Overview table:
   ```markdown
   | 01 | [feature-name] | ... | 📝 Specified |
   ```

Given that feature description (or idea document), do this:

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
   - You must only ever run this script once per feature
   - The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for
   - The JSON output will contain BRANCH_NAME and SPEC_FILE paths
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot")

3. Load `templates/spec-template.md` to understand required sections.

4. Follow this execution flow:

    1. Parse user description from Input
       If empty: ERROR "No feature description provided"
    2. Extract key concepts using Jobs-to-Be-Done lens
       Identify: actors (who), actions (what), outcomes (why), constraints (boundaries)
    3. For unclear aspects (apply Convention over Configuration):
       - Make informed guesses using industry conventions
       - Only mark with [NEEDS CLARIFICATION: specific question] if:
         - Significantly impacts scope (INVEST violation)
         - Multiple valid interpretations exist
         - No reasonable convention applies
       - **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
       - Prioritize: scope > security > UX > technical
    4. Fill User Scenarios using BDD Gherkin (Given-When-Then)
       If no clear user flow: ERROR "Cannot determine user scenarios"
    5. Generate Functional Requirements using EARS Syntax patterns
       Each requirement must pass INVEST "Testable" criterion
       Apply Convention over Configuration for unspecified details
    6. Define Success Criteria (SMART-style)
       Measurable, technology-agnostic outcomes
       Quantitative (time, performance) + qualitative (satisfaction, completion)
       Verifiable via Specification by Example
    7. Identify Key Entities (if data involved)
    8. **Include Technical Hints section** (if extracted from idea):
       - Add a "Technical Hints" section at the end of the spec
       - Include commands, tools, libraries, or approaches specified in the idea
       - Preserve execution order requirements
       - Mark as "For implementation planning - not part of functional spec"
    9. Return: SUCCESS (spec ready for planning)

5. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.

   **IMPORTANT**: If Technical Hints were extracted from the idea (step 4 above), add this section at the end of the spec:

   ```markdown
   ---

   ## Technical Hints (For Planning)

   > **Note**: This section preserves technical guidance from the source idea.
   > It is NOT part of the functional specification but MUST be considered during `/speckit.plan`.

   ### Source

   - **Idea**: [path to idea.md]
   - **Feature**: [path to feature file, if applicable]

   ### Technical Constraints

   [List technical constraints from idea's Constraints & Assumptions section]

   ### Implementation Guidance

   [List any commands, tools, libraries, or step-by-step procedures from idea]
   - Command/Step 1: [description]
   - Command/Step 2: [description]
   - Execution order: [specify if order matters]

   ### Discovery Decisions

   [Key technical decisions from idea's Discovery Notes]
   ```

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

> **Activated Frameworks**: Apply EARS Syntax for unambiguous requirements. Validate stories with INVEST criteria. Use Specification by Example for acceptance criteria. Frame needs as Jobs-to-Be-Done.

## Quick Guidelines

- Focus on **WHAT** users need and **WHY** (Jobs-to-Be-Done: "When [situation], I want [action], so I can [outcome]")
- Avoid HOW to implement (no tech stack, APIs, code structure)
- Written for business stakeholders, not developers
- Requirements MUST pass INVEST: Independent, Negotiable, Valuable, Estimable, Small, Testable
- DO NOT create any checklists that are embedded in the spec. That will be a separate command

### Section Requirements

- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation

> **Apply**: Convention over Configuration (sensible defaults), Principle of Least Astonishment (predictable behavior), YAGNI (no speculative features)

When creating this spec from a user prompt:

1. **Make informed guesses**: Apply Convention over Configuration - use industry standards and common patterns
2. **Document assumptions**: Record defaults in Assumptions section (Principle of Least Astonishment)
3. **Limit clarifications**: Maximum 3 [NEEDS CLARIFICATION] markers - only for decisions that:
   - Significantly impact scope (violates INVEST "Small" or "Independent")
   - Have multiple valid interpretations (fails "Testable" criteria)
   - Lack any reasonable default (no Convention applies)
4. **Prioritize clarifications**: scope > security/privacy > UX > technical details
5. **INVEST validation**: Every requirement must be Testable - if not, it's underspecified
6. **Common clarification areas** (only if no Convention applies):
   - Feature scope boundaries (affects INVEST "Independent")
   - User permissions (security-critical)
   - Compliance requirements (legal/financial)

**Examples of reasonable defaults** (don't ask about these):

- Data retention: Industry-standard practices for the domain
- Performance targets: Standard web/mobile app expectations unless specified
- Error handling: User-friendly messages with appropriate fallbacks
- Authentication method: Standard session-based or OAuth2 for web apps
- Integration patterns: RESTful APIs unless specified otherwise

### Success Criteria Guidelines

> **Apply**: SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound) adapted for features

Success criteria must be:

1. **Measurable**: Specific metrics (time, percentage, count, rate) - SMART "Measurable"
2. **Technology-agnostic**: No frameworks, languages, databases - focus on outcomes
3. **User-focused**: Describe from user/business perspective - Jobs-to-Be-Done outcomes
4. **Verifiable**: Testable via Specification by Example without implementation details

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
