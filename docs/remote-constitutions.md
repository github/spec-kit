# Remote Constitutions

## Overview

The Remote Constitutions feature allows organizations to maintain a centralized catalog of project constitutions in a GitHub repository. This enables teams to easily bootstrap new projects with pre-approved, standardized governance principles and development guidelines.

## Why Remote Constitutions?

At large companies or within development teams, there are often:
- **Standard practices** that should be followed across projects
- **Compliance requirements** that must be met
- **Technology standards** for cloud environments, CICD pipelines, etc.
- **Quality guidelines** that ensure consistency across the organization

Instead of requiring developers to recreate or copy-paste these constitutions, remote constitutions allow them to:
1. Browse available constitutions from a central repository
2. Select the appropriate constitution for their project type
3. Automatically apply it during project initialization

## Setting Up a Constitutions Repository

### Repository Structure

Create a GitHub repository to store your constitutions. The recommended structure is:

```
my-constitutions-repo/
├── README.md
├── python-microservices.md
├── react-frontend.md
├── golang-api.md
├── data-pipeline.md
└── mobile-app.md
```

Or organize them in directories:

```
my-constitutions-repo/
├── README.md
├── backend/
│   ├── python-microservices.md
│   ├── golang-api.md
│   └── java-spring.md
├── frontend/
│   ├── react-spa.md
│   └── vue-pwa.md
└── data/
    ├── batch-pipeline.md
    └── streaming-pipeline.md
```

### Constitution File Format

Each constitution file should be a markdown file (`.md`) following the structure defined in the spec-kit template. See `memory/constitution.md` in any initialized project for the template format.

Example constitution for a Python microservices project:

```markdown
# Python Microservices Constitution

## Core Principles

### I. API-First Design
Every microservice must define its API contract using OpenAPI 3.0 specification before implementation begins. APIs must be versioned and maintain backward compatibility.

### II. Test-Driven Development (NON-NEGOTIABLE)
- Unit test coverage must be >= 80%
- Integration tests required for all API endpoints
- Tests must pass before merging to main branch

### III. Observability
All services must implement:
- Structured logging (JSON format)
- Distributed tracing (OpenTelemetry)
- Metrics exposure (Prometheus format)
- Health check endpoints (/health, /ready)

### IV. Cloud Native Standards
Services must:
- Run in Docker containers
- Follow 12-factor app principles
- Use Kubernetes for orchestration
- Store configs in environment variables

### V. Security Requirements
- All external communications must use TLS
- Secrets managed via HashiCorp Vault
- No credentials in code or config files
- Regular dependency scanning for vulnerabilities

## Development Workflow

### Code Review Process
- Minimum 2 approvers required
- Architecture review for new services
- Security review for authentication changes

### CI/CD Pipeline
- Automated testing on every PR
- Automated security scanning
- Blue-green deployments for zero downtime

## Governance

This constitution supersedes all other development practices. Amendments require approval from the architecture steering committee and must be documented with rationale and migration plans.

**Version**: 1.0.0 | **Ratified**: 2025-01-15 | **Last Amended**: 2025-01-15
```

### Access Control

- **Public repositories**: Anyone can access the constitutions
- **Private repositories**: Users need a GitHub token with appropriate permissions

## Using Remote Constitutions

### Listing Available Constitutions

To see what constitutions are available in a repository:

```bash
specify list-constitutions myorg/constitutions-repo
```

With a custom path:

```bash
specify list-constitutions myorg/constitutions-repo --path backend
```

From a specific branch:

```bash
specify list-constitutions myorg/constitutions-repo --branch develop
```

For private repositories:

```bash
specify list-constitutions myorg/private-constitutions --github-token $GITHUB_TOKEN
```

Or set the token as an environment variable:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
specify list-constitutions myorg/private-constitutions
```

### Applying a Constitution During Init

#### Interactive Selection

Browse and select interactively:

```bash
specify init my-project --constitution-repo myorg/constitutions --constitution-interactive
```

#### Direct Specification

Specify the constitution name directly:

```bash
specify init my-project \
  --constitution-repo myorg/constitutions \
  --constitution-name python-microservices
```

#### With Custom Path

If constitutions are in a subdirectory:

```bash
specify init my-project \
  --constitution-repo myorg/constitutions \
  --constitution-path backend \
  --constitution-name python-microservices
```

#### From Non-Main Branch

Use a specific branch:

```bash
specify init my-project \
  --constitution-repo myorg/constitutions \
  --constitution-branch develop \
  --constitution-name experimental-python
```

#### Complete Example with All Options

```bash
specify init my-new-api \
  --ai claude \
  --script sh \
  --constitution-repo mycompany/engineering-standards \
  --constitution-path constitutions/backend \
  --constitution-name python-microservices \
  --github-token $GITHUB_TOKEN
```

## Best Practices

### For Constitution Repository Maintainers

1. **Clear Naming**: Use descriptive, hyphenated names for constitution files
   - ✅ `python-microservices.md`
   - ✅ `react-spa-enterprise.md`
   - ❌ `const1.md`
   - ❌ `v2.md`

2. **Version Your Constitutions**: Include version numbers in the constitution content itself

3. **Add a README**: Create a comprehensive README.md explaining:
   - Purpose of each constitution
   - When to use which constitution
   - How to contribute updates
   - Change approval process

4. **Use Examples**: Include practical examples in your constitutions

5. **Keep Them Updated**: Regular reviews to ensure constitutions reflect current practices

6. **Document Changes**: Use Git commit messages to explain constitution changes

### For Constitution Users

1. **Review Before Using**: Always review the constitution content before applying it

2. **Customize as Needed**: Remote constitutions are starting points; customize them for your specific project needs after initialization

3. **Stay Updated**: Periodically check if your constitution source has updates

4. **Provide Feedback**: Report issues or suggest improvements to constitution maintainers

## Security Considerations

### GitHub Tokens

When using private repositories, you'll need a GitHub Personal Access Token:

1. **Create a token** at https://github.com/settings/tokens
2. **Required scopes**: `repo` (for private repos) or `public_repo` (for public repos)
3. **Store securely**: Use environment variables, never hardcode tokens

```bash
# Set as environment variable
export GITHUB_TOKEN="ghp_your_token_here"

# Or pass directly (less secure)
specify init my-project --constitution-repo myorg/repo --github-token "ghp_your_token_here"
```

### Constitution Content Security

- **Review constitutions**: Ensure they come from trusted sources
- **Check for secrets**: Constitutions should never contain credentials or API keys
- **Validate practices**: Ensure recommended practices align with your security policies

## Troubleshooting

### "Repository or path not found"

**Cause**: The repository URL or path is incorrect, or you don't have access.

**Solutions**:
- Verify the repository exists: `https://github.com/owner/repo`
- Check if it's private and you need a token
- Verify the path within the repository is correct

### "No constitutions found"

**Cause**: No `.md` files in the specified path.

**Solutions**:
- Check the `--path` parameter
- Verify files have `.md` extension
- Use `list-constitutions` command to see what's available

### "Constitution 'name' not found"

**Cause**: The specified constitution name doesn't match any files.

**Solutions**:
- Run `list-constitutions` to see available names
- Constitution names are file names without the `.md` extension
- Check for typos in the name

### Rate Limiting

**Cause**: GitHub API has rate limits (60 requests/hour for unauthenticated users).

**Solution**:
- Use a GitHub token to get higher limits (5000 requests/hour)
- Wait before retrying

## Examples

### Example 1: Company-Wide Standards

**Scenario**: Your company has standardized on specific architectures and practices.

**Setup**: Create a `engineering-standards` repository with constitutions for each tech stack.

**Usage**:
```bash
# New Python microservice
specify init payment-service \
  --constitution-repo acme-corp/engineering-standards \
  --constitution-name python-microservices

# New React frontend
specify init customer-portal \
  --constitution-repo acme-corp/engineering-standards \
  --constitution-name react-spa-enterprise
```

### Example 2: Team-Specific Templates

**Scenario**: Your data engineering team has specific requirements.

**Setup**: Create a `data-team-constitutions` repository with pipelines, schemas, etc.

**Usage**:
```bash
specify init customer-analytics \
  --constitution-repo data-team/data-team-constitutions \
  --constitution-name spark-batch-pipeline \
  --constitution-interactive
```

### Example 3: Open Source Best Practices

**Scenario**: You want to share best practices publicly.

**Setup**: Create a public repository with example constitutions.

**Usage**:
```bash
# Anyone can use without authentication
specify init my-open-source-lib \
  --constitution-repo awesome-org/spec-kit-constitutions \
  --constitution-name python-library-best-practices
```

## Integration with CI/CD

You can automate project initialization with remote constitutions in your CI/CD pipelines:

```yaml
# GitHub Actions example
name: Bootstrap New Service

on:
  workflow_dispatch:
    inputs:
      service_name:
        description: 'Name of the new service'
        required: true
      constitution:
        description: 'Constitution to use'
        required: true
        type: choice
        options:
          - python-microservices
          - golang-api
          - nodejs-service

jobs:
  bootstrap:
    runs-on: ubuntu-latest
    steps:
      - name: Install specify-cli
        run: uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
      
      - name: Initialize project
        run: |
          specify init ${{ inputs.service_name }} \
            --ai copilot \
            --constitution-repo ${{ github.repository_owner }}/engineering-standards \
            --constitution-name ${{ inputs.constitution }} \
            --github-token ${{ secrets.GITHUB_TOKEN }}
      
      - name: Create repository
        # ... additional steps to create and push to new repo
```

## Future Enhancements

Potential future improvements to this feature:

- **Constitution metadata**: Support for metadata files describing constitutions
- **Constitution search**: Search within constitution content
- **Version locking**: Pin specific versions of constitutions
- **Constitution validation**: Validate constitution format before applying
- **Diff preview**: Show what will change when applying a constitution
- **Constitution inheritance**: Base constitutions that extend others
- **Custom protocols**: Support for other sources beyond GitHub (GitLab, Bitbucket, etc.)

## Contributing

To contribute improvements to the remote constitutions feature, see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Related Documentation

- [Installation](installation.md)
- [Quickstart](quickstart.md)
- [Constitution Command](../templates/commands/constitution.md)
