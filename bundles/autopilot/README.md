# Autopilot Bundle

A first-party Spec Kit bundle for autonomous spec-driven development, driven from your agent's chat.

## What it provides

- **Autopilot extension** (`extensions/autopilot`): `/speckit.autopilot.setup`, `/speckit.autopilot.run`, `/speckit.autopilot.status` and `/speckit.autopilot.recover`. Also the internal `epics` and `review` commands and the deterministic engine (`scripts/python/autopilot.py`).
- **autopilot-epic workflow**: the headless pipe for one epic. `specify → plan → tasks`, then `implement → converge → gate → review` until the gate passes or a cap is hit.
- **autopilot workflow**: the same conductor for CI and terminals, with verdict inputs for both gates.

## Install

```bash
specify init --here --force --integration claude --extension autopilot
```

For a project that is already initialized, ask your agent to run `specify extension add autopilot`. `/speckit.autopilot.setup` then installs the two workflows.

`specify bundle install autopilot` fetches this manifest from the catalog's `download_url`, which only resolves once `bundles/autopilot/bundle.yml` is published at that URL.

## Run

In your agent's chat:

```text
/speckit.autopilot.setup
/speckit.autopilot.run requirements=docs/requirements
```

See [Autopilot (autonomous SDD)](../../docs/reference/agentic-autopilot.md) for the gate, controls, recovery and headless use.
