export type MigrationStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'rolled_back';

export interface MigrationState {
  id: string;
  fromModel: 'claude' | 'gemini' | 'copilot';
  toModel: 'claude' | 'gemini' | 'copilot';
  projectId: string;
  status: MigrationStatus;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  steps: MigrationStep[];
  backup: BackupInfo;
  rollback?: RollbackInfo;
  metadata: MigrationMetadata;
}

export interface MigrationStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  order: number;
  startedAt?: string;
  completedAt?: string;
  errorMessage?: string;
  rollbackCommand?: string;
  requiredFiles: string[];
  outputFiles: string[];
}

export interface BackupInfo {
  id: string;
  path: string;
  createdAt: string;
  size: number;
  checksum: string;
  files: BackupFile[];
}

export interface BackupFile {
  originalPath: string;
  backupPath: string;
  checksum: string;
  size: number;
}

export interface RollbackInfo {
  triggeredAt: string;
  reason: string;
  completedAt?: string;
  success: boolean;
  restoredFiles: string[];
  errorMessage?: string;
}

export interface MigrationMetadata {
  version: string;
  dryRun: boolean;
  preserveHistory: boolean;
  userConfirmation: boolean;
  automaticRollback: boolean;
  skipValidation: boolean;
  customSettings: Record<string, unknown>;
}

export class MigrationStateManager {
  static create(params: {
    fromModel: 'claude' | 'gemini' | 'copilot';
    toModel: 'claude' | 'gemini' | 'copilot';
    projectId: string;
    backupPath: string;
    dryRun?: boolean;
  }): MigrationState {
    const now = new Date().toISOString();
    const migrationId = `migration_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    return {
      id: migrationId,
      fromModel: params.fromModel,
      toModel: params.toModel,
      projectId: params.projectId,
      status: 'pending',
      startedAt: now,
      steps: this.getDefaultSteps(params.fromModel, params.toModel),
      backup: {
        id: `backup_${migrationId}`,
        path: params.backupPath,
        createdAt: now,
        size: 0,
        checksum: '',
        files: [],
      },
      metadata: {
        version: '0.1.0',
        dryRun: params.dryRun || false,
        preserveHistory: true,
        userConfirmation: false,
        automaticRollback: true,
        skipValidation: false,
        customSettings: {},
      },
    };
  }

  private static getDefaultSteps(
    fromModel: 'claude' | 'gemini' | 'copilot',
    toModel: 'claude' | 'gemini' | 'copilot'
  ): MigrationStep[] {
    const baseSteps: Omit<MigrationStep, 'id'>[] = [
      {
        name: 'validate_project',
        description: 'Validate project configuration and structure',
        status: 'pending',
        order: 1,
        requiredFiles: ['.specify/config.json'],
        outputFiles: [],
      },
      {
        name: 'create_backup',
        description: 'Create backup of current project state',
        status: 'pending',
        order: 2,
        requiredFiles: [],
        outputFiles: [],
      },
      {
        name: 'update_config',
        description: `Update AI model from ${fromModel} to ${toModel}`,
        status: 'pending',
        order: 3,
        requiredFiles: ['.specify/config.json'],
        outputFiles: ['.specify/config.json'],
      },
      {
        name: 'migrate_specs',
        description: 'Migrate specification files to new model format',
        status: 'pending',
        order: 4,
        requiredFiles: [],
        outputFiles: [],
      },
      {
        name: 'update_tasks',
        description: 'Update task tracking configuration',
        status: 'pending',
        order: 5,
        requiredFiles: [],
        outputFiles: [],
      },
      {
        name: 'validate_migration',
        description: 'Validate migration success and functionality',
        status: 'pending',
        order: 6,
        requiredFiles: [],
        outputFiles: [],
      },
    ];

    return baseSteps.map((step, index) => ({
      ...step,
      id: `step_${index + 1}_${step.name}`,
    }));
  }

  static updateStep(
    migration: MigrationState,
    stepId: string,
    updates: Partial<MigrationStep>
  ): MigrationState {
    const steps = migration.steps.map(step =>
      step.id === stepId ? { ...step, ...updates } : step
    );

    return {
      ...migration,
      steps,
    };
  }

  static startRollback(
    migration: MigrationState,
    reason: string
  ): MigrationState {
    return {
      ...migration,
      status: 'rolled_back',
      rollback: {
        triggeredAt: new Date().toISOString(),
        reason,
        success: false,
        restoredFiles: [],
      },
    };
  }

  static complete(migration: MigrationState, success: boolean): MigrationState {
    const now = new Date().toISOString();
    const duration = migration.startedAt
      ? new Date(now).getTime() - new Date(migration.startedAt).getTime()
      : 0;

    return {
      ...migration,
      status: success ? 'completed' : 'failed',
      completedAt: now,
      duration,
    };
  }

  static canRollback(migration: MigrationState): boolean {
    return (
      migration.status !== 'rolled_back' &&
      migration.backup.files.length > 0 &&
      migration.metadata.automaticRollback
    );
  }
}