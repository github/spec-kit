import * as SDK from "azure-devops-extension-sdk";
import { IProjectPageService, CommonServiceIds } from "azure-devops-extension-api";
import { SpecKitOrchestrator } from "../services/orchestrator";
import { RepositoryService } from "../services/repository";
import { TelemetryService } from "../services/telemetry";
import { LLMService } from "../services/llm";

interface WorkflowRun {
    id: string;
    timestamp: Date;
    workflow: 'specify' | 'plan' | 'tasks';
    workItemId: number;
    workItemTitle: string;
    status: 'running' | 'success' | 'failed';
    duration?: number;
    cost?: number;
    errorMessage?: string;
}

class SpecKitHub {
    private orchestrator: SpecKitOrchestrator;
    private repositoryService: RepositoryService;
    private telemetryService: TelemetryService;
    private llmService: LLMService;
    private currentProject: any;

    constructor() {
        this.orchestrator = new SpecKitOrchestrator();
        this.repositoryService = new RepositoryService();
        this.telemetryService = new TelemetryService();
        this.llmService = new LLMService();
    }

    public async initialize(): Promise<void> {
        await SDK.init();
        await SDK.ready();

        // Get current project context
        const projectService = await SDK.getService<IProjectPageService>(CommonServiceIds.ProjectPageService);
        this.currentProject = await projectService.getProject();

        this.setupEventHandlers();
        await this.loadProjectStatus();
        await this.loadRecentActivity();
    }

    private setupEventHandlers(): void {
        // Workflow buttons
        document.getElementById('run-specify')?.addEventListener('click', () => this.runWorkflow('specify'));
        document.getElementById('run-plan')?.addEventListener('click', () => this.runWorkflow('plan'));
        document.getElementById('run-tasks')?.addEventListener('click', () => this.runWorkflow('tasks'));

        // Repository actions
        document.getElementById('seed-repo')?.addEventListener('click', () => this.seedRepository());
        document.getElementById('configure-settings')?.addEventListener('click', () => this.openSettings());

        // Analytics
        document.getElementById('view-analytics')?.addEventListener('click', () => this.viewAnalytics());
        document.getElementById('export-data')?.addEventListener('click', () => this.exportData());

        // LLM management
        document.getElementById('manage-llm')?.addEventListener('click', () => this.manageLLM());
        document.getElementById('test-connection')?.addEventListener('click', () => this.testLLMConnection());
    }

    private async loadProjectStatus(): Promise<void> {
        const statusElement = document.getElementById('project-status');
        if (!statusElement) return;

        try {
            const status = await this.getProjectSpecKitStatus();
            statusElement.innerHTML = this.renderProjectStatus(status);
        } catch (error) {
            statusElement.innerHTML = `<div class="error">Failed to load project status: ${error}</div>`;
        }
    }

    private async getProjectSpecKitStatus(): Promise<any> {
        // Check if repository is seeded
        const isSeeded = await this.repositoryService.isRepositorySeeded(this.currentProject.id);
        
        // Get LLM connection status
        const llmConnections = await this.llmService.getProjectConnections(this.currentProject.id);
        
        // Get recent metrics
        const metrics = await this.telemetryService.getProjectMetrics(this.currentProject.id);

        return {
            isSeeded,
            llmConnections: llmConnections.length,
            defaultLLM: llmConnections.find(c => c.isDefault)?.name || 'None',
            totalRuns: metrics.totalRuns || 0,
            successRate: metrics.successRate || 0,
            avgCost: metrics.avgCost || 0
        };
    }

    private renderProjectStatus(status: any): string {
        return `
            <div class="status-grid">
                <div class="status-item">
                    <strong>Repository Status:</strong> 
                    <span class="${status.isSeeded ? 'status-success' : 'status-warning'}">
                        ${status.isSeeded ? '✅ Seeded' : '⚠️ Not Seeded'}
                    </span>
                </div>
                <div class="status-item">
                    <strong>LLM Connections:</strong> ${status.llmConnections}
                </div>
                <div class="status-item">
                    <strong>Default LLM:</strong> ${status.defaultLLM}
                </div>
                <div class="status-item">
                    <strong>Total Runs:</strong> ${status.totalRuns}
                </div>
                <div class="status-item">
                    <strong>Success Rate:</strong> ${(status.successRate * 100).toFixed(1)}%
                </div>
                <div class="status-item">
                    <strong>Avg Cost per Run:</strong> $${status.avgCost.toFixed(3)}
                </div>
            </div>
        `;
    }

    private async loadRecentActivity(): Promise<void> {
        const tbody = document.getElementById('history-tbody');
        if (!tbody) return;

        try {
            const runs = await this.telemetryService.getRecentRuns(this.currentProject.id, 10);
            tbody.innerHTML = runs.map(run => this.renderWorkflowRun(run)).join('');
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="7" class="error">Failed to load activity: ${error}</td></tr>`;
        }
    }

    private renderWorkflowRun(run: WorkflowRun): string {
        const statusClass = `status-${run.status}`;
        const duration = run.duration ? `${(run.duration / 1000).toFixed(1)}s` : '-';
        const cost = run.cost ? `$${run.cost.toFixed(3)}` : '-';

        return `
            <tr>
                <td>${run.timestamp.toLocaleString()}</td>
                <td><code>/${run.workflow}</code></td>
                <td><a href="#" onclick="openWorkItem(${run.workItemId})">#${run.workItemId}</a></td>
                <td><span class="status-badge ${statusClass}">${run.status}</span></td>
                <td>${duration}</td>
                <td class="cost-info">${cost}</td>
                <td>
                    <button onclick="viewRunDetails('${run.id}')" class="link-button">Details</button>
                    ${run.status === 'failed' ? `<button onclick="retryRun('${run.id}')" class="link-button">Retry</button>` : ''}
                </td>
            </tr>
        `;
    }

    private async runWorkflow(workflow: 'specify' | 'plan' | 'tasks'): Promise<void> {
        try {
            // Show work item picker dialog
            const workItemId = await this.showWorkItemPicker();
            if (!workItemId) return;

            // Start workflow
            const runId = await this.orchestrator.startWorkflow(workflow, workItemId, this.currentProject.id);
            
            // Show progress notification
            this.showNotification(`Starting /${workflow} workflow for work item #${workItemId}`, 'info');
            
            // Refresh activity list
            await this.loadRecentActivity();
            
        } catch (error) {
            this.showNotification(`Failed to start workflow: ${error}`, 'error');
        }
    }

    private async seedRepository(): Promise<void> {
        try {
            const confirmed = await this.showConfirmDialog(
                'Seed Repository',
                'This will create a new branch with Spec Kit configuration files. Continue?'
            );
            
            if (!confirmed) return;

            this.showNotification('Seeding repository...', 'info');
            
            const result = await this.repositoryService.seedRepository(this.currentProject.id);
            
            if (result.success) {
                this.showNotification(
                    `Repository seeded successfully. PR created: ${result.prUrl}`, 
                    'success'
                );
                await this.loadProjectStatus();
            } else {
                throw new Error(result.error);
            }
            
        } catch (error) {
            this.showNotification(`Failed to seed repository: ${error}`, 'error');
        }
    }

    private async manageLLM(): Promise<void> {
        // Open service connections page
        const url = `${this.currentProject.webUrl}/_settings/adminservices`;
        window.open(url, '_blank');
    }

    private async testLLMConnection(): Promise<void> {
        try {
            const connections = await this.llmService.getProjectConnections(this.currentProject.id);
            const defaultConnection = connections.find(c => c.isDefault);
            
            if (!defaultConnection) {
                this.showNotification('No default LLM connection configured', 'warning');
                return;
            }

            this.showNotification('Testing LLM connection...', 'info');
            
            const result = await this.llmService.testConnection(defaultConnection.id);
            
            if (result.success) {
                this.showNotification(`Connection test successful. Model: ${result.model}`, 'success');
            } else {
                throw new Error(result.error);
            }
            
        } catch (error) {
            this.showNotification(`Connection test failed: ${error}`, 'error');
        }
    }

    private async showWorkItemPicker(): Promise<number | null> {
        // This would typically open a work item picker dialog
        // For now, prompt for work item ID
        const input = prompt('Enter Work Item ID:');
        return input ? parseInt(input, 10) : null;
    }

    private async showConfirmDialog(title: string, message: string): Promise<boolean> {
        return confirm(`${title}\n\n${message}`);
    }

    private showNotification(message: string, type: 'info' | 'success' | 'warning' | 'error'): void {
        // This would typically use Azure DevOps notification service
        const color = {
            info: '#0078d4',
            success: '#107c10',
            warning: '#ff8c00',
            error: '#d13438'
        }[type];

        console.log(`%c${message}`, `color: ${color}; font-weight: bold;`);
        
        // Show browser notification as fallback
        if (Notification.permission === 'granted') {
            new Notification('Spec Kit', { body: message });
        }
    }

    private openSettings(): void {
        // This would open extension settings
        console.log('Opening settings...');
    }

    private viewAnalytics(): void {
        // This would open analytics dashboard
        console.log('Opening analytics...');
    }

    private exportData(): void {
        // This would export telemetry data
        console.log('Exporting data...');
    }
}

// Global functions for HTML event handlers
(window as any).openWorkItem = (id: number) => {
    const url = `${window.location.origin}/${encodeURIComponent(document.title)}/_workitems/edit/${id}`;
    window.open(url, '_blank');
};

(window as any).viewRunDetails = (runId: string) => {
    console.log('Viewing run details:', runId);
};

(window as any).retryRun = (runId: string) => {
    console.log('Retrying run:', runId);
};

// Initialize the hub
const hub = new SpecKitHub();
hub.initialize().catch(console.error);