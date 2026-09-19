# Project Configuration

Use `specify config` to inspect and safely change supported settings recorded
when you initialized a project. Run these commands from the project root, or
set `SPECIFY_INIT_DIR` to the project root.

## Inspect configuration

```bash
specify config list
specify config list --json
specify config get script
```

`list` shows persisted initialization settings and a summary of installed
extensions. `--json` prints both as machine-readable JSON.

## Change supported initialization settings

```bash
specify config set feature-numbering timestamp
```

Supported values are:

| Setting | Values |
| --- | --- |
| `feature-numbering` | `sequential`, `timestamp` |

Legacy projects without `.specify/init-options.json` must first run
`specify integration install <key>` (or `specify integration use <key>` for an
already installed integration). Until then, `config set` refuses to create the
file because doing so without an active agent would disable legacy extension
and preset command registration.

Script type, the active integration, and skills layout are owned by
`specify integration`. Changing a script type requires regenerating installed
agent files:

```bash
specify integration upgrade <integration> --script py
```

Use the active integration key to update both its commands and the script
setting shown by `config get script`. Supported script types are `sh`, `ps`,
and `py`. Upgrade checks manifest hashes and refuses to overwrite modified
files without `--force`; review those changes before choosing to overwrite
them.

Use `specify integration use <integration>` to select an installed integration.
For layout changes, use `specify integration upgrade <integration>
--integration-options="..."` with that integration's supported options. For
example, Copilot supports `--integration-options="--commands"`. Layout options
vary by integration; `ai-skills` is not a universal toggle.

`here` and `speckit-version` are read-only initialization metadata. Known
read-only settings and unknown keys produce distinct errors when set.

## Manage extensions

`specify config extension` exposes the existing extension lifecycle under the
configuration namespace. It has the same behavior as `specify extension`.

```bash
specify config extension list
specify config extension add tdd
specify config extension disable tdd
specify config extension enable tdd
specify config extension remove tdd
```

Use `specify config extension --help` to see the full extension command set.
