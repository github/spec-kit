---
name: add-community-extension
description: 'Add a community extension to the Spec Kit catalog from a GitHub issue submission. USE FOR: processing extension submission issues, validating catalog entries, updating catalog.community.json and docs/community/extensions.md, creating PRs. DO NOT USE FOR: creating new extensions from scratch, or first-party extension work.'
argument-hint: 'GitHub issue URL or number for the extension submission'
---

# Add Community Extension

Process an extension submission issue and add or update it in the community catalog.

## When to Use

- A new `[Extension]` submission issue is filed
- An existing extension submits an update issue (new version, changed metadata)
- You need to add or update a community extension in `extensions/catalog.community.json` and `docs/community/extensions.md`

## Procedure

### 1. Fetch the submission issue

Read the GitHub issue to extract all metadata:
- Extension ID, name, version, description, author
- Repository URL, download URL, homepage, documentation, changelog
- License, required spec-kit version, optional tool dependencies
- Number of commands and hooks
- Tags

### 2. Validate against publishing rules

Check **all** of the following (per `extensions/EXTENSION-PUBLISHING-GUIDE.md`):

| Check | How |
|-------|-----|
| Repository exists and is public | Fetch the repository URL |
| `extension.yml` manifest present | Confirm in repo file listing |
| README.md present | Confirm in repo file listing |
| LICENSE file present | Confirm in repo file listing |
| GitHub release exists matching version | Check releases on the repo page |
| Download URL is accessible | Verify it follows `archive/refs/tags/vX.Y.Z.zip` pattern and release exists |
| Extension ID is lowercase-with-hyphens only | Regex: `^[a-z][a-z0-9-]*$` |
| Version follows semver | Format: `X.Y.Z` |
| Submission checklists are all checked | Confirm in issue body |

### 3. Determine if this is an add or update

Search `extensions/catalog.community.json` for the extension ID.

- **Not found** → this is a **new addition**. Proceed to step 4.
- **Found** → this is an **update**. Proceed to step 4 but replace the existing entry in-place instead of inserting.

### 4. Add or update `extensions/catalog.community.json`

**New extension:** Insert the entry in **alphabetical order** by extension ID.

**Update:** Replace the existing entry in-place. Update only the fields that changed (typically `version`, `download_url`, `description`, `provides`, `requires`, `tags`, `updated_at`). Preserve `created_at` and `downloads`/`stars` from the existing entry.

Use the existing entries as the format template. Required fields:

```json
{
  "<id>": {
    "name": "<name>",
    "id": "<id>",
    "description": "<description>",
    "author": "<author>",
    "version": "<version>",
    "download_url": "<download_url>",
    "repository": "<repository>",
    "homepage": "<homepage>",
    "documentation": "<documentation>",
    "changelog": "<changelog>",
    "license": "<license>",
    "requires": {
      "speckit_version": "<speckit_version>"
    },
    "provides": {
      "commands": <N>,
      "hooks": <N>
    },
    "tags": ["<tag1>", "<tag2>"],
    "verified": false,
    "downloads": 0,
    "stars": 0,
    "created_at": "<today>T00:00:00Z",
    "updated_at": "<today>T00:00:00Z"
  }
}
```

If the extension has optional tool dependencies, add a `"tools"` array inside `"requires"`:

```json
"tools": [{ "name": "<tool>", "required": false }]
```

Also update the top-level `"updated_at"` timestamp in the catalog.

After editing, **validate the JSON** by running:

```bash
python3 -c "import json; json.load(open('extensions/catalog.community.json')); print('Valid JSON')"
```

### 5. Add or update `docs/community/extensions.md` community extensions table

**New extension:** Insert a new row into the `# Community Extensions` table in **alphabetical order** by extension name.

**Update:** Find the existing row and update the description or other changed fields in-place.

Determine the category and effect from the extension's behavior:

```
| <Name> | <Description> | `<category>` | <Effect> | [<repo-name>](<repository-url>) |
```

**Category** — one of: `docs`, `code`, `process`, `integration`, `visibility`
**Effect** — `Read-only` (produces reports only) or `Read+Write` (modifies project files)

### 6. Commit, push, and open PR

Use `add-` for new extensions, `update-` for updates:

```bash
# New extension
git checkout -b add-<extension-id>-extension

# Update
git checkout -b update-<extension-id>-extension
```

```bash
git add extensions/catalog.community.json docs/community/extensions.md

# New extension
git commit -m "Add <Name> extension to community catalog

Add <id> extension submitted by @<issue-author> to:
- extensions/catalog.community.json (alphabetical order)
- docs/community/extensions.md community extensions table

Closes #<issue-number>"

# Update
git commit -m "Update <Name> extension to v<version>

Update <id> extension submitted by @<issue-author>:
- extensions/catalog.community.json (version, download_url, etc.)
- docs/community/extensions.md community extensions table

Closes #<issue-number>"

git push origin <branch-name>
```

Then create a PR to `upstream` (`github/spec-kit`) with:
- **Title:** `Add <Name> extension to community catalog` (or `Update <Name> extension to v<version>`)
- **Body:** Include validation summary, `Closes #<issue-number>`, and `cc @<issue-author>`
- **Head:** `<fork-owner>:<branch-name>`
- **Base:** `main`

## Common Pitfalls

- **Alphabetical order matters** — entries must be sorted by ID in the JSON and by name in the docs table.
- **Don't forget the catalog `updated_at`** — the top-level timestamp in `catalog.community.json` must be refreshed.
- **Validate JSON after editing** — a trailing comma or missing brace will break the catalog.
- **Use `Closes` not `Fixes`** — `Closes #N` is the correct keyword for submission issues.
- **Match the proposed entry but verify** — the issue may include a proposed JSON block, but always validate field values against the actual repository state.
- **Preserve `created_at` on updates** — keep the original `created_at` value; only change `updated_at`.
- **Preserve `downloads` and `stars` on updates** — these reflect usage metrics and must not be reset.
