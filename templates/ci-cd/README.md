# CI/CD Integration Templates

These templates provide automated codebase analysis integration for popular CI/CD platforms.

## Available Templates

### GitHub Actions

**File**: `github-actions-analysis.yml`

**Features**:

- Runs on pull requests, pushes to main, and weekly schedule
- Posts analysis summary as PR comments
- Fails build on critical vulnerabilities
- Uploads reports as artifacts
- Tracks metrics over time

**Setup**:

```bash
cp templates/ci-cd/github-actions-analysis.yml .github/workflows/codebase-analysis.yml
git add .github/workflows/codebase-analysis.yml
git commit -m "Add automated codebase analysis"
git push
```

**Configuration**:

Edit the `env` section to customize:

- `ANALYSIS_DEPTH`: QUICK, STANDARD, or COMPREHENSIVE
- `PYTHON_VERSION`: Python version to use

### GitLab CI

**File**: `gitlab-ci-analysis.yml`

**Features**:

- Runs on merge requests and main branch
- Posts comments to merge requests
- Security gate blocks pipelines on vulnerabilities
- Weekly comprehensive analysis
- Metrics as GitLab artifacts

**Setup**:

Option 1 - Include in existing `.gitlab-ci.yml`:

```yaml
include:
  - local: 'templates/ci-cd/gitlab-ci-analysis.yml'
```

Option 2 - Copy to `.gitlab-ci.yml`:

```bash
cat templates/ci-cd/gitlab-ci-analysis.yml >> .gitlab-ci.yml
git add .gitlab-ci.yml
git commit -m "Add automated codebase analysis"
git push
```

**Configuration**:

Edit `variables` section to customize depth and Python version.

### Jenkins

**File**: `jenkins-pipeline.groovy`

**Features**:

- Parameterized builds
- Configurable security gate
- HTML report publishing
- Weekly scheduled runs
- Email notifications (optional)

**Setup**:

1. Create new Pipeline job in Jenkins
2. Configure Pipeline script from SCM
3. Point to this repository
4. Set Script Path to `templates/ci-cd/jenkins-pipeline.groovy`
5. Save and run

**OR** copy content to Pipeline script section.

**Configuration**:

Parameters available in job configuration:

- `ANALYSIS_DEPTH`: QUICK, STANDARD, COMPREHENSIVE
- `FAIL_ON_VULNERABILITIES`: Block build on security issues

## Common Features

All templates provide:

- **Automated analysis** on code changes
- **Report generation** (analysis-report.md, decision-matrix.md)
- **Metrics tracking** (JSON output for dashboards)
- **Security scanning** (vulnerable dependency detection)
- **Artifact preservation** (30-day retention)

## Customization

### Analysis Depth

- **QUICK** (30 min): Basic scan, critical issues only
- **STANDARD** (2-4 hours): Comprehensive analysis [RECOMMENDED]
- **COMPREHENSIVE** (1-2 days): Deep analysis with all features

### Focus Areas

To analyze specific areas only, add `--focus` parameter:

```bash
--focus SECURITY              # Security vulnerabilities only
--focus DEPENDENCIES          # Dependency health only
--focus PERFORMANCE           # Performance bottlenecks only
--focus ARCHITECTURE          # Architecture and code quality only
```

Example in GitHub Actions:

```yaml
- name: Run analysis
  run: |
    /tmp/spec-kit/scripts/bash/analyze-project.sh \
      ${{ github.workspace }} \
      --depth QUICK \
      --focus SECURITY,DEPENDENCIES \
      --output analysis-results
```

## Security Considerations

### Failing Builds on Vulnerabilities

All templates include optional security gates that fail the build when vulnerable dependencies are detected.

**GitHub Actions**: Automatic, controlled by final step

**GitLab CI**: Controlled by `security_gate` job

**Jenkins**: Controlled by `FAIL_ON_VULNERABILITIES` parameter

### Required Permissions

**GitHub Actions**:

- `contents: read` - Read repository
- `pull-requests: write` - Post PR comments

**GitLab CI**:

- CI/CD token with `api` scope (for MR comments)

**Jenkins**:

- Agent with Python 3.11+ and Git

## Viewing Results

### Artifacts

All platforms save analysis results as artifacts:

- `analysis-report.md` - Main comprehensive report
- `upgrade-plan.md` - Step-by-step upgrade instructions (if applicable)
- `recommended-constitution.md` - Project principles (if applicable)
- `decision-matrix.md` - Stakeholder comparison table
- `metrics-summary.json` - Machine-readable metrics

### Metrics Tracking

Track metrics over time by storing `metrics-summary.json`:

**GitHub Actions** - Extend with metrics storage:

```yaml
- name: Upload to metrics DB
  run: |
    curl -X POST https://metrics.example.com/api/analysis \
      -H "Content-Type: application/json" \
      -d @analysis-results/metrics-summary.json
```

**GitLab CI** - Use GitLab metrics:

```yaml
artifacts:
  reports:
    metrics: analysis-results/metrics-summary.json
```

## Notifications

### Email Notifications

**Jenkins** - Uncomment email sections in pipeline:

```groovy
emailext (
    subject: "Codebase Analysis: ${currentBuild.result}",
    body: "View reports: ${env.BUILD_URL}",
    to: "team@example.com"
)
```

### Slack/Teams

Add webhook notifications:

**GitHub Actions** - Add to workflow:

```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Codebase analysis complete'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Troubleshooting

### Analysis Fails

1. Check Python version (3.11+ required)
2. Ensure project path is correct
3. Check for sufficient disk space
4. Review agent/runner logs

### Missing Tools

Optional but recommended:

```bash
# Install cloc for code metrics
sudo apt-get install cloc

# Install pip-audit for Python security
pip install pip-audit

# Install npm for Node.js analysis
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Timeout Issues

For very large codebases (>500K LOC):

1. Use `QUICK` depth initially
2. Use checkpointing (see checkpoint.py)
3. Increase CI/CD timeout limits
4. Run comprehensive analysis manually/scheduled only

## Support

Issues or questions? Open an issue:
<https://github.com/veerabhadra-ponna/spec-kit-smart/issues>
