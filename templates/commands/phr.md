---
description: Record an AI exchange as a Prompt History Record (PHR) for learning and traceability.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

# COMMAND: Record this AI exchange as a structured PHR artifact

## CONTEXT

The user has just completed work (or is requesting work) and needs to capture this exchange as a Prompt History Record (PHR) for:

- Learning and pattern recognition (spaced repetition)
- Team knowledge sharing and traceability
- Compliance and audit requirements
- Building a searchable corpus of effective prompts

**User's input to record:**

$ARGUMENTS

**CRITICAL**: The complete text above is the PROMPT to preserve verbatim. Do NOT truncate to first line only.

## YOUR ROLE

Act as a meticulous documentation specialist with expertise in:

- Knowledge management and organizational learning
- Software development lifecycle documentation
- Metadata extraction and classification
- Creating structured, searchable technical records

## QUICK OVERVIEW (strict)

After completing ANY work, automatically create a PHR:

1. **Detect work type**: constitution|spec|plan|tasks|implementation|debugging|refactoring|discussion|general
2. **Generate title**: 3-7 word descriptive title summarizing the work
3. **Capture context**: COMPLETE conversation (never truncate to summaries)
4. **Route correctly**:
   - Pre-feature work → `history/prompts/`
   - Feature-specific work → `specs/<feature>/prompts/`
5. **Confirm**: Show "📝 PHR-NNNN recorded"

## OUTPUT STRUCTURE (with quick flywheel hooks)

Execute this workflow in 5 sequential steps, reporting progress after each:

## Step 1: Execute User's Request (if not already done)

If the user provided a task/question in $ARGUMENTS:

- Complete the requested work first
- Provide full response to user
- Then proceed to Step 2 to record the exchange

If you already completed work and user just wants to record it:

- Skip to Step 2

## Step 2: Determine Stage and Routing

Select ONE stage that best describes the work:

**Constitution** (→ `history/prompts/constitution/`):
- `constitution` - Defining quality standards, project principles

**Feature-specific** (→ `history/prompts/<feature-name>/` - requires feature context):
- `spec` - Creating feature specifications
- `plan` - Architecture design and technical approach
- `tasks` - Implementation breakdown with test cases
- `red` - Debugging, fixing errors, test failures
- `green` - Implementation, new features, passing tests
- `refactor` - Code cleanup, optimization
- `explainer` - Code explanations, documentation
- `misc` - Other feature-specific work

**General/Catch-all** (→ `history/prompts/general/`):
- `general` - General work not tied to a specific feature

## Step 3: Create PHR File

Generate a concise title (3-7 words) summarizing what was accomplished.

Call the PHR creation script with title and stage:

```bash
scripts/bash/create-phr.sh \
  --title "<your-generated-title>" \
  --stage <selected-stage> \
  [--feature <feature-slug>] \
  --json
```

Parse the JSON output to get: `id`, `path`, `context`, `stage`, `feature`

**Routing is determined automatically:**
- `constitution` → `history/prompts/constitution/`
- Feature stages → `history/prompts/<feature-name>/`
- `general` → `history/prompts/general/`

## Step 4: Fill ALL Template Placeholders (Analyze→Measure)

Read the file at `path` from JSON output. Replace ALL {{PLACEHOLDERS}}:

**YAML Frontmatter:**

- `{{ID}}` → ID from JSON output
- `{{TITLE}}` → Your generated title
- `{{STAGE}}` → Selected stage
- `{{DATE_ISO}}` → Today (YYYY-MM-DD format)
- `{{SURFACE}}` → "agent"
- `{{MODEL}}` → Your model name or "unspecified"
- `{{FEATURE}}` → Feature from JSON or "none"
- `{{BRANCH}}` → Current branch name
- `{{USER}}` → Git user name or "unknown"
- `{{COMMAND}}` → "/sp.phr" or the command that triggered this
- `{{LABELS}}` → Extract key topics as ["topic1", "topic2", ...]
- `{{LINKS_SPEC}}`, `{{LINKS_TICKET}}`, `{{LINKS_ADR}}`, `{{LINKS_PR}}` → Relevant links or "null"
- `{{FILES_YAML}}` → List files modified/created, one per line with " - " prefix, or " - none"
- `{{TESTS_YAML}}` → List tests run/created, one per line with " - " prefix, or " - none"

**Content Sections:**

- `{{PROMPT_TEXT}}` → **THE COMPLETE $ARGUMENTS TEXT VERBATIM** (do NOT truncate to first line!)
- `{{RESPONSE_TEXT}}` → Brief summary of your response (1-3 sentences)
- `{{OUTCOME_IMPACT}}` → What was accomplished
- `{{TESTS_SUMMARY}}` → Tests run or "none"
- `{{FILES_SUMMARY}}` → Files modified or "none"
- `{{NEXT_PROMPTS}}` → Suggested next steps or "none"
- `{{REFLECTION_NOTE}}` → One key insight

Add short evaluation notes:
- **Failure modes observed:** Specify any issues encountered, such as ambiguous instructions, incomplete metadata, misrouted commands, or unexpected script errors. Example: "Prompt did not capture full user input; metadata field 'LABELS' was left blank."
- **Next experiment to improve prompt quality:** Suggest a concrete action to address the failure mode. Example: "Rephrase prompt to clarify required metadata fields," or "Test with a multi-line user input to ensure full capture."

**CRITICAL**: `{{PROMPT_TEXT}}` MUST be the FULL multiline user input from $ARGUMENTS above, not just the title or first line.

## Step 5: Report Completion

## FORMATTING REQUIREMENTS

Present results in this exact structure:

```
✅ Exchange recorded as PHR-{id} in {context} context
📁 {relative-path-from-repo-root}

Stage: {stage}
Feature: {feature or "none"}
Files modified: {count}
Tests involved: {count}

Acceptance Criteria (PASS only if all true)
- Full prompt preserved verbatim (no truncation)
- Stage and routing determined correctly
- Metadata fields populated; missing values noted explicitly
```

## ERROR HANDLING

If create-phr.sh fails:

1. Display the exact error message from script
2. Explain what went wrong in plain language
3. Provide specific corrective action with commands
4. Do NOT fail silently or hide errors

## TONE

Be professional, concise, and action-oriented. Focus on what was accomplished and what's next.
