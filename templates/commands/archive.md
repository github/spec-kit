---
description: "Archive completed sprint with high-level summary, extract key decisions, document pivots, and prepare for retrospective."
---

# Sprint Archive Command

## User Input

```text
$ARGUMENTS
```

You **MUST** execute the sprint archive process.

**IMPORTANT**: When prompting for near-complete features, ask about **ONE feature at a time** and wait for the user's response before showing the next feature. This is similar to how `/speckit.clarify` works - sequential questions, not all at once.

## Process

**Do this:**

1. **Check for near-complete features** (In Progress/In Review/Blocked):
   
   a. Read `sprints/active/backlog.md`
   
   b. For each feature with status "In Progress", "In Review", or "Blocked":
      - Check if `specs/<feature-id>/` exists
      - Check if `specs/<feature-id>/spec.md` exists
      - Check if `specs/<feature-id>/planning/plan.md` exists
      - Check if `specs/<feature-id>/planning/tasks.md` exists
      - Count TODO/FIXME/XXX markers in spec.md
   
   c. **Ask the user** for each near-complete feature **ONE AT A TIME**:
      ```
      Feature: <feature-id>
      Name: <feature-name>
      Status: <current-status>
      
      Completion indicators:
        ✅ Spec exists
        ✅ Plan exists
        ✅ Tasks exist
        ⚠️  2 TODO markers
      
      Should this feature be archived as complete? (y/n/skip-all)
      ```
   
   d. **WAIT for user response** before showing the next feature
   
   e. If user responds "skip-all", stop asking and proceed to step 2
   
   f. Collect feature IDs where user answered "y"

2. **Execute archive script** with collected decisions:
   
   Build the command with approved features:
   ```bash
   bash .specify/scripts/archive-sprint.sh --archive-features "005-api-lambda-implementation,007-deploy-frontend-aws"
   ```
   
   Or if no additional features:
   ```bash
   bash .specify/scripts/archive-sprint.sh
   ```
   
   The script will:
   - Archive features marked "Done/Completed/✅" automatically
   - Archive features from --archive-features parameter (if provided)
   - Move specs to archive directory
   - Generate summary, decisions, features.md, retrospective.md

3. **Report results** to the user:
   - Number of features archived
   - Archive location
   - Next steps (retrospective, new sprint)

### Step 1: Verify Active Sprint

1. **Check for active sprint**:
   - Verify `sprints/active/sprint.md` exists
   - If not found, error: "No active sprint to archive."

2. **Read sprint metadata**:
   - Sprint number
   - Sprint name
   - Start and end dates
   - Sprint goal
   - Features list

### Step 2: Determine Archive Location

1. **Create archive directory**:
   - Format: `sprints/archive/sprint-[NUMBER]-[slug]/`
   - Slug: lowercase, hyphenated version of sprint name
   - Example: `sprints/archive/sprint-001-foundation/`

2. **Create directory structure**:
   ```
   sprints/archive/sprint-[NUMBER]-[slug]/
   ├── summary.md         (generated)
   ├── decisions.md       (extracted)
   ├── retrospective.md   (template)
   └── features.md        (list)
   ```

### Step 3: Generate Sprint Summary

1. **Use template**: Copy from `templates/sprint-summary-template.md`

2. **Fill in metadata**:
   - Sprint number, name, duration
   - Start and end dates
   - Archived date (today)

3. **Analyze completed features**:
   - Read each feature spec from `specs/[feature-id]/`
   - Extract: feature name, status, completion date
   - Identify: completed, partial, carried over

4. **Generate executive summary**:
   - Summarize what was accomplished (2-3 paragraphs)
   - Assess sprint goal achievement
   - Highlight major accomplishments and challenges

5. **Calculate metrics**:
   - Features planned vs completed
   - Completion rate
   - Velocity (if tracked)

6. **Add custom summary** (if provided in `$ARGUMENTS`):
   - Prepend to executive summary
   - Use as additional context

### Step 4: Extract Key Decisions

1. **Scan feature specs**:
   - Look for decision sections in `specs/[feature-id]/plan.md`
   - Look for pivot notes in `specs/[feature-id]/COMPLETION_SUMMARY.md`
   - Check `sprints/active/decisions.md` for recorded decisions

2. **For each decision, extract**:
   - Decision title
   - Context (why decision was needed)
   - Options considered
   - Decision made
   - Rationale
   - Impact on project
   - Related features

3. **Identify pivots**:
   - Compare original plan vs actual outcome
   - Document: original plan, change, reason, outcome, lessons

4. **Write to decisions.md**:
   - Organize by importance
   - Include full context
   - Link to related feature specs

### Step 5: Document Lessons Learned

1. **Extract from feature specs**:
   - Look for "lessons learned" sections
   - Check completion summaries
   - Review implementation notes

2. **Categorize**:
   - What went well
   - What could be improved
   - Action items for next sprint

3. **Add to summary.md**:
   - Include in "Lessons Learned" section
   - Generate action items

### Step 6: Create Features List

1. **Generate features.md**:
   ```markdown
   # Sprint [NUMBER] Features
   
   ## Completed Features
   
   | Feature ID | Feature Name | Spec | Status |
   |------------|--------------|------|--------|
   | 001-auth   | Authentication | [spec](../../specs/001-auth/spec.md) | ✅ Complete |
   
   ## Partial Features
   
   [List features partially completed]
   
   ## Carried Over
   
   [List features moved to next sprint]
   ```

2. **Link to specs**:
   - Relative paths to feature specs
   - Include completion status

### Step 7: Create Retrospective Template

1. **Copy template**: From `templates/retrospective-template.md`

2. **Pre-fill sections**:
   - Sprint number and name
   - Date range
   - Completed features list
   - Known decisions (for clarification)
   - Known pivots (for analysis)

3. **Save to**: `sprints/archive/sprint-[NUMBER]-[slug]/retrospective.md`

4. **Mark as template**:
   - Add note: "Run `/speckit.retrospective` to conduct retrospective"

### Step 8: Move Sprint to Archive

1. **Copy files**:
   - Move `sprints/active/sprint.md` to archive
   - Move `sprints/active/decisions.md` to archive (if exists)
   - Move `sprints/active/backlog.md` to archive (if exists)

2. **Clean up active directory**:
   - Remove `sprints/active/` contents
   - Leave directory empty for next sprint

3. **Update roadmap** (if exists):
   - Mark sprint as complete in `sprints/roadmap.md`
   - Update project status

### Step 9: Output Summary

Display:
```
✅ Sprint [NUMBER] archived successfully!

Location: sprints/archive/sprint-[NUMBER]-[slug]/

Summary:
- Features completed: [X] of [Y]
- Key decisions: [N]
- Pivots: [M]

Files created:
- summary.md - High-level sprint summary
- decisions.md - Key decisions and pivots
- features.md - Feature list with links
- retrospective.md - Retrospective template

Next steps:
1. Review summary.md for accuracy
2. Run `/speckit.retrospective` to conduct retrospective
3. Run `/speckit.sprint start` to begin next sprint
```

## Example Output Structure

```
sprints/archive/sprint-001-foundation/
├── summary.md
│   ├── Executive Summary
│   ├── Sprint Goal Achievement
│   ├── Completed Features
│   ├── Key Decisions
│   ├── Pivots & Course Corrections
│   ├── Sprint Metrics
│   ├── Lessons Learned
│   └── Next Sprint Preview
│
├── decisions.md
│   ├── Decision 1: [Title]
│   ├── Decision 2: [Title]
│   └── ...
│
├── features.md
│   ├── Completed Features (with links)
│   ├── Partial Features
│   └── Carried Over
│
├── retrospective.md (template)
│   └── [Pre-filled with sprint context]
│
└── [Original sprint files]
    ├── sprint.md
    ├── backlog.md
    └── decisions.md
```

## Notes

- Archive can be run anytime (doesn't require sprint completion)
- Custom summary text in `$ARGUMENTS` is optional
- Decisions are extracted automatically from feature specs
- Retrospective template is created but not filled (use `/speckit.retrospective`)
- Archive is immutable - don't modify after creation

{SCRIPT}

## Script Integration

The `/speckit.archive` command uses the `archive-sprint` script to handle:
- Archive directory creation
- File moving and copying
- Feature spec scanning
- Summary generation
- Template processing

**Script Location**:
- Bash: `scripts/bash/archive-sprint.sh`
- PowerShell: `scripts/powershell/archive-sprint.ps1`

**Usage**:
```bash
# Bash
./scripts/bash/archive-sprint.sh --json --summary "Custom summary text"

# PowerShell
./scripts/powershell/archive-sprint.ps1 -Json -Summary "Custom summary text"
```

{SCRIPT}
