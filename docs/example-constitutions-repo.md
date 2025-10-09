# Example Constitution Repository

This is an example structure for creating a constitution repository that can be used with spec-kit's remote constitutions feature.

## Repository Structure

```
my-constitutions/
├── README.md                          # Overview and usage guide
├── python-microservices.md            # Python microservices constitution
├── golang-api.md                      # Go API services constitution
├── react-frontend.md                  # React frontend constitution
├── nodejs-backend.md                  # Node.js backend constitution
├── data-pipeline.md                   # Data pipeline constitution
└── mobile-app.md                      # Mobile app constitution
```

## Example Constitution Files

### python-microservices.md

```markdown
# Python Microservices Constitution

## Core Principles

### I. API-First Design
Every microservice must define its API contract using OpenAPI 3.0 specification before implementation begins. APIs must be versioned and maintain backward compatibility.

### II. Test-Driven Development (NON-NEGOTIABLE)
- Unit test coverage must be >= 80%
- Integration tests required for all API endpoints
- Tests must pass before merging to main branch
- TDD cycle: Red → Green → Refactor

### III. Observability
All services must implement:
- Structured logging using Python's `structlog` library (JSON format)
- Distributed tracing via OpenTelemetry
- Metrics exposure in Prometheus format
- Health check endpoints (`/health`, `/ready`)
- Request ID propagation across service boundaries

### IV. Cloud Native Standards
Services must:
- Run in Docker containers (Alpine-based for size optimization)
- Follow 12-factor app principles
- Use Kubernetes for orchestration
- Store configuration in environment variables
- Be stateless and horizontally scalable

### V. Security Requirements
- All external communications must use TLS 1.3+
- Secrets managed via HashiCorp Vault or Kubernetes Secrets
- No credentials in code, config files, or container images
- Regular dependency scanning (weekly) using `safety` and `snyk`
- Input validation on all API endpoints
- Rate limiting on public endpoints

### VI. Code Quality Standards
- Type hints required for all functions (use `mypy` for static checking)
- Code formatted with `black` (line length: 100)
- Import sorting with `isort`
- Linting with `ruff` (or `pylint` + `flake8`)
- Pre-commit hooks enforced for all the above

### VII. Dependency Management
- Use `Poetry` or `uv` for dependency management
- Pin all dependencies to specific versions
- Monthly dependency updates
- Security patches applied within 72 hours of disclosure

## Development Workflow

### Branching Strategy
- Main branch protected, requires PR
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Hotfixes: `hotfix/description`

### Code Review Process
- Minimum 2 approvers required
- Architecture review for new services or major changes
- Security review for authentication/authorization changes
- Performance review for database-heavy features

### Testing Requirements
- Unit tests: pytest with fixtures
- Integration tests: testcontainers for dependencies
- Contract tests: Pact for service-to-service
- Load tests: Locust for performance validation

### CI/CD Pipeline
- Automated testing on every PR
- Automated security scanning (SAST, dependency check)
- Automated Docker image building and scanning
- Blue-green deployments for zero downtime
- Automated rollback on health check failures

## Technology Stack

### Required
- **Language**: Python 3.11+
- **Framework**: FastAPI or Flask
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL (primary), Redis (cache/queue)
- **Message Queue**: RabbitMQ or Apache Kafka
- **Observability**: OpenTelemetry + Prometheus + Grafana

### Recommended
- **Testing**: pytest, pytest-asyncio, httpx (for async tests)
- **Validation**: Pydantic for data validation
- **Documentation**: Swagger UI (auto-generated from OpenAPI)

## Governance

This constitution supersedes all other development practices for Python microservices. Amendments require approval from:
- Tech Lead
- Architecture Review Board
- Security Team representative

All amendments must be documented with:
- Rationale for change
- Impact assessment
- Migration plan for existing services

**Version**: 1.0.0 | **Ratified**: 2025-01-15 | **Last Amended**: 2025-01-15
```

### react-frontend.md

```markdown
# React Frontend Constitution

## Core Principles

### I. Component-First Development
- Build reusable, self-contained components
- Follow atomic design principles (atoms, molecules, organisms)
- Components must be documented with Storybook
- Prop types required (TypeScript interfaces)

### II. Type Safety (NON-NEGOTIABLE)
- TypeScript strict mode enabled
- No `any` types allowed (use `unknown` if necessary)
- All props, state, and API responses must be typed
- Type definitions in separate `.types.ts` files

### III. Testing Strategy
- Unit tests for business logic (>= 80% coverage)
- Component tests using React Testing Library
- E2E tests for critical user flows (Playwright)
- Visual regression tests for UI components (Chromatic)

### IV. Performance Standards
- Lighthouse score >= 90 (all categories)
- Time to Interactive (TTI) < 3.5s on 4G
- First Contentful Paint (FCP) < 1.8s
- Cumulative Layout Shift (CLS) < 0.1
- Lazy loading for routes and heavy components
- Code splitting at route level minimum

### V. Accessibility (NON-NEGOTIABLE)
- WCAG 2.1 Level AA compliance required
- Semantic HTML elements
- Proper ARIA labels where needed
- Keyboard navigation support
- Screen reader tested
- Color contrast ratios compliant

### VI. State Management
- Use React Context for simple, localized state
- Use Zustand or Redux Toolkit for complex global state
- Server state managed by TanStack Query (React Query)
- Form state with React Hook Form
- URL as source of truth for navigation state

### VII. Code Quality
- ESLint with Airbnb or Standard config
- Prettier for formatting (single quotes, semicolons)
- Husky for pre-commit hooks
- No console.log statements in production code
- Custom hooks for shared logic

## Development Workflow

### Project Structure
```
src/
├── components/      # Reusable UI components
├── features/        # Feature-specific modules
├── hooks/          # Custom React hooks
├── pages/          # Route components
├── services/       # API clients
├── store/          # Global state
├── types/          # TypeScript types
├── utils/          # Utility functions
└── styles/         # Global styles
```

### Component Guidelines
- One component per file
- Use functional components with hooks
- Extract custom hooks for complex logic
- Props destructured in function signature
- Default exports for components

### Styling Approach
- Tailwind CSS for utility-first styling
- CSS Modules for component-specific styles
- styled-components for dynamic styling needs
- No inline styles except for dynamic values

### API Integration
- Centralize API calls in service modules
- Use TanStack Query for data fetching
- Implement request/response interceptors
- Handle loading, error, and success states
- Optimistic updates where appropriate

### Code Review Process
- Minimum 1 reviewer (2 for major changes)
- UI/UX review for new components
- Accessibility review for interactive elements
- Performance review for data-heavy features

### CI/CD Pipeline
- Type checking with TypeScript
- Linting with ESLint
- Unit and component tests
- Build verification
- Deploy preview for every PR
- Automated deployment to staging

## Technology Stack

### Required
- **Framework**: React 18+
- **Language**: TypeScript 5+
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State**: Zustand + TanStack Query
- **Routing**: React Router v6
- **Forms**: React Hook Form + Zod
- **Testing**: Vitest + React Testing Library + Playwright

### Recommended
- **UI Library**: shadcn/ui or Radix UI
- **Icons**: Lucide React or Heroicons
- **Date Handling**: date-fns
- **HTTP Client**: ky or axios

## Governance

This constitution applies to all React-based frontends. Amendments require approval from:
- Frontend Tech Lead
- UX Lead
- Accessibility Champion

All amendments must include:
- Rationale and benefits
- Migration guide for existing code
- Update to component library if needed

**Version**: 1.2.0 | **Ratified**: 2024-09-01 | **Last Amended**: 2025-01-20
```

## Using These Constitutions

1. Create a GitHub repository (public or private)
2. Add your constitution markdown files
3. Team members can list them:
   ```bash
   specify list-constitutions myorg/constitutions-repo
   ```

4. Initialize projects with a constitution:
   ```bash
   specify init my-app --constitution-repo myorg/constitutions-repo --constitution-name react-frontend
   ```

5. Or select interactively:
   ```bash
   specify init my-app --constitution-repo myorg/constitutions-repo --constitution-interactive
   ```

## Best Practices for Constitution Repositories

1. **Keep constitutions focused**: Each should target a specific use case or tech stack
2. **Version your constitutions**: Include version numbers and dates
3. **Document rationale**: Explain *why* rules exist, not just *what* they are
4. **Make them actionable**: Include specific tools, commands, and examples
5. **Review regularly**: Update constitutions as practices evolve
6. **Collect feedback**: Encourage teams to suggest improvements
7. **Maintain a changelog**: Track what changed and why
8. **Add a README**: Explain the purpose and usage of each constitution

## Example README.md for Constitution Repository

```markdown
# Engineering Constitutions

This repository contains standardized project constitutions for [Your Company Name].

## Available Constitutions

| Constitution | Use Case | Last Updated |
|--------------|----------|--------------|
| `python-microservices.md` | Backend microservices in Python | 2025-01-15 |
| `golang-api.md` | High-performance APIs in Go | 2025-01-10 |
| `react-frontend.md` | Web frontends using React | 2025-01-20 |
| `nodejs-backend.md` | Node.js backend services | 2025-01-12 |
| `data-pipeline.md` | ETL and data processing pipelines | 2024-12-20 |
| `mobile-app.md` | React Native mobile apps | 2025-01-05 |

## Usage

### List Available Constitutions

```bash
specify list-constitutions yourorg/engineering-constitutions
```

### Initialize New Project with Constitution

```bash
specify init my-new-service \
  --constitution-repo yourorg/engineering-constitutions \
  --constitution-name python-microservices
```

### Interactive Selection

```bash
specify init my-new-service \
  --constitution-repo yourorg/engineering-constitutions \
  --constitution-interactive
```

## Contributing

To propose changes to a constitution:

1. Create a new branch
2. Update the relevant constitution file
3. Include rationale in commit message
4. Open a PR with:
   - What changed
   - Why it changed
   - Impact on existing projects
   - Migration guidance if needed

## Approval Process

Constitution changes require approval from:
- Tech Lead of relevant domain
- Architecture Review Board representative
- At least 2 engineers who use that constitution

## Questions?

Contact the Architecture Team at #architecture-help
```

## Additional Resources

- [Remote Constitutions Guide](../docs/remote-constitutions.md)
- [spec-kit Documentation](../README.md)
