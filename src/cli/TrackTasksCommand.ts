import { Command } from 'commander';
import { TaskTracker } from '@services/TaskTracker';
import { ProjectDetector } from '@services/ProjectDetector';
import { TaskState } from '@models/TaskState';
import chalk from 'chalk';
import * as fs from 'fs-extra';
import * as path from 'path';

export interface TrackTasksOptions {
  sidebar?: boolean;
  format?: 'table' | 'json' | 'summary';
  filter?: string;
  watch?: boolean;
  export?: string;
}

export class TrackTasksCommand {
  private taskTracker: TaskTracker | null = null;
  private projectDetector: ProjectDetector;
  private watchMode = false;

  constructor() {
    this.projectDetector = new ProjectDetector();
  }

  create(): Command {
    const command = new Command('track-tasks');

    command
      .description('Manage task tracking UI and display task status')
      .argument('<action>', 'Action to perform (enable, disable, status, list, clear)')
      .option('--sidebar', 'Enable terminal sidebar UI for task tracking', false)
      .option('-f, --format <format>', 'Output format (table, json, summary)', 'table')
      .option('--filter <filter>', 'Filter tasks by status, category, or search term')
      .option('-w, --watch', 'Watch mode - continuously update task display', false)
      .option('--export <file>', 'Export tasks to file (JSON format)')
      .action(async (action, options) => {
        await this.execute(action, options);
      });

    return command;
  }

  async execute(action: string, options: TrackTasksOptions): Promise<void> {
    try {
      // Initialize task tracker
      await this.initializeTaskTracker();

      switch (action.toLowerCase()) {
        case 'enable':
          await this.enableTaskTracking(options);
          break;
        case 'disable':
          await this.disableTaskTracking(options);
          break;
        case 'status':
          await this.showTaskStatus(options);
          break;
        case 'list':
          await this.listTasks(options);
          break;
        case 'clear':
          await this.clearTasks(options);
          break;
        case 'stats':
          await this.showTaskStats(options);
          break;
        default:
          console.error(chalk.red(`❌ Unknown action: ${action}`));
          console.error(chalk.gray('Valid actions: enable, disable, status, list, clear, stats'));
          process.exit(1);
      }

    } catch (error) {
      console.error(chalk.red(`❌ Task tracking failed: ${error}`));
      process.exit(1);
    }
  }

  private async initializeTaskTracker(): Promise<void> {
    // Detect current project
    const detection = await this.projectDetector.detectProject();

    if (!detection.found || !detection.config) {
      throw new Error('No spec-kit project found. Run "specify detect-project" first.');
    }

    this.taskTracker = new TaskTracker(detection.config);
    await this.taskTracker.initialize();
  }

  private async enableTaskTracking(options: TrackTasksOptions): Promise<void> {
    console.log(chalk.blue('🚀 Enabling task tracking...'));

    if (!this.taskTracker) {
      throw new Error('Task tracker not initialized');
    }

    // Enable real-time updates
    const unsubscribe = this.taskTracker.onTasksChanged((tasks) => {
      if (options.sidebar || options.watch) {
        this.renderTaskSidebar(tasks);
      }
    });

    if (options.sidebar) {
      console.log(chalk.green('✅ Task tracking sidebar enabled'));
      console.log(chalk.gray('Task status will be displayed in sidebar during command execution'));
    } else {
      console.log(chalk.green('✅ Task tracking enabled'));
      console.log(chalk.gray('Use --sidebar for visual task tracking UI'));
    }

    // If watch mode, keep running
    if (options.watch) {
      console.log(chalk.blue('👀 Watch mode active - press Ctrl+C to stop'));
      this.watchMode = true;

      // Initial display
      const tasks = this.taskTracker.getAllTasks();
      await this.displayTasks(tasks, options);

      // Set up periodic updates
      const watchInterval = setInterval(async () => {
        if (!this.watchMode) {
          clearInterval(watchInterval);
          unsubscribe();
          return;
        }

        const updatedTasks = this.taskTracker!.getAllTasks();
        console.clear(); // Clear screen for fresh display
        console.log(chalk.blue(`📊 Task Status (Updated: ${new Date().toLocaleTimeString()})\n`));
        await this.displayTasks(updatedTasks, options);
      }, 2000); // Update every 2 seconds

      // Handle Ctrl+C
      process.on('SIGINT', () => {
        console.log(chalk.yellow('\n🛑 Stopping task tracking...'));
        this.watchMode = false;
        clearInterval(watchInterval);
        unsubscribe();
        process.exit(0);
      });

    } else {
      // Save tracking preferences
      await this.saveTrackingPreferences({ enabled: true, sidebar: options.sidebar });
    }
  }

  private async disableTaskTracking(options: TrackTasksOptions): Promise<void> {
    console.log(chalk.blue('🛑 Disabling task tracking...'));

    this.watchMode = false;

    await this.saveTrackingPreferences({ enabled: false, sidebar: false });

    console.log(chalk.green('✅ Task tracking disabled'));
  }

  private async showTaskStatus(options: TrackTasksOptions): Promise<void> {
    if (!this.taskTracker) {
      throw new Error('Task tracker not initialized');
    }

    const stats = this.taskTracker.getTaskStats();
    const tasks = this.taskTracker.getAllTasks();

    console.log(chalk.blue('📊 Task Tracking Status\n'));

    // Overall statistics
    console.log(chalk.white('Overall Progress:'));
    console.log(`  Total Tasks: ${chalk.cyan(stats.total)}`);
    console.log(`  Completed: ${chalk.green(stats.completed)} (${stats.percentComplete}%)`);
    console.log(`  In Progress: ${chalk.yellow(stats.inProgress)}`);
    console.log(`  Pending: ${chalk.gray(stats.pending)}`);
    console.log(`  Failed: ${chalk.red(stats.failed)}`);

    if (stats.estimatedTimeRemaining > 0) {
      const timeStr = this.formatDuration(stats.estimatedTimeRemaining);
      console.log(`  Estimated Time Remaining: ${chalk.cyan(timeStr)}`);
    }

    // Progress bar
    const progressBar = this.createProgressBar(stats.percentComplete);
    console.log(`\n${progressBar}\n`);

    // Ready tasks
    const readyTasks = this.taskTracker.getReadyTasks();
    if (readyTasks.length > 0) {
      console.log(chalk.green(`🟢 Ready to Start (${readyTasks.length}):`));
      readyTasks.slice(0, 5).forEach(task => {
        console.log(`  • ${task.title}`);
      });
      if (readyTasks.length > 5) {
        console.log(chalk.gray(`    ... and ${readyTasks.length - 5} more`));
      }
      console.log();
    }

    // Blocked tasks
    const blockedTasks = this.taskTracker.getBlockedTasks();
    if (blockedTasks.length > 0) {
      console.log(chalk.red(`🔴 Blocked Tasks (${blockedTasks.length}):`));
      blockedTasks.slice(0, 3).forEach(task => {
        console.log(`  • ${task.title}`);
        console.log(chalk.gray(`    Waiting for: ${task.dependencies.join(', ')}`));
      });
      if (blockedTasks.length > 3) {
        console.log(chalk.gray(`    ... and ${blockedTasks.length - 3} more`));
      }
      console.log();
    }

    // Parallel execution opportunities
    const parallelTasks = this.taskTracker.getParallelTasks();
    if (parallelTasks.length > 1) {
      console.log(chalk.blue(`⚡ Parallel Execution Available (${parallelTasks.length}):`));
      parallelTasks.forEach(task => {
        console.log(`  • ${task.title}`);
      });
      console.log();
    }

    if (options.format === 'json') {
      console.log(chalk.gray('\nDetailed data (JSON):'));
      console.log(JSON.stringify({ stats, readyTasks: readyTasks.length, blockedTasks: blockedTasks.length }, null, 2));
    }
  }

  private async listTasks(options: TrackTasksOptions): Promise<void> {
    if (!this.taskTracker) {
      throw new Error('Task tracker not initialized');
    }

    let tasks = this.taskTracker.getAllTasks();

    // Apply filters
    if (options.filter) {
      tasks = this.applyTaskFilter(tasks, options.filter);
    }

    if (tasks.length === 0) {
      console.log(chalk.yellow('📝 No tasks found'));
      return;
    }

    console.log(chalk.blue(`📋 Task List (${tasks.length} tasks)\n`));

    await this.displayTasks(tasks, options);

    // Export if requested
    if (options.export) {
      await this.exportTasks(tasks, options.export);
      console.log(chalk.green(`\n💾 Tasks exported to ${options.export}`));
    }
  }

  private async clearTasks(options: TrackTasksOptions): Promise<void> {
    if (!this.taskTracker) {
      throw new Error('Task tracker not initialized');
    }

    const stats = this.taskTracker.getTaskStats();

    if (stats.total === 0) {
      console.log(chalk.yellow('📝 No tasks to clear'));
      return;
    }

    console.log(chalk.yellow(`⚠️  This will remove all task tracking data (${stats.total} tasks)`));
    console.log(chalk.gray('Use Ctrl+C to cancel...'));

    // In a real CLI, you'd use a prompt library here
    await new Promise(resolve => setTimeout(resolve, 3000));

    const clearedCount = await this.taskTracker.clearCompleted();
    await this.taskTracker.reset();

    console.log(chalk.green(`✅ Task tracking data cleared (${stats.total} tasks removed)`));

    if (clearedCount > 0) {
      console.log(chalk.gray(`${clearedCount} completed tasks were cleared`));
    }
  }

  private async showTaskStats(options: TrackTasksOptions): Promise<void> {
    if (!this.taskTracker) {
      throw new Error('Task tracker not initialized');
    }

    const stats = this.taskTracker.getTaskStats();
    const tasks = this.taskTracker.getAllTasks();

    // Category breakdown
    const categoryStats = tasks.reduce((acc, task) => {
      const category = task.metadata.category;
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Priority breakdown
    const priorityStats = tasks.reduce((acc, task) => {
      acc[task.priority] = (acc[task.priority] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    console.log(chalk.blue('📈 Task Statistics\n'));

    // Overall stats
    console.log(chalk.white('📊 Overall:'));
    console.log(`  Total: ${stats.total}`);
    console.log(`  Completion Rate: ${stats.percentComplete}%`);
    console.log(`  Active: ${stats.inProgress}`);
    console.log(`  Failed: ${stats.failed}\n`);

    // Category breakdown
    console.log(chalk.white('📂 By Category:'));
    Object.entries(categoryStats).forEach(([category, count]) => {
      console.log(`  ${category}: ${count}`);
    });
    console.log();

    // Priority breakdown
    console.log(chalk.white('⭐ By Priority:'));
    Object.entries(priorityStats).forEach(([priority, count]) => {
      const color = this.getPriorityColor(priority);
      console.log(`  ${color(priority)}: ${count}`);
    });
    console.log();

    if (options.format === 'json') {
      console.log(JSON.stringify({
        stats,
        categoryStats,
        priorityStats,
        tasks: tasks.length,
      }, null, 2));
    }
  }

  private async displayTasks(tasks: TaskState[], options: TrackTasksOptions): Promise<void> {
    switch (options.format) {
      case 'json':
        console.log(JSON.stringify(tasks, null, 2));
        break;
      case 'summary':
        this.displayTaskSummary(tasks);
        break;
      case 'table':
      default:
        this.displayTaskTable(tasks);
        break;
    }
  }

  private displayTaskTable(tasks: TaskState[]): void {
    tasks.forEach(task => {
      const statusIcon = this.getStatusIcon(task.status);
      const priorityColor = this.getPriorityColor(task.priority);

      console.log(`${statusIcon} ${chalk.white(task.title)}`);
      console.log(`   ${chalk.gray(task.description)}`);
      console.log(`   Priority: ${priorityColor(task.priority)} | Category: ${chalk.cyan(task.metadata.category)} | Progress: ${task.progress.percentage}%`);

      if (task.status === 'failed' && task.metadata.errorMessage) {
        console.log(`   ${chalk.red('Error:')} ${task.metadata.errorMessage}`);
      }

      if (task.dependencies.length > 0) {
        console.log(`   ${chalk.gray('Depends on:')} ${task.dependencies.join(', ')}`);
      }

      console.log();
    });
  }

  private displayTaskSummary(tasks: TaskState[]): void {
    const grouped = tasks.reduce((acc, task) => {
      acc[task.status] = (acc[task.status] || []);
      acc[task.status].push(task);
      return acc;
    }, {} as Record<string, TaskState[]>);

    Object.entries(grouped).forEach(([status, statusTasks]) => {
      const icon = this.getStatusIcon(status as TaskState['status']);
      console.log(`${icon} ${chalk.white(status.toUpperCase())} (${statusTasks.length})`);

      statusTasks.forEach(task => {
        console.log(`   • ${task.title}`);
      });

      console.log();
    });
  }

  private renderTaskSidebar(tasks: TaskState[]): void {
    // This would render a terminal UI sidebar
    // For now, just show a simple status line
    const stats = {
      completed: tasks.filter(t => t.status === 'completed').length,
      inProgress: tasks.filter(t => t.status === 'in_progress').length,
      pending: tasks.filter(t => t.status === 'pending').length,
      failed: tasks.filter(t => t.status === 'failed').length,
    };

    const total = tasks.length;
    const progress = total > 0 ? Math.round((stats.completed / total) * 100) : 0;

    console.log(chalk.gray(`[Tasks: ${progress}% | ✅${stats.completed} ⚡${stats.inProgress} ⏳${stats.pending} ❌${stats.failed}]`));
  }

  private applyTaskFilter(tasks: TaskState[], filter: string): TaskState[] {
    const lowerFilter = filter.toLowerCase();

    // Status filter
    if (['pending', 'in_progress', 'completed', 'failed', 'skipped'].includes(lowerFilter)) {
      return tasks.filter(task => task.status === lowerFilter);
    }

    // Category filter
    if (['setup', 'test', 'implementation', 'ui', 'integration', 'polish'].includes(lowerFilter)) {
      return tasks.filter(task => task.metadata.category === lowerFilter);
    }

    // Priority filter
    if (['low', 'medium', 'high', 'critical'].includes(lowerFilter)) {
      return tasks.filter(task => task.priority === lowerFilter);
    }

    // Text search
    return tasks.filter(task =>
      task.title.toLowerCase().includes(lowerFilter) ||
      task.description.toLowerCase().includes(lowerFilter) ||
      task.id.toLowerCase().includes(lowerFilter)
    );
  }

  private getStatusIcon(status: TaskState['status']): string {
    switch (status) {
      case 'completed': return chalk.green('✅');
      case 'in_progress': return chalk.yellow('⚡');
      case 'pending': return chalk.gray('⏳');
      case 'failed': return chalk.red('❌');
      case 'skipped': return chalk.blue('⏭️');
      default: return '•';
    }
  }

  private getPriorityColor(priority: string): (text: string) => string {
    switch (priority) {
      case 'critical': return chalk.red.bold;
      case 'high': return chalk.red;
      case 'medium': return chalk.yellow;
      case 'low': return chalk.gray;
      default: return chalk.white;
    }
  }

  private createProgressBar(percentage: number, width: number = 30): string {
    const filled = Math.round((percentage / 100) * width);
    const empty = width - filled;

    const bar = chalk.green('█').repeat(filled) + chalk.gray('░').repeat(empty);
    return `${bar} ${percentage}%`;
  }

  private formatDuration(milliseconds: number): string {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  private async saveTrackingPreferences(prefs: { enabled: boolean; sidebar?: boolean }): Promise<void> {
    // Save to project configuration or local preferences file
    // Implementation would depend on config management approach
  }

  private async exportTasks(tasks: TaskState[], filePath: string): Promise<void> {
    const exportData = {
      exportedAt: new Date().toISOString(),
      taskCount: tasks.length,
      tasks: tasks,
    };

    await fs.writeJson(filePath, exportData, { spaces: 2 });
  }

  getUsageExamples(): string[] {
    return [
      'specify track-tasks enable --sidebar',
      'specify track-tasks status',
      'specify track-tasks list --filter completed',
      'specify track-tasks list --watch --format summary',
      'specify track-tasks clear',
      'specify track-tasks stats --format json',
    ];
  }
}