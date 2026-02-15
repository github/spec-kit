---
type: module
id: [MODULE_ID]
name: [Human Readable Module Name]
path: [src/module-path/]
created: [YYYY-MM-DD]
updated: [YYYY-MM-DD]
status: [active | deprecated | planned]
owners: [team or individuals responsible]
dependencies:
  internal: [other-module-1, other-module-2]
  external: [npm-package-1, npm-package-2]
related_decisions: [decision-id-1, decision-id-2]
---

# [Module Name]

## Purpose

[One paragraph describing what this module does and why it exists.]

## Responsibilities

This module is responsible for:
- [Responsibility 1]
- [Responsibility 2]
- [Responsibility 3]

This module is NOT responsible for:
- [Thing that might be confused as part of this module]
- [Another boundary clarification]

## Architecture

```
[ASCII diagram showing internal structure or data flow]

┌─────────────────┐
│   Public API    │
├─────────────────┤
│  [Component 1]  │──────▶ [External Service]
│  [Component 2]  │
│  [Component 3]  │
└─────────────────┘
```

## Public API

### Functions/Methods

#### `functionName(param: Type): ReturnType`
[Brief description of what it does]

**Parameters:**
- `param`: [Description]

**Returns:** [Description]

**Example:**
```typescript
const result = functionName(input);
```

#### `anotherFunction(...)`
[Description]

### Types/Interfaces

#### `TypeName`
```typescript
interface TypeName {
  field1: string;
  field2: number;
}
```
[Description of when/how to use this type]

## Internal Components

| Component | Purpose |
|-----------|---------|
| `ComponentA` | [What it does] |
| `ComponentB` | [What it does] |
| `helperFunction` | [What it does] |

## Data Flow

[Describe how data moves through this module]

1. [Step 1: Input comes from...]
2. [Step 2: Processing happens in...]
3. [Step 3: Output goes to...]

## Error Handling

[How does this module handle errors? What errors can it throw?]

| Error | When it occurs | How to handle |
|-------|----------------|---------------|
| `ErrorType1` | [Condition] | [Recovery strategy] |
| `ErrorType2` | [Condition] | [Recovery strategy] |

## Configuration

[If the module has configuration options, document them here]

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `optionA` | `string` | `"default"` | [What it controls] |
| `optionB` | `boolean` | `true` | [What it controls] |

## Testing

[How to test this module]

```bash
# Run module tests
npm test -- src/module-path/

# Run specific test file
npm test -- src/module-path/__tests__/specific.test.ts
```

### Test Coverage Areas
- [Area 1 that's tested]
- [Area 2 that's tested]
- [Known gaps in testing, if any]

## Common Tasks

### [Task 1: e.g., "Adding a new endpoint"]
1. [Step 1]
2. [Step 2]
3. [Step 3]

### [Task 2: e.g., "Modifying validation rules"]
1. [Step 1]
2. [Step 2]

## Gotchas / Known Issues

- ⚠️ [Something that might trip up developers]
- ⚠️ [Non-obvious behavior to be aware of]

## Changelog

| Date | Change | Decision |
|------|--------|----------|
| [YYYY-MM-DD] | [What changed] | [Link to decision if applicable] |
| [YYYY-MM-DD] | Initial implementation | - |

## Related Modules

- **[Related Module]**: [How they interact]
- **[Another Module]**: [Relationship]
