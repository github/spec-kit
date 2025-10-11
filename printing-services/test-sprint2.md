# Sprint 2 Testing Guide - SDD Validation

## 🎯 Objective
Validate Sprint 2 implementation against user-workflow.spec.md scenarios.

## 📋 Pre-Test Setup

### 1. Environment Preparation
```bash
# Backend setup
cd backend
npm install
npx prisma generate
npx prisma db push
npm run prisma:seed
npm run dev  # Should start on port 5000

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev  # Should start on port 3000
```

### 2. Email Testing Setup
- Sign up at [Mailtrap.io](https://mailtrap.io) (free)
- Get SMTP credentials from inbox settings
- Update `backend/.env`:
  ```
  EMAIL_HOST=smtp.mailtrap.io
  EMAIL_PORT=2525
  EMAIL_USER=your-mailtrap-username
  EMAIL_PASS=your-mailtrap-password
  ```

### 3. Clear Browser State
- Open Developer Tools → Application → Local Storage
- Clear all entries for localhost:3000

## 🧪 Test Scenarios

### Test 1: Customer Registration Flow
**Spec**: "Given visitor selects Customer role, When form submitted, Then account created and email sent"

**Steps**:
1. Visit `http://localhost:3000/register`
2. Select "Get Printing Services" (Customer role)
3. Fill form:
   - Email: `customer@test.com`
   - Password: `TestPass123!`
   - First Name: `John`
   - Last Name: `Doe`
   - Confirm Password: `TestPass123!`
   - Check terms agreement
4. Submit form

**Expected Results**:
- ✅ Success toast: "Registration successful! Please check your email"
- ✅ Redirect to verification page
- ✅ Email appears in Mailtrap inbox with verification link
- ✅ Database: User created with role="CUSTOMER", emailVerified=false

### Test 2: Broker Registration Flow
**Spec**: "Given visitor selects Broker role, When business details provided, Then broker account pending"

**Steps**:
1. Visit `http://localhost:3000/register`
2. Select "Provide Printing Services" (Broker role)
3. Notice "Company Name" field appears (conditional rendering)
4. Fill form:
   - Email: `broker@printshop.com`
   - Password: `BrokerPass456!`
   - First Name: `Jane`
   - Last Name: `Smith`
   - Company Name: `QuickPrint Solutions`
   - Business Number: `123456789` (optional)
5. Submit form

**Expected Results**:
- ✅ Success toast with broker-specific message
- ✅ Email sent to Mailtrap
- ✅ Database: User created with role="BROKER", companyName populated

### Test 3: Form Validation
**Spec**: "Given invalid input, Then specific error messages shown"

**Test Cases**:
- Weak password (`weak123`) → "Password must contain uppercase, lowercase, and number"
- Invalid email (`notanemail`) → "Please enter a valid email address"
- Broker without company name → "Company name is required for brokers"
- Mismatched passwords → "Passwords do not match"

### Test 4: Email Verification
**Spec**: "Given verification link clicked, When token valid, Then account activated"

**Steps**:
1. From Mailtrap email, copy verification URL
2. Visit the verification URL in browser
3. Should redirect to login with success message

**Expected Results**:
- ✅ Success message: "Email verified successfully"
- ✅ Database: emailVerified=true, emailVerifiedAt=timestamp
- ✅ Redirect to login page

### Test 5: Login & Authentication
**Spec**: "Given verified user credentials, When login submitted, Then dashboard access granted"

**Steps**:
1. Visit `http://localhost:3000/login`
2. Enter verified user credentials
3. Submit login form

**Expected Results**:
- ✅ Success toast: "Login successful"
- ✅ JWT token stored in localStorage
- ✅ Redirect to role-appropriate dashboard
- ✅ Navigation shows user name and logout option

### Test 6: Protected Routes & Role-Based Access
**Spec**: "Given logged-in user, When accessing dashboard, Then role-specific UI loads"

**Test Cases**:
- Customer login → Customer dashboard with "My Projects" section
- Broker login → Broker dashboard with "My Jobs" section
- Unauthenticated access to `/dashboard` → Redirect to login
- Customer accessing broker-only routes → Access denied

### Test 7: Profile Management
**Spec**: "Given logged-in user, When profile updated, Then changes saved"

**Steps**:
1. Login and navigate to `/profile`
2. Update firstName, lastName, phone
3. Submit changes

**Expected Results**:
- ✅ Profile data loads correctly
- ✅ Updates save successfully
- ✅ Success toast: "Profile updated"
- ✅ Database reflects changes

### Test 8: Email Resend Functionality
**Spec**: "Given unverified user, When resend requested, Then new email sent"

**Steps**:
1. Login with unverified account
2. Request resend verification
3. Check rate limiting (max 3 per hour)

## 🔍 API Testing (Optional - Postman/cURL)

### Registration API
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "api-test@example.com",
    "password": "ApiTest123!",
    "firstName": "API",
    "lastName": "Test",
    "role": "CUSTOMER"
  }'
```

**Expected**: 201 status, user object returned (no password)

### Login API
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "api-test@example.com",
    "password": "ApiTest123!"
  }'
```

**Expected**: 200 status, JWT token + user object

### Protected Profile API
```bash
curl -X GET http://localhost:5000/api/auth/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected**: 200 status with user profile data

## 📊 Success Criteria

### ✅ All Tests Pass When:
- [ ] Customer registration creates account and sends email
- [ ] Broker registration shows conditional fields and creates broker account
- [ ] Form validation catches all error cases with helpful messages
- [ ] Email verification activates accounts successfully
- [ ] Login works for verified users and sets up authentication
- [ ] Role-based dashboards load appropriate content
- [ ] Profile updates save correctly
- [ ] API endpoints return expected responses
- [ ] No console errors in browser or server logs

### 🚨 Common Issues & Fixes:
- **Email not sending**: Check Mailtrap credentials in `.env`
- **CORS errors**: Ensure frontend proxy configured in `vite.config.ts`
- **Token invalid**: Check JWT_SECRET matches between requests
- **Database errors**: Run `npx prisma db push` to sync schema
- **Module not found**: Restart TypeScript server in IDE

## 📈 Performance Checks
- Registration form loads < 1 second
- Form submission responds < 2 seconds
- Dashboard loads < 2 seconds
- All forms work on mobile (responsive design)

## 🎉 Sprint 2 Validation Complete
When all tests pass, Sprint 2 is validated against SDD specifications and ready for Sprint 3 (Printing Request System).

**Next**: Create `specs/printing-request.spec.md` and implement marketplace core functionality.
