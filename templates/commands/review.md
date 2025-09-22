---

description:
Run a scope-driven review that enforces project governance, quality gates, and
risk controls
version: 2.0
semantics:

- Levels use RFC 2119 / BCP 14 (MUST/SHOULD/MAY).
  authoritative_sources:
- NIST SSDF v1.1 (SP 800-218) PW.7–PW.8
- OWASP ASVS v4.x; OWASP Code Review Guide; OWASP SAMM
- ISO/IEC 27002:2022 (8.28 Secure Coding); ISO/IEC 27001 ISMS
- PCI DSS 4.0 (esp. 6.3.2 code review before release)
- GDPR Article 25 (Data Protection by Design & Default), CCPA
- SLSA v1.0 (supply chain provenance)
- Google Engineering Practices (Small CLs, Speed, What to look for)
- Microsoft Engineering Playbook (Code Reviews)
- WCAG 2.2 (Level AA)
- Google SRE (launch/readiness checklists)
  notes:
- This playbook is stack-agnostic and applies to any language or runtime.
- Always use absolute paths from the repository root for all file operations.

---

# Code Review Playbook

## Flow

1. Initialize Spec Kit configuration

    - Check for `/.specify.yaml` at the project root; if present, load it
    - Otherwise load `/config-default.yaml`
    - Extract the root `spec-kit` entry and store it as `SPEC_KIT_CONFIG`
    - Output the resulting `SPEC_KIT_CONFIG` for operator visibility
    - **Record** review posture: platform (GitHub/GitLab/etc.), branch protection, required checks, CODEOWNERS availability

2. Capture prerequisite signals

    - Run `/scripts/bash/check-implementation-prerequisites.sh --json` from the repo root
    - Parse `FEATURE_DIR` and the `AVAILABLE_DOCS` list; all future file paths must be absolute
    - Record sandbox mode, network access, and approval policy before running commands

3. Load and analyze the implementation context

    - **REQUIRED**: Read `tasks.md` for the complete task list and execution plan
    - **REQUIRED**: Read `plan.md` for tech stack, architecture, and file structure
    - **REQUIRED**: Read `spec.md` within `FEATURE_DIR`; extract the `Requirements` section and flag a missing or malformed
      spec as `[Open Question]`
    - **IF EXISTS**: Read `data-model.md` for entities and relationships
    - **IF EXISTS**: Read `contracts/` for API specifications and test requirements
    - **IF EXISTS**: Read `research.md` for technical decisions and constraints
    - **IF EXISTS**: Read `quickstart.md` for integration scenarios
    - **Record** the plan-of-record (POR) change intent

4. Enrich governance context

    - If defined, read documents from `SPEC_KIT_CONFIG.review.documents`
        - For each entry, resolve `path` to an absolute path from the repo root
        - Read the file and apply its `context` to guide review heuristics
        - If a document is missing, record it as a risk before continuing
    - Read the constitution at `SPEC_KIT_CONFIG.constitution.path` to understand constitutional requirements
    - Load platform enforcement posture (protected branches, required status checks, approval rules, CODEOWNERS)

5. Consolidate feature inputs

    - Treat `FEATURE_DIR` (e.g., `specs/006-story-2-2/`) as the authoritative dossier; read `plan.md`, `tasks.md`,
      `research.md`, and related outputs to gather every directive that states scope, explicit targets, exclusions, focus
      questions, risks, or acceptance gates
    - Assume implementation occurs on a branch named after the feature directory slug (e.g., branch `006-story-2-2`);
      compare that branch tip to its baseline (`main` unless overridden) to identify the change set under review, and note
      any caller-provided diff hints or commit ranges
    - Derive concrete scope hints by enumerating file paths, directories, and components referenced within `tasks.md` (task
      descriptions, `[P]` tags, dependency notes) and `plan.md` (project structure decisions); store the consolidated list
      as `REVIEW_SCOPE_HINTS`
    - Capture explicit guardrails, risk registers, checklist items, or out-of-scope statements and store them as
      `REVIEW_DIRECTIVES`
    - Parse the `Requirements` section of `spec.md` to build `SPEC_REQUIREMENTS`; for each requirement capture `id`
      (e.g., `FR-###`), verbatim rule text, related acceptance scenarios/tests, and any embedded clarification markers
    - Start a `CONTROL_INVENTORY` by mapping each cross-cutting control mandated in the gathered documents (e.g., logging,
      authentication, telemetry, storage, observability) to the code assets or services that already implement it; record
      the path locator, purpose, and reuse guidance in a structured format that can be emitted with review outputs
    - Confirm the instruction/assumption handling strategy defined for the feature; if absent, default to raising
      `[Open Question]` items for ambiguous inputs

6. Resolve scope and operating context

    - Normalize the scope into concrete path globs or files using the repository root
    - Union multiple hints and record the result as `RESOLVED_SCOPE`
    - Verify the paths exist; if not, pause and request clarification
    - When required commands are blocked by sandboxing or policy, request elevation or document the limitation

7. Harvest governing requirements

    - **Seed `REVIEW_REQUIREMENTS`** with:
        - Template gates from `/templates/plan-template.md`, `/templates/tasks-template.md`,
          and `.claude/commands/implement.md` (unchanged from v1)
        - **Global Normative Requirements (baseline)** from this playbook (see **Requirements Catalog**)
        - Additional controlling documents from `SPEC_KIT_CONFIG`, `AVAILABLE_DOCS`, and operator-provided standards digests
        - Feature-level directives from `SPEC_REQUIREMENTS`, preserving their IDs and original wording
   - Read each document and **extract explicit mandates** (architecture boundaries, logging strategy, dependency policy,
     quality gates, quality controls governance, testing posture, risk controls), appending them to `REVIEW_REQUIREMENTS`
      with:
       - `id`, `name`, `level` (MUST/SHOULD/MAY), `rule` (one sentence),
         `rationale`, `source`
    - Keep `CONTROL_INVENTORY` in sync with these mandates by capturing canonical implementations, known extension points,
      and noted gaps that require follow-up; flag missing controls as provisional entries pending remediation
    - For every entry in `SPEC_REQUIREMENTS`, append a matching record to `REVIEW_REQUIREMENTS` with `source_requirement`
      set to the original `FR-###`; initialize each entry with `status="unverified"` until evidence or findings resolve it
    - Treat these requirements as authoritative; flag any observed deviation
    - When a mandate is ambiguous, raise `[Open Question]` entries, resolve them, and record outcomes in the decision log

8. Run pre-review gates

    - **Context Gate**: required dossier files exist; else → `Blocked: Missing Context`
    - **Change Intent Gate**: change aligns with POR; else → `Blocked: Scope Mismatch`
    - **Unknowns Gate**: unresolved `[NEEDS CLARIFICATION: …]` → `Needs Clarification`
    - **Requirements Coverage Gate**: every `FR-###` in `SPEC_REQUIREMENTS` maps to implementation/test evidence, an
      explicit finding, or a documented clarification request; otherwise → `Changes Requested` (missing implementation),
      `Needs Clarification` (ambiguous requirement), or `Blocked: Scope Mismatch` (requirement intentionally deferred)
    - **Separation of Duties Gate**: author cannot self-approve; emergency bypasses are exceptional and auditable
    - **Code Owners Gate**: changes under owned paths require owner approval (if CODEOWNERS configured)
    - **Quality Controls Gate**: linting/typing/formatting/CI guardrails untouched unless explicitly in scope; unexpected
      changes → `Quality Controls Violation`
    - **Security & Privacy Gate**: security/privacy checklist attached and applicable items addressed; else →
      `Security Gate Failure` or `Privacy Gate Failure`
    - **Supply Chain Gate**: dependency/SBOM/provenance checks enabled per policy (SLSA/CIS posture); else →
      `Supply Chain Violation`
    - **TDD Evidence Gate**: tests drive behavior or equivalent rationale; absence → `TDD Violation`
    - **Environment Gate**: required tooling available; blocked tooling must be resolved before proceeding

9. Collect objective evidence

    - Identify mandatory quality commands from `REVIEW_REQUIREMENTS` (e.g., lint, typecheck, test,
      build, contract checks); execute them repo-wide unless governance specifies a narrower scope
    - Capture pass/fail status and key diagnostics for each command; aggregate multiple errors per category into single
      findings
    - Establish baseline and current dependency snapshots using the project's package manager; compare for new
      vulnerabilities, deprecated packages, or policy breaches
    - Record runtime warnings or deprecation notices (non-blocking unless policy elevates)
    - Store raw outputs or pointers needed to substantiate findings without exposing secrets

10. Analyze implementation changes

    - Review diffs/files for compliance with each item in `REVIEW_REQUIREMENTS`
    - For each `FR-###` requirement, trace implementation changes and associated tests; cite concrete files, commands, or
      scenarios that satisfy the requirement, and open findings when evidence is absent or contradictory
    - Map changes to architecture layers or boundaries; flag violations or missing abstractions with proposed remediations
    - Verify cross-cutting controls (validation, logging, error handling, accessibility, performance, security,
      observability) adhere to the mandates
    - Prefer reuse: consult `CONTROL_INVENTORY` (and the broader codebase) before recommending new infrastructure
    - Evaluate test coverage for new behavior, error paths, and regressions; highlight gaps and recommend targeted tests
    - Inspect dependency additions/upgrades for justification, maintenance health, license alignment, and version currency
    - Note strengths that should be preserved (patterns, abstractions, tests, documentation)

11. Assemble review deliverables

    - Populate `/templates/review-template.md` exactly as structured; the template is the canonical output
      format.
    - Record the **Final Status** using the defined taxonomy:
      `Approved`, `Changes Requested`, `Blocked: Missing Context`, `Blocked: Scope Mismatch`, `Needs Clarification`,
      `TDD Violation`, `Quality Controls Violation`, `Security Gate Failure`, `Privacy Gate Failure`,
      `Supply Chain Violation`, `Dependency Vulnerabilities`, `Deprecated Dependencies`, `Review Pending`.
    - Complete the **Resolved Scope** section with branch, baseline, diff source, narrative, concrete paths, and
      implementation scope bullets grounded in the analyzed artifacts.
    - In **Findings**, order items from highest to lowest severity and provide the full metadata set for each entry:
      `category`, `severity`, `confidence`, `impact`, `evidence`, `remediation`, `source_requirement`, `files`.
    - Document **Strengths** with supporting citations and list outstanding `[NEEDS CLARIFICATION: …]` items in the
      dedicated section.
    - Publish the current `CONTROL_INVENTORY` in the provided table (or link to its structured artifact if stored
      elsewhere).
    - Summarize lint, typecheck, test, and build evidence under **Quality Signal Summary**, capturing status and key
      diagnostics for each command.
    - Capture **Dependency Audit Summary** details: baseline vs current severity counts, new CVEs, deprecated packages,
      justifications, and version currency observations.
    - Update the **Requirements Compliance Checklist** with pass/fail status and notes per requirement group.
    - Generate a **Requirements Coverage Table** sourced from `SPEC_REQUIREMENTS` with columns for requirement id, summary,
      implementation evidence, validating tests, and linked finding/clarification ids.
    - Append the **Decision Log** with resolved assumptions, constitutional interpretations, control reuse, and
      remediation-audit outcomes.
    - Ensure the **Remediation Logging** section is populated per Step 12 when high-severity findings or non-approved
      statuses are present.

12. Log remediation tasks

    - For every finding with severity `Critical`, `Major`, or final status other than `Approved`, draft remediation tasks
      that capture the exact file path, root cause, impact, recommended fix steps, and references to the relevant entry in
      `CONTROL_INVENTORY` when one exists
    - Prefer remediations that align with existing controls or explicitly document when the inventory confirms a gap
    - Surface these remediation drafts in a dedicated **Remediation Logging** section using the template
      `Context → Control Reference → Actions → Verification`
    - Ensure all tasks cite exact file paths, root cause, impact, and steps; link the `CONTROL_INVENTORY` entry (or state
      no reusable control exists)
    - If write-back cannot be completed, preserve the wording in the review output, note the blocking condition, and
      provide clear manual application instructions
    - Maintain a non-destructive posture; remediation logging updates remain the single authorized exception

13. Audit remediation alignment

    - Compare newly appended remediation tasks against `CONTROL_INVENTORY` and the findings to verify each task references
      an appropriate existing control or documented gap
    - If any task lacks that linkage, add a reviewer warning and update the remediation text before finalizing the review
    - Preserve the audit outcome (pass/warn) in the decision log

14. **MANDATORY** Archival write-back and task generation

    - Reference `FEATURE_DIR` gathered in Step 2.
    - Review output filing: present the rendered report to the
      operator, and overwrite (or create) `review.md` inside `FEATURE_DIR` with the contents of the report.
    - Open `tasks.md` in `FEATURE_DIR` and overwrite or create a **Phase 4.R: Review Follow-Up** section using
      the format defined in `/templates/tasks-template.md` with a new task per finding.
        - Each finding documented in the report must be represented as a new unchecked task in Phase 4.R with the pattern
          `- [ ] F{FINDING_ID} Finding {FINDING_ID}: {FINDING_TITLE} as described in review.md`. Reference `review.md`
          (or the specific evidence path) in the description when additional context is needed.

---

## Requirements Catalog (Global Normative Baseline)

> The following baseline requirements are **seeded into `REVIEW_REQUIREMENTS`** in Step 7. Add project-specific mandates
> and citations as needed.

### Governance & Process

- **GOV-01 Policy & Scope** — **MUST**: A published code-review policy defines when review is required, who may approve,
  and any exemptions. *Rationale*: Organizational control; auditability. *Source*: NIST SSDF PW.7.
- **GOV-02 Peer Review for Protected Branches** — **MUST**: All merges to protected branches require peer review.
  *Rationale*: Process integrity. *Source*: Platform enforcement + Microsoft Playbook.
- **GOV-03 Code Owners** — **MUST**: Owned paths require owner approval (where supported). *Rationale*: Expertise and
  risk control. *Source*: Platform + CIS supply-chain guidance.
- **GOV-04 Separation of Duties** — **MUST**: Authors cannot self-approve; emergency bypasses are exceptional, logged,
  and post-reviewed. *Rationale*: Change-control integrity. *Source*: SOC2/ISO change management norms.
- **GOV-05 Small, Focused Changes** — **SHOULD**: Prefer small, coherent CLs with clear descriptions and linked issues.
  *Rationale*: Improves review quality and speed. *Source*: Google Eng Practices.
- **GOV-06 Review SLAs** — **SHOULD**: First response within one business day; stale reviews escalated. *Rationale*:
  Flow efficiency. *Source*: Google Eng Practices.
- **GOV-07 Traceability** — **MUST**: Record reviewers, outcomes, timestamps, and linked issues in the PR. *Rationale*:
  Audit trail, learning. *Source*: NIST SSDF PW.7.

### Security & Privacy

- **SEC-01 Secure Coding Baseline** — **MUST**: Adopt and apply secure coding standards/checklists. *Rationale*:
  Systematic security. *Source*: OWASP ASVS; ISO 27002 8.28.
- **SEC-02 Threat-Relevant Review** — **MUST**: Examine authN/Z, input validation, secrets, crypto, injection, SSRF,
  deserialization, data exposure proportional to change risk. *Rationale*: Vulnerability prevention. *Source*: ASVS;
  OWASP Code Review Guide.
- **SEC-03 Expert Review for High-Risk Changes** — **MUST**: Security specialist reviews
  auth/crypto/sandbox/privilege-sensitive changes. *Rationale*: Depth for critical areas. *Source*: NIST SSDF PW.7
  examples.
- **SEC-04 Static Analysis & Secrets Gate** — **MUST**: Required SAST/linters/secret scanning pass before merge;
  findings triaged in PR. *Rationale*: Automated defense + human judgment. *Source*: NIST SSDF PW.7–PW.8.
- **SEC-05 Dependency Risk & SBOM** — **MUST**: New/updated dependencies pass vulnerability, license, and SBOM checks
  per policy. *Rationale*: Supply-chain risk control. *Source*: SLSA; CIS.
- **SEC-06 PCI Scope** — **MUST**: For cardholder-data impact, perform pre-release code review focused on security
  defects. *Rationale*: Regulatory compliance. *Source*: PCI DSS 6.3.2.
- **SEC-07 Privacy by Design** — **MUST**: For personal-data changes, verify minimization, lawful basis, access
  controls, data-by-default, and logging scrubs. *Rationale*: Privacy compliance. *Source*: GDPR Art. 25; CCPA.

### Quality & Maintainability

- **QUAL-01 Correctness & Tests** — **MUST**: New behavior has tests; affected tests updated; all tests pass.
  *Rationale*: Regression prevention. *Source*: Google Eng Practices.
- **QUAL-02 Readability & Consistency** — **SHOULD**: Follow project style; clear naming; comments explain non-obvious
  decisions. *Rationale*: Evolvability. *Source*: Google Eng Practices.
- **QUAL-03 Complexity Boundaries** — **SHOULD**: Flag excessive function/module complexity; request refactors when
  comprehension suffers. *Rationale*: Reviewability and reliability. *Source*: Empirical review research.
- **QUAL-04 Architecture & Interfaces** — **SHOULD**: Check API boundaries, error handling, compatibility impacts.
  *Rationale*: System integrity. *Source*: Google/Microsoft guidance.
- **QUAL-05 Documentation Deltas** — **MUST**: Update docs/runbooks/API references when behavior or interfaces change.
  *Rationale*: Operational clarity. *Source*: Microsoft; SRE checklists.

### Reliability & Operations

- **REL-01 Production Readiness** — **MUST**: For availability/perf-affecting changes, confirm monitoring, alerts,
  capacity estimates, rollback, and staged rollout/canaries. *Rationale*: Reduce incident risk. *Source*: Google SRE.
- **REL-02 Defensive Coding** — **SHOULD**: Verify timeouts, retries, circuit breakers, idempotency, and failure modes.
  *Rationale*: Resilience. *Source*: SRE practices.

### Testing & CI

- **TEST-01 Required Checks** — **MUST**: CI required status checks (build/tests/linters/SAST) block merge on failure.
  *Rationale*: Quality gate. *Source*: Platform + SSDF.
- **TEST-02 Security Testing Linkage** — **SHOULD**: For security-sensitive areas, include dynamic/fuzz/IAST evidence
  when applicable. *Rationale*: Complement code review. *Source*: SSDF PW.8.

### Accessibility (UI Changes)

- **A11Y-01 WCAG 2.2 AA** — **MUST**: UI changes meet WCAG 2.2 AA (keyboard/focus/contrast/accessible auth).
  *Rationale*: Legal/compliance/usability. *Source*: W3C/WAI.
- **A11Y-02 ARIA Use** — **SHOULD**: Prefer native semantics; apply ARIA per APG when needed. *Rationale*: Avoid harming
  accessibility. *Source*: WAI-ARIA APG.

---

## Checklists (to attach/evaluate per change)

> Attach the relevant checklist(s) to the PR and link them in the deliverable.

### Security & Privacy Checklist (subset)

- Secrets absent / not in code; env/secret manager used
- Input validation & output encoding; injection risks mitigated
- AuthN/Z flows and permission checks intact; least privilege enforced
- Sensitive data minimized; logging scrubs PII; retention noted
- Dependency diff reviewed; vulnerabilities triaged; licenses aligned
- High-risk changes reviewed by security specialist
- SBOM/provenance evidence captured if required by policy (SLSA target)

### Reliability & Operations Checklist (subset)

- Monitoring/metrics/alerts updated; SLO/SLA considerations noted
- Rollback plan & feature-flag strategy documented
- Timeouts/retries/circuit breakers; idempotency for retried ops
- Runbooks updated; on-call impacted teams notified if relevant

### Accessibility (UI) Checklist (subset)

- Keyboard navigation (tab order, focus visible), skip links if applicable
- Semantic structure correct; ARIA only where necessary
- Color/contrast meet WCAG AA; no color-only signalling
- Accessible authentication patterns where relevant

---

## Review Content (unchanged structure, augmented expectations)

- **Governance Inputs**: `SPEC_KIT_CONFIG`, constitution path, and any `SPEC_KIT_CONFIG.review.documents` define
  baseline guardrails and MUST be loaded before analysis. Confirm platform enforcement posture (protected branches,
  required checks, CODEOWNERS).
- **Prerequisite Signals**: Outputs from `/scripts/bash/check-implementation-prerequisites.sh --json` (
  especially `FEATURE_DIR` and `AVAILABLE_DOCS`) guide dossier discovery, command authorization, and absolute-path
  enforcement.
- **Feature Dossier**: Files inside `FEATURE_DIR` (`plan.md`, `tasks.md`, `research.md`, plus optional `data-model.md`,
  `contracts/`, `quickstart.md`) capture scope, risks, exclusions, and priorities; use as the authoritative source for
  `REVIEW_SCOPE_HINTS` and `REVIEW_DIRECTIVES`.
- **Scope & Assumptions**: Normalized `RESOLVED_SCOPE`, recorded sandbox/network/approval posture, and the
  assumption-handling strategy govern artifact inspection and `[Open Question]` handling.
- **Control Inventory**: Maintain a structured mapping of cross-cutting controls (logging, auth, telemetry, storage,
  observability, privacy, security) to implementations or known gaps; all mandates, recommendations, and remediations
  should reference these entries where reuse applies.
- **Requirement Catalog**: Combine template-derived gates, constitution mandates, feature-specific directives, and the *
  *Global Normative Baseline** into `REVIEW_REQUIREMENTS`; each requirement includes `id`, `name`, `level`, `rule`,
  `rationale`, `source`.
- **Evidence Expectations**: Quality commands (lint, typecheck, tests, builds, contract checks), dependency baselines vs
  current state, runtime warnings, and diff analyses supply objective signals that substantiate findings.
- **Analysis Dimensions**: Evaluate architecture alignment, cross-cutting controls, regression risks, dependency health,
  security posture, accessibility, performance, and documentation strength before concluding.
- **Deliverable Schema**: Review outputs MUST be rendered from `/templates/review-template.md`, populating every
  section (Final Status, Resolved Scope narrative, severity-ordered findings with metadata, strengths, outstanding
  `[NEEDS CLARIFICATION]` items, published `CONTROL_INVENTORY`, Quality Signal Summary, Dependency Audit Summary,
  Requirements Compliance Checklist, Decision Log, Remediation Logging).
- **Remediation Standards**: High-severity findings require tasks formatted
  `Context → Control Reference → Actions → Verification`, tied to the relevant control entry or documented gap.
- **Decision Logging**: Record assumptions, constitutional interpretations, control-reuse decisions, remediation audits,
  and `[Open Question]` outcomes for traceability.

---

## Roles & Responsibilities (for reviewers and authors)

- **Authors MUST**: keep CLs small/coherent; link tickets/design docs; run/fix CI; include/update tests; attach relevant
  checklists; request appropriate reviewers/owners; avoid self-approval.
- **Reviewers MUST**: check correctness/design/tests/security/privacy/operational impacts; insist on clarity; be civil
  and actionable; respond within SLA; approve when the CL clearly improves code health.
- **Automation SHOULD**: gate merges (required checks), run SAST/linters/formatters, dependency/SBOM/license checks,
  secret scanning, and (where applicable) verify provenance.

---

## Minimal Viable Set (quick reference)

1. Peer review required for merges to protected branches; no self-approval
2. Required CI checks pass (build/tests/linters/SAST/secret scan)
3. Security & privacy checklists completed; expert review for high-risk changes
4. Traceability (reviewers, outcomes, timestamps, evidence) captured in PR
5. Small, coherent CLs with clear descriptions; linked issue/design
6. Tests added/updated for new behavior; results visible in PR
7. Code Owners approval required for owned paths
8. Dependency/SBOM checks (vulns/licenses/provenance) per policy
9. Production readiness gates for availability/perf-sensitive changes
10. A11y gates for UI changes (WCAG 2.2 AA)
