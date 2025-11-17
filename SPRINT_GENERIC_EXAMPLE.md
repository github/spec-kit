# Sprint/Cycle Management - Generic Example

This document provides a generic, reusable example of sprint/cycle management based on real-world project patterns. Use this as a template for any project type.

## Project Profile: Enterprise SaaS Application

**Domain**: Generic enterprise application  
**Team Size**: 3-5 developers  
**Duration**: 6 weeks across 4 sprints  
**Total Features**: 30+ features  

## Current State (Without Sprint Management)

Typical project structure:
- **30+ feature branches** (001-030+)
- **Individual feature specs** scattered across `specs/` directory
- **Ad-hoc completion notes** in some feature directories
- **No cross-feature visibility** or sprint tracking
- **No formal retrospectives** or decision archival
- **No project roadmap** or timeline view

### Common Pain Points

1. **Knowledge Fragmentation**: Decisions scattered across 30+ specs
2. **Onboarding Difficulty**: New team members must read all specs
3. **Progress Opacity**: Hard to explain what was done when
4. **Lost Context**: Why decisions were made is unclear months later
5. **No Learning Loop**: Same mistakes repeated across sprints
6. **Stakeholder Confusion**: No clear progress narrative

## Proposed State (With Sprint Management)

### Directory Structure

```
project-root/
├── memory/
│   └── constitution.md
├── sprints/
│   ├── active/
│   │   ├── sprint.md
│   │   ├── backlog.md
│   │   └── decisions.md
│   ├── archive/
│   │   ├── sprint-001-foundation/
│   │   ├── sprint-002-core-features/
│   │   ├── sprint-003-integration/
│   │   └── sprint-004-polish/
│   └── roadmap.md
└── specs/
    ├── 001-feature-name/
    └── ...
```

## Sprint Organization Pattern

### Sprint 001: Foundation (Week 1-2)
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

### Sprint 002: Core Features (Week 3-4)
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

### Sprint 003: Integration & Polish (Week 5)
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

### Sprint 004: Production Readiness (Week 6)
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

## Example Sprint Archive: Sprint 002

### Sprint 002 Summary: Core Features

**Duration**: Week 3-4 (10 working days)  
**Status**: Completed  
**Archived**: [DATE]

#### Executive Summary

Sprint 002 delivered the core user-facing functionality including user profiles, main dashboard, data entry workflows, search/filtering, notifications, file upload, data export, and audit logging. The sprint successfully implemented 8 features and established patterns for future development.

Key achievement: Implemented real-time notifications with email fallback, ensuring users stay informed of important events while maintaining system reliability.

Major pivot: Moved search from database queries to Elasticsearch mid-sprint after discovering performance issues with complex filters on large datasets.

#### Sprint Goal Achievement

**Original Goal**: Implement primary user-facing functionality to enable core workflows.

**Result**: ✅ Achieved

All 8 planned features completed. Search pivot improved performance by 10x. Notification system exceeded reliability targets.

#### Completed Features

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

#### Key Decisions

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

#### Pivots & Course Corrections

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

#### Sprint Metrics

- **Features Planned**: 8
- **Features Completed**: 8
- **Features Carried Over**: 0
- **Completion Rate**: 100%
- **Bugs Found**: 12
- **Bugs Fixed**: 12
- **Test Coverage**: 85%

#### Lessons Learned

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

#### Retrospective Highlights

**Top Insights**:
1. Performance testing with realistic data is critical
2. Simple MVP beats complex delayed feature
3. Good abstractions enable smooth pivots

**Experiments to Try**:
- Parallel implementation of cross-cutting concerns
- Performance testing in first 2 days of feature work
- "MVP definition" as required planning artifact

---

## Generic Decision Clarification Examples

### Example 1: Technology Choice

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

### Example 2: Architecture Pivot

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

### Example 3: Scope Reduction

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

## Generic Retrospective Template Usage

### Sprint Goal & Outcomes

**Q: Was the sprint goal achieved?**
- Listen for: Clear yes/no, explanation of gaps
- Follow-up: What would have helped achieve it fully?

**Q: What was the most valuable thing delivered?**
- Listen for: User impact, business value, technical foundation
- Follow-up: How do we deliver more of this value?

### Decision Clarification

**Q: Why did we choose [X] over [Y]?**
- Listen for: Constraints, trade-offs, information available
- Follow-up: Would we make the same choice again?

**Q: What information did we have when deciding?**
- Listen for: Known vs unknown factors, assumptions
- Follow-up: What would we have done with perfect information?

### Pivot Analysis

**Q: When did we realize we needed to pivot?**
- Listen for: Early warning signs, trigger events
- Follow-up: Could we have caught this earlier?

**Q: How did the pivot affect the sprint?**
- Listen for: Scope changes, team morale, technical debt
- Follow-up: What would we do differently?

### Process & Workflow

**Q: What worked well in our process?**
- Listen for: Specific practices, tools, communication
- Follow-up: How do we ensure we keep doing this?

**Q: What didn't work well?**
- Listen for: Bottlenecks, communication gaps, tool issues
- Follow-up: What's the root cause? How do we fix it?

---

## Benefits Demonstrated

### 1. Knowledge Preservation
**Before**: "Why did we choose Elasticsearch?" → Search through 30 specs  
**After**: Read Sprint 002 decisions.md → Clear answer with context

### 2. Onboarding
**Before**: New developer reads 30+ specs over 2 weeks  
**After**: New developer reads 4 sprint summaries in 2 hours, then dives into relevant specs

### 3. Stakeholder Communication
**Before**: "What did you do in October?" → Vague answer  
**After**: "Here's Sprint 002 summary" → Clear progress narrative

### 4. Decision Tracking
**Before**: "Why S3 instead of local storage?" → Lost in history  
**After**: Sprint 002 decisions.md documents rationale with full context

### 5. Continuous Improvement
**Before**: Same mistakes repeated (e.g., late performance testing)  
**After**: Action items from retrospectives prevent recurring issues

### 6. Pattern Recognition
**Before**: Hard to see patterns across features  
**After**: Retrospectives identify recurring issues (e.g., "we keep underestimating integration complexity")

---

## Conclusion

This generic example demonstrates how sprint/cycle management works for any project:

1. **Organize features into logical sprints** (foundation → core → integration → polish)
2. **Archive completed sprints** with high-level summaries
3. **Document decisions** with full context (why, not just what)
4. **Track pivots** and learn from them
5. **Conduct retrospectives** to clarify unclear decisions
6. **Generate action items** for continuous improvement

The pattern is universal - whether you're building a SaaS app, mobile app, data pipeline, or infrastructure project, the sprint/cycle management approach provides structure, visibility, and learning.

