#!/usr/bin/env bash
set -euo pipefail

rg -n "Repository-First Inputs" commands/speckit.arch.reverse.md >/dev/null
rg -n "repository-first/technical-dependency-matrix.md" commands/speckit.arch.reverse.md >/dev/null
rg -n "Repository-First Projection" templates/architecture-repo-facts-template.md >/dev/null
rg -n "Module Invocation Governance" templates/architecture-repo-facts-template.md >/dev/null
rg -n "Dependency Governance Signals" templates/architecture-repo-facts-template.md >/dev/null
rg -n "must not be copied verbatim into 4\\+1 views|must not be copied verbatim into architecture views" commands/speckit.arch.reverse.md >/dev/null
rg -n "repository-first" README.md CHANGELOG.md CATALOG-SUBMISSION.md >/dev/null
