import { Command } from 'commander';
import { ModelSwitcher } from '@services/ModelSwitcher';
import { ConfigManager } from '@services/ConfigManager';
import { ProjectDetector } from '@services/ProjectDetector';
import chalk from 'chalk';

export interface SwitchModelOptions {
  backup?: boolean;
  dryRun?: boolean;
  force?: boolean;
  validate?: boolean;
}

export class SwitchModelCommand {
  private modelSwitcher: ModelSwitcher;
  private configManager: ConfigManager;
  private projectDetector: ProjectDetector;

  constructor() {
    this.configManager = new ConfigManager();
    this.modelSwitcher = new ModelSwitcher(this.configManager);
    this.projectDetector = new ProjectDetector();
  }

  create(): Command {
    const command = new Command('switch-model');

    command
      .description('Switch AI model without losing project progress')
      .argument('<target>', 'Target AI model (claude or gemini)')
      .option('--backup', 'Create backup before switching (default: true)', true)
      .option('--dry-run', 'Show what would be changed without making changes', false)
      .option('--force', 'Force switch even if validation fails', false)
      .option('--no-validate', 'Skip validation checks', false)
      .action(async (target, options) => {
        await this.execute(target, options);
      });

    return command;
  }

  async execute(target: string, options: SwitchModelOptions): Promise<void> {
    try {
      // Validate target model
      if (!['claude', 'gemini'].includes(target)) {
        console.error(chalk.red(`Error: Invalid target model '${target}'. Must be 'claude' or 'gemini'.`));
        process.exit(1);
      }

      const targetModel = target as 'claude' | 'gemini';

      console.log(chalk.blue('🔄 Switching AI Model...'));
      console.log(chalk.gray(`Target model: ${targetModel}`));

      // Detect current project
      const detection = await this.projectDetector.detectProject();

      if (!detection.found || !detection.config) {
        console.error(chalk.red('❌ No spec-kit project found in current directory'));
        console.error(chalk.gray('Run "specify detect-project" for more information'));
        process.exit(1);
      }

      const currentConfig = detection.config;

      // Check if already using target model
      if (currentConfig.aiModel === targetModel) {
        console.log(chalk.yellow(`⚠️  Project is already using ${targetModel}`));
        return;
      }

      console.log(chalk.gray(`Current model: ${currentConfig.aiModel}`));

      // Perform validation unless disabled
      if (options.validate !== false && !options.force) {
        console.log(chalk.blue('🔍 Validating project...'));

        const validation = await this.configManager.validateConfig(currentConfig.configPath);

        if (!validation.valid && !options.force) {
          console.error(chalk.red('❌ Project validation failed:'));
          validation.errors.forEach(error => {
            console.error(chalk.red(`  • ${error}`));
          });

          if (validation.warnings.length > 0) {
            console.warn(chalk.yellow('⚠️  Warnings:'));
            validation.warnings.forEach(warning => {
              console.warn(chalk.yellow(`  • ${warning}`));
            });
          }

          console.error(chalk.gray('Use --force to proceed anyway'));
          process.exit(1);
        }

        if (validation.warnings.length > 0) {
          console.warn(chalk.yellow('⚠️  Warnings found:'));
          validation.warnings.forEach(warning => {
            console.warn(chalk.yellow(`  • ${warning}`));
          });
        }
      }

      if (options.dryRun) {
        console.log(chalk.cyan('🏃 Dry run mode - no changes will be made'));
      }

      // Perform the switch
      console.log(chalk.blue('🚀 Starting model migration...'));

      const result = await this.modelSwitcher.switchModel(currentConfig, {
        targetModel,
        createBackup: options.backup,
        dryRun: options.dryRun,
        force: options.force,
      });

      if (!result.success) {
        console.error(chalk.red(`❌ Migration failed: ${result.errorMessage}`));

        if (result.backupPath) {
          console.error(chalk.gray(`Backup available at: ${result.backupPath}`));
        }

        process.exit(1);
      }

      // Show results
      if (options.dryRun) {
        console.log(chalk.green('✅ Dry run completed successfully'));
        console.log(chalk.gray('No actual changes were made to your project'));
      } else {
        console.log(chalk.green(`✅ Successfully switched to ${targetModel}!`));
        console.log(chalk.gray(`Migration ID: ${result.migrationId}`));

        if (result.backupPath) {
          console.log(chalk.gray(`Backup created: ${result.backupPath}`));
        }
      }

      // Show warnings
      if (result.warnings.length > 0) {
        console.warn(chalk.yellow('⚠️  Warnings:'));
        result.warnings.forEach(warning => {
          console.warn(chalk.yellow(`  • ${warning}`));
        });
      }

      // Show next steps
      if (!options.dryRun) {
        console.log(chalk.blue('\n📋 Next steps:'));
        console.log(chalk.gray('  • Test your project to ensure everything works correctly'));
        console.log(chalk.gray('  • Update any model-specific configurations if needed'));
        console.log(chalk.gray(`  • Use "specify list-models" to see ${targetModel} capabilities`));
      }

    } catch (error) {
      console.error(chalk.red(`❌ Unexpected error: ${error}`));
      process.exit(1);
    }
  }

  async validateArgs(target: string): Promise<{
    valid: boolean;
    errors: string[];
    suggestions: string[];
  }> {
    const errors: string[] = [];
    const suggestions: string[] = [];

    if (!target) {
      errors.push('Target model is required');
      suggestions.push('Specify target model: specify switch-model <claude|gemini>');
    } else if (!['claude', 'gemini'].includes(target)) {
      errors.push(`Invalid target model: ${target}`);
      suggestions.push('Valid models are: claude, gemini');
    }

    return {
      valid: errors.length === 0,
      errors,
      suggestions,
    };
  }

  getUsageExamples(): string[] {
    return [
      'specify switch-model claude',
      'specify switch-model gemini --dry-run',
      'specify switch-model claude --force --no-backup',
      'specify switch-model gemini --validate',
    ];
  }
}