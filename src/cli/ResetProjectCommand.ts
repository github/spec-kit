import { Command } from 'commander';
import { ProjectDetector } from '@services/ProjectDetector';
import { ConfigManager } from '@services/ConfigManager';
import { TaskTracker } from '@services/TaskTracker';
import chalk from 'chalk';
import * as fs from 'fs-extra';
import * as path from 'path';

export interface ResetProjectOptions {
  backup?: boolean;
  force?: boolean;
  repair?: boolean;
  keepSpecs?: boolean;
  keepTasks?: boolean;
  dryRun?: boolean;
}

export class ResetProjectCommand {
  private projectDetector: ProjectDetector;
  private configManager: ConfigManager;

  constructor() {
    this.projectDetector = new ProjectDetector();
    this.configManager = new ConfigManager();
  }

  create(): Command {
    const command = new Command('reset-project');

    command
      .description('Clean project reset with backup and recovery options')
      .option('--backup', 'Create backup before reset (default: true)', true)
      .option('--force', 'Force reset without confirmation prompts', false)
      .option('--repair', 'Repair mode - fix issues without full reset', false)
      .option('--keep-specs', 'Keep specification files during reset', false)
      .option('--keep-tasks', 'Keep task tracking data during reset', false)
      .option('--dry-run', 'Show what would be reset without making changes', false)
      .action(async (options) => {
        await this.execute(options);
      });

    return command;
  }

  async execute(options: ResetProjectOptions): Promise<void> {
    try {
      console.log(chalk.blue('🔄 Project Reset Utility'));

      // Detect current project
      const detection = await this.projectDetector.detectProject();

      if (!detection.found) {
        console.log(chalk.yellow('⚠️  No spec-kit project found in current directory'));
        console.log(chalk.gray('Nothing to reset'));
        return;
      }

      const projectPath = detection.projectPath!;
      const config = detection.config;

      console.log(chalk.gray(`Project: ${config?.name || 'Unknown'}`));
      console.log(chalk.gray(`Path: ${projectPath}`));

      if (options.dryRun) {
        console.log(chalk.cyan('🏃 Dry run mode - no changes will be made\n'));
      }

      // Choose operation mode
      if (options.repair) {
        await this.repairProject(detection, options);
      } else {
        await this.resetProject(detection, options);
      }

    } catch (error) {
      console.error(chalk.red(`❌ Reset operation failed: ${error}`));
      process.exit(1);
    }
  }

  private async repairProject(detection: any, options: ResetProjectOptions): Promise<void> {
    console.log(chalk.blue('🔧 Repair Mode - Fixing project issues\n'));

    const issues = detection.issues || [];
    const fixableIssues = issues.filter((i: any) => i.fixable);

    if (fixableIssues.length === 0) {
      console.log(chalk.green('✅ No fixable issues found'));

      if (issues.length > 0) {
        console.log(chalk.yellow('\nRemaining issues that require manual attention:'));
        issues.filter((i: any) => !i.fixable).forEach((issue: any) => {
          console.log(chalk.yellow(`  • ${issue.message}`));
        });
      }

      return;
    }

    console.log(chalk.blue(`Found ${fixableIssues.length} fixable issues:`));
    fixableIssues.forEach((issue: any) => {
      console.log(chalk.gray(`  • ${issue.message}`));
    });

    if (!options.force && !options.dryRun) {
      // In a real CLI, you'd use a prompt library here
      console.log(chalk.yellow('\nWould proceed with repairs (use --force to skip confirmation)'));
    }

    if (options.dryRun) {
      console.log(chalk.cyan('Dry run complete - repairs would be applied'));
      return;
    }

    // Create backup if requested
    if (options.backup) {
      await this.createProjectBackup(detection.projectPath, detection.config);
    }

    // Attempt repairs
    const repairResult = await this.projectDetector.repairProject(
      detection.projectPath,
      detection.config
    );

    if (repairResult.found) {
      console.log(chalk.green('\n✅ Project repair completed successfully'));

      if (repairResult.suggestions.length > 0) {
        console.log(chalk.blue('\nActions taken:'));
        repairResult.suggestions.forEach(suggestion => {
          console.log(chalk.gray(`  • ${suggestion}`));
        });
      }

      if (repairResult.issues.length > 0) {
        console.log(chalk.yellow('\nRemaining issues:'));
        repairResult.issues.forEach((issue: any) => {
          console.log(chalk.yellow(`  • ${issue.message}`));
        });
      }
    } else {
      console.error(chalk.red('❌ Repair failed'));
      if (repairResult.issues.length > 0) {
        repairResult.issues.forEach((issue: any) => {
          console.error(chalk.red(`  • ${issue.message}`));
        });
      }
    }
  }

  private async resetProject(detection: any, options: ResetProjectOptions): Promise<void> {
    console.log(chalk.blue('🔄 Full Project Reset\n'));

    const projectPath = detection.projectPath;
    const config = detection.config;

    // Show what will be reset
    const resetItems = await this.getResetItems(projectPath, options);

    console.log(chalk.yellow('Items to be reset:'));
    resetItems.forEach(item => {
      const icon = item.keep ? '🔒' : '🗑️';
      const status = item.keep ? 'KEEP' : 'RESET';
      const color = item.keep ? chalk.green : chalk.gray;

      console.log(`  ${icon} ${item.name}: ${color(status)}`);
      if (item.description) {
        console.log(chalk.gray(`      ${item.description}`));
      }
    });

    if (options.dryRun) {
      console.log(chalk.cyan('\nDry run complete - no actual changes made'));
      return;
    }

    // Confirmation
    if (!options.force) {
      console.log(chalk.yellow('\nThis will permanently reset the selected items.'));
      console.log(chalk.gray('Use --force to skip this confirmation'));
      // In a real CLI, you'd use a prompt library here
      console.log(chalk.yellow('Would proceed with reset...'));
    }

    // Create backup
    let backupPath: string | undefined;
    if (options.backup) {
      backupPath = await this.createProjectBackup(projectPath, config);
      console.log(chalk.blue(`📦 Backup created: ${backupPath}`));
    }

    // Perform reset
    try {
      await this.performReset(projectPath, config, options);

      console.log(chalk.green('\n✅ Project reset completed successfully'));

      if (backupPath) {
        console.log(chalk.gray(`Backup available at: ${backupPath}`));
      }

      // Show next steps
      console.log(chalk.blue('\n🚀 Next steps:'));
      console.log(chalk.gray('  • Run "specify detect-project" to verify the reset'));
      console.log(chalk.gray('  • Initialize project: "specify init" if starting fresh'));
      console.log(chalk.gray('  • Restore from backup if needed'));

    } catch (error) {
      console.error(chalk.red(`❌ Reset failed: ${error}`));

      if (backupPath) {
        console.error(chalk.yellow(`💾 Backup available for recovery: ${backupPath}`));
        console.error(chalk.gray('You can manually restore files from the backup'));
      }

      throw error;
    }
  }

  private async getResetItems(projectPath: string, options: ResetProjectOptions): Promise<Array<{
    name: string;
    description?: string;
    path: string;
    keep: boolean;
  }>> {
    const items = [];

    // Configuration files
    items.push({
      name: 'Project Configuration',
      description: 'AI model settings, project metadata',
      path: path.join(projectPath, '.specify', 'config.json'),
      keep: false,
    });

    // Task tracking data
    items.push({
      name: 'Task Tracking Data',
      description: 'Task states, progress tracking',
      path: path.join(projectPath, '.specify', 'tasks.json'),
      keep: options.keepTasks || false,
    });

    // Specification files
    items.push({
      name: 'Specification Files',
      description: 'Feature specs, plans, contracts',
      path: path.join(projectPath, 'specs'),
      keep: options.keepSpecs || false,
    });

    // Migration history & backups
    items.push({
      name: 'Migration History',
      description: 'Model switch history and backups',
      path: path.join(projectPath, '.specify', 'backups'),
      keep: false,
    });

    // Cache and temporary files
    items.push({
      name: 'Cache & Temporary Files',
      description: 'Cached data, temporary files',
      path: path.join(projectPath, '.specify', 'cache'),
      keep: false,
    });

    return items;
  }

  private async createProjectBackup(projectPath: string, config: any): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupName = `project-backup-${timestamp}`;
    const backupPath = path.join(projectPath, '.specify', 'backups', backupName);

    await fs.ensureDir(backupPath);

    // Backup configuration
    const configPath = path.join(projectPath, '.specify', 'config.json');
    if (await fs.pathExists(configPath)) {
      await fs.copy(configPath, path.join(backupPath, 'config.json'));
    }

    // Backup task data
    const taskPath = path.join(projectPath, '.specify', 'tasks.json');
    if (await fs.pathExists(taskPath)) {
      await fs.copy(taskPath, path.join(backupPath, 'tasks.json'));
    }

    // Backup specs directory
    const specsPath = path.join(projectPath, 'specs');
    if (await fs.pathExists(specsPath)) {
      await fs.copy(specsPath, path.join(backupPath, 'specs'));
    }

    // Create backup manifest
    const manifest = {
      createdAt: new Date().toISOString(),
      projectName: config?.name || 'Unknown',
      projectId: config?.projectId,
      aiModel: config?.aiModel,
      originalPath: projectPath,
      backupType: 'full-project',
    };

    await fs.writeJson(
      path.join(backupPath, 'manifest.json'),
      manifest,
      { spaces: 2 }
    );

    return backupPath;
  }

  private async performReset(
    projectPath: string,
    config: any,
    options: ResetProjectOptions
  ): Promise<void> {
    const specifyDir = path.join(projectPath, '.specify');

    // Reset configuration (always)
    const configPath = path.join(specifyDir, 'config.json');
    if (await fs.pathExists(configPath)) {
      await fs.remove(configPath);
    }

    // Reset task data (unless keeping)
    if (!options.keepTasks) {
      const taskPath = path.join(specifyDir, 'tasks.json');
      if (await fs.pathExists(taskPath)) {
        await fs.remove(taskPath);
      }
    }

    // Reset specs (unless keeping)
    if (!options.keepSpecs) {
      const specsPath = path.join(projectPath, 'specs');
      if (await fs.pathExists(specsPath)) {
        await fs.remove(specsPath);
      }
    }

    // Clean up migration history and old backups
    const backupsPath = path.join(specifyDir, 'backups');
    if (await fs.pathExists(backupsPath)) {
      // Keep the most recent backup we just created
      const backups = await fs.readdir(backupsPath);
      const oldBackups = backups
        .filter(name => !name.startsWith('project-backup-'))
        .map(name => path.join(backupsPath, name));

      for (const backup of oldBackups) {
        await fs.remove(backup);
      }
    }

    // Clean cache
    const cachePath = path.join(specifyDir, 'cache');
    if (await fs.pathExists(cachePath)) {
      await fs.remove(cachePath);
    }
  }

  getUsageExamples(): string[] {
    return [
      'specify reset-project',
      'specify reset-project --repair',
      'specify reset-project --dry-run',
      'specify reset-project --force --no-backup',
      'specify reset-project --keep-specs --keep-tasks',
    ];
  }

  async listBackups(projectPath: string): Promise<Array<{
    name: string;
    path: string;
    createdAt: string;
    size: number;
  }>> {
    const backupsDir = path.join(projectPath, '.specify', 'backups');

    if (!await fs.pathExists(backupsDir)) {
      return [];
    }

    const backups = [];
    const items = await fs.readdir(backupsDir);

    for (const item of items) {
      const itemPath = path.join(backupsDir, item);
      const stats = await fs.stat(itemPath);

      if (stats.isDirectory()) {
        const manifestPath = path.join(itemPath, 'manifest.json');
        let createdAt = stats.mtime.toISOString();

        if (await fs.pathExists(manifestPath)) {
          try {
            const manifest = await fs.readJson(manifestPath);
            createdAt = manifest.createdAt || createdAt;
          } catch {
            // Use file stats if manifest is invalid
          }
        }

        backups.push({
          name: item,
          path: itemPath,
          createdAt,
          size: await this.getDirectorySize(itemPath),
        });
      }
    }

    return backups.sort((a, b) =>
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }

  private async getDirectorySize(dirPath: string): Promise<number> {
    let size = 0;

    try {
      const items = await fs.readdir(dirPath);

      for (const item of items) {
        const itemPath = path.join(dirPath, item);
        const stats = await fs.stat(itemPath);

        if (stats.isDirectory()) {
          size += await this.getDirectorySize(itemPath);
        } else {
          size += stats.size;
        }
      }
    } catch {
      // Return 0 if directory is not accessible
    }

    return size;
  }
}