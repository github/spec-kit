export interface SeedResult {
    success: boolean;
    prUrl?: string;
    branchName?: string;
    error?: string;
    filesAdded?: string[];
}

export interface RepositoryStatus {
    isSeeded: boolean;
    specKitVersion?: string;
    lastSeededDate?: Date;
    configFiles?: string[];
}

export class RepositoryService {
    private seedAssets = {
        prompts: [
            '.github/prompts/specify.md',
            '.github/prompts/plan.md', 
            '.github/prompts/tasks.md',
            '.github/prompts/constitution.md'
        ],
        config: [
            '.specify/config.yml',
            '.specify/templates/user-story.md',
            '.specify/templates/feature.md',
            '.specify/guardrails/security.yml',
            '.specify/guardrails/performance.yml'
        ]
    };

    public async isRepositorySeeded(projectId: string): Promise<boolean> {
        try {
            // This would check the repository for Spec Kit configuration files
            const status = await this.getRepositoryStatus(projectId);
            return status.isSeeded;
        } catch (error) {
            console.error('Error checking repository seed status:', error);
            return false;
        }
    }

    public async getRepositoryStatus(projectId: string): Promise<RepositoryStatus> {
        // This would integrate with Azure DevOps Git REST API
        // For now, return mock data
        return {
            isSeeded: false, // Change to true after first seed
            specKitVersion: undefined,
            lastSeededDate: undefined,
            configFiles: []
        };
    }

    public async seedRepository(projectId: string, targetRepo?: string): Promise<SeedResult> {
        try {
            // Get default repository if not specified
            const repoId = targetRepo || await this.getDefaultRepository(projectId);
            
            // Create seed branch
            const branchName = `spec-kit-seed-${Date.now()}`;
            await this.createBranch(repoId, branchName);

            // Add all seed files
            const filesAdded: string[] = [];
            
            // Add prompt templates
            for (const promptFile of this.seedAssets.prompts) {
                const content = await this.getPromptTemplate(promptFile);
                await this.addFile(repoId, branchName, promptFile, content);
                filesAdded.push(promptFile);
            }

            // Add configuration files
            for (const configFile of this.seedAssets.config) {
                const content = await this.getConfigTemplate(configFile);
                await this.addFile(repoId, branchName, configFile, content);
                filesAdded.push(configFile);
            }

            // Create pull request
            const prUrl = await this.createPullRequest(
                repoId,
                branchName,
                'main',
                'Add Spec Kit Configuration',
                'This PR adds Spec Kit configuration files and prompt templates to enable AI-powered specification workflows.'
            );

            return {
                success: true,
                prUrl,
                branchName,
                filesAdded
            };

        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    private async getDefaultRepository(projectId: string): Promise<string> {
        // This would get the default repository for the project
        return 'default-repo-id';
    }

    private async createBranch(repoId: string, branchName: string): Promise<void> {
        // This would create a new branch using Azure DevOps Git API
        console.log(`Creating branch ${branchName} in repository ${repoId}`);
    }

    private async addFile(repoId: string, branchName: string, filePath: string, content: string): Promise<void> {
        // This would add/update a file using Azure DevOps Git API
        console.log(`Adding file ${filePath} to branch ${branchName}`);
    }

    private async createPullRequest(
        repoId: string,
        sourceBranch: string,
        targetBranch: string,
        title: string,
        description: string
    ): Promise<string> {
        // This would create a pull request using Azure DevOps Git API
        const prId = Math.floor(Math.random() * 1000) + 1;
        return `https://dev.azure.com/organization/project/_git/repo/pullrequest/${prId}`;
    }

    private async getPromptTemplate(filePath: string): Promise<string> {
        const templates: Record<string, string> = {
            '.github/prompts/specify.md': `# Specification Prompt Template

## Context
You are helping to generate detailed specifications for software features.

## Instructions
1. Analyze the work item requirements
2. Consider the project constitution and guidelines
3. Generate comprehensive specifications including:
   - Functional requirements
   - Non-functional requirements
   - Acceptance criteria
   - Dependencies
   - Risk considerations

## Output Format
Generate specifications in markdown format with clear sections and detailed explanations.`,

            '.github/prompts/plan.md': `# Planning Prompt Template

## Context
You are creating implementation plans based on specifications.

## Instructions
1. Review the specification document
2. Break down into implementation phases
3. Identify dependencies and prerequisites
4. Estimate effort and timelines
5. Consider technical risks and mitigation strategies

## Output Format
Create a structured implementation plan with phases, tasks, and timelines.`,

            '.github/prompts/tasks.md': `# Task Generation Prompt Template

## Context
You are breaking down implementation plans into actionable tasks.

## Instructions
1. Analyze the implementation plan
2. Create specific, actionable tasks
3. Include effort estimates (in hours/story points)
4. Define clear acceptance criteria for each task
5. Identify task dependencies

## Output Format
Generate tasks in a structured format suitable for Azure DevOps work items.`,

            '.github/prompts/constitution.md': `# Project Constitution

## Coding Standards
- Follow team coding conventions
- Use consistent naming patterns
- Include comprehensive error handling
- Write meaningful comments and documentation

## Quality Guidelines
- All code must have unit tests
- Minimum 80% code coverage
- Peer review required for all changes
- Automated testing in CI/CD pipeline

## Architecture Principles
- Follow SOLID principles
- Use dependency injection
- Implement proper logging
- Consider security implications

## Non-Functional Requirements
- Performance: Page load times < 2 seconds
- Security: All inputs must be validated
- Accessibility: WCAG 2.1 compliance
- Scalability: Support 10,000 concurrent users`
        };

        return templates[filePath] || `# ${filePath}\n\nTemplate content for ${filePath}`;
    }

    private async getConfigTemplate(filePath: string): Promise<string> {
        const templates: Record<string, string> = {
            '.specify/config.yml': `# Spec Kit Configuration
version: "1.0"

# Default settings
defaults:
  temperature: 0.7
  max_tokens: 2000
  output_format: "markdown"

# Workflow settings
workflows:
  specify:
    enabled: true
    auto_save: true
    output_location: "specs/"
  
  plan:
    enabled: true
    auto_save: true
    output_location: "plans/"
  
  tasks:
    enabled: true
    auto_create_work_items: true
    task_prefix: "TASK"

# Integration settings
integrations:
  azure_devops:
    auto_link_work_items: true
    sync_state_changes: true
  
  wiki:
    auto_publish: false
    wiki_path: "Specifications/"`,

            '.specify/templates/user-story.md': `# User Story Template

## Title
{{title}}

## Description
{{description}}

## Acceptance Criteria
{{acceptanceCriteria}}

## Specification

### Functional Requirements
[Generated specifications will appear here]

### Non-Functional Requirements
[Performance, security, and other non-functional requirements]

### Dependencies
[External dependencies and prerequisites]

### Risk Assessment
[Potential risks and mitigation strategies]`,

            '.specify/templates/feature.md': `# Feature Template

## Feature: {{title}}

### Overview
{{description}}

### User Stories
{{acceptanceCriteria}}

### Technical Specification

#### Architecture
[High-level architecture description]

#### Components
[Detailed component breakdown]

#### Data Model
[Data structures and relationships]

#### API Specification
[API endpoints and contracts]

#### Security Considerations
[Security requirements and implementation]`,

            '.specify/guardrails/security.yml': `# Security Guardrails

rules:
  - name: "Input Validation"
    description: "All user inputs must be validated"
    severity: "high"
    pattern: "validate.*input|sanitize.*data"
    
  - name: "Authentication Required"
    description: "Protected endpoints must require authentication"
    severity: "high"
    pattern: "authenticate|authorize"
    
  - name: "SQL Injection Prevention"
    description: "Use parameterized queries"
    severity: "critical"
    pattern: "parameterized|prepared.*statement"
    
  - name: "XSS Prevention"
    description: "Escape output data"
    severity: "high"
    pattern: "escape.*output|sanitize.*html"`,

            '.specify/guardrails/performance.yml': `# Performance Guardrails

rules:
  - name: "Database Query Optimization"
    description: "Optimize database queries for performance"
    severity: "medium"
    pattern: "index|optimize.*query"
    
  - name: "Caching Strategy"
    description: "Implement appropriate caching"
    severity: "medium"
    pattern: "cache|memoize"
    
  - name: "Async Operations"
    description: "Use async/await for I/O operations"
    severity: "low"
    pattern: "async|await"
    
  - name: "Resource Management"
    description: "Proper resource cleanup"
    severity: "medium"
    pattern: "dispose|close|cleanup"`
        };

        return templates[filePath] || `# ${filePath}\n\nConfiguration template for ${filePath}`;
    }

    public async saveArtifact(
        projectId: string,
        filePath: string,
        content: string,
        commitMessage: string
    ): Promise<void> {
        // This would save an artifact to the repository
        console.log(`Saving artifact ${filePath} with message: ${commitMessage}`);
    }

    public async getArtifacts(projectId: string, artifactType: 'specs' | 'plans' | 'tasks'): Promise<string[]> {
        // This would retrieve existing artifacts from the repository
        return [`${artifactType}/example.md`];
    }
}