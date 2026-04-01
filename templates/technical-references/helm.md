# Helm Technical Context

Context for managing Helm chart releases via Crossplane `provider-helm`.

---

## Documentation Lookup

### Use Web Search

No dedicated Helm MCP server. Use web search for lookups:

```
search_web
Query: "site:helm.sh <chart_name>"
Query: "site:artifacthub.io <chart_name>"
Query: "site:marketplace.upbound.io provider-helm"
```

### Documentation URLs

| Source | URL |
|--------|-----|
| Helm Hub | `https://artifacthub.io/` |
| Upbound Marketplace | `https://marketplace.upbound.io/providers/crossplane-contrib/provider-helm` |
| GitHub | `https://github.com/crossplane-contrib/provider-helm` |

---

## Provider Package

| Provider | Package | Purpose |
|----------|---------|---------|
| Helm | `provider-helm` | Manage Helm charts and releases |

---

## Common Patterns

### Release Resource

Deploy a Helm chart:

```yaml
apiVersion: helm.crossplane.io/v1beta1
kind: Release
metadata:
  name: my-release
spec:
  forProvider:
    chart:
      name: redis
      repository: https://charts.bitnami.com/bitnami
      version: 17.3.14
    namespace: default
    values:
      architecture: standalone
      auth:
        enabled: true
  providerConfigRef:
    name: default
```

### Chart Sources

| Source | Configuration |
|--------|---------------|
| Helm Repository | `chart.repository` + `chart.name` + `chart.version` |
| OCI Registry | `chart.repository` (oci://...) + `chart.name` |

### Values Management

```yaml
spec:
  forProvider:
    # Inline values
    values:
      key: value
    
    # Values from ConfigMap
    valuesFrom:
      - configMapKeyRef:
          name: my-values
          key: values.yaml
```

---

## Provider Configuration

```yaml
apiVersion: helm.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: kubeconfig-secret
      key: kubeconfig
```

---

## Use Cases

| Use Case | Chart Examples |
|----------|----------------|
| Database | bitnami/postgresql, bitnami/redis |
| Monitoring | prometheus-community/kube-prometheus-stack |
| Ingress | ingress-nginx, traefik |
