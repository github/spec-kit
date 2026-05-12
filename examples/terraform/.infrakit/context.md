# Northwind Platform Infrastructure Constitution

## Project Information

| Property | Value |
|----------|-------|
| **Project Name** | Northwind Platform Engineering |
| **Cloud Provider** | AWS |
| **Environments** | dev, staging, prod |
| **Last Updated** | 2026-04-12 |

## Overview

Northwind Logistics' Platform Engineering team manages shared AWS infrastructure for 5 product teams
(orders, fulfillment, returns, analytics, customer-portal) using Terraform 1.7+ and Atlantis for GitOps.
Modules live in a central `infra-modules` monorepo; product teams consume them via a `terraform-live`
repo organized by `<env>/<team>/<resource>/`. State is stored in S3 with DynamoDB locking, one backend
bucket per environment.

---

## Architecture Decisions

### IaC Tool & Strategy

| Decision | Choice |
|----------|--------|
| **IaC Tool** | Terraform `>= 1.7.0` — hashicorp/aws `~> 5.0` provider |
| **GitOps Engine** | Atlantis on EKS — PRs to `main` in `terraform-live` trigger `atlantis plan`; merge triggers `atlantis apply`. No direct `terraform apply` from laptops in any environment. |
| **State Management** | S3 backend per environment (`northwind-tfstate-{env}`) with DynamoDB locking (`northwind-tflock-{env}`); state files encrypted with per-env KMS keys; versioning + 90-day lifecycle |
| **Module Distribution** | Modules sourced via Git tag (`git::https://github.com/northwind/infra-modules.git//modules/<name>?ref=v1.2.3`); SemVer-pinned. |

### Cloud Account Structure

AWS Organizations with 1 management account and 5 member accounts: `shared-services`, `dev`,
`staging`, `prod`, and `security-audit`. All member accounts reside under the Platform OU inside
the Northwind Root OU. Cross-account access is via STS AssumeRole from the `shared-services` account
only; product accounts have no direct cross-account trust with each other.

**Organization Hierarchy:**

```
Root OU (Northwind Logistics)
└── Platform OU
    ├── shared-services  (Transit Gateway, Route53 private zones, central CloudTrail, Atlantis)
    ├── dev              (development workloads)
    ├── staging          (staging workloads, mirrors prod config)
    ├── prod             (production workloads, full DR + compliance)
    └── security-audit   (read-only CloudTrail aggregation, GuardDuty master, Security Hub)
```

### Network Architecture

| Property | Value |
|----------|-------|
| **Topology** | Hub-and-spoke via AWS Transit Gateway in the `shared-services` account |
| **VPC Strategy** | Per-account VPCs — `dev` 10.10.0.0/16, `staging` 10.11.0.0/16, `prod` 10.12.0.0/16, `shared-services` 10.0.0.0/16 |
| **Connectivity** | Prod: private subnets only, egress via NAT Gateway in `shared-services`. Dev: public subnets permitted with mandatory restrictive security groups. No direct internet ingress to prod workloads except via ALB+WAF. |

---

## Resource Organization

### Environments

Three environments — `dev`, `staging`, `prod` — each mapping to a separate AWS account.

- **dev**: Active development; no DR requirement; relaxed controls (public subnets allowed for testing).
- **staging**: Mirrors prod configuration; single-AZ acceptable; 8h RTO / 4h RPO.
- **prod**: Full security, compliance, and DR policies; Multi-AZ mandatory; 4h RTO / 1h RPO.

### Naming Conventions

**Convention**: `kebab-case`; format: `{env}-{team}-{resource-type}-{purpose}`

| Resource Type | Pattern | Example |
|---------------|---------|---------|
| Cloud resource | `{env}-{team}-{resource-type}-{purpose}` | `prod-orders-s3-events`, `dev-analytics-rds-warehouse` |
| Terraform module name | `kebab-case` | `s3-secure-bucket`, `rds-postgres-multiaz` |
| Module directory | `modules/<module-name>/` | `modules/s3-secure-bucket/` |
| Track Name | `<module>-<YYYYMMDD-HHMMSS>` | `s3-secure-bucket-20260415-093000` |

### Workspace / Working Directory Strategy

- **Modules** (`infra-modules` repo): no remote state, no providers configured — pure reusable modules.
- **Live config** (`terraform-live` repo): each consumer of a module lives in its own directory with its own backend and provider config. Layout: `terraform-live/<env>/<team>/<resource-name>/`.

### Tagging Strategy

**Required Tags** (every managed resource MUST carry these — enforced via AWS Config rules in `security-audit`):

| Tag Key | Value Source | Description |
|---------|--------------|-------------|
| `managed-by` | Static: `terraform` | Identifies Terraform-managed resources |
| `environment` | `var.environment` | Target environment (`dev`/`staging`/`prod`) |
| `cost-center` | `var.cost_center` | Billing allocation code (e.g., `CC-3017`) |
| `team` | `var.team` | Owning team (e.g., `orders`, `analytics`) |
| `project` | `var.project` | Project identifier (e.g., `northwind-platform`) |
| `data-classification` | `var.data_classification` | One of `public`, `internal`, `confidential`, `restricted` |

**Optional Tags** (propagated via `var.tags` map):

| Tag Key | Description |
|---------|-------------|
| `owner` | Individual owner email for escalation |
| `created-by` | CI/CD pipeline or user that initiated the apply |
| `compliance-scope` | e.g., `pci`, `sox`, `hipaa` — only set when applicable |

---

## Cloud Provider Defaults

**Provider**: AWS (`hashicorp/aws ~> 5.0`)

| Setting | Default Value |
|---------|---------------|
| Default Region | `us-east-1` (primary), `us-west-2` (DR for prod) |
| Provider Authentication | Atlantis IRSA role: `arn:aws:iam::<account>:role/atlantis-runner` (assume per-env via `assume_role` block) |
| Provider Default Tags | All required tags above set via `default_tags { tags = local.required_tags }` in every live config |

---

## Security Standards

- **Encryption at rest required** on all storage resources (S3, RDS, ElastiCache, EBS, Secrets Manager, SQS, SNS).
- **Customer-managed KMS keys** for `confidential` and `restricted` data classifications; AWS-managed keys acceptable for `internal` and `public`.
- **TLS 1.2+ required** for all data in transit; TLS 1.3 preferred for new workloads.
- **No public network access** in prod; any exception requires documented security review and an approved waiver in the resource's track directory.
- **MFA required** for all AWS console access (enforced via SCP on the Platform OU).
- **Least-privilege IAM**: no wildcard `*` actions in production policies; module-level IAM is scoped to the resource's ARN.
- **All secrets** managed via AWS Secrets Manager or Parameter Store with `SecureString`; no plaintext secrets in code, `.tfvars`, or Terraform state.

---

## Compliance

- **SOC 2 Type II** — CloudTrail logging enabled on all accounts with 1-year retention in S3 (Glacier after 90 days); quarterly access reviews via automated report.
- **PCI-DSS** — Customer-portal workloads isolated to a dedicated VPC subnet group with security groups restricted to required egress only; cardholder data tokenized at the edge, never stored in S3 or RDS in cleartext.

---

## DR & HA

| Requirement | Production | Staging | Dev |
|-------------|------------|---------|-----|
| RTO | 4 hours | 8 hours | N/A |
| RPO | 1 hour | 4 hours | N/A |
| HA | Multi-AZ mandatory for RDS, ElastiCache, ALB, NAT Gateway | Single-AZ acceptable | None |

Prod database backups: automated RDS snapshots every 6h + daily cross-region copy to `us-west-2`.
S3 critical buckets: cross-region replication to `us-west-2`. DR runbook: `docs/runbooks/disaster-recovery.md`.

**Availability SLOs**:

| Environment | Availability SLO | Latency Target |
|-------------|------------------|----------------|
| `prod` | 99.9% monthly | p99 < 500ms for control-plane API calls (provisioning) |
| `staging` | 99.5% monthly | best-effort |
| `dev` | best-effort | best-effort |

---

## Organization Standards

- All resources must follow the naming conventions above.
- All managed resources must carry the required tags (see `.infrakit/tagging-standard.md`).
- All production resources must meet the security baseline above.
- Module outputs must expose any value a downstream consumer would otherwise hardcode (ARNs, IDs, endpoints, KMS key IDs).
- Modules must not configure backends or providers — those are the responsibility of the live config that consumes the module.
- Sensitive outputs must be marked `sensitive = true`.

---

**Version**: 1.0.0 | **Ratified**: 2026-01-08 | **Last Amended**: 2026-04-12
