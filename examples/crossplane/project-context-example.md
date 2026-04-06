# Acme Platform Infrastructure Constitution

## Overview

Acme Corp's Platform Engineering team manages shared AWS infrastructure for 4 product teams
(payments, data, frontend, mobile) using Crossplane on EKS. All infrastructure is GitOps-driven
via ArgoCD from the `infra-platform` monorepo. The platform team owns all Crossplane compositions;
product teams consume them via Claims in their respective namespaces.

---

## Architecture Decisions

### IaC Tool & Strategy

| Decision | Choice |
|----------|--------|
| **IaC Tool** | Crossplane v1.15.2 — Kubernetes-native, GitOps-aligned, no external state backend required |
| **GitOps Engine** | ArgoCD ApplicationSets; PRs to `main` trigger deployment; no direct `kubectl apply` in prod |
| **State Management** | EKS etcd (HA, 3 control plane nodes in separate AZs); Velero backups to S3 (`acme-velero-backups`) every 6 hours |

### Cloud Account Structure

AWS Organizations with 1 management account and 5 member accounts: `shared-services`, `dev`,
`staging`, `prod`, and `security-audit`. All member accounts reside under the Platform OU inside
the Acme Root OU. Cross-account access is via STS AssumeRole from the `shared-services` account
only; product accounts have no direct cross-account trust with each other.

**Organization Hierarchy:**

```
Root OU (Acme Corp)
└── Platform OU
    ├── shared-services  (Transit Gateway, Route53 private zones, Datadog, tooling)
    ├── dev              (development workloads)
    ├── staging          (staging workloads, mirrors prod config)
    ├── prod             (production workloads, full DR + compliance)
    └── security-audit   (read-only CloudTrail aggregation, GuardDuty master)
```

### Network Architecture

| Property | Value |
|----------|-------|
| **Topology** | Hub-and-spoke via AWS Transit Gateway in the `shared-services` account |
| **VPC Strategy** | Per-account VPCs — `dev` 10.10.0.0/16, `staging` 10.11.0.0/16, `prod` 10.12.0.0/16, `shared-services` 10.0.0.0/16 |
| **Connectivity Model** | Prod: private subnets only, outbound internet via NAT Gateway in `shared-services`. Dev: public subnets permitted with mandatory security group restrictions. No direct internet ingress to prod workloads. |

---

## Resource Organization

### Environments

Three environments — `dev`, `staging`, `prod` — each mapping to a separate AWS account and a
dedicated Kubernetes namespace (`dev`, `staging`, `prod`) on the platform EKS cluster.

- **dev**: Active development and experimentation; no DR requirement; relaxed security controls (public subnets allowed).
- **staging**: Mirrors prod configuration; single-AZ acceptable; 8h RTO / 4h RPO.
- **prod**: Subject to full security, compliance, and DR policies; Multi-AZ mandatory; 4h RTO / 1h RPO.

### Naming Conventions

**Convention**: `kebab-case`; format: `{env}-{team}-{resource-type}`

| Resource Type | Pattern | Example |
|---------------|---------|---------|
| Cloud resource | `{env}-{team}-{resource-type}` | `prod-payments-rds-primary`, `dev-data-s3-raw` |
| XRD Kind | PascalCase, X-prefixed | `XPostgreSQLInstance` |
| Claim Kind | PascalCase, no X prefix | `PostgreSQLInstance` |
| Composition Name | kebab-case | `postgres-aws` |

### Tagging Strategy

**Required Tags** (every managed resource MUST carry these):

| Tag Key | Value Source | Description |
|---------|-------------|-------------|
| `crossplane.io/claim-name` | Crossplane label | Name of the originating Claim |
| `crossplane.io/claim-namespace` | Crossplane label | Namespace of the originating Claim |
| `managed-by` | Static: `crossplane` | Identifies Crossplane-managed resources |
| `environment` | `spec.parameters.environment` | Target environment (`dev`/`staging`/`prod`) |
| `cost-center` | `spec.parameters.costCenter` | Billing allocation code (e.g., `CC-1042`) |
| `team` | `spec.parameters.teamName` | Owning team (e.g., `payments`, `data`) |

**Optional Tags** (propagated from Claim if provided):

| Tag Key | Description |
|---------|-------------|
| `project` | Project name for cost grouping |
| `owner` | Individual owner email for escalation |
| `created-by` | CI/CD pipeline or user who initiated the Claim |

---

## Security & Compliance

### Security Baseline

- Encryption at rest required on all storage resources (S3, RDS, ElastiCache, EBS, Secrets Manager).
- TLS 1.2+ required for all data in transit; TLS 1.3 preferred.
- No public network access in prod; any exception requires documented security review and GitHub issue approval.
- MFA required for all AWS console access (enforced via SCP on the Platform OU).
- Least-privilege IAM policies; no wildcard `*` actions in production policies.
- All API keys and credentials managed via AWS Secrets Manager; no plaintext secrets in code or YAML.

### Compliance Frameworks

- **SOC 2 Type II** — CloudTrail logging enabled on all accounts with 1-year retention in S3 (Glacier after 90 days); quarterly access reviews via automated report.
- **PCI-DSS** — Payments workloads isolated to a dedicated EKS node group (`payments-nodegroup`) with Kubernetes NetworkPolicies enforcing namespace isolation; cardholder data never stored in unencrypted form; annual PCI assessment by QSA.

### Access Management

- IRSA (IAM Roles for Service Accounts) for all pod-level AWS resource access; no EC2 instance profiles used for application workloads.
- No long-lived access keys; all programmatic access via STS AssumeRole with session duration ≤ 1 hour.
- Cross-account access from `shared-services` account only via dedicated cross-account roles.
- Emergency break-glass access: documented in runbook (`docs/runbooks/break-glass.md`); access events trigger PagerDuty alert and must be reviewed within 24h.

---

## Operational Standards

### Disaster Recovery & High Availability

| Requirement | Production | Staging | Dev |
|-------------|------------|---------|-----|
| **RTO** | 4 hours | 8 hours | N/A |
| **RPO** | 1 hour | 4 hours | N/A |
| **HA Requirement** | Multi-AZ mandatory for all RDS, ElastiCache, and ALBs | Single-AZ acceptable | None |

Prod database backups: automated RDS snapshots every 6h + daily cross-region copy to `us-west-2`.
EKS cluster state backed up via Velero to `acme-velero-backups` S3 bucket every 6h.
DR runbook: `docs/runbooks/disaster-recovery.md`.

### SLOs & SLAs

| Environment | Availability SLO | Latency Target |
|-------------|-----------------|----------------|
| `prod` | 99.9% monthly | p99 < 500ms for Crossplane reconciliation operations |
| `staging` | 99.5% monthly | best-effort |
| `dev` | best-effort | best-effort |

### Monitoring & Alerting

- **Metrics & Traces**: Datadog — all Crossplane controllers, managed resource sync status, and provider health instrumented via the Datadog Operator on the platform EKS cluster.
- **Prod P1/P2 alerts**: PagerDuty on-call rotation (`infra-oncall` schedule); escalation to platform team lead after 15 min.
- **Non-critical alerts**: Slack `#infra-alerts` channel.
- **Key dashboards**: Crossplane XR sync health, provider reconciliation errors, claim-to-ready latency P50/P95/P99.

---

## Governance & Change Management

### Change Process

- All infrastructure changes via GitHub PR against the `infra-platform` monorepo on the `main` branch.
- **Prod changes**: 2 approvals required — 1 from platform team, 1 from security team for any change affecting IAM, networking, or encryption.
- **Dev/staging changes**: 1 approval from any platform team member.
- **Emergency break-glass**: Follow `docs/runbooks/break-glass.md`; post-incident review required within 48h; all actions logged via CloudTrail.
- No direct `kubectl apply` or AWS console changes in prod; all changes must be traceable to a PR and ArgoCD sync.

### Enforcement

- This constitution supersedes all other team conventions; amendments require a platform team vote with ≥ 66% approval and documented rationale.
- All PRs must verify compliance with naming conventions, tagging requirements, and security baseline (automated checks via CI).
- Crossplane compositions that violate this constitution will not be merged; non-compliant resources in prod will be flagged in the weekly infrastructure health report.

---

**Version**: 1.0.0 | **Ratified**: 2026-01-15 | **Last Amended**: 2026-03-20
