# Specify Terminal Bench Agent

This package contains a Terminal Bench agent that wraps the stock Claude Code runner
with the Specify spec -> plan -> tasks workflow. It allows you to benchmark the
prompt set that ships with the Specify CLI without bundling the benchmarking tooling
into the end-user package.

## Project layout

```
benchmarks/
  terminal_bench_agent/
    pyproject.toml         # standalone uv project for benchmarking-only deps
    README.md              # this guide
    specify_terminal_bench/
      agent.py             # SpecifyClaudeWorkflowAgent definition
      __init__.py          # package export
      prompt_templates/
        specify_workflow.j2  # Spec->Plan->Tasks instruction template
```

## Getting started

1. Create an isolated environment for the benchmarking tools:
   ```bash
   cd benchmarks/terminal_bench_agent
   uv sync
   ```
2. Export the credentials required by your target CLI agent (for Claude Code this is
   `ANTHROPIC_API_KEY`; optionally set `ANTHROPIC_MODEL`).
3. Run Terminal Bench with the Specify workflow agent:
   ```bash
   uv run tb run \
     --task-id hello-world \
     --agent-import-path specify_terminal_bench.agent:SpecifyClaudeWorkflowAgent \
     --agent-kwarg model_name=anthropic/claude-3-5-sonnet-20241022
   ```
   Replace the model with any Claude Code release supported in your account.

## Customisation

- The prompt template lives at
  `specify_terminal_bench/prompt_templates/specify_workflow.j2`. Modify this file to
  tweak the stage instructions or add additional guardrails.
- Runtime keyword arguments passed via `--agent-kwarg` are forwarded to the underlying
  `ClaudeCodeAgent`. For example you can select a different model or version.
- To experiment with other Terminal Bench agents (e.g. Codex, Cursor) you can subclass
  their installed-agent wrappers and point them at the same prompt template.

## Tips

- Terminal Bench requires Python 3.12+. The dedicated project keeps this dependency
  separate from the end-user CLI which still targets Python 3.11.
- The agent expects to run from the repository root so that the prompt template can
  locate constitution files and other assets via relative paths.
- `uv run tb --help` lists the available subcommands, including utilities for listing
  tasks and resuming interrupted runs.
