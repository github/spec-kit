# Crossplane Technical Context

Core Crossplane concepts, patterns, and functions for XRDs, Compositions, and advanced features.

---

## Core Concepts

### CompositeResourceDefinition (XRD)

Defines the API for custom abstractions.

| Field | Description |
|-------|-------------|
| `spec.group` | API group (e.g., `platform.example.com`) |
| `spec.names.kind` | CamelCase, starts with `X` (e.g., `XDatabase`) |
| `spec.names.plural` | Lowercase plural (e.g., `xdatabases`) |
| `spec.claimNames` | User-facing Claim kind (without `X` prefix) |
| `spec.versions[].schema` | OpenAPIv3 schema for parameters and status |

### Composition

Maps the XRD to managed resources.

| Field | Description |
|-------|-------------|
| `spec.compositeTypeRef` | Links to the XRD (apiVersion + kind) |
| `spec.mode` | `Pipeline` (recommended) or `Resources` |
| `spec.pipeline[]` | Function steps for resource generation |

---

## Patch Types

| Type | Direction | Use Case |
|------|-----------|----------|
| `FromCompositeFieldPath` | Composite → Managed | Pass user inputs |
| `ToCompositeFieldPath` | Managed → Composite | Expose outputs |
| `CombineFromComposite` | Multiple inputs → Managed | Merge/format values |
| `CombineToComposite` | Multiple outputs → Composite | Aggregate status |
| `PatchSet` | N/A | Reusable patch groups |

---

## Transforms

| Type | Description | Example |
|------|-------------|---------|
| `map` | Map string to value | `"small" → "t3.micro"` |
| `string` | Format string | `fmt: "%s-bucket"` |
| `math` | Arithmetic | `multiply: 1024` |
| `convert` | Type conversion | `string → int` |
| `match` | Conditional mapping | Pattern-based transforms |

---

## Pipeline Mode

**Always use Pipeline mode with functions** for maximum flexibility and power.

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: example-composition
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: XExample
  
  mode: Pipeline
  pipeline:
    - step: patch-and-transform
      functionRef:
        name: crossplane-contrib-function-patch-and-transform
      input:
        apiVersion: pt.fn.crossplane.io/v1beta1
        kind: Resources
        resources:
          - name: resource-name
            base:
              apiVersion: <provider-api>
              kind: <ManagedResource>
              spec:
                forProvider:
                  # ...
            patches:
              - type: FromCompositeFieldPath
                fromFieldPath: spec.parameters.field
                toFieldPath: spec.forProvider.field
```

---

## Composition Functions

> **Best Practice**: Use functions liberally! They provide powerful capabilities that simplify complex compositions and enable dynamic behavior.

### Function Recommendation Guide

| Use Case | Recommended Function |
|----------|---------------------|
| Basic patching and transforms | `function-patch-and-transform` |
| Complex templating with full language | `function-go-templating` |
| Python scripting for complex logic | `function-python` |
| Ordering resource creation | `function-sequencer` |
| Automatic resource tagging | `function-auto-tag-manager` |
| Custom readiness conditions | `function-status-transformer` |
| Fetching existing resources | `function-extra-resources` |

---

### function-patch-and-transform

The standard function for patching and transforming resources in Pipeline mode.

| Property | Value |
|----------|-------|
| **Package** | `xpkg.upbound.io/crossplane-contrib/function-patch-and-transform` |
| **Version** | `v0.7.0` (latest) |
| **GitHub** | [crossplane-contrib/function-patch-and-transform](https://github.com/crossplane-contrib/function-patch-and-transform) |
| **Docs** | [Crossplane Docs - Patch and Transform](https://docs.crossplane.io/latest/concepts/patch-and-transform/) |

**When to use**: Basic to moderate composition complexity with standard patching needs.

```yaml
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-patch-and-transform
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-patch-and-transform:v0.7.0
```

---

### function-go-templating

Full Go templating support for complex compositions. Access to Sprig functions.

| Property | Value |
|----------|-------|
| **Package** | `xpkg.upbound.io/crossplane-contrib/function-go-templating` |
| **Version** | `v0.7.0` (latest) |
| **GitHub** | [crossplane-contrib/function-go-templating](https://github.com/crossplane-contrib/function-go-templating) |
| **Docs** | [GitHub README](https://github.com/crossplane-contrib/function-go-templating#readme) |

**When to use**: 
- Complex conditional logic
- Loops and iterations
- Dynamic resource generation
- String manipulation beyond basic transforms

```yaml
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-go-templating
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-go-templating:v0.7.0
```

**Example Pipeline Step**:

```yaml
- step: render-templates
  functionRef:
    name: crossplane-contrib-function-go-templating
  input:
    apiVersion: gotemplating.fn.crossplane.io/v1beta1
    kind: GoTemplate
    source: Inline
    inline:
      template: |
        apiVersion: s3.aws.upbound.io/v1beta1
        kind: Bucket
        metadata:
          name: {{ .observed.composite.resource.metadata.name }}-bucket
          annotations:
            crossplane.io/external-name: {{ .observed.composite.resource.spec.bucketName }}
        spec:
          forProvider:
            region: {{ .observed.composite.resource.spec.region }}
            {{- if eq .observed.composite.resource.spec.environment "production" }}
            versioning:
              - enabled: true
            {{- end }}
```

---

### function-python

Write composition logic in Python for maximum flexibility.

| Property | Value |
|----------|-------|
| **Package** | `xpkg.upbound.io/crossplane-contrib/function-python` |
| **Version** | `v0.3.0` (latest) |
| **GitHub** | [crossplane-contrib/function-python](https://github.com/crossplane-contrib/function-python) |
| **Docs** | [GitHub README](https://github.com/crossplane-contrib/function-python#readme) |

**When to use**:
- Complex business logic
- External API calls within composition
- Data transformations requiring full programming language
- When Go templates become unwieldy

```yaml
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-python
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-python:v0.3.0
```

---

### function-sequencer

Control the order of resource creation and deletion.

| Property | Value |
|----------|-------|
| **Package** | `xpkg.upbound.io/crossplane-contrib/function-sequencer` |
| **Version** | `v0.2.0` (latest) |
| **GitHub** | [crossplane-contrib/function-sequencer](https://github.com/crossplane-contrib/function-sequencer) |
| **Docs** | [GitHub README](https://github.com/crossplane-contrib/function-sequencer#readme) |

**When to use**:
- Resources depend on each other (e.g., create VPC before Subnet)
- Need to wait for one resource before creating another
- Controlled deletion order

```yaml
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-sequencer
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-sequencer:v0.2.0
```

**Example Pipeline Step**:

```yaml
- step: sequence-resources
  functionRef:
    name: crossplane-contrib-function-sequencer
  input:
    apiVersion: sequencer.fn.crossplane.io/v1beta1
    kind: Sequence
    rules:
      - sequence:
          - vpc
          - subnet
          - security-group
      - sequence:
          - subnet
          - rds-instance
```

---

### function-auto-tag-manager

Automatically apply tags/labels to all managed resources.

| Property | Value |
|----------|-------|
| **Package** | `xpkg.upbound.io/crossplane-contrib/function-auto-tag-manager` |
| **Version** | `v0.1.0` (latest) |
| **GitHub** | [crossplane-contrib/function-auto-tag-manager](https://github.com/crossplane-contrib/function-auto-tag-manager) |
| **Docs** | [GitHub README](https://github.com/crossplane-contrib/function-auto-tag-manager#readme) |

**When to use**:
- Enforce organizational tagging policies
- Apply common tags to all resources
- Cost allocation tracking
- Environment identification

```yaml
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-auto-tag-manager
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-auto-tag-manager:v0.1.0
```

**Example Pipeline Step**:

```yaml
- step: add-tags
  functionRef:
    name: crossplane-contrib-function-auto-tag-manager
  input:
    apiVersion: tagging.fn.crossplane.io/v1beta1
    kind: Tags
    tags:
      - type: FromCompositeFieldPath
        fromFieldPath: spec.environment
        key: Environment
      - type: Value
        key: ManagedBy
        value: crossplane
      - type: Value
        key: CostCenter
        value: platform-team
```

---

### function-status-transformer

Customize readiness conditions and status transformations.

| Property | Value |
|----------|-------|
| **Package** | `xpkg.upbound.io/crossplane-contrib/function-status-transformer` |
| **Version** | `v0.2.0` (latest) |
| **GitHub** | [crossplane-contrib/function-status-transformer](https://github.com/crossplane-contrib/function-status-transformer) |
| **Docs** | [GitHub README](https://github.com/crossplane-contrib/function-status-transformer#readme) |

**When to use**:
- Custom readiness conditions
- Aggregate status from multiple resources
- Transform status fields before exposing

```yaml
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-status-transformer
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-status-transformer:v0.2.0
```

---

### function-extra-resources

Fetch existing resources in the cluster for use in compositions.

| Property | Value |
|----------|-------|
| **Package** | `xpkg.upbound.io/crossplane-contrib/function-extra-resources` |
| **Version** | `v0.2.0` (latest) |
| **GitHub** | [crossplane-contrib/function-extra-resources](https://github.com/crossplane-contrib/function-extra-resources) |
| **Docs** | [GitHub README](https://github.com/crossplane-contrib/function-extra-resources#readme) |

**When to use**:
- Reference existing ConfigMaps or Secrets
- Lookup ProviderConfigs dynamically
- Access cluster-level resources in compositions
- Cross-reference between XRs

```yaml
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-extra-resources
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-extra-resources:v0.2.0
```

**Example Pipeline Step**:

```yaml
- step: fetch-extra-resources
  functionRef:
    name: crossplane-contrib-function-extra-resources
  input:
    apiVersion: extra-resources.fn.crossplane.io/v1beta1
    kind: ExtraResources
    resources:
      - kind: ConfigMap
        into: network-config
        apiVersion: v1
        type: Selector
        selector:
          matchLabels:
            app.kubernetes.io/component: network-config
```

---

## Crossplane Context

Context allows passing data between pipeline steps and accessing composite resource information.

### Accessing Context in Go Templates

```yaml
# Access the composite resource
{{ .observed.composite.resource.metadata.name }}
{{ .observed.composite.resource.spec.parameters.region }}

# Access observed managed resources
{{ (index .observed.resources "my-bucket").resource.status.atProvider.arn }}

# Access extra resources (from function-extra-resources)
{{ (index .extraResources "network-config").data.vpcId }}
```

### Common Context Fields

| Field | Description |
|-------|-------------|
| `.observed.composite.resource` | The XR/Claim being reconciled |
| `.observed.composite.connectionDetails` | Connection details from the XR |
| `.observed.resources` | Map of observed managed resources by name |
| `.desired.composite.resource` | Desired state of the XR |
| `.desired.resources` | Map of desired managed resources |
| `.extraResources` | Resources fetched by function-extra-resources |
| `.context` | Pipeline context data |

---

## EnvironmentConfig

EnvironmentConfigs provide a way to inject external configuration into compositions.

### Creating an EnvironmentConfig

```yaml
apiVersion: apiextensions.crossplane.io/v1alpha1
kind: EnvironmentConfig
metadata:
  name: production-config
data:
  region: us-east-1
  vpcId: vpc-12345
  environment: production
  defaultTags:
    Team: platform
    CostCenter: engineering
```

### Using EnvironmentConfig in Composition

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: database-aws
spec:
  environment:
    environmentConfigs:
      - type: Reference
        ref:
          name: production-config
      - type: Selector
        selector:
          matchLabels:
            - key: environment
              type: FromCompositeFieldPath
              valueFromFieldPath: spec.environment

  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: XDatabase
  
  mode: Pipeline
  pipeline:
    - step: patch-and-transform
      functionRef:
        name: crossplane-contrib-function-patch-and-transform
      input:
        apiVersion: pt.fn.crossplane.io/v1beta1
        kind: Resources
        resources:
          - name: rds-instance
            base:
              # ...
            patches:
              # Patch from EnvironmentConfig
              - type: FromEnvironmentFieldPath
                fromFieldPath: data.region
                toFieldPath: spec.forProvider.region
              - type: FromEnvironmentFieldPath
                fromFieldPath: data.vpcId
                toFieldPath: spec.forProvider.vpcSecurityGroupIds[0]
```

### EnvironmentConfig Use Cases

| Use Case | Description |
|----------|-------------|
| **Environment-specific config** | Different VPCs, regions per environment |
| **Shared defaults** | Common tags, security settings |
| **External data injection** | Data from external sources |
| **Multi-tenancy** | Tenant-specific configurations |

---

## Recommended Pipeline Patterns

### Pattern 1: Basic Composition

```yaml
pipeline:
  - step: patch-and-transform
    functionRef:
      name: crossplane-contrib-function-patch-and-transform
```

### Pattern 2: With Sequencing

```yaml
pipeline:
  - step: patch-and-transform
    functionRef:
      name: crossplane-contrib-function-patch-and-transform
  - step: sequence
    functionRef:
      name: crossplane-contrib-function-sequencer
```

### Pattern 3: Complex with Templating and Tagging

```yaml
pipeline:
  - step: fetch-context
    functionRef:
      name: crossplane-contrib-function-extra-resources
  - step: render-resources
    functionRef:
      name: crossplane-contrib-function-go-templating
  - step: add-tags
    functionRef:
      name: crossplane-contrib-function-auto-tag-manager
  - step: sequence
    functionRef:
      name: crossplane-contrib-function-sequencer
```

---

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| XRD name | `x<plural>.<group>` | `xdatabases.platform.example.com` |
| XR kind | `X<CamelCase>` | `XDatabase` |
| Claim kind | `<CamelCase>` | `Database` |
| Composition | `<resource>-<provider>` | `database-aws` |

---

## Versioning

| Stage | When to Use |
|-------|-------------|
| `v1alpha1` | Initial development |
| `v1beta1` | API stabilizing |
| `v1` | Production-ready |

---

## Function Installation Quick Reference

```bash
# Install commonly used functions
cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-patch-and-transform
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-patch-and-transform:v0.7.0
---
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-go-templating
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-go-templating:v0.7.0
---
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-sequencer
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-sequencer:v0.2.0
---
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-auto-tag-manager
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-auto-tag-manager:v0.1.0
---
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: crossplane-contrib-function-extra-resources
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-extra-resources:v0.2.0
EOF
```

---

## Lookup Resources

### Schema Verification and Documentation Lookup

**CRITICAL**: You MUST verify exact `apiVersion`, `kind`, and schema fields for every managed resource. Use the MCP fallback chain to ensure 100% accuracy.

### Lookup Flow (Prioritized)

Follow this fallback chain for Crossplane provider schema verification:

1. **search_web** (Primary - use `site:doc.crds.dev` for authoritative schemas)

### 1. Primary: search_web with doc.crds.dev

**Why doc.crds.dev is authoritative**: It hosts CRD schemas from provider repositories containing exact `apiVersion` strings, `kind` names, required/optional `spec.forProvider` fields, types, and validation rules.

**Target Repositories:**
- `upbound/provider-aws` or `crossplane-contrib/provider-aws`
- `upbound/provider-azure` or `crossplane-contrib/provider-azure`
- `upbound/provider-gcp` or `crossplane-contrib/provider-gcp`
- `crossplane/crossplane` (for core resources)

**Schema Verification Queries:**

| Purpose | Query Pattern | Example |
|---------|---------------|---------|
| **CRD Schema** | `site:doc.crds.dev upbound/provider-<p> <group> <Kind> <version>` | `site:doc.crds.dev upbound provider-aws rds Instance v1beta1` |
| **API Versions** | `site:marketplace.upbound.io <provider> <resource> apiVersion` | `site:marketplace.upbound.io provider-aws-rds Instance apiVersion` |
| **Function Docs** | `site:github.com crossplane <function-name>` | `site:github.com crossplane function-patch-and-transform` |
| **Best Practices** | `crossplane <topic> best practices` | `crossplane composition pipeline best practices` |

**Example Queries by Provider:**

| Provider | Query | Purpose |
|----------|-------|---------|
| **AWS S3** | `search_web("site:doc.crds.dev upbound provider-aws s3 Bucket v1beta1")` | Find S3 Bucket schema |
| **Azure SQL** | `search_web("site:doc.crds.dev upbound provider-azure sql MSSQLDatabase v1beta1")` | Find Azure SQL schema |
| **GCP Storage** | `search_web("site:doc.crds.dev upbound provider-gcp storage Bucket v1beta1")` | Find GCP Bucket schema |
| **Crossplane XRD** | `search_web("site:docs.crossplane.io CompositeResourceDefinition spec fields")` | Core XRD types |

**What to Extract from doc.crds.dev:**

```go
// Example from provider-aws/apis/rds/v1beta1/instance_types.go (via doc.crds.dev)

// GROUP: rds.aws.upbound.io
// VERSION: v1beta1
// KIND: Instance

type InstanceParameters struct {
    // Extract these exact field names for spec.forProvider:
    AllocatedStorage       *float64                `json:"allocatedStorage,omitempty"`
    Engine                 *string                 `json:"engine"`  // Required (no omitempty)
    EngineVersion          *string                 `json:"engineVersion,omitempty"`
    InstanceClass          *string                 `json:"instanceClass"`  // Required
    // ... more fields
}
```

**Result**: EXACT schema with no guessed field names or hallucinated apiVersions.

### Phase 0: Schema Verification Protocol

**BEFORE writing ANY YAML**, follow this protocol:

```
User Request: "Create an AWS RDS database"

Phase 0 - Schema Verification (MANDATORY):

1. search_web (Primary):
   Query: "site:doc.crds.dev upbound provider-aws rds Instance v1beta1"
   Extract EXACT:
   ✅ apiVersion: "rds.aws.upbound.io/v1beta1"
   ✅ kind: "Instance"
   ✅ Required fields: engine, instanceClass
   ✅ Optional fields: allocatedStorage, engineVersion, ...

2. Fallback (if doc.crds.dev unreachable):
   search_web("site:marketplace.upbound.io provider-aws Instance apiVersion")

Result: 100% accurate schema → Zero hallucinations in generated YAML
```

### Recommended Searches by Topic

| Topic | Tool | Query |
|-------|------|-------|
| **AWS Provider Schema** | search_web | `site:doc.crds.dev upbound provider-aws rds Instance v1beta1` |
| **Azure Provider Schema** | search_web | `site:doc.crds.dev upbound provider-azure sql MSSQLDatabase v1beta1` |
| **GCP Provider Schema** | search_web | `site:doc.crds.dev upbound provider-gcp sql DatabaseInstance v1beta1` |
| **Function Documentation** | search_web | `site:docs.crossplane.io composition functions patch-and-transform` |
| **Best Practices** | search_web | `crossplane composition best practices` |

---

## Best Practices

### XRD Design

| Practice | Description |
|----------|-------------|
| **Use descriptive field names** | `storageGB` not `size`, `engineVersion` not `ver` |
| **Add descriptions to all fields** | Every property should have a `description` in schema |
| **Use enums for constrained values** | `enum: [small, medium, large]` instead of freeform strings |
| **Provide sensible defaults** | Reduce required fields, use `default:` in schema |
| **Version appropriately** | Start with `v1alpha1`, promote to `v1beta1` then `v1` |
| **Use connectionSecretKeys** | Explicitly define what secrets the XR exposes |
| **Add categories** | Include `crossplane` and `composite` for discoverability |

### Composition Design

| Practice | Description |
|----------|-------------|
| **Always use Pipeline mode** | `mode: Pipeline` is more flexible and maintainable |
| **Name resources meaningfully** | Use descriptive names like `primary-database` not `resource-0` |
| **Keep functions focused** | One function per concern (patching, sequencing, tagging) |
| **Use function-sequencer for dependencies** | Explicit ordering prevents race conditions |
| **Apply tags consistently** | Use `function-auto-tag-manager` or explicit patches |
| **Always set providerConfigRef** | Never rely on implicit defaults |
| **Use PatchSets for repeated patches** | DRY principle for common patches |

### Security Best Practices

| Practice | Description |
|----------|-------------|
| **Never hardcode secrets** | Use `writeConnectionSecretToRef` and `connectionDetails` |
| **Use least privilege** | ProviderConfigs should have minimal required permissions |
| **Encrypt by default** | Enable encryption at rest and in transit |
| **Private networking** | Resources should not be publicly accessible unless required |
| **Audit trail** | Tag resources with claim name/namespace for traceability |
| **Separate ProviderConfigs** | Different configs for different environments/permissions |

### Operational Best Practices

| Practice | Description |
|----------|-------------|
| **Set deletionPolicy appropriately** | `Delete` for ephemeral, `Orphan` for stateful |
| **Use observability** | Expose status fields for monitoring |
| **Implement readiness checks** | Use proper readiness conditions |
| **Document everything** | README, inline comments, examples |
| **Version control compositions** | GitOps for composition management |
| **Test with `crossplane render`** | Validate before applying |

### Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| Hardcoded regions/zones | Inflexible, breaks multi-region | Use parameters or EnvironmentConfig |
| Giant single compositions | Hard to maintain and test | Break into smaller XRDs |
| No default values | Poor UX, too many required fields | Sensible defaults for most fields |
| Ignoring status | Users can't see what's happening | Expose meaningful status fields |
| No connection secrets | Users can't use the resource | Always configure connectionDetails |
| Resource name collisions | Creates conflicts | Include XR name in resource names |

---

## Common Patterns

### Pattern: Resource Naming with Hash

Ensure unique resource names that won't collide:

```yaml
metadata:
  name: {{ .observed.composite.resource.metadata.name }}-{{ .observed.composite.resource.metadata.uid | sha256sum | trunc 8 }}
```

### Pattern: Conditional Resources

Only create resources based on parameters:

```yaml
{{- if eq .observed.composite.resource.spec.parameters.enableReplica true }}
apiVersion: rds.aws.upbound.io/v1beta1
kind: Instance
metadata:
  name: {{ .observed.composite.resource.metadata.name }}-replica
spec:
  # ...
{{- end }}
```

### Pattern: Cross-Resource References

Reference outputs from other resources in the composition:

```yaml
patches:
  - type: FromCompositeFieldPath
    fromFieldPath: status.vpcId
    toFieldPath: spec.forProvider.vpcId
    policy:
      fromFieldPath: Required
```

### Pattern: Environment-Based Defaults

Use EnvironmentConfig for environment-specific values:

```yaml
- type: FromEnvironmentFieldPath
  fromFieldPath: data.defaultInstanceClass
  toFieldPath: spec.forProvider.instanceClass
```

### Pattern: Aggregate Connection Secrets

Combine secrets from multiple resources:

```yaml
connectionDetails:
  - name: host
    type: FromFieldPath
    fromFieldPath: status.atProvider.endpoint
  - name: port
    type: FromValue
    value: "5432"
  - name: username
    type: FromConnectionSecretKey
    fromConnectionSecretKey: username
  - name: password
    type: FromConnectionSecretKey
    fromConnectionSecretKey: password
```

