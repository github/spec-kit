# ReactJS Corporate Guidelines

**Tech Stack**: React, TypeScript, Frontend Web Applications
**Auto-detected from**: `package.json` with `"react"` dependency
**Version**: 1.0

---

## Scaffolding

**MUST**:

- Use corporate scaffolding command (`@YOUR_ORG/create-react-app`)
- Use TypeScript template for all new projects

**NEVER**:

- Use public `create-react-app` or `vite` directly

**Rationale**: Corporate scaffolding includes security, logging, auth, monitoring from day one

---

## Package Registry

**MUST**:

- Configure `.npmrc` with corporate npm registry (Artifactory/Nexus)
- All dependencies resolved through corporate registry only

**NEVER**:

- Install packages from public npmjs.org directly

---

## Mandatory Libraries

### UI Components

**MUST** use: `@YOUR_ORG/ui-components` package
**Includes**: Buttons, Modals, DataTables, Forms with built-in accessibility (WCAG 2.1 AA)
**Benefits**: Consistent design, built-in security, accessibility compliance

### Authentication

**MUST** use: `@YOUR_ORG/idm-client` package
**Requirements**:

- Wrap app with `<AuthProvider>` at root level
- Use `<ProtectedRoute>` for authenticated pages
- Access user context via `useAuth()` hook
- Pass authentication token to all API calls

### API Client

**MUST** use: `@YOUR_ORG/api-client` package
**Requirements**:

- Use `useQuery()` hook for GET requests
- Use `useMutation()` hook for POST/PUT/DELETE
- Never use raw `fetch()` or `axios` directly

**Features**: Automatic token injection, retry logic, error handling, request/response interceptors

### Logging

**MUST** use: `@YOUR_ORG/logger` package
**Requirements**:

- Log user actions for audit trail
- Include correlation ID in all logs
- Never log sensitive data (passwords, tokens, PII)

---

## Banned Libraries

**NEVER** use:

- Material-UI, Ant Design, Chakra UI → Use `@YOUR_ORG/ui-components`
- auth0-react, DIY JWT handling → Use `@YOUR_ORG/idm-client`
- Direct `fetch()` without interceptors → Use `@YOUR_ORG/api-client`

**Rationale**: Corporate libraries enforce security, accessibility, compliance

---

## Architecture

### Project Structure

**MUST** choose based on app size:

- **Feature-based** (large apps): Group by feature (authentication/, dashboard/, users/)
- **Layer-based** (small apps): Group by type (components/, hooks/, services/)

**MUST** have:

- `shared/` directory for reusable components and hooks
- Separate directories for components, hooks, services

### Code Splitting

**MUST**:

- Use lazy loading for routes (`React.lazy()`)
- Split large features into separate bundles
- Target bundle size < 500KB gzipped

### Service Layer

**MUST**:

- Centralize all API calls in service files
- Never call API client directly from components
- Export service objects with typed methods

---

## Security

### Environment Variables

**MUST**:

- Prefix all env vars with `REACT_APP_` or `VITE_`
- Store secrets in `.env` files (never commit to git)
- Use corporate secrets manager for production

**NEVER**:

- Hardcode API keys or secrets in code

### XSS Prevention

**MUST**:

- Sanitize user-generated HTML before rendering
- Use `dompurify` library for sanitization
- Validate all user inputs

### HTTPS Only

**MUST**:

- Use HTTPS in production environments
- All API URLs must use HTTPS protocol

### Route Protection

**MUST**:

- Wrap protected routes with `<ProtectedRoute>` component
- Specify required roles for role-based access
- Redirect unauthorized users to login page

---

## Coding Standards

### TypeScript

**MUST**:

- Use TypeScript for all new code
- Enable strict mode in `tsconfig.json`
- Define types for all props, state, API responses

**NEVER**:

- Use `any` type (use `unknown` if type is truly unknown)

### Components

**MUST**:

- Use functional components with hooks (no class components)
- Define prop types with TypeScript interfaces
- Export components as named exports

### Naming Conventions

**MUST** follow:

- Components: `PascalCase` (UserProfile.tsx)
- Hooks: `camelCase` with `use` prefix (useAuth.ts)
- Constants: `UPPER_SNAKE_CASE` (API_BASE_URL)
- Files: Match component name (UserProfile.tsx for UserProfile component)

### Testing

**MUST**:

- Write tests for critical user flows (authentication, checkout, etc.)
- Use React Testing Library (not Enzyme)
- Aim for 80%+ coverage on critical paths

---

## Performance

### Requirements

**MUST** meet:

- Initial load (LCP) < 3 seconds
- Time to interactive (TTI) < 5 seconds
- Bundle size < 500KB gzipped

### Optimization

**SHOULD**:

- Use `useMemo()` for expensive computations
- Use `useCallback()` for stable function references
- Avoid unnecessary re-renders (React DevTools Profiler)
- Lazy load images and routes

---

## Accessibility

**MUST**:

- Meet WCAG 2.1 Level AA compliance
- Use semantic HTML elements
- Provide alt text for images
- Support keyboard navigation

**Note**: Corporate UI components library includes accessibility by default

---

## Build & Deployment

### Build Process

**MUST**:

- Use `npm run build` for production builds
- Run tests before deployment (`npm test`)
- Verify bundle size meets requirements

### Docker

**MUST**:

- Use multi-stage builds (build stage + nginx runtime)
- Use official Node.js and nginx base images
- Copy only build artifacts to runtime image
- Serve via nginx or similar web server

**SHOULD**:

- Use layer caching for faster builds
- Keep final image small (< 100MB)

---

## Non-Compliance

If corporate library unavailable or causes blocking issue:

1. Document violation in `.guidelines-todo.md` with justification
2. Create ticket to resolve (target: next sprint)
3. Proceed with alternative, mark with `// TODO: GUIDELINE-VIOLATION` comment for tracking
