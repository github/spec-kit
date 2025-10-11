# Printing Request System Specification

## Overview
This specification defines the core marketplace functionality where customers create printing requests and brokers submit proposals.

## Request Creation Workflow

### Customer Request Submission
```gherkin
Given a logged-in verified customer
When they submit a printing request form with:
  - Title: "Business Cards"
  - Description: "Premium quality cards for my business"
  - Specs: {"type": "business-cards", "quantity": 500, "paper": "glossy", "color": "full"}
Then the system creates a request with status "PENDING"
And stores the JSON specifications
And displays success message "Request created successfully"
And redirects to customer dashboard
```

### Request Validation
```gherkin
Given a customer creating a request
When title is empty
Then show error "Title is required"
When quantity is less than 1
Then show error "Quantity must be at least 1"
When specs object is malformed
Then show error "Invalid specifications format"
```

### Role-Based Request Access
```gherkin
Given different user roles
When customer views requests
Then they see only their own requests
When broker views requests  
Then they see only PENDING requests (open jobs)
When admin views requests
Then they see all requests regardless of status
```

## Proposal Submission Workflow

### Broker Proposal Creation
```gherkin
Given a logged-in verified broker
And an open printing request exists
When they submit a proposal with:
  - Price: 120.00
  - Timeline: "5 business days"
  - Details: "High-quality offset printing with UV coating"
Then the system creates a proposal linked to the request
And updates request status to "PROPOSED"
And sends notification email to customer
And shows success message "Proposal submitted successfully"
```

### Proposal Validation
```gherkin
Given a broker submitting a proposal
When price is negative or zero
Then show error "Price must be greater than 0"
When timeline is empty
Then show error "Timeline is required"
When request is not in PENDING status
Then show error "This request is no longer accepting proposals"
When broker already has proposal for this request
Then show error "You have already submitted a proposal for this request"
```

## Proposal Acceptance Workflow

### Customer Accepts Proposal
```gherkin
Given a customer with requests that have proposals
When they accept a specific proposal
Then the proposal is marked as accepted
And request status changes to "APPROVED"
And other proposals for same request are marked as rejected
And broker receives acceptance notification email
And customer sees "Proposal accepted! Next steps will be communicated via email"
```

### Proposal Management
```gherkin
Given a customer viewing their requests
When request has multiple proposals
Then they can compare proposals side-by-side
And see broker ratings and reviews
And view proposal details (price, timeline, description)
And have clear accept/reject buttons for each proposal
```

## Request Status Lifecycle

### Status Transitions
```gherkin
Given a printing request lifecycle
When initially created
Then status is "PENDING"
When first proposal submitted
Then status becomes "PROPOSED"  
When customer accepts a proposal
Then status becomes "APPROVED"
When job is completed
Then status becomes "COMPLETED"
When customer cancels
Then status becomes "CANCELLED"
```

### Status-Based Visibility
```gherkin
Given requests with different statuses
When broker browses available jobs
Then they only see "PENDING" requests
When customer views dashboard
Then they see all their requests with current status
When request is "APPROVED" or "COMPLETED"
Then it no longer appears in broker job listings
```

## Dashboard Integration

### Customer Dashboard
```gherkin
Given a logged-in customer
When they visit their dashboard
Then they see "My Requests" section with:
  - Table of all their requests
  - Status indicators (PENDING, PROPOSED, APPROVED, etc.)
  - Proposal count for each request
  - "Create New Request" button
  - Request details view with proposals
```

### Broker Dashboard
```gherkin
Given a logged-in broker
When they visit their dashboard
Then they see "Available Jobs" section with:
  - Table of PENDING requests they can bid on
  - Request specifications and requirements
  - Customer information (name, location)
  - "Submit Proposal" button for each request
  - "My Proposals" section showing submitted proposals and status
```

## Data Specifications

### Request JSON Schema
```gherkin
Given a printing request specification
When stored in database
Then specs field contains JSON with structure:
{
  "type": "business-cards" | "flyers" | "banners" | "brochures" | "other",
  "quantity": number (min: 1),
  "dimensions": {"width": number, "height": number, "unit": "mm|in"},
  "paper": "standard" | "premium" | "recycled" | "glossy" | "matte",
  "color": "full" | "black-white" | "spot-color",
  "sides": "single" | "double",
  "finishing": ["lamination", "binding", "folding", "cutting"],
  "files": ["url1", "url2"],
  "notes": "string"
}
```

### Proposal Data Requirements
```gherkin
Given a broker proposal
When submitted to system
Then it must contain:
  - price: positive decimal number
  - timeline: string description (e.g., "5 business days")
  - details: optional description of approach/materials
  - requestId: valid existing request ID
  - brokerId: authenticated broker's user ID
```

## API Endpoint Specifications

### Request Endpoints
```gherkin
Given API endpoints for requests
When POST /api/requests with valid data and customer auth
Then return 201 with created request object
When GET /api/requests with customer auth
Then return 200 with array of customer's requests
When GET /api/requests with broker auth
Then return 200 with array of PENDING requests
When GET /api/requests with admin auth
Then return 200 with all requests
```

### Proposal Endpoints
```gherkin
Given API endpoints for proposals
When POST /api/proposals with valid data and broker auth
Then return 201 with created proposal object
When PATCH /api/proposals/:id/accept with customer auth
Then return 200 with updated proposal
And request status updated to APPROVED
When unauthorized user attempts proposal operations
Then return 403 Forbidden
```

## Error Handling

### Authentication Errors
```gherkin
Given API requests without proper authentication
When accessing protected endpoints
Then return 401 Unauthorized
When user lacks required role permissions
Then return 403 Forbidden with descriptive message
```

### Validation Errors
```gherkin
Given invalid request data
When submitting forms or API calls
Then return 400 Bad Request with specific field errors
And preserve user input for correction
And highlight invalid fields in UI
```

## Performance Requirements

### Response Times
- Request creation: < 500ms
- Request listing: < 1 second
- Proposal submission: < 500ms
- Dashboard load: < 2 seconds

### Data Limits
- Maximum 10MB total file attachments per request
- Maximum 50 proposals per request
- Request specifications JSON limited to 10KB

## Security Requirements

### Data Protection
- All request data encrypted at rest
- File uploads scanned for malware
- Sensitive customer information masked in broker views
- Audit trail for all request/proposal actions

### Access Control
- Customers can only access their own requests
- Brokers cannot see other brokers' proposals
- Request modification only allowed by original creator
- Proposal acceptance only by request owner
