# Architecture Review Report: xpostgresql-instance-20260415-101500

**Date**: 2026-04-15
**Reviewer Persona**: Cloud Architect
**Inputs**: `.infrakit/context.md`, spec.md, plan.md, definition.yaml, composition.yaml

---

## Verdict: APPROVED WITH NOTES

The Composition meets the platform baseline. Three MEDIUM-severity recommendations follow.
None block proceeding to security review.

---

## Findings

| ID | Severity | Category | Issue | Recommendation |
|----|----------|----------|-------|----------------|
| AR1 | 🟠 MEDIUM | Reliability | Backup retention default of 7 days is below the SOC 2 baseline used by the Acme Platform compliance checklist (14 days for production). Prod claims will pass schema validation today even when they specify 7-day retention. | Raise the per-environment minimum at policy time via Kyverno: `prod` requires `backupRetentionDays >= 14`. Alternatively, default the XRD `backupRetentionDays` to `14` and let dev/staging override down. |
| AR2 | 🟠 MEDIUM | Cost | `db.t3.micro` default is appropriate for dev but will result in surprise downgrades if a team accidentally omits `instanceClass` on a prod claim. There's no env-keyed default. | Either make `instanceClass` `required: true` in the XRD, or apply a Kyverno mutation policy that rewrites `instanceClass: db.t3.micro` to `db.r6g.large` when `environment == prod`. |
| AR3 | 🟠 MEDIUM | Operability | The shared admin password Secret (`crossplane-system/postgres-admin-credentials`) means all RDS instances share a credential rotation lifecycle. Convenient at this scale; a future risk when one team needs an isolated rotation cadence. | Document the constraint in the Composition README; revisit when instance count > 10. |

---

## Structural Security Flags

None — no public endpoints, no wildcard IAM, no plaintext secrets in YAML, encryption mandatory.

---

## Architecture Correctness

| Check | Status | Notes |
|-------|--------|-------|
| API group follows `<domain>.platform.acme.com` | ✅ | `database.platform.acme.com` |
| XRD/Composition file separation | ✅ | Two files under `compositions/xpostgresql-instance/` |
| Pipeline mode used | ✅ | `mode: Pipeline` |
| `defaultCompositionRef` set | ✅ | Points at `postgres-aws` |
| Connection secret keys declared in XRD | ✅ | All 6 keys |
| Required vs. optional parameters clearly modeled | ✅ | 5 required (env, team, costCenter, subnetGroupName, securityGroupIds); rest optional with defaults |
| KMS key per resource (not shared) | ✅ | Per-instance KMS |
| All managed resources tagged | ✅ | Same 5-tag set on both resources |
| Dependency between resources expressed | ✅ | `Required` policy on `kmsKeyId` patch ensures KMS readiness |

---

## Reliability

| Check | Status | Notes |
|-------|--------|-------|
| Multi-AZ default reflects environment | ✅ | `prod=true`, others=`false`; overridable |
| Deletion protection default reflects environment | ✅ | Same pattern |
| Storage type allows IOPS-provisioned for hot workloads | ✅ | `io2` available via enum |
| Backups enabled | ✅ | 7d default — see AR1 |
| Performance Insights enabled | ✅ | 7-day retention (free tier) |
| CloudWatch log exports | ✅ | `postgresql`, `upgrade` |

---

## Cost

| Driver | Estimate (prod, db.r6g.xlarge, 500 GB, 30-day backups) | Notes |
|--------|-----------|-------|
| RDS instance | ~$420/mo | r6g.xlarge on-demand, us-east-1 |
| Storage (gp3) | ~$57/mo | 500 GB × $0.115/GB-mo |
| Backup storage (30d) | ~$50/mo | Estimated for moderate change rate |
| Multi-AZ standby | +100% on compute & storage | Doubles RDS + storage cost in prod |
| KMS key | $1/mo | + per-call charges (minimal) |
| Performance Insights (7d) | $0 | Free tier (vs. paid long-term retention) |

Prod totals around ~$1,000/month per instance with Multi-AZ. The architect should make sure the
team owns the cost-center mapping and budget alerting for this allocation.

---

## Completeness

| Item | Status |
|------|--------|
| All required security baselines present | ✅ |
| Parameter schema covers spec inputs | ✅ |
| Status fields cover spec outputs | ✅ |
| Out-of-scope items documented | ✅ |
| Example claims for dev AND prod | ✅ |

---

## Next Actions

- Proceed to `/infrakit:security-review xpostgresql-instance-20260415-101500`.
- Address AR1/AR2 before tagging Composition `v1.0.0` (raise backup retention default; enforce instanceClass minimum in prod).
- Document AR3 (shared password rotation) in the composition README.
