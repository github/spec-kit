# Kubernetes Technical Context

Context for managing Kubernetes-native resources via Crossplane `provider-kubernetes`.

---

## Documentation Lookup

### Use Web Search

No dedicated Kubernetes provider MCP. Use web search:

```
search_web
Query: "site:kubernetes.io <resource> API"
Query: "site:marketplace.upbound.io provider-kubernetes"
```

### Documentation URLs

| Source | URL |
|--------|-----|
| Kubernetes Docs | `https://kubernetes.io/docs/` |
| Upbound Marketplace | `https://marketplace.upbound.io/providers/crossplane-contrib/provider-kubernetes` |
| GitHub | `https://github.com/crossplane-contrib/provider-kubernetes` |

---

## Provider Package

| Provider | Package | Purpose |
|----------|---------|---------|
| Kubernetes | `provider-kubernetes` | Manage raw K8s objects |

---

## Common Patterns

### Object Resource

Deploy any Kubernetes manifest:

```yaml
apiVersion: kubernetes.crossplane.io/v1alpha1
kind: Object
metadata:
  name: my-configmap
spec:
  forProvider:
    manifest:
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: my-config
        namespace: default
      data:
        key: value
  providerConfigRef:
    name: default
```

### Dynamic Manifests

Use patches to inject values from the composite:

```yaml
patches:
  - type: FromCompositeFieldPath
    fromFieldPath: spec.parameters.namespace
    toFieldPath: spec.forProvider.manifest.metadata.namespace
```

---

## Provider Configuration

```yaml
apiVersion: kubernetes.crossplane.io/v1alpha1
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

| Use Case | Manifest Kind |
|----------|---------------|
| Application config | ConfigMap |
| Deploy secrets | Secret |
| Create namespace | Namespace |
| Service accounts | ServiceAccount |
