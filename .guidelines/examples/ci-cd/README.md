# CI/CD Integration for Guidelines Compliance

This directory contains example CI/CD configurations for automating corporate guidelines compliance checks in your development workflow.

## Overview

Automated compliance checking provides:

- **Early detection** of guideline violations in pull requests
- **Automated fixes** for common issues
- **Compliance trends** tracked over time
- **Quality gates** to prevent non-compliant code from merging
- **Transparency** with automated reports and dashboards

## Available Integrations

### GitHub Actions

**File:** `github-actions.yml`

**Features:**

- Compliance check on PRs and pushes
- Automated PR comments with results
- Auto-fix common violations
- Weekly analytics updates
- Artifact uploads for reports

**Setup:**

```bash
# Copy to your repository
mkdir -p .github/workflows
cp github-actions.yml .github/workflows/guidelines-compliance.yml

# Commit and push
git add .github/workflows/guidelines-compliance.yml
git commit -m "ci: add guidelines compliance check"
git push
```

### GitLab CI

**File:** `gitlab-ci.yml`

**Features:**

- Compliance check on merge requests
- Auto-fix with automatic commits
- Scheduled analytics updates
- Merge request comments
- Artifact reports

**Setup:**

```bash
# Option 1: Replace existing .gitlab-ci.yml
cp gitlab-ci.yml .gitlab-ci.yml

# Option 2: Include in existing pipeline
# Add to your .gitlab-ci.yml:
include:
  - local: '.guidelines/examples/ci-cd/gitlab-ci.yml'

# Configure weekly schedule in GitLab:
# Settings > CI/CD > Schedules > New Schedule
# Cron: 0 0 * * 0 (Every Sunday at midnight)
```

### Jenkins

**File:** `Jenkinsfile`

**Features:**

- Multi-stage pipeline
- Compliance scoring
- Auto-fix on feature branches
- Analytics updates on main branch
- HTML report publishing

**Setup:**

```bash
# Option 1: Copy to repository root
cp Jenkinsfile /path/to/your/repo/

# Option 2: Reference from Jenkins
# Configure Jenkins job to use this Jenkinsfile
# Pipeline > Definition: Pipeline script from SCM
# Script Path: .guidelines/examples/ci-cd/Jenkinsfile

# Configure scheduled builds for analytics:
# Build Triggers > Build periodically
# Schedule: H 0 * * 0 (Every Sunday at midnight)
```

## Configuration

### Environment Variables

All CI/CD configurations support these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `COMPLIANCE_THRESHOLD` | Minimum compliance score (0-100) | 75 |
| `FAIL_ON_CRITICAL` | Fail build on CRITICAL violations | true |
| `FAIL_ON_HIGH` | Fail build on HIGH violations | false |
| `AUTO_FIX_ENABLED` | Enable automatic fixes | true |
| `ANALYTICS_ENABLED` | Enable analytics tracking | true |

### Customize Thresholds

Edit the CI/CD file to adjust pass/fail criteria:

```yaml
# GitHub Actions example
env:
  COMPLIANCE_THRESHOLD: 80  # Require 80/100 minimum
  FAIL_ON_HIGH: true       # Also fail on HIGH violations
```

### Notification Setup

#### GitHub Actions - Slack Notifications

Add Slack webhook to repository secrets, then add this step:

```yaml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Compliance check failed: ${{ github.event.pull_request.html_url }}"
      }
```

#### GitLab CI - Email Notifications

Configure in `.gitlab-ci.yml`:

```yaml
guidelines:compliance:
  after_script:
    - |
      if [ "$CI_JOB_STATUS" = "failed" ]; then
        echo "Compliance check failed" | mail -s "CI Failure" team@example.com
      fi
```

#### Jenkins - Email/Slack Notifications

Configure in `post` section:

```groovy
post {
    failure {
        // Email
        emailext(
            subject: "Compliance Failure: ${env.JOB_NAME}",
            body: "Check ${env.BUILD_URL}",
            to: "team@example.com"
        )

        // Slack (requires Slack Plugin)
        slackSend(
            color: 'danger',
            message: "Compliance check failed: ${env.JOB_NAME}"
        )
    }
}
```

## Workflow Examples

### Pull Request Workflow

```mermaid
graph LR
    A[Create PR] --> B[CI Triggered]
    B --> C[Run Compliance Check]
    C --> D{Violations?}
    D -->|CRITICAL| E[Block Merge]
    D -->|HIGH/MEDIUM| F[Warn Developer]
    D -->|None| G[Allow Merge]
    F --> H[Auto-Fix Available?]
    H -->|Yes| I[Apply Fixes]
    H -->|No| J[Manual Fix Required]
    I --> K[Commit Fixes]
    K --> C
```

### Main Branch Workflow

```mermaid
graph LR
    A[Merge to Main] --> B[CI Triggered]
    B --> C[Run Compliance Check]
    C --> D[Generate Report]
    D --> E[Update Analytics]
    E --> F[Commit History]
    F --> G[Send Weekly Summary]
```

## Advanced Features

### 1. Compliance Score Trending

Track compliance over time:

```bash
# In CI/CD, add:
./scripts/bash/guidelines-analytics.sh --save-history

# View trends:
./scripts/bash/guidelines-analytics.sh
```

### 2. Auto-Fix with Review

Require human review of auto-fixes:

```yaml
# Create separate branch for auto-fixes
- name: Auto-fix
  run: |
    git checkout -b autofix-${{ github.run_id }}
    ./scripts/bash/autofix-guidelines.sh
    git push origin autofix-${{ github.run_id }}

- name: Create PR for fixes
  uses: repo-sync/pull-request@v2
  with:
    source_branch: autofix-${{ github.run_id }}
    destination_branch: ${{ github.head_ref }}
    pr_title: "Auto-fix: Guidelines compliance"
```

### 3. Differential Compliance

Only check changed files:

```bash
# Get list of changed files
CHANGED_FILES=$(git diff --name-only origin/main...HEAD)

# Check only changed files (requires custom script)
./scripts/bash/check-guidelines-compliance.sh --files "$CHANGED_FILES"
```

### 4. Compliance Gates

Require specific score before deployment:

```yaml
deploy:
  stage: deploy
  script:
    - SCORE=$(jq -r '.compliance_score' compliance-report.json)
    - if [ "$SCORE" -lt 90 ]; then
        echo "Compliance score too low for production deployment"
        exit 1
      fi
    - ./deploy.sh
```

## Troubleshooting

### Issue: jq not found

**Solution:** Install jq in CI environment:

```yaml
# GitHub Actions
- run: sudo apt-get update && sudo apt-get install -y jq

# GitLab CI
before_script:
  - apt-get update && apt-get install -y jq

# Jenkins
sh 'apt-get update && apt-get install -y jq'
```

### Issue: Scripts not executable

**Solution:** Make scripts executable in CI:

```yaml
- run: chmod +x ./scripts/bash/*.sh
```

### Issue: Git push fails

**Solution:** Configure Git credentials in CI:

```yaml
# GitHub Actions - use built-in token
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.GITHUB_TOKEN }}

# GitLab CI - use CI token
- git remote set-url origin https://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.com/${CI_PROJECT_PATH}.git

# Jenkins - configure credentials
withCredentials([usernamePassword(...)]) {
  sh 'git push'
}
```

### Issue: Compliance check too slow

**Solution:** Optimize with caching:

```yaml
# GitHub Actions
- uses: actions/cache@v4
  with:
    path: .guidelines-cache
    key: guidelines-${{ hashFiles('.guidelines/**') }}

# Run incremental checks
- run: ./scripts/bash/check-guidelines-compliance.sh --incremental
```

## Best Practices

1. **Start with warnings only** - Don't block merges initially
2. **Gradually increase strictness** - Add gates as team adopts guidelines
3. **Review auto-fixes** - Ensure they align with intent
4. **Track trends** - Use analytics to measure improvement
5. **Customize reports** - Tailor output for your team's needs
6. **Test in feature branches** - Validate CI changes before main
7. **Document exceptions** - Allow overrides with justification

## Metrics and Reporting

### Daily Dashboard

View current compliance:

```bash
./scripts/bash/guidelines-analytics.sh
```

### Weekly Summary

Generate CSV for tracking:

```bash
./scripts/bash/guidelines-analytics.sh --output=csv > weekly-report.csv
```

### Historical Analysis

View trends over time:

```bash
# Show 30-day trend
./scripts/bash/guidelines-analytics.sh --show-history
```

## Support

- **Issues:** Open GitHub issue in spec-kit repository
- **Questions:** See main README.md
- **Customization:** Modify CI files for your specific needs

## See Also

- [Corporate Guidelines README](../../README.md)
- [Compliance Checker Documentation](../../../scripts/bash/check-guidelines-compliance.sh)
- [Auto-Fix Tool Documentation](../../../scripts/bash/autofix-guidelines.sh)
- [Analytics Dashboard Documentation](../../../scripts/bash/guidelines-analytics.sh)
