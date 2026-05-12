# Tagging Standard

All Crossplane-managed AWS resources at Acme Platform MUST carry the tags listed below. Tags are
applied via patches in every Composition; resources that lack required tags fail the
`/infrakit:review` step.

---

## Required Tags

| Tag Key | Value Source | Description |
|---------|--------------|-------------|
| `crossplane.io/claim-name` | Crossplane label `crossplane.io/claim-name` | Name of the originating Claim. |
| `crossplane.io/claim-namespace` | Crossplane label `crossplane.io/claim-namespace` | Namespace of the originating Claim. |
| `managed-by` | Static: `"crossplane"` | Identifies Crossplane-managed resources. |
| `environment` | `spec.parameters.environment` | One of `dev`, `staging`, `prod`. |
| `cost-center` | `spec.parameters.costCenter` | Billing allocation code (`CC-NNNN`). |
| `team` | `spec.parameters.teamName` | Owning team. Allowed values: `payments`, `data`, `frontend`, `mobile`, `platform`. |

## Optional Tags

| Tag Key | Description |
|---------|-------------|
| `project` | Project identifier for cross-team cost grouping. |
| `owner` | Individual owner email for escalation. |
| `created-by` | CI/CD pipeline or user that initiated the Claim (`argocd` for normal flow). |
| `compliance-scope` | `pci`, `soc2`, `hipaa` — only set when applicable. |

## Application Pattern

Every Composition includes a patch set that copies these labels/fields onto each managed resource's
`spec.forProvider.tags` map. The pattern looks like:

```yaml
patches:
  - type: FromCompositeFieldPath
    fromFieldPath: metadata.labels[crossplane.io/claim-name]
    toFieldPath: spec.forProvider.tags["crossplane.io/claim-name"]
  - type: FromCompositeFieldPath
    fromFieldPath: spec.parameters.environment
    toFieldPath: spec.forProvider.tags.environment
  # ... etc.
```

## Enforcement

- **At composition-author time**: `/infrakit:review` flags any managed resource that omits a required tag.
- **In cluster**: a Kyverno policy (`require-required-tags`) blocks Claims that would create resources without the required tag patches in the Composition.
- **In AWS account**: Config rule `required-tags` runs every 6 hours and pages the platform on-call for non-compliant resources.

## Exception Process

Tags that cannot be propagated due to AWS API limits (e.g., specific service endpoints that don't
support arbitrary tags) must be documented under "Tagging Exceptions" in the track's `spec.md` and
approved by the platform team lead.
