# Coding tasks for [feature]

**Inputs**: [spec, architecture, environment, plan and contract revisions]

## Coding task inventory

Use exactly one fenced JSON inventory with every field below. IDs are stable;
never reuse a retired ID. Categories: code, integration, configuration (application
files only), migration (migration source only). `done_when` describes written and
integrated code, never test success, deployment or acceptance. `files` lists concrete
project-relative source paths with forward slashes. No globs, tests, deployment
scripts or governance files. `deployment_targets` contains environment asset IDs;
shared libraries list all consuming assets.

```json
{
  "schema_version": 1,
  "tasks": [
    {
      "id": "T001",
      "title": "[specific coding output]",
      "category": "code",
      "requirement_ids": ["FR-001"],
      "component": "API",
      "deployment_targets": ["APP01"],
      "depends_on": [],
      "files": ["src/api/service.py"],
      "done_when": "[complete behavior and integration implemented to named contract]"
    }
  ]
}
```

## Dependency rationale

[Real dependency edges and independent work. Group by feature/story and coding
category, not server. Shared files require serialized execution.]

## Regeneration notes

[Changes, retained/retired IDs and bug finding IDs. No tests, test tasks, deployment
tasks, documentation-only tasks or approval tasks. code-progress.json owns progress
and is reconciled by the helper, never copied into this task definition.]
