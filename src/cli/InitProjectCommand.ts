import { Command } from 'commander';
import chalk from 'chalk';
import * as fs from 'fs-extra';
import * as path from 'path';
import { AIModelType } from '@models/ProjectConfig';

interface InitOptions {
  here?: boolean;
  ai?: AIModelType;
  script?: 'sh' | 'ps';
  ignoreAgentTools?: boolean;
  force?: boolean;
}

export class InitProjectCommand {
  create(): Command {
    return new Command('init')
      .argument('[project-name]', 'Name of the project to initialize')
      .option('--here', 'Initialize in the current directory')
      .option('--ai <type>', 'AI agent type (claude, gemini, copilot)')
      .option('--script <type>', 'Script type (sh, ps)', 'sh')
      .option('--ignore-agent-tools', 'Skip agent tools validation')
      .option('--force', 'Overwrite existing spec-kit configuration')
      .description('Initialize a new spec-kit project')
      .action((projectName, options) => this.execute(projectName, options));
  }

  async execute(projectName: string | undefined, options: InitOptions): Promise<void> {
    try {
      console.log(chalk.blue('🚀 Initializing spec-kit project...\n'));

      // Validate arguments
      if (!projectName && !options.here) {
        console.error(chalk.red('❌ Please specify a project name or use --here flag'));
        console.log(chalk.yellow('\nExamples:'));
        console.log('  specify init my-project');
        console.log('  specify init --here');
        process.exit(1);
      }

      // Determine target directory
      let targetDir: string;
      let projectNameForConfig: string;

      if (options.here) {
        targetDir = process.cwd();
        projectNameForConfig = path.basename(targetDir);
        console.log(chalk.cyan(`📍 Initializing in current directory: ${targetDir}`));
      } else if (projectName) {
        targetDir = path.join(process.cwd(), projectName);
        projectNameForConfig = projectName;
        console.log(chalk.cyan(`📍 Creating new project: ${projectName}`));
      } else {
        throw new Error('Invalid arguments');
      }

      // Check if directory exists (for new projects)
      if (!options.here && fs.existsSync(targetDir)) {
        if (!options.force) {
          console.error(chalk.red(`❌ Directory ${projectName} already exists`));
          console.log(chalk.yellow('Use --force to overwrite existing directory'));
          process.exit(1);
        }
      }

      // Create directory if needed
      if (!options.here) {
        await fs.ensureDir(targetDir);
      }

      // Create basic spec-kit structure
      await this.createBasicStructure(targetDir, projectNameForConfig, options);

      // Success message
      console.log(chalk.green('\n✅ Spec-kit project initialized successfully!\n'));

      // Show next steps
      console.log(chalk.white('📋 Next steps:'));
      if (!options.here) {
        console.log(`  1. cd ${projectName}`);
      } else {
        console.log('  1. You\'re ready to go!');
      }
      console.log('  2. Start with: /specify <your-feature-description>');
      console.log('  3. Then use: /plan and /tasks');
      console.log('  4. Track progress with: specify track-tasks enable');

      console.log(chalk.white('\n🔧 Available commands:'));
      console.log('  specify detect-project   - Validate project setup');
      console.log('  specify list-models      - See available AI models');
      console.log('  specify switch-model     - Change AI model');
      console.log('  specify track-tasks      - Manage task tracking');

      console.log(chalk.gray('\nRun "specify --help" for more information'));

    } catch (error: any) {
      console.error(chalk.red(`❌ Failed to initialize project: ${error.message}`));
      process.exit(1);
    }
  }

  private async createBasicStructure(targetDir: string, projectName: string, options: InitOptions): Promise<void> {
    console.log(chalk.cyan('📂 Creating project structure...'));

    // Create .specify directory structure
    const specifyDir = path.join(targetDir, '.specify');
    await fs.ensureDir(specifyDir);
    await fs.ensureDir(path.join(specifyDir, 'scripts'));
    await fs.ensureDir(path.join(specifyDir, 'scripts', 'bash'));
    await fs.ensureDir(path.join(specifyDir, 'scripts', 'powershell'));
    await fs.ensureDir(path.join(specifyDir, 'state'));
    await fs.ensureDir(path.join(specifyDir, 'templates'));
    await fs.ensureDir(path.join(specifyDir, 'memory'));

    // Create AI tool configuration directories
    await this.setupAIToolCommands(targetDir, options.ai || 'claude');

    // Create specs directory
    const specsDir = path.join(targetDir, 'specs');
    await fs.ensureDir(specsDir);

    // Create basic configuration
    const aiModel = options.ai || 'claude';
    const config = {
      projectId: `proj_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: projectName,
      aiModel,
      version: '0.1.0',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      specDirectory: specsDir,
      configPath: path.join(specifyDir, 'config.json'),
      isInitialized: true,
      migrationHistory: []
    };

    // Write configuration
    const configPath = path.join(specifyDir, 'config.json');
    await fs.writeJSON(configPath, config, { spaces: 2 });

    // Create README for specs directory
    const specsReadme = `# Specifications Directory

This directory contains all feature specifications, implementation plans, and task breakdowns.

## Structure

Each feature should have its own directory with the following structure:

\`\`\`
specs/
├── 001-feature-name/
│   ├── spec.md          # Feature specification
│   ├── plan.md          # Implementation plan
│   ├── tasks.md         # Task breakdown
│   ├── research.md      # Research notes (optional)
│   ├── data-model.md    # Data model (if applicable)
│   ├── quickstart.md    # Quick start guide (optional)
│   └── contracts/       # API contracts and schemas
│       ├── api.yaml
│       └── schema.json
└── README.md            # This file
\`\`\`

## Creating New Specifications

Use the AI agent commands:

1. \`/specify <feature-description>\` - Create a new specification
2. \`/plan <feature-name>\` - Generate implementation plan
3. \`/tasks <feature-name>\` - Break down into tasks

## Naming Convention

Use the format: \`NNN-feature-name\` where:
- \`NNN\` is a zero-padded sequence number (001, 002, etc.)
- \`feature-name\` is a kebab-case description
`;

    await fs.writeFile(path.join(specsDir, 'README.md'), specsReadme);

    // Create project README if it doesn't exist
    const readmePath = path.join(targetDir, 'README.md');
    if (!await fs.pathExists(readmePath)) {
      const projectReadme = `# ${projectName}

## Overview

This project uses hjLabs spec-kit for specification-driven development with AI assistance.

## Getting Started

### Prerequisites

- Node.js 16+
- Git
- AI Agent: ${aiModel}

### Development Workflow

1. **Specify**: Create feature specifications using \`/specify\`
2. **Plan**: Generate implementation plans using \`/plan\`
3. **Tasks**: Break down into actionable tasks using \`/tasks\`
4. **Implement**: Follow the generated plan and tasks
5. **Track**: Monitor progress with task tracking

### Available Commands

- \`specify detect-project\` - Validate project setup
- \`specify list-models\` - See available AI models
- \`specify switch-model <type>\` - Change AI model
- \`specify track-tasks <action>\` - Manage task tracking

## Project Structure

- \`specs/\` - Feature specifications and plans
- \`.specify/\` - Configuration and automation scripts
- \`README.md\` - This file

## AI Model Configuration

Current AI Model: **${aiModel}**

Switch models with:
\`\`\`bash
specify switch-model claude    # For Claude
specify switch-model gemini    # For Google Gemini
specify switch-model copilot   # For GitHub Copilot
\`\`\`

## Contributing

1. Create specifications before implementing
2. Follow the generated implementation plans
3. Track progress using the task system
4. Update documentation as needed

---

*Generated by hjLabs spec-kit*
`;
      await fs.writeFile(readmePath, projectReadme);
    }

    // Create .gitignore if it doesn't exist
    const gitignorePath = path.join(targetDir, '.gitignore');
    if (!await fs.pathExists(gitignorePath)) {
      const gitignoreContent = `# Spec-kit state files
.specify/state/
*.tmp
*.log

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# Dependency directories
node_modules/
.npm
.yarn

# Build outputs
dist/
build/
*.tgz

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
`;
      await fs.writeFile(gitignorePath, gitignoreContent);
    }

    console.log(chalk.green('✅ Project structure created'));
  }

  private async setupAIToolCommands(targetDir: string, aiModel: AIModelType): Promise<void> {
    // Find the spec-kit installation directory (where this script is running from)
    const currentRepoRoot = this.findSpecKitRoot();

    // Only copy files if we're not initializing in the spec-kit repo itself
    if (path.resolve(targetDir) !== path.resolve(currentRepoRoot)) {
      // Copy .specify templates and scripts
      await this.copySpecifyAssets(targetDir, currentRepoRoot);
    } else {
      console.log(chalk.yellow('📍 Initializing in spec-kit repo, skipping asset copy'));
    }

    // Setup AI-specific commands
    switch (aiModel) {
      case 'claude':
        await this.setupClaudeCommands(targetDir, currentRepoRoot);
        break;
      case 'gemini':
        await this.setupGeminiCommands(targetDir, currentRepoRoot);
        break;
      case 'copilot':
        await this.setupCopilotCommands(targetDir, currentRepoRoot);
        break;
      default:
        console.log(chalk.yellow(`⚠️ Unknown AI model: ${aiModel}, setting up Claude commands as default`));
        await this.setupClaudeCommands(targetDir, currentRepoRoot);
    }
  }

  private findSpecKitRoot(): string {
    // When installed via uvx/pip, templates are in the package directory
    // When run from source, templates are in the repo root

    // Method 1: Check if we're in the package (look for Python package structure)
    let currentDir = __dirname;
    while (currentDir !== path.dirname(currentDir)) {
      const specifyDir = path.join(currentDir, '.specify');
      const packageSpecifyDir = path.join(currentDir, 'specify_cli', '.specify');

      if (fs.existsSync(specifyDir)) {
        return currentDir;
      }
      if (fs.existsSync(packageSpecifyDir)) {
        return path.join(currentDir, 'specify_cli');
      }
      currentDir = path.dirname(currentDir);
    }

    // Method 2: Check working directory (for development)
    if (fs.existsSync(path.join(process.cwd(), '.specify'))) {
      return process.cwd();
    }

    // Method 3: Try to find package installation
    try {
      // This will work when installed as a Python package
      const packagePath = require.resolve('../../package.json');
      const packageDir = path.dirname(packagePath);
      if (fs.existsSync(path.join(packageDir, '.specify'))) {
        return packageDir;
      }
    } catch (e) {
      // Ignore if package.json not found
    }

    // Fallback to current working directory
    console.log(chalk.yellow('⚠️ Could not find spec-kit templates, using current directory'));
    return process.cwd();
  }

  private async copySpecifyAssets(targetDir: string, sourceRoot: string): Promise<void> {
    const sourceSpecifyDir = path.join(sourceRoot, '.specify');
    const targetSpecifyDir = path.join(targetDir, '.specify');

    // Copy templates
    const sourceTemplatesDir = path.join(sourceSpecifyDir, 'templates');
    const targetTemplatesDir = path.join(targetSpecifyDir, 'templates');
    if (await fs.pathExists(sourceTemplatesDir)) {
      await fs.copy(sourceTemplatesDir, targetTemplatesDir);
    }

    // Copy scripts
    const sourceScriptsDir = path.join(sourceSpecifyDir, 'scripts');
    const targetScriptsDir = path.join(targetSpecifyDir, 'scripts');
    if (await fs.pathExists(sourceScriptsDir)) {
      await fs.copy(sourceScriptsDir, targetScriptsDir);
    }

    // Copy memory
    const sourceMemoryDir = path.join(sourceSpecifyDir, 'memory');
    const targetMemoryDir = path.join(targetSpecifyDir, 'memory');
    if (await fs.pathExists(sourceMemoryDir)) {
      await fs.copy(sourceMemoryDir, targetMemoryDir);
    }
  }

  private async setupClaudeCommands(targetDir: string, sourceRoot: string): Promise<void> {
    const claudeDir = path.join(targetDir, '.claude');
    const commandsDir = path.join(claudeDir, 'commands');
    await fs.ensureDir(commandsDir);

    // Copy Claude commands only if source and target are different
    const sourceClaudeDir = path.join(sourceRoot, '.claude');
    if (await fs.pathExists(sourceClaudeDir) && path.resolve(targetDir) !== path.resolve(sourceRoot)) {
      await fs.copy(sourceClaudeDir, claudeDir);
      console.log(chalk.green('✅ Claude slash commands configured'));
    } else if (path.resolve(targetDir) === path.resolve(sourceRoot)) {
      console.log(chalk.green('✅ Claude commands already exist in current directory'));
    } else {
      console.log(chalk.yellow('⚠️ No Claude commands found in source'));
    }
  }

  private async setupGeminiCommands(targetDir: string, sourceRoot: string): Promise<void> {
    // Create GEMINI.md file with slash commands
    const geminiMdPath = path.join(targetDir, 'GEMINI.md');
    const geminiContent = `# Gemini CLI Commands

This file contains custom commands for use with Gemini CLI.

## Available Commands

### /specify
Create or update feature specifications from natural language descriptions.

\`\`\`bash
gemini /specify "Build a user authentication system with login and signup"
\`\`\`

### /plan
Generate technical implementation plans with architecture details.

\`\`\`bash
gemini /plan "Use React with TypeScript, Node.js backend with Express, PostgreSQL database"
\`\`\`

### /tasks
Break down features into actionable development tasks.

\`\`\`bash
gemini /tasks "Generate tasks for the authentication system implementation"
\`\`\`

## Usage

1. Use \`gemini /specify\` to create specifications
2. Use \`gemini /plan\` to create implementation plans
3. Use \`gemini /tasks\` to generate task breakdowns

These commands integrate with the spec-kit workflow and use the templates in \`.specify/templates/\`.
`;

    await fs.writeFile(geminiMdPath, geminiContent);
    console.log(chalk.green('✅ Gemini commands configured in GEMINI.md'));
  }

  private async setupCopilotCommands(targetDir: string, sourceRoot: string): Promise<void> {
    // Create .vscode directory for Copilot commands
    const vscodeDir = path.join(targetDir, '.vscode');
    await fs.ensureDir(vscodeDir);

    // Create Copilot slash commands configuration
    const copilotConfig = {
      "copilot.chat.commands": [
        {
          "name": "specify",
          "description": "Create or update feature specifications from natural language",
          "systemMessage": "Given the feature description, create a detailed specification using the template in .specify/templates/spec-template.md. Run .specify/scripts/bash/create-new-feature.sh first to set up the branch and files."
        },
        {
          "name": "plan",
          "description": "Generate technical implementation plans with architecture details",
          "systemMessage": "Create a technical implementation plan using .specify/templates/plan-template.md. Run .specify/scripts/bash/setup-plan.sh to prepare the planning workflow."
        },
        {
          "name": "tasks",
          "description": "Break down features into actionable development tasks",
          "systemMessage": "Generate actionable tasks using .specify/templates/tasks-template.md. Run .specify/scripts/bash/check-task-prerequisites.sh to check requirements."
        }
      ]
    };

    const settingsPath = path.join(vscodeDir, 'settings.json');
    await fs.writeJSON(settingsPath, copilotConfig, { spaces: 2 });

    // Also create COPILOT.md documentation
    const copilotMdPath = path.join(targetDir, 'COPILOT.md');
    const copilotContent = `# GitHub Copilot Commands

This file documents custom slash commands for use with GitHub Copilot in VS Code.

## Available Commands

### /specify
Create or update feature specifications from natural language descriptions.

Usage in VS Code:
1. Open Copilot Chat
2. Type: \`/specify Build a user authentication system with login and signup\`

### /plan
Generate technical implementation plans with architecture details.

Usage in VS Code:
1. Open Copilot Chat
2. Type: \`/plan Use React with TypeScript, Node.js backend with Express, PostgreSQL database\`

### /tasks
Break down features into actionable development tasks.

Usage in VS Code:
1. Open Copilot Chat
2. Type: \`/tasks Generate tasks for the authentication system implementation\`

## Setup

The commands are configured in \`.vscode/settings.json\` and integrate with spec-kit templates in \`.specify/templates/\`.

## Workflow

1. Use \`/specify\` to create specifications
2. Use \`/plan\` to create implementation plans
3. Use \`/tasks\` to generate task breakdowns
4. Implement following the generated plans and tasks
`;

    await fs.writeFile(copilotMdPath, copilotContent);
    console.log(chalk.green('✅ GitHub Copilot commands configured'));
  }

  private isValidAIModel(model: string): model is AIModelType {
    const validModels: AIModelType[] = ['claude', 'gemini', 'copilot'];
    return validModels.includes(model as AIModelType);
  }
}