# Community Bundles

> [!NOTE]
> Community bundles are independently created and maintained by their respective authors. Maintainers only verify that submission metadata is complete and correctly formatted — they do **not review, audit, endorse, or support the bundle code or the components it installs**. Review bundle manifests, component catalogs, and source repositories before installation and use at your own discretion.

Bundles compose existing Spec Kit components — extensions, presets, workflows, and steps — into a single role or team stack. They are useful when a user should be able to install a tested set of components together instead of following several separate install commands.

Accepted community bundle entries are published in [`bundles/catalog.community.json`](https://github.com/github/spec-kit/blob/main/bundles/catalog.community.json) and listed below. The built-in community source is discovery-only: `specify bundle search` and `specify bundle info` can inspect entries, but installing by ID requires explicitly adding an install-allowed catalog. Explicit catalogs use a higher default precedence than the built-in community source. To submit a bundle for review, file a [Bundle Submission](https://github.com/github/spec-kit/issues/new?template=bundle_submission.yml) issue.

| Bundle | Purpose | Role or team | Provides | Required catalogs | URL |
|--------|---------|--------------|----------|-------------------|-----|
| SicarioSpec Security & Governance Bundle | Secure-by-default governance bundle for GitHub Spec Kit. Enforces data classification, threat modeling, and code-owned verification gates. | `security-engineer` | 1 extension, 11 presets | Documented | [sicario-spec](https://github.com/dfirs1car1o/sicario-spec) |

## What to Submit

A bundle submission should include:

- A public repository with a valid `bundle.yml` manifest.
- A versioned GitHub release with a bundle artifact created by `specify bundle build`.
- Documentation that explains the intended role, installed components, required catalogs, and expected workflow.
- A proposed catalog entry with bundle metadata and component counts.
- Test evidence from a clean Spec Kit project.

## Component Resolution

A bundle catalog entry describes where to download the bundle artifact, but the bundle's component references still need to resolve when a user installs it. References can resolve from bundled components, already installed components, or active extension, preset, workflow, and step catalogs.

If your bundle depends on components that are not available from the default Spec Kit catalogs, include the required catalog URLs in the submission and in your README. Test the full install path from a clean project with those catalogs added before submitting.

For example:

```bash
specify preset catalog add https://example.com/presets.json --name example-bundle --install-allowed
specify extension catalog add https://example.com/extensions.json --name example-bundle --install-allowed
curl -L -o example-bundle-1.0.0.zip https://example.com/example-bundle-1.0.0.zip
specify bundle install ./example-bundle-1.0.0.zip

# Or install by id from an install-allowed bundle catalog.
specify bundle catalog add https://example.com/bundles.json --id example-bundle-catalog --policy install-allowed
specify bundle install example-bundle
```

## Review Scope

Maintainers check that:

- The submission fields are complete and correctly formatted.
- The release artifact and documentation URLs are reachable.
- The repository contains a `bundle.yml` manifest.
- The submission clearly identifies any required component catalogs.
- The proposed catalog entry uses the expected bundle catalog entry shape.

Maintainers do not audit the behavior of installed extensions, presets, workflows, steps, or scripts. Users should review those components before installing a community bundle.

## Updating a Bundle

To update a submitted bundle, file another [Bundle Submission](https://github.com/github/spec-kit/issues/new?template=bundle_submission.yml) issue with the new version, download URL, changed component list, and updated test evidence. Mention that the issue updates an existing bundle entry.
