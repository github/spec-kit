# User Workflow Specification - Sprint 2

## Overview
This specification defines the user registration, verification, and dashboard workflows for customers and brokers.

## User Registration Forms

### Customer Registration
```gherkin
Given a visitor on the registration page
When they select "Customer" role
And fill in email, password, firstName, lastName
And submit the form
Then the system creates a customer account
And sends email verification
And redirects to "Check your email" page
And displays success message
```

### Broker Registration
```gherkin
Given a visitor on the registration page  
When they select "Broker" role
And fill in email, password, firstName, lastName, companyName
And optionally add businessNumber
And submit the form
Then the system creates a broker account with PENDING status
And sends email verification
And displays "Account created, verification required" message
And shows additional verification steps needed
```

### Form Validation
```gherkin
Given a registration form
When email is invalid format
Then show "Please enter a valid email address"
When password is less than 8 characters
Then show "Password must be at least 8 characters"
When companyName is empty for broker
Then show "Company name is required for brokers"
When email already exists
Then show "Email already registered. Try logging in instead."
```

## Email Verification System

### Email Sending
```gherkin
Given a newly registered user
When registration completes successfully
Then the system generates verification token
And sends email with verification link
And token expires in 24 hours
And email contains user-friendly HTML template
```

### Email Verification
```gherkin
Given a user clicks verification link
When token is valid and not expired
Then set emailVerified = true
And set emailVerifiedAt = current timestamp
And redirect to login page with success message
When token is invalid or expired
Then show "Invalid or expired verification link"
And provide option to resend verification
```

### Resend Verification
```gherkin
Given a user with unverified email
When they request resend verification
Then generate new verification token
And send new verification email
And show "Verification email sent" message
And rate limit to prevent spam (max 3 per hour)
```

## User Profile Pages

### Profile Display
```gherkin
Given a logged-in user
When they visit /profile
Then display user information (name, email, role)
And show verification status
And display role-specific fields (companyName for brokers)
And provide edit functionality for allowed fields
```

### Profile Updates
```gherkin
Given a user editing their profile
When they update firstName, lastName, phone, or bio
And submit changes
Then validate input data
And update user record
And show "Profile updated successfully" message
When they try to change email or role
Then show "Contact support to change email or role"
```

## Role-Based Dashboards

### Customer Dashboard
```gherkin
Given a logged-in verified customer
When they visit /dashboard
Then display "My Projects" section
And show project statistics (total, active, completed)
And list recent printing requests
And provide "Create New Request" button
And show account status and profile completion
```

### Broker Dashboard  
```gherkin
Given a logged-in verified broker
When they visit /dashboard
Then display "My Jobs" section
And show job statistics (proposals sent, active jobs, completed)
And list available printing requests to bid on
And show recent proposals and their status
And display earnings summary
```

### Admin Dashboard
```gherkin
Given a logged-in admin
When they visit /dashboard
Then display platform statistics
And show pending broker verifications
And list recent user registrations
And provide user management tools
And display system health metrics
```

## Broker Verification Workflow

### Verification Request
```gherkin
Given a registered broker with verified email
When they complete business information
And upload required documents (business license, ID)
And submit for verification
Then system creates verification request
And notifies admin team
And shows "Verification submitted" status to broker
```

### Admin Verification Process
```gherkin
Given an admin reviewing broker verification
When they approve the broker
Then set broker status = VERIFIED
And send approval notification email
And unlock broker features (bidding, proposals)
When they reject the verification
Then set status = REJECTED
And send rejection email with reason
And allow broker to resubmit with corrections
```

## Protected Routes & Navigation

### Route Protection
```gherkin
Given a user accessing protected routes
When they are not logged in
Then redirect to /login with return URL
When they lack required permissions
Then show "Access denied" message
When their account is not verified
Then redirect to verification reminder page
```

### Navigation Behavior
```gherkin
Given a logged-in user
When they access the navigation
Then show role-appropriate menu items
And display user name and avatar
And provide logout functionality
And highlight current page
When they are not logged in
Then show login and register options only
```

## Error Handling & UX

### Network Errors
```gherkin
Given a form submission fails due to network error
When the request times out or fails
Then show "Connection error. Please try again."
And preserve form data
And allow retry without re-entering information
```

### Validation Feedback
```gherkin
Given form validation errors
When user submits invalid data
Then highlight invalid fields with red border
And show specific error messages below each field
And focus on first invalid field
And prevent form submission until fixed
```

## Performance Requirements

### Page Load Times
- Registration form: < 1 second
- Dashboard load: < 2 seconds  
- Profile update: < 500ms response
- Email sending: < 3 seconds

### User Experience
- Form validation: Real-time (on blur)
- Success feedback: Immediate visual confirmation
- Error recovery: Clear next steps provided
- Mobile responsive: All forms work on mobile devices
