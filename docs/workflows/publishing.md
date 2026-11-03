# Publishing workflows

Publish a versioned workflow package so other projects can install the same
definition and companion files. Workflow catalog submissions and custom
workflow-step submissions use different paths; do not treat them as
interchangeable.

## Prepare a release

Before sharing a workflow, provide:

- A valid `workflow.yml` with a unique ID, descriptive name, and quoted
  `X.Y.Z` version.
- A README describing the process, inputs, step graph, required integrations,
  tools, credentials, outputs, failure behavior, and side effects.
- An open-source license and, preferably, a changelog.
- Evidence from running the workflow on a real project, including relevant
  rejection, failure, and resume paths.

Use focused steps, descriptive input prompts, meaningful review gates, and
enums for fixed choices. Explain any destructive operations, credential access,
network calls, and elevated privileges. Declared `requires` values document
expectations; they do not enforce permissions or sandbox execution.

See the authoring guide for the package layout and a complete bundled example.
Test a local definition before release:

```bash
specify workflow run ./workflow.yml --input spec="Build a kanban board"
specify workflow status <run_id>
specify workflow resume <run_id>
```

`run` validates and then executes the workflow. It is not a dry run. Test
potentially mutating examples in a disposable project.

## Package and tag

Publish from a version tag matching `workflow.version`:

```bash
git tag v1.0.0
git push origin v1.0.0
```

For a single-file workflow, a tag-pinned raw URL is sufficient:

```text
https://raw.githubusercontent.com/your-org/my-workflow/v1.0.0/workflow.yml
```

If the definition needs scripts or other resources, publish the complete
package as `.zip`, `.tar.gz`, or `.tgz`. The archive must contain `workflow.yml`
at its root or inside one top-level directory. A raw YAML download does not
include adjacent files from the repository. Reference packaged resources
through `context.workflow_dir` or `SPECKIT_WORKFLOW_DIR`.

Use pinned release URLs, not branch URLs or `releases/latest`. Compute and
publish a SHA-256 digest for downloadable content, especially when advertising
historical releases.

## Test the published artifact

After reviewing the release source, install the exact published artifact in
an initialized test project:

```bash
specify workflow add my-workflow \
  --from https://raw.githubusercontent.com/your-org/my-workflow/v1.0.0/workflow.yml
specify workflow info my-workflow
specify workflow run my-workflow --input spec="Build a kanban board"
```

For a package with companion files, substitute the versioned archive URL.
Exercise gates and resume, not just installation. `info` shows metadata,
inputs, and steps; it does not display all shell commands or prove safety.

## Submit a workflow catalog entry

Workflow entries currently use a pull request editing
[`workflows/catalog.community.json`](https://github.com/github/spec-kit/blob/main/workflows/catalog.community.json).
There is no workflow-definition submission issue form. The separate
Workflow Step Type Submission form is for executable custom step packages.

Fork the repository and add the workflow under the `workflows` mapping, sorted
alphabetically by workflow ID. For example:

```json
{
  "schema_version": "1.0",
  "workflows": {
    "my-workflow": {
      "id": "my-workflow",
      "name": "My Workflow",
      "description": "A repeatable review process",
      "author": "Example Team",
      "version": "1.0.0",
      "url": "https://raw.githubusercontent.com/your-org/my-workflow/v1.0.0/workflow.yml",
      "sha256": "<64 hexadecimal digits for the published artifact>",
      "repository": "https://github.com/your-org/my-workflow",
      "license": "MIT",
      "requires": {
        "speckit_version": ">=1.0.0"
      },
      "tags": ["review", "automation"],
      "created_at": "2026-11-03T00:00:00Z",
      "updated_at": "2026-11-03T00:00:00Z"
    }
  }
}
```

Replace the example metadata, compatibility requirement, URL, and digest with
the release's real values. Keep `requires` consistent with the definition.
The current release stays at the top level; use `releases` for historical
versions as described in the catalog reference.

Submit a focused catalog PR with:

- Workflow ID, name, version, repository, and license.
- Pinned download URL and digest.
- README and step-graph links, required integrations, and side effects.
- Installation and end-to-end testing evidence, including gate and resume behavior.

Maintainers check catalog entry form and completeness. This is **not a security review**
of workflow definitions, scripts, or dependencies. Catalog acceptance is not
an endorsement, support commitment, or evidence that code was audited.
Users must vet source before installation and use.

The community catalog is discovery-only by default. Acceptance makes the
workflow discoverable with `specify workflow search`, not automatically
installable by ID. After vetting a release, install its pinned URL explicitly
or use a separately configured catalog you trust and allow for installation.

## Publish a custom workflow step

Custom steps contain executable Python and use a different catalog and
submission contract. Follow the
[Community Workflow Step Types guide](../community/workflow-steps.md) for
the issue form, versioned archive, individual tag-pinned file URLs, per-file
digests, package limits, and maintainer-triggered metadata validation.

Do not submit a hand-edited step catalog PR in place of that issue process.
Maintainers validate metadata and distribution evidence, not the submitted
Python code. The community step catalog remains discovery-only.

## Release updates

1. Update `workflow.version`, documentation, and the changelog.
2. Test the changed definition, including applicable failure and resume paths.
3. Publish a new tag and versioned artifact; test installation from that URL.
4. Submit a catalog PR updating the current `version`, `url`, digest, and
   release-specific requirements. Preserve advertised historical releases.

Repeat source review when updating a workflow, custom step, overlay, or
referenced script. Package installation and digest verification establish
which bytes were installed, not whether those bytes are safe.

## See also

- [Developing workflows](developing.md)
- [Workflow and step catalogs](catalogs.md)
- [Installation CLI](cli.md#install-a-workflow)
- [Shell execution review](steps.md#reviewing-shell-execution)
- [Expression interpolation and shell safety](expressions.md#interpolation-and-shell-safety)
- [Community workflow step submissions](../community/workflow-steps.md)
