# Security Compliance Report: xpostgresql-instance-20260415-101500

**Date**: 2026-04-15
**Reviewer Persona**: Cloud Security Engineer
**Frameworks Audited**: SOC 2 Type II (CC6, CC7); PCI-DSS v4.0 (req 3, 4, 8, 10)
**Inputs**: `.infrakit/context.md`, spec.md, definition.yaml, composition.yaml

---

## Verdict: COMPLIANT WITH NOTES

All MUST controls covering data-at-rest encryption, in-transit encryption, credential hygiene,
and audit logging are present. Three observations follow — one MEDIUM, two LOW. The MEDIUM is a
gap against PCI-DSS req 10 that should be closed before this Composition handles cardholder data.

---

## Findings

| ID | Severity | Framework | Control | Issue | Recommendation |
|----|----------|-----------|---------|-------|----------------|
| S1 | 🟠 MEDIUM | PCI-DSS req 10.2 / 10.5 | Audit logging integrity | CloudWatch log exports are enabled, but there's no policy enforcing CloudTrail data-events on the RDS resource for PCI scope. | Either: (a) instruct platform team to enable CloudTrail data events org-wide for RDS, OR (b) add an explicit `aws_cloudtrail` resource for `pci` workloads in a sibling composition `XPostgreSQLPCI`. Out of scope for this Composition; flag as a downstream dependency. |
| S2 | 🟢 LOW | SOC 2 (CC6.7) | TLS enforcement | RDS enforces TLS at the cluster level via the parameter group `rds.force_ssl`, but this Composition does not set a parameter group. Default parameter groups in RDS PostgreSQL 16 do NOT enforce SSL. | Either: (a) add a `db.parameter_group` managed resource to this Composition with `rds.force_ssl: 1`, OR (b) document that callers must point `securityGroupIds` at a security group whose egress prevents non-TLS connections. Long-term: (a). |
| S3 | 🟢 LOW | SOC 2 (CC6.1) | Connection-secret protection | The provider auto-generates the admin password and writes it to a Secret in `crossplane-system`. RBAC on `crossplane-system` is platform-team-only, but the namespace also hosts other operators — broad access to this Secret would be a single-point-of-failure. | Encrypt etcd at rest with a customer-managed KMS key (handled at cluster level — out of this Composition's scope), AND add a Kyverno `disallow-listing-secrets` policy in `crossplane-system`. |

No CRITICAL or HIGH findings. No waivers required for SOC 2 baseline.

---

## Control Coverage

### SOC 2 — CC6 (Logical and Physical Access)

| Control | Implementation | Status |
|---------|----------------|--------|
| CC6.1 — Restrict logical access | `publiclyAccessible: false` (non-overridable); RBAC on Claims namespace-scoped | ✅ |
| CC6.6 — Implement boundary protections | VPC-only; subnet group + security groups required from caller | ✅ |
| CC6.7 — Restrict transmission of confidential info | TLS available — see S2 for enforcement gap | 🟢 Note |
| CC6.8 — Manage cryptographic keys | Customer-managed KMS, rotation on, 30-day deletion window | ✅ |

### SOC 2 — CC7 (System Operations)

| Control | Implementation | Status |
|---------|----------------|--------|
| CC7.1 — Vulnerability detection | RDS engine version explicit (16.3); automated minor-version patching is RDS default | ✅ |
| CC7.2 — Monitor system components | CloudWatch log exports for `postgresql` + `upgrade`; Performance Insights | ✅ |

### PCI-DSS v4.0

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| 3.5 — Cryptographic keys protected | Customer-managed KMS per instance with rotation | ✅ |
| 3.6 — Key lifecycle documented | KMS deletion window 30d; managed via Crossplane | ✅ |
| 4.2 — Strong cryptography in transit | TLS available via PG client config — see S2 | 🟢 Note |
| 8 — Identify and authenticate access | Admin password auto-generated, never hardcoded; rotated by clearing the source Secret | ✅ |
| 10.2 — Audit trails for all access | CloudWatch log exports enabled; CloudTrail data events not enforced — see S1 | 🟠 |
| 10.5 — Audit logs protected | Logs land in CloudWatch with org-default retention (1 year per `.infrakit/context.md`) | ✅ |

---

## Data Classification Handling

This Composition stores application data; classification is set by the consumer's Claim
(`spec.parameters` does not currently include a `dataClassification` field — that's modeled at
the team's bucket/database level via the `cost-center` and `team` tags plus org policy).

For workloads at `confidential` / `restricted` classifications, the platform team must verify:
- Subnet group is in a private subnet with no egress to public internet.
- Security group restricts ingress to known application pods only.
- Backup retention meets per-classification minimum (see AR1 from architect-review).

---

## Compliance Waivers

None requested.

---

## Re-Audit Triggers

This audit must be re-run if any of the following change:
- `publiclyAccessible` becomes a parameter.
- `storageEncrypted` becomes a parameter.
- The shared admin-password Secret is replaced by per-instance Secrets.
- A parameter group is added (would resolve S2).
- The Composition is reused for cardholder-data workloads (would need to address S1).

---

## Next Actions

- Address S2 (parameter group enforcing `rds.force_ssl: 1`) before tagging Composition `v1.0.0`.
- Document S1 as a downstream dependency for any team targeting PCI scope.
- Proceed to `/infrakit:implement` (the YAML has already been written; track moves to `in-progress → done` after `/infrakit:review`).
