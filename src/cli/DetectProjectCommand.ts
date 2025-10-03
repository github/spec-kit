import { Command } from 'commander';
import { ProjectDetector } from '@services/ProjectDetector';
import chalk from 'chalk';
import * as path from 'path';

export interface DetectProjectOptions {
  validate?: boolean;
  autoFix?: boolean;
  repair?: boolean;
  verbose?: boolean;
  depth?: number;
  includeDrafts?: boolean;
}

export class DetectProjectCommand {
  private projectDetector: ProjectDetector;

  constructor() {
    this.projectDetector = new ProjectDetector();
  }

  create(): Command {
    const command = new Command('detect-project');

    command
      .description('Auto-detect existing spec-kit projects and validate configuration')
      .option('--validate', 'Perform detailed validation of project configuration', true)
      .option('--auto-fix', 'Automatically fix detected issues when possible', false)
      .option('--repair', 'Attempt to repair broken project configuration', false)
      .option('-v, --verbose', 'Show detailed information about detection process', false)
      .option('-d, --depth <number>', 'Search depth for project detection (default: 5)', '5')
      .option('--include-drafts', 'Include draft specifications in validation', false)
      .action(async (options) => {
        await this.execute(options);
      });

    return command;
  }

  async execute(options: DetectProjectOptions): Promise<void> {
    try {
      const searchDepth = options.depth ? parseInt(options.depth.toString()) : 5;

      console.log(chalk.blue('🔍 Detecting spec-kit projects...'));

      if (options.verbose) {
        console.log(chalk.gray(`Search path: ${process.cwd()}`));
        console.log(chalk.gray(`Search depth: ${searchDepth}`));
        console.log(chalk.gray(`Auto-fix enabled: ${options.autoFix ? 'Yes' : 'No'}`));
      }

      // Detect project
      const result = await this.projectDetector.detectProject(process.cwd(), {
        searchDepth,
        validateConfig: options.validate,
        autoFix: options.autoFix,
        includeDrafts: options.includeDrafts,
      });

      // Handle project not found
      if (!result.found) {
        console.log(chalk.yellow('❌ No spec-kit project detected'));

        if (result.issues.length > 0) {
          console.log(chalk.gray('\nDetection issues:'));
          this.displayIssues(result.issues);
        }

        if (result.suggestions.length > 0) {
          console.log(chalk.blue('\n💡 Suggestions:'));
          result.suggestions.forEach(suggestion => {
            console.log(chalk.gray(`  • ${suggestion}`));
          });
        }

        return;
      }

      // Project found - display results
      console.log(chalk.green('✅ Spec-kit project detected!'));
      console.log(chalk.gray(`Project path: ${result.projectPath}`));

      if (result.config) {
        console.log(chalk.blue('\n📋 Project Information:'));
        console.log(`  Name: ${chalk.white(result.config.name)}`);
        console.log(`  AI Model: ${chalk.white(result.config.aiModel)}`);
        console.log(`  Version: ${chalk.white(result.config.version)}`);
        console.log(`  Initialized: ${result.config.isInitialized ? chalk.green('Yes') : chalk.yellow('No')}`);
        console.log(`  Spec Directory: ${chalk.gray(path.relative(process.cwd(), result.config.specDirectory))}`);

        if (result.config.migrationHistory.length > 0) {
          console.log(`  Migrations: ${chalk.white(result.config.migrationHistory.length)} completed`);

          if (options.verbose) {
            console.log(chalk.blue('\n🔄 Migration History:'));
            result.config.migrationHistory.slice(-3).forEach(migration => {
              const status = migration.success ? chalk.green('✅') : chalk.red('❌');
              console.log(`    ${status} ${migration.fromModel} → ${migration.toModel} (${new Date(migration.timestamp).toLocaleDateString()})`);
            });
          }
        }
      }

      // Display issues if any
      if (result.issues.length > 0) {
        const errors = result.issues.filter(i => i.type === 'error');
        const warnings = result.issues.filter(i => i.type === 'warning');
        const info = result.issues.filter(i => i.type === 'info');

        if (errors.length > 0) {
          console.log(chalk.red('\n❌ Errors found:'));
          this.displayIssues(errors);
        }

        if (warnings.length > 0) {
          console.log(chalk.yellow('\n⚠️  Warnings:'));
          this.displayIssues(warnings);
        }

        if (info.length > 0 && options.verbose) {
          console.log(chalk.blue('\nℹ️  Information:'));
          this.displayIssues(info);
        }

        // Show repair option if needed
        if ((errors.length > 0 || warnings.length > 0) && !options.repair) {
          const fixableCount = result.issues.filter(i => i.fixable).length;
          if (fixableCount > 0) {
            console.log(chalk.blue(`\n🔧 ${fixableCount} issue(s) can be automatically fixed`));
            console.log(chalk.gray('Run with --repair to attempt automatic repairs'));
          }
        }
      }

      // Display suggestions
      if (result.suggestions.length > 0) {
        console.log(chalk.blue('\n💡 Suggestions:'));
        result.suggestions.forEach(suggestion => {
          console.log(chalk.gray(`  • ${suggestion}`));
        });
      }

      // Perform repair if requested
      if (options.repair && result.issues.some(i => i.fixable)) {
        console.log(chalk.blue('\n🔧 Attempting to repair project...'));

        const repairResult = await this.projectDetector.repairProject(
          result.projectPath!,
          result.config
        );

        if (repairResult.found) {
          console.log(chalk.green('✅ Project repair completed successfully'));

          if (repairResult.suggestions.length > 0) {
            console.log(chalk.blue('\nRepair actions taken:'));
            repairResult.suggestions.forEach(suggestion => {
              console.log(chalk.gray(`  • ${suggestion}`));
            });
          }

          if (repairResult.issues.length > 0) {
            console.log(chalk.yellow('\nRemaining issues after repair:'));
            this.displayIssues(repairResult.issues);
          }
        } else {
          console.error(chalk.red('❌ Project repair failed'));
          if (repairResult.issues.length > 0) {
            this.displayIssues(repairResult.issues);
          }
        }
      }

      // Show next steps
      if (result.config && result.issues.length === 0) {
        console.log(chalk.blue('\n🚀 Next steps:'));
        console.log(chalk.gray('  • Use "specify list-models" to see available AI models'));
        console.log(chalk.gray('  • Use "specify switch-model <model>" to change AI models'));
        console.log(chalk.gray('  • Use "specify track-tasks enable" for task tracking UI'));
      }

    } catch (error) {
      console.error(chalk.red(`❌ Detection failed: ${error}`));
      process.exit(1);
    }
  }

  private displayIssues(issues: any[]): void {
    issues.forEach(issue => {
      const icon = this.getIssueIcon(issue.type);
      const color = this.getIssueColor(issue.type);

      console.log(color(`  ${icon} ${issue.message}`));

      if (issue.path) {
        console.log(chalk.gray(`    Path: ${issue.path}`));
      }

      if (issue.fixable) {
        console.log(chalk.gray(`    Fixable: Yes`));
      }
    });
  }

  private getIssueIcon(type: string): string {
    switch (type) {
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '•';
    }
  }

  private getIssueColor(type: string): (text: string) => string {
    switch (type) {
      case 'error': return chalk.red;
      case 'warning': return chalk.yellow;
      case 'info': return chalk.blue;
      default: return chalk.gray;
    }
  }

  async validateCurrentProject(): Promise<{
    valid: boolean;
    projectPath?: string;
    config?: any;
    issues: any[];
  }> {
    try {
      const result = await this.projectDetector.detectProject(process.cwd(), {
        validateConfig: true,
        autoFix: false,
      });

      return {
        valid: result.found && result.issues.filter(i => i.type === 'error').length === 0,
        projectPath: result.projectPath,
        config: result.config,
        issues: result.issues,
      };

    } catch (error) {
      return {
        valid: false,
        issues: [{
          type: 'error',
          message: `Validation failed: ${error}`,
          fixable: false,
        }],
      };
    }
  }

  getUsageExamples(): string[] {
    return [
      'specify detect-project',
      'specify detect-project --verbose',
      'specify detect-project --repair',
      'specify detect-project --auto-fix --include-drafts',
      'specify detect-project --depth 10',
    ];
  }

  async searchProjectsInDirectory(
    directory: string,
    maxDepth: number = 3
  ): Promise<{
    projects: Array<{
      path: string;
      config?: any;
      valid: boolean;
    }>;
    totalFound: number;
  }> {
    const projects: Array<{ path: string; config?: any; valid: boolean }> = [];

    try {
      const result = await this.projectDetector.detectProject(directory, {
        searchDepth: maxDepth,
        validateConfig: true,
      });

      if (result.found && result.projectPath) {
        projects.push({
          path: result.projectPath,
          config: result.config,
          valid: result.issues.filter(i => i.type === 'error').length === 0,
        });
      }

    } catch (error) {
      // Continue searching even if one directory fails
    }

    return {
      projects,
      totalFound: projects.length,
    };
  }
}