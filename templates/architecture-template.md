# System architecture

**Revision**: [revision] | **Inputs**: [spec paths and constitution version]

## Scope and constraints

[System responsibilities from approved requirements; no new product features.]

## Components and technologies

Keep stable component IDs in this single canonical JSON inventory.

```json
{
  "schema_version": 1,
  "components": [
    {"id": "API", "responsibility": "[responsibility]", "technologies": ["[language/framework/database versions]"]}
  ]
}
```

## Interfaces and communication

| Interface ID | Producer | Consumer | Protocol and format | Authentication | Failure and retry semantics |
|---|---|---|---|---|---|
| [IF-001] | [component] | [component] | [choice] | [boundary] | [behavior] |

## Placement constraints

[Required co-location or separation and reasons. Capability constraints such as
an interactive desktop are permitted; specific OS, server counts and resources
belong to environment.md.]

## Decisions and alternatives

[Investigated standard solutions, compatibility, justified complexity, source
references and dates. Record assumptions explicitly.]

## Change impact

[Prior revision, changed decisions, affected features/components and which
environment/plan/task artifacts require review. Preserve approved decisions
unless this command was invoked to revise them.]
