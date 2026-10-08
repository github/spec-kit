# Community Workflow Steps

> [!NOTE]
> Community step types are independently maintained by their authors. Maintainers
> check submission metadata and distribution evidence only; they do **not review,
> audit, endorse, or support submitted code**. Users must vet step source before
> installation or execution. Loading a custom step imports executable Python.

Accepted entries are published in
[`workflows/step-catalog.community.json`](https://github.com/github/spec-kit/blob/main/workflows/step-catalog.community.json).
The built-in community catalog is **discovery-only**: use
`specify workflow step search` and `specify workflow step info <id>` to inspect
entries, not to establish trust. Install a vetted package from a direct archive
or local directory; installation by catalog ID requires an explicitly registered
install-allowed catalog.

| Step | Type | Purpose | URL |
|------|------|---------|-----|

## Submit a step type

Open a [Workflow Step Submission](https://github.com/github/spec-kit/issues/new?template=workflow_step_submission.yml)
issue for a new entry, version update, or metadata correction. A maintainer
applies `workflow-step-submission` during triage. The agent checks metadata,
published file availability and digests, documentation, and author testing
attestations, then proposes catalog/docs changes in a draft PR for maintainer
review. It does not install, import, execute, or audit your step.

Your package must contain `step.yml` and `__init__.py`, with `step.type_key`
matching the submitted ID. IDs must also pass the CLI's cross-platform path
validation; Windows device names such as `con`, `aux`, `com1`, and `lpt1` are
not allowed. Publish a GitHub release with a tag matching version
`X.Y.Z` (for example `v1.0.0` or `deploy-preview-v1.0.0`; no slashes in the tag).
Catalog installs download individual files, not archives. List all runtime files
using raw GitHub URLs pinned to that exact tag and a SHA-256 digest for each:

```json
{
  "deploy-preview": {
    "id": "deploy-preview",
    "name": "Deploy Preview",
    "version": "1.0.0",
    "description": "Deploy a preview environment",
    "author": "Example",
    "repository": "https://github.com/example/deploy-preview",
    "documentation": "https://github.com/example/deploy-preview/blob/v1.0.0/README.md",
    "license": "MIT",
    "requires": {"speckit_version": ">=0.11.0"},
    "step_yml_url": "https://raw.githubusercontent.com/example/deploy-preview/v1.0.0/step.yml",
    "init_url": "https://raw.githubusercontent.com/example/deploy-preview/v1.0.0/__init__.py",
    "extra_files": {
      "helpers.py": "https://raw.githubusercontent.com/example/deploy-preview/v1.0.0/helpers.py"
    },
    "sha256": {
      "step.yml": "<64 hex digits for step.yml>",
      "__init__.py": "<64 hex digits for __init__.py>",
      "helpers.py": "<64 hex digits for helpers.py>"
    },
    "tags": ["deployment", "preview"],
    "verified": false
  }
}
```

Replace the example metadata and digest placeholders with actual values.
Omit `extra_files` when no additional package files are needed. All file URLs
must belong to the submitted repository, tag, and package directory.
File paths must not alias one another or conflict with package directories
when compared case-insensitively, including on Windows.
Packages must fit the CLI's limits: 512 entries (files and distinct package
directories combined), 32 directory levels, and 50 MiB total. Submission
downloads also have a 10 MiB per-file limit. Validation downloads the complete
declared package in one pass to enforce the cumulative byte budget.

Include an open source license and a step-scoped README documenting dependencies,
credentials, setup, configuration, installation, and workflow YAML using your
step type. Test installation in a clean project and record successful execution
and an invalid-input or failure case, along with the Spec Kit version tested.

For example, after vetting the source:

```bash
specify workflow step add deploy-preview --from https://github.com/example/deploy-preview/archive/refs/tags/v1.0.0.zip
```

An archive must contain `step.yml` and `__init__.py` at its root or under exactly
one top-level directory. A bare `step.yml` URL cannot be used with `--from`.
For package authoring and catalog release history, see
[Custom step packages](../reference/workflows.md#custom-step-packages) and
[Workflow Step Design](https://github.com/github/spec-kit/blob/main/design/workflow-step.md).

New versions preserve existing release history. Same-version metadata repairs
must be identified explicitly and cannot replace file URLs or digests; publish
a new version when package content changes.
