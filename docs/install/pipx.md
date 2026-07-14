# Installing with pipx

[pipx](https://pipx.pypa.io/) is a tool for installing Python CLI applications in isolated environments. It does not require [uv](https://docs.astral.sh/uv/).

## Install Specify CLI

Pin a specific release tag for stability (check [Releases](https://github.com/github/spec-kit/releases) for the latest):

```bash
# Install a specific stable release (recommended — replace vX.Y.Z with the
# latest tag, keeping the leading v, e.g. v0.12.11 not 0.12.11)
pipx install git+https://github.com/github/spec-kit.git@vX.Y.Z

# Or install latest from main (may include unreleased changes)
pipx install git+https://github.com/github/spec-kit.git
```

## Verify

```bash
specify version
```

`specify version` reports the installed Spec Kit CLI version and runtime details. It is a useful version/runtime check, but it does not prove whether the executable came from a Git source, a PyPI package, or another location. If you need to confirm installation provenance, inspect the package manager's stored install metadata (for example, `pipx list` for `pipx`-managed installs).

## Upgrade

```bash
pipx install --force git+https://github.com/github/spec-kit.git@vX.Y.Z
```

If you want to move to the latest release instead of a pinned tag, omit the `@vX.Y.Z` suffix from the install command above.

## Uninstall

```bash
pipx uninstall specify-cli
```

## Next steps

Head to the [Quick Start](../quickstart.md) to initialize your first project.
