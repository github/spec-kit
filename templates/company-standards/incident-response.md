# Incident Response Plan

## Triage Levels

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **SEV-1** | Critical system down, data loss, or security breach. | Immediate (24/7) |
| **SEV-2** | Major feature broken, performance degraded. | < 2 Hours |
| **SEV-3** | Minor bug, workaround available. | Next Business Day |
| **SEV-4** | Cosmetic issue, non-urgent. | Scheduled Sprint |

## Roles

- **Incident Commander (IC)**: Manages the incident, coordinates communication.
- **Tech Lead**: Leads the technical investigation and fix.
- **Comms Lead**: Updates stakeholders and users.

## Response Process

1. **Detect**: Monitoring alert or user report triggers incident.
2. **Acknowledge**: On-call engineer acknowledges alert.
3. **Assess**: Determine severity and declare incident.
4. **Mobilize**: Open incident channel/bridge; assign roles.
5. **Mitigate**: Focus on restoring service (rollback, feature flag), not root cause fix.
6. **Resolve**: Service restored; verify stability.

## Post-Mortem Template

**Date**:
**Authors**:
**Severity**:

### Timeline
- [Time]: Incident started
- [Time]: Detected
- [Time]: Mitigated
- [Time]: Resolved

### Root Cause Analysis (5 Whys)
1. Why?
2. Why?
3. Why?
4. Why?
5. Why?

### Action Items
- [ ] [Fix]: Prevent recurrence
- [ ] [Detect]: Improve monitoring
- [ ] [Process]: Update runbooks
