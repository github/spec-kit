# Eleven command workflow

This fork separates product definition, system design, coding, deployment and testing.
Coding can finish before tests or deployment succeed. `CODE_COMPLETE` records a
coding deliverable; it is never a claim of correctness or product acceptance.

## Commands and file ownership

`F` is the active feature directory, normally `specs/NNN-feature`. Architecture and
environment describe the whole product and live in `.specify/memory/`. Features
reference those shared decisions rather than independently choosing a stack.

| Codex command | Reads | Owns |
|---|---|---|
| `$speckit-constitution` | Existing principles and project context | `.specify/memory/constitution.md` |
| `$speckit-specify` | Product request and constitution | `F/spec.md`, `F/checklists/requirements.md`, feature selection |
| `$speckit-clarify` | Spec and constitution | Spec clarifications and existing requirements checklist markers |
| `$speckit-architecture` | Constitution, spec, existing system decisions | `.specify/memory/architecture.md` |
| `$speckit-environment` | Requirements and architecture | `.specify/memory/environment.md` |
| `$speckit-plan` | Spec, architecture, environment, constitution | `F/plan.md`; research, model and contracts only when needed |
| `$speckit-taskscode` | All design inputs, existing tasks/progress and bugs | `F/tasks-code.md`; helper reconciliation of coding state |
| `$speckit-analyze` | Design inputs, tasks and constitution | `F/analysis.md` only |
| `$speckit-impcode` | Design, tasks, progress and relevant source | Task-listed application source; helper updates to `F/code-progress.json` |
| `$speckit-deployment` | Design, completed code, authorized destinations | `F/deployment.md`, deployment files and authorized target changes |
| `$speckit-test` | Requirements/contracts, code and relevant deployment evidence | Test source/configuration, `F/test-report.md`, `F/bugs.md`, test evidence |

The logical names are `speckit.architecture`, etc. Other agent integrations render
their native command spelling. Codex receives `.agents/skills/speckit-<name>/SKILL.md`.
There are exactly eleven core commands; tasks, implement, converge and checklist
are retired. The requirements checklist remains part of specify/clarify.

## Install from this fork

Use Python 3.11 or newer, Git and uv. In this checkout:

```powershell
uv sync --extra test
.\.venv\Scripts\specify.exe init C:\Projects\my-product --integration codex --script ps --ignore-agent-tools
```

For a POSIX development machine:

```bash
uv sync --extra test
.venv/bin/specify init ~/projects/my-product --integration codex --script sh --ignore-agent-tools
```

The shell launchers share the Python artifact/progress implementation, which is
installed alongside the selected shell scripts. Set `SPECKIT_PYTHON_EXECUTABLE` to
an explicit Python executable if discovery is unsuitable. PowerShell functionality
targets Windows PowerShell 5.1. New page templates are included in built wheels.

Initialization installs skills; it does not run them. Start with constitution and
specify, clarify ambiguities, then progress through architecture, environment,
plan, taskscode, analyze and impcode. Deploy to authorized compatible destinations
when ready, then run test. Local unit and isolated integration testing can run
without deployment; target-dependent tests report unavailable infrastructure as blocked.

The bundled `speckit` workflow follows these stages and retains the existing spec
and plan review gates. Its `deploy` input defaults to false. Set `deploy=true` and
provide destination references/authorized scope through `deployment_target` when
deployment is intended. Never put credentials into workflow inputs or reports.

## Architecture and environment contracts

Architecture selects components, languages, frameworks, database engines, protocols,
interfaces and necessary co-location/separation. It does not choose OS versions,
servers or hardware. Its single JSON inventory gives each component a stable ID.

Environment maps every component to logical asset IDs such as `APP01`. It specifies
OS/version, runtime, topology, networking, storage, asset count and minimum/recommended
resources from product demand. For managed services, use provider-managed OS and
actual service quotas. Quantities are positive numbers with units in their keys;
recommended values cannot be below minimum. The surrounding design explains capacity
assumptions, compatibility and resource totals for shared assets.

Logical assets allow code to identify its intended target before a physical server
is selected. Deployment later binds those IDs to observed, compatible destinations.
Environment never requires access credentials, purchases, running servers or tests
to complete its recommendation. Approved changes must include impact on other features.

## Coding tasks and durable progress

`tasks-code.md` contains one fenced JSON inventory. Every task has a stable `T001`
style ID, title, category, requirement IDs, component ID, deployment target IDs,
dependency IDs, concrete source paths and `done_when`. Categories are `code`,
`integration`, `configuration` and `migration`; the latter two describe application
files and migration source, not operational execution. No test, deployment, approval
or documentation-only tasks belong here.

The helper validates IDs, dependencies, cycles, targets, resource structure and source
path boundaries. Semantic questions such as whether a task adds an unjustified feature
remain the responsibility of taskscode/analyze. Dependencies determine scheduling;
server grouping and broad phase barriers do not.

PowerShell helper examples:

```powershell
.\.specify\scripts\powershell\workflow.ps1 context impcode --json
.\.specify\scripts\powershell\workflow.ps1 progress status
.\.specify\scripts\powershell\workflow.ps1 progress start --task T001
.\.specify\scripts\powershell\workflow.ps1 progress complete --task T001 --note 'API code and integration written'
```

Bash uses `.specify/scripts/bash/workflow.sh` with the same arguments. Python uses
`workflow_context.py STAGE` or `code_progress.py ACTION`. Context JSON supplies the
exact `PYTHON` and `PROGRESS_HELPER` paths for agent calls.

`taskscode` runs `validate` then `sync` after writing definitions. Unchanged definitions
retain progress; changed designs/tasks become `NEEDS_REVIEW` and prior evidence is
retained in history. Removed task records remain in history. IDs must not be reused.
`impcode` reads `status`, calls `start`, then `complete` or `block` for each task.

States are `PENDING`, `IN_PROGRESS`, `CODE_COMPLETE`, `BLOCKED` and `NEEDS_REVIEW`.
An interrupted `IN_PROGRESS` task resumes the same attempt. Failed attempts are bounded
to three per unchanged task/design; independent ready tasks remain available. Existing
source is inspected and continued, never erased merely to resume. Source hashes detect
external changes; authorized integration into shared files updates earlier file evidence.
Completion requires nonempty output files and a coding note, but cannot prove code quality.

State writes use an exclusive lock and atomic replacement. A crashed writer can leave
`code-progress.lock`; check that no helper is active before removing that lock. Never
delete the progress file to bypass an error. The lock protects brief state updates, not
the entire editor session: independent simultaneous agents still require coordination.

Each written/modified code file gets a language-valid header identifying component,
logical assets and task IDs at the earliest legal location after mandatory directives.
Shared files retain all applicable IDs. JSON, lockfiles and binary formats are not
corrupted with comments; their ownership stays in task definitions and progress.

## Execution boundaries and repair loop

`impcode` never writes or runs tests. Build, compile, type-check and lint are off by
default; a specific local check requires explicit permission and inspection to ensure
it cannot trigger tests, startup, installation hooks or deployment. Static code/diff
inspection and document/progress helpers remain allowed.

`analyze` is read-only with respect to its inputs and writes only `analysis.md`.
Context/progress reads do not persist `.specify/feature.json`. Analyze reports errors
in malformed task inventories; it does not repair those inputs automatically.

The new stage helpers require the selected feature directory to be inside the project.
Move externally stored feature artifacts deliberately before migrating such a project;
the helpers never silently copy or redirect them.

Deployment owns real preparation, dependencies, transfer, configuration and startup.
Its record includes release identity, exact safe commands, per-step state, evidence
and rollback. Resume observes actual resources before repeating side effects. Operational
health checks are distinct from test suites. No actual destinations are assumed by this
fork; access and authorization are supplied for each product deployment.

Test owns test planning, creation and execution. It reports measured outcomes and stable
bug IDs. Coding fixes follow `test → taskscode → impcode → test`; deployment defects
return to deployment and design contradictions to their owning command. Tests do not
rewrite task state or turn an earlier coding completion claim into a pass.
For target-dependent retesting after a code repair, deployment must refresh the
changed release first. Test compares the intended and observed deployed identities;
an old release cannot establish that new code passes. Explicitly authorized disposable
test data may change through the product API, while deployment files and configuration
remain owned by deployment.

These are agent command contracts, not an OS sandbox. Helpers enforce their own validation
and writes; they do not intercept arbitrary agent tools. Hooks/presets cannot silently
expand a stage's contract. Incompatible hooks are reported as separate work. A project
constitution that mandates TDD needs an explicit policy amendment before this separated
workflow can comply; commands must report that conflict rather than reinterpret it.

## Migration and customization

Use this fork's CLI to upgrade an existing integration:

```powershell
.\.venv\Scripts\specify.exe integration upgrade codex --help
```

Run the upgrade from the target project with the fork CLI executable's absolute path.
Normal upgrade refreshes tracked unchanged skills/shared files and preserves customizations;
review any reported conflicts. Do not use `--force` without reviewing what it overwrites.
Generated skills are copies: editing repository templates does not refresh an existing
project automatically. Old user-modified skills may be retained and require manual migration.

Preserve legacy `tasks.md` as historical evidence. Have taskscode classify and migrate
only programming work, keeping stable IDs and source evidence; move testing/deployment
responsibilities to their owners. Legacy checkboxes are not proof of correct code or tests.
Create architecture/environment decisions before regenerating implementation design.

The bundled lean preset overrides only constitution/specify. Its old plan/tasks/implement
files are not registered. Git hooks use taskscode/impcode names and no longer commit from
analyze. The GitHub extension prefers tasks-code.md and keeps a tasks.md fallback for
upstream projects. Third-party presets, extensions and custom workflows need a contract
review; legacy tasks/implement hooks are not automatically aliased to the new names.

The old setup-plan/setup-tasks/check-prerequisites helpers and legacy page scaffolds
remain available for existing optional consumers. The eleven core commands use the
new context/progress contracts for all changed stages.

## Validation

Every bundled command uses `capture: true` and `verify_completion: true`. A zero
process exit code alone cannot advance the workflow. The agent must report completion
for the current invocation and provide matching SHA-256 hashes of its output files.
Missing, blocked, stale, truncated or mismatched evidence fails the step. If clarification
needs an answer, supply it before resuming the failed step. Verification checks reported
completion and file identity; it does not prove semantic correctness or enforce a sandbox.
Review gates and the separate test stage remain necessary.

Run tests in this checkout's virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_fork_workflow.py -q
```

This exercises actual helper processes, resume, dependency failures, retry limits,
input/output change detection, malformed inputs, file preservation, generated Codex
skills and shell parity. PowerShell cases invoke `powershell.exe`, not PowerShell 7.
Repository tests verify the toolkit; the ban on testing belongs to generated impcode
runs against a product. Prompt assertions and helper tests do not establish that a
live coding agent followed every instruction or that a product was deployed/tested.

Validation on 2026-11-17 used Python 3.11.6 in this checkout's virtual environment:

- Final workflow, bundled orchestration and init checks: 76 passed, 3 platform skips.
  The workflow helper file contributes 31 passing cases, including interrupted and
  failed shared-file integration, bounded retries and external-change detection.
- Compatibility checks across integrations, presets and extensions: 1,232 passed,
  117 skipped. Windows symlink cases were excluded because this account cannot create
  symlinks; unavailable shell/platform cases retained their existing skips.
- Actual Windows PowerShell 5.1 and Git Bash helper parity passed, including paths
  with spaces, brackets and non-ASCII characters and missing-input failures.
- Ruff, documentation lint, diff whitespace checks, wheel build and isolated wheel
  installation passed. Fresh Codex initialization installed exactly eleven skills,
  the current Python helpers and the new page templates with native command references.

The initial bundled-workflow checks exercised deployment-enabled and deployment-disabled
paths with mocked agent command execution. The subsequent
[Tiny Notes end-to-end audit](fork-design/02-end-to-end-audit.md) exercised all eleven
installed skill procedures, a real local service and its repair/redeployment cycle:
22 sample tests passed. That report distinguishes the direct skill run from the separate
CLI launcher failure and includes observed file boundaries and retained evidence.

The [final engineering verification](fork-design/03-release-readiness.md) records the
broader Windows run, subsequent migration fixes, baseline comparisons, package checks
and the remaining unattended-CLI limitation.
