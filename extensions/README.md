# Spec Kit Extensions

Extension system for [Spec Kit](https://github.com/github/spec-kit) - add new functionality without bloating the core framework.

## Extension Catalogs

Spec Kit provides two catalog files with different purposes:

### Your Catalog (`catalog.json`)

- **Purpose**: Default upstream catalog of extensions used by the Spec Kit CLI
- **Default State**: Empty by design in the upstream project - you or your organization populate a fork/copy with extensions you trust
- **Location (upstream)**: `extensions/catalog.json` in the GitHub-hosted spec-kit repo
- **CLI Default**: The `specify extension` commands use the upstream catalog URL by default, unless overridden
- **Org Catalog**: Point `SPECKIT_CATALOG_URL` at your organization's fork or hosted catalog JSON to use it instead of the upstream default
- **Customization**: Copy entries from the community catalog into your org catalog, or add your own extensions directly

**Example override:**
```bash
# Override the default upstream catalog with your organization's catalog
export SPECKIT_CATALOG_URL="https://your-org.com/spec-kit/catalog.json"
specify extension search  # Now uses your organization's catalog instead of the upstream default
```

### Community Reference Catalog (`catalog.community.json`)

- **Purpose**: Browse available community-contributed extensions
- **Status**: Active - contains extensions submitted by the community
- **Location**: `extensions/catalog.community.json`
- **Usage**: Reference catalog for discovering available extensions
- **Submission**: Open to community contributions via Pull Request

**How It Works:**

## Making Extensions Available

You control which extensions your team can discover and install:

### Option 1: Curated Catalog (Recommended for Organizations)

Populate your `catalog.json` with approved extensions:

1. **Discover** extensions from various sources:
   - Browse `catalog.community.json` for community extensions
   - Find private/internal extensions in your organization's repos
   - Discover extensions from trusted third parties
2. **Review** extensions and choose which ones you want to make available
3. **Add** those extension entries to your own `catalog.json`
4. **Team members** can now discover and install them:
   - `specify extension search` shows your curated catalog
   - `specify extension add <name>` installs from your catalog

**Benefits**: Full control over available extensions, team consistency, organizational approval workflow

**Example**: Copy an entry from `catalog.community.json` to your `catalog.json`, then your team can discover and install it by name.

### Option 2: Direct URLs (For Ad-hoc Use)

Skip catalog curation - team members install directly using URLs:

```bash
specify extension add --from https://github.com/org/spec-kit-ext/archive/refs/tags/v1.0.0.zip
```

**Benefits**: Quick for one-off testing or private extensions

**Tradeoff**: Extensions installed this way won't appear in `specify extension search` for other team members unless you also add them to your `catalog.json`.

## Available Community Extensions

The following community-contributed extensions are available in [`catalog.community.json`](catalog.community.json):

| Extension | Purpose | URL |
|-----------|---------|-----|
| V-Model Extension Pack | Enforces V-Model paired generation of development specs and test specs with full traceability | [spec-kit-v-model](https://github.com/leocamello/spec-kit-v-model) |
| Cleanup Extension | Post-implementation quality gate that reviews changes, fixes small issues (scout rule), creates tasks for medium issues, and generates analysis for large issues | [spec-kit-cleanup](https://github.com/dsrednicki/spec-kit-cleanup) |

## Adding Your Extension

### Submission Process

To add your extension to the community catalog:

1. **Prepare your extension** following the [Extension Development Guide](EXTENSION-DEVELOPMENT-GUIDE.md)
2. **Create a GitHub release** for your extension
3. **Submit a Pull Request** that:
   - Adds your extension to `extensions/catalog.community.json`
   - Updates this README with your extension in the Available Extensions table
4. **Wait for review** - maintainers will review and merge if criteria are met

See the [Extension Publishing Guide](EXTENSION-PUBLISHING-GUIDE.md) for detailed step-by-step instructions.

### Submission Checklist

Before submitting, ensure:

- ✅ Valid `extension.yml` manifest
- ✅ Complete README with installation and usage instructions
- ✅ LICENSE file included
- ✅ GitHub release created with semantic version (e.g., v1.0.0)
- ✅ Extension tested on a real project
- ✅ All commands working as documented

## Installing Extensions
Once extensions are available (either in your catalog or via direct URL), install them:

```bash
# From your curated catalog (by name)
specify extension search                  # See what's in your catalog
specify extension add <extension-name>    # Install by name

# Direct from URL (bypasses catalog)
specify extension add --from https://github.com/<org>/<repo>/archive/refs/tags/<version>.zip

# List installed extensions
specify extension list
```

For more information, see the [Extension User Guide](EXTENSION-USER-GUIDE.md).
