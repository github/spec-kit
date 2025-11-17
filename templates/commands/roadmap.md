---
description: "Generate and maintain project-level roadmap showing sprint timeline, feature dependencies, and overall progress across the project."
---

# Roadmap Command

You are creating and maintaining a **project-level roadmap** that provides visibility across sprints, tracks dependencies, and shows overall project progress.

## Purpose

Generate a roadmap that shows:
1. Project vision and goals
2. Current sprint status
3. Upcoming sprints (planned)
4. Completed sprints (archived)
5. Feature backlog
6. Dependencies and blockers
7. Milestones and success metrics

## Commands

### `/speckit.roadmap` - Generate/Update Roadmap

**Usage**: `/speckit.roadmap`

**Process**:

### Step 1: Gather Project Context

1. **Read constitution**:
   - Extract project vision from `memory/constitution.md`
   - Identify core principles and goals

2. **Scan sprint archives**:
   - List all directories in `sprints/archive/`
   - For each sprint, read `summary.md`
   - Extract: sprint number, name, dates, features, status

3. **Check active sprint**:
   - Read `sprints/active/sprint.md` if exists
   - Extract: current sprint info, features, progress

4. **Scan feature specs**:
   - List all features in `specs/`
   - Identify: completed, in-progress, planned
   - Extract dependencies from plan.md files

### Step 2: Analyze Sprint History

1. **For each completed sprint**:
   - Sprint number and name
   - Duration and dates
   - Features completed
   - Key outcomes
   - Status (✅ Complete)

2. **Calculate project metrics**:
   - Total sprints completed
   - Total features delivered
   - Average velocity (if tracked)
   - Completion trends

### Step 3: Identify Current State

1. **Active sprint**:
   - Sprint number and name
   - Duration and dates
   - Current progress (% complete)
   - Features in progress
   - Blockers or risks

2. **If no active sprint**:
   - Show: "No active sprint"
   - Suggest: "Use `/speckit.sprint start` to begin next sprint"

### Step 4: Plan Future Sprints

1. **Analyze feature backlog**:
   - List features not yet in any sprint
   - Group by priority (P1, P2, P3)
   - Identify dependencies

2. **Suggest upcoming sprints**:
   - Based on feature priorities
   - Consider dependencies
   - Estimate 2-3 future sprints

3. **Tentative sprint planning**:
   - Sprint N+1: High-priority features
   - Sprint N+2: Medium-priority features
   - Sprint N+3: Lower-priority features

### Step 5: Map Dependencies

1. **Scan feature specs**:
   - Look for dependency mentions in plan.md
   - Check for "depends on" or "blocked by" statements

2. **Create dependency map**:
   - Feature X depends on Feature Y
   - External dependencies (APIs, services, approvals)

3. **Identify blockers**:
   - Features blocked by dependencies
   - External blockers (vendor, approval, etc.)

### Step 6: Define Milestones

1. **Extract from sprints**:
   - Major deliverables from sprint summaries
   - Key achievements and outcomes

2. **Project milestones**:
   - MVP milestone (first usable version)
   - Beta milestone (feature complete)
   - GA milestone (production ready)
   - Future milestones

3. **Milestone dates**:
   - Based on sprint timeline
   - Include target dates

### Step 7: Generate Roadmap Document

1. **Use template**: From `templates/roadmap-template.md` (if exists) or create new

2. **Fill sections**:

   **Vision**:
   - High-level project vision
   - What are we building and why?

   **Current Sprint**:
   - Sprint number, name, dates
   - Progress and status
   - Features in progress

   **Upcoming Sprints**:
   - Sprint N+1: Name, dates, planned features
   - Sprint N+2: Name, dates, planned features
   - Sprint N+3: Name, dates, planned features

   **Completed Sprints**:
   - Table of completed sprints
   - Sprint number, name, duration, features, status

   **Feature Backlog**:
   - High priority (P1)
   - Medium priority (P2)
   - Low priority (P3)

   **Dependencies & Blockers**:
   - Internal dependencies
   - External dependencies
   - Current blockers

   **Milestones**:
   - Milestone name, date, description
   - Status (upcoming, achieved)

   **Success Metrics**:
   - Key metrics for project success
   - Current status vs targets

3. **Save to**: `sprints/roadmap.md`

### Step 8: Generate Visual Timeline (Optional)

Create ASCII timeline:
```
Project Timeline
================

Sprint 001 [========] Complete (Oct 1-15)
Sprint 002 [========] Complete (Oct 16-31)
Sprint 003 [====----] In Progress (Nov 1-15)
Sprint 004 [--------] Planned (Nov 16-30)
           ^
           Today
```

### Step 9: Output Summary

Display:
```
📊 Project Roadmap Updated

Location: sprints/roadmap.md

Summary:
- Completed sprints: [N]
- Current sprint: [Sprint X: Name]
- Upcoming sprints: [M] planned
- Feature backlog: [P] features
- Blockers: [B] active blockers

Milestones:
- [Milestone 1]: [Status]
- [Milestone 2]: [Status]

Next steps:
1. Review roadmap for accuracy
2. Update sprint plans as needed
3. Address blockers
```

---

### `/speckit.roadmap view` - View Roadmap

**Usage**: `/speckit.roadmap view`

**Process**:

1. **Check if roadmap exists**:
   - Look for `sprints/roadmap.md`
   - If not found, suggest: `/speckit.roadmap` to generate

2. **Display roadmap**:
   - Show full roadmap content
   - Highlight current sprint
   - Show upcoming sprints

3. **Summary stats**:
   - Total sprints
   - Current progress
   - Next milestone

---

## Roadmap Structure

```markdown
# Project Roadmap: [PROJECT_NAME]

**Last Updated**: [DATE]
**Project Status**: [Active/On Hold/Complete]

## Vision

[High-level vision - what are we building and why?]

## Current Sprint

**Sprint [NUMBER]**: [NAME]
**Duration**: [START] - [END]
**Status**: [In Progress/Planning/Complete]

[Brief summary of current sprint goals]

**Features**:
- [Feature 1]
- [Feature 2]

## Upcoming Sprints

### Sprint [N+1]: [NAME] (Planned)
**Target**: [DATE_RANGE]
**Focus**: [High-level focus area]

**Planned Features**:
- [Feature 1]
- [Feature 2]

### Sprint [N+2]: [NAME] (Tentative)
**Target**: [DATE_RANGE]
**Focus**: [High-level focus area]

## Completed Sprints

| Sprint | Name | Duration | Features | Status |
|--------|------|----------|----------|--------|
| 001 | Foundation | 2w | 5 | ✅ Complete |
| 002 | Core Features | 2w | 8 | ✅ Complete |

## Feature Backlog

### High Priority (P1)
- [ ] [Feature name] - [Brief description]

### Medium Priority (P2)
- [ ] [Feature name] - [Brief description]

### Low Priority (P3)
- [ ] [Feature name] - [Brief description]

## Dependencies & Blockers

- [Dependency 1]: [Description and status]
- [Blocker 1]: [Description and mitigation]

## Milestones

- **[Milestone 1]**: [DATE] - [Description]
- **[Milestone 2]**: [DATE] - [Description]

## Success Metrics

- [Metric 1]: [Target]
- [Metric 2]: [Target]
```

## Integration with Other Commands

### `/speckit.sprint start` Integration
- Update roadmap when new sprint starts
- Move sprint from "Upcoming" to "Current"

### `/speckit.archive` Integration
- Update roadmap when sprint completes
- Move sprint from "Current" to "Completed"

### `/speckit.specify` Integration
- Add new features to backlog
- Update feature counts

## Notes

- Roadmap is living document - update regularly
- Roadmap shows high-level view, not detailed specs
- Use roadmap for stakeholder communication
- Update after each sprint completion
- Review and adjust upcoming sprints as needed

{SCRIPT}
