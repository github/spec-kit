# Complex Features (800-1000 LOC)

For new systems, critical features, or comprehensive changes.

## When to Use This Guide

- Estimated 800-1000 lines of code
- Requires architectural decisions
- High complexity or risk
- Examples: new subsystems, major refactors, security features

## The 5-Step Full Process

### Step 1: Specification (15 minutes)

Be explicit about **what** and **why**, not how.

```
/specify Build an authentication system supporting:
- Email/password login with bcrypt hashing
- JWT token-based sessions
- OAuth2 integration with GitHub and Google
- Email verification for new accounts
- Password reset via email
- Rate limiting on login attempts (5 per minute)
- Session management and logout

Requirements:
- Must work with existing database schema
- GDPR compliant
- Support both web and mobile clients
- Sessions expire after 30 days
```

Expected output:
- Detailed functional requirements
- Non-functional requirements (security, performance, scale)
- Technical constraints
- Use cases and acceptance criteria
- Review checklist

### Step 2: Refine Specification (10 minutes)

Ask clarifying questions:

```
/specify What about account recovery? What happens if someone loses access
to their email? Should we support security questions?
```

Use `/specify` multiple times to clarify and refine until you're confident.

### Step 3: Validate Specification (5 minutes)

```
/specify Review the Review & Acceptance Checklist. Check off items that pass.
Leave unchecked if they don't. This is your final validation before planning.
```

Don't proceed until the checklist looks good.

### Step 4: Create Implementation Plan (20 minutes)

Now describe **how** technically:

```
/plan Build this with:
- Express.js backend with TypeScript
- PostgreSQL for user and session data
- Redis for rate limiting and session management
- bcrypt for password hashing
- jsonwebtoken for JWT handling
- nodemailer for email verification
- Passport.js for OAuth2 integration
- Test with Jest and Supertest
```

Expected output:
- Architecture diagram and decisions
- Data model with schema
- API specifications
- Implementation approach broken into components
- Deployment and testing strategy
- Security considerations

### Step 5: Implement (varies)

```
/tasks

[Review the task list, then...]

implement specs/[feature-id]/plan.md
```

## Total Time: 45-60 minutes planning + implementation

## Detailed Walkthrough: Building a Payment System

### The Spec Phase

```
/specify Build a payment processing system that:
- Accepts card payments via Stripe integration
- Stores payment history and invoices
- Handles recurring subscriptions (monthly, annual)
- Supports multiple currencies
- Includes refund functionality
- Must PCI-compliant (no storing card data)
- Integration with existing user and order systems
```

Iterate:
```
/specify What should happen if a payment fails? Should we retry automatically?
How long should we retry?
```

```
/specify Should users be able to save multiple cards? How should we handle
card expiration?
```

### The Plan Phase

```
/plan Implement with:
- Stripe API for card processing
- Node.js/Express backend
- PostgreSQL for transaction history
- Webhook handling for payment events
- Idempotent payment API
- Comprehensive error handling for payment failures
- Unit and integration tests with Stripe test keys
```

AI generates:
- Data models for payments, subscriptions, invoices
- API endpoints: POST /payments, POST /subscriptions, POST /refunds, GET /invoices
- Webhook handling for Stripe events
- Error handling strategy
- Testing approach

### The Implementation Phase

```
/tasks
```

AI breaks down into:
1. Set up Stripe account and test keys
2. Create payment data models
3. Implement payment endpoint (create charge)
4. Implement subscription handling
5. Implement refund logic
6. Add webhook handling
7. Write comprehensive tests
8. Add error handling and logging

Each task becomes focused work.

## Quality Checkpoints

✅ Specification is clear and complete
✅ Implementation plan aligns with requirements
✅ Architectural decisions are documented
✅ Testing strategy is defined
✅ Security considerations addressed
✅ Data models properly designed

If any of these seem unclear, ask follow-up questions with `/specify` or `/plan`.

## Architecture & System Impact

With complex features, consider:

```
/plan also mention how this integrates with our system architecture.
If this requires changes to existing components, please document those
impacts and suggest an architecture version bump.
```

The plan should update `docs/system-architecture.md` to reflect new components and changes.

## Common Pitfalls

❌ **Starting code before specification is solid** - Results in rework
✅ **Ask clarifying questions upfront** - Saves implementation time

❌ **Trying to spec everything perfectly** - Perfectionism kills velocity
✅ **Good enough to start implementation** - Refine as you code

❌ **Ignoring the implementation plan** - You'll make the same decisions anyway
✅ **Review the plan before coding** - Find issues early

## Tips for Success

1. **Start general, get specific** - Begin with overview, then details
2. **Ask "why?" questions** - Understand motivation behind requirements
3. **Document constraints** - Know what you're working with (databases, APIs, etc.)
4. **Validate assumptions** - "Should X?" instead of assuming
5. **Plan for testing** - Quality is built in, not bolted on

## When to Escalate

If your feature is >1000 LOC estimated:

→ Use [Atomic PRs & Capabilities](./atomic-prs.md) to break it into smaller pieces

This way each piece gets focused review and merges faster.
