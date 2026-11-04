# Community Workflows

Community workflows compose Spec Kit steps into independently maintained,
repeatable processes.

> [!NOTE]
> Maintainers check catalog entry form and completeness, not workflow code,
> scripts, or dependencies. A listing is not an audit, endorsement, or support
> commitment. Review source, required integrations, side effects, and review
> gates before installation and use.

## Available workflows

Entries in the [community workflow catalog](https://github.com/github/spec-kit/blob/main/workflows/catalog.community.json):

| Workflow | Version | Description |
| --- | --- | --- |
| [Guided SDD Pipeline](https://github.com/domattioli/spec-kit-workflow-pipeline) (`pipeline`) | 1.1.0 | Chains specify, clarify, plan, tasks, analyze, implement, and converge, with a clarify gate and post-implementation convergence loop |
| [Full SDD Cycle - no gates](https://github.com/clintcparker/speckit-addons/tree/yolo-v0.1.0/workflows/yolo) (`yolo`) | 0.1.0 | Runs specify, plan, tasks, and implement without review gates |

These are community definitions, distinct from the workflows bundled with Spec
Kit. Inspect active sources and advertised releases:

```bash
specify workflow catalog list
specify workflow search
specify workflow info <id> --versions
```

Search uses all active workflow catalogs. The built-in community source is
discovery-only: a listing does not make `specify workflow add <id>` installable
through that source. After vetting a release, install its pinned URL explicitly
or use a separately configured catalog you trust and allow for installation.

## Contribute a workflow

Publish a versioned workflow definition or complete package and submit a focused
PR editing `workflows/catalog.community.json`. Include release metadata,
documentation, required integrations and side effects, and end-to-end testing
evidence, including applicable gate and resume behavior.

Workflow definitions do not use a submission issue form. The Workflow Step Type
Submission form is for executable custom step packages, not workflows. The
publishing guide owns the catalog entry format and release-update procedure.

## See also

- [Workflow overview and bundled definitions](../workflows/overview.md)
- [Workflow management CLI](../workflows/cli.md)
- [Developing workflows](../workflows/developing.md)
- [Publishing and submitting workflows](../workflows/publishing.md)
- [Workflow catalogs](../workflows/catalogs.md)
- [Community workflow step types](workflow-steps.md)
