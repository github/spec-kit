# Publishing bundles

Publish a versioned bundle artifact, test its distribution path, then submit
metadata through a Bundle Submission issue. Use the same issue flow for new
entries, version updates, and repairs. Do not hand-edit the community catalog
or its documentation table as a substitute for submission.

Community publication is not code certification. Maintainers check metadata,
links, artifact consistency, and submitted installation evidence; they do not
review, audit, endorse, or support bundle code or its installed components.
Users must vet those components before installation.

## Prepare a release

Provide a public GitHub repository containing `bundle.yml`, `README.md`, and a
license file (`LICENSE`, `LICENSE.md`, or `LICENSE.txt`). The README must explain
the intended role, installed components, required catalogs, and installation
and usage steps.

Use a safe bundle ID matching the manifest contract. Community submission
versions must be numeric `X.Y.Z`, without a `v` prefix. This is narrower than
the manifest parser's general SemVer support. Choose two to five lowercase tags.

Validate online and build the versioned artifact:

```bash
specify bundle validate --path ./team-setup
specify bundle build --path ./team-setup --output ./dist
```

Resolve warnings and confirm the intended component releases are available.
Build performs structural checks only; a built ZIP is not installation
evidence. Include the manifest and README as regular files, not symlinks.

Create a tag and GitHub release, then attach the generated
`team-setup-1.0.0.zip`. The community Download URL must belong to the submitted
repository and follow this form:

```text
https://github.com/<owner>/<repo>/releases/download/<tag>/<id>-<version>.zip
```

The tag must match the submitted version: `v1.0.0`, `1.0.0`, or a scoped tag
with the matching suffix, such as `team-setup-v1.0.0`. Floating
`releases/latest/` URLs and source archives are not the community bundle asset
contract. The release and exact attached ZIP asset must exist.

## Test the distribution path

Test in a clean Spec Kit project with the intended integration and every
required vetted component catalog registered. Installing the release artifact
must work without relying on components left over in the author's project.

For example, after vetting the sources:

```bash
specify init --here --integration copilot
specify preset catalog add https://example.com/presets.json \
  --name team --install-allowed
specify extension catalog add https://example.com/extensions.json \
  --name team --install-allowed
curl -L -o team-setup-1.0.0.zip \
  https://github.com/example/team-setup/releases/download/v1.0.0/team-setup-1.0.0.zip
specify bundle install ./team-setup-1.0.0.zip
specify bundle list --json
```

Use only the catalog commands your bundle actually needs, including workflow
and step catalogs where applicable. If every component resolves from packaged
or default sources, report `None` for required component catalogs.

If proposing a bundle catalog entry, test ID installation from an
install-allowed catalog in a separate clean project:

```bash
specify bundle catalog add https://example.com/bundles.json \
  --id team --policy install-allowed
specify bundle install team-setup
```

Register required component catalogs in that project too. The bundle catalog
locates the manifest; it does not register companion catalogs. The built-in
community catalog remains discovery-only after publication.

Describe validation, building, artifact installation, catalog-ID installation
when applicable, actual use of installed commands/workflows, and removal.
Include the tested Spec Kit version, operating system, integration, and any
dependency catalogs in the submitted testing details.

## Submit metadata

Open a
[Bundle Submission issue](https://github.com/github/spec-kit/issues/new?template=bundle_submission.yml).
Supply the ID, name, version, role/team, description, author, repository URL,
Download URL, Documentation URL, license, required Spec Kit version, optional
integration target, component summary, required catalogs, tags, key features,
testing details, example usage, and proposed catalog entry.

Complete every required testing and submission checkbox. The manifest,
README, issue metadata, catalog proposal, and test evidence must agree.
Required companion catalogs must have HTTPS URLs and documented setup
commands; submission automation does not register them.

An optional submitted checksum can be supplied as `sha256` in the proposed
catalog entry or beneath an appended `### SHA-256` heading. It must contain
exactly 64 hexadecimal characters. If both locations are supplied, they must
agree after trimming whitespace and normalizing case. A malformed or
mismatching checksum fails validation; it is not silently replaced.

## What happens after submission

1. The issue form applies the `triage-must-have` intake verdict. That does not
   start catalog validation.
2. A maintainer reviews the issue during triage and separately applies
   `bundle-submission` to start the automated workflow. Contributors do not
   need to apply or request that label.
3. Automation validates fields, repository/documentation availability,
   manifest consistency, license availability, release pinning, the actual
   artifact download and optional checksum, catalog shape, required catalogs,
   and testing attestations. It does not execute downloaded content or audit
   the code.
4. On success, automation proposes a draft pull request updating
   `bundles/catalog.community.json` and `docs/community/bundles.md`. It records
   the actual downloaded archive's SHA-256 and keeps `verified: false`.
5. A maintainer reviews the catalog changes and merges them when approved.
   The entry becomes discoverable with `specify bundle search`.

Confirmed submission defects receive `validation-failed` with correction
details. Permission, network, or tooling blockers are reported as blocked,
not as passed checks or necessarily as defects in the bundle. A checksum
mismatch or observed missing artifact is a submission failure.

## Updates and repairs

Publish a new immutable tagged release, update manifest and README references,
and retest the exact artifact and applicable catalog install path. File another
Bundle Submission issue and identify the existing entry being updated.
Versions must advance unless the issue explicitly explains a metadata-only
correction at the same version.

For a private catalog you operate, follow the catalog reference for current
and historical release records. Do not assume the community submission flow
retains old releases or changes the built-in source to install-allowed.

## See also

- [Developing and testing bundles](developing.md)
- [Manifest API](api.md)
- [Catalog entries and release history](catalogs.md)
- [CLI reference](cli.md)
- [Community bundle listing](../community/bundles.md)
- [Bundle overview](overview.md)
