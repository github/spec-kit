# ReactJS Corporate Guidelines

**Tech Stack**: React, TypeScript, Frontend Web Applications

**Auto-detected from**: `package.json` with `"react"` dependency

## 1. Scaffolding

### Creating New React Applications

**Corporate Command**:

```bash
npx @YOUR_ORG/create-react-app <app-name> --template typescript
```

**Example**:

```bash
npx @acmecorp/create-react-app my-dashboard --template typescript
```

**Options**:

- `--template typescript` - TypeScript template (recommended)
- `--template javascript` - JavaScript template
- `--enterprise` - Include corporate configuration pre-configured

**DO NOT USE**:

```bash
# ❌ Public scaffolding - bypasses corporate configuration
npx create-react-app my-app
npx vite my-app
```

### Creating New Components

**Corporate Component Generator** (if available):

```bash
npx @YOUR_ORG/generate-component <ComponentName>
```

**Generates**:

- `ComponentName.tsx` - Component implementation
- `ComponentName.test.tsx` - Unit tests
- `ComponentName.stories.tsx` - Storybook stories
- `index.ts` - Barrel export

## 2. Package Registry

### Configuration

**File**: `package.json` or `.npmrc`

**Registry URL**: `https://artifactory.YOUR_DOMAIN.com/artifactory/api/npm/npm-virtual/`

**Setup** (`.npmrc` in project root):

```text
registry=https://artifactory.acmecorp.com/artifactory/api/npm/npm-virtual/
@acmecorp:registry=https://artifactory.acmecorp.com/artifactory/api/npm/npm-local/
//artifactory.acmecorp.com/artifactory/api/npm/:_auth=${NPM_AUTH_TOKEN}
```

**Authentication**:

1. Obtain token from Artifactory (User Profile → API Key)
2. Set environment variable: `export NPM_AUTH_TOKEN=<your-token>`
3. Or use `.npmrc` in home directory with credentials

**Verification**:

```bash
npm config get registry
# Should show: https://artifactory.acmecorp.com/...
```

## 3. Mandatory Libraries

### UI Component Library

**MUST USE**: Corporate component library

**Package**:

```bash
npm install @YOUR_ORG/ui-components@latest
```

**Example**:

```bash
npm install @acmecorp/ui-components@^2.0.0
```

**Usage**:

```typescript
import { Button, Modal, DataTable, Form, Input } from '@acmecorp/ui-components';

function MyComponent() {
  return (
    <Form onSubmit={handleSubmit}>
      <Input label="Username" name="username" required />
      <Button type="submit" variant="primary">
        Submit
      </Button>
    </Form>
  );
}
```

**Documentation**: `https://ui-docs.YOUR_DOMAIN.com` or internal component library docs

**Why**: Ensures consistent branding, accessibility compliance, and reduces maintenance burden.

### Identity & Authentication

**MUST USE**: Corporate identity management client

**Package**:

```bash
npm install @YOUR_ORG/idm-client@latest
```

**Example**:

```bash
npm install @acmecorp/idm-client@^3.0.0
```

**Usage**:

```typescript
import { AuthProvider, useAuth, ProtectedRoute } from '@acmecorp/idm-client';

// App.tsx
function App() {
  return (
    <AuthProvider clientId={process.env.REACT_APP_CLIENT_ID}>
      <Router>
        <Route path="/login" component={LoginPage} />
        <ProtectedRoute path="/dashboard" component={Dashboard} />
      </Router>
    </AuthProvider>
  );
}

// Component using auth
function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

**Features**:

- SSO integration
- OAuth2/OIDC flows
- Token management (automatic refresh)
- Role-based access control (RBAC)

**Why**: Centralized authentication ensures audit logging, compliance, and security policy enforcement.

### API Client

**MUST USE**: Corporate API client SDK

**Package**:

```bash
npm install @YOUR_ORG/api-client@latest
```

**Example**:

```bash
npm install @acmecorp/api-client@^1.5.0
```

**Usage**:

```typescript
import { ApiClient, useQuery, useMutation } from '@acmecorp/api-client';

// Initialize client
const client = new ApiClient({
  baseURL: process.env.REACT_APP_API_URL,
  auth: true, // Automatic token injection
});

// Using React hooks
function UserList() {
  const { data, loading, error } = useQuery('/api/users');

  if (loading) return <Spinner />;
  if (error) return <Error message={error.message} />;

  return (
    <DataTable data={data.users} columns={columns} />
  );
}

// Mutations
function CreateUser() {
  const { mutate, loading } = useMutation('/api/users', 'POST');

  const handleSubmit = async (formData) => {
    await mutate(formData);
  };

  return <UserForm onSubmit={handleSubmit} loading={loading} />;
}
```

**Features**:

- Automatic authentication header injection
- Request/response interceptors
- Error handling with retry logic
- Rate limiting and caching
- Type-safe API calls (TypeScript)

**Why**: Ensures consistent error handling, monitoring, and compliance with corporate API standards.

### State Management

**RECOMMENDED**: Use corporate-approved state management library

**Options**:

```bash
# Option 1: Redux Toolkit (for complex apps)
npm install @reduxjs/toolkit react-redux

# Option 2: Zustand (for simpler apps)
npm install zustand

# Option 3: React Query + Context (for API-driven apps)
npm install @tanstack/react-query
```

**Corporate Preference**: Check with your team lead or architecture documentation.

**Why**: Standardizes state management patterns across teams.

### HTTP Client (If Not Using API Client)

**If `@YOUR_ORG/api-client` doesn't meet needs**:

**Allowed**:

```bash
npm install axios
# or
npm install @tanstack/react-query
```

**Configuration**:

```typescript
import axios from 'axios';
import { getAuthToken } from '@acmecorp/idm-client';

const http = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
});

// Automatic token injection
http.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Forms

**RECOMMENDED**: React Hook Form + Zod validation

```bash
npm install react-hook-form zod @hookform/resolvers
```

**Usage**:

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Input, Button } from '@acmecorp/ui-components';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input {...register('email')} error={errors.email?.message} />
      <Input {...register('password')} type="password" error={errors.password?.message} />
      <Button type="submit">Login</Button>
    </form>
  );
}
```

### Logging & Monitoring

**MUST USE**: Corporate logging client

**Package**:

```bash
npm install @YOUR_ORG/logger@latest
```

**Example**:

```bash
npm install @acmecorp/logger@^1.2.0
```

**Usage**:

```typescript
import { logger } from '@acmecorp/logger';

// Automatic context injection (user, session, etc.)
logger.info('User logged in', { userId: user.id });
logger.error('API request failed', { endpoint: '/api/users', error });
logger.debug('Component rendered', { component: 'Dashboard' });

// Error boundaries
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    logger.error('React error boundary caught error', { error, errorInfo });
  }
}
```

**Features**:

- Centralized log aggregation
- Automatic user context
- Error tracking integration
- Performance monitoring

**Why**: Enables debugging, monitoring, and incident response.

## 4. Banned Libraries

**DO NOT USE** the following public packages. Use corporate alternatives instead:

### UI Libraries

❌ **BANNED**:

- `material-ui` / `@mui/material`
- `ant-design`
- `chakra-ui`
- `bootstrap` / `react-bootstrap`
- `semantic-ui-react`

✅ **USE INSTEAD**: `@YOUR_ORG/ui-components`

**Why**: Corporate UI library ensures brand consistency, accessibility compliance, and centralized updates.

### Authentication Libraries

❌ **BANNED**:

- `auth0-react`
- `react-oauth2-pkce`
- `passport` (in frontend)
- DIY JWT handling

✅ **USE INSTEAD**: `@YOUR_ORG/idm-client`

**Why**: Security policy requires centralized authentication with audit logging.

### HTTP Clients

❌ **RESTRICTED** (require justification):

- `fetch` API directly (no interceptors)
- `superagent`
- `request` (deprecated)

✅ **PREFER**: `@YOUR_ORG/api-client` or `axios` with corporate interceptors

**Why**: Ensures consistent error handling, token management, and monitoring.

## 5. Architecture Patterns

### Preferred Architecture

**Option 1: Feature-based** (Recommended for large apps)

```text
src/
├── features/
│   ├── authentication/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── index.ts
│   ├── dashboard/
│   └── users/
├── shared/
│   ├── components/
│   ├── hooks/
│   └── utils/
└── App.tsx
```

**Option 2: Layer-based** (Simpler for small apps)

```text
src/
├── components/
│   ├── common/
│   ├── dashboard/
│   └── users/
├── hooks/
├── services/
├── utils/
└── App.tsx
```

### Code Splitting

**MUST** use code splitting for routes:

```typescript
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./features/dashboard'));
const Users = lazy(() => import('./features/users'));

function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/users" element={<Users />} />
      </Routes>
    </Suspense>
  );
}
```

### API Integration Pattern

**MUST** centralize API calls in services:

```typescript
// services/userService.ts
import { apiClient } from '@acmecorp/api-client';

export const userService = {
  getUsers: () => apiClient.get('/api/users'),
  getUser: (id: string) => apiClient.get(`/api/users/${id}`),
  createUser: (data: CreateUserDTO) => apiClient.post('/api/users', data),
  updateUser: (id: string, data: UpdateUserDTO) => apiClient.put(`/api/users/${id}`, data),
  deleteUser: (id: string) => apiClient.delete(`/api/users/${id}`),
};

// components/UserList.tsx
import { userService } from '../services/userService';

function UserList() {
  const { data, loading } = useQuery('users', userService.getUsers);
  // ...
}
```

**Why**: Enables mocking, testing, and changing API implementations without touching components.

## 6. Security & Compliance

### Environment Variables

**MUST** prefix all environment variables with `REACT_APP_`:

```bash
# .env
REACT_APP_API_URL=https://api.acmecorp.com
REACT_APP_CLIENT_ID=abc123
REACT_APP_ENV=production
```

**DO NOT** commit `.env` files. Use `.env.example` for documentation:

```bash
# .env.example
REACT_APP_API_URL=
REACT_APP_CLIENT_ID=
```

### Secrets Management

**NEVER** hardcode secrets in code:

```typescript
// ❌ NEVER DO THIS
const apiKey = 'sk-12345-abcdef';

// ✅ DO THIS
const apiKey = process.env.REACT_APP_API_KEY;
```

**For sensitive configuration**, use corporate secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault) accessed via backend API.

### Content Security Policy (CSP)

**MUST** configure CSP headers in production. Work with DevOps team.

**Example** (`public/index.html`):

```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self';
               script-src 'self';
               style-src 'self' 'unsafe-inline';
               img-src 'self' data: https:;
               connect-src 'self' https://api.acmecorp.com;">
```

### XSS Prevention

**ALWAYS** sanitize user input before rendering:

```bash
npm install dompurify
npm install @types/dompurify --save-dev
```

```typescript
import DOMPurify from 'dompurify';

function UserContent({ html }: { html: string }) {
  const sanitized = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}
```

### Authentication Guards

**MUST** protect routes requiring authentication:

```typescript
import { ProtectedRoute } from '@acmecorp/idm-client';

<Routes>
  <Route path="/public" element={<PublicPage />} />
  <ProtectedRoute path="/dashboard" element={<Dashboard />} roles={['user']} />
  <ProtectedRoute path="/admin" element={<AdminPanel />} roles={['admin']} />
</Routes>
```

### HTTPS Only

**MUST** use HTTPS in production. All API calls must use HTTPS URLs.

```typescript
// ✅ Correct
const API_URL = 'https://api.acmecorp.com';

// ❌ Never use HTTP in production
const API_URL = 'http://api.acmecorp.com';
```

## 7. Coding Standards

### TypeScript

**MUST** use TypeScript for all new projects:

```bash
npx @YOUR_ORG/create-react-app my-app --template typescript
```

**tsconfig.json** (strict mode):

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "esModuleInterop": true,
    "jsx": "react-jsx"
  }
}
```

### Component Structure

**Prefer functional components with hooks**:

```typescript
// ✅ Functional component
import { useState, useEffect } from 'react';

interface UserProfileProps {
  userId: string;
}

export function UserProfile({ userId }: UserProfileProps) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);

  return <div>{user?.name}</div>;
}

// ❌ Avoid class components (unless required for error boundaries)
class UserProfile extends React.Component { ... }
```

### Naming Conventions

**Components**: PascalCase

```typescript
UserProfile.tsx
DashboardCard.tsx
```

**Hooks**: camelCase with `use` prefix

```typescript
useAuth.ts
useFetchUsers.ts
```

**Utilities**: camelCase

```typescript
formatDate.ts
validateEmail.ts
```

**Constants**: UPPER_SNAKE_CASE

```typescript
const API_BASE_URL = 'https://api.acmecorp.com';
const MAX_RETRIES = 3;
```

### File Organization

**One component per file**:

```text
✅ Good:
src/components/UserProfile.tsx
src/components/Dashboard.tsx

❌ Bad:
src/components/index.tsx (contains 10 components)
```

**Barrel exports** for clean imports:

```typescript
// src/components/index.ts
export { UserProfile } from './UserProfile';
export { Dashboard } from './Dashboard';

// Usage
import { UserProfile, Dashboard } from '@/components';
```

### Props Destructuring

**Prefer destructuring**:

```typescript
// ✅ Good
function Button({ onClick, children, variant = 'primary' }: ButtonProps) {
  return <button onClick={onClick} className={variant}>{children}</button>;
}

// ❌ Less clear
function Button(props: ButtonProps) {
  return <button onClick={props.onClick}>{props.children}</button>;
}
```

### Custom Hooks

**Extract reusable logic into custom hooks**:

```typescript
// hooks/useFetchUser.ts
export function useFetchUser(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetchUser(userId)
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [userId]);

  return { user, loading, error };
}

// Usage
function UserProfile({ userId }: { userId: string }) {
  const { user, loading, error } = useFetchUser(userId);
  // ...
}
```

### Error Handling

**MUST** handle errors in components:

```typescript
function UserList() {
  const { data, loading, error } = useQuery('users', userService.getUsers);

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return <Empty message="No users found" />;

  return <DataTable data={data} />;
}
```

**Use error boundaries for uncaught errors**:

```typescript
import { ErrorBoundary } from '@acmecorp/ui-components';

function App() {
  return (
    <ErrorBoundary fallback={<ErrorPage />}>
      <Routes />
    </ErrorBoundary>
  );
}
```

### Testing

**MUST** write tests for:

- Critical user flows (authentication, checkout, etc.)
- Complex business logic
- Reusable components in shared library

**Test structure**:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('should submit form with valid credentials', async () => {
    const onSubmit = jest.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({ email: 'user@example.com', password: 'password123' });
    });
  });
});
```

### Performance

**MUST** optimize re-renders:

```typescript
import { memo, useMemo, useCallback } from 'react';

// Memoize expensive computations
function UserList({ users }: { users: User[] }) {
  const sortedUsers = useMemo(() => {
    return users.sort((a, b) => a.name.localeCompare(b.name));
  }, [users]);

  return <DataTable data={sortedUsers} />;
}

// Memoize callbacks
function Parent() {
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);

  return <Child onClick={handleClick} />;
}

// Memoize components
export const UserCard = memo(function UserCard({ user }: { user: User }) {
  return <div>{user.name}</div>;
});
```

## 8. Build & Deployment

### Build Configuration

**Production build**:

```bash
npm run build
```

**Ensure build optimizations are enabled**:

- Tree shaking
- Minification
- Code splitting
- Image optimization

### Environment-Specific Builds

**Use `.env` files per environment**:

```text
.env.local           # Local development
.env.development     # Dev environment
.env.staging         # Staging environment
.env.production      # Production environment
```

**Build for specific environment**:

```bash
REACT_APP_ENV=staging npm run build
```

### Docker

**Dockerfile** (multi-stage build):

```dockerfile
# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### CI/CD

**Corporate pipeline integration**: Work with DevOps team to set up CI/CD.

**Typical pipeline**:

1. Install dependencies: `npm ci`
2. Lint: `npm run lint`
3. Test: `npm test`
4. Build: `npm run build`
5. Deploy to environment

## 9. Performance Requirements

**MUST meet**:

- Initial page load: < 3 seconds (LCP)
- Time to interactive: < 5 seconds (TTI)
- Bundle size: < 500KB gzipped (excluding vendor chunks)

**Use tools**:

- Lighthouse CI in pipeline
- Bundle analyzer: `npm run build -- --stats && npx webpack-bundle-analyzer build/bundle-stats.json`

## 10. Accessibility

**MUST meet WCAG 2.1 Level AA**:

- Semantic HTML
- ARIA labels where needed
- Keyboard navigation
- Screen reader testing

**Use corporate component library** - accessibility built-in.

**Testing**:

```bash
npm install --save-dev @axe-core/react
```

```typescript
// src/index.tsx (development only)
if (process.env.NODE_ENV !== 'production') {
  import('@axe-core/react').then((axe) => {
    axe.default(React, ReactDOM, 1000);
  });
}
```

## See Also

- `README.md` - Guidelines overview
- `branching-guidelines.md` - Branch naming conventions
- Internal developer portal for corporate library documentation
- Architecture team for exceptions and clarifications
