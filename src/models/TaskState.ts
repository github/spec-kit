export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';

export interface TaskState {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: 'low' | 'medium' | 'high' | 'critical';
  tags: string[];
  createdAt: string;
  updatedAt: string;
  startedAt?: string;
  completedAt?: string;
  estimatedDuration?: number;
  actualDuration?: number;
  dependencies: string[];
  blockedBy: string[];
  progress: TaskProgress;
  metadata: TaskMetadata;
}

export interface TaskProgress {
  percentage: number;
  currentStep?: string;
  totalSteps?: number;
  completedSteps?: number;
  lastActivity: string;
}

export interface TaskMetadata {
  category: 'setup' | 'test' | 'implementation' | 'ui' | 'integration' | 'polish';
  filePath?: string;
  isParallel: boolean;
  requirements?: string[];
  outputs?: string[];
  errorMessage?: string;
  retryCount: number;
  maxRetries: number;
}

export class TaskStateManager {
  static create(params: {
    id: string;
    title: string;
    description: string;
    category: TaskMetadata['category'];
    isParallel?: boolean;
    dependencies?: string[];
    priority?: TaskState['priority'];
  }): TaskState {
    const now = new Date().toISOString();
    return {
      ...params,
      status: 'pending',
      priority: params.priority || 'medium',
      tags: [],
      createdAt: now,
      updatedAt: now,
      dependencies: params.dependencies || [],
      blockedBy: [],
      progress: {
        percentage: 0,
        lastActivity: now,
      },
      metadata: {
        category: params.category,
        isParallel: params.isParallel || false,
        retryCount: 0,
        maxRetries: 3,
      },
    };
  }

  static transition(
    task: TaskState,
    newStatus: TaskStatus,
    metadata?: Partial<TaskMetadata>
  ): TaskState {
    const now = new Date().toISOString();
    const updated: TaskState = {
      ...task,
      status: newStatus,
      updatedAt: now,
      progress: {
        ...task.progress,
        lastActivity: now,
      },
      metadata: {
        ...task.metadata,
        ...metadata,
      },
    };

    // Set timestamps based on status transitions
    if (newStatus === 'in_progress' && !task.startedAt) {
      updated.startedAt = now;
      updated.progress.percentage = 10;
    }

    if (newStatus === 'completed' || newStatus === 'failed') {
      updated.completedAt = now;
      updated.progress.percentage = newStatus === 'completed' ? 100 : 0;

      if (updated.startedAt) {
        updated.actualDuration =
          new Date(now).getTime() - new Date(updated.startedAt).getTime();
      }
    }

    return updated;
  }

  static updateProgress(
    task: TaskState,
    progress: Partial<TaskProgress>
  ): TaskState {
    return {
      ...task,
      updatedAt: new Date().toISOString(),
      progress: {
        ...task.progress,
        ...progress,
        lastActivity: new Date().toISOString(),
      },
    };
  }

  static canStart(task: TaskState, completedTaskIds: string[]): boolean {
    if (task.status !== 'pending') return false;
    if (task.blockedBy.length > 0) return false;

    return task.dependencies.every(depId => completedTaskIds.includes(depId));
  }

  static getParallelTasks(tasks: TaskState[]): TaskState[] {
    return tasks.filter(task =>
      task.metadata.isParallel &&
      task.status === 'pending'
    );
  }
}