# GCP Cloud Context

GCP documentation and Crossplane provider context.

---

## MCP Tools

### Lookup Flow (Prioritized)

GCP does not have a dedicated provider MCP server. Use `search_web` as the primary tool:

1. **search_web** (Primary)

### 1. Primary: search_web

```
search_web("site:cloud.google.com <service> <topic>")
search_web("site:marketplace.upbound.io provider-gcp-<family> <Resource> apiVersion")
search_web("site:doc.crds.dev provider-gcp-<family> <Resource> v1beta1")

Examples:
- search_web("site:cloud.google.com Cloud SQL PostgreSQL configuration")
- search_web("site:marketplace.upbound.io provider-gcp-sql DatabaseInstance apiVersion")
- search_web("site:doc.crds.dev upbound provider-gcp DatabaseInstance v1beta1")
```

---

## Documentation URLs

| Source | URL Pattern |
|--------|-------------|
| GCP Docs | `https://cloud.google.com/docs` |
| Upbound Marketplace | `https://marketplace.upbound.io/providers/upbound/provider-gcp-<family>` |
| GitHub Provider | `https://github.com/upbound/provider-gcp` |
| CRD Docs | `https://doc.crds.dev/github.com/upbound/provider-gcp` |

---

## Provider Packages

GCP uses family providers:

| Family | Package | Common Resources |
|--------|---------|------------------|
| Storage | `provider-gcp-storage` | Bucket, BucketIAMMember |
| SQL | `provider-gcp-sql` | DatabaseInstance, Database, User |
| Container | `provider-gcp-container` | Cluster, NodePool |
| Compute | `provider-gcp-compute` | Network, Subnetwork, Firewall, Instance |
| Redis | `provider-gcp-redis` | Instance |
| PubSub | `provider-gcp-pubsub` | Topic, Subscription |
| BigQuery | `provider-gcp-bigquery` | Dataset, Table |

---

## API Patterns

### API Version Format

```
<family>.gcp.upbound.io/v1beta1
```

**Examples**:
- `storage.gcp.upbound.io/v1beta1`
- `sql.gcp.upbound.io/v1beta1`
- `container.gcp.upbound.io/v1beta1`

### Common forProvider Fields

| Field | Type | Description |
|-------|------|-------------|
| `project` | string | GCP project ID |
| `region` | string | GCP region (e.g., `us-central1`) |
| `location` | string | Location (some resources use this instead) |
| `labels` | map | Resource labels |

### Cross-Resource References

```yaml
# Selector (preferred in compositions)
networkSelector:
  matchControllerRef: true

# Direct reference
networkRef:
  name: my-network
```

---

## Provider Configuration

```yaml
apiVersion: gcp.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  projectID: my-gcp-project
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: gcp-secret
      key: creds
```
