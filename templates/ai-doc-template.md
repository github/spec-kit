# AI Documentation: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]
**Status**: [Draft/Complete]
**Related Docs**: [spec.md](./spec.md) | [plan.md](./plan.md) | [tasks.md](./tasks.md)

## Feature Overview

### Purpose
[1-2 sentence summary of what this feature does and why it exists]

### Key Capabilities
- [Primary capability 1]
- [Primary capability 2]
- [Primary capability 3]

### User Impact
[How users interact with this feature - what changes for them]

## Code Map

### Core Implementation Files

```text
[List primary files/modules with brief descriptions]

src/
├── [module1/]
│   ├── [file1.ext]        # [Purpose and responsibility]
│   └── [file2.ext]        # [Purpose and responsibility]
├── [module2/]
│   └── [file3.ext]        # [Purpose and responsibility]
└── [file4.ext]            # [Purpose and responsibility]

tests/
├── [test1.ext]            # [What it tests]
└── [test2.ext]            # [What it tests]
```

### Entry Points

**Primary Entry Points** (where execution starts):
- **[Entry Point 1]**: `[file:line]` - [When/how this is triggered]
- **[Entry Point 2]**: `[file:line]` - [When/how this is triggered]

**Public APIs/Interfaces**:
- **[Function/Class/Endpoint 1]**: `[location]` - [Purpose]
- **[Function/Class/Endpoint 2]**: `[location]` - [Purpose]

## Architecture Snapshot

### Component Diagram

```text
[ASCII/text diagram showing relationships between key components]

┌─────────────┐
│   [Comp A]  │──────▶ [Comp B]
└─────────────┘         │
       │                │
       ▼                ▼
   [Comp C]         [Comp D]
```

### Component Responsibilities

**[Component 1]** (`[location]`)
- **Purpose**: [What it does]
- **Dependencies**: [What it depends on]
- **Used by**: [What uses it]

**[Component 2]** (`[location]`)
- **Purpose**: [What it does]
- **Dependencies**: [What it depends on]
- **Used by**: [What uses it]

[Continue for all major components]

## Data Flow

### Primary Data Flow

```text
[Step-by-step flow of data through the system]

1. [Input/Trigger]
   ↓
2. [First Processing Step] ([component/file])
   ↓
3. [Second Processing Step] ([component/file])
   ↓
4. [Output/Result]
```

### Data Transformations

- **Input**: [What data comes in and from where]
- **Processing**: [How data is transformed]
- **Output**: [What data goes out and to where]

### State Management

**State Location**: [Where state is stored - database, memory, file system, etc.]

**Key State Elements**:
- **[State 1]**: [What it represents, when it changes]
- **[State 2]**: [What it represents, when it changes]

**State Transitions**:
```text
[Initial State] → [Event/Action] → [New State]
```

## Key Components Deep Dive

### [Component/Class/Module 1]

**Location**: `[file:line]`
**Type**: [Class/Function/Module/Service]

**Purpose**: [Detailed explanation of what this does]

**Key Methods/Functions**:
- **`[method1]`**: [What it does, parameters, return value]
- **`[method2]`**: [What it does, parameters, return value]

**Dependencies**:
- [Dependency 1]: [Why needed]
- [Dependency 2]: [Why needed]

**Usage Example**:
```[language]
[Brief code example showing typical usage]
```

### [Component/Class/Module 2]

[Same structure as above]

## Integration Points

### External Dependencies

**Third-Party Libraries**:
- **[Library 1]** (`[version]`): [Why used, what functionality it provides]
- **[Library 2]** (`[version]`): [Why used, what functionality it provides]

### Internal System Connections

**Connected Features**:
- **[Feature/Module 1]**: [How they interact, data exchanged]
- **[Feature/Module 2]**: [How they interact, data exchanged]

### Data Storage

**Database/Storage Type**: [Type of storage used]

**Schema/Structure**:
```text
[Tables/Collections/Files involved]

[Entity 1]
- field1: [type, purpose]
- field2: [type, purpose]

[Entity 2]
- field1: [type, purpose]
- field2: [type, purpose]
```

**Queries/Operations**:
- [Key query/operation 1]: [Purpose]
- [Key query/operation 2]: [Purpose]

### External APIs/Services

**Outbound Calls**:
- **[API/Service 1]**: [What it's used for, endpoints called]
- **[API/Service 2]**: [What it's used for, endpoints called]

**Inbound Interfaces**:
- **[Endpoint/Interface 1]**: [What it accepts, what it returns]
- **[Endpoint/Interface 2]**: [What it accepts, what it returns]

## Testing Guide

### Test Coverage

**Test Files**:
- `[test-file-1]`: [What it covers]
- `[test-file-2]`: [What it covers]

**Coverage Areas**:
- ✅ [Covered area 1]
- ✅ [Covered area 2]
- ⚠️ [Partially covered area]
- ❌ [Not covered area - explain why]

### Running Tests

**Unit Tests**:
```bash
[Command to run unit tests for this feature]
```

**Integration Tests**:
```bash
[Command to run integration tests for this feature]
```

**Manual Testing**:
1. [Step 1 to manually verify feature works]
2. [Step 2 to manually verify feature works]
3. [Expected outcome]

### Test Data

**Required Test Data**:
- [Data 1]: [How to set up]
- [Data 2]: [How to set up]

**Test Fixtures**:
- `[fixture-file-1]`: [What it provides]
- `[fixture-file-2]`: [What it provides]

## Modification Guide

### Common Modifications

**Adding a new [capability type]**:
1. [Step 1 - which file to modify]
2. [Step 2 - what to add/change]
3. [Step 3 - tests to update]
4. [Step 4 - validation]

**Changing [behavior/configuration]**:
1. [Step 1 - where the configuration lives]
2. [Step 2 - how to modify it]
3. [Step 3 - side effects to consider]

**Extending [integration point]**:
1. [Step 1 - interface to implement/extend]
2. [Step 2 - where to register new implementation]
3. [Step 3 - testing requirements]

### Code Patterns

**Pattern 1: [Pattern Name]**
- **When to use**: [Scenario where this pattern is appropriate]
- **Example**: `[file:line]` - [Brief code snippet or reference]
- **Why**: [Rationale for this pattern]

**Pattern 2: [Pattern Name]**
- **When to use**: [Scenario where this pattern is appropriate]
- **Example**: `[file:line]` - [Brief code snippet or reference]
- **Why**: [Rationale for this pattern]

### Configuration

**Configuration Files**:
- `[config-file-1]`: [What it configures]
- `[config-file-2]`: [What it configures]

**Key Configuration Options**:
- **`[option-1]`**: [What it does, valid values, default]
- **`[option-2]`**: [What it does, valid values, default]

## Implementation Gotchas

### Non-Obvious Behaviors

**[Gotcha 1]**: [Title]
- **Issue**: [What's not obvious]
- **Why**: [Reason for this implementation]
- **Impact**: [What happens if you don't know this]
- **Location**: `[file:line]`

**[Gotcha 2]**: [Title]
- **Issue**: [What's not obvious]
- **Why**: [Reason for this implementation]
- **Impact**: [What happens if you don't know this]
- **Location**: `[file:line]`

### Edge Cases

**[Edge Case 1]**:
- **Scenario**: [When this happens]
- **Behavior**: [How system handles it]
- **Code**: `[file:line]`

**[Edge Case 2]**:
- **Scenario**: [When this happens]
- **Behavior**: [How system handles it]
- **Code**: `[file:line]`

### Performance Considerations

**Bottlenecks**:
- **[Operation/Component]**: [Why it might be slow, mitigation]

**Optimization Opportunities**:
- **[Area 1]**: [Potential improvement, trade-offs]
- **[Area 2]**: [Potential improvement, trade-offs]

**Resource Usage**:
- **Memory**: [Expected usage, peak scenarios]
- **CPU**: [Expected usage, intensive operations]
- **I/O**: [Database calls, file operations, network requests]

### Security & Privacy

**Security Considerations**:
- [Security concern 1]: [How it's addressed]
- [Security concern 2]: [How it's addressed]

**Data Privacy**:
- [What sensitive data is handled]
- [How it's protected]
- [Compliance requirements met]

## AI Agent Guidance

### When Modifying This Feature

**Before Making Changes**:
1. [Critical thing to check/understand first]
2. [Second critical thing to check/understand]
3. [Third critical thing to check/understand]

**Must Preserve**:
- [Invariant 1 that must not be broken]
- [Invariant 2 that must not be broken]
- [Behavior that must remain unchanged]

**Safe to Change**:
- [What can be safely modified without breaking things]
- [What can be safely extended]

### Debugging Tips

**Common Issues**:
1. **[Issue Description]**
   - **Symptoms**: [How to recognize it]
   - **Cause**: [Root cause]
   - **Fix**: [How to resolve]
   - **Location**: `[file:line]`

2. **[Issue Description]**
   - **Symptoms**: [How to recognize it]
   - **Cause**: [Root cause]
   - **Fix**: [How to resolve]
   - **Location**: `[file:line]`

**Debugging Entry Points**:
- Start here: `[file:function:line]` - [Why this is a good starting point]
- Breakpoint suggestion: `[file:line]` - [What to inspect]
- Logging: `[Where to add logs to track flow]`

### Related Documentation

**Internal Docs**:
- [spec.md](./spec.md) - Original requirements
- [plan.md](./plan.md) - Architecture and technical approach
- [tasks.md](./tasks.md) - Implementation tasks

**External Resources**:
- [Resource 1]: [URL] - [Why it's relevant]
- [Resource 2]: [URL] - [Why it's relevant]

**Dependencies Documentation**:
- [Library 1 docs]: [URL]
- [Library 2 docs]: [URL]

## Appendix

### Glossary

- **[Term 1]**: [Definition specific to this feature]
- **[Term 2]**: [Definition specific to this feature]

### Change History

| Date | Change | Reason | Modified By |
|------|--------|--------|-------------|
| [YYYY-MM-DD] | [What changed] | [Why] | [Who/What] |

### Future Enhancements

**Planned Improvements**:
- [Enhancement 1]: [Description, priority]
- [Enhancement 2]: [Description, priority]

**Known Limitations**:
- [Limitation 1]: [Description, workaround if any]
- [Limitation 2]: [Description, workaround if any]
