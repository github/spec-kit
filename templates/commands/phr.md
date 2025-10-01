---
description: Execute user request AND record the exchange as a Prompt History Record (PHR).
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

# PHR Command: Execute + Record

**CRITICAL**: This command does TWO things sequentially:

1. **EXECUTE** the user's actual request (do the work)
2. **RECORD** the entire exchange as a PHR (capture for learning)

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

### 4. Get Repository Context

Run `{SCRIPT}` once from repo root to get repository metadata. This will help auto-detect the correct location for the PHR.

### 5. Create PHR Record

Call `scripts/bash/create-phr.sh` with extracted metadata:

```bash
scripts/bash/create-phr.sh \
  --title "<concise title>" \
  --stage <stage> \
  --prompt "<original user request>" \
  --response "<your response summary>" \
  --files "<file1.py,file2.py>" \
  --tests "<test_module.py::test_name>" \
  --labels "<topic1,topic2>" \
  --json
```

**Notes:**

- Feature is auto-detected from current branch or latest numbered feature
- Script will use correct location: `docs/prompts/` (pre-feature) or `specs/<feature>/prompts/` (feature work)
- Sequence numbering is local to each directory (each starts at 0001)
- Stage validation ensures correct extension: `.constitution.prompt.md`, `.architect.prompt.md`, etc.

### 6. Confirm and Report

- Parse the JSON output to get `id`, `path`, `context`, and `stage`
- Show confirmation: "✅ Exchange recorded as PHR-{id} in {context} context"
- Display the file path (relative to repo root for brevity)
- **Do not** read the file back - just confirm creation

## Example Scenarios

### Scenario 1: Early-phase constitution work (no specs/ yet)

```
User: "Help me create a constitution.md for quality standards"
[You execute the work, create constitution.md]
[Then call:]
scripts/bash/create-phr.sh \
  --title "Define quality standards" \
  --stage constitution \
  --prompt "Help me create a constitution.md for quality standards" \
  --response "Created constitution.md with 5 quality principles" \
  --files "constitution.md" \
  --labels "constitution,quality" \
  --json
```

**Result:** `docs/prompts/0001-define-quality-standards.constitution.prompt.md`

### Scenario 2: Feature implementation work

```
User: "Add JWT authentication to the login endpoint"
[You execute the work, modify files, run tests]
[Then call:]
scripts/bash/create-phr.sh \
  --title "Add JWT authentication" \
  --stage green \
  --prompt "Add JWT authentication to the login endpoint" \
  --response "Implemented JWT auth with token generation and validation" \
  --files "src/auth/jwt.py,src/api/login.py,tests/test_auth.py" \
  --tests "tests/test_auth.py::test_jwt_generation" \
  --labels "auth,security,jwt" \
  --json
```

**Result:** `specs/001-authentication/prompts/0001-add-jwt-authentication.green.prompt.md`

### Scenario 3: Debugging work

```
User: "Fix the database connection timeout error"
[You debug, identify issue, apply fix]
[Then call:]
scripts/bash/create-phr.sh \
  --title "Fix DB timeout error" \
  --stage red \
  --prompt "Fix the database connection timeout error" \
  --response "Increased connection pool size and added retry logic" \
  --files "src/database/connection.py,config/database.yaml" \
  --labels "database,bugfix" \
  --json
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
