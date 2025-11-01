# API Contracts Reference

API specifications from implementation plans.

## What Are API Contracts?

When you create an implementation plan (`/plan`), it typically includes API endpoint specifications. These become the contract between frontend and backend, or between services.

## Typical Locations

API contracts are documented in:
- `specs/[feature-id]/plan.md` - Main implementation plan
- `specs/[feature-id]/contracts/api-spec.json` - OpenAPI/Swagger spec (if generated)
- `specs/[feature-id]/contracts/graphql-schema.graphql` - GraphQL schema (if applicable)

## REST API Documentation

Implementation plans typically include:

```markdown
### API Endpoints

#### POST /api/auth/login
**Description**: Authenticate user with email/password

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "token": "jwt-token-here",
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

**Errors**:
- 401 Unauthorized: Invalid credentials
- 422 Unprocessable Entity: Validation errors
```

## GraphQL Schema

For GraphQL APIs, implementation plans include:

```graphql
type User {
  id: ID!
  email: String!
  name: String!
  createdAt: DateTime!
}

type Query {
  me: User
  user(id: ID!): User
}

type Mutation {
  login(email: String!, password: String!): AuthPayload!
  register(input: RegisterInput!): AuthPayload!
}

type AuthPayload {
  token: String!
  user: User!
}
```

## Data Models

Implementation plans also document data structures:

```markdown
### User Model

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Unique identifier |
| email | String | Yes | User email (unique) |
| password_hash | String | Yes | Bcrypt hashed password |
| name | String | Yes | Display name |
| created_at | DateTime | Yes | Account creation timestamp |
| updated_at | DateTime | Yes | Last update timestamp |
```

## Validation Rules

```markdown
### Validation

- Email: Must be valid email format, max 255 chars
- Password: Min 8 chars, must contain uppercase, lowercase, number
- Name: 1-100 characters
```

## Error Responses

```markdown
### Standard Error Format

All errors follow this structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input provided",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address"
      }
    ]
  }
}
```
```

## Finding API Contracts

1. Look in `specs/[feature-id]/plan.md`
2. Check `specs/[feature-id]/contracts/` directory
3. Review data models section of plan
4. Check implementation for actual API code

## Best Practices

- Document all endpoints in implementation plan
- Include request/response examples
- Document error codes and messages
- Specify validation rules
- Note authentication/authorization requirements
- Version your APIs (v1, v2, etc.)

## Related

- [Concepts: Phase Planning](../concepts/phase-planning.md) - How plans are created
- [Templates](./templates.md) - Plan template structure
- [Guides](../guides/) - API development workflows
