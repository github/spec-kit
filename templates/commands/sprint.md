---
description: "Create and manage sprints - group features into time-boxed development cycles with goals, capacity planning, and progress tracking."
---

# Sprint Management Command

You are managing **sprints** (time-boxed development cycles) to organize features, track progress, and maintain project visibility.

## Commands

### `/speckit.sprint start` - Start New Sprint

**Usage**: `/speckit.sprint start "Sprint Name" --duration 2w`

**Arguments**: 
- Sprint name (required)
- `--duration` (optional): Sprint duration (e.g., 1w, 2w, 3w)

**Process**:

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

**Arguments**: One or more feature IDs

**Process**:

1. **Verify active sprint exists**:
   - Check `sprints/active/sprint.md`
   - If not found, error: "No active sprint. Use `/speckit.sprint start` first."

2. **Validate feature IDs**:
   - Check each feature exists in `specs/`
   - Warn if feature doesn't exist

3. **Update sprint.md**:
   - Add features to "Features in Sprint" table
   - Set status to "Not Started"
   - Leave owner blank (can be filled manually)

4. **Update backlog.md**:
   - Add feature to backlog list
   - Include feature name from spec.md if available

5. **Output**:
   - Confirm features added
   - Show updated feature count
   - Display current sprint backlog

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
