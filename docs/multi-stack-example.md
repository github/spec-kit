# Multi-Stack Guidelines Example: React + Java

This document demonstrates how Corporate Guidelines Phase 3 handles a multi-stack project with React frontend and Java backend.

## Project Structure

```text
my-fullstack-app/
├── .guidelines/
│   ├── README.md
│   ├── stack-mapping.json          # Maps paths to guidelines
│   ├── branch-config.json          # Branch naming config
│   ├── reactjs-guidelines.md       # Frontend standards
│   └── java-guidelines.md          # Backend standards
├── frontend/
│   ├── package.json                # React app
│   ├── src/
│   │   ├── components/
│   │   │   └── Login.tsx
│   │   └── services/
│   │       └── authService.ts
│   └── tsconfig.json
├── backend/
│   ├── pom.xml                     # Spring Boot app
│   └── src/main/java/
│       ├── controllers/
│       │   └── AuthController.java
│       └── services/
│           └── AuthService.java
└── shared/
    └── types/
        └── User.ts
```

## Stack Detection

When running `/specify tasks` or `/specify analyze`:

### Step 1: Auto-Detection

```text
Scanning project...

Found markers:
  - frontend/package.json → React detected
  - backend/pom.xml → Java detected

Detected stacks: React + Java (multi-stack project)
```

### Step 2: Load Guidelines

```text
Loading guidelines:
  ✓ .guidelines/reactjs-guidelines.md
  ✓ .guidelines/java-guidelines.md
  ✓ .guidelines/stack-mapping.json (path mappings)
```

### Step 3: Apply Mapping

Using `stack-mapping.json`:

```json
{
  "stacks": [
    {
      "name": "reactjs",
      "guideline": "reactjs-guidelines.md",
      "paths": ["frontend/**"],
      "extensions": [".tsx", ".jsx", ".ts", ".js"],
      "priority": 10
    },
    {
      "name": "java",
      "guideline": "java-guidelines.md",
      "paths": ["backend/**"],
      "extensions": [".java"],
      "priority": 10
    }
  ],
  "shared_paths": ["shared/**"]
}
```

**Result**:

- `frontend/**` → React guidelines apply
- `backend/**` → Java guidelines apply
- `shared/**` → Both guidelines apply (or constitution resolves conflicts)

## Task Generation Example

When running `/specify tasks` for a user story "Implement user authentication":

### Generated Tasks (Multi-Stack Aware)

```markdown
## Phase 1: Setup

- [ ] T001 [Frontend] Initialize React app using @acmecorp/create-react-app
  Location: frontend/
  Guidelines: reactjs-guidelines.md

- [ ] T002 [Backend] Initialize Spring Boot using corporate archetype
  Location: backend/
  Guidelines: java-guidelines.md

## Phase 2: Foundational

- [ ] T003 [Frontend] Install @acmecorp/ui-components library
  Location: frontend/package.json
  Guidelines: reactjs-guidelines.md (Mandatory Libraries section)

- [ ] T004 [Backend] Add com.acmecorp:acme-api-client dependency
  Location: backend/pom.xml
  Guidelines: java-guidelines.md (Mandatory Libraries section)

## Phase 3: User Story - Authentication (US1)

- [ ] T010 [US1] [Frontend] Create Login component in frontend/src/components/Login.tsx
  Using: @acmecorp/ui-components (Form, Input, Button)
  Guidelines: reactjs-guidelines.md

- [ ] T011 [US1] [Frontend] Implement auth service in frontend/src/services/authService.ts
  Using: @acmecorp/idm-client for OAuth2
  Guidelines: reactjs-guidelines.md (Security section)

- [ ] T012 [US1] [Backend] Create AuthController in backend/src/main/java/controllers/AuthController.java
  Using: @acmecorp/idm-client (Java SDK)
  Guidelines: java-guidelines.md (Security section)

- [ ] T013 [US1] [Backend] Implement AuthService in backend/src/main/java/services/AuthService.java
  Using: Spring Security + corporate OAuth2 config
  Guidelines: java-guidelines.md

## Phase 4: Polish

- [ ] T998 [Frontend] Verify React code compliance with reactjs-guidelines.md
- [ ] T999 [Backend] Verify Java code compliance with java-guidelines.md
- [ ] T1000 Check cross-stack integration (API contracts, types consistency)
```

## Analysis Example

When running `/specify analyze` on the above project:

### Multi-Stack Compliance Check

```markdown
## Guideline Compliance Analysis

### Stack Detection

- Frontend: React (detected from frontend/package.json)
- Backend: Java (detected from backend/pom.xml)

### Guidelines Loaded

- reactjs-guidelines.md (v1.0)
- java-guidelines.md (v1.0)
- stack-mapping.json (v1.0)

### Compliance Findings

#### Frontend (React)

✅ PASS: Uses @acmecorp/ui-components (required by reactjs-guidelines.md)
✅ PASS: Uses @acmecorp/idm-client for auth (required by reactjs-guidelines.md)
⚠️  WARNING: No TypeScript strict mode configured (recommended by reactjs-guidelines.md)

#### Backend (Java)

✅ PASS: Uses com.acmecorp:acme-api-client (required by java-guidelines.md)
❌ FAIL: Missing corporate Maven repository configuration (required by java-guidelines.md)
✅ PASS: Spring Boot version matches guidelines (2.7.x)

#### Cross-Stack

✅ PASS: API contract types consistent between frontend and backend
✅ PASS: Authentication strategy aligned (OAuth2 in both stacks)
```

## Precedence Resolution Example

When both guidelines have opinions about the same concern:

### Scenario: Logging Format

**React Guidelines**: Use `@acmecorp/logger` with JSON format
**Java Guidelines**: Use `logback` with XML configuration

**Resolution**:

1. Check `stack-mapping.json` precedence rules:

   ```json
   {
     "precedence_rules": {
       "constitution_beats_all": true,
       "explicit_beats_implicit": true
     }
   }
   ```

2. Check `/memory/constitution.md`:

   ```markdown
   ## Logging

   All services MUST use structured JSON logging for centralized log aggregation.
   ```

3. **Result**: Constitution requires JSON logging → Both stacks must use JSON format
   - Frontend: Use `@acmecorp/logger` (JSON) ✓
   - Backend: Configure `logback` for JSON output (not XML) ✓

## Token Optimization

For multi-stack projects, prompts use token-efficient loading:

### Summary Loading (Initial)

```text
Loading guideline summaries...

reactjs-guidelines.md (summary):
  - Architecture: React + TypeScript with hooks
  - UI Library: @acmecorp/ui-components
  - Auth: @acmecorp/idm-client (OAuth2)
  - Testing: Jest + React Testing Library

java-guidelines.md (summary):
  - Architecture: Spring Boot + Clean Architecture
  - API SDK: com.acmecorp:acme-api-client
  - Auth: Spring Security + OAuth2
  - Testing: JUnit 5 + Mockito
```

### On-Demand Detail Loading

```text
Task: Configure frontend authentication
Loading detailed section: reactjs-guidelines.md → "Security & Compliance"

Task: Configure backend API client
Loading detailed section: java-guidelines.md → "Mandatory Libraries"
```

## Validation

Run the validation tool to check multi-stack configuration:

```bash
python3 scripts/validate-guidelines.py

# Output:
🔍 Validating Corporate Guidelines...

✅ PASSED CHECKS: 21
✓ All stack mappings valid
✓ All referenced guideline files exist
✓ Path patterns are valid
✓ Precedence rules defined
```

## Benefits

1. **Contextual Application**: React guidelines apply to frontend, Java guidelines apply to backend
2. **Clear Organization**: No confusion about which guideline applies where
3. **Conflict Resolution**: Precedence rules handle overlapping concerns
4. **Token Efficient**: Load summaries first, details on-demand
5. **Flexible**: Customize `stack-mapping.json` for your project structure

## See Also

- [Corporate Guidelines README](.guidelines/README.md)
- [Stack Mapping Configuration](.guidelines/stack-mapping.json)
- [Guideline Validation Tool](scripts/validate-guidelines.py)
