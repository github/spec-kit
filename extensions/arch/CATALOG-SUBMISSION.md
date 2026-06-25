# Spec Kit Extension Submission

Extension ID: arch
Name: Architecture Workflow
Version: 1.2.2
Description: Generate or reverse project-level 4+1 architecture views with per-view and full-workflow commands
Author: bigsmartben
Repository URL: https://github.com/bigsmartben/spec-kit-arch
Download URL: https://github.com/bigsmartben/spec-kit-arch/archive/refs/tags/v1.2.2.zip
Documentation URL: https://github.com/bigsmartben/spec-kit-arch#readme
License: MIT
Required Spec Kit version: >=0.8.10.dev0
Commands count: 12
Hooks count: 0
Tags: architecture, 4plus1, workflow, design

Key features:
- Provides `.arch` namespaced commands for each 4+1 view: scenario, logical, process, development, and physical.
- Provides `/speckit.arch.full-generate` for one-command forward generation of all 4+1 views and synthesis.
- Provides `/speckit.arch.full-reverse` for one-command reverse generation of repo facts, all 4+1 views, and synthesis.
- Provides separate forward-generation and reverse-generation commands for every view.
- Records reverse workflow evidence in `.specify/memory/architecture-repo-facts.md`.
- Uses optional repository-first evidence in the reverse workflow, with dependency matrix interpretation owned by the development view rather than consumed evenly by every 4+1 view.
- Requires the Development View commands to produce a `Dependency Matrix` section in the development-view artifact.
- Allows teams to update one architecture view at a time while preserving the cross-view synthesis boundary.
- Defines synthesis readiness, repo-facts merge behavior, and source traceability expectations for repeatable command runs.
- Ships a schema-backed artifact contract plus bash and PowerShell readiness validators that emit `ready_gate` and stable blocker codes.
- Restricts writes to documented `.specify/memory/architecture*.md` files, including repo facts for reverse generation.

Testing performed:
- Local development install with `specify extension add --dev /home/administrator/github/spec-kit-arch`.
- Bash setup helper verified with `.specify/extensions/arch/scripts/bash/setup-arch.sh --json`.
- Release ZIP install to verify after publishing `v1.2.2`: `specify extension add arch --from https://github.com/bigsmartben/spec-kit-arch/archive/refs/tags/v1.2.2.zip`.
