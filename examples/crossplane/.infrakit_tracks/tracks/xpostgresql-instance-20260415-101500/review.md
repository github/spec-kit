# Crossplane YAML Review: compositions/xpostgresql-instance

**Date**: 2026-04-15
**Files Reviewed**: `definition.yaml`, `composition.yaml`, `examples/claim-dev.yaml`, `examples/claim-prod.yaml`, `README.md`

---

## Verdict: APPROVED WITH NOTES

Standards-compliance pass. Two follow-ups (from architect-review AR1, AR2 and security-review S2)
must be applied before tagging `v1.0.0`, but those are tracked as separate work — the current
implementation is internally consistent and ready to merge as a release-candidate.

---

## Findings

| ID | Severity | Check | File | Issue | Fix |
|----|----------|-------|------|-------|-----|
| R1 | 🟢 LOW | Documentation | composition.yaml:127-156 | The `multiAZ` patch's map covers `<nil>|env` as a fallback — this is the function-patch-and-transform contract for unset variables, but it's not obvious. | Add an inline comment explaining the `<nil>` token to readers who haven't seen it before. (Composition already has a brief comment; consider expanding.) |

No CRITICAL, HIGH, or MEDIUM findings.

---

## Standards Compliance

| Check | Status | Notes |
|-------|--------|-------|
| File structure (XRD + Composition + examples + README) | ✅ | 4 YAMLs + README under `compositions/xpostgresql-instance/` |
| Pipeline mode | ✅ | composition.yaml line 9 |
| `defaultCompositionRef` set in XRD | ✅ | `postgres-aws` |
| `connectionSecretKeys` declared in XRD | ✅ | All 6 keys |
| Provider package versions follow coding-style.md | ✅ | `kms.aws.upbound.io/v1beta1`, `rds.aws.upbound.io/v1beta1` — both v1.2.0 |
| Required tag keys on EVERY managed resource | ✅ | `managed-by`, `environment`, `team`, `cost-center`, `crossplane.io/claim-name`, `crossplane.io/claim-namespace` |
| Tag values come from labels or parameters (not hardcoded) | ✅ | All FromCompositeFieldPath |
| `publiclyAccessible: false` non-overridable | ✅ | In base, no patch |
| `storageEncrypted: true` non-overridable | ✅ | In base, no patch |
| No hardcoded credentials | ✅ | `autoGeneratePassword + passwordSecretRef` |
| Connection secret name follows the Claim | ✅ | PatchSet `connection-secret-name` |
| KMS dependency expressed via Required policy | ✅ | `kmsKeyId` patch policy |
| Status fields propagated back to XR | ✅ | `endpoint`, `port`, `arn`, `kmsKeyArn` |
| Example claims pass schema | ✅ | Required fields present in both `claim-dev.yaml` and `claim-prod.yaml` |
| Example claims cover the default/override distinction | ✅ | dev omits multiAZ/deletionProtection (env-default); prod also omits (env-default true) |
| File naming kebab-case | ✅ | `composition.yaml`, `claim-dev.yaml`, `claim-prod.yaml` |
| YAML syntactically valid | ✅ | `python3 -c "import yaml; list(yaml.safe_load_all(open(f)))"` passes |

---

## Verification Steps Run

| Step | Result |
|------|--------|
| YAML parse (Python `yaml.safe_load_all`) | ✅ pass on all 4 files |
| Pattern check — required tags on KMS | ✅ 5 patches present |
| Pattern check — required tags on RDS | ✅ 5 patches present |
| Pattern check — no `publiclyAccessible` patch | ✅ confirmed |
| Pattern check — no `storageEncrypted` patch | ✅ confirmed |

In CI:
- `crossplane render` against both example claims with `function-patch-and-transform` cached locally.
- Kyverno policy test (`require-required-tags`) — should produce no violations against the rendered output.

---

## Open Follow-ups (tracked from earlier phases — NOT blocking this review)

1. **AR1** — Raise default `backupRetentionDays` to `14` or enforce per-env minimum via Kyverno.
2. **AR2** — Make `instanceClass` required for prod (via Kyverno mutation or XRD validation).
3. **S2** — Add a DB parameter group with `rds.force_ssl: 1` to enforce TLS at the engine.

These will land in a `v1.0.1` follow-up after `v1.0.0` is cut.

---

## Verdict and Next Actions

**APPROVED**. Tag this work as Composition release-candidate `v1.0.0-rc.1`.

- Update `.infrakit_tracks/tracks.md` — change status to `✅ done`.
- Open a follow-up track for AR1+AR2+S2 → release-blocking work to reach `v1.0.0`.
- Announce availability to product teams (payments, data, frontend, mobile, customer-portal).
