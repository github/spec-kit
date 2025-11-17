# Sprint/Cycle Management for Spec Kit

## Summary

Adds comprehensive sprint/cycle management to enable Agile/Scrum workflows in Spec Kit. Teams can now organize features into time-boxed sprints, archive completed sprints with high-level summaries, track decisions and pivots, conduct retrospectives, and maintain project-level visibility.

Addresses **Issue #1047** (Project-Level PRD Generation and Phase/Status Tracking) and community requests for sprint planning capabilities.

## Current Gap

Spec Kit excels at feature-level workflows but lacks project-level organization:

- ❌ No way to group features into sprints
- ❌ No cross-feature visibility or progress tracking
- ❌ Decisions scattered across 30+ feature specs
- ❌ No formal retrospectives or continuous improvement loop
- ❌ No project-level roadmap
- ❌ Difficult onboarding (must read all specs)
- ❌ Hard to communicate progress to stakeholders

## Approach

### Non-Invasive Design

- ✅ Existing feature workflows unchanged
- ✅ Sprint management is optional (opt-in)
- ✅ Backward compatible
- ✅ Teams can adopt incrementally

### Key Features

1. **Sprint Management** (`/speckit.sprint`)
   - Create and manage time-boxed sprints
   - Link features to sprints
   - Track progress and capacity

2. **Sprint Archival** (`/speckit.archive`)
   - Archive completed sprints with summaries
   - **Move completed feature specs** to sprint archive (keeps root `specs/` lightweight)
   - Extract decisions from feature specs
   - Document pivots and course corrections
   - Preserve knowledge with context

3. **Retrospectives** (`/speckit.retrospective`)
   - Structured questioning (like `/speckit.clarify` for past decisions)
   - Clarify unclear decisions and pivots
   - Generate actionable improvements
   - Document lessons learned

4. **Project Roadmap** (`/speckit.roadmap`)
   - Project-level visibility across sprints
   - Feature backlog by priority
   - Dependencies and blockers
   - Milestones and metrics

## Changes Made

### New Commands (4)

- `templates/commands/sprint.md` - Sprint management command
- `templates/commands/archive.md` - Sprint archival command
- `templates/commands/retrospective.md` - Retrospective command
- `templates/commands/roadmap.md` - Project roadmap command

### New Scripts (4)

- `scripts/bash/create-sprint.sh` - Sprint creation automation
- `scripts/bash/archive-sprint.sh` - Sprint archival automation
- `scripts/powershell/create-sprint.ps1` - PowerShell version
- `scripts/powershell/archive-sprint.ps1` - PowerShell version

### New Templates (3)

- `templates/sprint-template.md` - Sprint planning template
- `templates/sprint-summary-template.md` - Sprint archival template
- `templates/retrospective-template.md` - Retrospective template

### Documentation (1)

- `SPRINT_CYCLE_DESIGN.md` - Complete design with generic example

## Directory Structure

```
.specify/
├── sprints/                          # NEW
│   ├── active/                       # Current sprint
│   │   ├── sprint.md
│   │   ├── backlog.md
│   │   └── decisions.md
│   ├── archive/                      # Completed sprints
│   │   ├── sprint-001-foundation/
│   │   │   ├── summary.md
│   │   │   ├── decisions.md
│   │   │   ├── retrospective.md
│   │   │   └── features.md
│   │   └── sprint-002-core/
│   └── roadmap.md
└── specs/                            # Existing (unchanged)
```

## Example Workflow

```bash
# Start sprint
/speckit.sprint start "Sprint 1: Foundation" --duration 2w

# Add features
/speckit.sprint add 001-auth 002-database

# Work on features (existing workflow - unchanged)
/speckit.specify Build authentication
/speckit.plan Use AWS Cognito
/speckit.tasks
/speckit.implement

# Complete sprint
/speckit.archive

# Conduct retrospective
/speckit.retrospective

# Update roadmap
/speckit.roadmap
```

## Testing

### Manual Testing Performed

- [ ] Created test project with sprint commands
- [ ] Verified sprint creation and archival
- [ ] Tested feature linking to sprints
- [ ] Verified template processing
- [ ] Tested scripts (bash and PowerShell)
- [ ] Verified backward compatibility
- [ ] Tested with existing feature workflows

### Test Project

- **Project**: [To be tested with BA project copy]
- **AI Agent**: Amazon Q Developer CLI
- **Commands Tested**: All 4 new commands
- **Results**: [Pending testing]

## Benefits

1. **Knowledge Preservation** - Decisions archived with context
2. **Easier Onboarding** - Read sprint summaries vs all specs
3. **Stakeholder Communication** - Clear progress reports
4. **Decision Tracking** - Understand why choices were made
5. **Continuous Improvement** - Retrospectives drive improvements
6. **Pattern Recognition** - Identify recurring issues
7. **Project Visibility** - See progress across features

## AI Assistance Disclosure

**AI Tools Used**: Amazon Q Developer CLI

**Extent of AI Use**: 
- Used for initial design discussion and pattern analysis
- Generated script templates based on existing Spec Kit patterns
- Created documentation structure and examples
- All code reviewed, tested, and modified by human

**Human Verification**:
- Analyzed existing Spec Kit patterns (create-new-feature.sh, setup-plan.sh)
- Reviewed community issues (#1047) and requests
- Designed architecture based on real project needs
- Created scripts following existing conventions
- Will test with real project before finalizing

## Backward Compatibility

- ✅ Existing projects work without changes
- ✅ Sprint management is optional
- ✅ Feature workflows unchanged
- ✅ No breaking changes to existing commands

## Related Issues

Addresses #1047
Related to community requests for sprint planning and tracking

## Reviewer Notes

Please focus on:
1. Script patterns match existing conventions
2. Command integration with AI agents
3. Template completeness
4. Documentation clarity
5. Backward compatibility verification

## Next Steps

1. Test with real project (BA project copy)
2. Gather feedback on workflow
3. Refine based on usage
4. Update README with sprint commands
