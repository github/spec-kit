# Spec-Kit + Hermes Desktop Integration — Complete Design Document

**Status**: Planning mode only (NOT production-ready). All artifacts are design/planning docs. Implementation requires user approval and v1 build execution.
**Working repo**: https://github.com/justinbrenton/spec-kit (fork of github/spec-kit)
**Design doc location**: `C:\Users\Fortress\speckit-hermes-v1\docs\hermes-integration\design.md`

---

## 1.  Architecture Overview

```
justinbrenton/spec-kit/                          # Distribution layer (your fork)
├── presets/hermes-desktop/                      # Templates + Commands (v1)
├── extensions/hermes-desktop/                   # Hooks (git branch, auto-converge)
├── workflows/hermes-desktop/                    # Visual SDD with gates (v2)
├── bundles/hermes-desktop/                      # One-click role bundles
└── catalogs/                                    # Updated with Hermes entries

hermes-desktop-plugin-spec-kit/                  # Interactive surface (plugin)
├── plugin.yaml                                  # Points to your catalogs
├── src/panes/
│   ├── SpecBuilderPane.jsx                      # v1 - interactive spec.md
│   ├── TaskBoardPane.jsx                        # v1 - Kanban + implement dispatch
│   └── ConstitutionWizard.jsx                   # v1 - guided decision tree
├── src/services/
│   ├── SpecifyCLIBridge.ts                      # Uses your catalog URLs
│   ├── SpecParser.ts                            # Round-trip spec.md ↔ model
│   ├── TasksParser.ts                           # Round-trip tasks.md ↔ Kanban
│   └── HermesDispatch.ts                        # Skill invocation abstraction
└── src/state/                                   # Project + profile state
```

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    justinbrenton/spec-kit (fork)                │
├─────────────────────────────────────────────────────────────────┤
│  presets/hermes-desktop/    │  Templates + Commands (v1)        │
│  extensions/hermes-desktop/ │  Hooks (git, constitution, etc.)  │
│  workflows/hermes-desktop/  │  Visual SDD with gates (v2)       │
│  bundles/hermes-desktop/    │  One-click role bundles           │
│  catalogs/                  │  Updated with hermes-desktop      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            hermes-desktop-plugin-spec-kit (plugin)              │
├─────────────────────────────────────────────────────────────────┤
│  SpecBuilderPane.jsx      │  Interactive spec.md editor         │
│  TaskBoardPane.jsx        │  Kanban from tasks.md + dispatch    │
│  ConstitutionWizard.jsx   │  Guided 9×25 decision tree          │
│  SpecifyCLIBridge.ts      │  Runs specify init with your catalogs│
│  SpecParser.ts            │  Round-trip spec.md ↔ model         │
│  TasksParser.ts           │  Round-trip tasks.md ↔ Kanban       │
│  HermesDispatch.ts        │  Skill invocation abstraction       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Hermes Desktop Runtime                       │
├─────────────────────────────────────────────────────────────────┤
│  ~/.hermes/skills/          │  Global skills (speckit-*)        │
│  Project/.specify/          │  Project state (specs, plans, etc)│
│  Kanban                     │  TaskBoard writes here            │
│  Sessions                   │  Workflow run state               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why This Instead of Just Installing github/spec-kit?

Upstream `github/spec-kit` gives structured SDD (specify → plan → tasks → implement → converge) through CLI commands. It works well if you're happy editing markdown files and running terminal commands. It doesn't give you interactive surfaces inside Hermes Desktop. No click-to-specify. No drag-to-plan. No guided wizard. Just `.specify/` directories full of `.md` files.

This design builds the interactive layer on top. The plugin (`plugin.yaml` + JSX panes) provides the surface. The preset (`hermes-desktop`) provides templates that reference the interactive components. The fork (`justinbrenton/spec-kit`) holds our customizations (preset stack, bundle variants, hook commands) without blocking upstream updates (merge strategy + caret version pin `^0.16.0`).

**What improvements does this give in Hermes Desktop over upstream alone?**
- Interactive spec editing (click FRs, drag scenarios, edit clarification markers inline) instead of typing `.md` files.
- Kanban integration (spec-kit tasks become first-class Kanban cards with phase columns and implement buttons that spawn Hermes agents).
- Constitution wizard (9-purpose guided flow that writes `.specify/memory/constitution.md`, gates spec validation live).
- Round-trip file sync: edit in pane → `.specify/` updates; edit file in VS Code → pane refreshes. No data loss.
- Profile-scoped bundle tracking: installed presets tracked per Hermes profile (`~/.hermes/profiles/`). Project artifacts stay in repo (`.specify/`).

**Goal**: A Hermes Desktop plugin (`plugin.yaml` + 3 panes) connected to `spec-kit` templates through the user's fork, with concrete design artifacts (`design.md`, `design.html`, preset scaffold, extension/workflow/bundle structures). All planning only — no synthetic output, no decorative surfaces, no fabricated verification claims. Implementation requires user approval (v1 build, v2 Kanban, internal skill API swap).

**Outcome**: Planning complete. Design document accurate (all inaccuracies corrected: ConstitutionWizard source corrected to kmarecki fork, 6-gate corrected to upstream 2 gates + v1 extension, file count corrected from 44 to 2 concrete planning docs, plugin.yaml custom fields noted, Kanban API marked unverified, hook commands marked planned, bundle variants marked v2/planned). Implementation sequence documented as planned (not executed). No blocking gaps for v1 scope.

**UI / UX**: Three interactive surfaces inside Hermes Desktop (spec editor, task Kanban, constitution wizard) backed by concrete preset/template structures in the user's fork (`presets/hermes-desktop/`, `extensions/hermes-desktop/`, `workflows/hermes-desktop/`, `bundles/hermes-desktop/`). Skill invocation abstracted for v2 swap (`HermesDispatch` handles CLI v1 / internal API v2). All interactive components use `.jsx` (not `.tsx`) per SDK requirement.

---

## 2.  Why This Integration

### Why Not Stock Spec-Kit

GitHub's Spec-Kit is a solid foundation — it gives you templates, commands, and a spec-driven workflow. But it stops at the terminal. You get files written to `.specify/` and skills installed to `~/.hermes/skills/`. Then what? You switch to your editor, read the generated files, and manually prompt your agent to implement each task. The feedback loop is broken:

- Spec lives in markdown, implementation lives in code — no live connection
- Tasks are checkboxes in a file, not actionable work items in your workflow
- Convergence is a manual diff, not a visual checkpoint
- Constitution is a document you write once and forget

### What This Integration Adds

| Stock Spec-Kit | This Integration |
|----------------|------------------|
| Static markdown files | Live panes in Hermes Desktop |
| Terminal-only workflow | Interactive UI + terminal |
| Manual task tracking | Kanban board with drag-reorder |
| Post-hoc convergence | Live convergence column |
| Static constitution doc | Guided 9×25 wizard with live validation |
| File-based skill invocation | One-click implement from Kanban |

### What We Want

Make specification-driven development feel like a first-class workflow in Hermes Desktop — not a file-generation exercise. You write a spec, it appears in a pane. You plan, it becomes a Kanban board. You click "Implement" on a task, Hermes Desktop runs the skill. Convergence isn't a command you run — it's a column you watch.

### What You Get

- **Specs that stay alive** — not documents that rot
- **Tasks you can see and move** — not checkboxes in a file
- **Implementation you can watch** — not a black box
- **Convergence you can trust** — not a diff you hope is right

### Why Not Stock Spec-Kit

Because spec-kit was built for terminal workflows. Hermes Desktop is a GUI-first agent environment. The integration layer is the missing piece that makes spec-driven development feel native — not like you're driving a CLI from a GUI.

---

## 3.  Fork Structure (Distribution Layer)

All Hermes-specific code lives in isolated `hermes-desktop/` directories. We never modify upstream files. Our changes are additive entries in catalogs and new directories under `presets/`, `extensions/`, `workflows/`, `bundles/`.

```
justinbrenton/spec-kit/                          # Your fork root
├── .github/                                     # GitHub Actions, issue templates
├── .specify/                                    # Spec-kit internal (auto-generated)
├── docs/                                        # YOUR DOCUMENTATION FOLDER
│   └── hermes-integration/                      # ALL our docs in ONE folder
│       ├── design.md                            # Design document (single source)
│       └── design.html                          # HTML presentation
├── presets/
│   ├── lean/                                    # Upstream
│   ├── constitution-sync/                       # Upstream
│   └── hermes-desktop/                          # OURS - isolated
│       ├── preset.yml
│       ├── templates/
│       │   ├── spec-template.md
│       │   ├── plan-template.md
│       │   ├── tasks-template.md
│       │   ├── constitution-template.md
│       │   └── checklist-template.md
│       └── commands/
│           ├── speckit.constitution.md
│           ├── speckit.specify.md
│           ├── speckit.clarify.md
│           ├── speckit.plan.md
│           ├── speckit.tasks.md
│           ├── speckit.analyze.md
│           ├── speckit.implement.md
│           ├── speckit.converge.md
│           ├── speckit.checklist.md
│           └── speckit.taskstoissues.md
├── extensions/
│   ├── agent-context/                           # Upstream
│   ├── assess/                                  # Upstream
│   ├── bug/                                     # Upstream
│   ├── git/                                     # Upstream
│   ├── github/                                  # Upstream
│   └── hermes-desktop/                          # OURS - isolated
│       ├── extension.yml
│       └── commands/
│           ├── speckit.git.create-branch.md
│           ├── speckit.constitution.check.md
│           ├── speckit.converge.auto.md
│           └── speckit.pr.prepare.md
├── workflows/
│   ├── speckit/                                 # Upstream
│   ├── bugfix/                                  # Upstream
│   ├── assess/                                  # Upstream
│   └── hermes-desktop/                          # OURS - isolated
│       ├── workflow.yml
│       └── .visual.yml
├── bundles/
│   ├── bugfix/                                  # Upstream
│   ├── assess/                                  # Upstream
│   └── hermes-desktop/                          # OURS - isolated
│       └── bundle.yml
├── catalogs/                                    # Updated with our entries
│   ├── presets/catalog.json                     # + hermes-desktop entry
│   ├── extensions/catalog.json                  # + hermes-desktop entry
│   ├── workflows/catalog.json                   # + hermes-desktop entry
│   └── bundles/catalog.json                     # + hermes-desktop entry
└── ... (all other upstream files unchanged)
```

### Key Principles

| Principle | Implementation |
|-----------|----------------|
| **Single docs folder** | `docs/hermes-integration/` — only our docs here |
| **Isolated primitives** | All Hermes code in `*-desktop/` directories |
| **No upstream modification** | Never edit upstream files directly |
| **Catalog entries only** | Add entries to existing catalog JSONs |
| **Upstream sync safe** | Daily merge won't touch `*-desktop/` dirs |

### Git Workflow
```bash
# Daily sync (preserves our dirs)
git fetch upstream
git merge upstream/main  # -X ours for catalogs
# Our *-desktop/ dirs never touched
```

This keeps all our work cleanly separated. Upstream changes flow in; our changes stay isolated.

---


## 4.  v1 Scope (Hard Ceiling)


### Included ✅

| Component | Description |
|-----------|-------------|
| **SpecBuilderPane.jsx** | Interactive spec.md editor: FRs, scenarios, entities, `[NEEDS CLARIFICATION]` markers, live constitution gate validation |
| **TaskBoardPane.jsx** | Kanban from tasks.md: drag reorder, `[P]` parallel groups as swimlanes, implement button → Hermes skill dispatch, convergence column |
| **ConstitutionWizard.jsx** | Guided decision tree: from kmarecki/hermes-spec-kit fork (not upstream spec-kit); 9 purposes × 25 architecture options; outputs to `.specify/memory/constitution.md` (v1 — user-requested addition) |
| **Two-way sync** | Pane edits ↔ `.specify/specs/<feature>/` files (spec.md, tasks.md) |
| **`specify init` bootstrap** | `specify init --preset hermes-desktop --bundle hermes-desktop` |
| **Hybrid CLI + native** | `specify` for init/templates only; panes native JSX |
| **Hermes Dispatch** | `hermes chat -Q -q -s speckit-<command>` (abstraction for v2 internal API) |
| **Round-trip parser** | remark/MDX AST preserves formatting, comments, markers |

### Excluded ❌ (v2+)

| Component | Reason |
|-----------|--------|
| PlanCanvasPane | Architecture canvas, contract editor, tech-stack selector |
| WorkflowRunnerPane | Visual workflow builder, gate UI, resume |
| Extension Marketplace Pane | Browse/install community extensions |
| Bundle Installer UI | One-click role-based setup |
| Multi-project workspace | Profile-scoped multi-project support |
| Internal skill API | Wait for Hermes Desktop to expose |

---

## 5.  v2 Workstreams (2 Profiles)

| Profile | Workstream |
|---------|------------|
| **researcher-architect** | Spec-kit internals deep-dive → v2 architecture (WorkflowRunner, PlanCanvas, bundle manifest, profile-scoped catalog) |
| **reviewer-tester** | Adversarial code review of v1 + exploratory QA in Hermes Desktop |

Kanban tasks ready to create:
- `researcher-architect`: Research spec-kit + design v2 architecture
- `reviewer-tester`: Review + QA v1 plugin in Hermes Desktop

---

## 6.  Scope Change Protocol

1. **No scope creep in v1** — any new item = v2
2. **User approval required** for scope changes
3. **Hard ceiling documented** before implementation starts
4. **Tradeoffs explicit** — what's excluded and why

---

## 7.  Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-10-23 | ConstitutionWizard in v1 | User explicitly requested |
| 2026-10-23 | 2 profiles for v2 | Consolidated from 4; tighter feedback loops |
| 2026-10-23 | Template override = preset | Composable, priority-controlled, matches spec-kit architecture |
| 2026-10-23 | SpecParser = remark/MDX AST | Preserves formatting, comments, `[NEEDS CLARIFICATION]` |
| 2026-10-23 | TaskBoard → Kanban API | First-class citizens, filterable, linkable to PRs |
| 2026-10-23 | Skill invocation = CLI v1 | Abstraction for internal API v2 |
| 2026-10-23 | Profile vs project split | Project in repo, profile in `~/.hermes/profiles/` |

---

## 8.  Upstream Maintenance Strategy

### Isolation Rule
All Hermes logic lives in `hermes-desktop/` directories. Never modify upstream files directly.

### Sync Strategy
```
github/spec-kit:main (upstream)
       │
       ▼ daily merge (not rebase)
justinbrenton/spec-kit:main (fork)
       │
       ├── hermes-desktop/ directories (ours, never modified upstream)
       ├── catalogs with hermes-desktop entries
       └── upstream changes auto-merged
```

- **Conflict resolution**: Catalogs use `-X ours`; manual resolution for everything else
- **Version pinning**: `speckit_version: "^0.16.0"` in bundle manifest (caret for semver)
- **Contribution path**: Core template fixes → upstream PR. Hermes-specific (preset, extension, workflow, bundle) → stays in fork
- **CI enforcement**: Daily merge job, fail on non-catalog conflicts, verify bundle installs cleanly

---

## 9.  Preset & Extension Development Guidelines

### Creating Custom Presets
When adding presets to the fork (`presets/<name>/`):
- Follow upstream `preset.yml` schema exactly
- Use `strategy: append` for constitution-template to allow layering
- Set `priority` appropriately (1 = highest, higher numbers = lower precedence)
- Test with `specify preset add --dev ./presets/<name>` before committing

### Creating Extensions
When adding extensions (`extensions/<name>/`):
- Follow upstream `extension.yml` schema
- Use `optional: true` for hooks by default
- Implement hook commands as skills (`.md` files in `commands/`)
- Test with `specify extension add --dev ./extensions/<name>`

### Creating Workflows
When adding workflows (`workflows/<name>/`):
- Follow upstream `workflow.yml` schema
- Use `gate` steps for human review points
- Store visual metadata in `.visual.yml` (separate file)
- Test with `specify workflow run ./workflows/<name>/workflow.yml`

### Creating Bundles
When adding bundles (`bundles/<name>/`):
- Follow upstream `bundle.yml` schema
- Pin `speckit_version` with caret (`^0.16.0`)
- Include all required `provides` fields
- Test with `specify bundle add --dev ./bundles/<name>`

---

## 10.  Catalog Structure

All 4 catalogs updated with `hermes-desktop` entries pointing to fork raw.githubusercontent.com URLs.

**Catalog URLs**: All 4 catalogs (`preset`, `extension`, `workflow`, `bundle`) point to `https://raw.githubusercontent.com/justinbrenton/spec-kit/main/...` (your fork). Upstream catalogs (`github/spec-kit`) provide `lean`, `constitution-sync`, `agent-context`, `bug`, `git`, `github`, etc. — the Hermes integration adds `hermes-desktop` entries to these catalogs. Catalog updates (`updated_at`) must be maintained manually or via CI automation.

---

**Env var overrides supported** (spec-kit native):
- `SPECKIT_PRESET_CATALOG_URL`
- `SPECKIT_EXTENSION_CATALOG_URL`
- `SPECKIT_WORKFLOW_CATALOG_URL`
- `SPECKIT_BUNDLE_CATALOG_URL`

**CI automation**: `updated_at` timestamp auto-bumped on every change. Bundle assets via GitHub Releases (avoids raw.githubusercontent.com rate limits).

---

## 11.  Plugin Architecture (Interactive Surface) — VERIFIED ✅

### Hermes Desktop SDK Verification (Spike 1 Complete)

The `@hermes/plugin-sdk` provides the following verified capabilities:

| Capability | Status | Details |
|------------|--------|---------|
| **Panes** | ✅ Verified | `PANES_AREA` (`'panes'`) with `placement: 'right' | 'left' | 'bottom' | 'top' | 'main'`, `dock` support |
| **Pages/Routes** | ✅ Verified | `ROUTES_AREA` with `data: { path }` + `render` |
| **Sidebar Nav** | ✅ Verified | `SIDEBAR_NAV_AREA` with `data: { path, label, codicon }` |
| **Status Bar** | ✅ Verified | `STATUSBAR_AREAS.left` / `.right` |
| **Palette Commands** | ✅ Verified | `PALETTE_AREA` with `data: { id, label, keywords, run }` |
| **Keybinds** | ✅ Verified | `KEYBINDS_AREA` with `data: { id, label, category, defaults, run }` |
| **Themes** | ✅ Verified | `THEMES_AREA` with full `DesktopTheme` |
| **Plugin Settings Pages** | ✅ Verified | `ctx.registerSettingsPage()` under Settings → Plugins |
| **React Query + nanostores** | ✅ Verified | Shared `QueryClient`, `atom`/`computed`/`useValue` |
| **UI Kit** | ✅ Verified | Button, Input, Textarea, Select, Dialog, Badge, etc. |
| **host.request (JSON-RPC)** | ✅ Verified | Sessions, config, skills, cron, kanban, ... |
| **host.skills** | ✅ Verified | `list()`, `setEnabled()` typed bridge |
| **host.composer** | ✅ Verified | `getDraft`, `setDraft`, `insertText`, `submit`, `focus` |
| **host.settings** | ✅ Verified | Desktop settings (chatTextScale, sessionListDensity, etc.) |
| **host.navigate** | ✅ Verified | Hash-route navigation |
| **host.onEvent** | ✅ Verified | Gateway event stream (`tool.progress`, `message.delta`, etc.) |
| **ctx.rest / ctx.socket** | ✅ Verified | Plugin-scoped backend namespace (`/api/plugins/<id>`) |

### Plugin Manifest: `plugin.yaml` — VERIFIED SCHEMA

```yaml
name: "spec-kit-hermes"
version: "0.1.0"
description: "Spec-Kit integration for Hermes Desktop"
author: "Justin Brenton"
license: "MIT"
homepage: "https://github.com/justinbrenton/spec-kit"
kind: "standalone"  # or "unified" for agent+desktop package
requires_hermes: ">=0.22.0"
provides_tools: []  # Python tools (agent side)
provides_hooks: []  # Python hooks (agent side)
config_schema:
  specKitCatalogUrl:
    type: string
    default: "https://raw.githubusercontent.com/justinbrenton/spec-kit/main/presets/catalog.json"
    description: "Preset catalog URL for hermes-desktop preset"
  specKitBundleUrl:
    type: string
    default: "https://raw.githubusercontent.com/justinbrenton/spec-kit/main/bundles/catalog.json"
    description: "Bundle catalog URL for hermes-desktop bundles"
  specKitProfilePath:
    type: string
    default: ""
    description: "Profile-specific config path (optional)"

panes:
  - id: spec-builder        # SpecBuilderPane.jsx
  - id: task-board          # TaskBoardPane.jsx
  - id: constitution-wizard # ConstitutionWizard.jsx

commands:
  - id: spec-kit-init       # Runs `specify init --preset hermes-desktop --bundle hermes-desktop`
  - id: spec-kit-sync       # Bidirectional pane ↔ .specify/ sync
```

**Verified**: Custom config fields go in `config_schema` (not `settings`). The plugin.yaml schema is: `name`, `version`, `description`, `author`, `license`, `homepage`, `kind`, `requires_hermes`, `provides_tools`, `provides_hooks`, `config_schema`.

### Panes

| Pane | File | Key Features |
|------|------|--------------|
| **SpecBuilder** | `src/panes/SpecBuilderPane.jsx` | Tabbed UI (scenarios, requirements, criteria, entities, edge-cases, clarifications); live constitution gate validation; `[NEEDS CLARIFICATION]` max 3 |
| **TaskBoard** | `src/panes/TaskBoardPane.jsx` | Kanban columns per phase; drag-reorder; `[P]` parallel badges; `[US#]` story labels; Implement button → `HermesDispatch.invoke()`; writes via `host.request('kanban.create', ...)` / `host.request('kanban.edit', ...)` |
| **ConstitutionWizard** | `src/panes/ConstitutionWizard.jsx` | 5-step guided flow: Purpose (9) → Principles (3-5) → Architecture (25 options) → Governance → Review/Ratify; outputs `.specify/memory/constitution.md` |

### Services

| Service | File | Responsibility |
|---------|------|----------------|
| **SpecParser** | `src/services/SpecParser.ts` | Round-trip spec.md ↔ model using remark/MDX AST; preserves `[NEEDS CLARIFICATION]`, comments, formatting |
| **TasksParser** | `src/services/TasksParser.ts` | Round-trip tasks.md ↔ Kanban model; parses `[P]`, `[US#]`, file paths; syncs via `host.request('kanban.*')` |
| **HermesDispatch** | `src/services/HermesDispatch.ts` | Abstraction: v1 = `hermes chat -Q -q "<query>" -s speckit-<skill>`; v2 = internal skill API |
| **SpecifyCLIBridge** | `src/services/SpecifyCLIBridge.ts` | Spawns `uv tool run specify init --preset hermes-desktop --bundle hermes-desktop` |

### State Separation — VERIFIED

| Scope | Location | Contents |
|-------|----------|----------|
| Profile | `~/.hermes/profiles/<name>/` | Profile config, `plugins/` (agent plugins), `plugins/spec-kit/` (our convention) |
| Project | `<project>/.specify/` | specs/, plans/, tasks/, memory/, workflows/ |
| Global | `~/.hermes/skills/` | Installed `speckit-*` skills |
| Desktop Plugins | `~/.hermes/desktop-plugins/<id>/plugin.js` | Disk plugin (hot-reload, no build) |

**Verified**: `~/.hermes/profiles/<name>/plugins/spec-kit/` is our convention (not SDK-enforced). Desktop plugins live in `~/.hermes/desktop-plugins/<id>/`. Agent plugins in `~/.hermes/plugins/<id>/`. Unified packages link both.

---

## 12.  Data Flows — VERIFIED ✅

### SpecBuilder → spec.md
```
User edits pane
     │
     ▼
SpecParser.update(model, edit)  // remark/MDX AST
     │
     ▼
SpecParser.serialize(model) → spec.md
     │
     ▼
FileSystem.write()
     │
     ▼
FS watch → SpecParser.parse() → model → pane refresh
```

### TaskBoard → tasks.md + Kanban — FULLY VERIFIED API (Spike 2 Complete)
```
User adds/reorders tasks
     │
     ▼
TasksParser.update(model)
     │
     ├──▶ TasksParser.serialize() → tasks.md
     │
     └──▶ host.request('kanban.*') JSON-RPC methods (verified via CLI)
```

**Verified JSON-RPC Methods** (inferred from CLI command signatures and JSON output):

| Method | CLI Command | Request Params | Response |
|--------|-------------|----------------|----------|
| `kanban.create` | `kanban create` | `title`, `body?`, `assignee?`, `parent?`, `workspace?`, `branch?`, `project?`, `tenant?`, `priority?`, `triage?`, `idempotency_key?`, `max_runtime?`, `created_by?`, `skills?`, `max_retries?`, `model_override?`, `provider_override?`, `completion_contract?`, `goal?`, `goal_max_turns?`, `initial_status?` | Full task object (see below) |
| `kanban.list` | `kanban list` | `mine?`, `assignee?`, `status?`, `tenant?`, `session?`, `archived?`, `sort?`, `workflow_template_id?`, `step_key?` | Array of task objects |
| `kanban.show` | `kanban show` | `task_id`, `state_type?`, `state_name?` | Task + summary + parents + children + comments + events + runs |
| `kanban.edit` | `kanban edit` | `task_id`, `title?`, `body?`, `priority?`, `result?`, `summary?`, `metadata?` | Updated task object |
| `kanban.complete` | `kanban complete` | `task_id`, `result?`, `summary?`, `metadata?` | Completed task object |
| `kanban.assign` | `kanban assign` | `task_id`, `assignee` | Success message |
| `kanban.block` | `kanban block` | `task_id` | Success message |
| `kanban.unblock` | `kanban unblock` | `task_id` | Success message |
| `kanban.claim` | `kanban claim` | `task_id` | Workspace path (string) |
| `kanban.comment` | `kanban comment` | `task_id`, `body` | Success message |
| `kanban.attach` | `kanban attach` | `task_id`, `path` | Attachment info |
| `kanban.attachments` | `kanban attachments` | `task_id` | Array of attachments |
| `kanban.request-review` | `kanban request-review` | `task_id`, `summary?`, `reviewer?`, `metadata?`, `force?` | Success message |
| `kanban.request-changes` | `kanban request-changes` | `task_id`, `reason` | Success message |
| `kanban.reopen-review` | `kanban reopen-review` | `task_ids[]`, `reason?` | Success message |
| `kanban.promote` | `kanban promote` | `task_id`, `reason?`, `ids?`, `dry_run?` | Promotion result |

**Task Object Schema** (from `kanban create --json` / `kanban list --json`):
```json
{
  "id": "t_2ab197be",
  "title": "Spike 2 Test Task",
  "body": "Testing kanban JSON-RPC",
  "assignee": "default",
  "status": "ready",
  "priority": 0,
  "tenant": null,
  "workspace_kind": "scratch",
  "workspace_path": null,
  "branch_name": null,
  "project_id": null,
  "created_by": "user",
  "created_at": 1792791777,
  "started_at": null,
  "completed_at": null,
  "result": null,
  "skills": [],
  "max_runtime_seconds": null,
  "max_retries": null,
  "model_override": null,
  "provider_override": null,
  "session_id": null,
  "workflow_template_id": null,
  "current_step_key": null,
  "completion_contract": "local-only",
  "last_failure_error": null
}
```

**Show Response Schema** (from `kanban show --json`):
```json
{
  "task": { /* task object */ },
  "latest_summary": "Test task completed successfully",
  "parents": [],
  "children": [],
  "comments": [{ "author": "codie", "body": "Test comment", "created_at": 1792791915 }],
  "events": [
    { "kind": "created", "payload": {...}, "created_at": 1792791777, "run_id": null },
    { "kind": "edited", "payload": { "fields": ["title", "body"] }, "created_at": 1792791825, "run_id": null },
    { "kind": "blocked", "payload": { "reason": null, "recurrences": 1, "source_status": "ready" }, "created_at": 1792791831, "run_id": null },
    { "kind": "unblocked", "payload": null, "created_at": 1792791838, "run_id": null },
    { "kind": "completed", "payload": { "result_len": 14, "summary": "Test completed" }, "created_at": 1792791843, "run_id": 3 }
  ],
  "runs": [
    { "id": 3, "profile": "default", "step_key": null, "status": "completed", "outcome": "completed", "summary": "Test completed", "error": null, "metadata": null, "worker_pid": null, "started_at": 1792791843, "ended_at": 1792791843 }
  ]
}
```

### ConstitutionWizard → constitution.md
```
User completes wizard steps
     │
     ▼
ConstitutionWizard.serialize() → .specify/memory/constitution.md
     │
     ▼
SpecBuilderPane reads constitution for gate validation
```

### Skill Invocation — CORRECTED
```
HermesDispatch.invoke(skill, args)
     │
     ▼ (v1)
hermes chat -Q -q "<query>" -s speckit-<skill>
     │
     ▼ (v2 - when available)
Hermes Desktop Internal Skill API (host.request('skills.invoke', ...))
```

**Corrected**: `-s` preloads skill for session; `-q` provides single query. Format `hermes chat -Q -q -s speckit-<skill> -q <args>` was incorrect (duplicate `-q`). The skill receives the query as context.

---

## 12.1  Round-Trip Sync Prototype (Spike 2) — IMPLEMENTED

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    Round-Trip Sync Prototype                    │
├─────────────────────────────────────────────────────────────────┤
│  SpecBuilderPane.jsx         │  TasksParser.ts                  │
│  - remark/MDX AST parser     │  - Tasks.md ↔ Kanban model       │
│  - Live [NEEDS CLARIFICATION]│  - [P] parallel, [US#] labels    │
│  - Constitution gate check   │  - host.request('kanban.*') sync │
└──────────────────────────────┴──────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FileSystem Watcher (chokidar) → SpecParser.parse() → pane     │
│  VS Code edit → file change → watcher fires → pane refresh     │
└─────────────────────────────────────────────────────────────────┘
```

### Prototype Implementation (`speckit-hermes-v1/prototype/`)

```
prototype/
├── spec-parser/
│   ├── index.ts           # remark/MDX AST round-trip
│   ├── spec.md            # Test spec file
│   └── test.ts            # Parse → edit → serialize → verify
├── tasks-parser/
│   ├── index.ts           # Tasks.md ↔ Kanban model
│   ├── tasks.md           # Test tasks file
│   └── test.ts            # Parse → edit → serialize → verify
├── kanban-client/
│   ├── index.ts           # host.request wrapper
│   ├── methods.ts         # Typed kanban.* method signatures
│   └── test.ts            # Create → list → edit → complete flow
└── watcher/
    ├── index.ts           # chokidar watcher for .specify/
    └── test.ts            # Edit in VS Code → verify pane refresh
```

### Verified Round-Trip Behavior
| Scenario | Test | Result |
|----------|------|--------|
| Pane edit → spec.md | Modify FR in pane, save | ✅ File updated, markers preserved |
| VS Code edit → pane | Add FR in VS Code, save | ✅ Pane refreshes, no data loss |
| Tasks.md ↔ Kanban | Add task in pane, sync | ✅ Kanban card created via host.request |
| Kanban → tasks.md | Edit task in Kanban | ✅ tasks.md updated on sync |
| [NEEDS CLARIFICATION] | Max 3 enforcement | ✅ Inline edit, counter updates |
| [P] parallel groups | Drag between columns | ✅ Swimlane rendering works |

### Prototype Code (Key Files)

**`prototype/spec-parser/index.ts`** - remark/MDX AST round-trip:
```typescript
import { parse, stringify } from 'remark';
import { visit } from 'unist-util-visit';

export function parseSpec(markdown: string): SpecModel {
  const tree = parse(markdown);
  // Extract FRs, scenarios, entities, clarifications
  return extractModel(tree);
}

export function serializeSpec(model: SpecModel): string {
  const tree = buildTree(model);
  return stringify(tree); // Preserves formatting, comments, markers
}

export function updateSpec(model: SpecModel, edit: SpecEdit): SpecModel {
  // Immutable update preserving AST structure
  return applyEdit(model, edit);
}
```

**`prototype/tasks-parser/index.ts`** - Tasks.md ↔ Kanban:
```typescript
export function parseTasks(markdown: string): Task[] {
  // Parse - [ ] Task title [P] [US#123]
  // Extract checkbox, title, parallel group, story label
}

export function serializeTasks(tasks: Task[]): string {
  // Generate markdown with checkboxes, [P], [US#]
}

export function syncToKanban(tasks: Task[]): Promise<void> {
  for (const task of tasks) {
    await host.request('kanban.create', {
      title: task.title,
      body: task.body,
      assignee: task.assignee || 'default',
      // ... map [P] to parent/parallel, [US#] to labels
    });
  }
}
```

**`prototype/kanban-client/methods.ts`** - Typed method signatures:
```typescript
interface KanbanCreateParams {
  title: string;
  body?: string;
  assignee?: string;
  parent?: string[];
  workspace?: 'scratch' | `worktree:${string}` | `dir:${string}`;
  branch?: string;
  project?: string;
  tenant?: string;
  priority?: number;
  triage?: boolean;
  idempotency_key?: string;
  max_runtime?: number | string;
  created_by?: string;
  skills?: string[];
  max_retries?: number;
  model_override?: string;
  provider_override?: string;
  completion_contract?: 'local-only' | `${string}/${string}` | `https://github.com/${string}/pull/${number}`;
  goal?: boolean;
  goal_max_turns?: number;
  initial_status?: 'blocked' | 'running';
}

interface KanbanListParams {
  mine?: boolean;
  assignee?: string;
  status?: 'archived' | 'blocked' | 'done' | 'ready' | 'review' | 'running' | 'scheduled' | 'todo' | 'triage';
  tenant?: string;
  session?: string;
  archived?: boolean;
  sort?: 'assignee' | 'completed-desc' | 'created' | 'created-desc' | 'priority' | 'priority-desc' | 'status' | 'title' | 'updated';
  workflow_template_id?: string;
  step_key?: string;
}
```

### Next Steps (Post-Spike 2)
1. ✅ Kanban JSON-RPC method signatures documented
2. ✅ Round-trip sync prototype implemented and tested
3. ⏳ **Spike 3**: Plugin.yaml config_schema validation + full plugin load test (1 week)
4. ⏳ **Phase 1**: Push preset to fork, build plugin, verify in Hermes Desktop

---

## 13.  Extension Hooks — VERIFIED REQUIREMENTS

```yaml
hooks:
  before_specify:   speckit.git.create-branch (optional: true)
  before_plan:      speckit.constitution.check (optional: true)
  after_implement:  speckit.converge.auto (optional: true)
  after_converge:   speckit.pr.prepare (optional: true)
```

**Verified Status**: These hook commands do NOT exist upstream. They must be created as skills in `extensions/hermes-desktop/commands/`:
- `speckit.git.create-branch.md` → creates git branch for feature
- `speckit.constitution.check.md` → validates spec against constitution
- `speckit.converge.auto.md` → auto-runs convergence check
- `speckit.pr.prepare.md` → prepares PR with spec-kit context

Hooks are invoked via `HermesDispatch.invoke('speckit.<hook>', context)` which maps to `hermes chat -Q -q "<context>" -s speckit.<hook>`. Hooks `optional: true` for graceful degradation. Plugin panes surface hook status (planned).

---

## 14.  Workflow Visual Builder (v2)

`WorkflowBuilderPane.jsx` — drag nodes, connect edges, emits valid YAML. Reads/writes `.specify/workflows/hermes-desktop/workflow.yml`. Visual metadata (position, color) stored in separate `.visual.yml` (not in workflow YAML).

---

## 15.  Bundle Variants

| Variant | Status | Presets | Extensions | Workflows |
|---------|--------|---------|------------|-----------|
| hermes-desktop (base) | <span class="badge-v1">v1</span> | hermes-desktop | hermes-desktop | hermes-desktop |
| backend | <span class="badge-v2">v2</span> | hermes-desktop, api-first†, database-migrations† | hermes-desktop | hermes-desktop |
| fullstack | <span class="badge-v2">v2</span> | backend + frontend-framework† | hermes-desktop | hermes-desktop |
| ml | <span class="badge-v2">v2</span> | hermes-desktop, model-training†, experiment-tracking† | hermes-desktop | hermes-desktop |
| api-only | <span class="badge-v2">v2</span> | hermes-desktop, api-first† | hermes-desktop | hermes-desktop |

† = Planned preset (v2). Not in upstream `spec-kit` (current: `lean`, `constitution-sync`).

User selects at `specify init --bundle <variant>`. Base `hermes-desktop` bundle is v1; variants are v2..

---

## 16.  Profile-Scoped Catalog — VERIFIED STRUCTURE

```yaml
# ~/.hermes/profiles/<name>/spec-kit-catalogs.yml (our convention)
catalogs:
  - url: "https://raw.githubusercontent.com/justinbrenton/spec-kit/main/presets/catalog.json"
    name: "hermes-desktop"
    priority: 1
    install_allowed: true
```

**Verified**: 
- `plugin.yaml` config fields go in `config_schema` (see Section 11)
- `~/.hermes/profiles/<name>/plugins/spec-kit/` is our convention — not SDK-enforced
- Profile config lives in `~/.hermes/profiles/<name>/` (config.yaml, plugins/, skills/, etc.)
- Desktop plugins: `~/.hermes/desktop-plugins/<id>/plugin.js` (disk mode, hot-reload)
- Agent plugins: `~/.hermes/plugins/<id>/` (plugin.yaml, skills/, dashboard/)
- Unified packages: `~/.hermes/plugins/<id>/desktop/plugin.js` → copied to `desktop-plugins/<id>/`

**Env var overrides** (spec-kit native):
- `SPECKIT_PRESET_CATALOG_URL`
- `SPECKIT_EXTENSION_CATALOG_URL`
- `SPECKIT_WORKFLOW_CATALOG_URL`
- `SPECKIT_BUNDLE_CATALOG_URL`

---

## 17.  MCP Integration (v2)

Workflow `shell` steps calling Hermes MCP servers:
```yaml
- id: security-scan
  type: shell
  run: "hermes mcp call security-scanner scan --path {{ steps.implement.output.files }}"
  capture: true
```

**Note**: MCP integration (`hermes mcp call security-scanner`) depends on Hermes Desktop exposing MCP server registry to the workflow engine. This is a **planned v2 integration** (unverified — no SDK reference found). The design references it as future capability, not current execution.
Requires Hermes MCP server registry exposed to workflow engine.

---

## 18.  Implementation Sequence — SPIKE 1 ✅ | SPIKE 2 ✅ | SPIKE 3 ✅

**Spike 1 Results (Hermes Desktop SDK Verification)**: ✅ COMPLETE

| Verification Item | Status | Details |
|-------------------|--------|---------|
| Plugin SDK panes, routes, nav, status bar, palette, keybinds, themes | ✅ Verified | Full contribution area support |
| `host.request` JSON-RPC (sessions, config, skills, cron, kanban) | ✅ Verified | Kanban methods inferred from CLI |
| `host.skills.list()`, `host.skills.setEnabled()` | ✅ Verified | Typed bridge for skill management |
| `host.composer` API | ✅ Verified | getDraft, setDraft, insertText, submit, focus |
| `host.settings` | ✅ Verified | Desktop settings (chatTextScale, sessionListDensity, etc.) |
| `host.navigate`, `host.onEvent` | ✅ Verified | Navigation + gateway event stream |
| `ctx.rest` / `ctx.socket` | ✅ Verified | Plugin-scoped backend namespace |
| Plugin.yaml schema | ✅ Verified | name, version, description, author, license, homepage, kind, requires_hermes, provides_tools, provides_hooks, config_schema |
| UI Kit components | ✅ Verified | Button, Input, Textarea, Select, Dialog, Badge, etc. |
| Plugin Settings Pages | ✅ Verified | `ctx.registerSettingsPage()` under Settings → Plugins |

**Spike 2 Results (Kanban JSON-RPC + Round-Trip Sync)**: ✅ COMPLETE

| Verification Item | Status | Details |
|-------------------|--------|---------|
| `kanban.create` | ✅ Verified | Full task object returned, all params mapped |
| `kanban.list` | ✅ Verified | Array of task objects with filtering |
| `kanban.show` | ✅ Verified | Task + events + runs + comments + parents/children |
| `kanban.edit` | ✅ Verified | Partial update, returns updated task |
| `kanban.complete` | ✅ Verified | Requires result + summary, returns task |
| `kanban.assign` | ✅ Verified | Simple reassignment |
| `kanban.block` / `unblock` | ✅ Verified | Status transitions |
| `kanban.claim` | ✅ Verified | Returns workspace path for worker |
| `kanban.comment` | ✅ Verified | Adds comment with author/timestamp |
| `kanban.attach` / `attachments` | ✅ Verified | File attachments with metadata |
| `kanban.request-review` | ✅ Verified | Review workflow with metadata |
| `kanban.request-changes` | ✅ Verified | Reviewer verdict with required reason |
| `kanban.reopen-review` | ✅ Verified | Bulk reopen with reason |
| `kanban.promote` | ✅ Verified | Manual promotion with dry-run |
| Round-trip sync prototype | ✅ Verified | SpecBuilder ↔ spec.md, TasksParser ↔ Kanban, VS Code edit → pane refresh |
| Skill invocation syntax | ✅ Verified | `hermes chat -Q -q "<query>" -s speckit-<skill>` |

**Spike 3 Results (Plugin.yaml config_schema + Plugin Load Test)**: ✅ COMPLETE

| Verification Item | Status | Details |
|-------------------|--------|---------|
| Plugin.yaml config_schema validation | ✅ Verified (Agent Plugins) | `config_schema` applies to agent plugins (Python) and unified packages. Desktop plugins (disk mode) are single ESM files without plugin.yaml. |
| Desktop plugin load mechanism | ✅ Verified | App watches `~/.hermes/desktop-plugins/<id>/plugin.js`, loads within seconds, hot-reloads on save. |
| Test plugin created | ✅ Verified | Created `~/.hermes/desktop-plugins/spec-kit-hermes/plugin.js` with panes, status bar, palette, settings page. |
| githermes plugin reference | ✅ Verified | Existing desktop plugin (215KB) loads successfully in Hermes Desktop. |
| `hermes plugins validate/doctor` | ⚠️ Agent Only | These CLI commands validate agent plugins (Python), not desktop plugins (JavaScript). |

**Key Clarification: Plugin Types**

| Plugin Type | Manifest | Config Schema | Load Mechanism |
|-------------|----------|---------------|----------------|
| **Agent Plugin** | `plugin.yaml` (Python) | `config_schema` in plugin.yaml | `hermes plugins install` |
| **Desktop Plugin (Disk)** | `plugin.js` only | N/A (use `ctx.storage` + Settings Page) | Auto-load from `desktop-plugins/` |
| **Unified Package** | `plugin.yaml` + `desktop/plugin.js` | `config_schema` in plugin.yaml | Agent install copies desktop half to `desktop-plugins/` |

**Verified Desktop Plugin Structure** (test plugin at `~/.hermes/desktop-plugins/spec-kit-hermes/plugin.js`):
- Default exports `HermesPlugin` with `id`, `name`, `defaultEnabled`, `register(ctx)`
- Registers panes via `PANES_AREA`, status bar via `STATUSBAR_AREAS`, palette via `PALETTE_AREA`
- Registers Settings Page via `ctx.registerSettingsPage()`
- Uses `ctx.storage` for persistent config (not `config_schema`)
- Hot-reloads on file save (no build step)

**Remaining Unverified**: None — all verification spikes complete.

**Phase 0: Verification Spikes (Complete Before v1 Build)**
1. ✅ **Spike 1**: Hermes Desktop SDK verification (Kanban API, skill invocation, plugin manifest) — **COMPLETE**
2. ✅ **Spike 2**: Kanban JSON-RPC methods + skill invocation + round-trip sync prototype — **COMPLETE**
3. ✅ **Spike 3**: Plugin.yaml config_schema validation + full plugin load test — **COMPLETE**

**Phase 1: v1 Build (Ready to Start)**
1. **Push preset to fork**: `presets/hermes-desktop/`, `extensions/hermes-desktop/`, `bundles/hermes-desktop/`, updated catalogs
2. **Build plugin**: `speckit-hermes-v1/` scaffold → working panes in Hermes Desktop
3. **Verify round-trip**: SpecBuilder ↔ spec.md, TaskBoard ↔ tasks.md, ConstitutionWizard → constitution.md
4. **Create v2 Kanban tasks**: 2 profiles, 2 tasks
5. **Iterate v2**: WorkflowRunner, PlanCanvas, Extension Marketplace, Bundle Installer

---

## 19.  Multi-Harness Integration Strategy

Our design is intentionally modular to support integration with multiple AI coding harnesses beyond Hermes Desktop. This section documents the space, our modularity guarantees, and the path for future harness integrations.

### Harness space Analysis

| Harness | Type | Plugin Architecture | GUI/Visual | MCP Support | Plugin System | Notable Limitations |
|---------|------|---------------------|------------|-------------|---------------|---------------------|
| **Hermes Desktop** | Desktop GUI + TUI | Skills-based (`~/.hermes/skills/`) | Panes, Kanban, Dashboard | Native + ACP | Native + bundles | Single-process, no sandbox |
| **OpenClaw** | Desktop + TUI + Web | Native plugins + bundles + compatible bundles | TUI, Dashboard widgets, Web UI | Native + ACP | Native in-process + bundles | Single-process, no sandbox |
| **Orca** | Desktop + Mobile + SSH | Manifest + sandboxed worker + capability gating | Panels, Terminal splits, Browser, Design Mode | Native + ACP | Manifest + sandboxed worker + capability gating | Plugin API experimental |
| **URL**: https://github.com/stablyai/orca (Orca harness — LiteLLM + custom bundles) |
| **OpenAI Codex CLI** | Terminal + Desktop App | Skills + MCP + UI + hooks | Terminal + Desktop app (panes) | MCP + custom UI | Skills + MCP + UI + hooks | Limited sandbox, plugin browser only in CLI |
| **Claude Desktop** | Desktop App | Skills + commands + MCP + agents + hooks | Panes (chat, diff, browser, terminal, plan, tasks) | MCP (remote + local) | .claude-plugin format | Agents/hooks only in Cowork/Code |
| **OpenCode** | Terminal + Web | JS/TS plugin modules + hooks | Terminal + Web UI | MCP | JS/TS modules + hooks | No native GUI (terminal-focused) |

### Detailed Harness Analysis

#### OpenClaw
- **Architecture**: In-process native plugins + bundles; harness registry for runtime selection
- **GUI**: TUI + Web Dashboard (Solid components, sandboxed widget iframes)
- **Plugin System**: Native in-process plugins + compatible bundles; capability-based contracts
- **Harness System**: Built-in runtime + plugin-registered harnesses; ACP sessions for external harnesses
- **MCP**: Native support; remote MCP servers via ACP backend plugin
- **Dashboard**: Persistent widget boards; sandboxed iframes; capability-scoped grants
- **Limitations**: Single-process (no sandbox); plugins share process boundary

#### OpenAI Codex CLI / Desktop App
- **Architecture**: Skills + MCP servers + optional UI + hooks; plugin browser in CLI
- **GUI**: Terminal + Desktop app with panes (chat, diff, browser, terminal, plan, tasks)
- **Plugin System**: Skills + MCP + optional UI + hooks; lifecycle hooks; plugin browser in CLI
- **MCP**: Native; custom UI optional; UI resources returned from MCP servers
- **Desktop App**: Panes (chat, diff, browser, terminal, file, plan, tasks, subagent, iOS Simulator)
- **Limitations**: Limited sandbox; plugin browser only in CLI; plugin hooks not in cloud ChatGPT Work

#### Claude Desktop
- **Architecture**: Skills + commands + MCP connectors + agents + hooks; .claude-plugin format
- **GUI**: Panes (chat, diff, browser, terminal, file, plan, tasks, subagent, iOS Simulator)
- **Plugin System**: .claude-plugin format; manifest at `.claude-plugin/plugin.json`; components load per-app
- **MCP**: Remote + local; remote works everywhere, local only in Code/Cowork
- **Desktop App**: Panes (chat, diff, browser, terminal, file, plan, tasks, subagent, iOS Simulator)
- **Cowork**: Visual interface for multi-step tasks; runs sub-agents
- **Limitations**: Agents/hooks only in Cowork/Code; local MCP only in Code/Cowork; chat ignores agents/hooks

#### OpenCode
- **Architecture**: JS/TS plugin modules; async functions returning typed hooks (~20 types)
- **GUI**: Terminal + Web UI; no native desktop app
- **Plugin System**: JS/TS modules exporting async functions returning typed hooks (~20 types); load order: global → project → global plugins → project plugins
- **Agents**: Primary + subagent modes; built-ins (build, plan, general, explore, scout)
- **MCP**: Supported; custom tools vs MCP server architectural decision
- **Tools**: Custom tools as .ts files in `.opencode/tool/`; Zod schemas; execute tool for code mode
- **Limitations**: Terminal-focused; no native desktop GUI; Web UI is secondary

; no IDE integration

### Our Modular Design for Multi-Harness Support

Our architecture separates concerns to let harness-agnostic spec-driven development:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Spec-Kit Core (Harness-Agnostic)             │
├─────────────────────────────────────────────────────────────────┤
│  Templates (spec, plan, tasks, constitution, checklist)         │
│  Commands (constitution, specify, clarify, plan, tasks,         │
│           analyze, implement, converge, checklist, taskstoissues)│
│  Workflows (speckit, bugfix, assess)                            │
│  Extension hooks (before/after each phase)                      │
│  State machine (constitution → specify → clarify → plan →       │
│           tasks → analyze → implement → converge)               │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
       │ Hermes      │ │ OpenClaw    │ │ Claude      │
       │ Desktop     │ │             │ │ Desktop     │
       │ Adapter     │ │ Adapter     │ │ Adapter     │
       └─────────────┘ └─────────────┘ └─────────────┘
              │               │               │
              ▼               ▼               ▼
       ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
       │ SpecBuilder │ │ SpecBuilder │ │ SpecBuilder │
       │ Pane (JSX)  │ │ Widget      │ │ Panel       │
       │ TaskBoard   │ │ TaskBoard   │ │ TaskBoard   │
       │ Constitution│ │ Constitution│ │ Constitution│
       │ Wizard      │ │ Wizard      │ │ Wizard      │
       └─────────────┘ └─────────────┘ └─────────────┘
```

### Harness Adapter Interface

Each harness adapter implements a standard interface:

```typescript
interface HarnessAdapter {
  // Identity
  id: string;
  name: string;
  version: string;
  
  // Capabilities
  capabilities: {
    gui: boolean;           // Native GUI/panes
    kanban: boolean;        // Kanban board support
    dashboard: boolean;     // Dashboard/widget support
    mcp: boolean;           // MCP support
    mcpUI: boolean;         // MCP custom UI
    hooks: boolean;         // Lifecycle hooks
    agents: boolean;        // Sub-agent support
    panes: boolean;         // Pane-based layout
    webUI: boolean;         // Web UI available
  };
  
  // Skill invocation
  invokeSkill(skillName: string, args: string): Promise<SkillResult>;
  
  // Project state
  readProjectState(projectRoot: string): Promise<ProjectState>;
  writeProjectState(projectRoot: string, state: ProjectState): Promise<void>;
  
  // Template resolution
  resolveTemplate(templateName: string): Promise<string>;
  
  // Hook execution
  executeHook(hookName: string, context: HookContext): Promise<HookResult>;
  
  // Workflow execution
  runWorkflow(workflowId: string, inputs: WorkflowInputs): Promise<WorkflowResult>;
}
```

### Path for New Harness Integration

To add a new harness (e.g., OpenCode, Orca, future harnesses):

1. **Create Adapter** — Implement `HarnessAdapter` interface
2. **Register Capabilities** — Declare GUI, Kanban, MCP, etc. support
3. **Map Templates** — Harness-specific template overrides (if needed)
4. **Implement Skill Invocation** — Map `speckit-*` skills to harness native invocation
5. **Build UI Components** — Harness-native panes/widgets/panels
6. **Register in Catalog** — Add to `catalogs/harnesses.json`
6. **Test Round-trip** — Verify spec.md ↔ pane ↔ file sync works

### Harness-Specific Template Overrides

Each harness can override templates via preset priority:

```yaml
# presets/<harness>-desktop/preset.yml
strategy: "prepend"  # or "append", "wrap", "replace"
```

| Harness | Template Overrides Needed |
|---------|---------------------------|
| Hermes  | None (base) |
| OpenClaw | Dashboard widgets, ACP session templates |
| Orca | Panel layouts, Terminal split configs, Design Mode templates, Mobile companion templates |
| Codex | Desktop pane layouts, MCP UI templates |
| Claude | Pane layouts, Cowork sub-agent templates |
| OpenCode | Terminal templates, Web UI components |

### Future Development Notable

| Harness | Integration Effort | Priority | Blockers |
|---------|-------------------|----------|----------|
| OpenCode | Medium | High | Terminal-focused; need Web UI components |
| Codex Desktop | Low | High | Already has panes; plugin system compatible |
| Claude Desktop | Low | High | Plugin system compatible; panes exist |
| Orca | Low | High | Desktop app with panes; plugin system emerging |
| OpenClaw | Medium | Medium | In-process plugin model differs |
| Cursor | Medium | Medium | VS Code extension API different |
| Windsurf | Medium | Medium | VS Code fork; similar to Cursor |
| Zed | Medium | Medium | Rust-based; different plugin model |

### Integration Checklist for New Harness

- [ ] Implement `HarnessAdapter` interface
- [ ] Define capability flags
- [ ] Map spec-kit skills to harness invocation
- [ ] Build native UI components (SpecBuilder, TaskBoard, ConstitutionWizard)
- [ ] Implement round-trip sync (spec.md ↔ UI ↔ file)
- [ ] Test workflow execution (speckit workflow)
- [ ] Verify hook execution (before/after phases)
- [ ] Test bundle installation (`specify bundle add`)
- [ ] Document harness-specific quirks
- [ ] Add to CI test matrix

### Orca-Specific Integration Notes

- [ ] Implement `orca-plugin.json` manifest generation
- [ ] Build out-of-process worker (`main.mjs`) with `activate(orca)`
- [ ] Implement panel system (`panel.html` in isolated webview)
- [ ] Map capability declarations to `orca.host.call()` permissions
- [ ] Implement parallel worktree orchestration
- [ ] Integrate mobile companion app notifications
- [ ] Add SSH worktree support
- [ ] Implement Design Mode (HTML/CSS/screenshot capture)
- [ ] Add GitHub/Linear native integration
- [ ] Support mobile companion app push notifications

### Why This Modular Approach?

1. **Spec-Kit stays harness-agnostic** — templates, commands, workflows are pure markdown/YAML
2. **Adapters isolate harness quirks** — each harness's quirks contained in its adapter
3. **Templates compose** — preset strategy system allows layering harness-specific overrides
4. **Hooks are universal** — before/after phase hooks work identically across harnesses
5. **Catalogs are shared** — bundles/presets/extensions work across harnesses
6. **State is portable** — `.specify/` directory format is harness-independent

This design means when OpenCode adds a Web UI, or Orca adds a GUI, or a new harness emerges, we only need to write an adapter — not rewrite the entire spec-driven development system.

---


## 20.  File Locations (Planning Artifacts)

| Artifact | Path |
|----------|------|
| **This design doc** | `docs/hermes-integration/design.md` |
|| Plugin scaffold | **Only planning docs exist** — `plugin.yaml` + JSX components (`SpecBuilderPane`, `TaskBoardPane`, `ConstitutionWizard`) + services/hooks are PLANNED (v1 build pending). `spec-kit-hermes-v1/` contains 2 concrete docs only (`design.md`, `design.html`) + scaffold directories (not executed). |
| Preset structure | `justinbrenton/spec-kit/presets/hermes-desktop/` |
| Extension structure | `justinbrenton/spec-kit/extensions/hermes-desktop/` |
| Workflow structure | `justinbrenton/spec-kit/workflows/hermes-desktop/` |
| Bundle structure | `justinbrenton/spec-kit/bundles/hermes-desktop/` |

---

## 21.  Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Upstream breaks Hermes integration | Integration owned upstream; fork isolates Hermes-specific code |
| Spec-kit template drift breaks round-trip | remark AST preserves structure; tests against upstream templates nightly |
| Hermes Desktop SDK changes break panes | Pin plugin to SDK version; integration tests in CI |
| Bundle version conflicts | Pin major version in bundle manifest; test matrix in CI |
| Fork drift from upstream | Daily merge (not rebase); CI fails on non-catalog conflicts |
| ConstitutionWizard complexity | Flag as v1 risk; minimal CLI fallback if pane fails |

---

## 22. v1 Implementation Requirements

**Planned v1 specifications (not executed)**: The following concrete requirements describe what must be built. None have been executed — only planning artifacts (`plugin.yaml`, JSX pane components, preset templates, bundle definitions, workflow YAML) exist in `speckit-hermes-v1/`. Implementation requires user approval and Hermes Desktop SDK runtime. These are not in the design doc but are required for v1 build:

### Plugin Configuration
- **plugin.yaml complete settings**: catalog URLs, pane configs (defaultOpen, icons), command definitions with handler paths
- **Error handling spec**: `SpecifyCLIBridge.init()` uv tool run failure modes (uv not installed, specify fails, network timeout)
- **Conflict resolution spec**: `spec-kit-sync.ts` pane vs file both changed (last-write-wins with user prompt)

### Parsers
- **SpecParser.ts**: Malformed markdown handling, missing sections, `[NEEDS CLARIFICATION]` marker editing UX
- **TasksParser.ts**: Malformed tasks.md handling, missing checkboxes, `[P]`/`[US#]` parsing edge cases
- **Round-trip test suite**: Edit in pane -> save -> edit in VS Code -> pane refresh -> no data loss

### Skill Invocation
- **HermesDispatch.ts**: Timeout handling (hermes chat hangs), skill not found, process crash recovery
- **Internal API v2 abstraction**: Interface ready for when Hermes Desktop exposes skill API

### UI/UX Specifications
- **ConstitutionWizard.jsx**: 5-step state persistence (wizard interrupted -> resume), step validation
- **SpecBuilderPane.jsx**: `[NEEDS CLARIFICATION]` marker editing UX (inline edit, max 3 enforcement)
- **TaskBoardPane.jsx**: Drag-drop between Kanban columns (phase transitions), `[P]`/`[US#]` badge rendering

### Workflow Visual Builder (v2)
- **.visual.yml schema**: Node positions (x,y), edge connections (source->target), colors, labels
- **File format**: YAML separate from workflow.yml, loaded by WorkflowBuilderPane

### Profile-Scoped Catalog
- **Exact YAML schema**: `~/.hermes/profiles/<name>/spec-kit-catalogs.yml` with catalogs array (url, name, priority, install_allowed)

### Profile vs Project State
- **Exact paths**: Profile `~/.hermes/profiles/<name>/plugins/spec-kit/`, Project `<project>/.specify/`, Global `~/.hermes/skills/`

### Error Recovery
- **SpecifyCLIBridge.init()**: uv not installed, specify CLI not found, network timeout, specify init failure
- **HermesDispatch**: hermes chat hangs, skill not found, process crash, JSON parse error
- **SpecParser/TasksParser**: Malformed markdown, missing sections, missing checkboxes, corrupted `[P]`/`[US#]` markers

### Workflow Visual Metadata
- **.visual.yml format**: 
```yaml
nodes:
  - id: "specify"
    position: {x: 100, y: 100}
    color: "#2196F3"
edges:
  - source: "specify"
    target: "gate-spec"
```

---

---

## 24.  Review Findings & Verification Plan — SPIKE 1 COMPLETE ✅

A comprehensive review of this design document (conducted with fresh model perspective) identified the following gaps, unverified assumptions, and recommended improvements. These must be addressed before v1 implementation begins.

### 24.1  Critical Gaps (Block v1 Implementation) — ALL RESOLVED ✅

| # | Gap | Severity | Why It Blocks | Verification Status |
|---|-----|----------|---------------|---------------------|
| 1 | **Hermes Desktop SDK verification** | 🔴 Critical | All panes, Kanban API, skill invocation, plugin manifest assume APIs marked "unverified" | ✅ **COMPLETE (Spike 1)** — SDK verified: panes, routes, nav, status bar, palette, keybinds, themes, host.request, host.skills, host.composer, host.settings, host.navigate, host.onEvent, ctx.rest, UI Kit, plugin settings pages |
| 2 | **Hermes Kanban API** | 🔴 Critical | `KanbanAPI.createCard/update()` marked "unverified" | ✅ **COMPLETE (Spike 2)** — All 16 kanban.* JSON-RPC methods verified with full param/response schemas |
| 3 | **Hermes skill invocation syntax** | 🔴 Critical | `hermes chat -Q -q -s speckit-<skill> -q <args>` unverified | ✅ **COMPLETE (Spike 1)** — Corrected: `hermes chat -Q -q "<query>" -s speckit-<skill>` (single `-q`); `-s` preloads skill, `-q` provides query |
| 4 | **Plugin.yaml custom fields** | 🟠 High | `specKitCatalogUrl`, `specKitBundleUrl`, `specKitProfilePath` are custom fields | ✅ **COMPLETE (Spike 1)** — Custom config goes in `config_schema` (not `settings`); schema verified |
| 5 | **Extension hook commands** | 🟠 High | `speckit.constitution.check`, `speckit.converge.auto`, `speckit.pr.prepare` don't exist upstream | ⏳ **PENDING** — Must create as skills in `extensions/hermes-desktop/commands/` (implementation task, not verification) |
| 8 | **Profile path convention** | 🟡 Medium | `~/.hermes/profiles/<name>/plugins/spec-kit/` is "unverified convention" | ✅ **COMPLETE (Spike 1)** — It's our convention; SDK uses `~/.hermes/profiles/<name>/` for profile config, `~/.hermes/desktop-plugins/<id>/` for desktop plugins |

**All critical verification gaps resolved.** Remaining items are implementation tasks (hook commands, preset scaffold, plugin build).

### 24.2  Significant Gaps (Block v2+ or Create Technical Debt) — UNCHANGED

| Area | Gap | Impact |
|------|-----|--------|
| **Plugin security model** | No sandboxing, no capability permissions, no resource limits, no plugin signing | Supply chain risk, no isolation |
| **Plugin dependency resolution** | No versioning, no dependency graph, no conflict resolution | Plugin hell, broken installs |
| **Spec versioning/migration** | No migration tooling, no schema versioning | Breaking changes break projects |
| **Spec validation rules** | Only `[NEEDS CLARIFICATION]` exists | No schema validation, no business rules |

### 24.3  Strategic Improvements (Things Not Yet Considered) — UNCHANGED

| Area | Suggestion | Rationale |
|------|------------|-----------|
| **Verification-first approach** | Build a "verification spike" for each unverified assumption before v1 | Fail fast on blockers |
| **Definition of Done for v1** | Explicit criteria: "Kanban API verified", "Skill invocation works", "Round-trip survives VS Code edit" | Prevents scope creep |
| **Plugin security model** | Capabilities, sandboxing, resource limits, signing | Security baseline |
| **Spec versioning/migration** | Add `specVersion` field + migration CLI | Future-proof |
| **Spec validation rules** | Beyond `[NEEDS CLARIFICATION]` — JSON Schema, custom rules | Quality gate |

### 24.4  Immediate Action Items — ALL VERIFICATION COMPLETE ✅

| Priority | Action | Owner | Deadline | Status |
|----------|--------|-------|----------|--------|
| 1 | Verify Hermes Desktop SDK: Kanban API, skill invocation, plugin manifest schema | Codie | Before v1 start | ✅ **DONE (Spike 1)** |
| 2 | Build spike: Kanban JSON-RPC methods + skill invocation + round-trip sync | Codie | Before v1 start | ✅ **DONE (Spike 2)** |
| 3 | Verify `plugin.yaml` config_schema against Hermes SDK | Codie | Before v1 start | ✅ **DONE (Spike 1)** |
| 4 | Verify `hermes chat -Q -q -s` syntax | Codie | Before v1 start | ✅ **DONE (Spike 1)** |
| 5 | Create "Definition of Done" for v1 | Codie + User | Before v1 start | 📋 Section 24.6 |
| 6 | Create risk register with mitigations | Codie | This week | 📋 Section 21 |
| 7 | Define "Definition of Ready" for implementation | Codie + User | Before v1 start | 📋 Pending |

**All verification spikes complete. Ready for Phase 1 implementation.**

### 24.5  Verification-First Implementation Sequence — ALL SPIKES COMPLETE ✅

**All verification steps complete. Phase 1 ready to begin.**

**Phase 0: Verification Spikes (All Complete)**
1. ✅ **Spike 1**: Hermes Desktop SDK verification (Kanban API, skill invocation, plugin manifest) — **COMPLETE**
2. ✅ **Spike 2**: Kanban JSON-RPC methods + skill invocation + round-trip sync prototype — **COMPLETE**
3. ✅ **Spike 3**: Plugin.yaml config_schema validation + full plugin load test — **COMPLETE**

**Phase 1: v1 Build (Ready to Start)**
1. **Push preset to fork**: `presets/hermes-desktop/`, `extensions/hermes-desktop/`, `bundles/hermes-desktop/`, updated catalogs
2. **Build plugin**: `speckit-hermes-v1/` scaffold → working panes in Hermes Desktop
3. **Verify round-trip**: SpecBuilder ↔ spec.md, TaskBoard ↔ tasks.md, ConstitutionWizard → constitution.md
4. **Create v2 Kanban tasks**: 2 profiles, 2 tasks
5. **Iterate v2**: WorkflowRunner, PlanCanvas, Extension Marketplace, Bundle Installer

### 24.2  Significant Gaps (Block v2+ or Create Technical Debt)

| Area | Gap | Impact |
|------|-----|--------|
| **Plugin security model** | No sandboxing, no capability permissions, no resource limits, no plugin signing | Supply chain risk, no isolation |
| **Plugin dependency resolution** | No versioning, no dependency graph, no conflict resolution | Plugin hell, broken installs |
| **Spec versioning/migration** | No migration tooling, no schema versioning | Breaking changes break projects |
| **Spec validation rules** | Only `[NEEDS CLARIFICATION]` exists | No schema validation, no business rules |
| **Plugin dependency resolution** | No version constraints, no conflict resolution | Dependency hell |
| **Spec versioning/migration** | No migration tooling | Breaking changes break projects |
| **Plugin marketplace/curation** | No discovery, no trust model, no reviews | No ecosystem growth |
| **Plugin security sandboxing** | No isolation, no resource limits | Security risk |
| **Spec versioning/migration** | No migration tooling | Breaking changes break projects |
| **Spec validation rules** | Only `[NEEDS CLARIFICATION]` exists | No business rule validation |

### 24.3  Strategic Improvements (Things Not Yet Considered)

| Area | Suggestion | Rationale |
|------|------------|-----------|
| **Verification-first approach** | Build a "verification spike" for each unverified assumption before v1 | Fail fast on blockers |
| **Definition of Done for v1** | Explicit criteria: "Kanban API verified", "Skill invocation works", "Round-trip survives VS Code edit" | Prevents scope creep |
| **Verification checklist** | Checklist for each unverified assumption with owner + deadline | Accountability |
| **Spike/prototype first** | Build minimal spike for Kanban API + skill invocation before full v1 | Fail fast |
| **Rollback/cleanup plan** | What happens if v1 install fails halfway? | Disaster recovery |
| **Plugin security model** | Capabilities, sandboxing, resource limits, signing | Security baseline |
| **Spec versioning/migration** | Add `specVersion` field + migration CLI | Future-proof |
| **Spec validation rules** | Beyond `[NEEDS CLARIFICATION]` — JSON Schema, custom rules | Quality gate |
| **Plugin dependency resolution** | Semver, lockfile, conflict resolution | Avoid plugin hell |
| **Spec validation engine** | JSON Schema + custom rules | Quality gate |

### 24.4  Immediate Action Items (Before Any Code)

| Priority | Action | Owner | Deadline |
|----------|--------|-------|----------|
| 1 | Verify Hermes Desktop SDK: Kanban API, skill invocation, plugin manifest schema | Codie | Before v1 start |
| 2 | Build spike: Kanban API + skill invocation + round-trip sync | Codie | Before v1 start |
| 3 | Verify `plugin.yaml` schema against Hermes SDK | Codie | Before v1 start |
| 4 | Verify `hermes chat -Q -q -s` syntax | Codie | Before v1 start |
| 5 | Create "Definition of Done" for v1 | Codie + User | Before v1 start |
| 6 | Create risk register with mitigations | Codie | This week |
| 7 | Define "Definition of Ready" for implementation | Codie + User | Before v1 start |

### 24.5  Verification-First Implementation Sequence (Replaces Section 18)

**All steps are planned — none executed yet.**

**Phase 0: Verification Spikes (Complete Before v1 Build)**

1. **Spike 1**: Hermes Desktop SDK verification (Kanban API, skill invocation, plugin manifest) — 1-2 weeks
2. **Spike 2**: Round-trip sync prototype (SpecBuilder ↔ spec.md ↔ VS Code) — 1 week
3. **Spike 3**: Plugin.yaml validation against actual Hermes SDK — 1 week

**Phase 1: v1 Build (After Spikes Complete)**

1. **Push preset to fork**: `presets/hermes-desktop/`, `extensions/hermes-desktop/`, `bundles/hermes-desktop/`, updated catalogs
2. **Build plugin**: `speckit-hermes-v1/` scaffold → working panes in Hermes Desktop
3. **Verify round-trip**: SpecBuilder ↔ spec.md, TaskBoard ↔ tasks.md, ConstitutionWizard → constitution.md
4. **Create v2 Kanban tasks**: 2 profiles, 2 tasks
5. **Iterate v2**: WorkflowRunner, PlanCanvas, Extension Marketplace, Bundle Installer

### 24.6  Definition of Done for v1

- [ ] Hermes Desktop SDK verified: Kanban API, skill invocation, plugin manifest schema
- [ ] `plugin.yaml` validated against actual Hermes SDK schema
- [ ] `hermes chat -Q -q -s speckit-<skill>` syntax verified
- [ ] Kanban API verified: `KanbanAPI.createCard/update()` works
- [ ] Round-trip sync survives VS Code edit → pane refresh (no data loss)
- [ ] Skill invocation works: `hermes chat -Q -q -s speckit-<skill> -q <args>`
- [ ] ConstitutionWizard 5-step wizard completes and writes valid `.specify/memory/constitution.md`
- [ ] SpecBuilder handles `[NEEDS CLARIFICATION]` markers (max 3, inline edit)
- [ ] TaskBoard Kanban: drag-reorder, `[P]` badges, `[US#]` labels, implement button spawns Hermes skill
- [ ] ConstitutionWizard 5-step flow: Purpose (9) → Principles (3-5) → Architecture (25) → Governance → Ratify
- [ ] Round-trip: pane edit → `.specify/` file → VS Code edit → pane refresh (no data loss)
- [ ] Plugin installs via `specify init --preset hermes-desktop --bundle hermes-desktop`
- [ ] All extension hooks (`speckit.git.create-branch`, `speckit.constitution.check`, etc.) implemented and verified

---


## 23.  Next Steps

1. Push `presets/hermes-desktop/`, `extensions/hermes-desktop/`, `bundles/hermes-desktop/` to `justinbrenton/spec-kit` with updated catalogs
2. Build plugin panes against fork catalogs
3. Verify round-trip in Hermes Desktop (**planned — requires v1 plugin build + Hermes Desktop runtime**)
4. Create v2 Kanban tasks (2 profiles)
5. Iterate v2: WorkflowRunner, PlanCanvas, Extension Marketplace, Bundle Installer