export interface WorkflowExecutionContext {
    workItemId: number;
    projectId: string;
    workflow: 'specify' | 'plan' | 'tasks';
    llmConnectionId?: string;
    options?: {
        temperature?: number;
        includeWikiPages?: string[];
        outputFormat?: 'repo' | 'wiki' | 'both';
    };
}
export interface WorkflowResult {
    success: boolean;
    runId: string;
    artifacts?: {
        specifications?: string[];
        plans?: string[];
        tasks?: any[];
    };
    cost?: number;
    duration?: number;
    error?: string;
}
export declare class SpecKitOrchestrator {
    private activeRuns;
    startWorkflow(workflow: 'specify' | 'plan' | 'tasks', workItemId: number, projectId: string, options?: any): Promise<string>;
    private executeWorkflow;
    private getWorkItemContext;
    private buildConstitution;
    private getWikiPageContent;
    private executeSpecifyWorkflow;
    private executePlanWorkflow;
    private executeTasksWorkflow;
    private saveArtifacts;
    private createChildTasks;
    private generateRunId;
    getActiveRuns(): string[];
    getRunStatus(runId: string): WorkflowExecutionContext | null;
}
