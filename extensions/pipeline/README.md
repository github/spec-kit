# Pipeline — a Spec Kit extension

Chain the [Spec Kit](https://github.com/github/spec-kit) phases into **one guided, single-invocation pipeline** instead of hand-running seven commands.

```
specify → clarify → plan → tasks → analyze → implement
```

`/speckit.pipeline.run` drives each phase in order, pausing exactly once — at an interactive **clarify** gate — then advances unattended through the rest, re-running `analyze` until findings are resolved (up to 3 cycles) before it implements. The phase order is produced by a small, deterministic resolver, so a tailored pipeline (`--skip`, `--add`) always lands in the same canonical order.

## Why

Taking a feature from description to implemented change means issuing `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement` by hand — and hand-resolving each analyze finding in between. This extension collapses that to a single invocation with one human checkpoint, while keeping every phase's own command as the source of truth (it *drives* the stock commands, it does not reimplement them).

## Commands

| Command | What it does |
|---|---|
| `speckit.pipeline.run` | Run the full pipeline from one feature description, with a single clarify checkpoint. |
| `speckit.pipeline.preview` | Print the resolved phase plan for the given flags without running anything (dry run). |

### Flags

- `--skip <csv>` — drop default phases (e.g. `--skip clarify,analyze`). `specify` and `implement` cannot be skipped.
- `--add <csv>` — insert optional phases: `constitution` (before specify), `checklist` (after tasks).
- `--yes` — unattended run. Answers the clarify gate itself (grounded in the spec/repo) rather than pausing for a human, and **halts before `plan`** if a question is too consequential to answer unattended. `--yes` never means "no clarification" — use `--skip clarify` for that.

## Examples

```
# Full default run
/speckit.pipeline.run Add rate limiting to the public API

# See the plan first, then run a tailored pipeline
/speckit.pipeline.preview --add checklist --skip clarify
/speckit.pipeline.run --add checklist Add a healthcheck endpoint

# Unattended (CI / routine), clarify answered in-place, halts on a consequential question
/speckit.pipeline.run --yes Migrate config loading to env vars
```

## How the resolver works

`scripts/resolve_phases.py` (pure Python, stdlib only) is the deterministic core. It takes the requested skip/add sets, validates them, and returns the phase list in a fixed canonical order. Ordering is a pure function of the *effective set*, so flag ordering never changes the result. Validation is strict, with dedicated exit codes:

| Exit | Meaning |
|---|---|
| 0 | resolved OK |
| 10 | unknown phase name |
| 11 | a phase is in both `--skip` and `--add` |
| 12 | `--add` names a non-insertable phase |
| 13 | `--skip` targets a required phase (`specify`/`implement`) |
| 14 | dependency break — a retained phase's dependency was skipped |

`run` and `preview` both call the resolver, so a bad flag combination is caught before any phase runs. `scripts/bash/resolve-phases.sh` and `scripts/powershell/resolve-phases.ps1` are thin wrappers over the same Python, matching Spec Kit's `scripts.sh` / `scripts.ps` command convention.

## Agent-neutral

The extension ships no dependency on any specific AI agent, model, or vendor tooling — it drives only stock `/speckit.*` commands (or their skills-mode equivalents `speckit-plan`, `speckit-tasks`, …). It works in any Spec Kit-initialized project regardless of which of the 30+ supported agents you use.

## Layout

```
pipeline/
├── extension.yml            # manifest
├── commands/
│   ├── run.md               # the orchestrator command
│   └── preview.md           # dry-run phase-plan printer
├── scripts/
│   ├── phase_registry.py    # deterministic resolver core (pure, no I/O)
│   ├── resolve_phases.py    # CLI over the resolver (exit codes 10–14)
│   ├── bash/resolve-phases.sh
│   └── powershell/resolve-phases.ps1
├── config-template.yml      # optional per-project defaults
├── tests/test_phase_registry.py   # stdlib unittest — determinism + exit codes
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## Install

Until it is listed in the community catalog, install by copying `pipeline/` into your project's Spec Kit extensions location (or your fork's `extensions/pipeline/`) so the two commands register on init. See the catalog submission notes in the parent directory's contribution guide.

## Tests

```
cd pipeline
python3 -m unittest discover -s tests -p 'test_*.py'
```

## License

MIT — see [LICENSE](LICENSE).

## Provenance

Ported from the `speckit-pipeline` orchestration skill (formerly `speckit-workflow`), decoupled from its origin repo's internal tooling into a portable, agent-neutral Spec Kit extension.
