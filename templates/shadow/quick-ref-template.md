# Quick Reference: [Project Name]

**Ultra-compact reference for AI agents (<200 tokens)**

---

## Stack
- **Language:** [Primary language]
- **Framework:** [Main framework]
- **Database:** [Database type]
- **Build:** [Build tool]

## Structure
```
src/
  core/      # Core business logic
  api/       # API endpoints
  utils/     # Helper functions
tests/       # Test files
```

## Patterns
- **Services:** Business logic in `src/services/`
- **Models:** Data models in `src/models/`
- **Controllers:** API controllers in `src/api/controllers/`

## Key Files
- `src/index.ts` - Entry point
- `src/config.ts` - Configuration
- `tests/setup.ts` - Test setup

## Build
```bash
npm install && npm run build && npm test
```

## Style
- Use TypeScript strict mode
- Async/await for promises
- Jest for testing
- ESLint + Prettier

## Current Focus
[Brief description of current work]

## Avoid
- Don't modify core interfaces
- Don't skip tests
- Don't use deprecated APIs
