# Security Code Review Guide

## OWASP Top 10 Checklist

### 1. Injection (SQL, NoSQL, OS, LDAP)

**Look for:**
```python
# BAD: String concatenation
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD: Parameterized queries
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

**Review points:**
- [ ] All database queries use parameterization
- [ ] No string interpolation in queries
- [ ] ORM used correctly (no raw queries with user input)
- [ ] Command execution sanitizes input

### 2. Broken Authentication

**Look for:**
- Weak password requirements
- Missing rate limiting on login
- Session fixation vulnerabilities
- Insecure session storage

**Review points:**
- [ ] Password hashing uses modern algorithm (bcrypt, argon2)
- [ ] Sessions invalidated on logout
- [ ] Session tokens are random and secure
- [ ] Multi-factor auth for sensitive operations

### 3. Sensitive Data Exposure

**Look for:**
```python
# BAD: Logging sensitive data
logger.info(f"User login: {username}, password: {password}")

# BAD: Returning sensitive data
return {"user": user, "ssn": user.ssn, "credit_card": user.cc}
```

**Review points:**
- [ ] PII not logged
- [ ] Sensitive data masked in responses
- [ ] Data encrypted in transit (HTTPS)
- [ ] Data encrypted at rest

### 4. XML External Entities (XXE)

**Look for:**
```python
# BAD: Default XML parser
parser = etree.XMLParser()

# GOOD: Disable external entities
parser = etree.XMLParser(resolve_entities=False)
```

**Review points:**
- [ ] XML parsers disable external entities
- [ ] DTD processing disabled
- [ ] Use JSON instead of XML when possible

### 5. Broken Access Control

**Look for:**
```python
# BAD: No authorization check
@app.route('/admin/users')
def list_users():
    return Users.all()

# GOOD: Authorization check
@app.route('/admin/users')
@requires_role('admin')
def list_users():
    return Users.all()
```

**Review points:**
- [ ] All endpoints have auth checks
- [ ] Object-level authorization (can user X access resource Y?)
- [ ] No IDOR vulnerabilities (Insecure Direct Object Reference)
- [ ] Deny by default

### 6. Security Misconfiguration

**Review points:**
- [ ] Debug mode disabled in production
- [ ] Default credentials changed
- [ ] Error messages don't leak stack traces
- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)
- [ ] Unnecessary features disabled

### 7. Cross-Site Scripting (XSS)

**Look for:**
```javascript
// BAD: Direct HTML injection
element.innerHTML = userInput;

// GOOD: Text content or sanitization
element.textContent = userInput;
// or
element.innerHTML = DOMPurify.sanitize(userInput);
```

**Review points:**
- [ ] User input escaped before rendering
- [ ] Content-Security-Policy header set
- [ ] Template engine auto-escapes
- [ ] No dangerouslySetInnerHTML with user data

### 8. Insecure Deserialization

**Look for:**
```python
# BAD: Pickle with untrusted data
data = pickle.loads(user_input)

# GOOD: JSON with validation
data = json.loads(user_input)
validate_schema(data, UserSchema)
```

**Review points:**
- [ ] No deserialization of untrusted data
- [ ] Type checking on deserialized objects
- [ ] Signature verification for serialized data

### 9. Using Components with Known Vulnerabilities

**Review points:**
- [ ] Dependencies are up to date
- [ ] No known CVEs in dependencies
- [ ] Automated vulnerability scanning in CI
- [ ] Lock files committed

### 10. Insufficient Logging & Monitoring

**Review points:**
- [ ] Security events logged (login, logout, failed auth)
- [ ] Logs don't contain sensitive data
- [ ] Logs are tamper-proof
- [ ] Alerting on suspicious activity

## Language-Specific Checks

### JavaScript/TypeScript
- [ ] No `eval()` with user input
- [ ] No `Function()` constructor with user input
- [ ] prototype pollution prevented
- [ ] RegExp DoS avoided (no super-linear patterns)

### Python
- [ ] No `exec()` or `eval()` with user input
- [ ] No `pickle` with untrusted data
- [ ] `subprocess` uses `shell=False`
- [ ] Path traversal prevented in file operations

### Java
- [ ] No `Runtime.exec()` with user input
- [ ] XML parsers configured securely
- [ ] No unsafe reflection
- [ ] Serialization filtered

### Go
- [ ] No `os/exec` with unsanitized input
- [ ] Template injection prevented
- [ ] Race conditions avoided
- [ ] Integer overflow checked

## Common Patterns to Flag

### Secrets in Code
```
# Flag these patterns:
password = "hardcoded"
api_key = "sk-..."
AWS_SECRET_ACCESS_KEY = "..."
```

### Dangerous Functions
```
# Flag usage of:
eval(), exec(), system(), popen()
dangerouslySetInnerHTML
innerHTML with user data
```

### Missing Checks
```
# Flag missing:
- Input validation
- Output encoding
- Authentication
- Authorization
- Rate limiting
```
