# Sprint/Cycle Management for Spec Kit

## Table of Contents

- [Overview](#overview)
- [Quick Summary](#quick-summary)
- [Key Principles](#key-principles)
- [Directory Structure](#directory-structure)
- [Commands](#commands)
- [Templates](#templates)
- [Generic Example](#generic-example)
- [Implementation Strategy](#implementation-strategy)
- [Integration with Existing Workflows](#integration-with-existing-workflows)
- [Benefits](#benefits)

---

## Overview

This design introduces sprint/cycle management to Spec Kit while preserving all existing feature-level workflows. It enables teams to:
- Group features into time-boxed sprints
- Archive completed sprints with high-level summaries
- Track decisions and pivots across cycles
- Conduct retrospectives to clarify unclear decisions
- Maintain project-level visibility

## Quick Summary

**What's Included:**
- 4 new commands: `/speckit.sprint`, `/speckit.archive`, `/speckit.retrospective`, `/speckit.roadmap`
- 3 new templates: sprint planning, sprint summary, retrospective
- Complete generic example with 4 sprints and 35 features
- Non-invasive: existing feature workflows unchanged

**Key Features:**
- ✅ Archive cycles with high-level summaries
- ✅ Highlight decisions with full context
- ✅ Document pivots (original → actual + lessons)
- ✅ Retrospective clarity (like `/speckit.clarify` for past decisions)
- ✅ Project visibility via roadmap

**Addresses:**
- Issue #1047: Project-Level PRD Generation and Phase/Status Tracking
- Community requests for sprint planning and tracking

---

## Key Principles

1. **Non-invasive**: Existing feature workflows remain unchanged
2. **Additive**: Sprint management is optional - teams can still work feature-by-feature
3. **Archival-first**: Completed sprints are archived with summaries, not deleted
4. **Decision-focused**: Captures why decisions were made, not just what was done
5. **Retrospective-driven**: Similar to `/speckit.clarify` but for understanding past decisions

---

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
│   │   ├── sprint-001-foundation/
│   │   │   ├── summary.md            # High-level summary
│   │   │   ├── decisions.md          # Key decisions & pivots
│   │   │   ├── retrospective.md      # Retrospective notes
│   │   │   └── features.md           # List of completed features
│   │   ├── sprint-002-core-features/
│   │   └── ...
│   └── roadmap.md                    # Project-level roadmap
├── specs/                            # Existing feature specs (unchanged)
│   ├── 001-feature-name/
│   └── ...
└── templates/
    ├── sprint-template.md            # NEW
    ├── sprint-summary-template.md    # NEW
    └── retrospective-template.md     # NEW
```

---

## Commands

### 1. `/speckit.sprint` - Sprint Planning & Management

**Purpose**: Create, manage, and track sprints

**Sub-commands**:

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

---

### 2. `/speckit.archive` - Sprint Archival

**Purpose**: Archive completed sprint and create summary

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

**Output Structure**:
```
sprints/archive/sprint-001-foundation/
├── summary.md         - Executive summary with decisions and pivots
├── decisions.md       - Key decisions with full context
├── features.md        - List of completed features with links
├── retrospective.md   - Retrospective template (run /speckit.retrospective to fill)
├── sprint.md          - Original sprint plan
├── backlog.md         - Original backlog
└── decisions.md       - Original decisions log
```

---

### 3. `/speckit.retrospective` - Sprint Retrospective

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

**Question Categories**:
1. Sprint goal & outcomes
2. Decision clarification
3. Pivot analysis
4. Process & workflow
5. Technical practices
6. Team health & morale

---

### 4. `/speckit.roadmap` - Project-Level Planning

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

**Roadmap Contents**:
- Project vision and goals
- Current sprint status
- Upcoming sprints (planned)
- Completed sprints (archived)
- Feature backlog by priority
- Dependencies and blockers
- Milestones and success metrics

---

## Generic Example

This section provides a complete, reusable example based on real-world project patterns. Use this as a template for any project type.

### Project Profile: Enterprise SaaS Application

**Domain**: Generic enterprise application  
**Team Size**: 3-5 developers  
**Duration**: 6 weeks across 4 sprints  
**Total Features**: 35 features  

### Sprint Organization Pattern

#### Sprint 001: Foundation (Week 1-2)
**Goal**: Establish technical foundation and core infrastructure

**Typical Features** (3-5 features):
- 001-project-setup - Initial project structure and tooling
- 002-authentication - User authentication system
- 003-authorization - Role-based access control
- 004-database-schema - Core data models
- 005-api-foundation - REST API infrastructure

**Common Decisions**:
- Technology stack selection (framework, database, cloud provider)
- Authentication approach (OAuth, OIDC, custom)
- API design patterns (REST, GraphQL)
- Database choice and schema design
- Deployment strategy

**Typical Pivots**:
- Auth provider change (e.g., custom → managed service)
- Database migration (e.g., SQL → NoSQL for specific use case)
- Framework version upgrade due to compatibility

**Success Criteria**:
- [ ] Users can authenticate
- [ ] Basic CRUD operations work
- [ ] API responds within SLA
- [ ] Database schema supports core entities

---

#### Sprint 002: Core Features (Week 3-4)
**Goal**: Implement primary user-facing functionality

**Typical Features** (5-8 features):
- 006-user-profile - User profile management
- 007-main-dashboard - Primary dashboard view
- 008-data-entry - Core data entry workflows
- 009-search-filter - Search and filtering
- 010-notifications - Notification system
- 011-file-upload - File upload and storage
- 012-data-export - Export functionality
- 013-audit-logging - Audit trail

**Common Decisions**:
- UI framework and component library
- State management approach
- File storage solution (S3, blob storage)
- Search implementation (database, Elasticsearch)
- Notification delivery (email, push, in-app)

**Typical Pivots**:
- UI framework change due to performance
- Search moved from database to dedicated service
- Notification strategy simplified for MVP

**Success Criteria**:
- [ ] Users can complete primary workflows
- [ ] Search returns results in < 1 second
- [ ] Files upload successfully
- [ ] Notifications delivered reliably

---

#### Sprint 003: Integration & Polish (Week 5)
**Goal**: Connect components and improve user experience

**Typical Features** (8-12 features):
- 014-ui-backend-integration - Connect frontend to backend
- 015-real-time-updates - WebSocket/polling for live updates
- 016-error-handling - Comprehensive error handling
- 017-loading-states - Loading indicators and skeletons
- 018-form-validation - Client and server validation
- 019-accessibility - WCAG compliance
- 020-responsive-design - Mobile responsiveness
- 021-performance-optimization - Performance tuning
- 022-caching - Caching strategy
- 023-monitoring - Observability and monitoring
- 024-security-hardening - Security improvements
- 025-documentation - User and API documentation

**Common Decisions**:
- Real-time vs polling trade-offs
- Caching strategy (client, server, CDN)
- Monitoring tools and metrics
- Accessibility compliance level
- Performance targets

**Typical Pivots**:
- Real-time moved to polling for simplicity
- Caching added earlier than planned due to performance
- Accessibility scope expanded for compliance

**Success Criteria**:
- [ ] All components integrated
- [ ] Page load time < 2 seconds
- [ ] WCAG 2.1 AA compliant
- [ ] Zero critical security issues
- [ ] Monitoring dashboards operational

---

#### Sprint 004: Production Readiness (Week 6)
**Goal**: Prepare for production deployment

**Typical Features** (5-10 features):
- 026-deployment-pipeline - CI/CD pipeline
- 027-backup-recovery - Backup and recovery procedures
- 028-disaster-recovery - DR plan and testing
- 029-load-testing - Performance and load testing
- 030-security-audit - Security audit and fixes
- 031-user-acceptance-testing - UAT with stakeholders
- 032-training-materials - User training content
- 033-runbook - Operational runbook
- 034-rollback-plan - Rollback procedures
- 035-go-live-checklist - Production launch checklist

**Common Decisions**:
- Deployment strategy (blue-green, canary, rolling)
- Backup frequency and retention
- DR RTO/RPO targets
- Load testing scenarios
- Go-live criteria

**Typical Pivots**:
- Deployment strategy simplified for first release
- DR scope reduced to essentials
- UAT timeline extended due to feedback

**Success Criteria**:
- [ ] Automated deployment works
- [ ] Backups tested and verified
- [ ] Load tests pass at 2x expected traffic
- [ ] Security audit complete
- [ ] Stakeholders approve for production

---

### Example Sprint Archive: Sprint 002

#### Sprint 002 Summary: Core Features

**Duration**: Week 3-4 (10 working days)  
**Status**: Completed  
**Archived**: [DATE]

##### Executive Summary

Sprint 002 delivered the core user-facing functionality including user profiles, main dashboard, data entry workflows, search/filtering, notifications, file upload, data export, and audit logging. The sprint successfully implemented 8 features and established patterns for future development.

Key achievement: Implemented real-time notifications with email fallback, ensuring users stay informed of important events while maintaining system reliability.

Major pivot: Moved search from database queries to Elasticsearch mid-sprint after discovering performance issues with complex filters on large datasets.

##### Sprint Goal Achievement

**Original Goal**: Implement primary user-facing functionality to enable core workflows.

**Result**: ✅ Achieved

All 8 planned features completed. Search pivot improved performance by 10x. Notification system exceeded reliability targets.

##### Completed Features

| Feature ID | Feature Name | Status | Notes |
|------------|--------------|--------|-------|
| 006 | User Profile Management | ✅ Complete | Added avatar upload |
| 007 | Main Dashboard | ✅ Complete | Responsive design |
| 008 | Data Entry Workflows | ✅ Complete | Multi-step forms |
| 009 | Search & Filtering | ✅ Complete | Pivoted to Elasticsearch |
| 010 | Notification System | ✅ Complete | Email + in-app |
| 011 | File Upload | ✅ Complete | S3 integration |
| 012 | Data Export | ✅ Complete | CSV and JSON formats |
| 013 | Audit Logging | ✅ Complete | Comprehensive tracking |

##### Key Decisions

**Decision 1: Elasticsearch for Search**
- **Context**: Database queries for complex filters were taking 5-10 seconds on test data
- **Options**: 
  1. Optimize database queries - estimated 2-3 days, uncertain outcome
  2. Add Elasticsearch - 1 day setup, proven performance
- **Decision**: Elasticsearch
- **Rationale**: Proven solution, better long-term scalability, acceptable setup cost
- **Impact**: Search now responds in < 200ms, supports complex filters, enables future features like fuzzy search

**Decision 2: Email + In-App Notifications**
- **Context**: Users needed to be notified of important events
- **Options**:
  1. Email only - simple but users might miss notifications
  2. In-app only - requires users to be logged in
  3. Both - more complex but comprehensive
- **Decision**: Both email and in-app
- **Rationale**: Critical notifications via email, convenience notifications in-app
- **Impact**: 95% notification delivery rate, positive user feedback

**Decision 3: S3 for File Storage**
- **Context**: Need reliable, scalable file storage
- **Options**:
  1. Local filesystem - simple but not scalable
  2. Database blobs - simple but performance issues
  3. S3 - more setup but industry standard
- **Decision**: S3
- **Rationale**: Scalable, reliable, cost-effective, integrates with CDN
- **Impact**: Handles files up to 5GB, automatic backups, CDN-ready

##### Pivots & Course Corrections

**Pivot 1: Database → Elasticsearch for Search**
- **Original Plan**: Use database with optimized queries and indexes
- **Change**: Implemented Elasticsearch for search functionality
- **Reason**: Performance testing revealed database queries taking 5-10 seconds with realistic data volumes. Elasticsearch reduced this to < 200ms.
- **Outcome**: Better performance, more features (fuzzy search, faceting), happier users
- **Lessons**: Performance test with realistic data early; don't optimize prematurely but be ready to pivot

**Pivot 2: Simplified Notification UI**
- **Original Plan**: Rich notification center with categories, filters, and mark-as-read
- **Change**: Simple notification list with basic mark-as-read
- **Reason**: Complex UI was taking too long; users just wanted to see notifications
- **Outcome**: Shipped on time, users satisfied with simple version
- **Lessons**: MVP first, add complexity based on user feedback

##### Sprint Metrics

- **Features Planned**: 8
- **Features Completed**: 8
- **Completion Rate**: 100%
- **Bugs Found**: 12
- **Bugs Fixed**: 12
- **Test Coverage**: 85%

##### Lessons Learned

**What Went Well**:
1. Early performance testing caught search issues before production
2. Elasticsearch pivot was smooth due to good abstraction layer
3. Notification system design allowed easy addition of new channels
4. File upload with S3 was straightforward with good documentation

**What Could Be Improved**:
1. Should have load-tested search earlier in sprint
2. Notification UI scope should have been clearer upfront
3. File upload error handling needed more edge case testing
4. Audit logging added late, should have been parallel with features

**Action Items for Next Sprint**:
- [ ] Add performance testing to sprint planning checklist
- [ ] Define MVP vs full scope for each feature upfront
- [ ] Build error handling and edge cases into initial estimates
- [ ] Start cross-cutting concerns (logging, monitoring) earlier

---

### Decision Clarification Examples

#### Example 1: Technology Choice

**Decision: Why did we choose [Framework X] over [Framework Y]?**

**Clarifying Questions**:
1. **Q: What were the key factors in this decision?**
   - A: Team familiarity, community support, performance, ecosystem
   
2. **Q: What information did we have at the time?**
   - A: Framework X had 3 team members with experience, Y had none. X had larger community and more libraries.
   
3. **Q: What were the trade-offs?**
   - A: X was more opinionated (less flexibility) but faster to develop. Y was more flexible but steeper learning curve.
   
4. **Q: Would we make the same choice again?**
   - A: Yes. Team productivity was higher than expected. The opinionated nature actually helped maintain consistency.

**Lessons**: Team familiarity and productivity matter more than theoretical flexibility for most projects.

---

#### Example 2: Architecture Pivot

**Decision: Why did we pivot from [Architecture A] to [Architecture B]?**

**Clarifying Questions**:
1. **Q: When did we realize we needed to pivot?**
   - A: Day 3 of sprint, during performance testing with realistic data volumes
   
2. **Q: What triggered the pivot?**
   - A: Database queries taking 5-10 seconds, well above our 1-second SLA
   
3. **Q: What alternatives did we consider?**
   - A: Query optimization (uncertain outcome), caching (band-aid), Elasticsearch (proven solution)
   
4. **Q: How did we minimize disruption?**
   - A: Good abstraction layer meant we only changed the search service implementation, not the API

**Lessons**: Good abstractions enable pivots. Performance test early with realistic data.

---

#### Example 3: Scope Reduction

**Decision: Why did we reduce scope for [Feature X]?**

**Clarifying Questions**:
1. **Q: What was the original scope?**
   - A: Rich notification center with categories, filters, search, and advanced settings
   
2. **Q: What did we actually ship?**
   - A: Simple notification list with mark-as-read
   
3. **Q: Why the reduction?**
   - A: Complex UI was taking 3x longer than estimated. Users just wanted to see notifications.
   
4. **Q: Were users satisfied?**
   - A: Yes. Post-launch feedback showed simple version met their needs. No requests for advanced features yet.

**Lessons**: MVP first. Add complexity only when users request it.

---

### Benefits Demonstrated

#### 1. Knowledge Preservation
**Before**: "Why did we choose Elasticsearch?" → Search through 30 specs  
**After**: Read Sprint 002 decisions.md → Clear answer with context

#### 2. Onboarding
**Before**: New developer reads 30+ specs over 2 weeks  
**After**: New developer reads 4 sprint summaries in 2 hours, then dives into relevant specs

#### 3. Stakeholder Communication
**Before**: "What did you do in October?" → Vague answer  
**After**: "Here's Sprint 002 summary" → Clear progress narrative

#### 4. Decision Tracking
**Before**: "Why S3 instead of local storage?" → Lost in history  
**After**: Sprint 002 decisions.md documents rationale with full context

#### 5. Continuous Improvement
**Before**: Same mistakes repeated (e.g., late performance testing)  
**After**: Action items from retrospectives prevent recurring issues

#### 6. Pattern Recognition
**Before**: Hard to see patterns across features  
**After**: Retrospectives identify recurring issues (e.g., "we keep underestimating integration complexity")

---

## Templates

### Sprint Template (`sprint-template.md`)

Complete sprint planning template with:
- Sprint goals and success criteria
- Feature backlog and priorities
- Dependencies and risks
- Daily progress tracking
- Decision documentation
- Pivot tracking
- Sprint metrics

### Sprint Summary Template (`sprint-summary-template.md`)

Archival summary template with:
- Executive summary
- Goal achievement analysis
- Completed features list
- Key decisions with full context
- Pivots and course corrections
- Sprint metrics
- Lessons learned
- Technical artifacts
- Impact and value delivered
- Next sprint preview

### Retrospective Template (`retrospective-template.md`)

Structured retrospective template with:
- What went well / what could improve
- Decision clarifications (similar to `/speckit.clarify`)
- Pivot analysis
- Process and technical practice evaluation
- Action items with owners
- Experiments to try
- Team health and morale
- Appreciation and recognition

---

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

---

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

---

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

---

## Benefits

### 1. Project Visibility
See progress across multiple features at sprint and project level

### 2. Decision Tracking
Understand why choices were made with full context preserved

### 3. Knowledge Preservation
Archive maintains institutional knowledge across team changes

### 4. Continuous Improvement
Retrospectives drive process improvements sprint over sprint

### 5. Team Coordination
Sprint planning aligns team efforts and manages capacity

### 6. Stakeholder Communication
Summaries provide clear status updates for non-technical audiences

### 7. Pattern Recognition
Identify recurring issues and successful practices across sprints

### 8. Onboarding Efficiency
New team members read sprint summaries instead of all feature specs

---

## Backward Compatibility

- Existing projects continue to work without sprints
- Sprint management is opt-in
- Feature-level workflows unchanged
- No breaking changes to existing commands
- Teams can adopt incrementally

---

## Future Enhancements

- Sprint velocity tracking and burndown charts
- Cross-sprint dependency visualization
- Integration with GitHub Projects/Issues
- Automated sprint reports and metrics
- Sprint templates for common patterns (MVP sprint, polish sprint, etc.)
- Multi-team sprint coordination
- Sprint comparison and trend analysis

---

## Reusable for Any Project Type

This sprint/cycle management approach works for:

- ✓ SaaS Applications - Web-based enterprise software
- ✓ Mobile Apps - iOS, Android, cross-platform
- ✓ Data Pipelines - ETL, data processing, analytics
- ✓ Infrastructure Projects - Cloud, DevOps, platform engineering
- ✓ Internal Tools - Admin dashboards, automation
- ✓ Customer-facing Products - E-commerce, portals, services

The patterns are universal - only the specifics change!

---

## Conclusion

This sprint/cycle management design adds project-level visibility and knowledge preservation to Spec Kit while maintaining all the great feature-level workflows. Teams can:

1. **Organize features into logical sprints** (foundation → core → integration → polish)
2. **Archive completed sprints** with high-level summaries
3. **Document decisions** with full context (why, not just what)
4. **Track pivots** and learn from them
5. **Conduct retrospectives** to clarify unclear decisions
6. **Generate action items** for continuous improvement
7. **Maintain roadmap** for project-level visibility

The approach is non-invasive, backward compatible, and provides immediate value for teams practicing Agile/Scrum methodologies.
