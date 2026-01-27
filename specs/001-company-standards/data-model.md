# Data Model: Company Standards & Agent Context

## 1. Company Standards Templates

### 1.1 Constitution Template (`constitution-template.md`)
**Type**: Markdown Template
**Structure**:
- `Core Principles`: List of principles (Name, Description).
- `Technology Stack`: Approved/Forbidden technologies.
- `Quality Gates`: Testing/Linting requirements.
- `Governance`: How to amend the constitution.

### 1.2 Code Style Templates (`code-style/*.md`)
**Type**: Markdown Document
**Structure**:
- `Naming Conventions`: Variables, Functions, Classes.
- `Formatting`: Indentation, Braces, Line length.
- `Best Practices`: Language-specific idioms.
- `Anti-patterns`: What to avoid.
- `Examples`: Code snippets (Good vs Bad).

### 1.3 Security Checklist (`security-checklist.md`)
**Type**: Markdown Checklist
**Structure**:
- `Authentication`: Password policies, MFA.
- `Authorization`: RBAC, Principle of Least Privilege.
- `Data Protection`: Encryption (At rest, In transit).
- `Input Validation`: Sanitization, Encoding.
- `Logging`: Audit trails.

### 1.4 Review Guidelines (`review-guidelines.md`)
**Type**: Markdown Document
**Structure**:
- `Process`: When and how to request review.
- `Checklist`: What to look for.
- `Severity Levels`: Critical, Major, Minor.
- `Feedback Templates`: Standard phrases.

### 1.5 Incident Response (`incident-response.md`)
**Type**: Markdown Document
**Structure**:
- `Triage`: Severity classification.
- `Response Steps`: Immediate actions.
- `Communication`: Who to notify.
- `Post-Mortem`: Root cause analysis template.

## 2. Agent Context

### 2.1 Main Context (`AGENTS.md`)
**Type**: Markdown Document
**Role**: Single Source of Truth
**Structure**:
- `Project Info`: Name, Description.
- `Tech Stack`: Languages, Frameworks.
- `Conventions`: Coding style summary.
- `Commands`: Common scripts/commands.
- `Architecture`: High-level design.

### 2.2 Pointer Files (e.g., `.cursor/rules/specify-rules.mdc`)
**Type**: Markdown Document
**Role**: Reference
**Content**:
- Link to `AGENTS.md`.
- Brief instruction to read the main file.
