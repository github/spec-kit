---
description: "Generate the active project-governance projection"
---

# Project Governance Projection Generation

## Input

$ARGUMENTS

## Output

- Active agent platform target.
- Generated `PROJECT GOVERNANCE` projection file.

## Procedure

1. Require `.specify/`.
2. Resolve the active agent platform target:
   - `.specify/init-options.json` `context_file` when it is a safe relative agent/rules/instructions context path
   - `.specify/integration.json` `default_integration` or `integration`
   - default context target from `CONTEXT_FILES`
3. Generate or overwrite the active agent platform target.
4. Distill detected repository areas into action rules.
   - depth: 2
   - include hidden and cache directories
5. Capture repository facts from the current repository state as vertical SSOT evidence.
   - Architecture evidence
   - Engineering evidence
   - Code Style evidence
   - Directory Structure evidence
   - Agent Harness evidence
   - README, project docs, repository policy, and Spec Kit metadata
   - extension assets, command/template governance contracts, manifests, lockfiles, task runners, build config, and runtime config
   - feature specs, API contracts, source paths, and test paths
   - development commands from package scripts or Python/uv test conventions
6. Resolve the Spec Kit Agent Adapter for the active integration.
   - active agent platform target
   - repository-local skill discovery behavior
   - MCP runtime discovery behavior
   - repository MCP config candidates as evidence only
7. Project the scenario capability index.
    - repository-local skill capabilities from `SKILL.md` name, description, trigger, and source path
    - MCP-backed external tool capability with runtime enumeration before use
8. Run:

   ```bash
   uv run python .specify/extensions/repository-governance/scripts/generate_repository_governance.py
   ```

## Report

- active agent platform target
- generated or updated
- review target
- captured evidence from the current repository state
