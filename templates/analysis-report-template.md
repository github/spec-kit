# Project Analysis Report: [PROJECT_NAME]

**Analysis Date**: [ANALYSIS_DATE]
**Analyzed By**: AI Agent
**Report Version**: 1.0

---

## Executive Summary

**Project Type**: [WEB_APP | MOBILE_APP | API | CLI_TOOL | LIBRARY | MONOLITH | MICROSERVICES]
**Primary Language**: [LANGUAGE]
**Framework**: [FRAMEWORK]
**Current State**: [EARLY_STAGE | PRODUCTION | LEGACY | UNMAINTAINED]

**Key Findings**:
- [High-level finding 1]
- [High-level finding 2]
- [High-level finding 3]

**Recommendation**: [INLINE_UPGRADE | GREENFIELD_REWRITE | HYBRID_APPROACH]

---

## 1. Project Overview

### 1.1 Technology Stack

#### Frontend
- **Framework**: [e.g., React 16.8.0]
- **Build Tool**: [e.g., Webpack 4.x]
- **State Management**: [e.g., Redux]
- **Styling**: [e.g., CSS-in-JS, SASS]
- **Testing**: [e.g., Jest, React Testing Library]

#### Backend
- **Runtime**: [e.g., Node.js 14.x]
- **Framework**: [e.g., Express 4.x]
- **Database**: [e.g., PostgreSQL 11]
- **ORM/Query Builder**: [e.g., Sequelize]
- **Authentication**: [e.g., Passport.js, JWT]

#### Infrastructure
- **Hosting**: [e.g., AWS, Azure, GCP, On-premise]
- **CI/CD**: [e.g., GitHub Actions, Jenkins]
- **Monitoring**: [e.g., DataDog, New Relic]
- **Containerization**: [e.g., Docker, Kubernetes]

### 1.2 Architecture Overview

**Architecture Pattern**: [MVC | MVVM | CLEAN_ARCHITECTURE | LAYERED | MICROSERVICES]

```
[Include architecture diagram or description]
```

**Key Components**:
- [Component 1]: [Description]
- [Component 2]: [Description]
- [Component 3]: [Description]

### 1.3 Codebase Metrics

- **Total Lines of Code**: [NUMBER]
- **Number of Files**: [NUMBER]
- **Test Coverage**: [PERCENTAGE]%
- **Number of Dependencies**: [NUMBER]
- **Estimated Team Size**: [NUMBER] developers
- **Development Timeline**: [TIMEFRAME]

---

## 2. What's Good ✅

### 2.1 Architecture & Design

**Strengths**:
- [Positive aspect 1 with evidence]
- [Positive aspect 2 with evidence]
- [Positive aspect 3 with evidence]

**Examples**:
```
[Code example or file reference showing good practice]
```

### 2.2 Code Quality

**Strengths**:
- [Quality aspect 1]
- [Quality aspect 2]
- [Quality aspect 3]

**Best Practices Observed**:
- [Practice 1]
- [Practice 2]

### 2.3 Testing & Quality Assurance

**Strengths**:
- [Testing aspect 1]
- [Testing aspect 2]

**Test Coverage Highlights**:
- Unit tests: [PERCENTAGE]%
- Integration tests: [YES/NO]
- E2E tests: [YES/NO]

### 2.4 Documentation

**Strengths**:
- [Documentation aspect 1]
- [Documentation aspect 2]

### 2.5 Maintainability

**Strengths**:
- [Maintainability aspect 1]
- [Maintainability aspect 2]

---

## 3. What's Bad ❌

### 3.1 Technical Debt

**Critical Issues**:

| Issue | Impact | Location | Effort to Fix |
|-------|--------|----------|---------------|
| [Issue 1] | HIGH/MEDIUM/LOW | [File/Component] | [DAYS/WEEKS/MONTHS] |
| [Issue 2] | HIGH/MEDIUM/LOW | [File/Component] | [DAYS/WEEKS/MONTHS] |

**Examples**:
```
[Code example showing technical debt]
```

### 3.2 Anti-Patterns

**Identified Anti-Patterns**:
- **[Anti-pattern name]**: [Description and location]
  - **Impact**: [What problems does this cause?]
  - **Recommendation**: [How to fix it]

### 3.3 Security Issues

**Severity Levels**: 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM | 🟢 LOW

| Issue | Severity | Description | Remediation |
|-------|----------|-------------|-------------|
| [Issue 1] | 🔴 | [Description] | [Fix steps] |
| [Issue 2] | 🟠 | [Description] | [Fix steps] |

### 3.4 Performance Issues

**Identified Bottlenecks**:
- [Performance issue 1]
- [Performance issue 2]

**Metrics** (if available):
- Average response time: [MS]
- Database query time: [MS]
- Bundle size: [KB/MB]

### 3.5 Code Smells

**Common Code Smells**:
- [Code smell 1 with location]
- [Code smell 2 with location]

### 3.6 Outdated Practices

**Deprecated Patterns**:
- [Outdated practice 1]
- [Outdated practice 2]

---

## 4. Dependency Analysis

### 4.1 Outdated Dependencies

| Package | Current Version | Latest LTS | Latest Stable | Security Issues | Breaking Changes |
|---------|----------------|------------|---------------|-----------------|------------------|
| [package-1] | [x.y.z] | [x.y.z] | [x.y.z] | 🔴 YES / 🟢 NO | 🔴 YES / 🟢 NO |
| [package-2] | [x.y.z] | [x.y.z] | [x.y.z] | 🔴 YES / 🟢 NO | 🔴 YES / 🟢 NO |

### 4.2 Vulnerable Dependencies

**Critical Vulnerabilities** (CVE/CVSS):

| Package | Vulnerability | CVSS Score | Fix Version | Exploit Available |
|---------|---------------|------------|-------------|-------------------|
| [package] | [CVE-XXXX-XXXX] | [0-10] | [version] | YES/NO |

### 4.3 Deprecated Dependencies

**Unmaintained Packages** (no updates in 2+ years):
- [package-1]: Last update [DATE], [recommendation]
- [package-2]: Last update [DATE], [recommendation]

### 4.4 License Issues

**License Compatibility**:
- [package]: [LICENSE] - ⚠️ [Issue if any]

---

## 5. Runtime & Platform Analysis

### 5.1 Runtime Versions

| Runtime | Current Version | LTS Version | EOL Date | Upgrade Priority |
|---------|----------------|-------------|----------|------------------|
| Node.js | [version] | [version] | [date] | HIGH/MEDIUM/LOW |
| Python | [version] | [version] | [date] | HIGH/MEDIUM/LOW |
| .NET | [version] | [version] | [date] | HIGH/MEDIUM/LOW |

### 5.2 Platform Compatibility

**OS Compatibility**: [Windows | macOS | Linux | All]
**Browser Support**: [List of supported browsers and versions]
**Mobile Support**: [iOS | Android | Both | None]

---

## 6. Upgrade Path Analysis

### 6.1 LTS Upgrade Roadmap

**Node.js Upgrade** (Example):
```
Current: Node.js 14.x (EOL: 2023-04-30)
  ↓
Step 1: Node.js 16.x (LTS until 2023-09-11)
  ↓
Step 2: Node.js 18.x (LTS until 2025-04-30)
  ↓
Target: Node.js 20.x (LTS until 2026-04-30)
```

**Estimated Effort**: [DAYS/WEEKS]

### 6.2 Framework Upgrades

**[Framework Name] Upgrade**:
```
Current: [version]
  ↓
Target: [version]
```

**Breaking Changes**:
- [Breaking change 1]: [Migration effort]
- [Breaking change 2]: [Migration effort]

**Estimated Effort**: [DAYS/WEEKS]

### 6.3 Security Patches

**Immediate Actions Required**:

| Priority | Package | Action | Effort |
|----------|---------|--------|--------|
| 🔴 CRITICAL | [package] | Upgrade to [version] | [HOURS] |
| 🟠 HIGH | [package] | Upgrade to [version] | [HOURS] |

---

## 7. Modernization Suggestions

### 7.1 Architecture Improvements

**Recommended Changes**:

1. **[Improvement 1]**
   - **Current State**: [Description]
   - **Proposed State**: [Description]
   - **Benefits**: [List benefits]
   - **Effort**: [DAYS/WEEKS/MONTHS]
   - **Risk**: [LOW/MEDIUM/HIGH]

2. **[Improvement 2]**
   - **Current State**: [Description]
   - **Proposed State**: [Description]
   - **Benefits**: [List benefits]
   - **Effort**: [DAYS/WEEKS/MONTHS]
   - **Risk**: [LOW/MEDIUM/HIGH]

### 7.2 Technology Modernization

**Recommended Technology Updates**:

| Current | Recommended | Rationale | Migration Effort |
|---------|-------------|-----------|------------------|
| [Tech 1] | [New Tech 1] | [Why upgrade] | [EFFORT] |
| [Tech 2] | [New Tech 2] | [Why upgrade] | [EFFORT] |

### 7.3 Development Process Improvements

**Process Enhancements**:
- [ ] Implement CI/CD pipeline
- [ ] Add automated testing
- [ ] Set up code quality gates
- [ ] Implement monitoring and observability
- [ ] Add security scanning

### 7.4 Code Organization

**Refactoring Opportunities**:
- [Refactoring 1]: [Description and benefits]
- [Refactoring 2]: [Description and benefits]

### 7.5 Performance Optimizations

**Quick Wins** (low effort, high impact):
- [Optimization 1]
- [Optimization 2]

**Long-term Optimizations** (high effort, high impact):
- [Optimization 1]
- [Optimization 2]

---

## 8. Feasibility & Confidence Analysis

### 8.1 Inline Upgrade Feasibility

**Feasibility Score**: [0-100]/100

**Factors**:

| Factor | Weight | Score | Weighted Score | Notes |
|--------|--------|-------|----------------|-------|
| Code Quality | 20% | [0-10] | [calc] | [Notes] |
| Test Coverage | 15% | [0-10] | [calc] | [Notes] |
| Dependency Health | 20% | [0-10] | [calc] | [Notes] |
| Architecture Quality | 15% | [0-10] | [calc] | [Notes] |
| Team Familiarity | 10% | [0-10] | [calc] | [Notes] |
| Documentation | 10% | [0-10] | [calc] | [Notes] |
| Breaking Changes | 10% | [0-10] | [calc] | [Notes] |

**Total Feasibility Score**: [WEIGHTED_SUM] / 100

**Interpretation**:
- **80-100**: Highly feasible - proceed with inline upgrade
- **60-79**: Feasible with caution - assess risks carefully
- **40-59**: Moderately risky - consider hybrid approach
- **0-39**: High risk - consider greenfield rewrite

**Scoring Rubric (0-10 for each factor)**:

- **Code Quality**:
  - 9-10: Clean code, low complexity, few smells
  - 7-8: Generally good with some debt
  - 5-6: Moderate debt, manageable
  - 3-4: Significant debt, needs work
  - 0-2: Critical debt, hard to maintain

- **Test Coverage**:
  - 9-10: >80% coverage, good test quality
  - 7-8: 60-80% coverage
  - 5-6: 40-60% coverage
  - 3-4: 20-40% coverage
  - 0-2: <20% or no tests

- **Dependency Health**:
  - 9-10: All current, no vulnerabilities
  - 7-8: Mostly current, low-severity issues only
  - 5-6: Some outdated, medium-severity issues
  - 3-4: Many outdated, high-severity issues
  - 0-2: Critical vulnerabilities, major upgrades needed

- **Architecture Quality**:
  - 9-10: Well-designed, modular, loosely coupled
  - 7-8: Good structure with minor coupling issues
  - 5-6: Acceptable structure, some refactoring needed
  - 3-4: Poor separation of concerns
  - 0-2: Monolithic, tightly coupled

- **Team Familiarity**:
  - 9-10: Team knows codebase well
  - 7-8: Most team members familiar
  - 5-6: Some knowledge exists
  - 3-4: Limited team knowledge
  - 0-2: No original team members remain

- **Documentation**:
  - 9-10: Comprehensive docs, architecture diagrams
  - 7-8: Good docs with minor gaps
  - 5-6: Basic docs exist
  - 3-4: Minimal documentation
  - 0-2: No documentation

- **Breaking Changes**:
  - 9-10: No breaking changes in upgrades
  - 7-8: Few minor breaking changes
  - 5-6: Moderate breaking changes
  - 3-4: Many breaking changes
  - 0-2: Complete API/behavior changes

**Calculation**:
```
Score = (Code_Quality * 0.20) +
        (Test_Coverage * 0.15) +
        (Dependency_Health * 0.20) +
        (Architecture_Quality * 0.15) +
        (Team_Familiarity * 0.10) +
        (Documentation * 0.10) +
        (Breaking_Changes * 0.10)

Each factor scored 0-10, then multiplied by weight and summed (max 10.0)
Final score = (Weighted sum) * 10 (max 100)
```

### 8.2 Greenfield Rewrite Feasibility

**Feasibility Score**: [0-100]/100

**Factors**:

| Factor | Weight | Score | Weighted Score | Notes |
|--------|--------|-------|----------------|-------|
| Requirements Clarity | 20% | [0-10] | [calc] | [Notes] |
| Technical Debt Level | 20% | [0-10] | [calc] | [Notes] |
| Business Continuity | 15% | [0-10] | [calc] | [Notes] |
| Team Capacity | 15% | [0-10] | [calc] | [Notes] |
| Time Available | 15% | [0-10] | [calc] | [Notes] |
| Budget | 15% | [0-10] | [calc] | [Notes] |

**Total Feasibility Score**: [WEIGHTED_SUM] / 100

### 8.3 Confidence Scores

**Analysis Confidence**: [0-100]/100

**Factors Affecting Confidence**:
- Code accessibility: [HIGH/MEDIUM/LOW]
- Documentation availability: [HIGH/MEDIUM/LOW]
- Test coverage: [PERCENTAGE]%
- Complexity assessment: [HIGH/MEDIUM/LOW]

**Recommendation Confidence**: [0-100]/100

Based on:
- Data completeness: [PERCENTAGE]%
- Industry experience with similar migrations
- Risk assessment accuracy

---

## 9. Decision Matrix

### 9.1 Inline Upgrade vs Greenfield Comparison

| Criteria | Inline Upgrade | Greenfield Rewrite | Winner |
|----------|----------------|--------------------| -------|
| **Time to Complete** | [TIMEFRAME] | [TIMEFRAME] | [INLINE/GREENFIELD] |
| **Cost** | [ESTIMATE] | [ESTIMATE] | [INLINE/GREENFIELD] |
| **Risk Level** | [LOW/MED/HIGH] | [LOW/MED/HIGH] | [INLINE/GREENFIELD] |
| **Business Disruption** | [LOW/MED/HIGH] | [LOW/MED/HIGH] | [INLINE/GREENFIELD] |
| **Technical Debt Reduction** | [LOW/MED/HIGH] | [LOW/MED/HIGH] | [INLINE/GREENFIELD] |
| **Team Learning Curve** | [LOW/MED/HIGH] | [LOW/MED/HIGH] | [INLINE/GREENFIELD] |
| **Feature Parity Timeline** | [TIMEFRAME] | [TIMEFRAME] | [INLINE/GREENFIELD] |

### 9.2 Hybrid Approach (Strangler Fig Pattern)

**Feasibility**: [YES/NO]

**Strategy**:
1. [Step 1: e.g., Extract authentication module]
2. [Step 2: e.g., Modernize API layer]
3. [Step 3: e.g., Migrate database incrementally]

**Timeline**: [TIMEFRAME]

---

## 10. Recommendations

### 10.1 Primary Recommendation

**🎯 RECOMMENDATION: [INLINE_UPGRADE | GREENFIELD_REWRITE | HYBRID_APPROACH]**

**Rationale**:
[Detailed explanation of why this approach is recommended based on the analysis]

**Confidence Level**: [HIGH/MEDIUM/LOW] ([0-100]%)

### 10.2 Immediate Actions (Next 2 Weeks)

1. **[Action 1]**
   - Priority: 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM
   - Effort: [HOURS/DAYS]
   - Impact: [Description]

2. **[Action 2]**
   - Priority: 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM
   - Effort: [HOURS/DAYS]
   - Impact: [Description]

### 10.3 Short-term Actions (1-3 Months)

1. [Action 1]
2. [Action 2]
3. [Action 3]

### 10.4 Long-term Roadmap (3-12 Months)

**Quarter 1**: [Goals]
**Quarter 2**: [Goals]
**Quarter 3**: [Goals]
**Quarter 4**: [Goals]

---

## 11. Risk Assessment

### 11.1 Upgrade Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| [Risk 1] | HIGH/MED/LOW | HIGH/MED/LOW | [Strategy] |
| [Risk 2] | HIGH/MED/LOW | HIGH/MED/LOW | [Strategy] |

### 11.2 Rewrite Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| [Risk 1] | HIGH/MED/LOW | HIGH/MED/LOW | [Strategy] |
| [Risk 2] | HIGH/MED/LOW | HIGH/MED/LOW | [Strategy] |

---

## 12. Suggested Project Constitution

**IF proceeding with greenfield rewrite**, use these recommended principles:

### Principle 1: [PRINCIPLE_NAME]
[Description of principle and rationale]

### Principle 2: [PRINCIPLE_NAME]
[Description of principle and rationale]

### Principle 3: [PRINCIPLE_NAME]
[Description of principle and rationale]

**See**: `recommended-constitution.md` for full details

---

## 13. Suggested Specification

**IF proceeding with greenfield rewrite**, use this as starting point:

**See**: `recommended-spec.md` for detailed specification based on reverse-engineered requirements

---

## 14. Resources & References

### 14.1 Migration Guides
- [Link to official migration guide]
- [Link to community resources]

### 14.2 Tools Recommended
- [Tool 1]: [Purpose]
- [Tool 2]: [Purpose]

### 14.3 Further Reading
- [Article/Book 1]
- [Article/Book 2]

---

## Appendix A: Detailed Dependency List

[Complete list of all dependencies with versions]

---

## Appendix B: Test Coverage Report

[Detailed test coverage metrics if available]

---

## Appendix C: Security Scan Results

[Full security scan output]

---

**End of Report**

---

**Next Steps**:
1. Review this analysis with stakeholders
2. Choose upgrade path (inline/greenfield/hybrid)
3. If inline: Use generated upgrade plan
4. If greenfield: Use recommended constitution and spec to start new project with `/speckit.orchestrate`
