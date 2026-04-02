# Azure Cloud Context

Azure documentation and Crossplane provider context.

---

## MCP Tools

### Lookup Flow (Prioritized)

Follow this fallback chain for Azure documentation:

1. **microsoft-learn MCP** (Primary)
2. **azure-best-practices MCP** (Co-Primary for security/architecture)
3. **search_web** (Final fallback)

### 1. Primary: microsoft-learn MCP

| Tool | Purpose | Example |
|------|---------|---------|
| `microsoft_docs_search` | Search Azure docs | `"Azure SQL Database encryption"` |
| `microsoft_docs_fetch` | Read full doc page | Use URL from search |
| `microsoft_code_sample_search` | Find code examples | `"Azure Storage Account Terraform"` |

**Usage:**
```
1. microsoft_docs_search
   Query: "Azure <service> <topic>"
   Example: "Azure PostgreSQL Flexible Server configuration"

2. microsoft_docs_fetch
   URL: <from search results>

3. microsoft_code_sample_search (optional)
   Query: "Azure <service> example"
```

### 2. Co-Primary: azure-best-practices MCP

**Use for security, compliance, and architectural best practices.**

| Tool | Purpose | Example |
|------|---------|---------|
| `search_best_practices` | Azure Well-Architected Framework | `"Azure SQL security best practices"` |
| `get_recommendation` | Specific recommendations | `"Azure Storage encryption"` |

**Usage:**
```
search_best_practices("Azure <service> security")
search_best_practices("Azure <service> high availability")
get_recommendation("Azure <architecture pattern>")
```

### 3. Final Fallback: search_web

```
search_web("site:marketplace.upbound.io provider-azure-<family> <Resource> apiVersion")
search_web("site:learn.microsoft.com azure <service> <topic>")
search_web("site:doc.crds.dev provider-azure-<family> <Resource> v1beta1")

Examples:
- search_web("site:marketplace.upbound.io provider-azure-dbforpostgresql FlexibleServer apiVersion")
- search_web("site:learn.microsoft.com azure sql database security")
- search_web("site:doc.crds.dev upbound provider-azure MSSQLDatabase v1beta1")
```

---

## Documentation URLs

| Source | URL Pattern |
|--------|-------------|
| Microsoft Learn | `https://learn.microsoft.com/en-us/azure/<service>/` |
| Upbound Marketplace | `https://marketplace.upbound.io/providers/upbound/provider-azure-<family>` |
| GitHub Provider | `https://github.com/upbound/provider-azure` |
| CRD Docs | `https://doc.crds.dev/github.com/upbound/provider-azure` |

---

## Provider Packages

Azure uses family providers:

| Family | Package | Common Resources |
|--------|---------|------------------|
| Storage | `provider-azure-storage` | Account, Container, Blob |
| SQL | `provider-azure-sql` | MSSQLServer, MSSQLDatabase |
| ContainerService | `provider-azure-containerservice` | KubernetesCluster, KubernetesClusterNodePool |
| Network | `provider-azure-network` | VirtualNetwork, Subnet, SecurityGroup |
| Cache | `provider-azure-cache` | RedisCache, RedisFirewallRule |
| DBforPostgreSQL | `provider-azure-dbforpostgresql` | FlexibleServer, FlexibleServerDatabase |
| KeyVault | `provider-azure-keyvault` | Vault, Secret, Key |

---

## API Patterns

### API Version Format

```
<family>.azure.upbound.io/v1beta1
```

**Examples**:
- `storage.azure.upbound.io/v1beta1`
- `sql.azure.upbound.io/v1beta1`
- `containerservice.azure.upbound.io/v1beta1`

### Common forProvider Fields

| Field | Type | Description |
|-------|------|-------------|
| `location` | string | Azure region (e.g., `eastus`, `westeurope`) |
| `resourceGroupName` | string | Resource group name |
| `resourceGroupNameRef` | object | Reference to ResourceGroup |
| `tags` | map | Resource tags |

### Cross-Resource References

```yaml
# Selector (preferred in compositions)
resourceGroupNameSelector:
  matchControllerRef: true

# Direct reference
resourceGroupNameRef:
  name: my-resource-group
```

---

## Provider Configuration

```yaml
apiVersion: azure.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: azure-secret
      key: creds
```
