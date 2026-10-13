# Installing from PyPI

Spec Kit is published to PyPI as [`specify-cli`](https://pypi.org/project/specify-cli/), maintained by the Spec Kit maintainers. Installing from PyPI is the second supported install route alongside installing from the [GitHub source](../installation.md#install-from-source--persistent-installation-recommended). Use whichever fits your workflow — both provide the same `specify` CLI.

> [!NOTE]
> The PyPI release version tracks the GitHub release tags (for example, PyPI `0.12.11` corresponds to the `v0.12.11` tag). `specify version` is only a local version/runtime sanity check — it reports the installed version but not where the `specify` executable came from, so it cannot distinguish a PyPI install from a Git install. To confirm the install source, inspect the source metadata your package manager records: `pipx list --json` reports the exact install specification for each tool, and for uv/pip installs you can check the package's [PEP 610](https://peps.python.org/pep-0610/) `direct_url.json` inside its `*.dist-info` directory (a Git or URL install records the repository/archive URL there, while a plain PyPI index install does not create that file). Note that `pip show specify-cli` only prints package metadata and will not see uv/pipx-managed environments from the host interpreter.

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

## Install from a custom or private package index

Some environments (corporate networks, mirrors, proxies, or artifact feeds) require installing `specify-cli` from a package index other than the default public PyPI. Each Python tool exposes a way to point at a different index — configure it before running the install commands above. Substitute your own index URL for the placeholder shown here.

```bash
# uv — via environment variable (applies to the whole command)
UV_DEFAULT_INDEX=https://your-index.example.com/pypi/simple/ uv tool install specify-cli

# uv — via flag
uv tool install --default-index https://your-index.example.com/pypi/simple/ specify-cli

# pipx — pass a pip argument through
pipx install specify-cli --index-url https://your-index.example.com/pypi/simple/

# pip
pip install specify-cli --index-url https://your-index.example.com/pypi/simple/
```

> [!NOTE]
> The same index configuration applies to pinned installs, upgrades (`--force`/`--upgrade`), and one-time usage — set the environment variable or flag on those commands too. If your index requires authentication, follow your tool's documentation and prefer credential environment variables, keyring, or netrc; do not embed secrets in command-line URLs because they can leak through shell history, process listings, or logs. Avoid committing secrets. For fully offline installs, see the [air-gapped installation guide](air-gapped.md).

## Verify

```bash
specify version
```

## Initialize a project

```bash
specify init <PROJECT_NAME> --integration copilot
```

## Upgrade

Upgrade by reinstalling the package through the same tool you used for the original install. If you originally pinned a version, note that `uv tool upgrade` preserves that pin; to move to the newest PyPI release, use an unpinned install command so you do not keep the existing version pin:

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
