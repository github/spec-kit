# Authentication Specification

## Overview
This specification defines the authentication and authorization requirements for the Printing Services Marketplace platform.

## User Registration

### Customer Registration
```gherkin
Given a new user wants to register as a customer
When they provide valid email, password, firstName, and lastName
Then the system creates a user with role CUSTOMER
And status PENDING
And sends email verification
And returns success message without sensitive data
```

### Broker Registration
```gherkin
Given a new user wants to register as a broker
When they provide valid email, password, firstName, lastName, and companyName
Then the system creates a user with role BROKER
And status PENDING
And sends email verification
And requires business verification documents
And returns success message without sensitive data
```

### Registration Validation
```gherkin
Given a registration request
When the email already exists
Then the system returns "Email already registered" error
And does not create duplicate user

Given a registration request
When the password is less than 8 characters
Then the system returns "Password too weak" error
And does not create user

Given a broker registration
When companyName is missing
Then the system returns "Company name required for brokers" error
And does not create user
```

## User Login

### Successful Login
```gherkin
Given a verified user with email "customer@example.com"
When they provide correct email and password
Then the system validates credentials
And generates JWT token with 7-day expiry
And returns user data (excluding password)
And sets secure httpOnly cookie
```

### Failed Login Attempts
```gherkin
Given a login attempt with invalid email
When the email doesn't exist in database
Then the system returns "Invalid credentials" error
And does not reveal if email exists

Given a login attempt with wrong password
When the password doesn't match
Then the system returns "Invalid credentials" error
And increments failed attempt counter

Given a user with 5 failed login attempts
When they attempt to login again
Then the system temporarily locks the account
And returns "Account temporarily locked" error
```

### Unverified User Login
```gherkin
Given a user with emailVerified = false
When they attempt to login with correct credentials
Then the system returns "Please verify your email" error
And provides resend verification option
```

## Email Verification

### Verification Process
```gherkin
Given a newly registered user
When they click the verification link in email
Then the system validates the verification token
And sets emailVerified = true
And sets emailVerifiedAt = current timestamp
And updates status to VERIFIED (for customers)
And redirects to login page with success message
```

### Broker Verification
```gherkin
Given a broker with verified email
When admin reviews business documents
And approves the broker
Then the system sets status = VERIFIED
And sends approval notification email
And allows broker to access broker features
```

## JWT Token Management

### Token Generation
```gherkin
Given a successful login
When generating JWT token
Then the token contains:
  - userId
  - email
  - role
  - status
  - iat (issued at)
  - exp (expires in 7 days)
And is signed with JWT_SECRET
```

### Token Validation
```gherkin
Given a protected API endpoint
When request includes valid JWT token
Then the system validates token signature
And checks expiration
And extracts user information
And allows access to endpoint

Given a protected API endpoint
When request includes expired token
Then the system returns "Token expired" error
And status code 401

Given a protected API endpoint
When request includes invalid token
Then the system returns "Invalid token" error
And status code 401
```

## Authorization Rules

### Customer Access
```gherkin
Given a logged-in customer
When they access customer-only endpoints
Then the system allows access
When they access broker-only endpoints
Then the system returns "Insufficient permissions" error
When they access admin-only endpoints
Then the system returns "Insufficient permissions" error
```

### Broker Access
```gherkin
Given a logged-in verified broker
When they access broker-only endpoints
Then the system allows access
When they access admin-only endpoints
Then the system returns "Insufficient permissions" error
```

### Admin Access
```gherkin
Given a logged-in admin
When they access any endpoint
Then the system allows access
```

## Password Security

### Password Requirements
```gherkin
Given a password input
When the password is less than 8 characters
Then validation fails with "Password must be at least 8 characters"
When the password has no uppercase letter
Then validation fails with "Password must contain uppercase letter"
When the password has no lowercase letter
Then validation fails with "Password must contain lowercase letter"
When the password has no number
Then validation fails with "Password must contain number"
```

### Password Hashing
```gherkin
Given a valid password
When storing in database
Then the system hashes with bcrypt
And uses 12 salt rounds
And never stores plain text password
```

## Session Management

### Logout
```gherkin
Given a logged-in user
When they logout
Then the system clears httpOnly cookie
And invalidates client-side token
And returns success message
```

### Token Refresh
```gherkin
Given a token expiring within 24 hours
When user makes authenticated request
Then the system issues new token
And updates cookie with new token
And maintains user session
```

## Security Headers

### API Security
```gherkin
Given any API response
When headers are set
Then includes:
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security: max-age=31536000
```

## Rate Limiting

### Login Rate Limiting
```gherkin
Given login attempts from same IP
When more than 5 attempts in 15 minutes
Then the system blocks further attempts
And returns "Too many login attempts" error
And requires waiting period
```
