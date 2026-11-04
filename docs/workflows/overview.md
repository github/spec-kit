# Workflows

Workflows automate multi-step Spec Kit processes through YAML definitions.
They chain agent commands, prompts, shell tasks, control flow, and human review
gates into repeatable, resumable runs. They are distinct from the processes
you follow manually with `/speckit.*` commands and from GitHub Actions workflows.

## Before you start

Install the [Specify CLI](../installation.md) and initialize your project with
an [agent integration](../integrations/index.md). Agent command and prompt
steps require an integration capable of CLI execution. Shell-only local YAML
workflows can run outside an initialized project.

Review a workflow's source before installation and use, including companion
scripts, called workflows, custom step packages, and active overlays. Catalog
listing and install permission are not evidence of code review or safety.

## Run, review, and resume

```bash
specify workflow search
specify workflow add speckit
specify workflow run speckit --input spec="Build a kanban board"
```

The bundled SDD workflow runs specify, plan, tasks, and implement, with review
gates after specification and planning. On an interactive terminal a gate asks
for a verdict; otherwise it pauses. Review the output and resume the same run:

```bash
specify workflow status <run_id>
specify workflow resume <run_id>
```

Each run gets its own ID and state directory. Completed occurrences are replayed
into the expression context without re-executing their implementations.
Unfinished work continues from its persisted state; a side effect interrupted
before its completion checkpoint may still repeat.

You can also run a local definition without installing it:

```bash
specify workflow run ./workflow.yml --input spec="Build a kanban board"
```

## Bundled workflows

| ID | Purpose | Main input |
| --- | --- | --- |
| `speckit` | Full SDD delivery cycle with specification and plan review gates | `spec` |
| `bugfix` | Bug assessment, fixing, and validation | `report` |
| `assess` | Idea intake, research, definition, shaping, and decision | `idea` |

Use `specify workflow info <id>` for metadata, inputs, and the step graph.
The `speckit` workflow declares `spec` and optional `integration`, not a `scope`
input. Workflows using extension commands also need those commands installed;
consult each bundled definition's requirements.

## Customize a workflow

Author a definition for a new automation process, call another installed
workflow through a `workflow` step, or use overlays to customize an installed
workflow without editing its package. An overlay can fill a named slot or
insert, replace, and remove steps; it cannot change the base input schema.

## FAQ

### Can I run the same workflow multiple times?

Yes. Runs have independent IDs and persisted state. `specify workflow status`
lists runs; supplying a run ID shows its status.

### What happens at a review gate?

A declared verdict input can decide the gate without a prompt. Otherwise a
gate prompts on a TTY or pauses for resume. Rejection can abort, skip, or pause
for retry, according to its configuration.

### Who maintains workflows?

Most workflows are independently maintained by their authors. Maintainers
check community catalog entries for form and completeness, not workflow code.
They do not review, audit, endorse, or support that code. Users must vet source
before installation and use.

## See also

- [Workflow CLI](cli.md)
- [Developing workflows](developing.md)
- [Built-in step types](steps.md)
- [Workflow overlays](overlays.md)
- [Catalogs and trust](catalogs.md)
- [Publishing workflows](publishing.md)
