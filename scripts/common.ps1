# Common PowerShell functions for Spec Kit Azure DevOps tasks

function Get-SpecifyTemplate {
    return @"
# Specification Generation Prompt

## Context
You are an expert software analyst helping to create detailed specifications for software features and requirements.

## Instructions
1. Analyze the work item requirements thoroughly
2. Consider the project constitution and guidelines provided
3. Generate comprehensive specifications that include:
   - **Functional Requirements**: What the system should do
   - **Non-Functional Requirements**: Performance, security, usability constraints
   - **Acceptance Criteria**: Clear, testable conditions for completion
   - **Dependencies**: External systems, services, or components required
   - **Risk Assessment**: Potential issues and mitigation strategies
   - **Implementation Notes**: Technical considerations and recommendations

## Output Format
Structure your response as a well-organized markdown document with clear sections and detailed explanations.

## Quality Guidelines
- Be specific and actionable
- Include measurable criteria where possible
- Consider edge cases and error scenarios
- Align with project standards and best practices
"@
}

function Get-PlanTemplate {
    return @"
# Implementation Planning Prompt

## Context
You are an experienced software architect creating detailed implementation plans based on specifications.

## Instructions
1. Review the specification document thoroughly
2. Break down the implementation into logical phases
3. Create a structured plan that includes:
   - **Phase Breakdown**: Logical implementation phases with clear objectives
   - **Task Dependencies**: Prerequisites and blocking relationships
   - **Effort Estimates**: Time estimates for each phase/task
   - **Technical Approach**: High-level implementation strategy
   - **Risk Mitigation**: Technical risks and mitigation plans
   - **Milestone Definitions**: Key deliverables and checkpoints

## Output Format
Create a structured implementation plan with clear phases, dependencies, and timelines.

## Planning Principles
- Prioritize high-risk or foundational components first
- Consider parallel development opportunities
- Include testing and validation in each phase
- Plan for iterative delivery and feedback cycles
"@
}

function Get-TasksTemplate {
    return @"
# Task Breakdown Prompt

## Context
You are a senior developer breaking down implementation plans into specific, actionable development tasks.

## Instructions
1. Analyze the implementation plan carefully
2. Create specific, actionable tasks that include:
   - **Task Title**: Clear, descriptive name
   - **Description**: Detailed explanation of what needs to be done
   - **Acceptance Criteria**: Specific conditions for task completion
   - **Effort Estimate**: Hours or story points
   - **Dependencies**: Other tasks that must be completed first
   - **Technical Notes**: Implementation hints or considerations

## Output Format
Generate tasks in a structured format suitable for work item creation:

```
### Task: [Title]
**Description:** [Detailed description]
**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
**Effort:** [X hours/points]
**Dependencies:** [List of dependent tasks]
**Notes:** [Technical considerations]
```

## Task Guidelines
- Each task should be completable in 1-3 days
- Include both development and testing activities
- Consider code review and documentation tasks
- Ensure tasks are independent where possible
"@
}

function Get-ConstitutionTemplate {
    return @"
# Project Constitution and Guidelines

## Coding Standards
- Follow established team coding conventions
- Use consistent naming patterns across the codebase
- Include comprehensive error handling for all edge cases
- Write meaningful comments and maintain up-to-date documentation

## Quality Assurance
- All code must have corresponding unit tests
- Maintain minimum 80% code coverage
- Peer review is required for all code changes
- Automated testing must pass in CI/CD pipeline

## Architecture Principles
- Follow SOLID principles in object-oriented design
- Use dependency injection for loose coupling
- Implement proper logging and monitoring
- Always consider security implications in design decisions

## Non-Functional Requirements
- **Performance**: Page load times must be under 2 seconds
- **Security**: All user inputs must be validated and sanitized
- **Accessibility**: Maintain WCAG 2.1 AA compliance
- **Scalability**: Design to support 10,000+ concurrent users

## Documentation Standards
- Maintain comprehensive API documentation
- Update README files with setup and usage instructions
- Document architectural decisions and rationale
- Keep deployment and operational guides current
"@
}

function Get-ConfigTemplate {
    return @"
# Spec Kit Configuration
version: "1.0"

# Default LLM settings
defaults:
  temperature: 0.7
  max_tokens: 2000
  output_format: "markdown"

# Workflow configuration
workflows:
  specify:
    enabled: true
    auto_save: true
    output_location: "specs/"
    template: ".github/prompts/specify.md"
  
  plan:
    enabled: true
    auto_save: true
    output_location: "plans/"
    template: ".github/prompts/plan.md"
  
  tasks:
    enabled: true
    auto_create_work_items: true
    task_prefix: "TASK"
    template: ".github/prompts/tasks.md"

# Integration settings
integrations:
  azure_devops:
    auto_link_work_items: true
    sync_state_changes: true
    add_comments: true
  
  wiki:
    auto_publish: false
    wiki_path: "Specifications/"
    
# Guardrails
guardrails:
  security:
    enabled: true
    config_file: ".specify/guardrails/security.yml"
  
  performance:
    enabled: true
    config_file: ".specify/guardrails/performance.yml"

# Cost controls
cost_controls:
  daily_limit: 10.00
  monthly_limit: 300.00
  alert_threshold: 0.80
"@
}

function Get-UserStoryTemplate {
    return @"
# User Story Specification Template

## Story: {{title}}

### Overview
{{description}}

### User Personas
[Define the target users for this story]

### Acceptance Criteria
{{acceptanceCriteria}}

### Detailed Specification

#### Functional Requirements
[Generated functional requirements will appear here]

#### User Interface Requirements
[UI/UX requirements and wireframe descriptions]

#### Business Rules
[Business logic and validation rules]

#### Integration Requirements
[External system integrations needed]

#### Performance Requirements
[Performance criteria specific to this story]

#### Security Considerations
[Security requirements and data protection needs]

#### Testing Strategy
[Approach for testing this user story]

### Dependencies
[Prerequisites and blocking dependencies]

### Assumptions
[Key assumptions made during specification]

### Out of Scope
[What is explicitly not included in this story]
"@
}

function Get-FeatureTemplate {
    return @"
# Feature Specification Template

## Feature: {{title}}

### Executive Summary
{{description}}

### Business Objectives
[High-level business goals this feature addresses]

### User Stories
{{acceptanceCriteria}}

### Technical Specification

#### System Architecture
[High-level architecture and component design]

#### Data Model
[Database schema and data structures]

#### API Specification
[REST endpoints, GraphQL schemas, or other API contracts]

#### User Interface Design
[UI components, layouts, and user workflows]

#### Integration Points
[External systems, services, and third-party integrations]

#### Security Architecture
[Authentication, authorization, and data protection]

#### Performance Requirements
[Load, response time, and scalability requirements]

#### Monitoring and Observability
[Logging, metrics, and alerting strategy]

### Implementation Phases
[Breakdown of feature delivery phases]

### Testing Strategy
[Comprehensive testing approach including unit, integration, and E2E tests]

### Deployment Strategy
[Rollout plan and deployment considerations]

### Success Metrics
[KPIs and metrics to measure feature success]

### Risk Assessment
[Technical and business risks with mitigation strategies]
"@
}

function Get-SecurityGuardrailsTemplate {
    return @"
# Security Guardrails Configuration

rules:
  - name: "Input Validation Required"
    description: "All user inputs must be validated and sanitized"
    severity: "high"
    pattern: "validate.*input|sanitize.*data|input.*validation"
    
  - name: "Authentication Required"
    description: "Protected endpoints must require authentication"
    severity: "high"
    pattern: "authenticate|authorize|auth.*required"
    
  - name: "SQL Injection Prevention"
    description: "Use parameterized queries to prevent SQL injection"
    severity: "critical"
    pattern: "parameterized.*query|prepared.*statement|query.*parameters"
    
  - name: "XSS Prevention"
    description: "Escape or sanitize output to prevent XSS attacks"
    severity: "high"
    pattern: "escape.*output|sanitize.*html|xss.*prevention"
    
  - name: "HTTPS Required"
    description: "All communications must use HTTPS"
    severity: "high"
    pattern: "https|ssl|tls"
    
  - name: "Secret Management"
    description: "Secrets must be stored securely, not in code"
    severity: "critical"
    pattern: "secret.*management|key.*vault|environment.*variable"
    
  - name: "Error Handling"
    description: "Implement proper error handling without exposing sensitive information"
    severity: "medium"
    pattern: "error.*handling|exception.*handling|try.*catch"

# Compliance checks
compliance:
  - name: "GDPR"
    description: "General Data Protection Regulation compliance"
    checks:
      - "data_retention_policy"
      - "user_consent"
      - "data_portability"
      - "right_to_deletion"
      
  - name: "SOC2"
    description: "SOC 2 Type II compliance"
    checks:
      - "access_controls"
      - "data_encryption"
      - "audit_logging"
      - "incident_response"
"@
}

function Get-PerformanceGuardrailsTemplate {
    return @"
# Performance Guardrails Configuration

rules:
  - name: "Database Query Optimization"
    description: "Optimize database queries for performance"
    severity: "medium"
    pattern: "index|optimize.*query|query.*performance"
    
  - name: "Caching Strategy"
    description: "Implement appropriate caching mechanisms"
    severity: "medium"
    pattern: "cache|memoize|redis|memcached"
    
  - name: "Asynchronous Operations"
    description: "Use async/await for I/O operations"
    severity: "low"
    pattern: "async|await|asynchronous"
    
  - name: "Resource Management"
    description: "Proper cleanup of resources and connections"
    severity: "medium"
    pattern: "dispose|close|cleanup|using.*statement"
    
  - name: "Pagination"
    description: "Implement pagination for large data sets"
    severity: "medium"
    pattern: "pagination|page.*size|limit.*offset"
    
  - name: "Compression"
    description: "Use compression for large responses"
    severity: "low"
    pattern: "compression|gzip|deflate"

# Performance targets
targets:
  response_time:
    api_endpoints: "< 200ms"
    page_loads: "< 2s"
    database_queries: "< 100ms"
    
  throughput:
    requests_per_second: "> 1000"
    concurrent_users: "> 10000"
    
  resource_usage:
    cpu_utilization: "< 70%"
    memory_usage: "< 80%"
    disk_io: "< 80%"

# Monitoring
monitoring:
  - name: "Response Time Monitoring"
    metric: "response_time_percentile_95"
    threshold: "2000ms"
    
  - name: "Error Rate Monitoring"
    metric: "error_rate"
    threshold: "1%"
    
  - name: "Throughput Monitoring"
    metric: "requests_per_second"
    threshold: "1000"
"@
}

function Get-ServiceConnectionDetails {
    param(
        [string]$ConnectionId
    )
    
    # In a real implementation, this would fetch service connection details
    # from Azure DevOps using the service connections API
    return @{
        id = $ConnectionId
        baseUrl = "https://api.openai.com/v1"
        model = "gpt-4"
        apiKey = "encrypted-api-key"
    }
}

function Get-WikiPageContent {
    param(
        [string]$ProjectName,
        [string]$PagePath,
        [hashtable]$Headers
    )
    
    try {
        $wikiUrl = "$organizationUri$ProjectName/_apis/wiki/wikis/default/pages" + "?path=$PagePath&api-version=7.0"
        $wikiResponse = Invoke-RestMethod -Uri $wikiUrl -Headers $Headers -Method Get
        return $wikiResponse.content
    }
    catch {
        Write-Warning "Could not fetch wiki page '$PagePath': $_"
        return ""
    }
}

function Get-WorkflowPrompt {
    param(
        [string]$Workflow
    )
    
    switch ($Workflow) {
        "specify" { return Get-SpecifyTemplate }
        "plan" { return Get-PlanTemplate }
        "tasks" { return Get-TasksTemplate }
        default { throw "Unknown workflow: $Workflow" }
    }
}

function Invoke-SpecKitWorkflow {
    param(
        [string]$Workflow,
        [hashtable]$Context,
        [hashtable]$LLMConnection,
        [float]$Temperature,
        [int]$MaxTokens
    )
    
    # This would make actual LLM API calls
    # For now, return mock results
    $mockResults = @{
        specify = @{
            artifacts = @(
                @{
                    content = "# Specification for $($Context.workItem.title)`n`nDetailed specification content..."
                    extension = "md"
                }
            )
            cost = 0.05
            tokens = @{ input = 1200; output = 800 }
        }
        plan = @{
            artifacts = @(
                @{
                    content = "# Implementation Plan for $($Context.workItem.title)`n`n## Phase 1: Analysis`n## Phase 2: Implementation"
                    extension = "md"
                }
            )
            cost = 0.03
            tokens = @{ input = 800; output = 600 }
        }
        tasks = @{
            artifacts = @(
                @{
                    content = "# Task Breakdown for $($Context.workItem.title)`n`n### Task 1: Core Implementation"
                    extension = "md"
                }
            )
            tasks = @(
                @{ title = "Implement core functionality"; description = "Core implementation"; effort = 8 },
                @{ title = "Add unit tests"; description = "Test coverage"; effort = 4 },
                @{ title = "Update documentation"; description = "API docs"; effort = 2 }
            )
            cost = 0.04
            tokens = @{ input = 1000; output = 500 }
        }
    }
    
    return $mockResults[$Workflow]
}

function Save-ArtifactsToRepository {
    param(
        [array]$Artifacts,
        [string]$WorkItemId,
        [string]$Workflow,
        [hashtable]$Headers
    )
    
    # This would save artifacts to the repository using Git API
    Write-Host "Saving $($Artifacts.Count) artifacts to repository /specs/ folder"
}

function Publish-ArtifactsToWiki {
    param(
        [array]$Artifacts,
        [string]$WorkItemId,
        [string]$Workflow,
        [hashtable]$Headers
    )
    
    # This would publish artifacts to Azure DevOps Wiki
    Write-Host "Publishing $($Artifacts.Count) artifacts to project wiki"
}

function Create-ChildWorkItems {
    param(
        [string]$ParentWorkItemId,
        [array]$Tasks,
        [hashtable]$Headers
    )
    
    # This would create child work items using Azure DevOps REST API
    Write-Host "Creating $($Tasks.Count) child work items for parent #$ParentWorkItemId"
    return $Tasks.Count
}

function Add-WorkItemComment {
    param(
        [string]$WorkItemId,
        [string]$Comment,
        [hashtable]$Headers
    )
    
    # This would add a comment to the work item
    Write-Host "Adding comment to work item #$WorkItemId"
}