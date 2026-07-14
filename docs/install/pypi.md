# Installing from PyPI

Spec Kit is published to PyPI as [`specify-cli`](https://pypi.org/project/specify-cli/), maintained by the Spec Kit maintainers. Installing from PyPI is the second supported install route alongside installing from the [GitHub source](../installation.md#install-from-source--persistent-installation-recommended). Use whichever fits your workflow — both provide the same `specify` CLI.

> [!NOTE]
> The PyPI release version tracks the GitHub release tags (for example, PyPI `0.12.11` corresponds to the `v0.12.11` tag). Use `specify version` as a local sanity check, and inspect your package manager's record (for example `uv tool list`, `pipx list`, or `pip show specify-cli`) if you need to confirm the installed package source.

## Install Specify CLI

Use whichever Python tool you already have:

```bash
# Using uv (recommended)
uv tool install specify-cli

# Or using pipx
pipx install specify-cli

# Or using pip
pip install specify-cli
```

### Install a specific release

Pin an exact version for reproducible installs (check [PyPI](https://pypi.org/project/specify-cli/#history) or [Releases](https://github.com/github/spec-kit/releases) for available versions):

```bash
# Using uv
uv tool install specify-cli==0.12.11

# Or using pipx
pipx install specify-cli==0.12.11

# Or using pip
pip install specify-cli==0.12.11
```

## Verify

```bash
specify version
```

## Initialize a project

```bash
specify init <PROJECT_NAME> --integration copilot
```

## Upgrade

Upgrade by reinstalling the package through the same tool you used for the original install. If you want to move to the newest PyPI release, use an unpinned install command so you do not keep the existing version pin:

```bash
# Using uv
uv tool install --force specify-cli

# Or using pipx
pipx install --force specify-cli

# Or using pip
pip install --upgrade specify-cli
```

> [!NOTE]
> `specify self upgrade` currently rebuilds `uv tool` and `pipx` installs from the GitHub source release URL rather than preserving a PyPI-based installation. If you want to stay on the PyPI route, use the package-manager commands above. A plain `pip install specify-cli` is treated as an unmanaged install — upgrade it with `pip install --upgrade specify-cli`. See the [Upgrade Guide](../upgrade.md) for details.

## Uninstall

```bash
# Using uv
uv tool uninstall specify-cli

# Or using pipx
pipx uninstall specify-cli

# Or using pip
pip uninstall specify-cli
```

## Next steps

Head to the [Quick Start](../quickstart.md) to initialize your first project.
