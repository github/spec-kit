# Onboarding Existing Projects to Spec-Driven Development

The Spec-Kit MCP server provides powerful tools to onboard existing projects to a spec-driven development workflow. This includes both complete project onboarding and progressive onboarding for incremental adoption across teams and features.

## Overview

The Spec-Kit MCP server supports two onboarding approaches:

### Complete Project Onboarding
For migrating entire projects at once. This approach:
- Analyzes complete project structures and codebases
- Extracts requirements and specifications from documentation and code
- Generates standardized specifications following Spec-Kit format
- Creates detailed migration plans for adopting spec-driven development
- Performs complete end-to-end onboarding analysis

### Progressive Onboarding (NEW)
For incremental adoption by different teams, features, or sub-projects. This approach:
- Enables feature-level and component-level onboarding
- Supports multiple teams working on different parts independently
- Provides specification assembly and coordination tools
- Manages dependencies between features during progressive migration
- Tracks progress across multiple onboarding efforts

## MCP Tools Overview

### Complete Project Onboarding Tools

#### 1. `analyze_existing_project`
Analyzes the structure of an existing project to understand its organization.

**Parameters:**
- `project_path` (required): Path to the existing project directory
- `max_depth` (optional): Maximum directory depth to scan (default: 3)

#### 2. `parse_existing_documentation`
Parses existing documentation files to extract requirements and specifications.

**Parameters:**
- `project_path` (required): Path to the project directory
- `file_patterns` (optional): List of file patterns to search for

#### 3. `extract_requirements_from_code`
Extracts requirements from code comments, docstrings, and TODO/FIXME items.

**Parameters:**
- `project_path` (required): Path to the project directory
- `file_patterns` (optional): List of file patterns to search for

#### 4. `generate_standardized_spec`
Generates a standardized specification from existing project analysis.

**Parameters:**
- `project_analysis` (required): Result from `analyze_existing_project`
- `documentation_analysis` (required): Result from `parse_existing_documentation`
- `code_analysis` (required): Result from `extract_requirements_from_code`

#### 5. `create_migration_plan`
Creates a detailed migration plan for adopting spec-driven development.

**Parameters:**
- `project_analysis` (required): Result from `analyze_existing_project`
- `standardized_spec` (required): Result from `generate_standardized_spec`

#### 6. `onboard_existing_project`
Complete end-to-end onboarding (combines all analysis steps).

**Parameters:**
- `project_path` (required): Path to the existing project directory
- `max_depth` (optional): Maximum directory depth to scan (default: 3)
- `include_migration_plan` (optional): Whether to include migration plan (default: true)

### Progressive Onboarding Tools (NEW)

#### 7. `analyze_feature_component`
Analyzes a specific feature or component within a project for progressive onboarding.

**Parameters:**
- `project_path` (required): Path to the main project directory
- `feature_path` (required): Relative path to the feature/component within the project
- `max_depth` (optional): Maximum directory depth to scan within the feature (default: 2)

**Returns:** Feature-specific analysis including:
- File counts and complexity estimation
- Languages and frameworks detected
- Dependencies and external references
- Test coverage and documentation status
- Integration points and potential boundaries

#### 8. `extract_feature_boundaries`
Identifies logical feature boundaries within a project to support progressive onboarding.

**Parameters:**
- `project_path` (required): Path to the project directory
- `analysis_depth` (optional): Depth to analyze for feature boundaries (default: 2)

**Returns:** Feature boundary analysis including:
- Suggested feature candidates
- Confidence scores and reasoning
- Boundary criteria used
- Sub-feature identification

#### 9. `onboard_project_feature`
Onboards a specific feature to spec-driven development with dependency analysis.

**Parameters:**
- `project_path` (required): Path to the main project directory
- `feature_path` (required): Relative path to the feature within the project
- `include_dependencies` (optional): Whether to analyze feature dependencies (default: true)

**Returns:** Complete feature onboarding including:
- Feature-specific specification
- Dependency analysis and integration points
- Implementation recommendations
- Readiness assessment

#### 10. `merge_feature_specifications`
Merges multiple feature specifications into a master specification.

**Parameters:**
- `feature_specifications` (required): List of feature specification dictionaries to merge
- `master_project_info` (optional): Master project information for context

**Returns:** Merged specification including:
- Consolidated requirements and user stories
- Integrated technical stack
- Cross-feature coordination notes
- Assembly metadata and conflict information

#### 11. `detect_specification_conflicts`
Detects conflicts between multiple feature specifications.

**Parameters:**
- `feature_specifications` (required): List of feature specification dictionaries to analyze

**Returns:** Conflict analysis including:
- API endpoint conflicts
- Requirement conflicts
- Technology stack conflicts
- Resolution suggestions

#### 12. `resolve_feature_dependencies`
Analyzes and documents dependencies between features.

**Parameters:**
- `feature_specifications` (required): List of feature specification dictionaries to analyze

**Returns:** Dependency analysis including:
- Dependency graph and relationships
- Circular dependency detection
- Critical dependency identification
- Implementation order suggestions
- Resolution plan

#### 13. `create_progressive_migration_plan`
Creates a progressive migration plan for incremental adoption of spec-driven development.

**Parameters:**
- `project_path` (required): Path to the project directory
- `feature_boundaries` (required): Result from `extract_feature_boundaries`
- `priority_features` (optional): List of features to prioritize

**Returns:** Progressive migration plan including:
- Phased migration approach
- Resource allocation and timeline estimates
- Success metrics and risk mitigation
- Coordination plan for multiple teams

#### 14. `track_onboarding_progress`
Tracks progress of progressive onboarding migration.

**Parameters:**
- `project_path` (required): Path to the project directory
- `migration_plan` (required): Result from `create_progressive_migration_plan`
- `completed_features` (optional): List of features that have been completed

**Returns:** Progress tracking including:
- Overall and phase-wise progress
- Feature status tracking
- Next actions and recommendations
- Blocker identification

#### 15. `validate_specification_consistency`
Validates consistency across multiple feature specifications.

**Parameters:**
- `feature_specifications` (required): List of feature specification dictionaries to validate

**Returns:** Consistency validation including:
- Format and naming consistency checks
- Requirement and technical consistency
- Inconsistency identification
- Improvement recommendations

## Usage Examples

### Complete Project Onboarding

#### Basic Project Analysis
```javascript
// Analyze an existing project structure
const analysis = await mcpClient.callTool("analyze_existing_project", {
  project_path: "/path/to/your/project",
  max_depth: 3
});
```

#### Parse Documentation
```javascript
// Extract requirements from documentation
const docs = await mcpClient.callTool("parse_existing_documentation", {
  project_path: "/path/to/your/project",
  file_patterns: ["*.md", "README*", "docs/**/*"]
});
```

#### Complete Onboarding
```javascript
// Perform complete end-to-end onboarding
const onboarding = await mcpClient.callTool("onboard_existing_project", {
  project_path: "/path/to/your/project",
  max_depth: 2,
  include_migration_plan: true
});

console.log("Project:", onboarding.summary.project_name);
console.log("Size:", onboarding.summary.estimated_size);
console.log("Languages:", onboarding.summary.languages);
console.log("Next steps:", onboarding.summary.next_steps);
```

### Progressive Onboarding Workflow (NEW)

#### Step 1: Identify Feature Boundaries
```javascript
// Discover logical feature boundaries in your project
const boundaries = await mcpClient.callTool("extract_feature_boundaries", {
  project_path: "/path/to/your/project",
  analysis_depth: 2
});

// Review suggested features
boundaries.suggested_features.forEach(feature => {
  console.log(`Feature: ${feature.feature_name}`);
  console.log(`Confidence: ${feature.confidence_score}`);
  console.log(`Reasons: ${feature.reasons.join(', ')}`);
});
```

#### Step 2: Analyze Individual Features
```javascript
// Analyze a specific feature component
const featureAnalysis = await mcpClient.callTool("analyze_feature_component", {
  project_path: "/path/to/your/project",
  feature_path: "src/user-management",
  max_depth: 2
});

console.log(`Feature complexity: ${featureAnalysis.estimated_complexity}`);
console.log(`External dependencies: ${featureAnalysis.external_references.length}`);
```

#### Step 3: Onboard Features Progressively
```javascript
// Onboard individual features
const featureOnboarding = await mcpClient.callTool("onboard_project_feature", {
  project_path: "/path/to/your/project",
  feature_path: "src/user-management",
  include_dependencies: true
});

console.log(`Feature readiness: ${featureOnboarding.summary.ready_for_spec_driven}`);
```

#### Step 4: Create Progressive Migration Plan
```javascript
// Create a phased migration plan
const migrationPlan = await mcpClient.callTool("create_progressive_migration_plan", {
  project_path: "/path/to/your/project",
  feature_boundaries: boundaries,
  priority_features: ["user-management", "core-api"]
});

// Review migration phases
migrationPlan.migration_phases.forEach(phase => {
  console.log(`Phase ${phase.phase}: ${phase.name}`);
  console.log(`Duration: ${phase.duration}`);
  console.log(`Features: ${phase.features.join(', ')}`);
});
```

#### Step 5: Track Progress
```javascript
// Track onboarding progress
const progress = await mcpClient.callTool("track_onboarding_progress", {
  project_path: "/path/to/your/project",
  migration_plan: migrationPlan,
  completed_features: ["user-management"]
});

console.log(`Overall progress: ${progress.overall_progress.completion_percentage}%`);
console.log(`Next actions:`, progress.next_actions);
```

#### Step 6: Merge Feature Specifications
```javascript
// Once multiple features are onboarded, merge their specifications
const mergedSpec = await mcpClient.callTool("merge_feature_specifications", {
  feature_specifications: [
    featureOnboarding1.feature_specification,
    featureOnboarding2.feature_specification,
    featureOnboarding3.feature_specification
  ],
  master_project_info: {
    project_name: "MyApplication",
    description: "Multi-feature application"
  }
});
```

#### Step 7: Validate Consistency
```javascript
// Validate consistency across feature specifications
const validation = await mcpClient.callTool("validate_specification_consistency", {
  feature_specifications: [
    featureSpec1,
    featureSpec2,
    featureSpec3
  ]
});

console.log(`Consistency score: ${validation.consistency_score}`);
console.log(`Status: ${validation.overall_status}`);
console.log(`Recommendations:`, validation.recommendations);
```

#### Step 8: Detect and Resolve Conflicts
```javascript
// Detect conflicts between feature specifications
const conflicts = await mcpClient.callTool("detect_specification_conflicts", {
  feature_specifications: [featureSpec1, featureSpec2, featureSpec3]
});

if (conflicts.conflicts.length > 0) {
  console.log("Conflicts detected:");
  conflicts.conflicts.forEach(conflict => {
    console.log(`- ${conflict.type}: ${conflict.description}`);
  });
}

// Analyze feature dependencies
const dependencies = await mcpClient.callTool("resolve_feature_dependencies", {
  feature_specifications: [featureSpec1, featureSpec2, featureSpec3]
});

console.log("Suggested implementation order:", dependencies.implementation_order);
```

## Migration Workflows

### Complete Project Migration Workflow

The typical workflow for onboarding an entire existing project is:

1. **Initial Analysis**: Use `analyze_existing_project` to understand the project structure
2. **Documentation Review**: Use `parse_existing_documentation` to extract existing requirements
3. **Code Analysis**: Use `extract_requirements_from_code` to find additional requirements
4. **Specification Generation**: Use `generate_standardized_spec` to create a Spec-Kit compatible specification
5. **Migration Planning**: Use `create_migration_plan` to create a detailed migration roadmap

Or simply use `onboard_existing_project` for a complete end-to-end analysis.

### Progressive Onboarding Workflow (NEW)

The progressive onboarding workflow supports incremental adoption across teams and features:

#### Phase 1: Discovery and Planning
1. **Feature Identification**: Use `extract_feature_boundaries` to identify logical features
2. **Feature Prioritization**: Select which features to onboard first based on:
   - Team readiness and availability
   - Feature complexity and dependencies
   - Business priority and impact
3. **Progressive Planning**: Use `create_progressive_migration_plan` to create a phased approach

#### Phase 2: Feature-Level Onboarding
1. **Feature Analysis**: Use `analyze_feature_component` for each selected feature
2. **Feature Onboarding**: Use `onboard_project_feature` to create feature specifications
3. **Dependency Analysis**: Use `resolve_feature_dependencies` to understand inter-feature relationships
4. **Conflict Detection**: Use `detect_specification_conflicts` to identify potential issues early

#### Phase 3: Integration and Coordination
1. **Specification Merging**: Use `merge_feature_specifications` to create master specifications
2. **Consistency Validation**: Use `validate_specification_consistency` to ensure coherence
3. **Progress Tracking**: Use `track_onboarding_progress` to monitor overall advancement
4. **Continuous Refinement**: Iterate based on feedback and lessons learned

#### Phase 4: Scaling and Optimization
1. **Team Coordination**: Establish cross-team processes for specification management
2. **Workflow Integration**: Integrate spec-driven development into regular team workflows
3. **Continuous Improvement**: Regular reviews and optimization of the progressive process
4. **Knowledge Sharing**: Document and share best practices across teams

## Migration Approaches Comparison

| Aspect | Complete Migration | Progressive Migration |
|--------|-------------------|----------------------|
| **Timeline** | 2-4 months | 3-8 months |
| **Risk** | Higher (all-or-nothing) | Lower (incremental) |
| **Resource Requirements** | High initial commitment | Distributed over time |
| **Team Impact** | Significant disruption | Minimal disruption |
| **Flexibility** | Limited once started | High adaptability |
| **Coordination Complexity** | Medium | Higher |
| **Early Value** | Delayed | Immediate for early features |
| **Best For** | Small teams, simple projects | Large teams, complex projects |

## Migration Phases

### Complete Project Migration Phases

The migration plan includes these standard phases:

1. **Assessment and Planning** (1-2 weeks): Complete analysis and roadmap creation
2. **Specification Creation** (2-4 weeks): Comprehensive project specification development
3. **Process Integration** (2-3 weeks): Integrate spec-driven processes into workflow
4. **Pilot Implementation** (3-4 weeks): Pilot new approach with selected features
5. **Full Adoption** (Ongoing): Complete transition to spec-driven development

### Progressive Migration Phases

Progressive migration typically follows these phases:

1. **Pilot Migration** (2-3 weeks): Start with 1-2 simple features
   - Establish spec-driven workflow
   - Train team on new process
   - Validate tooling and templates
   - Gather initial feedback

2. **Progressive Expansion** (3-4 weeks per batch): Add more features gradually
   - Apply spec-driven process to additional features
   - Refine and optimize workflow
   - Address integration challenges
   - Build team expertise

3. **Integration and Optimization** (2-3 weeks): Integrate all features
   - Create master specification
   - Resolve cross-feature dependencies
   - Optimize development workflow
   - Establish maintenance procedures

## Best Practices

### Complete Project Onboarding
- **Start with Analysis**: Always begin with a thorough project analysis
- **Review Results**: Manually review and validate extracted requirements
- **Fill Gaps**: Address any gaps identified in the analysis
- **Stakeholder Validation**: Validate specifications with project stakeholders
- **Full Migration**: Follow the phased approach for complete transition
- **Team Training**: Ensure team is trained on spec-driven development methodology

### Progressive Onboarding (NEW)
- **Start Small**: Begin with 1-2 simple, well-defined features to build confidence
- **Choose Pilot Features Wisely**: Select features that are:
  - Relatively independent
  - Well-understood by the team
  - Have clear boundaries
  - Lower complexity and risk
- **Establish Team Champions**: Identify team members who can drive adoption in each feature area
- **Regular Coordination**: Set up regular sync meetings between feature teams
- **Document Lessons Learned**: Capture insights and improvements for subsequent features
- **Iterative Improvement**: Continuously refine the process based on feedback
- **Dependency Management**: Analyze and plan for inter-feature dependencies early
- **Conflict Resolution**: Address specification conflicts promptly
- **Progress Visibility**: Maintain clear visibility into overall migration progress

### Team Coordination for Progressive Onboarding
- **Clear Ownership**: Establish clear ownership for each feature specification
- **Interface Contracts**: Define clear interfaces between features early
- **Regular Reviews**: Implement regular cross-feature specification reviews
- **Shared Standards**: Establish and maintain shared specification standards
- **Communication Channels**: Set up dedicated channels for coordination
- **Decision Making**: Define clear decision-making processes for cross-feature issues

### Feature Selection Strategies
- **Complexity-First**: Start with simpler features to build momentum
- **Value-First**: Prioritize features that deliver business value quickly
- **Dependency-First**: Start with features that others depend on
- **Team-First**: Begin with teams most ready and motivated for change
- **Risk-First**: Address highest-risk features early when resources are fresh

### Common Pitfalls to Avoid
- **Over-Ambitious Scope**: Don't try to onboard too many features simultaneously
- **Insufficient Coordination**: Neglecting cross-feature coordination leads to conflicts
- **Specification Drift**: Allowing quality and consistency to degrade over time
- **Resource Competition**: Teams competing for limited migration resources
- **Communication Gaps**: Poor communication between feature teams and stakeholders
- **Process Rigidity**: Being too rigid about process when flexibility is needed

## Supported File Types

The onboarding tools support analysis of:

**Documentation:**
- Markdown files (*.md)
- README files
- Text files (*.txt, *.rst)
- Documentation directories

**Code:**
- Python (*.py)
- JavaScript/TypeScript (*.js, *.ts)
- Java (*.java)
- C# (*.cs)
- C/C++ (*.c, *.cpp, *.h, *.hpp)
- Configuration files (package.json, pyproject.toml, etc.)

**Configuration:**
- YAML/JSON files
- Docker files
- CI/CD configurations (.github, .gitlab)
- Build configurations (Makefile, etc.)

## Troubleshooting

**Large Projects**: For very large projects, consider:
- Reducing `max_depth` parameter
- Using specific `file_patterns` to focus analysis
- Running analysis on project subsections

**Analysis Timeouts**: If analysis takes too long:
- Exclude large directories (node_modules, .git, etc.)
- Use more specific file patterns
- Analyze project sections separately

**Missing Requirements**: If few requirements are found:
- Check documentation file patterns
- Review file naming conventions
- Manually supplement with stakeholder interviews

## Integration with Existing Workflow

Both complete and progressive onboarding tools integrate seamlessly with existing Spec-Kit workflows:

### Standard Integration
- Generated specifications use standard Spec-Kit templates
- Migration plans align with Spec-Kit methodology
- Output formats are compatible with existing tools
- Can be used alongside `init_project` for hybrid approaches

### Progressive Integration (NEW)
- **Feature-Level Branching**: Each feature can have its own specification branch
- **Incremental Documentation**: Build documentation incrementally as features are onboarded
- **Gradual Process Adoption**: Teams can adopt spec-driven practices at their own pace
- **Cross-Feature Coordination**: Tools support coordination between independently onboarded features
- **Specification Assembly**: Multiple feature specifications can be merged into master specifications
- **Continuous Integration**: Progress tracking integrates with existing project management tools

### Enterprise Integration
- **Multi-Team Support**: Tools designed for organizations with multiple development teams
- **Governance Integration**: Supports integration with existing architecture and governance processes
- **Compliance**: Progressive approach helps maintain compliance during transition
- **Risk Management**: Incremental approach reduces risk compared to big-bang migrations
- **Resource Planning**: Better resource allocation across teams and time periods

This enables organizations to adopt spec-driven development for both new and existing projects using a consistent approach and toolset, while accommodating different team needs and organizational constraints.