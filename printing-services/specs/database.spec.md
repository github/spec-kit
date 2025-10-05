# Database Specification

## Overview
This specification defines the database requirements and behaviors for the Printing Services Marketplace platform.

## Database Schema Requirements

### User Management
- **Given** a user registration request
- **When** the user provides valid email, password, and role (customer/broker)
- **Then** the system creates a user with PENDING status
- **And** sends email verification

### Printing Request Lifecycle
- **Given** a verified customer
- **When** they submit a printing request with specifications
- **Then** the system stores the request with DRAFT status
- **And** allows the customer to publish it as OPEN

### Proposal System
- **Given** an OPEN printing request
- **When** a verified broker submits a proposal
- **Then** the system stores the proposal with PENDING status
- **And** notifies the customer

### Sample Workflow
- **Given** an ACCEPTED proposal
- **When** the broker creates a sample
- **Then** the system tracks sample status (PENDING → APPROVED/REJECTED)
- **And** allows customer feedback

### Transaction Security
- **Given** an approved sample
- **When** the customer initiates payment
- **Then** the system creates 50% deposit transaction
- **And** holds funds in escrow until completion

## Data Integrity Rules

### User Constraints
- Email addresses must be unique across all users
- Brokers must have companyName when status is VERIFIED
- Only VERIFIED users can create proposals or requests

### Request Constraints
- Only customers can create printing requests
- Budget must be positive decimal value
- Delivery date must be in the future

### Proposal Constraints
- Only brokers can create proposals
- Total price must be positive
- Timeline must be reasonable (1-90 days)

### Sample Constraints
- Only one active sample per proposal
- Customer must approve/reject within 7 days
- Broker can create revision if rejected

## Seed Data Verification

### Test Scenario: Database Seeding
```gherkin
Given an empty database
When the seed script runs
Then it creates:
  - 1 admin user (admin@printmarket.ca)
  - 1 customer user (customer@example.com)
  - 1 broker user (broker@printshop.ca)
  - 1 sample printing request
  - 1 sample proposal
And all users have VERIFIED status
And the printing request has OPEN status
And the proposal has PENDING status
```

### Test Scenario: User Authentication Data
```gherkin
Given a seeded database
When querying user by email "customer@example.com"
Then the user exists
And has role CUSTOMER
And has status VERIFIED
And password hash is valid
```

### Test Scenario: Request-Proposal Relationship
```gherkin
Given a seeded database
When querying the sample printing request
Then it has exactly 1 proposal
And the proposal belongs to the broker user
And the proposal references the correct request
```

## Performance Requirements

### Query Performance
- User lookup by email: < 50ms
- Request listing with filters: < 200ms
- Proposal creation: < 100ms
- Sample status updates: < 50ms

### Data Volume Expectations
- Support 10,000+ users
- Handle 1,000+ concurrent requests
- Store 100MB+ of file references
- Maintain 6 months of transaction history

## Security Requirements

### Data Protection
- All passwords hashed with bcrypt (12 rounds)
- Sensitive data encrypted at rest
- No plain text storage of payment info
- Audit trail for all transactions

### Access Control
- Users can only access their own data
- Brokers can view OPEN requests only
- Customers can view their proposals only
- Admins have read-only access to all data

## Migration Strategy

### Schema Evolution
- All changes via Prisma migrations
- Backward compatible for 2 versions
- Data migration scripts for breaking changes
- Rollback procedures documented

### Environment Promotion
- Development → Staging → Production
- Seed data for development only
- Production data never copied down
- Schema validation before deployment
