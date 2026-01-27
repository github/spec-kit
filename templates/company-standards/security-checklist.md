# Security Review Checklist

## Authentication & Authorization

- [ ] All endpoints requiring access control are protected.
- [ ] Passwords are hashed using strong algorithms (Argon2, bcrypt).
- [ ] No hardcoded credentials in code or version control.
- [ ] Role-Based Access Control (RBAC) is enforced correctly.

## Data Protection

- [ ] Sensitive data (PII) is encrypted at rest and in transit (TLS).
- [ ] Data validation is performed on all user inputs.
- [ ] Secrets are managed via a secrets manager, not environment variables in plain text.

## OWASP Top 10 Coverage

- [ ] **Injection**: SQL/NoSQL injection prevention (use ORM or parameterized queries).
- [ ] **Broken Auth**: Session management is secure (HttpOnly cookies, secure flags).
- [ ] **Sensitive Data Exposure**: No sensitive data in logs or error messages.
- [ ] **XXE**: XML processors configured to prevent external entity expansion.
- [ ] **Broken Access Control**: IDOR vulnerabilities checked.
- [ ] **Security Misconfiguration**: Default accounts/passwords disabled.
- [ ] **XSS**: Output encoding applied; CSP headers configured.
- [ ] **Insecure Deserialization**: Safe serialization libraries used.
- [ ] **Using Components with Known Vulnerabilities**: Dependencies scanned (Snyk/Dependabot).
- [ ] **Insufficient Logging**: Security events logged and monitored.

## Infrastructure

- [ ] Security groups/Firewalls configured to least privilege.
- [ ] OS and container images patched to latest security updates.
