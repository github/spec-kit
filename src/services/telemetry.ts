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
        byMonth: { month: string; cost: number }[];
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

export class TelemetryService {
    private metricsCache: Map<string, ProjectMetrics> = new Map();
    private runsCache: Map<string, WorkflowRun[]> = new Map();

    public async recordWorkflowStart(
        projectId: string,
        workflowRun: Omit<WorkflowRun, 'id' | 'timestamp' | 'status'>
    ): Promise<string> {
        const runId = this.generateRunId();
        const run: WorkflowRun = {
            ...workflowRun,
            id: runId,
            timestamp: new Date(),
            status: 'running'
        };

        // Add to cache
        const projectRuns = this.runsCache.get(projectId) || [];
        projectRuns.unshift(run);
        this.runsCache.set(projectId, projectRuns.slice(0, 100)); // Keep last 100 runs

        // Record audit entry
        await this.recordAuditEntry({
            runId,
            action: 'workflow_started',
            details: { workflow: workflowRun.workflow, workItemId: workflowRun.workItemId },
            userId: await this.getCurrentUserId(),
            projectId
        });

        // In a real implementation, this would save to Azure DevOps extension data storage
        console.log(`Recorded workflow start: ${runId}`);
        
        return runId;
    }

    public async recordWorkflowCompletion(
        runId: string,
        projectId: string,
        result: {
            status: 'success' | 'failed';
            duration: number;
            cost?: number;
            tokens?: { input: number; output: number };
            errorMessage?: string;
            artifacts?: string[];
        }
    ): Promise<void> {
        const projectRuns = this.runsCache.get(projectId) || [];
        const runIndex = projectRuns.findIndex(r => r.id === runId);
        
        if (runIndex >= 0) {
            projectRuns[runIndex] = {
                ...projectRuns[runIndex],
                status: result.status,
                duration: result.duration,
                cost: result.cost,
                tokens: result.tokens,
                errorMessage: result.errorMessage,
                artifacts: result.artifacts
            };
            
            this.runsCache.set(projectId, projectRuns);
        }

        // Record audit entry
        await this.recordAuditEntry({
            runId,
            action: 'workflow_completed',
            details: result,
            userId: await this.getCurrentUserId(),
            projectId
        });

        // Clear metrics cache to force recalculation
        this.metricsCache.delete(projectId);

        console.log(`Recorded workflow completion: ${runId}`);
    }

    public async getProjectMetrics(projectId: string): Promise<ProjectMetrics> {
        // Check cache first
        if (this.metricsCache.has(projectId)) {
            return this.metricsCache.get(projectId)!;
        }

        const runs = await this.getRecentRuns(projectId, 1000); // Get more runs for accurate metrics
        const metrics = this.calculateMetrics(runs);
        
        this.metricsCache.set(projectId, metrics);
        return metrics;
    }

    private calculateMetrics(runs: WorkflowRun[]): ProjectMetrics {
        const successfulRuns = runs.filter(r => r.status === 'success');
        const totalRuns = runs.length;
        const successRate = totalRuns > 0 ? successfulRuns.length / totalRuns : 0;

        // Calculate costs
        const totalCost = successfulRuns.reduce((sum, r) => sum + (r.cost || 0), 0);
        const avgCost = successfulRuns.length > 0 ? totalCost / successfulRuns.length : 0;

        // Calculate durations
        const avgDuration = successfulRuns.length > 0 
            ? successfulRuns.reduce((sum, r) => sum + (r.duration || 0), 0) / successfulRuns.length
            : 0;

        // Workflow breakdown
        const workflowBreakdown = {
            specify: runs.filter(r => r.workflow === 'specify').length,
            plan: runs.filter(r => r.workflow === 'plan').length,
            tasks: runs.filter(r => r.workflow === 'tasks').length
        };

        // Cost breakdown by workflow
        const costByWorkflow = {
            specify: successfulRuns.filter(r => r.workflow === 'specify').reduce((sum, r) => sum + (r.cost || 0), 0),
            plan: successfulRuns.filter(r => r.workflow === 'plan').reduce((sum, r) => sum + (r.cost || 0), 0),
            tasks: successfulRuns.filter(r => r.workflow === 'tasks').reduce((sum, r) => sum + (r.cost || 0), 0)
        };

        // Monthly cost breakdown
        const costByMonth = this.calculateMonthlyCosts(successfulRuns);

        // Lead time metrics (mock data for now)
        const leadTimeMetrics = {
            avgSpecifyToMerge: 48, // hours
            avgPlanToImplementation: 24, // hours
            avgTasksToCompletion: 72 // hours
        };

        return {
            totalRuns,
            successRate,
            avgCost,
            avgDuration,
            workflowBreakdown,
            costBreakdown: {
                total: totalCost,
                byWorkflow: costByWorkflow,
                byMonth: costByMonth
            },
            leadTimeMetrics
        };
    }

    private calculateMonthlyCosts(runs: WorkflowRun[]): { month: string; cost: number }[] {
        const monthlyData: Record<string, number> = {};
        
        runs.forEach(run => {
            if (run.cost) {
                const month = run.timestamp.toISOString().slice(0, 7); // YYYY-MM
                monthlyData[month] = (monthlyData[month] || 0) + run.cost;
            }
        });

        return Object.entries(monthlyData)
            .map(([month, cost]) => ({ month, cost }))
            .sort((a, b) => a.month.localeCompare(b.month));
    }

    public async getRecentRuns(projectId: string, limit: number = 10): Promise<WorkflowRun[]> {
        const cached = this.runsCache.get(projectId);
        if (cached) {
            return cached.slice(0, limit);
        }

        // In a real implementation, this would fetch from Azure DevOps extension data storage
        // For now, return mock data
        const mockRuns: WorkflowRun[] = [
            {
                id: 'run_1',
                timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
                workflow: 'specify',
                workItemId: 12345,
                workItemTitle: 'User authentication system',
                status: 'success',
                duration: 25000,
                cost: 0.05,
                tokens: { input: 1200, output: 800 },
                llmModel: 'gpt-4'
            },
            {
                id: 'run_2',
                timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
                workflow: 'plan',
                workItemId: 12346,
                workItemTitle: 'Payment processing module',
                status: 'success',
                duration: 18000,
                cost: 0.03,
                tokens: { input: 800, output: 600 },
                llmModel: 'gpt-4'
            },
            {
                id: 'run_3',
                timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4), // 4 hours ago
                workflow: 'tasks',
                workItemId: 12347,
                workItemTitle: 'Data validation framework',
                status: 'failed',
                duration: 5000,
                errorMessage: 'LLM connection timeout',
                llmModel: 'gpt-4'
            }
        ];

        this.runsCache.set(projectId, mockRuns);
        return mockRuns.slice(0, limit);
    }

    public async getRunDetails(runId: string): Promise<WorkflowRun | null> {
        // Search across all cached runs
        for (const runs of this.runsCache.values()) {
            const run = runs.find(r => r.id === runId);
            if (run) return run;
        }

        // In a real implementation, this would query the database
        return null;
    }

    private async recordAuditEntry(entry: Omit<AuditEntry, 'id' | 'timestamp'>): Promise<void> {
        const auditEntry: AuditEntry = {
            ...entry,
            id: this.generateAuditId(),
            timestamp: new Date()
        };

        // In a real implementation, this would save to audit storage
        console.log('Audit entry:', auditEntry);
    }

    private async getCurrentUserId(): Promise<string> {
        // This would get the current Azure DevOps user ID
        return 'current-user-id';
    }

    private generateRunId(): string {
        return `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    private generateAuditId(): string {
        return `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    public async exportMetrics(projectId: string, format: 'json' | 'csv'): Promise<string> {
        const metrics = await this.getProjectMetrics(projectId);
        const runs = await this.getRecentRuns(projectId, 1000);

        if (format === 'json') {
            return JSON.stringify({ metrics, runs }, null, 2);
        } else {
            // CSV format
            let csv = 'Timestamp,Workflow,WorkItemId,Status,Duration,Cost,Tokens\n';
            runs.forEach(run => {
                csv += `${run.timestamp.toISOString()},${run.workflow},${run.workItemId},${run.status},${run.duration || ''},${run.cost || ''},${run.tokens ? `${run.tokens.input}/${run.tokens.output}` : ''}\n`;
            });
            return csv;
        }
    }

    public clearCache(): void {
        this.metricsCache.clear();
        this.runsCache.clear();
    }
}