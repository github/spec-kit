import { ProjectConfig, ProjectConfigValidator } from '@models/ProjectConfig';
import * as fs from 'fs-extra';
import * as path from 'path';

export interface DetectionResult {
  found: boolean;
  projectPath?: string;
  config?: ProjectConfig;
  issues: DetectionIssue[];
  suggestions: string[];
}

export interface DetectionIssue {
  type: 'error' | 'warning' | 'info';
  message: string;
  path?: string;
  fixable: boolean;
}

export interface DetectionOptions {
  searchDepth?: number;
  validateConfig?: boolean;
  autoFix?: boolean;
  includeDrafts?: boolean;
}

export class ProjectDetector {
  private static readonly SPECIFY_DIR = '.specify';
  private static readonly CONFIG_FILE = 'config.json';
  private static readonly SPEC_DIR = 'specs';

  async detectProject(
    startPath: string = process.cwd(),
    options: DetectionOptions = {}
  ): Promise<DetectionResult> {
    const {
      searchDepth = 5,
      validateConfig = true,
      autoFix = false,
      includeDrafts = false,
    } = options;

    const issues: DetectionIssue[] = [];
    const suggestions: string[] = [];

    try {
      // Search for .specify directory
      const projectPath = await this.findSpecifyDirectory(startPath, searchDepth);

      if (!projectPath) {
        return {
          found: false,
          issues: [{
            type: 'info',
            message: 'No .specify directory found in current path or parent directories',
            fixable: true,
          }],
          suggestions: [
            'Run "specify init" to initialize a new project',
            'Ensure you are in the correct project directory',
          ],
        };
      }

      // Check for config file
      const configPath = path.join(projectPath, ProjectDetector.SPECIFY_DIR, ProjectDetector.CONFIG_FILE);

      if (!await fs.pathExists(configPath)) {
        issues.push({
          type: 'error',
          message: 'Configuration file not found',
          path: configPath,
          fixable: true,
        });

        if (autoFix) {
          await this.createDefaultConfig(projectPath);
          suggestions.push('Created default configuration file');
        } else {
          suggestions.push('Run "specify detect-project --auto-fix" to create default configuration');
        }
      }

      // Load and validate configuration
      let config: ProjectConfig | undefined;

      if (await fs.pathExists(configPath)) {
        try {
          const configData = await fs.readJson(configPath);

          if (validateConfig && !ProjectConfigValidator.validate(configData)) {
            issues.push({
              type: 'error',
              message: 'Invalid configuration file format',
              path: configPath,
              fixable: true,
            });

            if (autoFix) {
              config = await this.repairConfig(configData, projectPath);
              suggestions.push('Repaired configuration file');
            } else {
              suggestions.push('Run with --auto-fix to repair configuration');
            }
          } else {
            config = configData as ProjectConfig;
          }
        } catch (error) {
          issues.push({
            type: 'error',
            message: `Failed to read configuration: ${error}`,
            path: configPath,
            fixable: false,
          });
        }
      }

      // Validate project structure
      await this.validateProjectStructure(projectPath, config, issues, suggestions, includeDrafts);

      // Check for migration issues
      if (config) {
        await this.checkMigrationIssues(config, issues, suggestions);
      }

      return {
        found: true,
        projectPath,
        config,
        issues,
        suggestions,
      };

    } catch (error) {
      return {
        found: false,
        issues: [{
          type: 'error',
          message: `Detection failed: ${error}`,
          fixable: false,
        }],
        suggestions: ['Check file permissions and try again'],
      };
    }
  }

  async validateProject(
    projectPath: string,
    config: ProjectConfig
  ): Promise<DetectionIssue[]> {
    const issues: DetectionIssue[] = [];

    // Check required directories
    const requiredDirs = [
      path.join(projectPath, ProjectDetector.SPECIFY_DIR),
      config.specDirectory,
    ];

    for (const dir of requiredDirs) {
      if (!await fs.pathExists(dir)) {
        issues.push({
          type: 'error',
          message: `Required directory missing: ${dir}`,
          path: dir,
          fixable: true,
        });
      }
    }

    // Check configuration file
    if (!await fs.pathExists(config.configPath)) {
      issues.push({
        type: 'error',
        message: 'Configuration file missing',
        path: config.configPath,
        fixable: true,
      });
    }

    // Validate AI model settings
    const modelSettings = await import('@models/AIModelSettings');
    const settings = modelSettings.AIModelSettingsProvider.getSettings(config.aiModel);

    if (!settings) {
      issues.push({
        type: 'error',
        message: `Unknown AI model: ${config.aiModel}`,
        fixable: false,
      });
    }

    // Check for spec files
    const specFiles = await this.getSpecFiles(config.specDirectory);
    if (specFiles.length === 0) {
      issues.push({
        type: 'warning',
        message: 'No specification files found',
        path: config.specDirectory,
        fixable: false,
      });
    }

    return issues;
  }

  async repairProject(
    projectPath: string,
    config?: ProjectConfig
  ): Promise<DetectionResult> {
    const issues: DetectionIssue[] = [];
    const suggestions: string[] = [];

    try {
      // Ensure .specify directory exists
      const specifyDir = path.join(projectPath, ProjectDetector.SPECIFY_DIR);
      await fs.ensureDir(specifyDir);

      // Create or repair config
      let repairedConfig = config;
      if (!config) {
        repairedConfig = await this.createDefaultConfig(projectPath);
        suggestions.push('Created default configuration');
      } else {
        const validation = await this.validateProject(projectPath, config);
        for (const issue of validation) {
          if (issue.fixable) {
            await this.fixIssue(issue, projectPath, config);
            suggestions.push(`Fixed: ${issue.message}`);
          } else {
            issues.push(issue);
          }
        }
      }

      // Ensure spec directory exists
      if (repairedConfig) {
        await fs.ensureDir(repairedConfig.specDirectory);
      }

      return {
        found: true,
        projectPath,
        config: repairedConfig,
        issues,
        suggestions,
      };

    } catch (error) {
      return {
        found: false,
        issues: [{
          type: 'error',
          message: `Repair failed: ${error}`,
          fixable: false,
        }],
        suggestions: [],
      };
    }
  }

  private async findSpecifyDirectory(
    startPath: string,
    maxDepth: number
  ): Promise<string | null> {
    let currentPath = path.resolve(startPath);
    let depth = 0;

    while (depth <= maxDepth) {
      const specifyPath = path.join(currentPath, ProjectDetector.SPECIFY_DIR);

      if (await fs.pathExists(specifyPath)) {
        const stats = await fs.stat(specifyPath);
        if (stats.isDirectory()) {
          return currentPath;
        }
      }

      const parentPath = path.dirname(currentPath);
      if (parentPath === currentPath) {
        break; // Reached root directory
      }

      currentPath = parentPath;
      depth++;
    }

    return null;
  }

  private async createDefaultConfig(projectPath: string): Promise<ProjectConfig> {
    const projectName = path.basename(projectPath);
    const configPath = path.join(projectPath, ProjectDetector.SPECIFY_DIR, ProjectDetector.CONFIG_FILE);
    const specDirectory = path.join(projectPath, ProjectDetector.SPEC_DIR);

    const config = ProjectConfigValidator.create({
      projectId: `project_${Date.now()}`,
      name: projectName,
      aiModel: 'claude', // Default to Claude
      specDirectory,
      configPath,
    });

    config.isInitialized = true;

    await fs.ensureDir(path.dirname(configPath));
    await fs.writeJson(configPath, config, { spaces: 2 });

    return config;
  }

  private async repairConfig(
    configData: any,
    projectPath: string
  ): Promise<ProjectConfig> {
    const projectName = path.basename(projectPath);
    const configPath = path.join(projectPath, ProjectDetector.SPECIFY_DIR, ProjectDetector.CONFIG_FILE);

    // Merge with defaults for missing fields
    const repairedConfig: ProjectConfig = {
      projectId: configData.projectId || `project_${Date.now()}`,
      name: configData.name || projectName,
      aiModel: configData.aiModel || 'claude',
      version: configData.version || '0.1.0',
      createdAt: configData.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      specDirectory: configData.specDirectory || path.join(projectPath, ProjectDetector.SPEC_DIR),
      configPath: configData.configPath || configPath,
      isInitialized: configData.isInitialized !== undefined ? configData.isInitialized : true,
      migrationHistory: configData.migrationHistory || [],
    };

    await fs.writeJson(configPath, repairedConfig, { spaces: 2 });
    return repairedConfig;
  }

  private async validateProjectStructure(
    projectPath: string,
    config: ProjectConfig | undefined,
    issues: DetectionIssue[],
    suggestions: string[],
    includeDrafts: boolean
  ): Promise<void> {
    // Check for common project files
    const expectedFiles = [
      'package.json',
      'tsconfig.json',
      '.gitignore',
    ];

    for (const file of expectedFiles) {
      const filePath = path.join(projectPath, file);
      if (!await fs.pathExists(filePath)) {
        issues.push({
          type: 'info',
          message: `Recommended file missing: ${file}`,
          path: filePath,
          fixable: false,
        });
      }
    }

    // Check spec directory structure
    if (config) {
      const specDir = config.specDirectory;
      if (await fs.pathExists(specDir)) {
        const specFiles = await this.getSpecFiles(specDir);

        if (specFiles.length === 0 && !includeDrafts) {
          suggestions.push('No specification files found - consider running "specify init" to create initial specs');
        }

        // Check for common spec file patterns
        const hasFeatureSpecs = specFiles.some(f => f.includes('spec.md'));
        const hasPlans = specFiles.some(f => f.includes('plan.md'));
        const hasTasks = specFiles.some(f => f.includes('tasks.md'));

        if (!hasFeatureSpecs && specFiles.length > 0) {
          issues.push({
            type: 'info',
            message: 'No feature specification files (spec.md) found',
            fixable: false,
          });
        }
      }
    }
  }

  private async checkMigrationIssues(
    config: ProjectConfig,
    issues: DetectionIssue[],
    suggestions: string[]
  ): Promise<void> {
    // Check for incomplete migrations
    const incompleteMigrations = config.migrationHistory.filter(m => !m.success);

    if (incompleteMigrations.length > 0) {
      issues.push({
        type: 'warning',
        message: `${incompleteMigrations.length} incomplete migration(s) found`,
        fixable: true,
      });
      suggestions.push('Run "specify reset-project --repair" to clean up incomplete migrations');
    }

    // Check for migration backups
    const backupDir = path.join(path.dirname(config.configPath), '..', 'backups');
    if (await fs.pathExists(backupDir)) {
      const backups = await fs.readdir(backupDir);
      if (backups.length > 10) {
        suggestions.push(`${backups.length} backup files found - consider cleaning old backups`);
      }
    }
  }

  private async getSpecFiles(specDirectory: string): Promise<string[]> {
    const files: string[] = [];

    try {
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
    } catch (error) {
      // Directory might not exist or be accessible
    }

    return files;
  }

  private async fixIssue(
    issue: DetectionIssue,
    projectPath: string,
    config: ProjectConfig
  ): Promise<void> {
    if (!issue.path) return;

    switch (issue.type) {
      case 'error':
        if (issue.message.includes('directory missing')) {
          await fs.ensureDir(issue.path);
        } else if (issue.message.includes('Configuration file')) {
          await this.createDefaultConfig(projectPath);
        }
        break;
    }
  }
}