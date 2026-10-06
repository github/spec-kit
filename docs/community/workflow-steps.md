# Community Workflow Step Types

> [!NOTE]
> Community workflow step types are independently created and maintained by
> their authors. Maintainers verify submission metadata and package shape; they
> do **not review, audit, endorse, or support the executable Python code**.
> Installing a custom step imports and runs that code with the user's
> privileges. Review the source before installing it.

Custom workflow step packages add a `type:` that workflows can use beyond the
built-in step types. The canonical intake path is the
[Workflow Step Type Submission](https://github.com/github/spec-kit/issues/new?template=workflow_step_submission.yml)
issue form.

This is currently an **intake-only** process. Opening the form applies only the
`triage-must-have` verdict. It does not trigger catalog validation, create a
branch, or open a draft pull request. Maintainers review submissions manually
and, when accepted, update
[`workflows/step-catalog.community.json`](https://github.com/github/spec-kit/blob/main/workflows/step-catalog.community.json)
through the normal reviewed pull request process.

The built-in community catalog is **discovery-only**. Accepted entries can
appear in `specify workflow step search` and `info`, but
`specify workflow step add <id>` will not install executable code from that
source. After reviewing the source, install the submitted immutable archive
directly with `--from`, or use a separately configured step catalog that you
explicitly allow for installation.

## Package Contract

One installed package provides one workflow step type:

```text
my-step/
├── step.yml
├── __init__.py
└── helpers.py     # optional; every catalog-downloaded extra file is declared
```

The package must satisfy the current installer and loader contract:

- `step.yml` and `__init__.py` are regular, non-symlink files at the package
  root. An archive may wrap the package in exactly one top-level directory.
- `step.type_key`, the catalog key/ID, and the matching
  `StepBase.type_key` are identical.
- The ID is one safe path component. The installer rejects separators, leading
  dots, trailing dots or spaces, reserved names, control characters, and
  Windows-invalid filename characters.
- `__init__.py` defines a `StepBase` subclass matching that single type key.
  Additional classes do not make the package provide additional registered
  step types.
- The package stays within the current installer limits: 512 retained entries,
  32 directory levels, and 50 MiB of retained content.
- `.git`, `__pycache__`, and `.DS_Store` are excluded from installation.

See [Custom step packages](../reference/workflows.md#custom-step-packages) for
the complete install, validation, and runtime behavior.

## Submission Contract

The issue form separates fields consumed by the current package/catalog code
from provenance and disclosure fields used during manual review.

| Submission data | Current contract |
| --- | --- |
| Step type ID | Catalog key, `step.type_key`, and matching `StepBase.type_key` |
| Name, version, description, author | `step.yml` metadata and catalog/installed registry metadata |
| Release artifact URL | Immutable archive used to test the supported direct-URL installation path |
| `step.yml`, `__init__.py`, and extra-file URLs | Exact HTTPS file URLs consumed when installing from an explicitly install-allowed catalog |
| Per-file SHA-256 mapping | Catalog `sha256`; keys must be exactly the files the installer downloads |
| Provided type name/count | Loader invariant: one matching type key per installed package |
| Repository, license, documentation, changelog | Source provenance and manual-review evidence; these are not `step.yml` fields |
| Spec Kit compatibility | Required intake disclosure; the step catalog accepts a `requires` mapping but does not yet define or enforce a Spec Kit compatibility schema |
| Runtime and tool dependencies | Required intake disclosure; the CLI does not resolve or install dependencies for custom steps |

Use tag-pinned URLs for the release artifact, documentation, and every catalog
file. Do not submit branch URLs, `releases/latest` URLs, or other moving
targets. Exact-release installation from an install-allowed catalog requires a
valid release version and a 64-character hexadecimal SHA-256 digest for
`step.yml`, `__init__.py`, and every `extra_files` path.

## Prepare a Submission

1. Create a public source repository with the complete package, license,
   documentation, and changelog where applicable.
2. Test valid and invalid configuration, `StepStatus`, outputs, errors, and any
   relevant resume, nested-step, or concurrent execution behavior.
3. Publish an immutable versioned archive (`.zip`, `.tar.gz`, or `.tgz`) and
   test it:

   ```bash
   specify workflow step add my-step \
     --from https://github.com/your-org/my-step/releases/download/v1.0.0/my-step-1.0.0.zip
   ```

4. Publish tag-pinned HTTPS URLs for `step.yml`, `__init__.py`, and every extra
   package file. Compute the SHA-256 digest of each downloaded file.
5. File the canonical submission issue with the exact release metadata and
   test evidence.

## Current Review Scope

Maintainers currently check the form manually for:

- complete identity, release, repository, license, and documentation metadata;
- consistency between the package ID, manifest type key, provided class, and
  version;
- immutable release and file URLs;
- complete per-file checksum and extra-file mappings;
- disclosed compatibility and runtime dependencies; and
- evidence that the released archive follows the supported package shape and
  installation path.

There is no workflow-step submission validator or draft-PR generator in this
phase. A future automation phase will need a canonical step catalog entry
schema, including defined compatibility and dependency shapes, before all
submission fields can be machine-validated rather than reviewed as text.
