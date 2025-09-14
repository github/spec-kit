import blessed from 'blessed';
import { TaskTrackingSidebar } from './TaskTrackingSidebar';
import { TaskState } from '@models/TaskState';

export interface LayoutConfiguration {
  sidebarEnabled: boolean;
  sidebarPosition: 'left' | 'right';
  sidebarWidth: number | string;
  mainContentPadding: number;
  theme: LayoutTheme;
}

export interface LayoutTheme {
  background: string;
  border: string;
  text: string;
  accent: string;
}

export interface ContentArea {
  log: blessed.Widgets.BoxElement;
  input?: blessed.Widgets.TextboxElement;
  status: blessed.Widgets.BoxElement;
}

export class LayoutManager {
  private screen: blessed.Widgets.Screen;
  private sidebar: TaskTrackingSidebar | null = null;
  private mainContent: blessed.Widgets.BoxElement | null = null;
  private contentAreas: ContentArea | null = null;
  private config: LayoutConfiguration;
  private isInitialized = false;

  constructor(config: Partial<LayoutConfiguration> = {}) {
    this.config = {
      sidebarEnabled: false,
      sidebarPosition: 'right',
      sidebarWidth: '25%',
      mainContentPadding: 1,
      theme: {
        background: 'black',
        border: 'gray',
        text: 'white',
        accent: 'cyan',
      },
      ...config,
    };

    this.screen = blessed.screen({
      smartCSR: true,
      title: 'Specify CLI',
      dockBorders: true,
      fullUnicode: true,
    });

    this.setupGlobalEvents();
  }

  initialize(): void {
    if (this.isInitialized) return;

    this.createLayout();
    this.isInitialized = true;
  }

  private createLayout(): void {
    this.createMainContent();

    if (this.config.sidebarEnabled) {
      this.enableSidebar();
    }

    this.createContentAreas();
    this.render();
  }

  private createMainContent(): void {
    const sidebarWidth = this.config.sidebarEnabled
      ? (typeof this.config.sidebarWidth === 'string'
          ? parseInt(this.config.sidebarWidth)
          : this.config.sidebarWidth)
      : 0;

    const mainLeft = this.config.sidebarEnabled && this.config.sidebarPosition === 'left'
      ? this.config.sidebarWidth
      : 0;

    const mainWidth = this.config.sidebarEnabled
      ? `100%-${sidebarWidth}%`
      : '100%';

    this.mainContent = blessed.box({
      top: 0,
      left: mainLeft,
      width: mainWidth,
      height: '100%',
      style: {
        bg: this.config.theme.background,
      },
    });

    this.screen.append(this.mainContent);
  }

  private createContentAreas(): void {
    if (!this.mainContent) return;

    // Status bar at the top
    const statusBar = blessed.box({
      top: 0,
      left: 0,
      width: '100%',
      height: 3,
      border: {
        type: 'line',
      },
      style: {
        border: {
          fg: this.config.theme.border,
        },
        bg: this.config.theme.background,
        fg: this.config.theme.text,
      },
      tags: true,
      label: ' Status ',
    });

    // Main log area
    const logArea = blessed.log({
      top: 3,
      left: 0,
      width: '100%',
      height: '100%-6',
      border: {
        type: 'line',
      },
      style: {
        border: {
          fg: this.config.theme.border,
        },
        bg: this.config.theme.background,
        fg: this.config.theme.text,
      },
      tags: true,
      scrollable: true,
      alwaysScroll: true,
      mouse: true,
      keys: true,
      label: ' Output ',
    });

    // Input area at the bottom (optional)
    const inputArea = blessed.textbox({
      bottom: 0,
      left: 0,
      width: '100%',
      height: 3,
      border: {
        type: 'line',
      },
      style: {
        border: {
          fg: this.config.theme.border,
        },
        bg: this.config.theme.background,
        fg: this.config.theme.text,
      },
      inputOnFocus: true,
      mouse: true,
      keys: true,
      label: ' Input ',
    });

    this.mainContent.append(statusBar);
    this.mainContent.append(logArea);
    this.mainContent.append(inputArea);

    this.contentAreas = {
      log: logArea,
      input: inputArea,
      status: statusBar,
    };

    this.setupContentEvents();
  }

  private setupContentEvents(): void {
    if (!this.contentAreas) return;

    // Handle input submission
    this.contentAreas.input?.on('submit', (text: string) => {
      if (text.trim()) {
        this.handleCommand(text.trim());
        this.contentAreas!.input!.clearValue();
        this.render();
      }
    });

    // Handle log scrolling
    this.screen.key(['pageup'], () => {
      this.contentAreas!.log.scroll(-10);
      this.render();
    });

    this.screen.key(['pagedown'], () => {
      this.contentAreas!.log.scroll(10);
      this.render();
    });
  }

  private setupGlobalEvents(): void {
    // Handle screen resize
    this.screen.on('resize', () => {
      this.handleResize();
    });

    // Global key bindings
    this.screen.key(['C-c', 'q'], () => {
      this.destroy();
      process.exit(0);
    });

    this.screen.key(['C-l'], () => {
      this.clearLog();
    });

    this.screen.key(['tab'], () => {
      this.toggleSidebar();
    });

    this.screen.key(['F1'], () => {
      this.showHelp();
    });
  }

  enableSidebar(options?: {
    position?: 'left' | 'right';
    width?: number | string;
  }): void {
    if (options) {
      if (options.position) {
        this.config.sidebarPosition = options.position;
      }
      if (options.width) {
        this.config.sidebarWidth = options.width;
      }
    }

    this.config.sidebarEnabled = true;

    if (!this.sidebar) {
      this.sidebar = new TaskTrackingSidebar({
        position: this.config.sidebarPosition,
        width: this.config.sidebarWidth,
        height: '100%',
      });

      this.sidebar.initialize(this.screen);
    }

    if (this.isInitialized) {
      this.recreateLayout();
    }
  }

  disableSidebar(): void {
    this.config.sidebarEnabled = false;

    if (this.sidebar) {
      this.sidebar.destroy();
      this.sidebar = null;
    }

    if (this.isInitialized) {
      this.recreateLayout();
    }
  }

  toggleSidebar(): void {
    if (this.config.sidebarEnabled) {
      this.disableSidebar();
    } else {
      this.enableSidebar();
    }
  }

  updateTasks(tasks: TaskState[]): void {
    if (this.sidebar) {
      this.sidebar.updateTasks(tasks);
    }
  }

  log(message: string, level: 'info' | 'warn' | 'error' | 'success' = 'info'): void {
    if (!this.contentAreas?.log) return;

    const timestamp = new Date().toLocaleTimeString();
    const levelColor = this.getLevelColor(level);
    const levelIcon = this.getLevelIcon(level);

    const formattedMessage = `{gray-fg}${timestamp}{/} ${levelIcon} {${levelColor}-fg}${message}{/}`;

    (this.contentAreas.log as any).pushLine(formattedMessage);
    this.render();
  }

  updateStatus(status: string, type: 'default' | 'progress' | 'error' = 'default'): void {
    if (!this.contentAreas?.status) return;

    const typeColor = type === 'error' ? 'red' :
                     type === 'progress' ? 'yellow' :
                     this.config.theme.accent;

    this.contentAreas.status.setContent(`{center}{${typeColor}-fg}${status}{/}{/center}`);
    this.render();
  }

  showProgressBar(percentage: number, label?: string): void {
    if (!this.contentAreas?.status) return;

    const width = 20;
    const filled = Math.round((percentage / 100) * width);
    const empty = width - filled;

    const bar = '█'.repeat(filled) + '░'.repeat(empty);
    const content = label
      ? `{center}${label}: {cyan-fg}${bar}{/} ${percentage}%{/center}`
      : `{center}{cyan-fg}${bar}{/} ${percentage}%{/center}`;

    this.contentAreas.status.setContent(content);
    this.render();
  }

  clearLog(): void {
    if (this.contentAreas?.log) {
      this.contentAreas.log.setContent('');
      this.render();
    }
  }

  focusInput(): void {
    if (this.contentAreas?.input) {
      this.contentAreas.input.focus();
    }
  }

  focusSidebar(): void {
    if (this.sidebar) {
      this.sidebar.focus();
    }
  }

  showHelp(): void {
    const helpContent = `{bold}Specify CLI - Layout Help{/bold}

{bold}Global Keys:{/bold}
Tab      Toggle sidebar
F1       Show this help
Ctrl+C   Quit application
Ctrl+L   Clear log
PgUp/Dn  Scroll log

{bold}Sidebar Keys:{/bold}
↑/↓      Navigate tasks
Enter    View task details
r        Refresh tasks
h/?      Show sidebar help

{bold}Layout Features:{/bold}
• Real-time task tracking
• Command output logging
• Interactive task details
• Progress visualization

{gray-fg}Press ESC to close this help{/}`;

    this.showModal('Help', helpContent);
  }

  showModal(title: string, content: string): void {
    const modal = blessed.box({
      top: 'center',
      left: 'center',
      width: '70%',
      height: '70%',
      border: {
        type: 'line',
      },
      style: {
        border: {
          fg: this.config.theme.accent,
        },
        bg: this.config.theme.background,
        fg: this.config.theme.text,
      },
      tags: true,
      label: ` ${title} `,
      scrollable: true,
      alwaysScroll: true,
      mouse: true,
      keys: true,
    });

    modal.setContent(content);

    modal.key(['escape', 'q'], () => {
      this.screen.remove(modal);
      this.render();
    });

    this.screen.append(modal);
    modal.focus();
    this.render();
  }

  private handleCommand(command: string): void {
    // In a real implementation, this would handle CLI commands
    this.log(`Command executed: ${command}`, 'info');
  }

  private handleResize(): void {
    if (this.isInitialized) {
      this.render();
    }
  }

  private recreateLayout(): void {
    if (!this.isInitialized) return;

    // Clear existing layout
    this.screen.children.forEach(child => {
      this.screen.remove(child);
    });

    // Recreate layout
    this.createLayout();
  }

  private getLevelColor(level: string): string {
    switch (level) {
      case 'error': return 'red';
      case 'warn': return 'yellow';
      case 'success': return 'green';
      default: return 'white';
    }
  }

  private getLevelIcon(level: string): string {
    switch (level) {
      case 'error': return '❌';
      case 'warn': return '⚠️';
      case 'success': return '✅';
      default: return 'ℹ️';
    }
  }

  render(): void {
    this.screen.render();
  }

  getScreen(): blessed.Widgets.Screen {
    return this.screen;
  }

  getSidebar(): TaskTrackingSidebar | null {
    return this.sidebar;
  }

  isInitialized_(): boolean {
    return this.isInitialized;
  }

  getConfiguration(): LayoutConfiguration {
    return { ...this.config };
  }

  updateConfiguration(updates: Partial<LayoutConfiguration>): void {
    this.config = { ...this.config, ...updates };

    if (this.isInitialized) {
      this.recreateLayout();
    }
  }

  destroy(): void {
    if (this.sidebar) {
      this.sidebar.destroy();
    }

    if (this.screen) {
      this.screen.destroy();
    }
  }
}