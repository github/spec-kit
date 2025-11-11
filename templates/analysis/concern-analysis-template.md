# Cross-Cutting Concern Analysis: <<CONCERN_TYPE>>

**Project**: <<PROJECT_NAME>>
**Analysis Date**: <<DATE>>
**Analyzed By**: AI Agent
**Current Implementation**: <<CURRENT_IMPLEMENTATION>>
**Target Implementation**: <<TARGET_IMPLEMENTATION>>

---

## Executive Summary

| Attribute | Value |
|-----------|-------|
| **Concern Type** | <<e.g., Authentication/Authorization>> |
| **Current** | <<e.g., Custom JWT implementation>> |
| **Target** | <<e.g., Migrate to Okta>> |
| **Abstraction Level** | <<HIGH / MEDIUM / LOW>> |
| **Blast Radius** | <<X% of codebase, N files, M LOC>> |
| **Coupling Degree** | <<LOOSE / MODERATE / TIGHT>> |
| **Recommended Strategy** | <<STRANGLER_FIG / ADAPTER_PATTERN / REFACTOR_FIRST / BIG_BANG_WITH_FEATURE_FLAGS>> |
| **Risk Assessment** | <<LOW / MEDIUM / HIGH>> |
| **Effort Estimate** | <<Time range, e.g., 2-4 weeks>> |
| **Business Impact** | <<Brief statement on why this migration matters>> |

**Primary Recommendation**: <<One-sentence summary of recommended approach>>

---

## 1. Current Implementation Analysis

### 1.1 Identified Concern Files

| File Path | Type | Evidence | LOC | Criticality |
|-----------|------|----------|-----|-------------|
| <<file:line>> | Core Implementation | <<Evidence, e.g., Exports authenticate(), uses jsonwebtoken>> | <<LOC>> | CRITICAL / STANDARD |
| <<file:line>> | Middleware | <<Evidence>> | <<LOC>> | CRITICAL / STANDARD |
| <<file:line>> | Configuration | <<Evidence>> | <<LOC>> | STANDARD |
| ... | ... | ... | ... | ... |

**Summary**:
- **Total Files**: <<N>> files
- **Total LOC**: <<M>> lines (~<<X>>% of codebase)
- **Critical Files**: <<Count of CRITICAL files>>
- **Configuration Files**: <<Count>>

### 1.2 Entry Points & Consumer Callsites

Analysis of where and how this concern is used throughout the codebase:

| Entry Point | Type | Usage Count | Evidence (file:line) | Criticality |
|-------------|------|-------------|----------------------|-------------|
| <<FunctionName>>() | Interface/Service | <<N>> callsites | <<file:line>> | CRITICAL / STANDARD |
| <<DecoratorName>> | Decorator | <<N>> usages | <<file:line>> | CRITICAL / STANDARD |
| ... | ... | ... | ... | ... |

**Consumer Files** (files that depend on this concern):
- <<file:line>> - <<N>> callsites - <<Brief description, e.g., "All user endpoints require auth">>
- <<file:line>> - <<M>> callsites - <<Description>>
- ... (list all major consumers)

**Total Callsites**: <<Count>> across <<N>> files

### 1.3 Abstraction Assessment

**Level**: <<HIGH / MEDIUM / LOW>>

**Rationale**:
- <<Evidence 1 with file:line references>>
- <<Evidence 2 with file:line references>>
- <<Evidence 3 with file:line references>>

**Interface/Contract Analysis**:
- **Interfaces Found**:
  - <<IInterfaceName>> at <<file:line>>
  - ... (list all interfaces)
- **Implementation Classes**:
  - <<ClassName>> at <<file:line>> (implements <<IInterfaceName>>)
  - ... (list all implementations)
- **Consumer Dependencies**:
  - <<X>> files depend on interface (GOOD - loose coupling)
  - <<Y>> files depend on concrete implementation (CONCERN - tight coupling)

**Dependency Injection Usage**:
- **DI Framework**: <<Detected framework or "None">>
- **Injection Pattern**: <<Constructor / Property / Service Locator / Manual instantiation>>
- **Coverage**: <<X%>> of consumers use DI, <<Y%>> use direct instantiation

**Abstraction Quality Indicators**:

<<IF HIGH ABSTRACTION>>:
✅ **HIGH Abstraction Indicators Detected**:
- Single interface/contract serving all consumers
- Dependency injection used throughout
- No direct implementation imports in consumers
- Configuration-driven behavior
- Clear separation: Interface → Implementation → Consumers

<<ELSE IF MEDIUM ABSTRACTION>>:
⚠️ **MEDIUM Abstraction Indicators Detected**:
- Multiple entry points with consistent patterns
- Some direct dependencies, but localized
- Partial use of interfaces
- Mix of dependency injection and direct instantiation

<<ELSE IF LOW ABSTRACTION>>:
❌ **LOW Abstraction Indicators Detected**:
- Scattered across codebase with no clear pattern
- Direct imports of implementation everywhere
- No interfaces or contracts
- Hardcoded dependencies
- Implementation details leak into business logic

---

## 2. Blast Radius Analysis

### 2.1 Impact Metrics

| Metric | Value | Assessment |
|--------|-------|------------|
| **Files Affected** | <<N>> files | <<Small (<20 files) / Medium (20-50) / Large (>50)>> |
| **LOC Affected** | <<M>> lines | <<X%>> of total codebase (<<Total LOC>> lines) |
| **Consumer Callsites** | <<Count>> callsites | <<Focused (<50) / Moderate (50-150) / Widespread (>150)>> |
| **Critical Paths** | <<Count>> critical paths | <<List: user login, API auth, session refresh, ...>> |
| **Test Coverage** | <<X%>> (<<N>> test files) | <<Low (<50%) / Medium (50-80%) / High (>80%)>> |

**Risk Categorization**: <<LOW (<10% codebase) / MEDIUM (10-25%) / HIGH (>25%)>>

### 2.2 Critical Dependencies

Files that heavily depend on this concern (high risk for migration):

| File | Callsites | Criticality | Reason | Evidence (file:line) |
|------|-----------|-------------|--------|----------------------|
| <<file>> | <<N>> calls | CRITICAL | <<e.g., "All user endpoints require auth">> | <<file:line>> |
| <<file>> | <<M>> calls | CRITICAL | <<Reason>> | <<file:line>> |
| <<file>> | <<K>> calls | STANDARD | <<Reason>> | <<file:line>> |
| ... | ... | ... | ... | ... |

### 2.3 Affected Business Functions

Mapping concern usage to business capabilities:

| Business Function | Affected Files | Impact | Mitigation Required |
|-------------------|----------------|--------|---------------------|
| <<e.g., User Authentication>> | <<N>> files | HIGH / MEDIUM / LOW | <<e.g., "Comprehensive E2E testing required">> |
| <<e.g., API Authorization>> | <<M>> files | HIGH / MEDIUM / LOW | <<Mitigation strategy>> |
| ... | ... | ... | ... |

---

## 3. Coupling Degree Analysis

**Level**: <<LOOSE / MODERATE / TIGHT>>

### 3.1 Dependency Graph

**Concern → External Dependencies**:
- <<Package name + version>> - <<Purpose, e.g., "JWT token generation">>
- ... (list all external packages)

**Concern → Business Logic**:
<<IF imports from business domain>>:
⚠️ Concern has dependencies on business logic:
- <<Import statement>> from <<file:line>> - <<e.g., "User entity import">>
- ... (list all business logic imports)
<<ELSE>>:
✅ Concern is isolated - no imports from business logic

**Business Logic → Concern**:
- <<Import statement>> from <<file:line>> - <<e.g., "IAuthService interface import">>
- ... (list all consumers)

**Circular Dependencies**:
<<IF circular deps exist>>:
❌ **CRITICAL**: Circular dependencies detected:
- <<file1>> → <<file2>> → <<file1>> (<<Evidence>>)
- ... (list all cycles)
<<ELSE>>:
✅ No circular dependencies detected

### 3.2 Isolation Score

**Score**: <<0-10>>/10 (where 10 = fully isolated, 0 = tightly coupled)

**Breakdown**:
- **Module Boundaries**: <<Clear / Blurred>> (<<Evidence>>)
- **Shared State**: <<None / Some / Extensive>> (<<Evidence>>)
- **Bidirectional Dependencies**: <<Yes / No>> (<<Evidence>>)
- **Testability**: <<Can be tested independently / Requires app context>> (<<Evidence>>)

**Coupling Quality Indicators**:

<<IF LOOSE COUPLING>>:
✅ **LOOSE Coupling Indicators Detected**:
- Concern isolated in dedicated module/package
- Well-defined boundaries with clear contracts
- Unidirectional dependencies (business logic → concern)
- Can be tested independently

<<ELSE IF MODERATE COUPLING>>:
⚠️ **MODERATE Coupling Indicators Detected**:
- Some separation but with leaks
- Unidirectional dependencies overall
- Shared models/DTOs with business logic

<<ELSE IF TIGHT COUPLING>>:
❌ **TIGHT Coupling Indicators Detected**:
- Bidirectional dependencies
- Shared state or global variables
- Circular dependencies
- Concern implementation embedded in business logic

---

## 4. Configuration & Environment Analysis

### 4.1 Configuration Files

| Config File | Purpose | Values | Evidence (file:line) |
|-------------|---------|--------|----------------------|
| <<file>> | <<e.g., "JWT secret, token expiration">> | <<Key config values>> | <<file:line>> |
| ... | ... | ... | ... |

### 4.2 Environment Dependencies

| Environment Aspect | Current | Target | Migration Impact |
|-------------------|---------|--------|------------------|
| **Runtime Version** | <<e.g., Node 16>> | <<e.g., Node 20>> | <<NONE / LOW / MEDIUM / HIGH>> |
| **External Services** | <<e.g., "None (self-contained)">> | <<e.g., "Okta SaaS">> | NEW dependency |
| **Infrastructure** | <<Current setup>> | <<Target setup>> | <<Impact description>> |

---

## 5. Technical Debt & Risk Assessment

### 5.1 Current Technical Debt

<<List technical debt items found in current implementation>>:

| Issue | Severity | Evidence (file:line) | Impact on Migration |
|-------|----------|----------------------|---------------------|
| <<e.g., "Hardcoded secrets in code">> | HIGH / MEDIUM / LOW | <<file:line>> | <<Impact>> |
| <<e.g., "No interface abstraction">> | HIGH / MEDIUM / LOW | <<file:line>> | <<Impact>> |
| ... | ... | ... | ... |

### 5.2 Migration Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| <<e.g., "Breaking existing auth flows">> | HIGH / MEDIUM / LOW | HIGH / MEDIUM / LOW | <<Strategy>> |
| <<e.g., "Performance degradation">> | HIGH / MEDIUM / LOW | HIGH / MEDIUM / LOW | <<Strategy>> |
| ... | ... | ... | ... |

### 5.3 Rollback Considerations

**Rollback Complexity**: <<EASY / MODERATE / DIFFICULT>>

**Rollback Plan**:
<<Describe how to revert migration if it fails>>:
1. <<Step 1>>
2. <<Step 2>>
...

**Rollback Time Estimate**: <<Time to revert, e.g., "< 1 hour with feature flag toggle">>

---

## 6. Testing Requirements

### 6.1 Existing Test Coverage

| Test Type | Count | Coverage | Quality |
|-----------|-------|----------|---------|
| **Unit Tests** | <<N>> tests | <<X%>> | <<GOOD / ADEQUATE / POOR>> |
| **Integration Tests** | <<M>> tests | <<Y%>> | <<GOOD / ADEQUATE / POOR>> |
| **E2E Tests** | <<K>> tests | <<Z%>> | <<GOOD / ADEQUATE / POOR>> |

**Test Files**:
- <<test-file:line>> - <<Description>>
- ... (list all test files)

### 6.2 Testing Strategy for Migration

**Required New Tests**:
1. **Unit Tests**: <<Description of unit tests needed>>
   - Test <<TARGET_IMPLEMENTATION>> provider in isolation
   - Mock all external dependencies
   - Target coverage: <<X%>>

2. **Integration Tests**: <<Description>>
   - Test integration with business logic
   - Test configuration variations
   - Test error scenarios

3. **E2E Tests**: <<Description>>
   - Test critical user journeys end-to-end
   - <<List critical paths to test>>

**Testing Phases**:
- **Phase 1**: Local development testing (<<Timeline>>)
- **Phase 2**: Staging/QA environment (<<Timeline>>)
- **Phase 3**: Production canary rollout (<<Timeline>>)
- **Phase 4**: Full production deployment (<<Timeline>>)

---

## 7. Dependencies & Prerequisites

### 7.1 Migration Prerequisites

**Before migration can begin**:
- [ ] <<Prerequisite 1, e.g., "Okta tenant provisioned">>
- [ ] <<Prerequisite 2, e.g., "Target infrastructure setup">>
- [ ] <<Prerequisite 3, e.g., "Team training on new technology">>
- ... (checklist of prerequisites)

### 7.2 New Dependencies Required

| Dependency | Purpose | Version | License | Security Scan |
|------------|---------|---------|---------|---------------|
| <<package-name>> | <<Purpose>> | <<Version>> | <<License>> | ✅ PASS / ⚠️ REVIEW / ❌ FAIL |
| ... | ... | ... | ... | ... |

---

## 8. Findings Summary

### 8.1 Strengths (What's Good)

✅ **Positive Findings**:
- <<Strength 1 with evidence>>
- <<Strength 2 with evidence>>
- ... (things that will make migration easier)

### 8.2 Concerns (What Needs Attention)

⚠️ **Areas of Concern**:
- <<Concern 1 with evidence>>
- <<Concern 2 with evidence>>
- ... (things that will make migration harder)

### 8.3 Critical Issues (Must Address)

❌ **Critical Issues**:
- <<Issue 1 with evidence>> - **Must be resolved before migration**
- <<Issue 2 with evidence>> - **Must be resolved before migration**
- ... (blockers)

---

## 9. Recommendations

### 9.1 Recommended Migration Strategy

**Strategy**: <<STRANGLER_FIG / ADAPTER_PATTERN / REFACTOR_FIRST / BIG_BANG_WITH_FEATURE_FLAGS>>

**Rationale**:
- **Abstraction Level**: <<HIGH/MEDIUM/LOW>> → <<Implication for migration>>
- **Blast Radius**: <<X% of codebase>> → <<Risk level and phasing needs>>
- **Coupling Degree**: <<LOOSE/MODERATE/TIGHT>> → <<Isolation capability>>
- **Conclusion**: <<Why this strategy is the best fit>>

**Detailed Strategy Description**:
<<Describe the chosen strategy and how it applies to this specific migration>>

### 9.2 Alternative Approaches (Considered but Not Recommended)

| Approach | Pros | Cons | Why Not Chosen |
|----------|------|------|----------------|
| <<Strategy>> | <<Pros>> | <<Cons>> | <<Reason>> |
| ... | ... | ... | ... |

---

## 10. Next Steps

### 10.1 Immediate Actions

1. **Review this analysis** with technical team and stakeholders
2. **Validate findings** - Verify file:line references and impact assessment
3. **Read abstraction-recommendations.md** - Understand abstraction improvements (if LOW abstraction)
4. **Read concern-migration-plan.md** - Review detailed migration roadmap
5. **Decision point**: Approve migration approach or request modifications

### 10.2 Decision Required

**Question for Stakeholders**: Based on this analysis, should we:
- [ ] **Option A**: Proceed with recommended migration strategy (<<STRATEGY>>)
- [ ] **Option B**: First refactor to improve abstractions, then migrate (if LOW abstraction)
- [ ] **Option C**: Defer migration - risk/effort doesn't justify value
- [ ] **Option D**: Explore alternative approach (specify)

**Decision Factors**:
- **Business Value**: <<Describe value of migration>>
- **Technical Risk**: <<Risk level>>
- **Effort Required**: <<Timeline>>
- **Team Capacity**: <<Consider team availability>>

---

## Appendix A: File Inventory

<<Complete list of all concern-related files with metadata>>

| # | File Path | Type | LOC | Last Modified | Owner/Team |
|---|-----------|------|-----|---------------|------------|
| 1 | <<file>> | <<Type>> | <<LOC>> | <<Date>> | <<Team>> |
| 2 | ... | ... | ... | ... | ... |

**Total Files**: <<N>>
**Total LOC**: <<M>> lines

---

## Appendix B: Glossary

**Terms used in this analysis**:

- **Abstraction Level**: How well the concern is separated from implementation details
- **Blast Radius**: The scope of code affected by migration
- **Coupling Degree**: How tightly the concern is integrated with the rest of the system
- **Entry Point**: A function/method/decorator that provides access to the concern
- **Consumer**: A file/module that uses the concern
- **Callsite**: A specific location (file:line) where the concern is invoked
- **STRANGLER_FIG**: Gradual migration pattern with old and new running side-by-side
- **ADAPTER_PATTERN**: Wrap new implementation behind existing interface
- **REFACTOR_FIRST**: Improve abstractions before migrating
- **BIG_BANG_WITH_FEATURE_FLAGS**: Complete migration with gradual rollout via flags

---

**Document Version**: 1.0
**Template Version**: Phase 9 - Cross-Cutting Concern Analysis
**Generated By**: Spec Kit Analyze Project Command
