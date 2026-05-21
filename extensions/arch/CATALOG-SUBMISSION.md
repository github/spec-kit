# Spec Kit Extension Submission

Extension ID: arch
Name: Architecture Workflow
Version: 1.1.0
Description: Generate or reverse project-level 4+1 architecture view artifacts and synthesis
Author: bigsmartben
Repository URL: https://github.com/bigsmartben/spec-kit-arch
Download URL: https://github.com/bigsmartben/spec-kit-arch/archive/refs/tags/v1.1.0.zip
Documentation URL: https://github.com/bigsmartben/spec-kit-arch#readme
License: MIT
Required Spec Kit version: >=0.8.10.dev0
Commands count: 2
Hooks count: 0
Tags: architecture, 4plus1, workflow, design

Key features:
- Generates or refreshes six architecture memory artifacts.
- Provides `/speckit.arch.reverse` for evidence-backed architecture reconstruction from ordinary historical repositories.
- Records reverse workflow evidence in `.specify/memory/architecture-repo-facts.md`.
- Consumes optional repository-first dependency matrices and module invocation specs as reverse workflow evidence.
- Guides scenario, logical, process, development, physical, and synthesis views.
- Restricts writes to documented `.specify/memory/architecture*.md` files, including repo facts for reverse generation.

Testing performed:
- Local development install with `specify extension add --dev /home/administrator/github/spec-kit-arch`.
- Bash setup helper verified with `.specify/extensions/arch/scripts/bash/setup-arch.sh --json`.
- Release ZIP install to verify after publishing `v1.1.0`: `specify extension add arch --from https://github.com/bigsmartben/spec-kit-arch/archive/refs/tags/v1.1.0.zip`.
