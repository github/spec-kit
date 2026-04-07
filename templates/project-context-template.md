# [PROJECT_NAME] Infrastructure Constitution
<!-- Example: Acme Platform Infrastructure Constitution, DataOps Infra Constitution -->

## Overview

[PLATFORM_OVERVIEW]
<!-- Example: Acme Corp's Platform Engineering team manages shared AWS infrastructure for 4 product
teams (payments, data, frontend, mobile) using Crossplane on EKS. All infrastructure is GitOps-driven
via ArgoCD from the infra-platform monorepo. The platform team owns all Crossplane compositions;
product teams consume them via Claims. -->

---

## Architecture Decisions

### IaC Tool & Strategy

| Decision | Choice |
|----------|--------|
| **IaC Tool** | [IAC_TOOL_CHOICE] |
| **GitOps Engine** | [GITOPS_STRATEGY] |
| **State Management** | [STATE_MANAGEMENT] |

<!-- Example:
| IaC Tool | Crossplane v1.15.2 — Kubernetes-native, GitOps-aligned, no external state backend |
| GitOps Engine | ArgoCD ApplicationSets; PRs to main trigger deployment; no direct kubectl apply in prod |
| State Management | EKS etcd (HA, 3 control plane nodes); Velero backups to S3 every 6 hours |
-->

### Cloud Account Structure

[ACCOUNT_STRUCTURE]
<!-- Example: AWS Organizations — 1 management account + 5 member accounts: shared-services, dev,
staging, prod, security-audit. All member accounts reside under the Platform OU inside the Acme Root OU. -->

**Organization Hierarchy:**

```
[ORG_HIERARCHY]
```

<!-- Example:
Root OU (Acme)
└── Platform OU
    ├── shared-services (Transit Gateway, DNS, tooling)
    ├── dev
    ├── staging
    ├── prod
    └── security-audit (read-only, CloudTrail aggregation)
-->

### Network Architecture

| Property | Value |
|----------|-------|
| **Topology** | [NETWORK_TOPOLOGY] |
| **VPC Strategy** | [VPC_STRATEGY] |
| **Connectivity Model** | [CONNECTIVITY_MODEL] |

<!-- Example:
| Topology | Hub-and-spoke via AWS Transit Gateway in shared-services account |
| VPC Strategy | Per-account VPCs — dev 10.10.0.0/16, staging 10.11.0.0/16, prod 10.12.0.0/16, shared 10.0.0.0/16 |
| Connectivity Model | Prod: private subnets only, NAT via shared-services. Dev: public subnets allowed with security group restrictions. No direct internet access for prod workloads. |
-->

---

## Resource Organization

### Environments

[ENVIRONMENTS_LIST]
<!-- Example: dev, staging, prod — each maps to a separate AWS account and a dedicated Kubernetes
namespace on the platform EKS cluster. dev is used for active development and experimentation;
staging mirrors prod configuration but with relaxed DR requirements; prod is subject to full
security, compliance, and DR policies. -->

### Naming Conventions

**Convention**: [NAMING_CONVENTION]
<!-- Example: kebab-case; format: {env}-{team}-{resource-type} -->

| Resource Type | Pattern | Example |
|---------------|---------|---------|
| Cloud resource | [NAMING_EXAMPLES] | [NAMING_EXAMPLE_CONCRETE] |
| XRD Kind | PascalCase, X-prefixed | `XPostgreSQLInstance` |
| Claim Kind | PascalCase, no X prefix | `PostgreSQLInstance` |
| Composition Name | kebab-case | `postgres-aws` |

<!-- Example:
| Cloud resource | {env}-{team}-{resource-type} | prod-payments-rds-primary, dev-data-s3-raw |
-->

---

## Security & Compliance

### Security Baseline

[SECURITY_BASELINE]
<!-- Example:
- Encryption at rest required on all storage resources (S3, RDS, ElastiCache, EBS)
- TLS 1.2+ required for all data in transit
- No public network access in prod without explicit security review and approval
- MFA required for all AWS console access
- Least-privilege IAM policies; no wildcard actions in production
-->

### Compliance Frameworks

[COMPLIANCE_FRAMEWORKS]
<!-- Example:
- SOC 2 Type II — CloudTrail logging enabled on all accounts; log retention ≥ 1 year; access reviews quarterly
- PCI-DSS — Payments workloads isolated to dedicated node group with network policies; cardholder data never stored in non-encrypted form
-->

### Access Management

[ACCESS_MANAGEMENT]
<!-- Example:
- IRSA (IAM Roles for Service Accounts) for all pod-level AWS resource access
- No long-lived access keys; all programmatic access via STS AssumeRole
- Cross-account access from shared-services account only; product accounts have no cross-account trust to each other
- Emergency access (break-glass) documented in runbook; access logged and reviewed within 24h
-->

---

## Operational Standards

### Disaster Recovery & High Availability

| Requirement | Production | Staging | Dev |
|-------------|------------|---------|-----|
| **RTO** | [PROD_RTO] | [STAGING_RTO] | N/A |
| **RPO** | [PROD_RPO] | [STAGING_RPO] | N/A |
| **HA Requirement** | [PROD_HA] | [STAGING_HA] | None |

<!-- Example:
| RTO | 4 hours | 8 hours | N/A |
| RPO | 1 hour | 4 hours | N/A |
| HA | Multi-AZ required for all RDS and ElastiCache | Single-AZ acceptable | None |
-->

[DR_TARGETS]
<!-- Example: Prod database backups: automated RDS snapshots every 6h + daily cross-region copy to us-west-2.
EKS state backed up via Velero to S3 every 6h. -->

### SLOs & SLAs

| Environment | Availability SLO | Latency Target |
|-------------|-----------------|----------------|
[SLO_DEFINITIONS]

<!-- Example:
| prod | 99.9% monthly | p99 < 500ms for provisioning operations |
| staging | 99.5% monthly | best-effort |
| dev | best-effort | best-effort |
-->

### Monitoring & Alerting

[MONITORING_STACK]
<!-- Example:
- Metrics & Traces: Datadog — all Crossplane controllers and managed resources instrumented
- Prod P1/P2 alerts: PagerDuty (on-call rotation required)
- Non-critical alerts: Slack #infra-alerts channel
- Crossplane health dashboard: Datadog — monitors XR sync status, provider health, reconciliation errors
-->

---

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
<!-- Example: Version: 1.0.0 | Ratified: 2026-01-15 | Last Amended: 2026-03-20 -->
