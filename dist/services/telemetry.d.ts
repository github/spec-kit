export interface ProjectMetrics {
    totalRuns: number;
    successRate: number;
    avgCost: number;
    avgDuration: number;
    workflowBreakdown: {
        specify: number;
        plan: number;
        tasks: number;
    };
    costBreakdown: {
        total: number;
        byWorkflow: {
            specify: number;
            plan: number;
            tasks: number;
        };
        byMonth: {
            month: string;
            cost: number;
        }[];
    };
    leadTimeMetrics: {
        avgSpecifyToMerge: number;
        avgPlanToImplementation: number;
        avgTasksToCompletion: number;
    };
}
export interface WorkflowRun {
    id: string;
    timestamp: Date;
    workflow: 'specify' | 'plan' | 'tasks';
    workItemId: number;
    workItemTitle: string;
    status: 'running' | 'success' | 'failed';
    duration?: number;
    cost?: number;
    tokens?: {
        input: number;
        output: number;
    };
    llmModel?: string;
    errorMessage?: string;
    artifacts?: string[];
}
export interface AuditEntry {
    id: string;
    timestamp: Date;
    runId: string;
    action: 'workflow_started' | 'workflow_completed' | 'artifact_saved' | 'error_occurred';
    details: any;
    userId: string;
    projectId: string;
}
export declare class TelemetryService {
    private metricsCache;
    private runsCache;
    recordWorkflowStart(projectId: string, workflowRun: Omit<WorkflowRun, 'id' | 'timestamp' | 'status'>): Promise<string>;
    recordWorkflowCompletion(runId: string, projectId: string, result: {
        status: 'success' | 'failed';
        duration: number;
        cost?: number;
        tokens?: {
            input: number;
            output: number;
        };
        errorMessage?: string;
        artifacts?: string[];
    }): Promise<void>;
    getProjectMetrics(projectId: string): Promise<ProjectMetrics>;
    private calculateMetrics;
    private calculateMonthlyCosts;
    getRecentRuns(projectId: string, limit?: number): Promise<WorkflowRun[]>;
    getRunDetails(runId: string): Promise<WorkflowRun | null>;
    private recordAuditEntry;
    private getCurrentUserId;
    private generateRunId;
    private generateAuditId;
    exportMetrics(projectId: string, format: 'json' | 'csv'): Promise<string>;
    clearCache(): void;
}
