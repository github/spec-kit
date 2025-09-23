# Spec Kit - Azure DevOps Extension

AI-powered specification management workflows integrated into Azure DevOps.

## Features

### 🎯 Project Hub
- **Spec Kit Hub** under Boards/Repos for running `/specify`, `/plan`, `/tasks` workflows
- Queue pipelines and track execution status
- One-click repository seeding with `.github/prompts/**` and `.specify/**` assets
- Comprehensive run history with cost tracking

### 📝 Work Item Integration
- **Spec Assist Tab** on User Stories & Features
- Generate specifications, create plans, and create tasks with AI assistance
- Publish artifacts directly to Wiki
- Seamless integration with Azure Boards workflow

### 📊 Dashboard Widgets
- **Spec Throughput**: Track specification generation velocity
- **Lead Time**: Monitor time from `/specify` to merge
- **AI vs Human Effort**: Compare efficiency metrics
- **Guardrail Coverage**: Ensure compliance with specification standards

### 🔗 LLM Service Connections
- Project-level **Spec Kit LLM** service connection type
- Support for multiple LLM providers (OpenAI, Azure OpenAI, etc.)
- Secure API key storage and regional configuration
- Temperature controls and model selection

### 🚀 Pipeline Tasks
- **SpecKit.Seed**: Copy assets into repository and create PR
- **SpecKit.Run**: Execute `/specify`, `/plan`, `/tasks` workflows on build agents
- Cross-platform support (Windows + Linux)

### 🔄 Repository Integration
- Automated PR to Work Item state synchronization
- Branch lifecycle tracking (created → In Progress, PR → In Review, merged → Done)
- Artifact storage in `/specs/**` and Wiki integration

### 🛡️ Security & Audit
- Minimal OAuth scopes with secure credential storage
- Comprehensive audit trails with redacted prompt/response logging
- Cost and latency telemetry with privacy controls
- Per-project dashboard analytics

## Installation

1. Install the extension from the Azure DevOps Marketplace
2. Configure LLM service connections in Project Settings
3. Set up default LLM preferences per project
4. Start using Spec Kit workflows in your work items!

## Configuration

### Service Connection Setup
1. Go to Project Settings → Service connections
2. Create a new "Spec Kit LLM" connection
3. Configure your LLM provider details:
   - Base URL
   - Model name
   - API token
   - Region (optional)
   - Temperature cap (optional)

### Project Settings
1. Navigate to the Spec Kit hub
2. Configure default LLM per project
3. Set up repository seeding preferences
4. Configure audit and telemetry settings

## Usage

### Quick Start
1. Open a User Story or Feature work item
2. Click the "Spec Assist" tab
3. Use the workflow buttons:
   - **Generate Spec**: Run `/specify` workflow
   - **Create Plan**: Execute `/plan` workflow
   - **Create Tasks**: Generate `/tasks` breakdown
   - **Publish to Wiki**: Save artifacts to project wiki

### Repository Seeding
1. Go to the Spec Kit hub
2. Click "Seed Repository"
3. Review the assets to be added
4. Create a new branch with Spec Kit configuration
5. Open PR for team review

### Pipeline Integration
Add Spec Kit tasks to your build pipelines:

```yaml
- task: SpecKitSeed@1
  displayName: 'Seed Spec Kit Assets'
  inputs:
    targetBranch: 'main'
    createPR: true

- task: SpecKitRun@1
  displayName: 'Run Spec Kit Workflows'
  inputs:
    workflow: 'specify'
    workItemId: $(System.PullRequest.PullRequestId)
    llmConnection: 'MyLLMConnection'
```

## Support

- [GitHub Repository](https://github.com/AI-Pundit/spec-kit)
- [Issue Tracker](https://github.com/AI-Pundit/spec-kit/issues)
- [Documentation](https://github.com/AI-Pundit/spec-kit/wiki)

## License

MIT License - see [LICENSE](LICENSE) for details.