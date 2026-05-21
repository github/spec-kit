# Architecture Reverse Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/speckit.arch.reverse`, a repo-facts-first workflow that reverse-generates architecture SSOT artifacts from ordinary historical repositories.

**Architecture:** The feature adds one evidence artifact ahead of the existing 4+1 architecture files. Setup scripts create the new repo facts file from a template and expose `REPO_FACTS_FILE` in JSON. The new command writes repo facts first, then derives the existing five views and synthesis with explicit source-traceability gates.

**Tech Stack:** Markdown command/templates, YAML extension metadata, Bash setup script, PowerShell setup script, shell-based verification.

---

## File Structure

- Create `templates/architecture-repo-facts-template.md`: evidence-layer artifact template used by reverse workflow.
- Create `commands/speckit.arch.reverse.md`: command definition and workflow instructions for reverse generation.
- Modify `scripts/bash/setup-arch.sh`: define `REPO_FACTS_FILE`, copy repo facts template when missing, include it in JSON/plain output.
- Modify `scripts/powershell/setup-arch.ps1`: same behavior as Bash setup.
- Modify `extension.yml`: register `speckit.arch.reverse`.
- Modify `README.md`: document generate vs reverse usage and seven reverse-written files.
- Modify `CHANGELOG.md`: record the new command in Unreleased.
- Modify `CATALOG-SUBMISSION.md`: update command count and feature summary if preparing catalog metadata in this branch.

## Task 1: Add Repo Facts Template

**Files:**
- Create: `templates/architecture-repo-facts-template.md`

- [ ] **Step 1: Create the repo facts template**

Use this exact file content:

```markdown
# Architecture Repo Facts: [PROJECT]

**Purpose**: Record observable repository facts that support reverse generation of the project-level 4+1 architecture artifacts.

**Note**: This evidence file is filled in by the `__SPECKIT_COMMAND_ARCH_REVERSE__` command before the architecture views are updated. It is a fact source for architecture reasoning, not an implementation audit report.

## Repository Identity

| Fact | Evidence Source | Confidence | Architecture Relevance |
|------|-----------------|------------|--------------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Entry Points

| Entry Point | Type | Evidence Source | Observed Responsibility | Supported Scenario |
|-------------|------|-----------------|--------------------------|--------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## User-Visible Behaviors

| Behavior | Evidence Source | Actor / Trigger | Observable Outcome | Supported Use Case |
|----------|-----------------|-----------------|--------------------|--------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## System Boundaries

| Boundary | Evidence Source | Inbound Interaction | Outbound Interaction | Not Proven |
|----------|-----------------|---------------------|----------------------|------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Data and State Clues

| Fact / Entity | Evidence Source | Observed Lifecycle Clue | Fact Source | Not Proven |
|---------------|-----------------|-------------------------|-------------|------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Runtime and Process Clues

| Runtime Fact | Evidence Source | Trigger / Handoff | Failure or Retry Clue | Not Proven |
|--------------|-----------------|-------------------|-----------------------|------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Development Structure Clues

| Module / Package Area | Evidence Source | Observed Responsibility | Dependency Clue | Boundary Risk |
|-----------------------|-----------------|--------------------------|-----------------|---------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Physical / Deployment Clues

| Deployment Fact | Evidence Source | Environment / External System | Operational Constraint | Not Proven |
|-----------------|-----------------|-------------------------------|------------------------|------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Git History Signals

| Signal | Evidence Source | Architecture Meaning | Confidence | Review Trigger |
|--------|-----------------|----------------------|------------|----------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Evidence Gaps

| Gap | Affected View | Why It Blocks Architecture Conclusion |
|-----|---------------|----------------------------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Evidence Rules

- Every non-placeholder fact must name an evidence source such as a file, directory, configuration, test, script, manifest, command output, or commit signal.
- Confidence values are `High`, `Medium`, or `Low`.
- `High` means multiple independent sources agree, or docs/tests and code entry points agree.
- `Medium` means one strong source is present, such as clear configuration, entry point, route declaration, or behavior test.
- `Low` means naming, directory structure, isolated code, or Git history suggests a fact but lacks behavior evidence.
- Git history is an auxiliary signal for change axes and boundary risks. It cannot independently prove architecture conclusions.
- Concrete classes, functions, fields, endpoints, database tables, and implementation data structures may appear only as evidence sources, not architecture conclusions.
```

- [ ] **Step 2: Verify placeholder consistency**

Run:

```bash
rg -n "NEEDS REPO FACTS UPDATE" templates/architecture-repo-facts-template.md
```

Expected: matches in each table body. No command failure.

- [ ] **Step 3: Commit**

```bash
git add templates/architecture-repo-facts-template.md
git commit -m "feat: add architecture repo facts template"
```

## Task 2: Update Setup Scripts for Repo Facts File

**Files:**
- Modify: `scripts/bash/setup-arch.sh`
- Modify: `scripts/powershell/setup-arch.ps1`

- [ ] **Step 1: Update Bash setup path variables**

In `scripts/bash/setup-arch.sh`, add this variable after `ARCH_FILE`:

```bash
REPO_FACTS_FILE="$ARCH_DIR/architecture-repo-facts.md"
```

- [ ] **Step 2: Update Bash template copying**

In `scripts/bash/setup-arch.sh`, add this call before copying the synthesis template:

```bash
copy_template_if_missing "architecture-repo-facts-template" "$REPO_FACTS_FILE"
```

- [ ] **Step 3: Update Bash JSON output**

In the `jq -cn` block, add:

```bash
--arg repo_facts_file "$REPO_FACTS_FILE" \
```

and include the field in the object:

```bash
REPO_FACTS_FILE:$repo_facts_file,
```

In the fallback `printf`, change the JSON format to:

```bash
printf '{"ARCH_FILE":"%s","ARCH_DIR":"%s","REPO_FACTS_FILE":"%s","SCENARIO_VIEW":"%s","LOGICAL_VIEW":"%s","PROCESS_VIEW":"%s","DEVELOPMENT_VIEW":"%s","PHYSICAL_VIEW":"%s"}\n' \
    "$(json_escape "$ARCH_FILE")" \
    "$(json_escape "$ARCH_DIR")" \
    "$(json_escape "$REPO_FACTS_FILE")" \
    "$(json_escape "$SCENARIO_VIEW")" \
    "$(json_escape "$LOGICAL_VIEW")" \
    "$(json_escape "$PROCESS_VIEW")" \
    "$(json_escape "$DEVELOPMENT_VIEW")" \
    "$(json_escape "$PHYSICAL_VIEW")"
```

- [ ] **Step 4: Update Bash plain output**

Add this line after `ARCH_DIR`:

```bash
echo "REPO_FACTS_FILE: $REPO_FACTS_FILE"
```

- [ ] **Step 5: Update PowerShell setup path variables**

In `scripts/powershell/setup-arch.ps1`, add this variable after `$archFile`:

```powershell
$repoFactsFile = Join-Path $archDir "architecture-repo-facts.md"
```

- [ ] **Step 6: Update PowerShell template copying**

Add this call before copying the synthesis template:

```powershell
Copy-TemplateIfMissing -TemplateName "architecture-repo-facts-template" -Destination $repoFactsFile
```

- [ ] **Step 7: Update PowerShell JSON and plain output**

In the `[PSCustomObject]` block, add:

```powershell
REPO_FACTS_FILE = $repoFactsFile
```

In the plain output block, add this line after `ARCH_DIR`:

```powershell
Write-Output "REPO_FACTS_FILE: $repoFactsFile"
```

- [ ] **Step 8: Verify Bash setup in a temporary ordinary repository**

Run:

```bash
tmpdir=$(mktemp -d)
git -C "$tmpdir" init >/dev/null
mkdir -p "$tmpdir/.specify/extensions/arch"
cp -R commands scripts templates "$tmpdir/.specify/extensions/arch/"
cd "$tmpdir"
.specify/extensions/arch/scripts/bash/setup-arch.sh --json
test -f .specify/memory/architecture-repo-facts.md
test -f .specify/memory/architecture.md
```

Expected: JSON includes `REPO_FACTS_FILE`; both `test` commands exit 0.

- [ ] **Step 9: Verify PowerShell setup when `pwsh` is available**

Run:

```bash
if command -v pwsh >/dev/null 2>&1; then
  tmpdir=$(mktemp -d)
  git -C "$tmpdir" init >/dev/null
  mkdir -p "$tmpdir/.specify/extensions/arch"
  cp -R commands scripts templates "$tmpdir/.specify/extensions/arch/"
  cd "$tmpdir"
  pwsh -NoProfile -File .specify/extensions/arch/scripts/powershell/setup-arch.ps1 -Json
  test -f .specify/memory/architecture-repo-facts.md
else
  echo "pwsh not installed; skip PowerShell runtime verification"
fi
```

Expected: if `pwsh` is installed, JSON includes `REPO_FACTS_FILE` and the file exists. If not installed, output says the check was skipped.

- [ ] **Step 10: Commit**

```bash
git add scripts/bash/setup-arch.sh scripts/powershell/setup-arch.ps1
git commit -m "feat: create repo facts artifact in setup"
```

## Task 3: Add Reverse Command

**Files:**
- Create: `commands/speckit.arch.reverse.md`

- [ ] **Step 1: Create reverse command document**

Use this exact file content:

````markdown
---
description: Reverse-generate 4+1 architecture artifacts from observable repository facts.
scripts:
  sh: .specify/extensions/arch/scripts/bash/setup-arch.sh --json
  ps: .specify/extensions/arch/scripts/powershell/setup-arch.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Reverse-generate or refresh the project-level architecture SSOT for an ordinary historical repository by first recording observable repository facts, then deriving 4+1 architecture artifacts from those facts.

The workflow writes:

- Repo facts: `.specify/memory/architecture-repo-facts.md`
- Main synthesis: `.specify/memory/architecture.md`
- Scenario view: `.specify/memory/architecture-scenario-view.md`
- Logical view: `.specify/memory/architecture-logical-view.md`
- Process view: `.specify/memory/architecture-process-view.md`
- Development view: `.specify/memory/architecture-development-view.md`
- Physical view: `.specify/memory/architecture-physical-view.md`

`architecture-repo-facts.md` is the evidence layer for this reverse pass. The six architecture files remain the architecture SSOT. They must summarize architecture conclusions, not become source-code audit reports.

## Operating Boundaries

- Write only the seven files listed above.
- Do not modify source code, README files, project documentation, package files, configuration, tests, deployment files, `.specify/memory/uc.md`, `.specify/memory/constitution.md`, feature specs, plans, tasks, root `docs/`, deployment manifests, or runbooks.
- Do not require `.specify/memory/uc.md`.
- Stay at abstract architecture-design level.
- Do not write concrete classes, files, functions, endpoints, DTO fields, database table fields, framework selections, library choices, UI component details, deployment manifests, task breakdowns, test strategy, validation anchors, code notes, deployment scripts, or runbooks into the architecture views.
- If evidence is insufficient, record a specific gap in the repo facts file and affected view instead of inventing business facts, actors, use cases, components, interfaces, modules, deployment units, or numeric metrics.

## Evidence Sources

Inspect the repository for observable facts. Prefer concise inventory over exhaustive source listing.

Use these source categories when present:

- README and project documentation
- Source layout and named entry points
- Package manager files and build scripts
- Configuration and environment examples
- Tests, fixtures, examples, and sample data
- CLI commands, API routes, UI routes, scheduled jobs, workers, middleware, or event handlers
- CI/CD definitions
- Docker, Compose, Kubernetes, Terraform, or deployment configuration
- Operational scripts
- Recent Git history signals

Git history is auxiliary. It may indicate change axes, hotspots, and boundary risks, but it must not independently prove an architecture conclusion.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_DIR`, `REPO_FACTS_FILE`, `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, and `PHYSICAL_VIEW`.
2. **Load templates and existing artifacts**:
   - Read the seven architecture artifacts created by setup.
   - Read the seven architecture templates under `.specify/extensions/arch/templates/`.
3. **Build repo fact inventory**:
   - Identify repository identity, entry points, visible behaviors, boundaries, state clues, runtime clues, development structure, deployment clues, and Git history signals.
   - Assign confidence: `High`, `Medium`, or `Low`.
4. **Write repo facts**:
   - Fill `REPO_FACTS_FILE` using the repo facts template.
   - Every non-placeholder fact must name an evidence source.
5. **Derive scenario view**:
   - Derive actors, triggers, use cases, paths, branches, and acceptance semantics from repo facts.
6. **Derive logical view**:
   - Derive capability boundaries, domain objects, states, relationships, and invariants from scenario facts and repo facts.
7. **Derive process view**:
   - Derive runtime links, handoffs, retries, approvals, receipts, and failure closure from repo facts plus scenario and logical views.
8. **Derive development view**:
   - Derive architecture-level components and package boundaries from repo facts plus logical and process views.
9. **Derive physical view**:
   - Derive deployment, external systems, fact sources, observability, and operations constraints from repo facts plus process and development views.
10. **Update synthesis**:
   - Update `ARCH_FILE` using the synthesis template and all completed source artifacts.
11. **Stop and report**:
   - Report the seven updated paths and explicit unresolved architecture gaps.

## Inference Rules

- README, docs, CLI help, API route declarations, UI routes, tests, and examples primarily support scenario view.
- Package directories, module boundaries, imports, configuration ownership, and test grouping primarily support development view.
- State fields, migrations, schema files, fixtures, domain naming, and persistence configuration may support logical view, but cannot alone prove a complete domain model.
- Workers, queues, schedulers, middleware, async jobs, transactions, retries, locks, event handlers, approvals, and receipts may support process view when evidence sources are named.
- Dockerfiles, Compose files, Kubernetes manifests, Terraform, CI/CD, environment examples, and service configuration may support physical view.
- Low-confidence facts may appear in evidence gaps or view gaps, but must not become architecture conclusions.
- Concrete class names, function names, DTO fields, database table fields, endpoint details, and implementation data structures may appear only as evidence sources, not architecture conclusions.

## Confidence

- `High`: multiple independent sources agree, or docs/tests and code entry points agree.
- `Medium`: one strong source is present, such as clear configuration, entry point, route declaration, or behavior test.
- `Low`: naming, directory structure, isolated code, or Git history suggests a fact but lacks behavior evidence.

## Quality Gates

- ERROR if an architecture conclusion has no repo fact source or stated external constraint source.
- ERROR if the repo facts file contains generic claims without file paths, directories, configuration, tests, or commit signals.
- ERROR if 4+1 views promote classes, functions, fields, endpoints, database structure, or implementation details into architecture conclusions.
- ERROR if Git history signals are used alone as architecture conclusions.
- ERROR if physical view invents deployment units not visible from repo facts.
- GAP if actors, use cases, authority boundaries, runtime processes, or deployment topology cannot be supported by repository evidence.
- GAP if the repository lacks deployment, runtime, or business documentation. Missing evidence does not block generation, but it must be explicit.

## Quality Bar

- `architecture-repo-facts.md` must contain enough evidence for every non-gap architecture conclusion.
- Every non-placeholder architecture conclusion must be grounded in a repo fact, scenario, object, runtime link, component boundary, deployment boundary, or stated external constraint.
- Use stable names consistently across repo facts, all five views, and synthesis.
- Keep uncertainty specific: record what is unknown, which view it affects, and which architecture conclusion cannot yet be made.
- Remove generic statements such as "scalable", "secure", "observable", or "modular" unless they name owner, affected view, scope, evidence source, and architecture consequence.
````

- [ ] **Step 2: Verify command references setup JSON fields**

Run:

```bash
rg -n "REPO_FACTS_FILE|architecture-repo-facts.md|Write only the seven" commands/speckit.arch.reverse.md
```

Expected: all three terms are present.

- [ ] **Step 3: Commit**

```bash
git add commands/speckit.arch.reverse.md
git commit -m "feat: add architecture reverse command"
```

## Task 4: Register Extension Metadata

**Files:**
- Modify: `extension.yml`

- [ ] **Step 1: Add reverse command to `provides.commands`**

Update the `provides.commands` section to include:

```yaml
    - name: speckit.arch.reverse
      file: commands/speckit.arch.reverse.md
      description: "Reverse-generate 4+1 architecture artifacts from observable repository facts"
```

The full section should become:

```yaml
provides:
  commands:
    - name: speckit.arch.generate
      file: commands/speckit.arch.generate.md
      description: "Execute the 4+1 architecture workflow and generate architecture view artifacts"
    - name: speckit.arch.reverse
      file: commands/speckit.arch.reverse.md
      description: "Reverse-generate 4+1 architecture artifacts from observable repository facts"
```

- [ ] **Step 2: Verify both commands are registered**

Run:

```bash
rg -n "speckit\\.arch\\.(generate|reverse)" extension.yml
```

Expected: two matches, one for `generate` and one for `reverse`.

- [ ] **Step 3: Commit**

```bash
git add extension.yml
git commit -m "feat: register architecture reverse command"
```

## Task 5: Update User Documentation and Catalog Metadata

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `CATALOG-SUBMISSION.md`

- [ ] **Step 1: Update README command list**

In `README.md`, replace the sentence under `## Extension` that says the extension installs one command with:

````markdown
The extension installs two commands:

```text
/speckit.arch.generate
/speckit.arch.reverse
```
````

- [ ] **Step 2: Add README reverse usage section**

After the existing `/speckit.arch.generate` use paragraph, add:

````markdown
Run the reverse command in an ordinary historical repository when architecture should be inferred from repo facts:

```text
/speckit.arch.reverse
```

The reverse command first writes `.specify/memory/architecture-repo-facts.md`, then derives the 4+1 view files and synthesis from those evidence-backed facts. Use it when the repository does not already have Spec Kit feature context.
````

- [ ] **Step 3: Update README files written section**

In the "Files Written" code block, add this line before `architecture.md`:

```text
.specify/memory/architecture-repo-facts.md
```

After the code block, add:

```markdown
`/speckit.arch.generate` writes the six architecture SSOT files. `/speckit.arch.reverse` writes those six files plus `.specify/memory/architecture-repo-facts.md`.
```

- [ ] **Step 4: Update changelog**

Add this bullet under `## Unreleased`:

```markdown
- Add `/speckit.arch.reverse` for repo-facts-first reverse generation of architecture artifacts from ordinary historical repositories.
```

- [ ] **Step 5: Update catalog metadata**

In `CATALOG-SUBMISSION.md`, update:

```markdown
Commands count: 2
```

Add these bullets under key features:

```markdown
- Provides `/speckit.arch.reverse` for evidence-backed architecture reconstruction from ordinary historical repositories.
- Records reverse workflow evidence in `.specify/memory/architecture-repo-facts.md`.
```

- [ ] **Step 6: Verify documentation references**

Run:

```bash
rg -n "speckit\\.arch\\.reverse|architecture-repo-facts|Commands count: 2" README.md CHANGELOG.md CATALOG-SUBMISSION.md
```

Expected: matches in all three files.

- [ ] **Step 7: Commit**

```bash
git add README.md CHANGELOG.md CATALOG-SUBMISSION.md
git commit -m "docs: document architecture reverse command"
```

## Task 6: Final Verification

**Files:**
- Inspect all changed files.

- [ ] **Step 1: Check command write boundaries**

Run:

```bash
rg -n "Write only the seven|Do not modify source code|Do not require `.specify/memory/uc.md`" commands/speckit.arch.reverse.md
```

Expected: all required boundary statements are present.

- [ ] **Step 2: Check implementation detail prohibitions**

Run:

```bash
rg -n "classes|functions|endpoints|database|implementation details|Git history" commands/speckit.arch.reverse.md templates/architecture-repo-facts-template.md
```

Expected: output shows prohibitions and Git-history limitations in both command/template context.

- [ ] **Step 3: Run Bash setup verification from repository checkout**

Run:

```bash
tmpdir=$(mktemp -d)
git -C "$tmpdir" init >/dev/null
mkdir -p "$tmpdir/.specify/extensions/arch"
cp -R commands scripts templates "$tmpdir/.specify/extensions/arch/"
cd "$tmpdir"
json=$(.specify/extensions/arch/scripts/bash/setup-arch.sh --json)
printf '%s\n' "$json"
printf '%s\n' "$json" | rg '"REPO_FACTS_FILE"'
test -f .specify/memory/architecture-repo-facts.md
test -f .specify/memory/architecture.md
test -f .specify/memory/architecture-scenario-view.md
test -f .specify/memory/architecture-logical-view.md
test -f .specify/memory/architecture-process-view.md
test -f .specify/memory/architecture-development-view.md
test -f .specify/memory/architecture-physical-view.md
```

Expected: JSON prints `REPO_FACTS_FILE`; all file checks pass.

- [ ] **Step 4: Run PowerShell setup verification if available**

Run:

```bash
if command -v pwsh >/dev/null 2>&1; then
  tmpdir=$(mktemp -d)
  git -C "$tmpdir" init >/dev/null
  mkdir -p "$tmpdir/.specify/extensions/arch"
  cp -R commands scripts templates "$tmpdir/.specify/extensions/arch/"
  cd "$tmpdir"
  json=$(pwsh -NoProfile -File .specify/extensions/arch/scripts/powershell/setup-arch.ps1 -Json)
  printf '%s\n' "$json"
  printf '%s\n' "$json" | rg '"REPO_FACTS_FILE"'
  test -f .specify/memory/architecture-repo-facts.md
else
  echo "pwsh not installed; skip PowerShell runtime verification"
fi
```

Expected: if `pwsh` exists, JSON prints `REPO_FACTS_FILE` and the file check passes. If not, the skip message is printed.

- [ ] **Step 5: Check metadata registration**

Run:

```bash
rg -n "name: speckit\\.arch\\.generate|name: speckit\\.arch\\.reverse" extension.yml
```

Expected: both command names are present.

- [ ] **Step 6: Check final diff**

Run:

```bash
git status --short
git diff --stat HEAD
```

Expected: only intended files differ from `HEAD`, unless the user has unrelated pre-existing changes. Do not revert unrelated changes.

- [ ] **Step 7: Final commit if needed**

If Tasks 1-5 were committed separately, no final commit is required. If any verification fix was made, commit it:

```bash
git add commands/speckit.arch.reverse.md templates/architecture-repo-facts-template.md scripts/bash/setup-arch.sh scripts/powershell/setup-arch.ps1 extension.yml README.md CHANGELOG.md CATALOG-SUBMISSION.md
git commit -m "fix: verify architecture reverse workflow"
```

## Self-Review

- Spec coverage: The plan covers the new reverse command, repo facts template, setup script outputs, extension metadata, docs, quality gates, and verification.
- Placeholder scan: The plan intentionally includes template placeholders `NEEDS REPO FACTS UPDATE`; no plan placeholder such as `TBD`, `TODO`, or "implement later" is used.
- Type consistency: The path and JSON field name is consistently `REPO_FACTS_FILE`; the artifact path is consistently `.specify/memory/architecture-repo-facts.md`; the command name is consistently `speckit.arch.reverse`.
