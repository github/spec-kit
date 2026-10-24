# Enterprise / Air-Gapped Installation

If your environment blocks access to PyPI or GitHub, you can create a portable wheel bundle on a connected machine and transfer it to the air-gapped target.

## Step 1: Build the wheel on a connected machine

> **Important:** `pip download` resolves platform-specific wheels (e.g., PyYAML includes native extensions). You must run this step on a machine with the **same OS and Python version** as the air-gapped target. If you need to support multiple platforms, repeat this step on each target OS (Linux, macOS, Windows) and Python version.

```bash
# Clone the repository
git clone https://github.com/github/spec-kit.git
cd spec-kit

# Build the wheel
pip install build
python -m build --wheel --outdir dist/

# Download the wheel and all its runtime dependencies
pip download -d dist/ dist/specify_cli-*.whl
```

## Step 2: Transfer the `dist/` directory

Copy the entire `dist/` directory (which contains the `specify-cli` wheel and all dependency wheels) to the target machine via USB, network share, or other approved transfer method.

## Step 3: Install on the air-gapped machine

```bash
pip install --no-index --find-links=./dist specify-cli
```

## Step 4: Initialize a project

No network access is required — bundled assets are used by default:

```bash
specify init my-project --integration copilot
```

> **Note:** Python 3.11+ is required.
>
> **Windows note:** Offline scaffolding requires PowerShell 7+ (`pwsh`), not Windows PowerShell 5.x (`powershell.exe`). Install from <https://aka.ms/powershell>.

## Component catalogs and sources

Built-in integrations and bundled components remain available without network
access. Catalog-based installation of external integration adapters,
extensions, presets, workflows, workflow steps, and bundles needs both the
catalog metadata and the referenced release artifacts. For component types
that support a direct or local source, that installation route does not require
catalog metadata.

For a restricted network that can reach approved internal services, host
reviewed catalogs and artifacts on internal HTTPS endpoints, then register each
component-specific source with its `catalog add` command. For a fully
disconnected network, transfer reviewed component artifacts through your
approved process and install them from their supported direct or local source
instead of relying on an unreachable remote catalog.

External integration adapters are an exception. `specify integration install`
has no direct or local source option: it must resolve the adapter through an
install-allowed integration catalog and download its archive. To add an
external adapter inside an isolated environment, keep both an approved internal
catalog and its adapter archive reachable there, or install the adapter before
disconnecting the target. Transferring the archive alone is not sufficient.

Treat bundles separately: a transferred bundle directory or ZIP supplies the
bundle manifest, not the component payloads it names. Before disconnecting,
install matching non-bundled components separately. Components with an explicit
catalog `source` still require network verification even when already installed,
and workflow step payloads currently resolve only through step catalogs. Review
the [bundle offline limits](../reference/bundles.md#install-a-bundle) before
depending on `specify bundle install --offline`.

See the [Catalogs reference](../reference/catalogs.md) for catalog types, trust
policies, and source precedence. If internal endpoints require credentials,
also configure [Authentication](../reference/authentication.md).

## Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```
