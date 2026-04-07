# [PROJECT_NAME] Crossplane Coding Style Guide
<!-- Example: Acme Platform Crossplane Coding Style Guide -->

> This document captures both universal Crossplane standards (non-negotiable) and
> project-specific conventions for this platform. Run `/infrakit:setup-coding-style` to populate
> the placeholder sections.

All Crossplane engineers **MUST** follow these standards when generating infrastructure code.

---

## 1. IaC Tool & Version

| Setting | Value |
|---------|-------|
| **Crossplane Version** | [CROSSPLANE_VERSION] |
| **Primary Pipeline Function** | [PRIMARY_FUNCTION] |
| **Provider Package(s)** | [PROVIDER_PACKAGES] |

<!-- Example:
| Crossplane Version | v1.15.2 |
| Primary Pipeline Function | function-go-template v0.7.0 |
| Provider Package(s) | upbound/provider-aws-s3 v1.2.0, upbound/provider-aws-rds v1.2.0 |
-->

---

## 2. File Organization

**Project directory structure:**

```
[PROJECT_FILE_STRUCTURE]
```

<!-- Example:
apis/
  database/
    v1alpha1/
      xpostgresqlinstances_types.yaml
  cache/
    v1alpha1/
      xrediscaches_types.yaml
compositions/
  database/
    postgres-aws.yaml
  cache/
    redis-aws.yaml
examples/
  database/
    claim.yaml
  cache/
    claim.yaml
-->

**Non-negotiable rules (apply to all projects):**
- **File Naming**: Use `kebab-case` for all YAML files (e.g., `postgres-instance.yaml`).
- **One composition per file**: Never combine multiple Compositions in one file.
- **Separation**: XRD (`definition.yaml`) and Composition (`composition.yaml`) must be in separate files.

---

## 3. Naming Conventions

### API Groups

**Base API Group**: `[BASE_API_GROUP]`
<!-- Example: platform.acme.com -->

| Resource | Pattern | Example |
|----------|---------|---------|
| XRD Kind | PascalCase prefixed with `X` | [XRD_KIND_EXAMPLE] |
| Claim Kind | Same as XRD without `X` prefix | [CLAIM_KIND_EXAMPLE] |
| Composition Name | `[COMPOSITION_NAME_PATTERN]` | [COMPOSITION_NAME_EXAMPLE] |
| CRD/XRD Name | `x<plural>.<group>` | `xpostgresqlinstances.[BASE_API_GROUP]` |
| File Names | kebab-case | `postgres-aws.yaml` |

<!-- Example:
XRD Kind: XPostgreSQLInstance
Claim Kind: PostgreSQLInstance
Composition Name pattern: {resource}-{provider} — e.g., postgres-aws
CRD Name: xpostgresqlinstances.platform.acme.com
-->

### Properties

- **Field Names**: `camelCase` (e.g., `storageSize`, `engineVersion`).
- **Enums**: `PascalCase` or `kebab-case` — be consistent within a resource.

### API Versioning Policy

| Version | Policy |
|---------|--------|
| `v1alpha1` | [V1ALPHA1_POLICY] |
| `v1beta1` | [V1BETA1_POLICY] |
| `v1` | [V1_POLICY] |

<!-- Example:
v1alpha1: Experimental / new — internal use only, no compatibility guarantees
v1beta1: Stable API, minor backward-compatible changes allowed; announced to consumers
v1: Production stable — no breaking changes permitted without migration plan
-->

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
        name: [PREFERRED_FUNCTION]
```

<!-- Example: function-go-template -->

### Preferred Templating Function

**Project standard**: `[PREFERRED_FUNCTION]`
<!-- Example: function-go-template — use source: Inline for all templates -->

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

- **API Groups**: Use the project base API group (`[BASE_API_GROUP]`) distinct from provider groups.
- **Descriptions**: ALWAYS add descriptions to all `properties` in the OpenAPI schema.
- **Categories**: Always include `crossplane` and `composite` (or `managed`) categories.
- **Required Fields**: Mark all mandatory parameters as `required` in the OpenAPI schema.

### Validation Approach

[PROJECT_VALIDATION_APPROACH]
<!-- Example: Use OpenAPI enum constraints on all environment fields; mark all required fields as required; use pattern constraints on name fields (e.g., pattern: "^[a-z][a-z0-9-]*$") -->

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

**Project default**: `[DELETION_POLICY_DEFAULT]`
<!-- Example: Delete — use Orphan only for stateful production resources where data loss is unacceptable; justification comment required in YAML -->

### Management Policies

**Project standard**: `[PROJECT_MANAGEMENT_POLICY]`
<!-- Example: Full lifecycle management by default (Create, Read, Update, Delete); use ["Observe"] only for resources imported from pre-existing infrastructure -->

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
[PROJECT_SPECIFIC_TAGS]

<!-- Example:
| `environment` | `spec.parameters.environment` | Target environment (dev/staging/prod) |
| `cost-center` | `spec.parameters.costCenter` | Billing allocation code |
| `team` | `spec.parameters.teamName` | Owning team name |
| `project` | Static: `"acme-platform"` | Platform identifier |
-->

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

**Pattern**: `[CONNECTION_SECRET_NAME_PATTERN]`
<!-- Example: {claim-name}-{resource-type}-conn — e.g., my-db-postgres-conn, cache-redis-conn -->

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

[PROJECT_CONNECTION_SECRET_KEYS]
<!-- Example: All database connections must also include db-name and ssl-mode keys. -->

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

[PROJECT_SECURITY_DEFAULTS]
<!-- Example:
- storageEncrypted: true on all RDS instances regardless of environment
- publiclyAccessible: false always; override requires security team approval tracked as GitHub issue
- deletionProtection: true for prod environment; false for dev/staging
- multiAZ: true required in prod for all RDS and ElastiCache; false acceptable in dev/staging
-->

---

## 10. Reference Example

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: postgres-aws
  labels:
    provider: aws
    crossplane.io/xrd: xpostgresqlinstances.[BASE_API_GROUP]
spec:
  compositeTypeRef:
    apiVersion: [BASE_API_GROUP]/v1alpha1
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
            providerConfigRef:
              name: default
```
