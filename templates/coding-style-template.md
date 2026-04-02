# Crossplane Coding Style Guide

All Crossplane engineers **MUST** follow these standards when generating infrastructure code.

## 1. File Organization

- **Directory Structure**:
  ```
  apis/
    <group>/
      <version>/
        <kind>_types.yaml  # XRDs
  compositions/
    <composition>.yaml          # Compositions
  examples/
    <kind>/
      claim.yaml           # Example Claims
  ```
- **File Naming**: Use `kebab-case` for file names (e.g., `postgres-instance.yaml`).

## 2. Naming Conventions

### Kubernetes Objects
- **Metadata Name**: Use `kebab-case`.
- **CRD/XRD Names**: `x<plural>.<group>` (e.g., `xpostgresqlinstances.database.example.com`).
- **Kind**: `PascalCase`.
  - XR: Start with `X` (e.g., `XPostgreSQLInstance`).
  - Claim: Same as XR without `X` (e.g., `PostgreSQLInstance`).

### Properties
- **Field Names**: `camelCase` (e.g., `storageSize`, `engineVersion`).
- **Enums**: `PascalCase` or `kebab-case` (be consistent within a resource).

## 3. Formatting & Syntax

- **Indentation**: 2 spaces.
- **Line Length**: Keep lines under 100 characters where possible.
- **Sorting**:
  - Sort `metadata` fields alphabetically.
  - Sort `spec` fields logically (required first, then optional).

## 4. CompositeResourceDefinitions (XRDs)

- **API Groups**: Use a domain-based group distinct from providers (e.g., `platform.acme.com`).
- **Versions**:
  - `v1alpha1`: Experimental / new.
  - `v1beta1`: Stable API, minor changes possible.
  - `v1`: Production stable.
- **Descriptions**: ALWAYS add descriptions to `properties` in the OpenAPI schema.
- **Categories**: Add `crossplane` and `managed` (or `composite`) categories.

## 5. Compositions

- **Mode**: ALWAYS use `mode: Pipeline`.
- **Labels**:
  - `provider: <provider_name>` (e.g., `provider: aws`).
  - `crossplane.io/xrd: <xrd_name>`.
- **Functions**: Prefer `function-go-template` for resource generation and patching logic.
- **Templating**:
  - Use `source: Inline` for templates to keep logic visible.
  - Access XR parameters via `.observed.composite.resource.spec.parameters`.
  - Use standard Go template variables and loops for complex logic.
  - Ensure all generated resources have unique names.

## 6. Managed Resources

- **ProviderConfig**: ALWAYS explicitly set `providerConfigRef`.
  ```yaml
  providerConfigRef:
    name: default
  ```
- **DeletionPolicy**: Default to `Delete`. use `Orphan` only for stateful resources where requested.
- **ManagementPolicies**: Use explicit policies if not managing the full lifecycle (e.g., `["Observe", "Create", "Update", "Delete"]`).

## 7. Resource Tagging

**ALWAYS add tags to managed resources when the provider supports tagging.**

### Required Tags
Every managed resource MUST include these tags (via patches or templates):

| Tag Key | Source | Description |
|---------|--------|-------------|
| `crossplane.io/claim-name` | `metadata.labels["crossplane.io/claim-name"]` | Name of the originating Claim |
| `crossplane.io/claim-namespace` | `metadata.labels["crossplane.io/claim-namespace"]` | Namespace of the originating Claim |
| `crossplane.io/composite` | `metadata.name` | Name of the XR |
| `managed-by` | `"crossplane"` (static) | Indicates resource is managed by Crossplane |

### Optional Tags (propagate from Claim if provided)
| Tag Key | Description |
|---------|-------------|
| `environment` | Environment (dev/staging/prod) |
| `cost-center` | Cost center for billing |
| `team` | Owning team |
| `project` | Project name |

### Example Tag Patch
```yaml
- type: FromCompositeFieldPath
  fromFieldPath: metadata.labels["crossplane.io/claim-name"]
  toFieldPath: spec.forProvider.tags[0].value
  transforms:
    - type: string
      string:
        type: Format
        fmt: "%s"
```

### Provider-Specific Tag Fields
| Provider | Tag Field Path |
|----------|---------------|
| AWS | `spec.forProvider.tags` (array of key/value) |
| Azure | `spec.forProvider.tags` (map) |
| GCP | `spec.forProvider.labels` (map) |

---

## 8. Connection Details

**ALWAYS publish connection details for resources that generate credentials or connection information.**

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

---

## 9. Security & Best Practices

- **Secrets**:
  - NEVER hardcode secrets in Compositions.
  - Use `writeConnectionSecretToRef` for all resources generating credentials.
- **Hard-coding**: Avoid hard-coding region-specific IDs (like AZ IDs) unless necessary. Use labels or transforms.
- **Tags**: Propagate common tags (CostCenter, Environment) from the Claim to all managed resources.

---

## 10. Example
```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: postgres-aws
  labels:
    provider: aws
    crossplane.io/xrd: xpostgresqlinstances.database.example.com
spec:
  compositeTypeRef:
    apiVersion: database.example.com/v1alpha1
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
