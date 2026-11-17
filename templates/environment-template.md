# Runtime environment design

**Revision**: [revision] | **Architecture**: [revision/path] | **Requirements**: [links]

## Workload and sizing assumptions

[Demand, concurrency, data growth, availability, residency and retention.
Recommendations derive from requirements, independently of existing inventory.]

## Logical deployment assets

Asset IDs describe roles, not purchased machines. Specify OS/version and runtime
for every component. For a provider-managed OS, say so and give the service/runtime
version. Resource keys include units; all quantities are positive numbers.
Managed services may use quotas instead of invented server hardware. Recommended
values must be at least minimum. Replace example values using sizing rationale.

```json
{
  "schema_version": 1,
  "assets": [
    {
      "id": "APP01",
      "components": ["API"],
      "os": "[specific OS or provider-managed]",
      "os_version": "[version/support policy]",
      "runtime": "[runtime and version]",
      "minimum": {"vcpu": 2, "memory_gib": 4, "storage_gib": 20},
      "recommended": {"vcpu": 4, "memory_gib": 8, "storage_gib": 40}
    }
  ]
}
```

## Topology and placement

[Asset count, replicas per asset, component allocation, co-location and separation.
Network paths, cloud/region constraints, storage, backup, DNS/TLS, ports, runtime
accounts and secrets references, without credentials.]

## Compatibility and capacity rationale

[OS/runtime compatibility for each component, minimum operating limits, recommended
headroom, totals for co-located services and failure domains. No empirical claims.]

## Change impact

[Approved-design changes and affected plans/deployments. Actual target selection,
provisioning and installation occur only in deployment.]
