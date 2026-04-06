# Acme Platform Crossplane Coding Style Guide

> This document captures both universal Crossplane standards (non-negotiable) and
> project-specific conventions for the Acme Platform. Run `/infrakit:setup` to update
> project-specific sections.

All Crossplane engineers **MUST** follow these standards when generating infrastructure code.

---

## 1. IaC Tool & Version

| Setting | Value |
|---------|-------|
| **Crossplane Version** | v1.15.2 |
| **Primary Pipeline Function** | `function-go-template` v0.7.0 |
| **Provider Package(s)** | `upbound/provider-aws-s3` v1.2.0, `upbound/provider-aws-rds` v1.2.0, `upbound/provider-aws-ec2` v1.2.0, `upbound/provider-aws-elasticache` v1.2.0 |

---

## 2. File Organization

**Project directory structure:**

```
apis/
  database/
    v1alpha1/
      xpostgresqlinstances_types.yaml
  cache/
    v1alpha1/
      xrediscaches_types.yaml
  storage/
    v1alpha1/
      xobjectstores_types.yaml
compositions/
  database/
    postgres-aws.yaml
  cache/
    redis-aws.yaml
  storage/
    s3-aws.yaml
examples/
  database/
    claim.yaml
  cache/
    claim.yaml
  storage/
    claim.yaml
```

**Non-negotiable rules (apply to all projects):**
- **File Naming**: Use `kebab-case` for all YAML files (e.g., `postgres-instance.yaml`).
- **One composition per file**: Never combine multiple Compositions in one file.
- **Separation**: XRD (`definition.yaml`) and Composition (`composition.yaml`) must be in separate files.

---

## 3. Naming Conventions

### API Groups

**Base API Group**: `platform.acme.com`

| Resource | Pattern | Example |
|----------|---------|---------|
| XRD Kind | PascalCase prefixed with `X` | `XPostgreSQLInstance` |
| Claim Kind | Same as XRD without `X` prefix | `PostgreSQLInstance` |
| Composition Name | `{resource}-{provider}` | `postgres-aws`, `redis-aws` |
| CRD/XRD Name | `x<plural>.<group>` | `xpostgresqlinstances.platform.acme.com` |
| File Names | kebab-case | `postgres-aws.yaml` |

### Properties

- **Field Names**: `camelCase` (e.g., `storageSize`, `engineVersion`).
- **Enums**: `PascalCase` or `kebab-case` — be consistent within a resource.

### API Versioning Policy

| Version | Policy |
|---------|--------|
| `v1alpha1` | Experimental / new — internal use only, no compatibility guarantees; may change without notice |
| `v1beta1` | Stable API, backward-compatible minor changes allowed; changes announced to consuming teams with 2-sprint notice |
| `v1` | Production stable — no breaking changes permitted; requires migration plan, deprecation notice, and team ratification |

---

## 4. Compositions (MANDATORY STANDARDS)

### Pipeline Mode — ALWAYS Required

**NEVER use Resources mode.** All compositions MUST use `mode: Pipeline`:

```yaml
spec:
  mode: Pipeline
  pipeline:
    - step: render-resources
      functionRef:
        name: function-go-template
```

### Preferred Templating Function

**Project standard**: `function-go-template` — use `source: Inline` for all templates.

**Templating rules:**
- Use `source: Inline` to keep template logic visible in the composition file.
- Access XR parameters via `.observed.composite.resource.spec.parameters`.
- Use standard Go template variables and loops for complex logic.
- Ensure all generated resources have unique names.

### Patch Patterns

**Input patch (Composite → Managed Resource):**
```yaml
- type: FromCompositeFieldPath
  fromFieldPath: spec.parameters.<field>
  toFieldPath: spec.forProvider.<field>
```

**Output patch (Managed Resource → Composite Status):**
```yaml
- type: ToCompositeFieldPath
  fromFieldPath: status.atProvider.<field>
  toFieldPath: status.<field>
```

**String format transform:**
```yaml
- type: FromCompositeFieldPath
  fromFieldPath: metadata.name
  toFieldPath: spec.forProvider.name
  transforms:
    - type: string
      string:
        type: Format
        fmt: "%s-<suffix>"
```

### Formatting & Syntax

- **Indentation**: 2 spaces.
- **Line Length**: Keep lines under 100 characters where possible.
- **Sorting**: Sort `metadata` fields alphabetically; sort `spec` fields logically (required first, then optional).

---

## 5. CompositeResourceDefinitions (XRDs)

- **API Groups**: Use `platform.acme.com` as the base group for all compositions.
- **Descriptions**: ALWAYS add descriptions to all `properties` in the OpenAPI schema.
- **Categories**: Always include `crossplane` and `composite` (or `managed`) categories.
- **Required Fields**: Mark all mandatory parameters as `required` in the OpenAPI schema.

### Validation Approach

Use OpenAPI enum constraints on all environment fields (allowed: `dev`, `staging`, `prod`).
Mark all required fields as `required`. Apply pattern constraints on name fields:
`pattern: "^[a-z][a-z0-9-]*$"` to enforce kebab-case. Use `minimum`/`maximum` for numeric
resource sizes (e.g., storage in GiB, min: 20, max: 16384 for RDS).

---

## 6. Managed Resource Standards

### ProviderConfig (MANDATORY)

Every managed resource MUST explicitly set `providerConfigRef`:

```yaml
spec:
  providerConfigRef:
    name: default
```

**Never hardcode provider config names other than `default`** unless explicitly required by project context.

### Deletion Policy

**Project default**: `Delete` — use `Orphan` only for stateful production resources where data
loss is unacceptable. When using `Orphan`, add a comment in YAML:
```yaml
# ORPHAN: Production stateful resource — manual cleanup required on composition deletion
deletionPolicy: Orphan
```

### Management Policies

**Project standard**: Full lifecycle management by default (`["Create", "Read", "Update", "Delete"]`).
Use `["Observe"]` only for resources imported from pre-existing infrastructure; document the
import in the composition with a comment explaining why the resource is observe-only.

---

## 7. Resource Tagging

**ALWAYS add tags to managed resources when the provider supports tagging.**

### Required Tags (MANDATORY for all managed resources)

Every managed resource MUST include these tags via patches or templates:

| Tag Key | Source | Description |
|---------|--------|-------------|
| `crossplane.io/claim-name` | `metadata.labels["crossplane.io/claim-name"]` | Name of the originating Claim |
| `crossplane.io/claim-namespace` | `metadata.labels["crossplane.io/claim-namespace"]` | Namespace of the originating Claim |
| `crossplane.io/composite` | `metadata.name` | Name of the XR |
| `managed-by` | Static: `"crossplane"` | Indicates resource is managed by Crossplane |

### Project-Specific Tags

In addition to the required tags above, this project requires:

| Tag Key | Value Source | Description |
|---------|-------------|-------------|
| `environment` | `spec.parameters.environment` | Target environment (`dev`/`staging`/`prod`) |
| `cost-center` | `spec.parameters.costCenter` | Billing allocation code (e.g., `CC-1042`) |
| `team` | `spec.parameters.teamName` | Owning team (e.g., `payments`, `data`) |
| `project` | Static: `"acme-platform"` | Platform identifier for cost grouping |

### Provider-Specific Tag Field Paths

| Provider | Tag Field Path | Notes |
|----------|---------------|-------|
| **AWS** | `spec.forProvider.tags` | Array of `{key, value}` objects |
| **Azure** | `spec.forProvider.tags` | Map of key/value pairs |
| **GCP** | `spec.forProvider.labels` | GCP uses labels, not tags |

---

## 8. Connection Details

**ALWAYS publish connection details for resources that generate credentials or connection information.**

### Connection Secret Naming

**Pattern**: `{claim-name}-{resource-type}-conn`

Examples: `my-db-postgres-conn`, `payments-cache-redis-conn`, `data-store-s3-conn`

### When to Publish Connection Details

- Databases (endpoints, ports, credentials)
- Message queues (endpoints, credentials)
- Storage (bucket names, access keys)
- Caches (endpoints, auth tokens)
- Any resource users need to connect to

### Connection Secret Configuration

**In XRD (CompositeResourceDefinition):**
```yaml
spec:
  connectionSecretKeys:
    - endpoint
    - port
    - username
    - password
```

**In Composition Pipeline:**
```yaml
- step: connection-details
  functionRef:
    name: function-patch-and-transform
  input:
    apiVersion: pt.fn.crossplane.io/v1beta1
    kind: Resources
    resources:
      - name: my-database
        connectionDetails:
          - name: endpoint
            type: FromFieldPath
            fromFieldPath: status.atProvider.endpoint
          - name: port
            type: FromFieldPath
            fromFieldPath: status.atProvider.port
          - name: username
            type: FromConnectionSecretKey
            fromConnectionSecretKey: username
          - name: password
            type: FromConnectionSecretKey
            fromConnectionSecretKey: password
```

### Standard Connection Secret Keys

| Resource Type | Required Keys |
|---------------|---------------|
| Database | `endpoint`, `port`, `username`, `password`, `database` |
| Cache | `endpoint`, `port`, `authToken` |
| Message Queue | `endpoint`, `queueUrl`, `accessKey`, `secretKey` |
| Storage | `bucketName`, `endpoint`, `accessKey`, `secretKey` |

### Project-Specific Additional Keys

All database connection secrets must also include:
- `db-name` — the logical database name within the instance
- `ssl-mode` — the SSL mode to use for connections (e.g., `require`, `verify-full`)

---

## 9. Security Standards

### Non-Negotiable Rules

- **Secrets**: NEVER hardcode secrets, passwords, or API keys in Compositions.
- **Secrets**: Use `writeConnectionSecretToRef` for all resources that generate credentials.
- **Hard-coding**: Avoid hard-coding region-specific IDs (like AZ IDs) unless necessary — use labels or transforms.
- **Public access**: NEVER set public network access in production without explicit override and justification.
- **Encryption**: ALWAYS enable encryption at rest for storage resources in staging and prod.
- **Deletion policy**: Default to `Delete`; use `Orphan` only for stateful resources where explicitly requested.

### Project-Specific Security Defaults

- `storageEncrypted: true` on all RDS instances regardless of environment (including dev).
- `publiclyAccessible: false` on all RDS instances always; override requires a documented security review linked as a GitHub issue in the YAML comment.
- `deletionProtection: true` for prod environment; `false` for dev and staging.
- `multiAZ: true` required in prod for all RDS and ElastiCache instances; `false` acceptable in dev and staging to reduce cost.
- `backupRetentionPeriod: 7` (days) in prod; `1` in staging; `0` in dev.

---

## 10. Reference Example

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: postgres-aws
  labels:
    provider: aws
    crossplane.io/xrd: xpostgresqlinstances.platform.acme.com
spec:
  compositeTypeRef:
    apiVersion: platform.acme.com/v1alpha1
    kind: XPostgreSQLInstance
  mode: Pipeline
  pipeline:
    - step: render-resources
      functionRef:
        name: function-go-template
      input:
        apiVersion: gotemplating.fn.crossplane.io/v1beta1
        kind: GoTemplate
        source: Inline
        inline: |
          apiVersion: rds.aws.upbound.io/v1beta1
          kind: Instance
          metadata:
            name: {{ .observed.composite.resource.metadata.name }}-rds
            annotations:
              crossplane.io/external-name: {{ .observed.composite.resource.metadata.name }}
          spec:
            forProvider:
              region: {{ .observed.composite.resource.spec.parameters.region }}
              publiclyAccessible: false
              storageEncrypted: true
              instanceClass: {{ .observed.composite.resource.spec.parameters.instanceClass }}
              deletionProtection: {{ eq .observed.composite.resource.spec.parameters.environment "prod" }}
              multiAZ: {{ eq .observed.composite.resource.spec.parameters.environment "prod" }}
              tags:
                - key: managed-by
                  value: crossplane
                - key: environment
                  value: {{ .observed.composite.resource.spec.parameters.environment }}
                - key: team
                  value: {{ .observed.composite.resource.spec.parameters.teamName }}
                - key: project
                  value: acme-platform
            providerConfigRef:
              name: default
```
