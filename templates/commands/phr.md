---
description: Manually create a Prompt History Record (PHR) with custom metadata. Note - PHRs are normally created automatically via constitution rules.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

# PHR Command: Manual Exchange Recording

## About PHRs (Automatic vs Manual)

**IMPORTANT:** PHRs are normally created **automatically** via constitution rules after every Spec Kit command. This `/phr` command is for **manual control** in special cases.

### Automatic Mode (Default - via Constitution)

- ✅ Happens automatically after all Spec Kit commands
- ✅ Stage auto-detected from command context
- ✅ Metadata extracted automatically
- ✅ No user action required
- ✅ Silent, non-intrusive

### Manual Mode (This Command)

Use `/phr` manually when you need to:

- 📝 Capture a conversation that wasn't a standard command
- 🎯 Override auto-detected stage or title
- 🔧 Add custom metadata that auto-detection missed
- 📚 Retrospectively document an important exchange
- ✏️ Create PHR with specific labels or links

**This command does TWO things sequentially:**

1. **EXECUTE** the user's actual request (do the work)
2. **RECORD** the entire exchange as a PHR with custom metadata

## Execution Flow

### 1. Execute the User's Request

- Perform whatever the user asked for (code, analysis, planning, debugging, etc.)
- Provide the complete response/solution
- Finish the actual work requested
- **Do not mention PHR creation during execution** - just do the work naturally

### 2. Classify the Exchange

Determine the appropriate **stage** based on the work performed:

**Pre-feature stages** (when specs/ doesn't exist OR working on constitution/spec):

- `constitution`: Defining quality standards, project principles, or constitution.md
- `spec`: Creating feature specifications or business requirements
- `general`: General queries, setup, documentation, or unclassified work

**Feature-specific stages** (when working inside a feature in specs/):

- `architect`: Planning, design, system architecture, API contracts
- `red`: Debugging, fixing errors, troubleshooting, test failures
- `green`: Implementation, new features, passing tests
- `refactor`: Code cleanup, optimization, restructuring
- `explainer`: Code explanations, documentation, tutorials
- `misc`: Other feature-related work that doesn't fit above categories

### 3. Extract Exchange Metadata

Gather the following information from the completed work:

- **Title**: 3-7 word summary of what was accomplished
- **Stage**: One of the stages listed above (required)
- **Prompt**: The user's original request (from $ARGUMENTS or conversation)
- **Response**: Brief summary of what you provided (1-2 sentences)
- **Files**: List of files mentioned, created, or modified (comma-separated paths)
- **Tests**: List of tests mentioned or run (comma-separated test names)
- **Labels**: Relevant topic tags (comma-separated, e.g., "auth,security,api")

### 4. Create PHR File

Call `scripts/bash/create-phr.sh` to create the PHR file with template:

```bash
scripts/bash/create-phr.sh \
  --title "<concise 3-7 word title>" \
  --stage <stage> \
  --json
```

**Notes:**

- Script creates file from template with {{PLACEHOLDERS}}
- Feature auto-detected from current branch or latest numbered feature
- Location: `docs/prompts/` (pre-feature) or `specs/<feature>/prompts/` (feature work)
- Filename: `<id>-<title-slug>.<stage>.prompt.md`
- Returns JSON with `id`, `path`, `context`, `stage`, `feature`, `template`

### 5. Fill Template Placeholders

Read the created file and replace ALL {{PLACEHOLDERS}} with actual values:

**Metadata section (YAML frontmatter):**

- `{{ID}}`: Use ID from script output (e.g., "0001")
- `{{TITLE}}`: Brief title of what was accomplished
- `{{STAGE}}`: Stage from step 2
- `{{DATE_ISO}}`: Today's date (YYYY-MM-DD)
- `{{SURFACE}}`: "agent" (for AI agent)
- `{{MODEL}}`: Model name (e.g., "gpt-4", "claude-3-opus") or "unspecified"
- `{{FEATURE}}`: Feature name from script output, or context (pre-feature/feature)
- `{{BRANCH}}`: Current git branch
- `{{USER}}`: User's name or "unknown"
- `{{COMMAND}}`: Command used (e.g., "/constitution", "/plan") or "manual"
- `{{LABELS}}`: Comma-separated labels (e.g., "auth", "security", "api")
- `{{LINKS_SPEC}}`: Link to spec file if relevant, or "null"
- `{{LINKS_TICKET}}`: Link to ticket if relevant, or "null"
- `{{LINKS_ADR}}`: Link to ADR if relevant, or "null"
- `{{LINKS_PR}}`: Link to PR if relevant, or "null"
- `{{FILES_YAML}}`: List files as YAML array (one per line with " - " prefix)
- `{{TESTS_YAML}}`: List tests as YAML array (one per line with " - " prefix)

**Content sections:**

- `{{PROMPT_TEXT}}`: The user's original request (verbatim)
- `{{RESPONSE_TEXT}}`: Your response summary (1-3 sentences)
- `{{OUTCOME_IMPACT}}`: What was accomplished
- `{{TESTS_SUMMARY}}`: Tests that were run or created
- `{{FILES_SUMMARY}}`: Files that were created or modified
- `{{NEXT_PROMPTS}}`: Suggested next steps or "none"
- `{{REFLECTION_NOTE}}`: One insight or learning point

**IMPORTANT:** Replace ALL placeholders - do not leave any {{PLACEHOLDER}} unfilled.

### 6. Confirm and Report

- Show confirmation: "✅ Exchange recorded as PHR-{id} in {context} context"
- Display the file path (relative to repo root for brevity)
- Briefly summarize what was captured (1 sentence)

## Example Scenarios

### Scenario 1: Early-phase constitution work (no specs/ yet)

```
User: "Help me create a constitution.md for quality standards"
[You execute the work, create constitution.md]

[Step 1: Create PHR file]
scripts/bash/create-phr.sh \
  --title "Define quality standards" \
  --stage constitution \
  --json

[Step 2: Fill placeholders in the created file]
- {{PROMPT_TEXT}}: "Help me create a constitution.md for quality standards"
- {{RESPONSE_TEXT}}: "Created constitution.md with 5 quality principles covering code quality, testing, and documentation"
- {{FILES_YAML}}:
  - memory/constitution.md
- {{LABELS}}: "constitution", "quality", "principles"
```

**Result:** `docs/prompts/0001-define-quality-standards.constitution.prompt.md`

### Scenario 2: Feature implementation work

```
User: "Add JWT authentication to the login endpoint"
[You execute the work, modify files, run tests]

[Step 1: Create PHR file]
scripts/bash/create-phr.sh \
  --title "Add JWT authentication" \
  --stage green \
  --json

[Step 2: Fill placeholders in the created file]
- {{PROMPT_TEXT}}: "Add JWT authentication to the login endpoint"
- {{RESPONSE_TEXT}}: "Implemented JWT auth with token generation, validation, and refresh logic"
- {{FILES_YAML}}:
  - src/auth/jwt.py
  - src/api/login.py
  - tests/test_auth.py
- {{TESTS_YAML}}:
  - tests/test_auth.py::test_jwt_generation
  - tests/test_auth.py::test_token_validation
- {{LABELS}}: "auth", "security", "jwt", "api"
```

**Result:** `specs/001-authentication/prompts/0001-add-jwt-authentication.green.prompt.md`

### Scenario 3: Debugging work

```
User: "Fix the database connection timeout error"
[You debug, identify issue, apply fix]

[Step 1: Create PHR file]
scripts/bash/create-phr.sh \
  --title "Fix DB timeout error" \
  --stage red \
  --json

[Step 2: Fill placeholders in the created file]
- {{PROMPT_TEXT}}: "Fix the database connection timeout error"
- {{RESPONSE_TEXT}}: "Increased connection pool size from 5 to 20 and added exponential backoff retry logic"
- {{FILES_YAML}}:
  - src/database/connection.py
  - config/database.yaml
- {{LABELS}}: "database", "bugfix", "performance"
```

**Result:** `specs/002-database/prompts/0001-fix-db-timeout-error.red.prompt.md`

## Quality Checklist

Before finalizing the PHR:

- ✅ User's request was fully executed (work is done)
- ✅ Stage accurately reflects the type of work performed
- ✅ Title is concise and descriptive (3-7 words)
- ✅ File paths are relative to repo root
- ✅ Test names include module paths when possible
- ✅ Labels are relevant and useful for future search
- ✅ Response summary captures key outcomes
- ✅ PHR was created successfully (JSON output received)

## Error Handling

**If create-phr.sh fails:**

- Show the error message from the script
- Explain what went wrong (e.g., invalid stage, missing directory)
- Suggest corrective action (e.g., create feature directory first)
- Do NOT fail silently - PHR creation failures should be visible

**If stage is ambiguous:**

- Use best judgment based on the work performed
- Prefer more specific stages (architect, red, green) over generic (misc, general)
- When in doubt: `misc` for feature work, `general` for pre-feature work

## Why PHRs Matter

PHRs create a **searchable, reviewable history** of AI-assisted development that:

- 📚 **Compounds learning**: Revisit successful strategies
- 🔍 **Enables traceability**: Track why code was written that way
- 🧠 **Builds intuition**: Recognize patterns in effective prompting
- 👥 **Supports collaboration**: Share knowledge across team
- ✅ **Improves compliance**: Audit trail for code reviews

**Remember:** PHRs are for learning and traceability, not execution. Execute first, record second.
