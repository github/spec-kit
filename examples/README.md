# InfraKit Examples

Two complete, end-to-end walkthroughs showing every file InfraKit produces when you take an
infrastructure resource from "I need this" to "ready to publish."

| Walkthrough | IaC Tool | Scenario | Path |
|-------------|----------|----------|------|
| [Terraform](terraform/) | Terraform 1.7+ | AWS S3 secure-bucket module with KMS, lifecycle, optional CRR | [`examples/terraform/`](terraform/) |
| [Crossplane](crossplane/) | Crossplane v1.15+ | `XPostgreSQLInstance` XR wrapping AWS RDS via `provider-aws-rds` | [`examples/crossplane/`](crossplane/) |

Each example contains the `.infrakit/` config (context, coding-style, tagging-standard), a
single track under `.infrakit_tracks/tracks/`, and the actual deliverable (the `.tf` module or
the Crossplane Composition YAML).

Read the per-example README inside each directory for the full file map and a recommended
reading order.
