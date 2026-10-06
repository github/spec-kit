# MCP Server

> [!WARNING]
> `specify mcp` is experimental. Its command inventory and tool contracts may
> change before the MCP surface is declared stable.

This page documents the current transitional implementation. See
[Specify MCP Command Architecture](https://github.com/github/spec-kit/blob/main/design/mcp.md)
for the intended first-class tool, shared-operation, policy, and transport
architecture.

```bash
specify mcp
```

Starts a Model Context Protocol server over **stdio only**. The command does
not provide HTTP, SSE, daemon/service management, or transport-selection
options. Configure an MCP host to launch `specify mcp` as a local subprocess.

Because stdout carries MCP protocol frames, the server does not print the Spec
Kit banner, Rich output, startup messages, warnings, or logs there.

## Tools

The server exposes three generic tools:

| Tool | Purpose |
| --- | --- |
| `specify_list_commands` | List CLI commands currently supported through MCP |
| `specify_describe_command` | Describe one supported dotted CLI command |
| `specify_run_command` | Run one supported command through the real Specify CLI |

This first experimental release supports only the dotted command `version`.
Every other command name is rejected with an `unavailable_command` tool error.
The server does not expose project discovery, artifacts, mutations,
installation or update operations, workflows, confirmations, or access tiers.

## Version result and errors

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
