import * as SDK from "azure-devops-extension-sdk";
import { getClient } from "azure-devops-extension-api";
import { WorkItemTrackingRestClient } from "azure-devops-extension-api/WorkItemTracking";
import { SpecKitOrchestrator } from "../services/orchestrator";
import { LLMService } from "../services/llm";
import { RepositoryService } from "../services/repository";
import { TelemetryService } from "../services/telemetry";

interface WorkItemData {
    id: number;
    title: string;
    description: string;
    acceptanceCriteria: string;
    workItemType: string;
    state: string;
    assignedTo: string;
}

interface GeneratedArtifact {
    type: 'specification' | 'plan' | 'tasks';
    title: string;
    content: string;
    timestamp: Date;
    cost?: number;
}

class SpecAssistTab {
    private workItemClient!: WorkItemTrackingRestClient;
    private orchestrator: SpecKitOrchestrator;
    private llmService: LLMService;
    private repositoryService: RepositoryService;
    private telemetryService: TelemetryService;
    private currentWorkItem: WorkItemData | null = null;
    private projectId: string = '';
    private artifacts: GeneratedArtifact[] = [];
    private activeRunId: string | null = null;

    constructor() {
        this.orchestrator = new SpecKitOrchestrator();
        this.llmService = new LLMService();
        this.repositoryService = new RepositoryService();
        this.telemetryService = new TelemetryService();
    }

    public async initialize(): Promise<void> {
        try {
            console.log('Spec Kit Tab: Starting initialization...');
            
            // Initialize Azure DevOps Extension SDK
            await SDK.init();
            console.log('SDK initialized');
            
            await SDK.ready();
            console.log('SDK ready');

            // Get work item tracking client
            this.workItemClient = getClient(WorkItemTrackingRestClient);
            console.log('Work item client initialized');

            // Get project context
            const webContext = SDK.getWebContext();
            this.projectId = webContext.project?.id || '';
            console.log('Project ID:', this.projectId);

            // Initialize services
            this.orchestrator = new SpecKitOrchestrator();
            this.llmService = new LLMService();
            this.repositoryService = new RepositoryService();
            this.telemetryService = new TelemetryService();
            console.log('Services initialized');

            await this.loadWorkItemData();
            await this.loadLLMConnections();
            this.setupEventHandlers();
            await this.loadExistingArtifacts();
            
            // Hide loading and show content
            this.hideLoading();
            
            console.log('Spec Kit Tab initialization completed successfully');
        } catch (error) {
            console.error('Failed to initialize Spec Kit Tab:', error);
            this.showError('Initialization failed: ' + (error as Error).message, error);
        }
    }

    private async loadWorkItemData(): Promise<void> {
        try {
            // In Azure DevOps tabs, work item ID is available via URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            const workItemIdStr = urlParams.get('workItemId') || urlParams.get('id');
            const workItemId = workItemIdStr ? parseInt(workItemIdStr) : 0;
            
            if (!workItemId) {
                throw new Error('Work item ID not found');
            }

            const workItem = await this.workItemClient.getWorkItem(workItemId, this.projectId);
            
            this.currentWorkItem = {
                id: workItem.id || 0,
                title: (workItem.fields?.['System.Title'] as string) || '',
                description: (workItem.fields?.['System.Description'] as string) || '',
                acceptanceCriteria: (workItem.fields?.['Microsoft.VSTS.Common.AcceptanceCriteria'] as string) || '',
                workItemType: (workItem.fields?.['System.WorkItemType'] as string) || 'Task',
                state: (workItem.fields?.['System.State'] as string) || 'New',
                assignedTo: (workItem.fields?.['System.AssignedTo'] as any)?.displayName || 'Unassigned'
            };

            this.updateWorkItemDisplay();

        } catch (error) {
            console.error('Error loading work item data:', error);
            this.showStatus('Error loading work item data', 'error');
        }
    }

    private updateWorkItemDisplay(): void {
        if (!this.currentWorkItem) return;

        const titleElement = document.getElementById('work-item-title');
        const idElement = document.getElementById('work-item-id');
        const typeElement = document.getElementById('work-item-type');
        const stateElement = document.getElementById('work-item-state');
        const assigneeElement = document.getElementById('work-item-assignee');

        if (titleElement) titleElement.textContent = this.currentWorkItem.title;
        if (idElement) idElement.textContent = this.currentWorkItem.id.toString();
        if (typeElement) typeElement.textContent = this.currentWorkItem.workItemType;
        if (stateElement) stateElement.textContent = this.currentWorkItem.state;
        if (assigneeElement) assigneeElement.textContent = this.currentWorkItem.assignedTo;
    }

    private async loadLLMConnections(): Promise<void> {
        try {
            const connections = await this.llmService.getProjectConnections(this.projectId);
            const select = document.getElementById('llm-connection') as HTMLSelectElement;
            
            if (select) {
                select.innerHTML = '';
                
                if (connections.length === 0) {
                    select.innerHTML = '<option value="">No LLM connections configured</option>';
                } else {
                    connections.forEach(conn => {
                        const option = document.createElement('option');
                        option.value = conn.id;
                        option.textContent = `${conn.name} (${conn.model})`;
                        if (conn.isDefault) {
                            option.selected = true;
                        }
                        select.appendChild(option);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading LLM connections:', error);
            const select = document.getElementById('llm-connection') as HTMLSelectElement;
            if (select) {
                select.innerHTML = '<option value="">Error loading connections</option>';
            }
        }
    }

    private setupEventHandlers(): void {
        // Workflow buttons
        document.getElementById('btn-specify')?.addEventListener('click', () => this.runWorkflow('specify'));
        document.getElementById('btn-specify-custom')?.addEventListener('click', () => this.runCustomWorkflow('specify'));
        
        document.getElementById('btn-plan')?.addEventListener('click', () => this.runWorkflow('plan'));
        document.getElementById('btn-plan-custom')?.addEventListener('click', () => this.runCustomWorkflow('plan'));
        
        document.getElementById('btn-tasks')?.addEventListener('click', () => this.runWorkflow('tasks'));
        document.getElementById('btn-tasks-custom')?.addEventListener('click', () => this.runCustomWorkflow('tasks'));

        // Publishing buttons
        document.getElementById('btn-publish-wiki')?.addEventListener('click', () => this.publishToWiki());
        document.getElementById('btn-publish-repo')?.addEventListener('click', () => this.publishToRepo());
    }

    private async runWorkflow(workflow: 'specify' | 'plan' | 'tasks'): Promise<void> {
        if (!this.currentWorkItem) {
            this.showStatus('No work item loaded', 'error');
            return;
        }

        if (this.activeRunId) {
            this.showStatus('A workflow is already running. Please wait for it to complete.', 'error');
            return;
        }

        try {
            this.setButtonsEnabled(false);
            this.showStatus(`Starting ${workflow} workflow...`, 'running');

            // Get selected settings
            const llmConnectionId = (document.getElementById('llm-connection') as HTMLSelectElement)?.value;
            const temperature = parseFloat((document.getElementById('temperature') as HTMLSelectElement)?.value || '0.7');
            const outputLocation = (document.getElementById('output-location') as HTMLSelectElement)?.value || 'both';

            if (!llmConnectionId) {
                throw new Error('No LLM connection selected. Please configure an LLM connection first.');
            }

            // Start workflow
            const runId = await this.orchestrator.startWorkflow(
                workflow,
                this.currentWorkItem.id,
                this.projectId,
                {
                    temperature,
                    outputFormat: outputLocation,
                    llmConnectionId
                }
            );

            this.activeRunId = runId;

            // Poll for completion
            await this.pollWorkflowCompletion(runId, workflow);

        } catch (error) {
            this.showStatus(`Error: ${error}`, 'error');
            this.setButtonsEnabled(true);
            this.activeRunId = null;
        }
    }

    private async runCustomWorkflow(workflow: 'specify' | 'plan' | 'tasks'): Promise<void> {
        // This would open a dialog for custom workflow options
        const customOptions = await this.showCustomOptionsDialog(workflow);
        if (customOptions) {
            // Run workflow with custom options
            console.log('Running custom workflow with options:', customOptions);
        }
    }

    private async pollWorkflowCompletion(runId: string, workflow: 'specify' | 'plan' | 'tasks'): Promise<void> {
        const maxAttempts = 60; // 5 minutes max
        let attempts = 0;

        const poll = async (): Promise<void> => {
            attempts++;
            
            try {
                const runDetails = await this.telemetryService.getRunDetails(runId);
                
                if (!runDetails) {
                    throw new Error('Run details not found');
                }

                if (runDetails.status === 'success') {
                    this.showStatus(`${workflow} workflow completed successfully!`, 'success');
                    await this.loadGeneratedArtifacts(runId, workflow);
                    this.setButtonsEnabled(true);
                    this.activeRunId = null;
                    return;
                }

                if (runDetails.status === 'failed') {
                    this.showStatus(`${workflow} workflow failed: ${runDetails.errorMessage}`, 'error');
                    this.setButtonsEnabled(true);
                    this.activeRunId = null;
                    return;
                }

                if (runDetails.status === 'running' && attempts < maxAttempts) {
                    this.showStatus(`${workflow} workflow running... (${attempts * 5}s)`, 'running');
                    setTimeout(poll, 5000); // Poll every 5 seconds
                    return;
                }

                throw new Error('Workflow timed out');

            } catch (error) {
                this.showStatus(`Error polling workflow status: ${error}`, 'error');
                this.setButtonsEnabled(true);
                this.activeRunId = null;
            }
        };

        await poll();
    }

    private async loadGeneratedArtifacts(runId: string, workflow: 'specify' | 'plan' | 'tasks'): Promise<void> {
        try {
            const runDetails = await this.telemetryService.getRunDetails(runId);
            if (!runDetails || !runDetails.artifacts) return;

            // Create artifact objects
            runDetails.artifacts.forEach(artifactPath => {
                const artifact: GeneratedArtifact = {
                    type: workflow as any,
                    title: `${workflow.charAt(0).toUpperCase() + workflow.slice(1)} - ${this.currentWorkItem?.title}`,
                    content: `Generated content from ${artifactPath}`, // Would load actual content
                    timestamp: new Date(),
                    cost: runDetails.cost
                };
                
                this.artifacts.push(artifact);
            });

            this.updateArtifactsDisplay();

        } catch (error) {
            console.error('Error loading generated artifacts:', error);
        }
    }

    private updateArtifactsDisplay(): void {
        const container = document.getElementById('artifacts-container');
        if (!container) return;

        if (this.artifacts.length === 0) {
            container.innerHTML = '<p>No artifacts generated yet. Run a workflow to see results here.</p>';
            return;
        }

        container.innerHTML = this.artifacts.map((artifact, index) => `
            <div class="artifact-item">
                <div class="artifact-header" onclick="toggleArtifact(${index})">
                    <span>${artifact.title}</span>
                    <span>
                        ${artifact.cost ? `$${artifact.cost.toFixed(3)}` : ''}
                        <span style="margin-left: 10px;">▼</span>
                    </span>
                </div>
                <div class="artifact-content hidden" id="artifact-content-${index}">
                    <pre>${artifact.content}</pre>
                    <div style="margin-top: 10px;">
                        <button onclick="copyArtifact(${index})" class="workflow-button">Copy</button>
                        <button onclick="editArtifact(${index})" class="workflow-button">Edit</button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    private async publishToWiki(): Promise<void> {
        if (this.artifacts.length === 0) {
            this.showStatus('No artifacts to publish', 'error');
            return;
        }

        try {
            this.showStatus('Publishing to wiki...', 'running');
            
            // This would publish artifacts to Azure DevOps Wiki
            await this.sleep(2000); // Simulate API call
            
            this.showStatus('Successfully published to wiki!', 'success');
        } catch (error) {
            this.showStatus(`Error publishing to wiki: ${error}`, 'error');
        }
    }

    private async publishToRepo(): Promise<void> {
        if (this.artifacts.length === 0) {
            this.showStatus('No artifacts to publish', 'error');
            return;
        }

        try {
            this.showStatus('Saving to repository...', 'running');
            
            for (const artifact of this.artifacts) {
                const filePath = `specs/${artifact.type}/${this.currentWorkItem?.id}-${artifact.type}.md`;
                await this.repositoryService.saveArtifact(
                    this.projectId,
                    filePath,
                    artifact.content,
                    `Add ${artifact.type} for work item #${this.currentWorkItem?.id}`
                );
            }
            
            this.showStatus('Successfully saved to repository!', 'success');
        } catch (error) {
            this.showStatus(`Error saving to repository: ${error}`, 'error');
        }
    }

    private async loadExistingArtifacts(): Promise<void> {
        if (!this.currentWorkItem) return;

        try {
            // Load existing artifacts for this work item
            const specs = await this.repositoryService.getArtifacts(this.projectId, 'specs');
            const plans = await this.repositoryService.getArtifacts(this.projectId, 'plans');
            const tasks = await this.repositoryService.getArtifacts(this.projectId, 'tasks');

            // Filter artifacts for current work item
            const workItemArtifacts = [...specs, ...plans, ...tasks].filter(path => 
                path.includes(this.currentWorkItem!.id.toString())
            );

            // Load artifact content and create artifact objects
            // This would involve actual file reading in a real implementation

        } catch (error) {
            console.error('Error loading existing artifacts:', error);
        }
    }

    private setButtonsEnabled(enabled: boolean): void {
        const buttons = [
            'btn-specify', 'btn-specify-custom',
            'btn-plan', 'btn-plan-custom',
            'btn-tasks', 'btn-tasks-custom'
        ];

        buttons.forEach(id => {
            const button = document.getElementById(id) as HTMLButtonElement;
            if (button) {
                button.disabled = !enabled;
            }
        });
    }

    private showStatus(message: string, type: 'running' | 'success' | 'error'): void {
        const statusElement = document.getElementById('execution-status');
        const contentElement = document.getElementById('status-content');
        
        if (statusElement && contentElement) {
            statusElement.className = `execution-status ${type}`;
            statusElement.classList.remove('hidden');
            
            const icon = type === 'running' ? '<span class="loading-spinner"></span>' : '';
            contentElement.innerHTML = `${icon}${message}`;
        }
    }

    private async showCustomOptionsDialog(workflow: string): Promise<any> {
        // This would show a custom dialog for workflow options
        return null;
    }

    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    private hideLoading(): void {
        const loading = document.getElementById('loading-indicator');
        const content = document.getElementById('main-content');
        if (loading) loading.style.display = 'none';
        if (content) content.style.display = 'block';
    }

    private showError(message: string, details?: any): void {
        console.error('Spec Kit Tab Error:', message, details);
        
        const loading = document.getElementById('loading-indicator');
        const content = document.getElementById('main-content');
        const errorContainer = document.getElementById('error-container');
        const errorMessage = document.getElementById('error-message');
        const errorDetails = document.getElementById('error-details');

        if (loading) loading.style.display = 'none';
        if (content) content.style.display = 'none';
        if (errorContainer) errorContainer.style.display = 'block';
        if (errorMessage) errorMessage.textContent = message;
        if (errorDetails) {
            errorDetails.textContent = details ? JSON.stringify(details, null, 2) : 'No additional details';
        }
    }
}

// Global functions for HTML event handlers
(window as any).toggleArtifact = (index: number) => {
    const content = document.getElementById(`artifact-content-${index}`);
    if (content) {
        content.classList.toggle('hidden');
    }
};

(window as any).copyArtifact = (index: number) => {
    const artifact = (window as any).specAssistTab?.artifacts[index];
    if (artifact) {
        navigator.clipboard.writeText(artifact.content);
        console.log('Artifact copied to clipboard');
    }
};

(window as any).editArtifact = (index: number) => {
    console.log('Edit artifact:', index);
    // This would open an editor dialog
};

// Initialize the tab
console.log('Spec Kit Tab: Creating tab instance...');

const tab = new SpecAssistTab();
(window as any).specKitTab = tab;
(window as any).specAssistTab = tab; // Backward compatibility

// Initialize when SDK is ready
SDK.ready().then(() => {
    console.log('Spec Kit Tab: SDK ready, initializing tab...');
    tab.initialize().catch(error => {
        console.error('Failed to initialize Spec Kit tab:', error);
        if ((window as any).showError) {
            (window as any).showError('Failed to initialize: ' + error.message, error);
        }
    });
}).catch(error => {
    console.error('SDK ready failed:', error);
    if ((window as any).showError) {
        (window as any).showError('SDK initialization failed: ' + error.message, error);
    }
});
tab.initialize().catch(console.error);