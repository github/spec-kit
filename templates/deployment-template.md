# Deployment record for [feature]

**Status**: [planned/in progress/deployed/blocked/rolled back]
**Code revision or artifact digest**: [identity] | **Design revisions**: [references]

## Destination mapping

| Logical asset | Actual destination reference | Compatibility | Authorized scope |
|---|---|---|---|
| [APP01] | [host/resource identifier; no credentials] | [OS/runtime/resources] | [actions] |

## Execution and recovery

| Step | Asset | Action and exact command | State | Evidence | Rollback |
|---|---|---|---|---|---|
| [D001] | [APP01] | [reviewed action] | [pending/running/done/blocked] | [result] | [recovery] |

[Dependencies, output acquisition/build, configuration and secrets references,
transfer, migrations, service start, endpoint accessibility and operational health.
Resume by observing actual state before repeating any side effect.]

## Result and handoff

[Endpoints, release identity, operational smoke checks and obstacles. Accessibility
is not test-suite success or acceptance. Hand off to __SPECKIT_COMMAND_TEST__.]
