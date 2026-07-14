# Fixed-Version Guide

The AI Team distribution is pinned to `v0.12.5+teamwork.1`. Automatic
`specify self check` and `specify self upgrade` are not advertised for this
release because the team intentionally uses one reviewed CLI and workflow
baseline.

## Install Or Repair The CLI

Use the same command for a new installation, a repair, or standardizing a
workstation that has another Spec Kit version:

```bash
uv tool install specify-cli --force \
  --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.1
```

For `pipx` environments:

```bash
pipx install --force \
  git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.1
```

Verify the pinned package version:

```bash
specify --version
```

Expected output includes:

```text
specify 0.12.5+teamwork.1
```

## Refresh Project Files

Installing the CLI does not silently replace a project's existing commands,
templates, extensions, presets, or workflow state. From the project root,
refresh only the integration and components the team has selected.

Inspect the active setup first:

```bash
specify version --features
specify integration list
specify extension list
specify preset list
specify workflow list
```

Re-run project initialization only when the team has reviewed which managed
files may be refreshed:

```bash
specify init --here --integration <your-agent>
```

Do not use `--force` casually in an established project. Preserve customized
project files and review the generated diff before committing.

## Moving To A Future Teamwork Release

A future release must publish a new reviewed tag and update the pinned version
in this guide. Do not follow the latest upstream Spec Kit release implicitly;
the AI Team distribution remains locked until maintainers approve a new
one-time baseline or Teamwork release.
