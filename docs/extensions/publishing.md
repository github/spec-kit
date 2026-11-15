# Extension Publishing Guide

This guide explains how to publish your extension to the Spec Kit extension catalog, making it discoverable by `specify extension search`.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Prepare Your Extension](#prepare-your-extension)
3. [Submit to Catalog](#submit-to-catalog)
4. [Release Workflow](#release-workflow)
5. [Best Practices](#best-practices)

---

## Prerequisites

Before publishing an extension, ensure you have:

1. **Valid Extension**: A working extension with a valid `extension.yml` manifest
2. **GitHub Repository**: Extension hosted in a public GitHub repository for
   community catalog submission
3. **Documentation**: README.md with installation and usage instructions
4. **License**: Open source license file (MIT, Apache 2.0, etc.)
5. **Versioning**: Semantic versioning (e.g., 1.0.0)
6. **Testing**: Extension tested on real projects

---

## Prepare Your Extension

### 1. Extension Structure

Ensure your extension follows the standard structure:

```text
your-extension/
├── extension.yml              # Required: Extension manifest
├── README.md                  # Required: Documentation
├── LICENSE                    # Required: License file
├── CHANGELOG.md               # Recommended: Version history
├── .gitignore                 # Recommended: Git ignore rules
│
├── commands/                  # Extension commands
│   ├── command1.md
│   └── command2.md
│
├── config-template.yml        # Config template (if needed)
│
└── docs/                      # Additional documentation
    ├── usage.md
    └── examples/
```

### 2. extension.yml Validation

Verify your manifest is valid:

```yaml
schema_version: "1.0"

extension:
  id: "your-extension"           # Unique lowercase-hyphenated ID
  name: "Your Extension Name"     # Human-readable name
  version: "1.0.0"                # Semantic version
  description: "Brief description (one sentence)"
  author: "Your Name or Organization"
  repository: "https://github.com/your-org/spec-kit-your-extension"
  license: "MIT"
  homepage: "https://github.com/your-org/spec-kit-your-extension"

requires:
  speckit_version: ">=0.1.0"    # Required spec-kit version

provides:
  commands:                       # List all commands
    - name: "speckit.your-extension.command"
      file: "commands/command.md"
      description: "Command description"

tags:                             # 2-5 relevant tags
  - "category"
  - "tool-name"
```

**Validation Checklist**:

- ✅ `id` starts with a lowercase letter and otherwise contains only lowercase
  letters, digits, or hyphens (`^[a-z][a-z0-9-]*$` for community submissions)
- ✅ `version` follows semantic versioning (X.Y.Z)
- ✅ `description` is concise (under 200 characters for community submissions)
- ✅ `repository` URL is valid and public
- ✅ All command files exist in the extension directory
- ✅ Tags are lowercase and descriptive

### 3. Create GitHub Release

Create a GitHub release for your extension version:

```bash
# Tag the release
git tag v1.0.0
git push origin v1.0.0

# Create release on GitHub
# Go to: https://github.com/your-org/spec-kit-your-extension/releases/new
# - Tag: v1.0.0
# - Title: v1.0.0 - Release Name
# - Description: Changelog/release notes
```

The release archive URL will be:

```text
https://github.com/your-org/spec-kit-your-extension/archive/refs/tags/v1.0.0.zip
```

### 4. Test Installation

Test that users can install from your release:

```bash
# Test dev installation
specify extension add --dev /path/to/your-extension

# Test from GitHub archive
specify extension add <extension-name> --from https://github.com/your-org/spec-kit-your-extension/archive/refs/tags/v1.0.0.zip
```

---

## Submit to Catalog

### Understanding the Catalogs

Spec Kit uses a catalog stack with built-in install and discovery sources.
See [Extension catalogs](catalogs.md) for configuration, release metadata,
and trust boundaries.

**For extension publishing**: All community extensions are listed in
`extensions/catalog.community.json`. Users must vet a release before installing
it directly or copying its entry into their own trusted catalog.

### How to Submit

To submit your extension to the community catalog, file a new issue using the **[Extension Submission](https://github.com/github/spec-kit/issues/new?template=extension_submission.yml)** template. The template collects all required metadata, including:

- Extension ID, name, and version
- Description, author, and license
- Repository, download URL, and documentation links
- Required Spec Kit version and any tool dependencies
- Number of commands and hooks
- Tags and key features
- Testing confirmation

> [!IMPORTANT]
> Do **not** open a pull request directly to edit `extensions/catalog.community.json`. All community extension submissions must go through the issue template. Submissions that do not use the issue template will be closed, and you will be asked to resubmit using it.

### Submission validation

Community submissions are stricter than the general extension runtime:

- The extension ID must match `^[a-z][a-z0-9-]*$`.
- The version must be `X.Y.Z` with digits only and no `v` prefix. The release
  tag may include a `v` prefix or a scope, but its version must match the
  submitted version.
- The repository must be public and contain `extension.yml`, `README.md`, and
  `LICENSE`.
- The download URL must belong to that same GitHub repository and use either
  `https://github.com/<owner>/<repo>/archive/refs/tags/<tag>.zip` or
  `https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>.zip`.
  Floating `releases/latest/` URLs are rejected.
- The archive must be accessible. If a SHA-256 digest is submitted, it must
  match the downloaded archive. The automation records the downloaded archive's
  digest in the proposed catalog entry even when one was not submitted.

These are metadata and archive-provenance checks, not a review of extension
code. Other public hosting and private releases can be used with a catalog you
control, but are not accepted through this community submission process.

### What Happens After You Submit

1. GitHub applies the `triage-must-have` verdict when the issue is opened through the Extension Submission form. This intake automation is specific to extension submissions and does not change the manual triage rubric for other issues.
2. A maintainer reviews the issue during issue triage and applies the separate `extension-submission` label, which starts the automated catalog validation. On this public repository, contributors cannot apply that label themselves, so there is nothing to label or re-request — the issue simply waits in triage.
3. The automated workflow validates the submission and, when validation passes, updates `extensions/catalog.community.json` and `docs/community/extensions.md` in a draft pull request
4. A maintainer reviews the generated pull request and merges it when approved
5. Your extension becomes discoverable via `specify extension search`

### What Maintainers Check

- The catalog entry fields are complete and correctly formatted
- The download URL is accessible
- The repository exists and contains an `extension.yml` manifest

> [!NOTE]
> Maintainers do **not** review, audit, or test the extension code itself.

### Updating an Existing Extension

To update an extension that is already in the catalog (e.g., for a new version), file a new **[Extension Submission](https://github.com/github/spec-kit/issues/new?template=extension_submission.yml)** issue with the updated version, download URL, and any other changed fields. Mention in the issue that this is an update to an existing entry.

---

## Release Workflow

### Publishing New Versions

When releasing a new version:

1. **Update version** in `extension.yml`:

   ```yaml
   extension:
     version: "1.1.0"  # Updated version
   ```

2. **Update CHANGELOG.md**:

   ```markdown
   ## [1.1.0] - 2026-02-15

   ### Added
   - New feature X

   ### Fixed
   - Bug fix Y
   ```

3. **Create GitHub release**:

   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   # Create release on GitHub
   ```

4. **File an update submission** using the [Extension Submission](https://github.com/github/spec-kit/issues/new?template=extension_submission.yml) template with the new version and download URL. Mention in the issue that this is an update to an existing entry.

---

## Best Practices

### Extension Design

1. **Single Responsibility**: Each extension should focus on one tool/integration
2. **Clear Naming**: Use descriptive, unambiguous names
3. **Minimal Dependencies**: Avoid unnecessary dependencies
4. **Backward Compatibility**: Follow semantic versioning strictly

### Documentation

1. **README.md Structure**:
   - Overview and features
   - Installation instructions
   - Configuration guide
   - Usage examples
   - Troubleshooting
   - Contributing guidelines

2. **Command Documentation**:
   - Clear description
   - Prerequisites listed
   - Step-by-step instructions
   - Error handling guidance
   - Examples

3. **Configuration**:
   - Provide template file
   - Document all options
   - Include examples
   - Explain defaults

### Security

1. **Input Validation**: Validate all user inputs
2. **No Hardcoded Secrets**: Never include credentials
3. **Safe Dependencies**: Only use trusted dependencies
4. **Audit Regularly**: Check for vulnerabilities

### Maintenance

1. **Respond to Issues**: Acknowledge and investigate reports as maintainer
   capacity permits
2. **Regular Updates**: Keep dependencies updated
3. **Changelog**: Maintain detailed changelog
4. **Deprecation**: Give advance notice for breaking changes

### Community

1. **License**: Use permissive open-source license (MIT, Apache 2.0)
2. **Contributing**: Welcome contributions
3. **Code of Conduct**: Be respectful and inclusive
4. **Support**: Provide ways to get help (issues, discussions, email)

---

## FAQ

### Q: Can I publish private/proprietary extensions?

A: The main catalog is for public extensions only. For private extensions:

- Host your own catalog.json file
- After vetting its releases, users add your catalog as an install source:

  ```bash
  specify extension catalog add https://your-domain.com/catalog.json \
    --name private-catalog --install-allowed
  ```

### Q: How long does review take?

A: Submissions wait for maintainer triage, automated validation, and review of
the generated catalog pull request. There is no promised turnaround.

### Q: What if my extension is rejected?

A: You'll receive feedback on what needs to be fixed. Make the changes and resubmit.

### Q: Can I update my extension anytime?

A: Yes, file a new [Extension Submission](https://github.com/github/spec-kit/issues/new?template=extension_submission.yml) issue with the updated version and download URL. Mention that it is an update to an existing entry.

### Q: Do I need to be verified to be in the catalog?

A: No. All community extensions are listed in the catalog once their submission is reviewed and accepted.

### Q: Can extensions have paid features?

A: Extensions should be free and open-source. Commercial support/services are allowed, but core functionality must be free.

---

## Support

- **Catalog Issues**: <https://github.com/github/spec-kit/issues>
- **Extension Submission**: [Submit or update a community extension](https://github.com/github/spec-kit/issues/new?template=extension_submission.yml)
- **Development Guide**: See [Developing extensions](developing.md)
- **Community**: Discussions and Q&A

---

## Catalog metadata

Use the canonical [catalog entry schema](catalogs.md#catalog-entry-schema),
including [historical release records](catalogs.md#historical-releases) when
advertising older versions. For community submissions, provide all descriptive
fields collected by the issue form.

### Valid Tags

Recommended tag categories:

- **Integration**: jira, linear, github, gitlab, azure-devops
- **Category**: issue-tracking, vcs, ci-cd, documentation, testing
- **Platform**: atlassian, microsoft, google
- **Feature**: automation, reporting, deployment, monitoring

Use 2-5 tags that best describe your extension.

---

*Last Updated: 2026-01-28*
*Catalog Format Version: 1.0*

## See also

- [Developing extensions](developing.md)
- [Extension API reference](api.md)
- [Extension catalogs](catalogs.md)
- [Extension CLI reference](cli.md)
- [Community extensions](../community/extensions.md)
