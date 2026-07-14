# Installing with pipx

[pipx](https://pipx.pypa.io/) is a tool for installing Python CLI applications in isolated environments. It does not require [uv](https://docs.astral.sh/uv/).

## Install Specify CLI

Install the pinned AI Team release:

```bash
pipx install git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.1
```

## Verify

```bash
specify version
```

## Upgrade

```bash
pipx install --force git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.1
```

## Uninstall

```bash
pipx uninstall specify-cli
```

## Next steps

Head to the [Quick Start](../quickstart.md) to initialize your first project.
