# Specify Terminal Bench Agent

This package provides Terminal Bench agents that drive the Spec -> Plan -> Tasks
workflow using the exact prompts and templates that ship with the Specify CLI. The
agents run outside the end-user CLI so benchmarking dependencies stay isolated.

## Project layout

```
benchmarks/
  terminal_bench_agent/
    pyproject.toml         # standalone uv project for benchmarking-only deps
    README.md              # this guide
    specify_terminal_bench/
      __init__.py          # package export
      agent.py             # workflow-aware agent definitions
      prompt_templates/    # legacy prompt assets (unused by the new mixin)
```

## Getting started

1. Create an isolated environment for the benchmarking tools:
   ```bash
   cd benchmarks/terminal_bench_agent
   uv sync
   ```
2. (Optional) Export credentials for paid providers if you plan to use them
   (e.g. `ANTHROPIC_API_KEY` for Claude Code).
3. Run Terminal Bench with the OpenCode workflow agent and the public core dataset:
   ```bash
   uv run tb run \
     --dataset terminal-bench-core==head \
     --task-id hello-world \
     --agent-import-path specify_terminal_bench.agent:SpecifyOpenCodeWorkflowAgent
   ```
   This defaults to the free `opencode/grok-code-fast-1` model. Provide
   `--agent-kwarg model_name=<provider/model>` if you want another OpenCode target.
4. To benchmark with Claude Code instead, switch the import path:
   ```bash
   uv run tb run \
     --dataset terminal-bench-core==head \
     --task-id hello-world \
     --agent-import-path specify_terminal_bench.agent:SpecifyClaudeWorkflowAgent \
     --agent-kwarg model_name=anthropic/claude-3-5-sonnet-20241022
   ```

## Customisation

- The agents assemble their prompts at runtime from the real Specify CLI sources:
  `templates/commands/specify.md`, `plan.md`, `tasks.md` and their corresponding
  templates. Update those files in the main repository to change benchmarking
  behaviour.
- Pass additional keyword arguments through `--agent-kwarg` to reach provider specific
  options (e.g. `version=...`).
- If you need a different provider entirely, subclass the desired Terminal Bench agent
  under `specify_terminal_bench/agent.py` and reuse `SpecifyWorkflowMixin`.

## Tips

- Terminal Bench requires Python 3.12+. The dedicated project keeps this dependency
  separate from the end-user CLI which still targets Python 3.11.
- The agents read prompt assets from the repository root, so run benchmarks from the
  root checkout.
- `uv run tb --help` lists additional switches (filtering tasks, resuming runs, etc.).
