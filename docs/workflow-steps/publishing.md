# Publishing workflow steps

Publish a versioned Python package so workflows can reuse the same step type.
Custom steps use a different catalog and submission contract from workflow
definitions.

## Prepare a release

Provide a package with matching `step.type_key` and `StepBase.type_key`, a
quoted PEP 440-compatible version, an open-source license, and documentation.
Describe installation, configuration, dependencies, outputs, failure behavior,
side effects, and example workflow usage.

Test valid and invalid configuration, returned statuses, and relevant resume
and concurrent execution paths. Publish a versioned archive with `step.yml`
and `__init__.py` at the root or inside exactly one top-level directory.

After reviewing the source, test installation of the published artifact in a
disposable initialized project:

```bash
specify workflow step add my-step \
  --from https://github.com/your-org/my-step/releases/download/v1.0.0/my-step-1.0.0.zip
```

Installation validates and copies the package without importing it. Exercise
the installed type through a workflow as well: loading the package executes
Python with your privileges.

## Community submission

Follow the [Community Workflow Step Types guide](../community/workflow-steps.md)
for the canonical issue form, versioned archive, individual tag-pinned file
URLs, per-file digests, package limits, and maintainer-triggered metadata
validation.

Do not submit a hand-edited step catalog PR in place of that issue process.
Maintainers validate metadata and distribution evidence, not the submitted
Python code. The community step catalog remains discovery-only.

## Release updates

Publish a new version when package content changes, and use the same community
submission issue form for version updates and metadata corrections. Preserve
advertised historical releases. Review source again before replacing an
installed package; digest checks identify bytes, not whether those bytes are
safe.

## See also

- [Developing step packages](developing.md)
- [Python API](api.md)
- [Installation CLI](cli.md)
- [Step catalogs and releases](catalogs.md)
- [Community submission contract](../community/workflow-steps.md#submission-contract)
- [Publishing workflow definitions](../workflows/publishing.md)
