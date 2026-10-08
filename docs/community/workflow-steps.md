# Community Workflow Step Types

> [!NOTE]
> Community workflow step types are independently created and maintained by
> their authors. Maintainers verify submission metadata and package shape; they
> do **not review, audit, endorse, or support the executable Python code**.
> Installation validates and copies the package without importing its Python
> code. Later `specify workflow add`, `run`, and `resume` commands load installed
> step packages, executing import-time code with the user's privileges. Review
> the source before installation and use.

Custom workflow step packages add a `type:` that workflows can use beyond the
built-in step types. The canonical intake path is the
[Workflow Step Type Submission](https://github.com/github/spec-kit/issues/new?template=workflow_step_submission.yml)
issue form for new entries, version updates, and metadata corrections.

Opening the form applies only the `triage-must-have` verdict. A maintainer
applies `workflow-step-submission` during triage to start automated metadata
validation. Successful validation proposes catalog and documentation changes
in a draft PR for maintainer review. The automation never installs, imports,
executes, or reviews submitted Python.

Accepted entries are published in
[`workflows/step-catalog.community.json`](https://github.com/github/spec-kit/blob/main/workflows/step-catalog.community.json).
The built-in community catalog is **discovery-only**. Accepted entries can
appear in `specify workflow step search` and `info`, but
`specify workflow step add <id>` will not install executable code from that
source. After reviewing the source, install the submitted versioned archive
directly with `--from`, or use a separately configured step catalog that you
explicitly allow for installation.

## Available Step Types

| Step type | Version | Description |
| --- | --- | --- |
| [Decision](https://github.com/markuswondrak/spec-kit-decision-step) (`decision`) | 0.9.0 | Typed bounded choice, score, and noul decisions with native probabilities and score legends using Jev and Laya backends. |

Decision is maintained by [Markus Wondrak](https://github.com/markuswondrak).
As in the other community submission tables, author metadata belongs in the
catalog; it is not used as a substitute for maintainer attribution.

Decision declares runtime compatibility with Spec Kit `>=0.11.0`; installing
its [versioned release archive](https://github.com/markuswondrak/spec-kit-decision-step/releases/download/v0.9.0/decision-0.9.0.zip)
with `--from` requires Spec Kit `>=1.1.0`. The catalog compatibility field is
advisory and is not enforced by the current step installer.

The package uses the host's PyYAML and `specify_cli` packages. Jev requires
`TYPESAFE_API_KEY` (or a configured `api_key_env`) and outbound HTTPS to the
configured backend endpoint; in-process Laya requires the optional
`laya[onnx]` package. See the
[version-pinned documentation](https://github.com/markuswondrak/spec-kit-decision-step/blob/v0.9.0/README.md)
for configuration, outputs, failure behavior, and side effects, and the
[changelog](https://github.com/markuswondrak/spec-kit-decision-step/blob/v0.9.0/CHANGELOG.md)
for release details. The MIT-licensed manifest credits
`spec-kit-decision-step contributors` as the package author.

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
  Windows-invalid filename characters. Catalog automation additionally requires
  lowercase letters, digits, and hyphens, starting with a letter.
- `__init__.py` defines a `StepBase` subclass matching that single type key.
  Additional classes do not make the package provide additional registered
  step types. This is an author attestation, not a maintainer code check.
- Extra-file paths use forward slashes, are relative and non-empty, contain no
  empty, `.` or `..` segments, and do not case-insensitively alias `step.yml`,
  `__init__.py`, another file, or a package directory.
- The package stays within the current installer limits: 512 retained entries
  (files and directories combined), 32 directory levels, and 50 MiB of retained
  content. Submission downloads additionally have a 10 MiB per-file limit.
- `.git`, `__pycache__`, and `.DS_Store` are excluded from installation;
  submission automation rejects case-insensitive aliases of these components.

See [Custom step packages](../reference/workflows.md#custom-step-packages) for
the complete install, validation, and runtime behavior.

## Submission Contract

The issue form separates fields consumed by the current package/catalog code
from provenance and disclosure fields used during metadata review.

| Submission data | Current contract |
| --- | --- |
| Step type ID | Catalog key, `step.type_key`, and matching `StepBase.type_key` |
| Name, version, description, author | `step.yml` metadata and catalog/installed registry metadata |
| Download URL | Versioned release archive used to test the supported direct-URL installation path |
| `step.yml`, `__init__.py`, and extra-file URLs | Exact HTTPS file URLs consumed when installing from an explicitly install-allowed catalog; extra-file keys follow the package-relative path restrictions above |
| Per-file SHA-256 mapping | Catalog `sha256`; keys must be exactly the files the installer downloads |
| Provided type name/count | Loader invariant: one matching type key per installed package |
| Repository, license, documentation, changelog | Source provenance and metadata-review evidence; these are not `step.yml` fields |
| Spec Kit compatibility | Required intake disclosure; stored as advisory `requires.speckit_version`, not enforced by the installer |
| Runtime and tool dependencies | Required intake disclosure; the CLI does not resolve or install dependencies for custom steps |

Use a versioned GitHub release URL for the archive, consistent with the other
community submission forms. Versions must be PEP 440-compatible and match the
manifest. The archive's release tag must identify that version, optionally
with a `v` prefix or a scoped prefix, and must contain no slashes.
Epoch versions such as `1!2.0` and local versions such as `2.0+cpu` are
supported. Tag characters must match `^[A-Za-z0-9._~+!-]+$`.
All catalog file URLs must use `raw.githubusercontent.com` in the submitted
repository, pinned to that exact release tag and package directory. The
required per-file SHA-256 mapping detects changed bytes even if a referenced
tag is later moved. Do not submit branch URLs, `releases/latest` URLs, or other
floating targets.

The archive URL path must match `^[A-Za-z0-9._~+!/-]+$`. Package-relative
file keys and file paths within the tag must match `^[A-Za-z0-9._~/-]+$`.
Spaces, percent escapes (including `%20` in asset names), query strings,
fragments, and empty/dot/traversal file-path segments are not accepted by
community submission automation. Publish archives and package files with
names in these alphabets rather than URL-encoding unsupported characters.

GitHub-generated `archive/refs/tags/<tag>` archives support `.zip` and `.tar.gz`
only. A `.tgz` archive must be a named `releases/download/<tag>/<asset>.tgz`
release asset, not a generated tag archive.

Documentation may be any tag-pinned Markdown file (`.md`, case-insensitive)
in the submitted GitHub repository, including `docs/deploy.md`; it need not be
named `README.md`. It must explain installation, configuration, dependencies,
outputs, failure behavior, side effects, and example workflow usage.

The direct `--from` archive installer does not currently accept or verify an
archive digest. The submitted Download URL and Testing Details fields provide
versioned-release and installation-test evidence, not an immutable content
guarantee; the per-file digests protect the separate catalog-installation path.
Automation downloads the complete declared file set in one pass to enforce
the cumulative byte budget. It does not execute the archive or its contents.

License must be one exact SPDX license identifier from the official license
list, matching the repository license detected at the submitted release tag.
An unknown identifier or known license mismatch fails validation. If release
license detection is unavailable or inconclusive, validation is Blocked for
maintainer clarification rather than guessing a license. This metadata check
is not a legal opinion or code audit.

## Prepare a Submission

1. Create a public source repository with the complete package, license,
   documentation, and changelog where applicable.
2. Test valid and invalid configuration, `StepStatus`, outputs, errors, and any
   relevant resume, nested-step, or concurrent execution behavior.
3. Publish a versioned release archive (`.zip`, `.tar.gz`, or a named `.tgz`
   release asset) and test it:

   ```bash
   specify workflow step add my-step \
     --from https://github.com/your-org/my-step/releases/download/v1.0.0/my-step-1.0.0.zip
   ```

4. Publish tag-pinned raw GitHub URLs for `step.yml`, `__init__.py`, and every
   extra package file. Compute the SHA-256 digest of each downloaded file.
5. File the canonical submission issue with the exact release metadata and
   test evidence.

## Automated Metadata Validation

The maintainer-triggered workflow checks complete metadata, matching manifest
identity, pinned release/file URLs, per-file digests, package paths and limits,
documentation, and author testing attestations. It does not review submitted
code or claim to verify its execution behavior.

Confirmed submission defects produce `validation-failed` and actionable
corrections. Environment failures, including permissions, unavailable tools,
timeouts, and transient HTTP failures, are Blocked rather than submission
defects. Only the guarded conclusion job can apply `validation-passed`, after
successful publication of the draft catalog PR.

New versions preserve existing catalog release history. Same-version metadata
repairs must be identified explicitly and cannot replace file URLs or digests;
publish a new version when package content changes.
The repository-owned verifier snapshots the expected catalog before edits and
checks the complete generated catalog before PR creation, including migration
of the previous current release and preservation of history. Missing existing
release digests block publication pending maintainer repair.
