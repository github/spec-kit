import { ProjectConfig } from '@models/ProjectConfig';
import { MigrationState, MigrationStateManager } from '@models/MigrationState';
import { AIModelSettings, AIModelSettingsProvider } from '@models/AIModelSettings';
import { ConfigManager } from './ConfigManager';
import * as path from 'path';
import * as fs from 'fs-extra';

export interface SwitchModelOptions {
  targetModel: 'claude' | 'gemini';
  createBackup?: boolean;
  dryRun?: boolean;
  force?: boolean;
}

export interface SwitchResult {
  success: boolean;
  migrationId: string;
  backupPath?: string;
  errorMessage?: string;
  warnings: string[];
}

export class ModelSwitcher {
  constructor(
    private configManager: ConfigManager,
    private backupDirectory: string = './.specify/backups'
  ) {}

  async switchModel(
    projectConfig: ProjectConfig,
    options: SwitchModelOptions
  ): Promise<SwitchResult> {
    const warnings: string[] = [];

    try {
      // Validate target model
      if (projectConfig.aiModel === options.targetModel) {
        return {
          success: false,
          migrationId: '',
          errorMessage: `Project is already using ${options.targetModel}`,
          warnings,
        };
      }

      // Check model compatibility
      const targetSettings = AIModelSettingsProvider.getSettings(options.targetModel);
      if (!targetSettings) {
        return {
          success: false,
          migrationId: '',
          errorMessage: `Unknown target model: ${options.targetModel}`,
          warnings,
        };
      }

      // Check compatibility warnings
      if (targetSettings.compatibility.deprecationWarning) {
        warnings.push(targetSettings.compatibility.deprecationWarning);
      }

      // Create migration state
      const backupPath = await this.createBackupPath(projectConfig.projectId);
      const migration = MigrationStateManager.create({
        fromModel: projectConfig.aiModel,
        toModel: options.targetModel,
        projectId: projectConfig.projectId,
        backupPath,
        dryRun: options.dryRun || false,
      });

      if (options.dryRun) {
        return {
          success: true,
          migrationId: migration.id,
          warnings: [...warnings, 'Dry run completed - no changes made'],
        };
      }

      // Execute migration steps
      const result = await this.executeMigration(migration, projectConfig, options);

      return {
        ...result,
        warnings,
      };

    } catch (error) {
      return {
        success: false,
        migrationId: '',
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
        warnings,
      };
    }
  }

  private async executeMigration(
    migration: MigrationState,
    projectConfig: ProjectConfig,
    options: SwitchModelOptions
  ): Promise<Omit<SwitchResult, 'warnings'>> {
    try {
      // Step 1: Validate project
      await this.validateProject(projectConfig);

      // Step 2: Create backup
      if (options.createBackup !== false) {
        await this.createBackup(migration, projectConfig);
      }

      // Step 3: Update configuration
      const updatedConfig = await this.updateProjectConfig(
        projectConfig,
        migration.toModel,
        migration.id
      );

      // Step 4: Migrate spec files (if needed)
      await this.migrateSpecFiles(projectConfig, migration);

      // Step 5: Validate migration
      await this.validateMigration(updatedConfig);

      const completedMigration = MigrationStateManager.complete(migration, true);

      return {
        success: true,
        migrationId: completedMigration.id,
        backupPath: migration.backup.path,
      };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Migration failed';

      // Attempt rollback if backup exists
      if (migration.backup.files.length > 0 && MigrationStateManager.canRollback(migration)) {
        try {
          await this.rollbackMigration(migration);
        } catch (rollbackError) {
          return {
            success: false,
            migrationId: migration.id,
            errorMessage: `${errorMessage}. Rollback also failed: ${rollbackError}`,
          };
        }
      }

      return {
        success: false,
        migrationId: migration.id,
        errorMessage,
        backupPath: migration.backup.path,
      };
    }
  }

  private async validateProject(config: ProjectConfig): Promise<void> {
    if (!config.isInitialized) {
      throw new Error('Project is not properly initialized');
    }

    if (!await fs.pathExists(config.configPath)) {
      throw new Error('Project configuration file not found');
    }

    if (!await fs.pathExists(config.specDirectory)) {
      throw new Error('Specification directory not found');
    }
  }

  private async createBackup(
    migration: MigrationState,
    config: ProjectConfig
  ): Promise<void> {
    await fs.ensureDir(this.backupDirectory);

    const backupDir = path.join(this.backupDirectory, migration.backup.id);
    await fs.ensureDir(backupDir);

    // Copy configuration files
    const configBackupPath = path.join(backupDir, 'config.json');
    await fs.copy(config.configPath, configBackupPath);

    // Copy spec directory
    const specBackupPath = path.join(backupDir, 'specs');
    await fs.copy(config.specDirectory, specBackupPath);

    // Update backup info
    const stats = await fs.stat(backupDir);
    migration.backup.size = await this.getDirectorySize(backupDir);
    migration.backup.checksum = await this.calculateChecksum(backupDir);
    migration.backup.files = [
      {
        originalPath: config.configPath,
        backupPath: configBackupPath,
        checksum: await this.calculateFileChecksum(configBackupPath),
        size: (await fs.stat(configBackupPath)).size,
      },
      {
        originalPath: config.specDirectory,
        backupPath: specBackupPath,
        checksum: await this.calculateFileChecksum(specBackupPath),
        size: await this.getDirectorySize(specBackupPath),
      },
    ];
  }

  private async updateProjectConfig(
    config: ProjectConfig,
    targetModel: 'claude' | 'gemini' | 'copilot',
    migrationId: string
  ): Promise<ProjectConfig> {
    const updatedConfig: ProjectConfig = {
      ...config,
      aiModel: targetModel,
      updatedAt: new Date().toISOString(),
      migrationHistory: [
        ...config.migrationHistory,
        {
          id: migrationId,
          fromModel: config.aiModel,
          toModel: targetModel,
          timestamp: new Date().toISOString(),
          success: true,
        },
      ],
    };

    await this.configManager.saveConfig(updatedConfig);
    return updatedConfig;
  }

  private async migrateSpecFiles(
    config: ProjectConfig,
    migration: MigrationState
  ): Promise<void> {
    // In a real implementation, this would handle model-specific
    // spec format migrations (e.g., Claude vs Gemini prompt formats)
    // For now, we'll just ensure files are accessible
    const specFiles = await this.getSpecFiles(config.specDirectory);

    for (const file of specFiles) {
      const content = await fs.readFile(file, 'utf8');
      // Perform any model-specific transformations here
      await fs.writeFile(file, content);
    }
  }

  private async validateMigration(config: ProjectConfig): Promise<void> {
    // Verify the updated configuration is valid
    if (!await fs.pathExists(config.configPath)) {
      throw new Error('Configuration file missing after migration');
    }

    const savedConfig = await this.configManager.loadConfig(config.configPath);
    if (savedConfig.aiModel !== config.aiModel) {
      throw new Error('Configuration not properly updated');
    }
  }

  private async rollbackMigration(migration: MigrationState): Promise<void> {
    const rollbackState = MigrationStateManager.startRollback(
      migration,
      'Migration failed, attempting rollback'
    );

    for (const file of migration.backup.files) {
      if (await fs.pathExists(file.backupPath)) {
        await fs.copy(file.backupPath, file.originalPath);
        rollbackState.rollback!.restoredFiles.push(file.originalPath);
      }
    }

    rollbackState.rollback!.success = true;
    rollbackState.rollback!.completedAt = new Date().toISOString();
  }

  private async createBackupPath(projectId: string): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    return path.join(this.backupDirectory, `${projectId}_${timestamp}`);
  }

  private async getSpecFiles(specDirectory: string): Promise<string[]> {
    const files: string[] = [];
    const items = await fs.readdir(specDirectory);

    for (const item of items) {
      const itemPath = path.join(specDirectory, item);
      const stats = await fs.stat(itemPath);

      if (stats.isDirectory()) {
        files.push(...(await this.getSpecFiles(itemPath)));
      } else if (item.endsWith('.md') || item.endsWith('.json')) {
        files.push(itemPath);
      }
    }

    return files;
  }

  private async getDirectorySize(dirPath: string): Promise<number> {
    let size = 0;
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

    return size;
  }

  private async calculateChecksum(path: string): Promise<string> {
    // Simplified checksum - in production, use crypto.createHash
    return `checksum_${Date.now()}_${Math.random()}`;
  }

  private async calculateFileChecksum(filePath: string): Promise<string> {
    // Simplified checksum - in production, use crypto.createHash
    const stats = await fs.stat(filePath);
    return `file_${stats.size}_${stats.mtime.getTime()}`;
  }
}