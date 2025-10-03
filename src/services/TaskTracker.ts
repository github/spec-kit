import { TaskState, TaskStateManager } from '@models/TaskState';
import { ProjectConfig } from '@models/ProjectConfig';
import * as fs from 'fs-extra';
import * as path from 'path';

export interface TaskTrackingOptions {
  enableRealTimeUpdates: boolean;
  autoSave: boolean;
  maxHistoryItems: number;
  notificationThreshold: number;
}

export interface TaskFilter {
  status?: TaskState['status'][];
  category?: TaskState['metadata']['category'][];
  priority?: TaskState['priority'][];
  tags?: string[];
  search?: string;
}

export interface TaskStats {
  total: number;
  pending: number;
  inProgress: number;
  completed: number;
  failed: number;
  skipped: number;
  percentComplete: number;
  estimatedTimeRemaining: number;
}

export class TaskTracker {
  private tasks: Map<string, TaskState> = new Map();
  private taskFilePath: string;
  private options: TaskTrackingOptions;
  private listeners: Array<(tasks: TaskState[]) => void> = [];
  private saveTimeout: NodeJS.Timeout | null = null;

  constructor(
    projectConfig: ProjectConfig,
    options: Partial<TaskTrackingOptions> = {}
  ) {
    this.taskFilePath = path.join(
      path.dirname(projectConfig.configPath),
      'tasks.json'
    );

    this.options = {
      enableRealTimeUpdates: true,
      autoSave: true,
      maxHistoryItems: 1000,
      notificationThreshold: 5000, // 5 seconds
      ...options,
    };
  }

  async initialize(): Promise<void> {
    await this.loadTasks();
  }

  async addTask(taskData: {
    id: string;
    title: string;
    description: string;
    category: TaskState['metadata']['category'];
    isParallel?: boolean;
    dependencies?: string[];
    priority?: TaskState['priority'];
    estimatedDuration?: number;
    tags?: string[];
  }): Promise<TaskState> {
    const task = TaskStateManager.create(taskData);

    if (taskData.estimatedDuration) {
      task.estimatedDuration = taskData.estimatedDuration;
    }

    if (taskData.tags) {
      task.tags = taskData.tags;
    }

    this.tasks.set(task.id, task);
    await this.notifyListeners();
    await this.scheduleAutoSave();

    return task;
  }

  async updateTask(
    taskId: string,
    updates: Partial<TaskState>
  ): Promise<TaskState | null> {
    const task = this.tasks.get(taskId);
    if (!task) return null;

    const updatedTask = {
      ...task,
      ...updates,
      updatedAt: new Date().toISOString(),
    };

    this.tasks.set(taskId, updatedTask);
    await this.notifyListeners();
    await this.scheduleAutoSave();

    return updatedTask;
  }

  async updateTaskStatus(
    taskId: string,
    status: TaskState['status'],
    metadata?: Partial<TaskState['metadata']>
  ): Promise<TaskState | null> {
    const task = this.tasks.get(taskId);
    if (!task) return null;

    const updatedTask = TaskStateManager.transition(task, status, metadata);
    this.tasks.set(taskId, updatedTask);

    await this.notifyListeners();
    await this.scheduleAutoSave();

    return updatedTask;
  }

  async updateTaskProgress(
    taskId: string,
    progress: Partial<TaskState['progress']>
  ): Promise<TaskState | null> {
    const task = this.tasks.get(taskId);
    if (!task) return null;

    const updatedTask = TaskStateManager.updateProgress(task, progress);
    this.tasks.set(taskId, updatedTask);

    await this.notifyListeners();
    await this.scheduleAutoSave();

    return updatedTask;
  }

  getTask(taskId: string): TaskState | null {
    return this.tasks.get(taskId) || null;
  }

  getAllTasks(): TaskState[] {
    return Array.from(this.tasks.values());
  }

  getFilteredTasks(filter: TaskFilter): TaskState[] {
    let filtered = this.getAllTasks();

    if (filter.status) {
      filtered = filtered.filter(task => filter.status!.includes(task.status));
    }

    if (filter.category) {
      filtered = filtered.filter(task =>
        filter.category!.includes(task.metadata.category)
      );
    }

    if (filter.priority) {
      filtered = filtered.filter(task => filter.priority!.includes(task.priority));
    }

    if (filter.tags && filter.tags.length > 0) {
      filtered = filtered.filter(task =>
        filter.tags!.some(tag => task.tags.includes(tag))
      );
    }

    if (filter.search) {
      const searchLower = filter.search.toLowerCase();
      filtered = filtered.filter(task =>
        task.title.toLowerCase().includes(searchLower) ||
        task.description.toLowerCase().includes(searchLower) ||
        task.id.toLowerCase().includes(searchLower)
      );
    }

    return filtered;
  }

  getTaskStats(): TaskStats {
    const tasks = this.getAllTasks();
    const total = tasks.length;

    if (total === 0) {
      return {
        total: 0,
        pending: 0,
        inProgress: 0,
        completed: 0,
        failed: 0,
        skipped: 0,
        percentComplete: 0,
        estimatedTimeRemaining: 0,
      };
    }

    const statusCounts = tasks.reduce((acc, task) => {
      acc[task.status] = (acc[task.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const completed = statusCounts.completed || 0;
    const percentComplete = Math.round((completed / total) * 100);

    // Calculate estimated time remaining
    const remainingTasks = tasks.filter(t =>
      ['pending', 'in_progress'].includes(t.status)
    );
    const estimatedTimeRemaining = remainingTasks.reduce((sum, task) => {
      return sum + (task.estimatedDuration || 0);
    }, 0);

    return {
      total,
      pending: statusCounts.pending || 0,
      inProgress: statusCounts.in_progress || 0,
      completed,
      failed: statusCounts.failed || 0,
      skipped: statusCounts.skipped || 0,
      percentComplete,
      estimatedTimeRemaining,
    };
  }

  getReadyTasks(): TaskState[] {
    const completedTaskIds = this.getAllTasks()
      .filter(t => t.status === 'completed')
      .map(t => t.id);

    return this.getAllTasks().filter(task =>
      TaskStateManager.canStart(task, completedTaskIds)
    );
  }

  getParallelTasks(): TaskState[] {
    const allTasks = this.getAllTasks();
    return TaskStateManager.getParallelTasks(allTasks);
  }

  getBlockedTasks(): TaskState[] {
    const completedTaskIds = this.getAllTasks()
      .filter(t => t.status === 'completed')
      .map(t => t.id);

    return this.getAllTasks().filter(task => {
      if (task.status !== 'pending') return false;
      return !TaskStateManager.canStart(task, completedTaskIds);
    });
  }

  async markTaskAsFailed(
    taskId: string,
    errorMessage: string,
    allowRetry: boolean = true
  ): Promise<TaskState | null> {
    const task = this.tasks.get(taskId);
    if (!task) return null;

    const updatedTask = TaskStateManager.transition(task, 'failed', {
      errorMessage,
      retryCount: allowRetry ? task.metadata.retryCount + 1 : task.metadata.maxRetries,
    });

    this.tasks.set(taskId, updatedTask);
    await this.notifyListeners();
    await this.scheduleAutoSave();

    return updatedTask;
  }

  async retryTask(taskId: string): Promise<TaskState | null> {
    const task = this.tasks.get(taskId);
    if (!task || task.status !== 'failed') return null;

    if (task.metadata.retryCount >= task.metadata.maxRetries) {
      return null; // Max retries exceeded
    }

    const updatedTask = TaskStateManager.transition(task, 'pending', {
      errorMessage: undefined,
    });

    this.tasks.set(taskId, updatedTask);
    await this.notifyListeners();
    await this.scheduleAutoSave();

    return updatedTask;
  }

  onTasksChanged(listener: (tasks: TaskState[]) => void): () => void {
    this.listeners.push(listener);

    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  async saveTasks(): Promise<void> {
    const tasksData = {
      tasks: Object.fromEntries(this.tasks),
      savedAt: new Date().toISOString(),
      version: '1.0',
    };

    await fs.ensureDir(path.dirname(this.taskFilePath));
    await fs.writeJson(this.taskFilePath, tasksData, { spaces: 2 });
  }

  async loadTasks(): Promise<void> {
    try {
      if (await fs.pathExists(this.taskFilePath)) {
        const data = await fs.readJson(this.taskFilePath);

        if (data.tasks) {
          this.tasks.clear();
          for (const [id, taskData] of Object.entries(data.tasks)) {
            this.tasks.set(id, taskData as TaskState);
          }
        }
      }
    } catch (error) {
      // If loading fails, start with empty task list
      this.tasks.clear();
    }
  }

  async clearCompleted(): Promise<number> {
    const completedTasks = this.getAllTasks().filter(t => t.status === 'completed');

    for (const task of completedTasks) {
      this.tasks.delete(task.id);
    }

    await this.notifyListeners();
    await this.scheduleAutoSave();

    return completedTasks.length;
  }

  async reset(): Promise<void> {
    this.tasks.clear();
    await this.notifyListeners();
    await this.saveTasks();
  }

  private async notifyListeners(): Promise<void> {
    if (!this.options.enableRealTimeUpdates) return;

    const tasks = this.getAllTasks();
    for (const listener of this.listeners) {
      try {
        listener(tasks);
      } catch (error) {
        // Continue notifying other listeners even if one fails
      }
    }
  }

  private async scheduleAutoSave(): Promise<void> {
    if (!this.options.autoSave) return;

    if (this.saveTimeout) {
      clearTimeout(this.saveTimeout);
    }

    this.saveTimeout = setTimeout(async () => {
      try {
        await this.saveTasks();
      } catch (error) {
        // Auto-save failure - could log this
      }
    }, 1000); // Save after 1 second of inactivity
  }
}