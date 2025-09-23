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

export class SpecKitOrchestrator {
    private activeRuns: Map<string, WorkflowExecutionContext> = new Map();

    public async startWorkflow(
        workflow: 'specify' | 'plan' | 'tasks',
        workItemId: number,
        projectId: string,
        options?: any
    ): Promise<string> {
        const runId = this.generateRunId();
        const context: WorkflowExecutionContext = {
            workItemId,
            projectId,
            workflow,
            options
        };

        this.activeRuns.set(runId, context);

        // Start the workflow execution asynchronously
        this.executeWorkflow(runId, context).catch(error => {
            console.error(`Workflow ${runId} failed:`, error);
        });

        return runId;
    }

    private async executeWorkflow(runId: string, context: WorkflowExecutionContext): Promise<WorkflowResult> {
        const startTime = Date.now();
        
        try {
            // Get work item context
            const workItemContext = await this.getWorkItemContext(context.workItemId, context.projectId);
            
            // Get constitution and policies
            const constitution = await this.buildConstitution(context.projectId, context.options?.includeWikiPages);
            
            // Execute the specific workflow
            let result: any;
            switch (context.workflow) {
                case 'specify':
                    result = await this.executeSpecifyWorkflow(workItemContext, constitution, context);
                    break;
                case 'plan':
                    result = await this.executePlanWorkflow(workItemContext, constitution, context);
                    break;
                case 'tasks':
                    result = await this.executeTasksWorkflow(workItemContext, constitution, context);
                    break;
                default:
                    throw new Error(`Unknown workflow: ${context.workflow}`);
            }

            const duration = Date.now() - startTime;
            
            // Save artifacts
            await this.saveArtifacts(result.artifacts, context);
            
            // Update work item if needed
            if (context.workflow === 'tasks' && result.tasks) {
                await this.createChildTasks(context.workItemId, result.tasks, context.projectId);
            }

            const workflowResult: WorkflowResult = {
                success: true,
                runId,
                artifacts: result.artifacts,
                cost: result.cost,
                duration
            };

            this.activeRuns.delete(runId);
            return workflowResult;

        } catch (error) {
            const duration = Date.now() - startTime;
            const workflowResult: WorkflowResult = {
                success: false,
                runId,
                duration,
                error: error instanceof Error ? error.message : String(error)
            };

            this.activeRuns.delete(runId);
            return workflowResult;
        }
    }

    private async getWorkItemContext(workItemId: number, projectId: string): Promise<any> {
        // This would integrate with Azure DevOps REST API to get work item details
        return {
            id: workItemId,
            title: `Work Item ${workItemId}`,
            description: 'Sample description',
            acceptanceCriteria: 'Sample acceptance criteria',
            type: 'User Story',
            state: 'New'
        };
    }

    private async buildConstitution(projectId: string, wikiPages?: string[]): Promise<string> {
        // This would aggregate constitution from multiple sources:
        // - Project wiki pages (policies, NFRs, style guides)
        // - Repository .specify/ configuration
        // - Team guidelines
        
        let constitution = "# Project Constitution\n\n";
        
        if (wikiPages && wikiPages.length > 0) {
            for (const page of wikiPages) {
                constitution += `## ${page}\n\n`;
                constitution += await this.getWikiPageContent(projectId, page);
                constitution += "\n\n";
            }
        } else {
            constitution += "## Default Guidelines\n\n";
            constitution += "- Follow team coding standards\n";
            constitution += "- Include comprehensive error handling\n";
            constitution += "- Write unit tests for all new functionality\n";
            constitution += "- Document public APIs\n";
        }

        return constitution;
    }

    private async getWikiPageContent(projectId: string, pagePath: string): Promise<string> {
        // This would fetch content from Azure DevOps Wiki API
        return `Content from wiki page: ${pagePath}`;
    }

    private async executeSpecifyWorkflow(workItemContext: any, constitution: string, context: WorkflowExecutionContext): Promise<any> {
        // This would implement the /specify workflow
        // For now, return mock data
        return {
            artifacts: {
                specifications: [
                    `# Specification for ${workItemContext.title}\n\n## Overview\n\nDetailed specification based on constitution and work item requirements.`
                ]
            },
            cost: 0.05,
            tokens: {
                input: 1200,
                output: 800
            }
        };
    }

    private async executePlanWorkflow(workItemContext: any, constitution: string, context: WorkflowExecutionContext): Promise<any> {
        // This would implement the /plan workflow
        return {
            artifacts: {
                plans: [
                    `# Implementation Plan for ${workItemContext.title}\n\n## Phases\n\n1. Analysis\n2. Design\n3. Implementation\n4. Testing`
                ]
            },
            cost: 0.03,
            tokens: {
                input: 800,
                output: 600
            }
        };
    }

    private async executeTasksWorkflow(workItemContext: any, constitution: string, context: WorkflowExecutionContext): Promise<any> {
        // This would implement the /tasks workflow
        return {
            artifacts: {
                tasks: [
                    {
                        title: "Implement core functionality",
                        description: "Core implementation based on specification",
                        effort: 8,
                        type: "Task"
                    },
                    {
                        title: "Add unit tests",
                        description: "Comprehensive test coverage",
                        effort: 4,
                        type: "Task"
                    },
                    {
                        title: "Update documentation",
                        description: "API documentation and user guides",
                        effort: 2,
                        type: "Task"
                    }
                ]
            },
            cost: 0.04,
            tokens: {
                input: 1000,
                output: 500
            }
        };
    }

    private async saveArtifacts(artifacts: any, context: WorkflowExecutionContext): Promise<void> {
        // This would save artifacts to the specified location (repo, wiki, or both)
        console.log('Saving artifacts:', artifacts);
    }

    private async createChildTasks(parentWorkItemId: number, tasks: any[], projectId: string): Promise<void> {
        // This would create child work items in Azure DevOps
        console.log(`Creating ${tasks.length} child tasks for work item ${parentWorkItemId}`);
    }

    private generateRunId(): string {
        return `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    public getActiveRuns(): string[] {
        return Array.from(this.activeRuns.keys());
    }

    public getRunStatus(runId: string): WorkflowExecutionContext | null {
        return this.activeRuns.get(runId) || null;
    }
}