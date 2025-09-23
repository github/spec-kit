"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TelemetryService = void 0;
class TelemetryService {
    constructor() {
        this.metricsCache = new Map();
        this.runsCache = new Map();
    }
    async recordWorkflowStart(projectId, workflowRun) {
        const runId = this.generateRunId();
        const run = {
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
    async recordWorkflowCompletion(runId, projectId, result) {
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
    async getProjectMetrics(projectId) {
        // Check cache first
        if (this.metricsCache.has(projectId)) {
            return this.metricsCache.get(projectId);
        }
        const runs = await this.getRecentRuns(projectId, 1000); // Get more runs for accurate metrics
        const metrics = this.calculateMetrics(runs);
        this.metricsCache.set(projectId, metrics);
        return metrics;
    }
    calculateMetrics(runs) {
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
    calculateMonthlyCosts(runs) {
        const monthlyData = {};
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
    async getRecentRuns(projectId, limit = 10) {
        const cached = this.runsCache.get(projectId);
        if (cached) {
            return cached.slice(0, limit);
        }
        // In a real implementation, this would fetch from Azure DevOps extension data storage
        // For now, return mock data
        const mockRuns = [
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
    async getRunDetails(runId) {
        // Search across all cached runs
        for (const runs of this.runsCache.values()) {
            const run = runs.find(r => r.id === runId);
            if (run)
                return run;
        }
        // In a real implementation, this would query the database
        return null;
    }
    async recordAuditEntry(entry) {
        const auditEntry = {
            ...entry,
            id: this.generateAuditId(),
            timestamp: new Date()
        };
        // In a real implementation, this would save to audit storage
        console.log('Audit entry:', auditEntry);
    }
    async getCurrentUserId() {
        // This would get the current Azure DevOps user ID
        return 'current-user-id';
    }
    generateRunId() {
        return `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    generateAuditId() {
        return `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    async exportMetrics(projectId, format) {
        const metrics = await this.getProjectMetrics(projectId);
        const runs = await this.getRecentRuns(projectId, 1000);
        if (format === 'json') {
            return JSON.stringify({ metrics, runs }, null, 2);
        }
        else {
            // CSV format
            let csv = 'Timestamp,Workflow,WorkItemId,Status,Duration,Cost,Tokens\n';
            runs.forEach(run => {
                csv += `${run.timestamp.toISOString()},${run.workflow},${run.workItemId},${run.status},${run.duration || ''},${run.cost || ''},${run.tokens ? `${run.tokens.input}/${run.tokens.output}` : ''}\n`;
            });
            return csv;
        }
    }
    clearCache() {
        this.metricsCache.clear();
        this.runsCache.clear();
    }
}
exports.TelemetryService = TelemetryService;
//# sourceMappingURL=telemetry.js.map