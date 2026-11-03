# Workflows

This directory contains bundled workflow definitions and discovery catalogs.
The canonical user, authoring, CLI, and API documentation is published in
the [workflow documentation](https://github.github.io/spec-kit/workflows/overview.html).

## Directory contents

| Path | Purpose |
| --- | --- |
| `speckit/workflow.yml` | Full SDD delivery cycle |
| `bugfix/workflow.yml` | Bug assessment, fixing, and validation |
| `assess/workflow.yml` | Idea assessment process |
| `catalog.json` | First-party workflow catalog |
| `catalog.community.json` | Community workflow catalog |
| `step-catalog.json` | First-party custom-step catalog |
| `step-catalog.community.json` | Community custom-step catalog |

Community catalogs are discovery channels, not code-review or safety
endorsements. Users must vet workflow definitions, referenced scripts,
custom step packages, and overlays before installation and use.

## See also

- [Workflow CLI](https://github.github.io/spec-kit/workflows/cli.html)
- [Developing workflows](https://github.github.io/spec-kit/workflows/developing.html)
- [Workflow API](https://github.github.io/spec-kit/workflows/api.html)
- [Workflow and step catalogs](https://github.github.io/spec-kit/workflows/catalogs.html)
- [Publishing workflows](https://github.github.io/spec-kit/workflows/publishing.html)
