# Publishing presets

Publish a versioned preset archive, test it with Spec Kit, and submit a
Preset Submission issue to make it discoverable in the community catalog.
Use the same issue flow for new entries, version updates, and repairs.
Do not submit a hand-edited catalog pull request.

Community listing is not code certification. Maintainers check catalog
entries for completeness and format; they do not review, audit, endorse,
or support community preset code. Users must vet third-party presets before
installing them.

## Prepare the package

Before submitting, have a publicly accessible repository containing a
working `preset.yml`, a preset usage README, and an open-source `LICENSE`.
Use a descriptive letter-leading lowercase-hyphenated ID and numeric
`X.Y.Z` version, such as `team-traceability` and `1.0.0`. Keep descriptions
concise (under 200 characters) and choose two to five useful lowercase tags.
A changelog is recommended.

Start from the developing guide and check the API reference for manifest
fields and dependencies. Include all declared contribution files, and
ensure commands refer to sections the effective templates provide. Local
manifest validation is not a security review or a complete publishing
checklist.

## Test local and release installation

In an initialized test project:

```bash
specify preset add --dev /path/to/team-traceability
specify preset info team-traceability
specify preset resolve spec-template
specify preset list
specify preset remove team-traceability
```

Test on at least one real project. For command contributions, inspect and
invoke the delivered command or skill with supported active integrations.
Check stacking, composition, and removal/restoration, not just whether
installation exits successfully.

Create a tag and a GitHub release for the version. For example:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Pushing a tag is not by itself creating the GitHub release; create that
release through GitHub or your release tooling. Submission accepts pinned
ZIP URLs belonging to the submitted repository:

```text
https://github.com/<owner>/<repo>/archive/refs/tags/v1.0.0.zip
https://github.com/<owner>/<repo>/releases/download/v1.0.0/<asset>.zip
```

Tags may use `vX.Y.Z`, `X.Y.Z`, or a scope with a matching version suffix,
such as `team-traceability-v1.0.0`. A floating `releases/latest/` URL is not
accepted. The GitHub release must exist for that tag.

The CLI also supports `.tar.gz` and `.tgz`, but the community submission
contract currently requires a tag-pinned ZIP. For direct CLI installation,
`preset.yml` must be at the archive root or inside one top-level directory.
The submission verifier can locate preset-scoped manifests in monorepos;
that does not make arbitrary nested monorepo archives installable by the
CLI. Publish a preset-specific asset when necessary.

Test the exact archive URL you will submit:

```bash
specify preset add --from https://github.com/example/team-traceability/archive/refs/tags/v1.0.0.zip
specify preset resolve spec-template
specify preset remove team-traceability
```

## Usage README requirements

The submission's Documentation URL must point to a readable GitHub-hosted
README explaining how to use this preset, not a pitch for a broader
framework or separate CLI. Accepted URL forms are GitHub `blob` or `raw`
URLs and `raw.githubusercontent.com` URLs. The path must end in
`README.md` (case-insensitive); query strings and fragments are ignored for
fetching.

In a monorepo, prefer the preset-scoped README, such as
`presets/team-traceability/README.md`, instead of the repository overview.
Keep that README accessible before downloading the release, whether or
not it also ships inside the archive.

Include what the preset provides, when to use it or not use it, supported
integrations and dependencies, and a valid install command. Prefer:

```bash
specify preset add --from https://github.com/example/team-traceability/archive/refs/tags/v1.0.0.zip
```

The `--from` URL must exactly match the submitted Download URL. A valid
`specify preset add <id>` or `specify preset add --dev <path>` command is
also accepted by validation. ID installation still requires an
install-allowed catalog, so a direct pinned archive is clearest for
community users.

A README with no valid install command fails validation. Stale release
URLs identifiable as belonging to this preset also fail, even if another
valid command is present. Unrelated presets' release examples in monorepos
are distinguished rather than automatically treated as stale.

## Submit to the community catalog

Open a
[Preset Submission issue](https://github.com/github/spec-kit/issues/new?template=preset_submission.yml).
Provide the ID, name, version, description, author, repository URL, pinned
Download URL, Documentation URL, license, required Spec Kit version,
required extension IDs, provided templates/commands/scripts, tags, and key
features. Complete the testing and submission checklists.

Declare required extensions in `preset.yml` too. Catalog metadata alone
cannot convey dependencies for local and direct-archive installs.

An optional submitted checksum can be supplied by appending a `### SHA-256`
heading to the issue with exactly 64 hexadecimal characters. There is no
dedicated checksum field in the form. If supplied, it must match the fetched
archive; a mismatch is a validation failure, not a value the automation
silently replaces.

Do not edit `presets/catalog.community.json` or
`docs/community/presets.md` yourself as a substitute for submission.
Automation prepares those changes after validation.

## What happens after submission

1. The issue form applies the `triage-must-have` intake verdict. It does not
   start catalog validation.
2. During triage, a maintainer separately applies `preset-submission` to
   start the validation workflow. Contributors do not need to apply or
   request that label.
3. Validation checks submission metadata, repository/license availability,
   the linked README and install references, release pinning, archive
   availability, optional submitted checksum, and required checklists.
   The verifier parses the published manifest without executing archive
   content, comparing its ID, version, Spec Kit requirement, and required
   extensions to the issue.
4. On success, automation proposes a draft pull request updating the catalog
   and community table. It records the actual archive digest, preserves
   `created_at` on updates, sorts catalog IDs and display names appropriately,
   and verifies the generated files before marking validation passed.
5. A maintainer reviews the generated catalog changes and merges them when
   approved. The preset becomes discoverable; the community catalog remains
   discovery-only.

Confirmed submission defects are reported with `validation-failed`.
Permission, network, or tooling blockers are reported as blocked, not as
successful checks or necessarily as defects in the preset. The workflow
reports what could not run so a maintainer can investigate and rerun it.

These are metadata and artifact-consistency checks, not a review of preset
instructions, template quality, or executable code safety. There is no
community code-approval or support guarantee.

## Release updates

Update the manifest version and changelog, publish a new immutable tagged
release, and retest its exact archive. Update README install references for
that release, then submit another Preset Submission issue with the new
version and URL. The same issue flow applies to repairing a broken entry.

For private catalogs you operate yourself, maintain current and historical
release records according to the catalog reference. Do not assume the
community submission process publishes a release history or makes that
catalog install-allowed.

## See also

- [Preset overview](overview.md)
- [Developing presets](developing.md)
- [Manifest API](api.md)
- [Catalog entries and historical releases](catalogs.md)
- [CLI reference](cli.md)
- [Community presets](../community/presets.md)
