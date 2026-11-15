# Community Bundles

> [!NOTE]
> Community bundles are independently created and maintained by their respective authors. Maintainers only verify that submission metadata is complete and correctly formatted — they do **not review, audit, endorse, or support the bundle code or the components it installs**. Review bundle manifests, component catalogs, and source repositories before installation and use at your own discretion.

Bundles compose existing Spec Kit components — extensions, presets, workflows, and steps — into a single role or team stack. They are useful when a user should be able to install a tested set of components together instead of following several separate install commands.

Accepted community bundle entries are published in [`bundles/catalog.community.json`](https://github.com/github/spec-kit/blob/main/bundles/catalog.community.json) and listed below. The built-in community source is discovery-only: `specify bundle search` and `specify bundle info` can inspect entries, but installing by ID requires explicitly adding a vetted, install-allowed catalog. Explicit catalogs use a higher default precedence than the built-in community source. To submit a bundle for metadata validation, follow the [publishing guide](../bundles/publishing.md) and file a [Bundle Submission](https://github.com/github/spec-kit/issues/new?template=bundle_submission.yml) issue.

| Bundle | Purpose | Role or team | Provides | Required catalogs | URL |
|--------|---------|--------------|----------|-------------------|-----|
| Agentstandards Multi-Vendor Architecture | Installs a Codex-orchestrated, multi-vendor architecture council, its hard task gate, and the supporting Spec Kit workflow. | `architecture-governance` | 1 extension, 1 preset, 1 workflow | Documented | [agentstandards](https://github.com/bbjwz/agentstandards) |
| SicarioSpec Security & Governance Bundle | Secure-by-default governance bundle for GitHub Spec Kit. Enforces data classification, threat modeling, and code-owned verification gates. | `security-engineer` | 1 extension, 11 presets | Documented | [sicario-spec](https://github.com/dfirs1car1o/sicario-spec) |
| Spec Kit for Azure DevOps | The ado extension plus the ado-lifecycle workflow: an ADO story to Done with a human gate on every board or PR change. | `developer` | 1 extension, 1 workflow | Documented | [spec-kit-ado](https://github.com/praveenlavu/spec-kit-ado) |
| SpecAssay | Durable-ID promotion for stock Spec Kit: templates, Gate 2 refusal, and trace-manifest emission. | `developer` | 1 extension, 1 preset | Documented | [specassay](https://github.com/rdryfoos/specassay) |

## See also

- [Bundle overview](../bundles/overview.md)
- [Installing and inspecting bundles](../bundles/cli.md)
- [Catalog policies and component-source vetting](../bundles/catalogs.md)
- [Developing bundles](../bundles/developing.md)
- [Publishing, updating, and submission review scope](../bundles/publishing.md)
