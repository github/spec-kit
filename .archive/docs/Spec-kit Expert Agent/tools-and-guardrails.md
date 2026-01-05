# tools-and-guardrails.md

## Tools (LLM-facing contracts)

### 1) create_feature
**Maps to**: `scripts/create-new-feature.sh --json "<desc>"`  
**Input**:
```json
{ "description": "Short imperative feature description" }
````

**Success Output**:

```json
{ "BRANCH_NAME":"001-login-flow","SPEC_FILE":"/abs/path/specs/001-login-flow/spec.md","FEATURE_NUM":"001" }
```

**Failure Modes**:

* `E_CREATE_FEATURE/NO_DESC`: empty description
* `E_CREATE_FEATURE/GIT`: git missing or repo not initialized
* `E_CREATE_FEATURE/JSON`: non-JSON stdout
  **Safety**:
* Non-destructive; creates a new branch and copies the spec template only.

---

### 2) setup\_plan

**Maps to**: `scripts/setup-plan.sh --json`
**Output**:

```json
{
  "FEATURE_SPEC":"/abs/.../specs/001-login-flow/spec.md",
  "IMPL_PLAN":"/abs/.../specs/001-login-flow/plan.md",
  "SPECS_DIR":"/abs/.../specs/001-login-flow",
  "BRANCH":"001-login-flow"
}
```

**Failure Modes**:

* `E_PLAN/BRANCH`: not on a feature branch
* `E_PLAN/SPEC_MISSING`: `FEATURE_SPEC` does not exist
* `E_PLAN/JSON`: non-JSON stdout

---

### 3) get\_paths

**Maps to**: `scripts/get-feature-paths.sh` (read-only)
**Output Keys (all absolute)**: `REPO_ROOT, BRANCH, FEATURE_DIR, FEATURE_SPEC, IMPL_PLAN, TASKS`
**Failure Modes**:

* `E_PATHS/BRANCH`: not on feature branch

---

### 4) fs.read(path)

Returns file text or error `{ code, cause }`.
**Guard**: Only allow paths under repo root.

### 5) fs.write(path, content, mode="replace")

Overwrites entire file; ensures parent directory exists.
**Guard**: Only within repo root; reject path traversal.

### 6) json.parse(text) / json.stringify(obj)

Strict JSON; on parse error, stop current phase with `E_JSON/PARSE`.

---

## Guardrails (derived from repo methodology)

* **Constitution gates** must pass or block with explicit justification. Record violations and STOP with remediation steps.
* **NEEDS CLARIFICATION** markers required for any ambiguity; do not silently assume defaults.
* **TDD ordering**: generate tests before implementation in `tasks.md`; contract and integration tests precede core tasks.
* **Parallelization rule**: mark `[P]` only when tasks do not touch the same files. If they would, make them sequential.
* **Absolute paths only** to avoid ambiguous file writes.
* **No external side effects**: no package installs, network calls, or code execution beyond listed scripts and file operations.
* **Stop-after-phase**: never chain `/specify → /plan → /tasks` in one run; the human must review at each gate.

---

## Unsafe Patterns (block and explain)

* Writing outside `/specs/<branch>/…` or `/memory/…`
* Skipping constitution checks
* Removing or reordering template headings
* Collapsing `[NEEDS CLARIFICATION]` into guesses
* Creating parallel tasks that modify the same file
* Proceeding to implementation within `/plan` phase

---

## Safe Patterns (encouraged)

* Short, checklist-style summaries + final JSON `REPORT`
* Explicit dependency graphs in `tasks.md`
* Minimal diffs and exact file lists per task
* Visible, greppable markers: `GATE:`, `ERROR:`, `NEEDS CLARIFICATION:`

## Software Development Best Practices
- **Spec-first & plan-reviewed:** Specs define scope. Plans gate implementation. No code before spec/plan gates pass.
- **TDD precedence:** Write/lock contract & integration tests before feature code. Tests must be deterministic and isolated.
- **Small batches:** Prefer short feature loops and minimal diffs. Decompose until parallel-safe (`[P]`) is clear.
- **Explicit contracts:** Every endpoint/service/model change updates contracts and acceptance criteria.
- **Version control discipline:** One branch per feature; atomic commits; meaningful messages; PRs reference specs.
- **Documentation as code:** Keep `spec.md`, `plan.md`, `tasks.md` current; corrections happen at the source files.
- **Dependency hygiene:** Pin versions; avoid needless frameworks; remove dead deps; verify licenses.
- **Configuration management:** No secrets in repo; use `.env.example`; document required vars.
- **Security baseline:** Least privilege; input validation; output encoding; authn/authz checks; audit logging where relevant.
- **Performance & reliability:** Measure before optimizing; capture SLOs; add basic health checks where applicable.
- **Observability:** Structured logs; minimal, actionable metrics; error taxonomies with remediation guidance.
- **CI/CD gates (conceptual):** Lint → Build → Test (unit/contract/integration) → Security scan → Docs check.