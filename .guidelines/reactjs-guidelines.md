# ReactJS Corporate Guidelines

**Tech Stack**: React, TypeScript, Frontend Web Applications

**Auto-detected from**: `package.json` with `"react"` dependency

## Scaffolding

**MUST** use corporate scaffolding:

```bash
npx @YOUR_ORG/create-react-app <app-name> --template typescript
```

**DO NOT** use public scaffolding:

- `create-react-app`
- `vite`

## Package Registry

Configure `.npmrc`:

```text
registry=https://artifactory.YOUR_DOMAIN.com/artifactory/api/npm/npm-virtual/
@YOUR_ORG:registry=https://artifactory.YOUR_DOMAIN.com/artifactory/api/npm/npm-local/
```

## Mandatory Libraries

### UI Components

**MUST** use corporate component library:

```bash
npm install @YOUR_ORG/ui-components@latest
```

```typescript
import { Button, Modal, DataTable } from '@YOUR_ORG/ui-components';
```

### Authentication

**MUST** use corporate identity client:

```bash
npm install @YOUR_ORG/idm-client@latest
```

```typescript
import { AuthProvider, useAuth, ProtectedRoute } from '@YOUR_ORG/idm-client';

// Wrap app
<AuthProvider clientId={process.env.REACT_APP_CLIENT_ID}>
  <ProtectedRoute path="/dashboard" component={Dashboard} />
</AuthProvider>
```

### API Client

**MUST** use corporate API client:

```bash
npm install @YOUR_ORG/api-client@latest
```

```typescript
import { useQuery, useMutation } from '@YOUR_ORG/api-client';

const { data, loading } = useQuery('/api/users');
const { mutate } = useMutation('/api/users', 'POST');
```

### Logging

**MUST** use corporate logger:

```bash
npm install @YOUR_ORG/logger@latest
```

```typescript
import { logger } from '@YOUR_ORG/logger';

logger.info('User action', { userId: user.id });
logger.error('Error occurred', { error });
```

## Banned Libraries

**DO NOT USE**:

- Material-UI, Ant Design, Chakra UI → use `@YOUR_ORG/ui-components`
- auth0-react, DIY JWT → use `@YOUR_ORG/idm-client`
- Direct fetch without interceptors → use `@YOUR_ORG/api-client`

## Architecture

**Structure** (feature-based for large apps):

```text
src/
├── features/
│   ├── authentication/
│   ├── dashboard/
│   └── users/
├── shared/
│   ├── components/
│   └── hooks/
└── App.tsx
```

**Structure** (layer-based for small apps):

```text
src/
├── components/
├── hooks/
├── services/
└── App.tsx
```

**MUST** use code splitting for routes:

```typescript
const Dashboard = lazy(() => import('./features/dashboard'));
```

**MUST** centralize API calls in services:

```typescript
// services/userService.ts
export const userService = {
  getUsers: () => apiClient.get('/api/users'),
  createUser: (data) => apiClient.post('/api/users', data),
};
```

## Security

**Environment variables** - prefix with `REACT_APP_`:

```bash
REACT_APP_API_URL=https://api.example.com
REACT_APP_CLIENT_ID=abc123
```

**NEVER** hardcode secrets. Use `.env` files, not committed to git.

**XSS prevention** - sanitize user input:

```bash
npm install dompurify
```

**HTTPS only** in production. All API URLs must use HTTPS.

**Route protection**:

```typescript
<ProtectedRoute path="/admin" element={<Admin />} roles={['admin']} />
```

## Coding Standards

**MUST** use TypeScript with strict mode:

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true
  }
}
```

**Prefer** functional components with hooks:

```typescript
export function UserProfile({ userId }: UserProfileProps) {
  const [user, setUser] = useState<User | null>(null);
  return <div>{user?.name}</div>;
}
```

**Naming**:

- Components: PascalCase (`UserProfile.tsx`)
- Hooks: camelCase with `use` prefix (`useAuth.ts`)
- Constants: UPPER_SNAKE_CASE (`API_BASE_URL`)

**Testing** - MUST test critical flows:

```typescript
import { render, screen } from '@testing-library/react';

test('should render component', () => {
  render(<LoginForm />);
  expect(screen.getByRole('button')).toBeInTheDocument();
});
```

## Build & Deployment

**Production build**:

```bash
npm run build
```

**Docker** (multi-stage):

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
```

## Performance

**MUST** meet:

- Initial load < 3 seconds (LCP)
- Time to interactive < 5 seconds (TTI)
- Bundle size < 500KB gzipped

**Optimize re-renders**:

```typescript
const sortedUsers = useMemo(() => users.sort(...), [users]);
const handleClick = useCallback(() => {...}, []);
```

## Accessibility

**MUST** meet WCAG 2.1 Level AA. Use corporate component library for built-in accessibility.
