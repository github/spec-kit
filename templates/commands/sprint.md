---
description: "Create and manage sprints - group features into time-boxed development cycles with goals, capacity planning, and progress tracking."
---

# Sprint Management Command

## User Input

```text
$ARGUMENTS
```

You **MUST** execute the sprint command based on the user input.

## Commands

The user's input will be one of these commands. **Execute the corresponding action immediately:**

### `/speckit.sprint start "Sprint Name" --duration 2w`

**Do this:**

1. Extract sprint name and duration from `$ARGUMENTS`
2. Execute the create-sprint script:
   ```bash
   bash .specify/scripts/bash/create-sprint.sh "Sprint Name" "2w"
   ```
3. Parse the script output and report success/failure to the user

### `/speckit.sprint add <feature-ids>`

**Do this:**

1. Extract feature IDs from `$ARGUMENTS` (space-separated)
2. For each feature ID:
   - Check if `specs/<feature-id>/` exists
   - Check if already in `sprints/active/backlog.md`
   - If valid and not duplicate, extract feature name from `specs/<feature-id>/spec.md`
   - Append to backlog: `| <feature-id> | <name> | P1 | Not Started | | |`
3. Report which features were added and which were skipped

### `/speckit.sprint status`

**Do this:**

1. Read `sprints/active/sprint.md` to get sprint info
2. Read `sprints/active/backlog.md` to count features by status
3. Calculate completion percentage
4. Display formatted status with progress and blockers

### `/speckit.sprint complete`

**Do this:**

1. Execute the archive-sprint script:
   ```bash
   bash .specify/scripts/bash/archive-sprint.sh
   ```
2. Answer any interactive prompts about near-complete features
3. Parse the script output and report success/failure to the user

1. **Check for active sprint**:
   - If `sprints/active/sprint.md` exists, warn user and ask to complete it first
   - Suggest: `/speckit.sprint complete` or `/speckit.archive`

2. **Determine sprint number**:
   - Count existing archives in `sprints/archive/`
   - Next sprint number = count + 1 (e.g., sprint-001, sprint-002)

3. **Create sprint structure**:
   ```
   sprints/active/
   ├── sprint.md       (from templates/sprint-template.md)
   ├── backlog.md      (empty, will be populated)
   └── decisions.md    (empty, will be populated)
   ```

4. **Fill sprint template**:
   - Replace `[NUMBER]` with sprint number
   - Replace `[NAME]` with provided sprint name
   - Replace `[DURATION]` with provided duration or default "2 weeks"
   - Set `[START_DATE]` to today
   - Calculate `[END_DATE]` based on duration
   - Replace `$ARGUMENTS` with user's full input

5. **Initialize backlog.md**:
   ```markdown
   # Sprint [NUMBER] Backlog
   
   ## Features
   
   No features added yet. Use `/speckit.sprint add <feature-id>` to add features.
   
   ## Notes
   
   [Sprint planning notes]
   ```

6. **Initialize decisions.md**:
   ```markdown
   # Sprint [NUMBER] Decisions
   
   Document key decisions made during this sprint.
   
   ## Decision Log
   
   No decisions recorded yet.
   ```

7. **Output**:
   - Confirm sprint created
   - Show sprint number, name, duration
   - Suggest next steps: add features, define goals

---

### `/speckit.sprint add` - Add Features to Sprint

**Usage**: `/speckit.sprint add 001-feature-name 002-another-feature`

**Arguments**: One or more feature IDs (space-separated)

**Process**:

1. **Verify active sprint exists**:
   - Check `sprints/active/sprint.md`
   - If not found, error: "No active sprint. Use `/speckit.sprint start` first."

2. **For each feature ID**:
   
   a. **Validate feature exists**:
      - Check if `specs/[feature-id]/` directory exists
      - If not found, warn: "Feature [feature-id] not found in specs/, skipping"
      - Continue to next feature
   
   b. **Check if already in backlog**:
      - Search `sprints/active/backlog.md` for feature ID
      - If found, skip with message: "Feature [feature-id] already in sprint"
   
   c. **Extract feature name**:
      - Read `specs/[feature-id]/spec.md`
      - Find line matching `# Feature Specification: [NAME]`
      - Extract feature name, or use "Unknown" if not found
   
   d. **Add to backlog.md**:
      - Append to the features table:
        ```markdown
        | [feature-id] | [Feature Name] | P1 | Not Started | | |
        ```
      - If backlog has "No features added yet" message, replace it with the table header first

3. **Output summary**:
   ```
   ✅ Added 2 features to Sprint [NUMBER]:
     - 001-feature-name: Feature Title
     - 002-another-feature: Another Title
   
   Current sprint backlog: 5 features
   ```

**Example**:
```bash
/speckit.sprint add 001-auth 002-dashboard 003-api
```

---

### `/speckit.sprint status` - View Sprint Status

**Usage**: `/speckit.sprint status`

**Process**:

1. **Check for active sprint**:
   - If no active sprint, show: "No active sprint. Use `/speckit.sprint start` to begin."

2. **Read sprint.md**:
   - Extract sprint number, name, duration, dates
   - Parse features table
   - Calculate progress metrics

3. **Display status**:
   ```
   Sprint [NUMBER]: [NAME]
   Duration: [START] - [END] ([X] days remaining)
   
   Progress:
   - Features: [X] total, [Y] complete, [Z] in progress
   - Completion: [N]%
   
   Features:
   [Table of features with status]
   
   Recent Decisions: [Count]
   ```

4. **Highlight blockers**:
   - Show any features marked as "Blocked"
   - Suggest actions

---

### `/speckit.sprint complete` - Complete Sprint

**Usage**: `/speckit.sprint complete`

**Process**:

1. **Verify active sprint**:
   - Check `sprints/active/sprint.md` exists
   - If not, error: "No active sprint to complete."

2. **Trigger archival**:
   - Call `/speckit.archive` internally
   - This will:
     - Generate sprint summary
     - Move to archive
     - Extract decisions
     - Create retrospective template

3. **Output**:
   - Confirm sprint completed
   - Show archive location
   - Suggest: `/speckit.retrospective` to conduct retrospective

---

## Integration with Existing Commands

### `/speckit.specify` Integration

When creating a new feature, optionally link to active sprint:

```
After creating feature spec, ask:
"Add this feature to the current sprint? (y/n)"

If yes:
- Run `/speckit.sprint add [feature-id]`
- Update sprint backlog
```

### `/speckit.implement` Integration

When implementing features, update sprint progress:

```
After completing feature implementation:
- Update sprint.md feature status to "Complete"
- Update sprint metrics
- Check if sprint goal achieved
```

## Notes

- Only one active sprint at a time
- Features can be added/removed during sprint
- Sprint duration is flexible (can be extended)
- Decisions are captured automatically from feature specs
- Use `/speckit.archive` to manually archive without completing

{SCRIPT}

## Script Integration

The `/speckit.sprint start` command uses the `create-sprint` script to handle:
- Sprint number calculation
- Directory creation
- Template copying and variable replacement
- File initialization

**Script Location**:
- Bash: `scripts/bash/create-sprint.sh`
- PowerShell: `scripts/powershell/create-sprint.ps1`

**Usage**:
```bash
# Bash
./scripts/bash/create-sprint.sh --json --duration 2w "Sprint Name"

# PowerShell
./scripts/powershell/create-sprint.ps1 -Json -Duration 2w "Sprint Name"
```

{SCRIPT}
