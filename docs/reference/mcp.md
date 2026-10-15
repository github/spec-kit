# MCP Server

> [!WARNING]
> `specify mcp` is experimental. Its command inventory and tool contracts may
> change before the MCP surface is declared stable.

```bash
specify mcp
```

Starts a Model Context Protocol server over **stdio only**. The command does
not provide HTTP, SSE, daemon/service management, or transport-selection
options. Configure an MCP host to launch `specify mcp` as a local subprocess.

Because stdout carries MCP protocol frames, the server does not print the Spec
Kit banner, Rich output, startup messages, warnings, or logs there.

## Tools

The server exposes first-class tools with typed inputs and results. All are
read-only, local-only (no network access), and reject unexpected arguments.

| Tool | Purpose |
| --- | --- |
| `specify_version` | Return the installed CLI version, runtime, system, and feature capabilities. Takes no arguments. |
| `specify_artifact_list` | Return one paginated page of a project's artifact inventory (`command`, `template`, `script`, `hook`) |
| `specify_artifact_info` | Return one artifact and its complete composition stack |

The artifact tools take an optional absolute `project_directory`; it defaults
to the directory the server was launched from.

`specify_artifact_list` also takes `limit` (1-1000, default 100) and `cursor`.
Its result has `rows`, `next_cursor`, and `truncated`; while `truncated` is
true, pass `next_cursor` as `cursor` to get the next page.

`specify_artifact_info` takes `identifier` (bare name or `kind:name`) and an
optional `kind` (`command`, `template`, `script`, or `hook`).

`specify artifact lookup` is not available through MCP: it does not yet have a
shared typed operation, so no `specify_artifact_lookup` tool is registered.

Three generic tools are also registered, and support only the dotted command
`version`; every other command name is rejected with an `unavailable_command`
tool error.

| Tool | Purpose |
| --- | --- |
| `specify_list_commands` | List CLI commands supported by the generic tools |
| `specify_describe_command` | Describe one supported dotted CLI command |
| `specify_run_command` | Run one supported command through the real Specify CLI |

The server does not expose mutations, installation or update operations,
workflows, confirmations, or access tiers.

## Input validation errors

The first-class tools validate arguments against their input schema before
running. Unexpected arguments, an out-of-range `limit`, a malformed `cursor`,
or an unsupported `kind` are rejected as a text-only MCP tool error with no
structured content, so clients cannot read an `error.code` from it.

## Version tool result and errors

`specify_version` returns the result object directly. If the operation fails,
it returns an MCP tool error whose structured content has `error.code`
(`invalid_operation_result` or `internal_error`), `error.message`, and
`error.details`.

## Artifact results and errors

Artifact tools return their result as structured content. Operation failures
are MCP tool errors whose structured content has `error.code`,
`error.message`, `error.details`, and `error.retryable`.
Both artifact tools can return `invalid_project_directory`,
`not_a_spec_kit_project`, `artifact_resolution_failed`,
`invalid_operation_result`, and `internal_error`.
`specify_artifact_info` can also return `invalid_artifact_identifier`,
`unknown_artifact`, `unknown_hook`, and `ambiguous_artifact`. Results larger
than 1 MiB return a retryable `response_too_large` error; for the list tool,
retry with a smaller `limit`.

## Generic tool result and errors

`specify_run_command` invokes the canonical command below in an isolated child
process using the same Python environment as the running CLI:

```bash
specify version --json
```

On success, the MCP tool returns that command's direct JSON object with
`cli_version`, `runtime`, `system`, and `features`. It does not wrap the result
in universal `schema_version`, `ok`, or `result` fields.

On CLI failure, the adapter consumes the structured JSON error from stderr and
returns an MCP tool error containing `error.code`, `error.message`, and
`error.details`. Empty, malformed, mixed, or non-JSON child-process output is
reported as a sanitized `adapter_internal_error`; the server never substitutes
a success-shaped fallback or exposes a traceback.
