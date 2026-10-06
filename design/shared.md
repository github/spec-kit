# Shared Command Application Architecture

This document defines the application layer beneath Specify delivery adapters.
A logical operation has one shared implementation. The CLI, MCP, and any future
delivery surface translate their own inputs into that operation and translate
its outcome into their own output and error conventions.

[Specify CLI Command Architecture](cli.md) defines the Typer/terminal adapter.
[Specify MCP Command Architecture](mcp.md) defines MCP tool exposure, policy,
and transport. Neither adapter document owns application behavior.

## Design goals

The shared layer optimizes for:

- **One behavior:** every adapter for a logical operation invokes the same
  semantic implementation.
- **Adapter independence:** adapters own invocation and reporting without
  calling or parsing one another.
- **Typed contracts:** requests, results, warnings, and expected errors are
  explicit and testable.
- **Transport neutrality:** shared contracts contain no Typer, Rich, MCP,
  stdout/stderr, protocol, or exit-code concerns.
- **Explicit context:** project roots, policy, deadlines, cancellation, and
  output budgets are passed rather than read from mutable process globals.
- **Reviewable ownership:** application behavior has a predictable source and
  mirrored tests.

## Non-goals

The shared layer does not:

- Standardize how adapters spell arguments, display progress, or format human
  output.
- Require byte-identical CLI JSON and MCP protocol envelopes.
- Turn the shared operation into a universal string-based command dispatcher.
- Replace focused domain modules with a central service locator.
- Make transport authentication, MCP authorization, or CLI prompting part of
  domain behavior.
- Require extra modules for a small operation when an existing Typer-free
  domain module is already the correct owner.

## One logical operation, multiple adapters

Adapters are peers above one application operation:

```text
CLI arguments/options ─┐
MCP tool input JSON ───┼─> typed operation request -> shared behavior
future adapter input ──┘                         -> typed operation outcome

typed operation outcome ─┬─> CLI text, JSON, warnings, and exit status
                         ├─> MCP structured content or tool error
                         └─> future adapter representation
```

The shared operation is the semantic source of truth. Adapters may expose
different presentation features, but equivalent requests must produce
equivalent results, warnings, expected failures, and side effects.

An adapter must not:

- Invoke another adapter.
- Parse another adapter's output.
- Reimplement application orchestration.
- Add semantic defaults, trust, consent, or side effects that are absent from
  the shared request.

## Ownership boundaries

| Concern | Owner |
| --- | --- |
| Logical operation ID and contract version | Shared operation descriptor |
| Semantic request/result/warning/error models | Relevant command/domain hierarchy |
| Capability-free and state-dependent validation | Shared operation |
| Application orchestration and side effects | Shared operation and domain modules |
| Operation-private phases | `_operation_<name>_<phase>.py` |
| Invocation syntax and presentation | Delivery adapter |
| Human prompting and terminal rendering | CLI adapter |
| MCP tool schemas, annotations, and tool errors | MCP adapter |
| CLI exit-code mapping | CLI adapter |
| MCP access-policy enforcement and transport | MCP infrastructure |

Domain behavior that already has a focused Typer-free owner may remain there.
A dedicated `_operation_<name>.py` coordinates domain calls when the adapter
otherwise would own semantic validation or orchestration.

## Logical operation identity

The operation ID follows the CLI leaf path without the leading `specify`:

```text
specify version                -> version
specify artifact list          -> artifact.list
specify extension set-priority -> extension.set-priority
```

The ID names application behavior, not a transport endpoint. Adapter identities
derive from it:

```text
operation: artifact.list
CLI:       specify artifact list
MCP:       specify_artifact_list
```

An operation descriptor declares at least:

```text
operation_id
contract_version
request_type
result_type
warning_types
error_types
capabilities
network_access
project_scope
default_timeout
```

Adapter-specific registration metadata extends this descriptor without moving
the shared fields into adapter infrastructure.

## Naming and layout

When a focused shared application entry point is required, use:

```text
_operation_<name>.py
```

For example:

```text
src/specify_cli/
├── _operation_version.py
├── command_version.py
└── mcp_version.py
```

A simple operation stays in one operation or existing domain module. Do not
split it for symmetry.

When a complex operation has cohesive phases with distinct invariants, failure
behavior, rollback, or tests, use:

```text
_operation_<name>.py
_operation_<name>_<phase>.py
```

For example:

```text
src/specify_cli/
├── _operation_init.py
├── _operation_init_validation.py
├── _operation_init_plan.py
├── _operation_init_apply.py
├── _operation_init_finalize.py
├── command_init.py
└── mcp_init.py
```

`_operation_init.py` is the application entry point. Phase modules do not
register commands or tools.

Adapter-only phases retain adapter-specific names:

```text
_command_<name>_<phase>.py
_mcp_<name>_<phase>.py
```

If more than one adapter needs a phase, it is not adapter-private and belongs
in the shared operation or domain layer.

Nested directories continue to represent real command namespaces or bounded
subdomains. Do not create an operation-phase directory that implies a
nonexistent CLI namespace.

## Typed request contract

The relevant command/domain hierarchy owns a typed request model. It:

- Uses semantic names rather than CLI flag or MCP field implementation names.
- Distinguishes omitted values from explicit false, empty, or null values.
- Rejects unknown fields.
- Represents paths, enums, identifiers, and bounded collections explicitly.
- Carries explicit consent such as `force` or external-source trust only when
  the operation defines that behavior.

Adapters perform transport parsing and map into this request. They do not
perform state-dependent semantic work while constructing it.

## Validation and authorization lifecycle

No denied capability may be exercised while deciding whether a request is
authorized. Invocation follows this order:

1. The adapter parses and schema-validates input without filesystem, network,
   environment, or process access.
2. The shared operation performs capability-free request validation using
   only request values and static operation metadata.
3. The shared operation computes request-required capabilities, network
   requirements, and requested roots without I/O.
4. The applicable policy layer authorizes those requirements. A denial stops
   the invocation.
5. Under authorized capabilities, the shared operation resolves project
   context and performs state-dependent validation.
6. The shared operation performs side effects and returns its typed outcome.

Capability-free validation covers types, enums, mutually exclusive fields,
required combinations, and similar pure invariants. State-dependent
validation includes reading project files, resolving installed integrations,
consulting catalogs, inspecting host tools, and other I/O.

The computed requirements must conservatively cover every path reachable from
the pure validated request. Stateful validation must not discover and exercise
an additional unauthorized capability.

## Typed outcome contract

The operation returns a typed outcome containing:

- The command-specific result.
- Zero or more structured warnings.
- Adapter-relevant execution metadata such as changed paths or transaction
  status.

Warnings have a stable code, human-readable message, and typed details. The
operation does not print them. Each adapter decides how its surface represents
them.

There is no mandatory universal success envelope. Command-specific output
types remain owned by the command/domain hierarchy.

## Structured errors

Expected failures use a transport-neutral operation error:

```text
code
message
details
retryable
```

The operation hierarchy owns error codes and detail schemas. Adapters map them:

- CLI maps them to human or JSON failure output and established exit codes.
- MCP maps them to structured tool errors.

Shared errors contain no CLI exit code, Rich markup, MCP content block, HTTP
status, traceback, raw subprocess output, or secret.

Unexpected exceptions are normalized by the adapter boundary to a sanitized
internal error and logged only through the adapter's diagnostic channel.

## Contract versions and machine compatibility

The operation descriptor is the source of truth for `contract_version`. The
version covers the semantic request, result, warning, and expected-error
contract, not package or transport versions.

Both adapters conform to that declared version:

- MCP exposes it through tool or inventory metadata.
- CLI contract tests reference it while preserving established human and JSON
  output. A version field is not injected into an existing JSON result unless
  that result contract already defines one.

Contract evolution follows these rules:

- Backward-compatible optional fields and warning codes may retain the current
  major version.
- Removing, renaming, or changing the meaning of an input, output, warning, or
  error requires a new major version and explicit compatibility strategy.
- Adapter-only presentation changes do not change the operation contract
  version.
- Tests lock established adapter schemas and machine-output shapes to the
  declared contract.

## Invocation context

Shared operations receive an immutable context rather than reading adapter or
process globals:

```text
InvocationContext
├── launch_working_directory
├── project_root
├── allowed_roots
├── access_policy
├── deadline
├── cancellation
└── output_budget
```

Not every operation uses every field. Adapters and application infrastructure
construct the context; command/domain code consumes it explicitly.

Shared operations must not call `os.chdir()` to establish request context.
They pass resolved roots through operation phases and domain calls. Deadlines,
cancellation, and output budgets are likewise explicit.

## Capability declarations

Capabilities are independent requirements, not a highest-risk hierarchy:

| Capability | Meaning |
| --- | --- |
| `local-read` | Read process, host, or project state within allowed roots |
| `project-write` | Create or change project/target files or configuration |
| `execution` | Start host tools, workflows, hooks, agents, or processes |
| `self-modifying` | Change the Specify installation or machine-level state |

The descriptor declares the conservative union an operation may require.
`required_capabilities(request)` may compute an exact subset only from the
capability-free validated request and static metadata.

Network access is declared separately as `none`, `optional`, or `required`.
Trust and destructive consent remain explicit request values, not implied
capabilities.

The MCP design defines policy enforcement for its tool surface. CLI invocation
and reporting remain defined by the CLI design, but the CLI adapter must not
change the operation's capability, trust, or consent semantics.

## Testing structure

Tests mirror source ownership:

```text
src/specify_cli/artifacts/_operation_list.py
tests/specify_cli/artifacts/test_operation_list.py

src/specify_cli/artifacts/command_list.py
tests/specify_cli/artifacts/test_command_list.py

src/specify_cli/artifacts/mcp_list.py
tests/specify_cli/artifacts/test_mcp_list.py
```

Operation tests cover:

- Valid requests and intended results.
- Pure and state-dependent validation failures.
- Warnings and structured errors.
- Capabilities, trust, consent, network behavior, side effects, rollback,
  cancellation, and output bounds.
- Domain behavior without Typer, Rich, MCP, or transport assertions.

Adapter tests cover invocation mapping and adapter-specific reporting.

Parity tests invoke CLI and MCP adapters against the same operation fixture
and compare semantic request, result, warning, error, and side-effect behavior.
Parity does not require byte-identical presentation.

Behavioral changes follow
[Testing deterministic behavior](../CONTRIBUTING.md#testing-deterministic-behavior):
positive and negative evidence is required, and bug fixes need before-and-after
regression evidence.

## Anti-patterns

Avoid:

- Calling a Typer handler from MCP or an MCP tool from CLI.
- Invoking the human CLI as application dispatch.
- Parsing Rich, stdout, stderr, or protocol output to recover domain results.
- Duplicating validation or orchestration in adapters.
- Adding adapter concepts to request, outcome, warning, or error models.
- Hiding operations behind a central string dispatcher or service locator.
- Letting adapters infer force, trust, consent, or extra capabilities.
- Reading mutable process cwd instead of using invocation context.
- Splitting simple operations or creating phase modules solely for symmetry.

## Review checklist

For an operation with CLI and MCP adapters:

- [ ] One logical operation ID identifies both surfaces.
- [ ] Both adapters map into the same typed request and shared entry point.
- [ ] Semantic validation, orchestration, and side effects are below adapters.
- [ ] Adapter modules contain only invocation, mapping, presentation, and
      adapter-specific concerns.
- [ ] Shared request, outcome, warning, and error types are transport-neutral.
- [ ] Capability computation is pure and authorization precedes stateful work.
- [ ] CLI exit codes and MCP tool errors remain adapter-owned.
- [ ] Contract-version ownership and compatibility tests are explicit.
- [ ] Operation tests and adapter parity tests cover positive and negative
      behavior.
- [ ] No adapter invokes or parses another adapter.
