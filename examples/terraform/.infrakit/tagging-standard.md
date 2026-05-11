# Tagging Standard

All Terraform-managed resources at Northwind Platform MUST carry the tags listed below. The
`managed-by`, `environment`, `cost-center`, `team`, `project`, and `data-classification` tags are
enforced by AWS Config rules in the `security-audit` account — non-compliant resources page the
platform on-call within 30 minutes.

---

## Required Tags

| Tag Key | Value Source | Description |
|---------|--------------|-------------|
| `managed-by` | Static: `"terraform"` | Identifies Terraform-managed resources. Used by audit tooling to distinguish from console-created or ad-hoc resources. |
| `environment` | `var.environment` | One of `dev`, `staging`, `prod`. |
| `cost-center` | `var.cost_center` | Billing allocation code. Format: `CC-NNNN` (e.g., `CC-3017`). |
| `team` | `var.team` | Owning team name. Allowed values: `orders`, `fulfillment`, `returns`, `analytics`, `customer-portal`, `platform`. |
| `project` | `var.project` | Project identifier (default `northwind-platform`). |
| `data-classification` | `var.data_classification` | One of `public`, `internal`, `confidential`, `restricted`. Drives encryption-key choice and access-review cadence. |

## Optional Tags

| Tag Key | Description |
|---------|-------------|
| `owner` | Individual owner email for escalation. |
| `created-by` | CI/CD pipeline or user that initiated the apply (`atlantis` for normal flow). |
| `compliance-scope` | `pci`, `sox`, `hipaa` — only set when the resource is in scope for the named framework. |
| `terraform-module` | The module that created the resource (set via `path.module`). |

## Application Pattern

Every module declares `local.required_tags` from input variables, and every resource sets
`tags = merge(local.required_tags, var.tags)`. Live configs additionally set `default_tags` on
the `aws` provider with the same map, providing defense-in-depth coverage for resources that miss
the per-resource pattern.

## Enforcement

- **At apply time**: pre-commit hook `tflint` rules + a custom validation step in Atlantis verify all required tags are present in the plan output.
- **In account**: AWS Config managed rule `required-tags` runs every 6 hours on all supported resource types.
- **In CI**: `tfsec` and `checkov` scans block PRs that introduce resources without required tags.

## Exception Process

Resources that genuinely cannot carry tags (e.g., specific AWS service endpoints, certain managed
service internals) must be documented in the resource's track `spec.md` under "Tagging Exceptions".
The track must be reviewed and approved by the platform team lead before apply.
