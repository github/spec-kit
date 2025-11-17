# Sprint/Cycle Management Design for Spec Kit

## Overview

This design introduces sprint/cycle management to Spec Kit while preserving all existing feature-level workflows. It enables teams to:
- Group features into time-boxed sprints
- Archive completed sprints with high-level summaries
- Track decisions and pivots across cycles
- Conduct retrospectives to clarify unclear decisions
- Maintain project-level visibility

## Key Principles

1. **Non-invasive**: Existing feature workflows remain unchanged
2. **Additive**: Sprint management is optional - teams can still work feature-by-feature
3. **Archival-first**: Completed sprints are archived with summaries, not deleted
4. **Decision-focused**: Captures why decisions were made, not just what was done
5. **Retrospective-driven**: Similar to `/speckit.clarify` but for understanding past decisions

## Directory Structure

```
.specify/
├── memory/
│   └── constitution.md
├── sprints/                          # NEW: Sprint management
│   ├── active/                       # Current sprint
│   │   ├── sprint.md                 # Sprint plan & goals
│   │   ├── backlog.md                # Sprint backlog
│   │   └── decisions.md              # Decisions made during sprint
│   ├── archive/                      # Completed sprints
│   │   ├── sprint-001/
│   │   │   ├── summary.md            # High-level summary
│   │   │   ├── decisions.md          # Key decisions & pivots
│   │   │   ├── retrospective.md      # Retrospective notes
│   │   │   └── features.md           # List of completed features
│   │   ├── sprint-002/
│   │   └── ...
│   └── roadmap.md                    # Project-level roadmap
├── specs/                            # Existing feature specs
│   ├── 001-feature-name/
│   └── ...
└── templates/
    ├── sprint-template.md            # NEW
    ├── sprint-summary-template.md    # NEW
    └── retrospective-template.md     # NEW
```

## New Commands

### 1. `/speckit.sprint` - Sprint Planning & Management

**Purpose**: Create, manage, and track sprints

**Usage**:
```bash
# Start a new sprint
/speckit.sprint start "Sprint 1: Core Authentication & UI Foundation" --duration 2w

# Add features to current sprint
/speckit.sprint add 001-auth-foundation 002-ui-components

# View sprint status
/speckit.sprint status

# Complete current sprint (triggers archival)
/speckit.sprint complete
```

**What it does**:
- Creates sprint plan with goals, duration, and capacity
- Links features to the sprint
- Tracks sprint progress
- Archives sprint when complete

### 2. `/speckit.retrospective` - Sprint Retrospective

**Purpose**: Conduct retrospectives to understand decisions and identify improvements

**Usage**:
```bash
# Start retrospective for current sprint
/speckit.retrospective

# Review specific archived sprint
/speckit.retrospective sprint-001
```

**What it does**:
- Similar to `/speckit.clarify` but for past decisions
- Asks structured questions about:
  - What went well?
  - What could be improved?
  - Why were certain decisions made?
  - What pivots occurred and why?
  - What would we do differently?
- Records answers in `retrospective.md`
- Updates `decisions.md` with clarifications

### 3. `/speckit.roadmap` - Project-Level Planning

**Purpose**: Maintain project-level visibility across sprints

**Usage**:
```bash
# Create/update roadmap
/speckit.roadmap

# View roadmap
/speckit.roadmap view
```

**What it does**:
- Creates high-level project roadmap
- Shows sprint timeline
- Tracks feature dependencies
- Visualizes progress

### 4. `/speckit.archive` - Manual Sprint Archival

**Purpose**: Archive current sprint and create summary

**Usage**:
```bash
# Archive current sprint
/speckit.archive

# Archive with custom summary
/speckit.archive --summary "Completed core auth, pivoted from OAuth to OIDC"
```

**What it does**:
- Moves sprint from `active/` to `archive/sprint-NNN/`
- Generates high-level summary from completed features
- Extracts key decisions and pivots
- Creates retrospective template
- Updates roadmap

## Templates

### Sprint Template (`sprint-template.md`)

```markdown
# Sprint [NUMBER]: [NAME]

**Duration**: [START_DATE] - [END_DATE] ([DURATION])  
**Status**: Active  
**Created**: [DATE]

## Sprint Goal

[High-level goal for this sprint - what are we trying to achieve?]

## Success Criteria

- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]
- [ ] [Measurable outcome 3]

## Capacity

- **Team Size**: [NUMBER] developers
- **Available Days**: [NUMBER] working days
- **Estimated Velocity**: [NUMBER] story points (if using)

## Features in Sprint

| Feature ID | Feature Name | Priority | Status | Owner |
|------------|--------------|----------|--------|-------|
| 001-auth   | Authentication | P1 | In Progress | @user |
| 002-ui     | UI Foundation | P1 | Not Started | @user |

## Dependencies

- [Feature X] depends on [Feature Y]
- External dependency: [Description]

## Risks

- **Risk**: [Description]
  - **Mitigation**: [Strategy]

## Daily Progress

### [DATE]
- Completed: [What was finished]
- Blocked: [Any blockers]
- Next: [What's next]

## Notes

[Any additional context, decisions, or observations]
```

### Sprint Summary Template (`sprint-summary-template.md`)

```markdown
# Sprint [NUMBER] Summary: [NAME]

**Duration**: [START_DATE] - [END_DATE]  
**Status**: Completed  
**Archived**: [DATE]

## Overview

[2-3 paragraph summary of what was accomplished in this sprint]

## Sprint Goal Achievement

**Goal**: [Original sprint goal]  
**Result**: ✅ Achieved / ⚠️ Partially Achieved / ❌ Not Achieved

[Explanation of outcome]

## Completed Features

| Feature ID | Feature Name | Status | Notes |
|------------|--------------|--------|-------|
| 001-auth   | Authentication | ✅ Complete | Pivoted from OAuth to OIDC |
| 002-ui     | UI Foundation | ✅ Complete | Added accessibility features |

## Key Decisions

### Decision 1: [Title]
- **Context**: [Why this decision was needed]
- **Options Considered**: [What alternatives were evaluated]
- **Decision**: [What was chosen]
- **Rationale**: [Why this was chosen]
- **Impact**: [How this affected the project]

### Decision 2: [Title]
[Same structure]

## Pivots & Changes

### Pivot 1: [Title]
- **Original Plan**: [What was originally planned]
- **Change**: [What actually happened]
- **Reason**: [Why the pivot occurred]
- **Outcome**: [Result of the pivot]

## Metrics

- **Features Planned**: [NUMBER]
- **Features Completed**: [NUMBER]
- **Features Carried Over**: [NUMBER]
- **Velocity**: [NUMBER] (if tracked)

## Artifacts

- Specifications: `specs/001-auth/`, `specs/002-ui/`
- Implementation: [Links to PRs, commits, deployments]
- Documentation: [Links to updated docs]

## Lessons Learned

[Key takeaways from this sprint - what worked, what didn't]

## Next Sprint Preview

[Brief look ahead to what's coming next]
```

### Retrospective Template (`retrospective-template.md`)

```markdown
# Sprint [NUMBER] Retrospective

**Sprint**: [NAME]  
**Date**: [DATE]  
**Participants**: [List of participants]

## What Went Well? 🎉

[Things that worked well and should be continued]

- [Item 1]
- [Item 2]

## What Could Be Improved? 🔧

[Things that didn't work well and should be changed]

- [Item 1]
- [Item 2]

## Decision Clarifications 🤔

### Decision: [Title]
**Question**: Why did we choose [X] over [Y]?  
**Answer**: [Clarification of the decision rationale]

### Decision: [Title]
**Question**: What led to the pivot from [X] to [Y]?  
**Answer**: [Explanation of the pivot]

## Action Items 📋

- [ ] [Action item 1] - Owner: [Name]
- [ ] [Action item 2] - Owner: [Name]

## Experiments to Try 🧪

[New approaches or techniques to try in the next sprint]

- [Experiment 1]
- [Experiment 2]

## Appreciation 💙

[Shout-outs to team members for specific contributions]

- [Appreciation 1]
- [Appreciation 2]
```

### Roadmap Template (`roadmap-template.md`)

```markdown
# Project Roadmap: [PROJECT_NAME]

**Last Updated**: [DATE]  
**Project Status**: [Active/On Hold/Complete]

## Vision

[High-level vision for the project - what are we building and why?]

## Current Sprint

**Sprint [NUMBER]**: [NAME]  
**Duration**: [START_DATE] - [END_DATE]  
**Status**: [In Progress/Planning/Complete]

[Brief summary of current sprint goals]

## Upcoming Sprints

### Sprint [NUMBER]: [NAME] (Planned)
**Target**: [DATE_RANGE]  
**Focus**: [High-level focus area]

**Planned Features**:
- [Feature 1]
- [Feature 2]

### Sprint [NUMBER]: [NAME] (Tentative)
**Target**: [DATE_RANGE]  
**Focus**: [High-level focus area]

## Completed Sprints

| Sprint | Name | Duration | Features | Status |
|--------|------|----------|----------|--------|
| 001 | Auth & UI | 2w | 5 | ✅ Complete |
| 002 | API Layer | 2w | 4 | ✅ Complete |

## Feature Backlog

### High Priority (P1)
- [ ] [Feature name] - [Brief description]
- [ ] [Feature name] - [Brief description]

### Medium Priority (P2)
- [ ] [Feature name] - [Brief description]

### Low Priority (P3)
- [ ] [Feature name] - [Brief description]

## Dependencies & Blockers

- [Dependency 1]: [Description and status]
- [Blocker 1]: [Description and mitigation plan]

## Milestones

- **[Milestone 1]**: [DATE] - [Description]
- **[Milestone 2]**: [DATE] - [Description]

## Risks & Assumptions

### Risks
- **[Risk 1]**: [Description]
  - Likelihood: [High/Medium/Low]
  - Impact: [High/Medium/Low]
  - Mitigation: [Strategy]

### Assumptions
- [Assumption 1]
- [Assumption 2]

## Success Metrics

- [Metric 1]: [Target]
- [Metric 2]: [Target]
```

## Implementation Strategy

### Phase 1: Core Sprint Management
1. Add sprint templates to `templates/`
2. Create `/speckit.sprint` command
3. Implement sprint creation and feature linking
4. Test with single sprint workflow

### Phase 2: Archival & Summaries
1. Implement `/speckit.archive` command
2. Auto-generate summaries from completed features
3. Extract decisions from feature specs
4. Test archival workflow

### Phase 3: Retrospectives
1. Create `/speckit.retrospective` command
2. Implement structured questioning (similar to `/speckit.clarify`)
3. Record answers in retrospective.md
4. Test retrospective workflow

### Phase 4: Roadmap & Visibility
1. Implement `/speckit.roadmap` command
2. Generate project-level views
3. Track cross-sprint dependencies
4. Test roadmap updates

## Integration with Existing Workflows

### Feature Creation (`/speckit.specify`)
- Optionally link feature to current sprint
- Update sprint backlog automatically
- No change to existing behavior if no sprint active

### Feature Planning (`/speckit.plan`)
- Reference sprint goals in planning
- Consider sprint capacity
- No change to existing behavior

### Feature Implementation (`/speckit.implement`)
- Update sprint progress
- Track completion in sprint.md
- No change to existing behavior

### Feature Completion
- Mark feature complete in sprint backlog
- Update sprint metrics
- Trigger sprint completion check

## Example Workflow

### Starting a Sprint
```bash
# 1. Create sprint
/speckit.sprint start "Sprint 1: Authentication & Authorization" --duration 2w

# 2. Add features to sprint
/speckit.sprint add 001-auth-foundation 002-role-management

# 3. View sprint status
/speckit.sprint status
```

### During Sprint
```bash
# Work on features as normal
/speckit.specify Build authentication system with OIDC
/speckit.plan Use AWS Cognito with custom authorizers
/speckit.tasks
/speckit.implement

# Track decisions
# (Automatically captured from feature specs)
```

### Completing Sprint
```bash
# 1. Archive sprint
/speckit.archive

# 2. Conduct retrospective
/speckit.retrospective

# 3. Update roadmap
/speckit.roadmap
```

## Benefits

1. **Project Visibility**: See progress across multiple features
2. **Decision Tracking**: Understand why choices were made
3. **Knowledge Preservation**: Archive maintains institutional knowledge
4. **Continuous Improvement**: Retrospectives drive process improvements
5. **Team Coordination**: Sprint planning aligns team efforts
6. **Stakeholder Communication**: Summaries provide clear status updates

## Backward Compatibility

- Existing projects continue to work without sprints
- Sprint management is opt-in
- Feature-level workflows unchanged
- No breaking changes to existing commands

## Future Enhancements

- Sprint velocity tracking
- Burndown charts
- Cross-sprint dependency visualization
- Integration with GitHub Projects/Issues
- Automated sprint reports
- Sprint templates for common patterns (MVP sprint, polish sprint, etc.)
