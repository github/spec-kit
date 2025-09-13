#!/usr/bin/env node

import { Command } from 'commander';
import { SwitchModelCommand } from './SwitchModelCommand';
import { ListModelsCommand } from './ListModelsCommand';
import { DetectProjectCommand } from './DetectProjectCommand';
import { ResetProjectCommand } from './ResetProjectCommand';
import { TrackTasksCommand } from './TrackTasksCommand';
import { InitProjectCommand } from './InitProjectCommand';
import chalk from 'chalk';
import * as fs from 'fs-extra';
import * as path from 'path';

class SpecifyCLI {
  private program: Command;
  private version: string;

  constructor() {
    this.program = new Command();
    this.version = this.loadVersion();
    this.setupProgram();
    this.setupCommands();
    this.setupGlobalOptions();
    this.setupErrorHandling();
  }

  private loadVersion(): string {
    try {
      const packageJsonPath = path.join(__dirname, '../../package.json');
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
      return packageJson.version || '0.1.0';
    } catch (error) {
      return '0.1.0';
    }
  }

  private setupProgram(): void {
    this.program
      .name('specify')
      .description('AI Model Switching and Task Tracking CLI for Spec-Driven Development')
      .version(this.version, '-v, --version', 'Output the current version')
      .helpOption('-h, --help', 'Display help for command');
  }

  private setupCommands(): void {
    // Init Project Command
    const initProjectCmd = new InitProjectCommand();
    this.program.addCommand(initProjectCmd.create());

    // Switch Model Command
    const switchModelCmd = new SwitchModelCommand();
    this.program.addCommand(switchModelCmd.create());

    // List Models Command
    const listModelsCmd = new ListModelsCommand();
    this.program.addCommand(listModelsCmd.create());

    // Detect Project Command
    const detectProjectCmd = new DetectProjectCommand();
    this.program.addCommand(detectProjectCmd.create());

    // Reset Project Command
    const resetProjectCmd = new ResetProjectCommand();
    this.program.addCommand(resetProjectCmd.create());

    // Track Tasks Command
    const trackTasksCmd = new TrackTasksCommand();
    this.program.addCommand(trackTasksCmd.create());

    // Add aliases for common commands
    this.program
      .command('switch <target>')
      .description('Alias for switch-model command')
      .action((target, options) => {
        const switchCmd = new SwitchModelCommand();
        switchCmd.execute(target, options);
      });

    this.program
      .command('models')
      .description('Alias for list-models command')
      .action((options) => {
        const listCmd = new ListModelsCommand();
        listCmd.execute(options);
      });

    this.program
      .command('detect')
      .description('Alias for detect-project command')
      .action((options) => {
        const detectCmd = new DetectProjectCommand();
        detectCmd.execute(options);
      });

    this.program
      .command('status')
      .description('Show project and task status')
      .action(async () => {
        await this.showStatus();
      });

    this.program
      .command('info')
      .description('Show detailed project information')
      .action(async () => {
        await this.showInfo();
      });
  }

  private setupGlobalOptions(): void {
    this.program
      .option('--debug', 'Enable debug output', false)
      .option('--no-color', 'Disable colored output', false)
      .option('--config <path>', 'Path to configuration file')
      .option('--quiet', 'Suppress non-error output', false);
  }

  private setupErrorHandling(): void {
    this.program.exitOverride();

    process.on('unhandledRejection', (error) => {
      console.error(chalk.red('Unhandled promise rejection:'), error);
      process.exit(1);
    });

    process.on('uncaughtException', (error) => {
      console.error(chalk.red('Uncaught exception:'), error);
      process.exit(1);
    });

    // Handle SIGINT (Ctrl+C) gracefully
    process.on('SIGINT', () => {
      console.log(chalk.yellow('\n👋 Goodbye!'));
      process.exit(0);
    });
  }

  private async showStatus(): Promise<void> {
    try {
      console.log(chalk.blue('📊 Specify Project Status\n'));

      // Detect project
      const { DetectProjectCommand } = await import('./DetectProjectCommand');
      const detectCmd = new DetectProjectCommand();
      const validation = await detectCmd.validateCurrentProject();

      if (!validation.valid) {
        console.log(chalk.yellow('⚠️  No valid spec-kit project found'));
        console.log(chalk.gray('Run "specify detect-project" for more details'));
        return;
      }

      const config = validation.config;

      // Project info
      console.log(chalk.white('📋 Project Information:'));
      console.log(`  Name: ${chalk.cyan(config.name)}`);
      console.log(`  AI Model: ${chalk.cyan(config.aiModel)}`);
      console.log(`  Version: ${chalk.gray(config.version)}`);
      console.log(`  Path: ${chalk.gray(validation.projectPath)}`);

      // Task status
      try {
        const { TaskTracker } = await import('@services/TaskTracker');
        const taskTracker = new TaskTracker(config);
        await taskTracker.initialize();

        const stats = taskTracker.getTaskStats();

        console.log(chalk.white('\n📈 Task Status:'));
        console.log(`  Total: ${chalk.cyan(stats.total)}`);
        console.log(`  Completed: ${chalk.green(stats.completed)} (${stats.percentComplete}%)`);
        console.log(`  In Progress: ${chalk.yellow(stats.inProgress)}`);
        console.log(`  Pending: ${chalk.gray(stats.pending)}`);

        if (stats.failed > 0) {
          console.log(`  Failed: ${chalk.red(stats.failed)}`);
        }

        // Progress bar
        const progressBar = this.createProgressBar(stats.percentComplete);
        console.log(`\n  ${progressBar}`);

      } catch (error) {
        console.log(chalk.gray('\n📈 Task Status: No task data available'));
      }

      // Model compatibility
      const { AIModelSettingsProvider } = await import('@models/AIModelSettings');
      const modelSettings = AIModelSettingsProvider.getSettings(config.aiModel);

      if (modelSettings) {
        console.log(chalk.white('\n🤖 AI Model Status:'));
        console.log(`  Current: ${chalk.cyan(modelSettings.modelType)} v${modelSettings.version}`);
        console.log(`  Max Tokens: ${chalk.gray(modelSettings.capabilities.maxTokens.toLocaleString())}`);
        console.log(`  Features: ${chalk.gray(modelSettings.capabilities.features.length)} available`);
      }

    } catch (error) {
      console.error(chalk.red(`❌ Failed to get status: ${error}`));
    }
  }

  private async showInfo(): Promise<void> {
    try {
      console.log(chalk.blue(`🔧 Specify CLI v${this.version}\n`));

      console.log(chalk.white('📦 Available Commands:'));
      console.log('  switch-model <target>  Switch AI model (claude/gemini)');
      console.log('  list-models           Show available AI models');
      console.log('  detect-project        Auto-detect and validate project');
      console.log('  reset-project         Clean project reset with backup');
      console.log('  track-tasks <action>  Manage task tracking UI');
      console.log('');

      console.log(chalk.white('🔗 Aliases:'));
      console.log('  switch <target>       Alias for switch-model');
      console.log('  models               Alias for list-models');
      console.log('  detect               Alias for detect-project');
      console.log('  status               Show project and task status');
      console.log('  info                 Show this information');
      console.log('');

      console.log(chalk.white('🎯 Examples:'));
      console.log('  specify switch claude');
      console.log('  specify models --details');
      console.log('  specify detect --repair');
      console.log('  specify track-tasks enable --sidebar');
      console.log('');

      console.log(chalk.white('🏗️  Architecture:'));
      console.log('  • Library-first design with CLI wrappers');
      console.log('  • Real-time task tracking with terminal UI');
      console.log('  • Automatic project detection and validation');
      console.log('  • AI model migration with rollback support');
      console.log('');

      console.log(chalk.gray('Use --help with any command for detailed usage information'));

    } catch (error) {
      console.error(chalk.red(`❌ Failed to show info: ${error}`));
    }
  }

  private createProgressBar(percentage: number, width: number = 20): string {
    const filled = Math.round((percentage / 100) * width);
    const empty = width - filled;

    const bar = chalk.green('█').repeat(filled) + chalk.gray('░').repeat(empty);
    return `${bar} ${percentage}%`;
  }

  async run(args: string[] = process.argv): Promise<void> {
    try {
      // Check for no arguments (show help)
      if (args.length <= 2) {
        this.program.outputHelp();
        return;
      }

      // Parse and execute
      await this.program.parseAsync(args);

    } catch (error: any) {
      // Handle Commander.js errors
      if (error.code === 'commander.invalidArgument') {
        console.error(chalk.red(`❌ Invalid argument: ${error.message}`));
        console.error(chalk.gray('Use --help for usage information'));
      } else if (error.code === 'commander.unknownCommand') {
        console.error(chalk.red(`❌ Unknown command: ${error.message}`));
        console.error(chalk.gray('Use --help to see available commands'));
      } else if (error.code === 'commander.help') {
        // Help was requested, exit normally
        return;
      } else if (error.code === 'commander.version') {
        // Version was requested, exit normally
        return;
      } else {
        console.error(chalk.red(`❌ Error: ${error.message || error}`));
      }

      process.exit(1);
    }
  }

  getProgram(): Command {
    return this.program;
  }

  getVersion(): string {
    return this.version;
  }
}

// Export for testing
export { SpecifyCLI };

// Run if called directly
if (require.main === module) {
  const cli = new SpecifyCLI();
  cli.run().catch((error) => {
    console.error(chalk.red('Fatal error:'), error);
    process.exit(1);
  });
}