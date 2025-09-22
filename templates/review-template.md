# Code Review Report: {FEATURE_NAME} ({FEATURE_ID})

## Final Status: **{REVIEW_STATUS}** _(Approved | Changes Requested | Blocked: Missing Context | Blocked: Scope Mismatch | Needs Clarification | TDD Violation | Quality Controls Violation | Security Gate Failure | Privacy Gate Failure | Supply Chain Violation | Dependency Vulnerabilities | Deprecated Dependencies | Review Pending)_

## Resolved Scope

**Branch**: `{BRANCH_NAME}`
**Baseline**: `{BASE_BRANCH}`
**Diff Source**: `{DIFF_SOURCE}`
**Review Target**: {FEATURE_DESCRIPTION}
**Files Analyzed**: {CHANGED_FILES_COUNT} changed files including {FILE_CATEGORIES}

**Resolved Scope Narrative**: {RESOLVED_SCOPE_NARRATIVE}

**Feature Directory**: `{FEATURE_DIR}`
**Implementation Scope**:
- {SCOPE_ITEM_1}
- {SCOPE_ITEM_2}
- {SCOPE_ITEM_3}
- {SCOPE_ITEM_4}
- {SCOPE_ITEM_5}
- {SCOPE_ITEM_6}

## SPEC_KIT_CONFIG

```yaml
spec-kit:
  constitution:
    path: '{CONSTITUTION_PATH}'
  review:
    documents:
      - path: '{DOCUMENT_1_PATH}'
        context: '{DOCUMENT_1_CONTEXT}'
      - path: '{DOCUMENT_2_PATH}'
        context: '{DOCUMENT_2_CONTEXT}'
      - path: '{DOCUMENT_3_PATH}'
        context: '{DOCUMENT_3_CONTEXT}'
```

## Pre-Review Gates

| Gate | Status | Details |
|------|--------|---------|
| **Context Gate** | {CONTEXT_GATE_STATUS} | {CONTEXT_GATE_DETAILS} |
| **Change Intent Gate** | {INTENT_GATE_STATUS} | {INTENT_GATE_DETAILS} |
| **Unknowns Gate** | {UNKNOWNS_GATE_STATUS} | {UNKNOWNS_GATE_DETAILS} |
| **Separation of Duties** | {SOD_GATE_STATUS} | {SOD_GATE_DETAILS} |
| **Code Owners Gate** | {OWNERS_GATE_STATUS} | {OWNERS_GATE_DETAILS} |
| **Quality Controls Gate** | {QUALITY_GATE_STATUS} | {QUALITY_GATE_DETAILS} |
| **TDD Evidence Gate** | {TDD_GATE_STATUS} | {TDD_GATE_DETAILS} |

## Findings

> Order findings from highest to lowest severity. Populate every metadata field to satisfy the deliverable schema.

### Finding {FINDING_1_ID}: {FINDING_1_TITLE}
- **Category**: {FINDING_1_CATEGORY}
- **Severity**: {FINDING_1_SEVERITY}
- **Confidence**: {FINDING_1_CONFIDENCE}
- **Impact**: {FINDING_1_IMPACT}
- **Evidence**: {FINDING_1_EVIDENCE}
- **Remediation**: {FINDING_1_REMEDIATION}
- **Source Requirement**: {FINDING_1_SOURCE_REQUIREMENT}
- **Files**: {FINDING_1_FILES}

### Finding {FINDING_2_ID}: {FINDING_2_TITLE}
- **Category**: {FINDING_2_CATEGORY}
- **Severity**: {FINDING_2_SEVERITY}
- **Confidence**: {FINDING_2_CONFIDENCE}
- **Impact**: {FINDING_2_IMPACT}
- **Evidence**: {FINDING_2_EVIDENCE}
- **Remediation**: {FINDING_2_REMEDIATION}
- **Source Requirement**: {FINDING_2_SOURCE_REQUIREMENT}
- **Files**: {FINDING_2_FILES}

_(Add additional findings as required, maintaining severity ordering.)_

## Strengths

{STRENGTHS_SECTION}

## Outstanding Clarifications

- [NEEDS CLARIFICATION: {CLARIFICATION_ITEM_1}]
- [NEEDS CLARIFICATION: {CLARIFICATION_ITEM_2}]
- [NEEDS CLARIFICATION: {CLARIFICATION_ITEM_3}]

## Control Inventory

The project demonstrates established control patterns:

| Control Domain | Implementation | Status | Reference |
|----------------|----------------|--------|-----------|
| **Authentication** | {AUTH_IMPLEMENTATION} | {AUTH_STATUS} | `{AUTH_REFERENCE}` |
| **Logging** | {LOGGING_IMPLEMENTATION} | {LOGGING_STATUS} | {LOGGING_REFERENCE} |
| **Error Handling** | {ERROR_IMPLEMENTATION} | {ERROR_STATUS} | {ERROR_REFERENCE} |
| **Repository Pattern** | {REPO_IMPLEMENTATION} | {REPO_STATUS} | `{REPO_REFERENCE}` |
| **Input Validation** | {VALIDATION_IMPLEMENTATION} | {VALIDATION_STATUS} | `{VALIDATION_REFERENCE}` |
| **State Management** | {STATE_IMPLEMENTATION} | {STATE_STATUS} | {STATE_REFERENCE} |
| **Performance** | {PERF_IMPLEMENTATION} | {PERF_STATUS} | {PERF_REFERENCE} |

## Quality Signal Summary

### Linting Results
- **Status**: {LINT_STATUS}
- **Warnings**: {LINT_WARNING_COUNT} warnings, {LINT_ERROR_COUNT} errors
- **Key Issues**:
  - {LINT_ISSUE_1}
  - {LINT_ISSUE_2}
  - {LINT_ISSUE_3}

### Type Checking
- **Status**: {TYPECHECK_STATUS}
- **Results**: {TYPECHECK_RESULTS}

### Test Results
- **Status**: {TEST_STATUS}
- **Results**: {TEST_FAILURE_COUNT} of {TEST_TOTAL_COUNT} tests failing ({TEST_FAILURE_RATE}% failure rate)
- **Root Cause**: {TEST_FAILURE_ROOT_CAUSE}

### Build Status
- **Status**: {BUILD_STATUS}
- **{BUILD_DETAILS}**

## Dependency Audit Summary

- **Baseline Severity Counts**: {DEPENDENCY_BASELINE_SEVERITIES}
- **Current Severity Counts**: {DEPENDENCY_CURRENT_SEVERITIES}
- **New CVEs Identified**: {DEPENDENCY_NEW_CVES}
- **Deprecated Packages**: {DEPENDENCY_DEPRECATED_PACKAGES}
- **Justifications / Version Currency**: {DEPENDENCY_JUSTIFICATIONS}

## Requirements Coverage Table

| Requirement | Summary | Implementation Evidence | Validating Tests | Linked Findings / Clarifications |
|-------------|---------|-------------------------|------------------|-----------------------------------|
| **FR-###** | {REQ_SUMMARY_1} | {REQ_EVIDENCE_1_FILES} | {REQ_TESTS_1} | {REQ_LINKS_1} |
| **FR-###** | {REQ_SUMMARY_2} | {REQ_EVIDENCE_2_FILES} | {REQ_TESTS_2} | {REQ_LINKS_2} |
| **FR-###** | {REQ_SUMMARY_3} | {REQ_EVIDENCE_3_FILES} | {REQ_TESTS_3} | {REQ_LINKS_3} |

## Requirements Compliance Checklist

| Requirement Group | Status | Notes |
|-------------------|--------|-------|
| **Constitutional Principles** | {CONSTITUTIONAL_STATUS} | {CONSTITUTIONAL_NOTES} |
| **SOC 2 Authentication** | {SOC2_AUTH_STATUS} | {SOC2_AUTH_NOTES} |
| **SOC 2 Logging** | {SOC2_LOG_STATUS} | {SOC2_LOG_NOTES} |
| **Security Controls** | {SECURITY_STATUS} | {SECURITY_NOTES} |
| **Code Quality** | {QUALITY_STATUS} | {QUALITY_NOTES} |
| **Testing Requirements** | {TESTING_STATUS} | {TESTING_NOTES} |

## Decision Log

{DECISION_LOG_SECTION}

## Remediation Logging

> Capture tasks for every Critical/Major finding or non-Approved status using `Context → Control Reference → Actions → Verification`.

### Remediation {REMEDIATION_ID_1}
- **Context**: {REMEDIATION_CONTEXT_1}
- **Control Reference**: {REMEDIATION_CONTROL_REFERENCE_1}
- **Actions**: {REMEDIATION_ACTIONS_1}
- **Verification**: {REMEDIATION_VERIFICATION_1}

### Remediation {REMEDIATION_ID_2}
- **Context**: {REMEDIATION_CONTEXT_2}
- **Control Reference**: {REMEDIATION_CONTROL_REFERENCE_2}
- **Actions**: {REMEDIATION_ACTIONS_2}
- **Verification**: {REMEDIATION_VERIFICATION_2}

_(Add additional remediation tasks as needed.)_

---

**Review Completed**: {REVIEW_TIMESTAMP}
**Reviewer**: Claude Code Review v2.0
**Next Action**: {NEXT_ACTION}
