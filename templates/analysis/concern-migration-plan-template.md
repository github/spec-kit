# Migration Plan: <<CONCERN_TYPE>>

**Project**: <<PROJECT_NAME>>
**Migration**: <<CURRENT_IMPLEMENTATION>> → <<TARGET_IMPLEMENTATION>>
**Strategy**: <<STRANGLER_FIG / ADAPTER_PATTERN / REFACTOR_FIRST / BIG_BANG_WITH_FEATURE_FLAGS>>
**Plan Date**: <<DATE>>
**Estimated Timeline**: <<Total weeks, e.g., "8-12 weeks">>
**Risk Level**: <<LOW / MEDIUM / HIGH>>

---

## Executive Summary

**What**: Migrate <<CONCERN_TYPE>> from <<CURRENT_IMPLEMENTATION>> to <<TARGET_IMPLEMENTATION>>

**Why**: <<Business justification for migration>>

**How**: Using <<STRATEGY>> pattern with phased rollout (50/30/15/5 value delivery)

**When**: <<Proposed start date>> to <<Proposed end date>>

**Who**:
- **Technical Lead**: <<TBD>>
- **Implementation Team**: <<TBD>>
- **QA/Testing**: <<TBD>>
- **Stakeholder/Approver**: <<TBD>>

**Risk Level**: <<LOW / MEDIUM / HIGH>>

**Confidence**: <<0-100%>> confidence in estimates

---

## Migration Strategy: <<STRATEGY>>

<<IF STRATEGY = STRANGLER_FIG>>

### STRANGLER_FIG Pattern

**Description**: Gradually replace the old implementation with the new one by running both side-by-side and incrementally migrating consumers.

**Why This Strategy**:
- ✅ High abstraction level detected - easy to swap implementations
- ✅ Loose coupling - minimal impact on consumers
- ✅ Low risk - can roll back individual consumers if issues arise
- ✅ Business continuity - no downtime required

**How It Works**:
1. Implement new <<TARGET_IMPLEMENTATION>> provider alongside existing <<CURRENT_IMPLEMENTATION>>
2. Add feature flag to control which provider is used
3. Gradually migrate consumers from old to new provider
4. Monitor each migration wave for issues
5. Roll back individual consumers if problems detected
6. Once all consumers migrated, decommission old provider

**Key Requirements**:
- Interface/contract: <<IInterfaceName>> at <<file:line>>
- Feature flag system: <<Recommended tool/approach>>
- Monitoring: Track success rates for old vs. new provider

**Timeline**: 2-4 weeks (if abstractions in place)

---

<<ELSE IF STRATEGY = ADAPTER_PATTERN>>

### ADAPTER_PATTERN

**Description**: Create an adapter layer that wraps the new implementation behind the existing interface, allowing gradual internal migration without changing consumers.

**Why This Strategy**:
- ⚠️ Medium abstraction level - some refactoring needed
- ⚠️ Moderate coupling - adapter isolates impact
- ⚠️ Medium risk - adapter tested independently before rollout

**How It Works**:
1. Create adapter interface matching current API
2. Implement adapter wrapping <<TARGET_IMPLEMENTATION>>
3. Replace current implementation with adapter (single swap)
4. Consumers unchanged (call same API, new implementation underneath)
5. Monitor adapter for performance/correctness
6. Once stable, optionally refactor consumers to use new API directly

**Key Requirements**:
- Adapter interface design
- Backward compatibility testing
- Performance benchmarking (adapter overhead)

**Timeline**: 4-8 weeks

---

<<ELSE IF STRATEGY = REFACTOR_FIRST>>

### REFACTOR_FIRST Pattern

**Description**: First refactor to introduce proper abstractions, then migrate using STRANGLER_FIG or ADAPTER_PATTERN.

**Why This Strategy**:
- ❌ Low abstraction level detected - direct migration too risky
- ❌ High coupling - must decouple before migrating
- ⚠️ Small blast radius (<20% codebase) - refactoring feasible

**How It Works**:
1. **Phase 1 (Weeks 1-4)**: Refactoring
   - Extract interfaces/contracts
   - Implement dependency injection
   - Externalize configuration
   - Wrap current implementation in provider pattern
2. **Phase 2 (Weeks 5-12)**: Migration
   - Implement new <<TARGET_IMPLEMENTATION>> provider
   - Use STRANGLER_FIG to migrate consumers
   - Monitor and validate

**Key Requirements**:
- Team buy-in for refactoring investment
- Comprehensive testing during refactoring
- No functionality changes during Phase 1 (pure refactoring)

**Timeline**: 6-12 weeks (2-4 weeks refactoring + 4-8 weeks migration)

---

<<ELSE IF STRATEGY = BIG_BANG_WITH_FEATURE_FLAGS>>

### BIG_BANG_WITH_FEATURE_FLAGS

**Description**: Complete migration in one large change, but use feature flags for gradual rollout to mitigate risk.

**Why This Strategy**:
- ❌ Low abstraction + large blast radius (>25% codebase)
- ❌ Tight coupling - piecemeal migration not feasible
- ⚠️ High risk - requires extensive testing and careful rollout

**How It Works**:
1. **Phase 1 (Weeks 1-8)**: Implementation
   - Implement new <<TARGET_IMPLEMENTATION>> throughout codebase
   - Add feature flags at critical decision points
   - Build comprehensive test suite
2. **Phase 2 (Weeks 9-16)**: Gradual Rollout
   - Week 9-10: Internal/dev team only (1% traffic)
   - Week 11-12: Beta users (10% traffic)
   - Week 13-14: Expanded rollout (50% traffic)
   - Week 15-16: Full rollout (100% traffic)
3. **Phase 3**: Monitoring and stabilization

**Key Requirements**:
- Feature flag infrastructure
- Extensive testing (unit, integration, E2E, load)
- Monitoring and alerting
- Rollback plan for each rollout phase

**Timeline**: 3-6 months

---

<<END IF>>

---

## Phase-Based Implementation (50/30/15/5 Value Delivery)

### Phase 1: Core Migration (50% Business Value)

**Timeline**: <<Weeks X-Y>>

**Goal**: Migrate the most critical functionality that delivers majority of business value.

**Scope**:
<<List core functionality to migrate first>>:
- [ ] <<Critical feature 1, e.g., "User login authentication">>
- [ ] <<Critical feature 2, e.g., "API token validation">>
- [ ] <<Critical feature 3>>
- ... (focus on high-value, high-usage features)

**Deliverables**:
1. **Implementation**:
   - [ ] <<TARGET_IMPLEMENTATION>> provider implemented: <<file:line>>
   - [ ] Core integration completed
   - [ ] Configuration setup (dev/staging/prod)

2. **Testing**:
   - [ ] Unit tests: <<X>> tests, <<Y%>> coverage
   - [ ] Integration tests: <<Z>> critical paths tested
   - [ ] E2E tests: <<Core user journeys>>

3. **Deployment**:
   - [ ] Deployed to dev environment
   - [ ] Deployed to staging environment
   - [ ] Internal testing complete
   - [ ] Feature flag: <<flagName>> = true for internal users

**Success Criteria**:
- ✅ Core functionality working in staging
- ✅ All tests passing
- ✅ Performance benchmarks met or exceeded
- ✅ Zero critical bugs in staging for 1 week

**Validation**:
- [ ] <<Metric 1, e.g., "Login success rate ≥ 99.9%">>
- [ ] <<Metric 2, e.g., "Auth latency < 100ms p95">>
- [ ] <<Metric 3>>

**Business Value Delivered**: <<Describe what users/business get from Phase 1>>

**Rollback Plan**: <<How to revert Phase 1 if issues arise>>

---

### Phase 2: Extended Features (30% Business Value)

**Timeline**: <<Weeks X-Y>>

**Goal**: Migrate additional features that provide substantial but secondary value.

**Scope**:
<<List extended functionality>>:
- [ ] <<Extended feature 1>>
- [ ] <<Extended feature 2>>
- [ ] <<Extended feature 3>>
- ... (important but not critical features)

**Deliverables**:
1. **Implementation**:
   - [ ] Extended <<TARGET_IMPLEMENTATION>> integrations
   - [ ] Additional configurations
   - [ ] Edge case handling

2. **Testing**:
   - [ ] Extended test coverage to <<Y+10%>>
   - [ ] Additional E2E scenarios
   - [ ] Load testing under production-like conditions

3. **Deployment**:
   - [ ] Beta user rollout (10-25% of production traffic)
   - [ ] Feature flag: <<flagName>> = true for beta cohort
   - [ ] Monitoring dashboards active

**Success Criteria**:
- ✅ Extended features working in production (beta)
- ✅ No increase in error rates
- ✅ Beta user feedback positive
- ✅ Performance stable under load

**Validation**:
- [ ] <<Metric 1>>
- [ ] <<Metric 2>>
- [ ] User feedback score ≥ <<threshold>>

**Business Value Delivered**: <<Describe Phase 2 value>>

**Rollback Plan**: <<How to revert Phase 2>>

---

### Phase 3: Remaining Features (15% Business Value)

**Timeline**: <<Weeks X-Y>>

**Goal**: Complete migration of less frequently used features.

**Scope**:
<<List remaining functionality>>:
- [ ] <<Remaining feature 1>>
- [ ] <<Remaining feature 2>>
- [ ] <<Admin/internal tools>>
- ... (low-frequency, specialized features)

**Deliverables**:
1. **Implementation**:
   - [ ] All remaining integrations complete
   - [ ] Comprehensive configuration options
   - [ ] Documentation updated

2. **Testing**:
   - [ ] Full test coverage (target: <<95%>>)
   - [ ] Chaos testing / fault injection
   - [ ] Security penetration testing

3. **Deployment**:
   - [ ] Expanded rollout (50-75% of production traffic)
   - [ ] Feature flag: <<flagName>> = true for expanded cohort

**Success Criteria**:
- ✅ All features migrated
- ✅ Production metrics stable
- ✅ No critical bugs for 2 weeks

**Validation**:
- [ ] <<All metrics from Phase 1 & 2 still met>>
- [ ] <<Additional validation for remaining features>>

**Business Value Delivered**: <<Describe Phase 3 value>>

**Rollback Plan**: <<How to revert Phase 3>>

---

### Phase 4: Polish & Optimization (5% Business Value)

**Timeline**: <<Weeks X-Y>>

**Goal**: Finalize migration, optimize performance, decommission old implementation.

**Scope**:
- [ ] Performance tuning
- [ ] Cost optimization
- [ ] Documentation finalization
- [ ] Team training
- [ ] Decommission old <<CURRENT_IMPLEMENTATION>>

**Deliverables**:
1. **Optimization**:
   - [ ] Performance benchmarks documented
   - [ ] Cost analysis (old vs. new)
   - [ ] Configuration tuned for production

2. **Documentation**:
   - [ ] User documentation updated
   - [ ] Developer documentation (API, config, troubleshooting)
   - [ ] Runbook for operations team
   - [ ] Architecture Decision Record (ADR)

3. **Deployment**:
   - [ ] 100% production traffic on new implementation
   - [ ] Feature flag: <<flagName>> = true globally
   - [ ] Old implementation decommissioned
   - [ ] Feature flag removed (cleanup)

4. **Training**:
   - [ ] Development team trained on new implementation
   - [ ] Operations team trained on monitoring/troubleshooting
   - [ ] Support team aware of changes

**Success Criteria**:
- ✅ 100% traffic migrated
- ✅ Old implementation removed
- ✅ Team trained and confident
- ✅ Documentation complete

**Validation**:
- [ ] Cost savings achieved: <<$ or % reduction>>
- [ ] Performance improvement: <<X% faster / more reliable>>
- [ ] Team satisfaction survey ≥ <<threshold>>

**Business Value Delivered**: <<Describe Phase 4 value - usually long-term maintainability>>

---

## Detailed Implementation Steps

### Pre-Migration Preparation

**Week 0 (Before Migration Starts)**:

1. **Environment Setup**:
   - [ ] Provision <<TARGET_IMPLEMENTATION>> accounts/resources
   - [ ] Configure dev environment
   - [ ] Configure staging environment
   - [ ] Configure production environment (ready but inactive)

2. **Team Preparation**:
   - [ ] Assign roles and responsibilities
   - [ ] Schedule kickoff meeting
   - [ ] Review migration plan with all stakeholders
   - [ ] Set up communication channels (Slack, email list, etc.)

3. **Tooling Setup**:
   - [ ] Feature flag system configured: <<tool/approach>>
   - [ ] Monitoring dashboards created: <<tool/dashboards>>
   - [ ] Alerting rules configured
   - [ ] Logging infrastructure ready

4. **Baseline Metrics**:
   - [ ] Capture current performance: <<metrics>>
   - [ ] Capture current error rates: <<metrics>>
   - [ ] Capture current costs: <<$$/month>>
   - [ ] Document SLAs/SLOs: <<targets>>

**Sign-off Required**: [ ] Technical Lead, [ ] Product Owner, [ ] Operations Lead

---

### Week-by-Week Execution Plan

<<IF STRATEGY = STRANGLER_FIG>>

**Week 1-2: Implement New Provider**
- [ ] Day 1-2: Set up <<TARGET_IMPLEMENTATION>> SDK/libraries
- [ ] Day 3-5: Implement <<IInterfaceName>> using <<TARGET_IMPLEMENTATION>>
- [ ] Day 6-8: Unit tests for new provider (target: 90% coverage)
- [ ] Day 9-10: Integration tests with mock services

**Week 3: Feature Flag Integration**
- [ ] Day 1-2: Add feature flag: `use_<<target>>_<<concern>>`
- [ ] Day 3-4: Update DI container to resolve based on flag
- [ ] Day 5: Test flag toggling in dev environment

**Week 4-6: Gradual Migration (Phase 1)**
- [ ] Week 4: Internal users only (1% traffic)
- [ ] Week 5: Beta cohort (10% traffic)
- [ ] Week 6: Expanded rollout (50% traffic)
- [ ] Monitor metrics daily, rollback if issues

**Week 7-8: Full Rollout & Cleanup**
- [ ] Week 7: 100% traffic to new provider
- [ ] Week 8: Decommission old provider, remove feature flag

<<ELSE IF STRATEGY = ADAPTER_PATTERN>>

**Week 1-3: Adapter Design & Implementation**
- [ ] Week 1: Design adapter interface
- [ ] Week 2: Implement adapter wrapping <<TARGET_IMPLEMENTATION>>
- [ ] Week 3: Unit + integration tests

**Week 4-5: Adapter Testing**
- [ ] Week 4: Staging deployment, load testing
- [ ] Week 5: Fix issues, performance tuning

**Week 6-8: Production Rollout**
- [ ] Week 6: Canary deployment (5-10% traffic)
- [ ] Week 7: Expanded rollout (50% traffic)
- [ ] Week 8: Full rollout (100% traffic)

<<ELSE IF STRATEGY = REFACTOR_FIRST>>

**Week 1-4: Refactoring Phase**
- [ ] Week 1-2: Extract interfaces, implement DI
- [ ] Week 3: Wrap current implementation in provider pattern
- [ ] Week 4: Testing and validation (no functionality changes)

**Week 5-12: Migration Phase**
- [ ] Week 5-6: Implement new provider
- [ ] Week 7-10: Gradual migration (STRANGLER_FIG)
- [ ] Week 11-12: Full rollout and cleanup

<<ELSE IF STRATEGY = BIG_BANG_WITH_FEATURE_FLAGS>>

**Week 1-8: Implementation Phase**
- [ ] Week 1-2: Implement <<TARGET_IMPLEMENTATION>> in all consumers
- [ ] Week 3-4: Add feature flags at decision points
- [ ] Week 5-6: Comprehensive testing (unit, integration, E2E)
- [ ] Week 7-8: Load testing, security testing, bug fixes

**Week 9-16: Gradual Rollout Phase**
- [ ] Week 9-10: Internal/dev (1% traffic)
- [ ] Week 11-12: Beta users (10% traffic)
- [ ] Week 13-14: Expanded (50% traffic)
- [ ] Week 15-16: Full rollout (100% traffic)

**Week 17-20: Stabilization & Cleanup**
- [ ] Week 17-18: Monitor production, fix issues
- [ ] Week 19: Decommission old implementation
- [ ] Week 20: Remove feature flags, final cleanup

<<END IF>>

---

## Risk Management

### Identified Risks

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
|---------|------------------|-------------|--------|---------------------|-------|
| R1 | <<e.g., "Breaking authentication for existing users">> | HIGH / MEDIUM / LOW | HIGH / MEDIUM / LOW | <<Strategy>> | <<TBD>> |
| R2 | <<e.g., "Performance degradation during migration">> | MEDIUM | MEDIUM | <<Strategy>> | <<TBD>> |
| R3 | <<e.g., "Cost overruns for new service">> | LOW | MEDIUM | <<Strategy>> | <<TBD>> |
| ... | ... | ... | ... | ... | ... |

### Risk Mitigation Details

**R1: <<Risk Description>>**
- **Mitigation**:
  - [ ] <<Action 1>>
  - [ ] <<Action 2>>
- **Contingency**: <<What to do if risk materializes>>
- **Monitoring**: <<How to detect early>>

**R2: <<Risk Description>>**
- **Mitigation**:
  - [ ] <<Action 1>>
  - [ ] <<Action 2>>
- **Contingency**: <<Contingency plan>>
- **Monitoring**: <<Detection strategy>>

<<Continue for all risks>>

---

## Testing Strategy

### Test Pyramid

**Unit Tests**:
- **Target Coverage**: <<90%>> for new provider code
- **Focus Areas**:
  - [ ] Core <<TARGET_IMPLEMENTATION>> integration
  - [ ] Error handling and edge cases
  - [ ] Configuration variations
- **Tools**: <<Jest, JUnit, pytest, etc.>>

**Integration Tests**:
- **Target Coverage**: All critical integration points
- **Focus Areas**:
  - [ ] New provider ↔ Business logic integration
  - [ ] Configuration loading and validation
  - [ ] External service communication (<<TARGET_IMPLEMENTATION>>)
- **Tools**: <<Testing framework + test containers/mocks>>

**End-to-End Tests**:
- **Target Coverage**: All critical user journeys
- **Critical Paths to Test**:
  - [ ] <<User journey 1, e.g., "User login flow">>
  - [ ] <<User journey 2, e.g., "API authentication">>
  - [ ] <<User journey 3>>
- **Tools**: <<Selenium, Cypress, Playwright, etc.>>

**Performance Tests**:
- **Baseline**: <<Current performance metrics>>
- **Target**: <<Performance goals>>
- **Test Scenarios**:
  - [ ] Normal load: <<X requests/second>>
  - [ ] Peak load: <<Y requests/second>>
  - [ ] Stress test: <<Z requests/second>>
- **Tools**: <<k6, JMeter, Gatling, etc.>>

**Security Tests**:
- [ ] Penetration testing
- [ ] Vulnerability scanning
- [ ] Auth/authz validation
- [ ] Data encryption verification
- **Tools**: <<OWASP ZAP, Burp Suite, etc.>>

### Testing Timeline

| Week | Test Type | Environment | Pass Criteria |
|------|-----------|-------------|---------------|
| 1-2 | Unit | Dev | 90% coverage, all tests pass |
| 3 | Integration | Dev | All critical paths pass |
| 4 | E2E | Staging | All user journeys pass |
| 5 | Performance | Staging | Meets or exceeds baseline |
| 6 | Security | Staging | No critical/high vulnerabilities |
| 7+ | Production Validation | Production | Metrics stable, no regressions |

---

## Monitoring & Validation

### Key Metrics to Monitor

**Business Metrics**:
- **<<Metric 1>>**: <<e.g., "Login success rate">>
  - Current: <<baseline>>
  - Target: <<goal>>
  - Alert threshold: <<when to alert>>
- **<<Metric 2>>**: <<e.g., "API request success rate">>
  - Current: <<baseline>>
  - Target: <<goal>>
  - Alert threshold: <<threshold>>

**Technical Metrics**:
- **Latency (p50, p95, p99)**:
  - Current: <<ms>>
  - Target: <<ms>>
- **Error Rate**:
  - Current: <<X%>>
  - Target: <<Y%>>
- **Throughput**:
  - Current: <<requests/sec>>
  - Target: <<requests/sec>>

**Cost Metrics**:
- **Monthly Cost**:
  - Current (<<CURRENT_IMPLEMENTATION>>): <<$$/month>>
  - Projected (<<TARGET_IMPLEMENTATION>>): <<$$/month>>
  - Target savings: <<$$ or %>>, or acceptable increase: <<$$>>

### Dashboards

**Dashboard 1: Migration Progress**
- Percentage of traffic on new vs. old implementation
- Feature flag status across environments
- Migration phase status

**Dashboard 2: Health Metrics**
- Error rates (old vs. new)
- Latency comparisons (old vs. new)
- Throughput and capacity

**Dashboard 3: Business Impact**
- User-facing metrics (login success, API calls, etc.)
- Business KPIs affected by this concern

**Tools**: <<Grafana, DataDog, New Relic, CloudWatch, etc.>>

### Alerting Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| <<Alert 1>> | <<e.g., "Error rate > 1%">> | CRITICAL | Rollback immediately |
| <<Alert 2>> | <<e.g., "Latency p95 > 500ms">> | HIGH | Investigate, prepare rollback |
| <<Alert 3>> | <<e.g., "Cost > $X/day">> | MEDIUM | Optimize configuration |

---

## Rollback Plan

### Rollback Triggers

**Immediate Rollback** (within minutes):
- ❌ Error rate > <<X%>> for <<Y>> minutes
- ❌ Critical functionality broken
- ❌ Data integrity issues detected
- ❌ Security vulnerability discovered

**Planned Rollback** (within hours/days):
- ⚠️ Performance degradation > <<X%>>
- ⚠️ Cost overruns > <<$$ or %>>
- ⚠️ User complaints > <<threshold>>

### Rollback Procedures

**For STRANGLER_FIG / ADAPTER_PATTERN / BIG_BANG_WITH_FEATURE_FLAGS**:

**Step 1: Feature Flag Toggle** (< 5 minutes)
- [ ] Set feature flag `<<flagName>>` to `false` (revert to old implementation)
- [ ] Verify rollback via monitoring dashboards
- [ ] Confirm error rate returns to normal

**Step 2: Communication** (< 15 minutes)
- [ ] Notify team via <<Slack/Teams/email>>
- [ ] Update status page if user-facing
- [ ] Log incident for post-mortem

**Step 3: Root Cause Analysis** (hours-days)
- [ ] Investigate what went wrong
- [ ] Document findings
- [ ] Plan remediation

**Step 4: Retry** (when ready)
- [ ] Fix root cause
- [ ] Re-test in staging
- [ ] Retry migration with fixes

**For REFACTOR_FIRST**:

**During Refactoring Phase (Weeks 1-4)**:
- Rollback = revert Git commits (functionality unchanged)
- Run full test suite to verify
- Should be low risk (no functionality changes during refactoring)

**During Migration Phase (Weeks 5+)**:
- Same as STRANGLER_FIG rollback above

### Rollback Testing

- [ ] Test rollback procedure in dev environment
- [ ] Test rollback procedure in staging environment
- [ ] Document rollback time: <<X>> minutes
- [ ] Ensure team knows rollback steps

---

## Success Criteria

### Phase 1 Success Criteria

- [ ] Core functionality (50% value) migrated and stable
- [ ] All Phase 1 tests passing
- [ ] Performance ≥ baseline
- [ ] Error rate ≤ baseline
- [ ] Staging environment stable for 1 week
- [ ] Internal users validated in production

### Phase 2 Success Criteria

- [ ] Extended functionality (30% value) migrated and stable
- [ ] Beta users validated in production
- [ ] No increase in error rates
- [ ] Performance remains stable under load
- [ ] Beta feedback positive

### Phase 3 Success Criteria

- [ ] All functionality (100%) migrated
- [ ] 50-75% of production traffic migrated
- [ ] All tests passing (95% coverage)
- [ ] Production metrics stable for 2 weeks

### Phase 4 Success Criteria

- [ ] 100% production traffic on new implementation
- [ ] Old implementation decommissioned
- [ ] Feature flags removed (cleanup complete)
- [ ] Documentation complete
- [ ] Team trained
- [ ] Cost targets met
- [ ] Performance targets met

### Overall Migration Success

**The migration is considered successful when**:
- ✅ 100% of functionality migrated to <<TARGET_IMPLEMENTATION>>
- ✅ Old <<CURRENT_IMPLEMENTATION>> decommissioned
- ✅ All success criteria met (performance, cost, reliability)
- ✅ Team confident in operating new implementation
- ✅ No critical bugs for 30 days post-migration
- ✅ Business value realized (<<describe>>)

---

## Communication Plan

### Stakeholder Communication

**Weekly Status Updates** (during migration):
- **Audience**: Product Owner, Engineering Manager, Operations Lead
- **Format**: Email + Slack summary
- **Content**:
  - Migration progress (% complete)
  - Metrics snapshot (errors, performance, costs)
  - Risks and issues
  - Next week's plan

**Phase Completion Reviews**:
- **Audience**: All stakeholders
- **Format**: Meeting + document
- **Content**:
  - Phase recap
  - Success criteria validation
  - Lessons learned
  - Go/no-go decision for next phase

**Incident Communication** (if rollback needed):
- **Audience**: All stakeholders + affected users
- **Format**: Immediate Slack/email, followed by post-mortem
- **Content**:
  - What happened
  - Impact
  - Rollback status
  - Next steps

### Team Communication

**Daily Standups** (during active implementation):
- Progress updates
- Blockers
- Help needed

**Retrospectives** (after each phase):
- What went well
- What could be improved
- Action items for next phase

---

## Post-Migration Activities

### Week 1-2 After 100% Rollout

**Monitoring**:
- [ ] Monitor all metrics daily
- [ ] Compare to baseline
- [ ] Address any anomalies

**Optimization**:
- [ ] Performance tuning based on production data
- [ ] Cost optimization (right-sizing resources)
- [ ] Configuration refinement

**Documentation**:
- [ ] Update architecture diagrams
- [ ] Finalize runbooks
- [ ] Document known issues and workarounds

### Week 3-4 After 100% Rollout

**Decommission Old Implementation**:
- [ ] Remove old provider code
- [ ] Clean up old dependencies
- [ ] Remove old configuration
- [ ] Archive old monitoring dashboards

**Remove Feature Flags**:
- [ ] Remove `<<flagName>>` feature flag
- [ ] Clean up flag-related code
- [ ] Simplify logic now that migration is complete

**Training & Knowledge Transfer**:
- [ ] Conduct training sessions for team
- [ ] Record training videos (if applicable)
- [ ] Update onboarding documentation

### Month 2-3 After Migration

**Long-term Monitoring**:
- [ ] Validate cost savings/increases align with projections
- [ ] Validate performance improvements sustained
- [ ] Collect user feedback

**Post-Migration Review**:
- [ ] Schedule post-mortem meeting
- [ ] Document lessons learned
- [ ] Update migration playbook for future migrations
- [ ] Celebrate success with team! 🎉

---

## Dependencies & Prerequisites

### External Dependencies

- [ ] <<TARGET_IMPLEMENTATION>> account/tenant provisioned
- [ ] Access credentials configured
- [ ] Network/firewall rules configured (if needed)
- [ ] Third-party integrations set up

### Internal Dependencies

- [ ] Feature flag system available: <<tool>>
- [ ] Monitoring infrastructure ready: <<tool>>
- [ ] CI/CD pipeline configured for deployments
- [ ] Staging environment available

### Team Dependencies

- [ ] Development team allocated: <<X>> developers for <<Y>> weeks
- [ ] QA team allocated: <<Z>> testers
- [ ] Operations team aware and prepared
- [ ] Product owner available for decisions

---

## Budget & Resources

### Estimated Costs

**Development Effort**:
- Developers: <<X>> FTE × <<Y>> weeks = <<Total person-weeks>>
- QA/Testing: <<Z>> FTE × <<W>> weeks = <<Total person-weeks>>
- Total Labor Cost: <<$$>> (if tracking)

**Infrastructure Costs**:
- <<TARGET_IMPLEMENTATION>> service: <<$$/month>>
- Additional monitoring/tooling: <<$$/month>>
- Total Infrastructure: <<$$/month>>

**One-Time Costs**:
- Training: <<$$>>
- Consulting (if needed): <<$$>>
- Licensing: <<$$>>

**Expected Savings** (if applicable):
- Decommission <<CURRENT_IMPLEMENTATION>>: Save <<$$/month>>
- Performance improvements: <<business value>>
- Reduced maintenance: <<$$/month>>

**ROI Calculation**:
- Total investment: <<$$>>
- Monthly savings: <<$$/month>>
- Payback period: <<X>> months

---

## Lessons Learned & Continuous Improvement

### Lessons Learned (to be filled post-migration)

**What Went Well**:
- <<TBD>>

**What Could Be Improved**:
- <<TBD>>

**Unexpected Challenges**:
- <<TBD>>

**Recommendations for Future Migrations**:
- <<TBD>>

---

## Appendix

### Appendix A: Terminology

- **<<CURRENT_IMPLEMENTATION>>**: <<Brief description>>
- **<<TARGET_IMPLEMENTATION>>**: <<Brief description>>
- **Feature Flag**: <<Explanation>>
- **Canary Deployment**: <<Explanation>>
- **Blast Radius**: <<Explanation>>

### Appendix B: References

- **concern-analysis.md**: Detailed analysis of current implementation
- **abstraction-recommendations.md**: Guidance on abstractions (if LOW abstraction)
- **<<TARGET_IMPLEMENTATION>> Documentation**: <<Link>>
- **Corporate Guidelines**: <<Link to relevant guidelines>>

### Appendix C: Contacts

| Role | Name | Email | Slack |
|------|------|-------|-------|
| Technical Lead | <<TBD>> | <<email>> | @<<handle>> |
| Product Owner | <<TBD>> | <<email>> | @<<handle>> |
| Operations Lead | <<TBD>> | <<email>> | @<<handle>> |
| QA Lead | <<TBD>> | <<email>> | @<<handle>> |

---

**Document Version**: 1.0
**Template Version**: Phase 9 - Cross-Cutting Concern Migration
**Generated By**: Spec Kit Analyze Project Command
**Last Updated**: <<DATE>>

---

## Sign-Off

**Plan Approval**:
- [ ] Technical Lead: _________________ Date: _______
- [ ] Product Owner: _________________ Date: _______
- [ ] Engineering Manager: ___________ Date: _______
- [ ] Operations Lead: _______________ Date: _______

**Ready to Proceed**: [ ] YES [ ] NO

**Approved Start Date**: ______________
