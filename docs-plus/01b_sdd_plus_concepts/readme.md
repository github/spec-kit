# SDD++ — A Comprehensive Paper

**Title:** SDD++ — Spec‑Driven Development (Extended)

**Abstract**

SDD++ (Spec‑Driven Development Plus) is an evolution of traditional Spec‑Driven Development (SDD) that explicitly treats specifications, architecture history, prompt history, tests, and automated evaluations as first‑class artifacts. Where SDD focused primarily on specifications as source of truth, SDD++ expands this remit to include the full set of evidence and records that justify design and implementation choices, enabling traceability, reproducibility, and measurable quality control in modern software and AI‑augmented systems. This paper defines SDD++, explains all terminology and abbreviations, details its core components and practices, provides implementation patterns and examples, and offers adoption guidance for teams.

**Keywords:** SDD++, Spec‑Driven Development, AHR, PHR, evals, TDD, traceability, artifacts, ADR, evidence

---

## Table of Contents
1. Introduction
2. Motivation and Context
3. Definitions and Core Concepts
4. The SDD++ Architecture (Components & Artifacts)
5. Workflows and Practices
6. Tooling and Implementation Patterns
7. Governance, Compliance & Auditability
8. Metrics, KPIs and Eval Design
9. Example: Applying SDD++ to a Feature
10. Migration Strategy from SDD
11. Challenges, Risks and Anti‑Patterns
12. Organizational Roles & Responsibilities
13. Conclusion
14. Glossary & Abbreviations

---

## 1. Introduction

Spec‑Driven Development (SDD) has been a widely accepted approach where clear specifications are written up front and implementation follows those specifications. As systems have grown in complexity — particularly with the adoption of machine learning and LLMs — relying solely on static specifications is insufficient. Decisions are influenced by experiments, prompt design, architecture tradeoffs, and continuous automated evaluations. SDD++ extends SDD by making the additional artifacts and signals explicit and first‑class. SDD++ treats the development process as an evidence loop: specify, record, implement, evaluate, and iterate — with every artifact linked and discoverable.

## 2. Motivation and Context

Why extend SDD? Key drivers:

- **Reproducibility & Auditability:** In regulated or safety‑critical contexts, teams must show why a decision was made and what evidence supports it.
- **AI/LLM Integration:** Prompt engineering and model evals influence behavior but are often undocumented. PHR and evals capture that work.
- **Continuous Quality Measurement:** Automated evals quantify model or feature quality over time; they must be part of the artifact trail.
- **Traceability Needs:** Stakeholders (product, security, legal) demand traceable mappings from requirement to release.
- **Knowledge Preservation:** AHR and PHR preserve intent and rationale that would otherwise be lost.

SDD++ addresses these needs by embedding records and evaluative signals into the routine of development.

## 3. Definitions and Core Concepts

This section defines the central terms used in SDD++.

### Spec / Specification
A precise, testable description of intended behavior or requirements. A spec can be functional (e.g., an API contract), non‑functional (e.g., latency target), or behavioral (e.g., how an LLM should respond to a certain user intent). Specs are versioned artifacts and are the foundational input for tests and evaluations.

### SDD (Spec‑Driven Development)
The traditional approach where development is guided primarily by specifications. SDD++ is built on SDD but extends it.

### **SDD++ (Spec‑Driven Development Plus)**
An extended methodology where the spec remains foundational but is augmented by: architecture history records (AHR), prompt history records (PHR), automated evaluations (evals), test artifacts (TDD/BBD), and trace links between artifacts.

### AHR (Architecture History Record)
A structured log of architectural decisions, design tradeoffs, diagrams, versioned component maps, and the rationale for changes. AHR entries often include timestamp, author, decision, alternatives considered, and consequences.

### ADR (Architecture Decision Record)
A specific, commonly used format for recording architecture decisions; ADRs are often part of AHR tooling or repositories. ADRs are a unit within the AHR.

### PHR (Prompt History Record)
A versioned history of prompts, prompt templates, and prompt experiments used in LLM or prompt‑driven components. PHR records inputs, expected outputs, contextual settings (temperature, top‑k), performance metrics, and revision rationale.

### Artifact
Any file, record, or structured object used in development and governance: specs, tests, prompts, diagrams, ADRs, AHR entries, eval reports, and release notes.

### Traceability
The ability to map and navigate links between artifacts (e.g., requirement → spec → AHR entry → test → eval → code commit → release). Good traceability is bidirectional: you can trace forward and backward across artifacts.

### Evals (Evaluations)
Automated or manual evaluation runs that measure quality against specified metrics. Evals include unit tests, integration tests, model benchmarks, prompt sensitivity checks, fairness tests, and production monitoring metrics.

### TDD (Test‑Driven Development)
A practice of writing tests before code. In SDD++, tests are artifacts that are created along with specs and are key to evidence of correctness.

### BDD (Behavior‑Driven Development)
A style of specifying behavior in natural language (Given/When/Then) that often links to automated acceptance tests.

### SSOT (Single Source of Truth)
The artifact or repository that is considered the authoritative version of a piece of information (e.g., the approved spec or the artifact manager’s canonical copy).

### Evidence
Any artifact or result (test pass/fail, eval metric, PHR entry) that can be used to justify a decision or to demonstrate conformance to a spec.

### CI / CD (Continuous Integration / Continuous Delivery)
Automations that run tests and evaluations on changes, and that may manage artifact publishing or deployment pipelines.

### RAG (Retrieval‑Augmented Generation)
A common architecture pattern in LLM systems where external documents/records are retrieved and included in model context. PHR/AHR entries often feed retrieval indices for RAG systems.

## 4. The SDD++ Architecture (Components & Artifacts)

SDD++ defines a set of artifacts and components that together form the methodology.

### 4.1 Specification Repository
- **What:** Versioned specs (functional, non‑functional, behavior). Stored in a repo (Markdown, structured spec language, OpenAPI, or similar).
- **Why:** Specs are the starting point for tests, AHR entries, and eval objectives.
- **Best Practice:** Specs should include acceptance criteria and measurable success criteria.

### 4.2 Artifact Store / Index
- **What:** Central index or store for artifacts (AHR, PHR, ADRs, eval reports, test artifacts). Could be implemented via a git monorepo plus an artifact metadata index, or a dedicated artifact management system.
- **Why:** Enables discovery and traceability.

### 4.3 Architecture History Record (AHR)
- **Contents:** ADRs, decision logs, versioned topology diagrams, migration notes.
- **Format:** Structured markdown or JSON/YAML records with fields: id, title, date, author, decision, alternatives, rationale, impact, related artifacts.

### 4.4 Prompt History Record (PHR)
- **Contents:** Prompt templates, sample inputs/outputs, context windows, model config (temperature), eval runs, changelog entries.
- **Format:** Versioned JSON/YAML with fields: prompt_id, version, created_by, created_at, model_version, prompt_text, example_inputs, expected_outputs, metrics, rationale, linked_spec_id.

### 4.5 Tests & TDD Artifacts
- **Unit tests:** Small, fast tests validating components.
- **Integration tests:** Validate interaction between components including LLM/API calls.
- **Acceptance tests / BDD scenarios:** High‑level tests reflecting spec acceptance criteria.
- **Test metadata:** Link tests to spec IDs and AHR/PHR where appropriate.

### 4.6 Evals & Metrics
- **Evaluation Suites:** Collections of automated checks that run in CI and in scheduled evaluative pipelines.
- **Metric types:** accuracy, F1, latencies, throughput, hallucination rate, fairness metrics, stability under prompt variations.
- **Eval Reports:** Versioned output of eval runs with links to commit IDs, PHR versions, and spec IDs.

### 4.7 Code Implementation & Commits
- **Conventions:** Commits reference spec IDs, test IDs, and ADR/AHR entries.
- **Trace links:** Each PR should include artifact evidence (test results, eval summary) and reference to relevant spec/PHR/AHR IDs.

### 4.8 Dashboard & Trace Explorer
- **What:** A UI that can show trace relationships and present the most relevant evidence for a release or change.
- **Why:** Improves stakeholder visibility.

## 5. Workflows and Practices

### 5.1 Spec‑First Workflow (Core)
1. Create or update a spec (include acceptance criteria and measurable metrics).
2. Create linked test artifacts (unit + acceptance) that express spec expectations.
3. Capture any architectural decisions in AHR/ADRs that the spec requires.
4. If feature uses LLMs, create initial PHR entry (prompt template + example interactions).
5. Implement code with TDD where possible, referencing spec and tests in commits and PRs.
6. Run automated evals; record results as eval reports linked to the feature.
7. Iterate: refine spec/PHR/AHR/tests based on evals and production monitoring.

### 5.2 Eval‑Driven Iteration
- Treat evals as gates: failing to meet spec metrics triggers a loop back to spec or PHR refinement.
- Use scheduled evals (nightly/weekly) to track model drift or regressions.

### 5.3 Artifact Reviews
- Expand code reviews to include artifact reviews. PRs should include checks that linked artifacts exist and are up to date.

### 5.4 Traceability Enforcement
- Enforce metadata requirements in CI (e.g., PR must reference spec ID and include an eval summary or link to the eval report).

### 5.5 Prompt/Model Experiment Management
- Version prompts as part of PHR; run controlled A/B style experiments and store results in eval reports; only promote prompt versions that meet acceptance criteria.

## 6. Tooling and Implementation Patterns

SDD++ is methodology‑agnostic but benefits from certain tooling patterns.

### 6.1 Repositories and Artifact Layout
- Keep a clear repo layout: `/specs/`, `/ahr/`, `/phr/`, `/tests/`, `/evals/`, `/src/`.
- Use metadata files for each artifact linking IDs to upstream/downstream artifacts.

### 6.2 CI/CD Integration
- CI pipelines should run: static checks, unit/integration tests, and a fast eval subset on PRs.
- CD pipelines should reference artifact evidence before promoting to staging/production.

### 6.3 Artifact Metadata and Indexing
- Maintain a small metadata index (YAML/JSON) where each artifact has: id, type, status, linked_artifacts, owners, created_at, updated_at.

### 6.4 Evaluation Pipelines
- Maintain separate evaluation pipelines: quick smoke eval on PR; deeper nightly evals; full benchmark before release.

### 6.5 Prompt Management
- Treat prompt templates like code: linting, templating, parameterized variables, and version control.

### 6.6 AHR/ADR Workflows
- Use ADR templates to log architecture choices; link ADRs to change requests and spec IDs.

## 7. Governance, Compliance & Auditability

For organizations with compliance requirements, SDD++ offers concrete value:

- **Audit Trails:** AHR and PHR entries plus eval reports provide a documented trail for regulators.
- **Change Control:** With artifact linkage, changes are reviewed in context.
- **Data Provenance:** Evals can include dataset versions and training or fine‑tune metadata, improving provenance.
- **Retention Policies:** Artifacts must be retained according to policy (e.g., 3–7 years in regulated industries).

## 8. Metrics, KPIs and Eval Design

Define metrics that map directly to spec acceptance criteria. Examples:

- **Functional correctness:** Pass rate of acceptance tests (binary pass/fail).
- **Quality metrics:** Precision/recall, F1, BLEU, ROUGE (for text tasks), task‑specific accuracy.
- **Stability metrics:** Variance in outputs across prompt paraphrases.
- **Safety metrics:** Rate of unsafe outputs triggered by adversarial prompts.
- **Operational metrics:** Latency, error rate, CPU/memory usage.

Eval design should ensure tests are reproducible and linked to specific PHR/AHR versions and dataset snapshots.

## 9. Example: Applying SDD++ to a Feature

**Feature:** "Smart Reply" for a customer support app that suggests short reply candidates for incoming user messages.

### Steps (illustrative):

1. **Spec (spec-001)**
   - *Functional:* For messages categorized as "transactional", provide 3 suggested replies of length ≤ 120 chars. Recommendations must have a diversity score ≥ 0.6 and relevance score ≥ 0.8.
   - *Non‑Functional:* Latency ≤ 200ms P95.
   - *Acceptance Criteria:* Automated scenario tests showing 90% relevance on test set.

2. **AHR (ahr-010)**
   - ADR: Choose RAG architecture with a small context store versus purely generative model. Rationale: retrieval increases factual consistency for transactional replies.

3. **PHR (phr-021, v1)**
   - Prompt template with placeholders, example inputs/outputs, model config (`temperature=0.2`), and a note: "use conservative tone for transactional replies".

4. **Tests**
   - Unit tests for pre/post processing.
   - Integration tests that call LLM with PHR v1 and assert response format.
   - Acceptance tests (BDD scenarios) referencing spec-001.

5. **Evals**
   - Eval suite runs over curated dataset measuring relevance, diversity, latency. Results stored in `evals/` with references to `phr-021@v1` and code commit hash.

6. **Implementation & PR**
   - PR description references `spec-001`, `phr-021`, `ahr-010`, and includes a link to the eval report. CI runs smoke eval; nightly pipeline runs full eval.

7. **Iterate**
   - If eval shows relevance < 0.8, refine prompt (PHR v2) or adjust retrieval pipeline; log changes and rationale.

This structure ensures each change contains evidence and is reproducible.

## 10. Migration Strategy from SDD

For teams already practicing SDD, migration to SDD++ is incremental:

1. **Identify critical artifacts to capture first:** start with ADRs (AHR) and acceptance tests.
2. **Introduce minimal PHR:** when an LLM is involved, start capturing prompt templates and experiments.
3. **Add eval pipelines:** begin with smoke evals in PRs, expand to nightly runs.
4. **Enforce metadata in PRs:** require references to spec IDs and at least one linked artifact.
5. **Train teams:** run workshops on ADRs, PHR practices, and writing measurable specs.

## 11. Challenges, Risks and Anti‑Patterns

### Challenges
- **Overhead:** Additional artifacts add maintenance cost. Mitigation: automate artifact generation and linking.
- **Artifact rot:** Stale artifacts reduce trust. Mitigation: define ownership and update gates.
- **Too much traceability noise:** Excessive links make discovery hard. Mitigation: clear metadata taxonomy and search UI.

### Anti‑Patterns
- **Artifacts as bureaucracy:** Creating records to satisfy process rather than to add value.
- **Unlinked artifacts:** Documents that are never linked to code or tests.
- **PHR sprawl:** Many ad‑hoc prompt variants without evaluation.

## 12. Organizational Roles & Responsibilities

- **Product Owner:** Defines measurable acceptance criteria in specs.
- **Architect / System Designer:** Maintains AHR/ADRs and links architectural decisions to specs.
- **Prompt Engineer (when applicable):** Owns PHR entries and experiments.
- **Developer:** Writes code and tests; links commits/PRs to artifacts.
- **QA / SRE:** Author and maintain eval suites and operational metrics.
- **Reviewer / Gatekeeper:** Ensures PRs include necessary artifact links and evidence.

## 13. Conclusion

SDD++ modernizes Spec‑Driven Development by elevating the artifacts that matter in contemporary systems: architecture history, prompt history, tests, and automated evaluations. It preserves the clarity of spec‑first design while adding the audits, evidence, and continuous measurement necessary for AI‑augmented, safety‑sensitive, and highly regulated systems. When adopted judiciously and supported by automation, SDD++ improves reproducibility, traceability, and the ability of organizations to prove correctness.


---

## 14. Glossary & Abbreviations

Below are the abbreviations and terms used in this paper with concise explanations.

- **SDD:** Spec‑Driven Development — development approach centered on specifications.
- **SDD++:** Spec‑Driven Development Plus — extended SDD that includes AHR, PHR, evals, and tests as first‑class artifacts.
- **Spec:** Specification — a precise, versioned description of expected behavior.
- **AHR:** Architecture History Record — structured record of architecture decisions and rationale.
- **ADR:** Architecture Decision Record — a formal entry recording a specific architecture decision (often part of AHR).
- **PHR:** Prompt History Record — versioned history of prompts and prompt experiments used with LLMs.
- **TDD:** Test‑Driven Development — practice of writing tests before code.
- **BDD:** Behavior‑Driven Development — specification style using human‑readable scenarios (Given/When/Then).
- **Eval / Evals:** Evaluation(s) — automated or manual evaluation runs and their results.
- **Artifact:** Any doc, test, prompt, ADR, AHR entry, or other stored object used in development.
- **Traceability:** The ability to map and traverse relationships between artifacts.
- **SSOT:** Single Source of Truth — the authoritative artifact or repository for a piece of information.
- **CI/CD:** Continuous Integration / Continuous Delivery — automation for building, testing, and delivering software.
- **RAG:** Retrieval‑Augmented Generation — LLM architecture pattern that uses external documents as context.
- **KPI:** Key Performance Indicator — measurable value tied to business or technical goals.
- **Prompt:** Input template or instruction given to an LLM to elicit desired behavior.
- **Prompt Engineer:** A role that designs and experiments with prompts for LLMs.
- **Artifact Store:** Storage and index for artifacts.
- **Eval Suite:** A collection of evaluations designed to measure system quality.

---

### Appendix A: Example Artifact Schemas (YAML/JSON style)

**Spec (YAML)**

```yaml
id: spec-001
title: Smart Reply for Transactional Messages
created_by: product@company.com
created_at: 2025-09-29
acceptance_criteria:
  - id: ac-1
    description: Provide 3 replies, <=120 chars
    metric: relevance >= 0.8
  - id: ac-2
    description: P95 latency <= 200ms
linked_artifacts:
  - ahr-010
  - phr-021
  - tests/acceptance/smart_reply.spec
```

**PHR (JSON)**

```json
{
  "prompt_id": "phr-021",
  "version": "v1",
  "created_by": "prompteng@company.com",
  "created_at": "2025-09-29T10:00:00Z",
  "model": "llm‑v1",
  "prompt_template": "Given the customer message: {{message}}\nProvide 3 short reply suggestions:",
  "config": {"temperature": 0.2, "max_tokens": 80},
  "examples": [
    {"input": "Where is my order?", "expected": ["Your order is on the way", "It will arrive tomorrow", "I'll check and update you"]}
  ],
  "linked_spec": "spec-001"
}
```

**AHR / ADR (Markdown)**

```markdown
# ADR-010: Choose RAG for Smart Reply
Date: 2025-09-29
Status: Accepted
Context: Transactional replies require factual consistency and use of account data.
Decision: Use retrieval augmention to include recent account info before generating suggestions.
Consequences: Added retrieval component; increased latency but higher factual accuracy.
Related: spec-001, phr-021
```

**Eval Report (YAML)**

```yaml
id: eval-073
created_at: 2025-09-30
linked_phr: phr-021@v1
linked_spec: spec-001
metrics:
  relevance: 0.82
  diversity: 0.62
  latency_p95_ms: 190
notes: "Passes acceptance criteria for relevance and latency. Diversity above threshold."
```

---

*End of document.*

