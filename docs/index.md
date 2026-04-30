# InfraKit

*Build production-ready infrastructure faster.*

**An infrastructure-first toolkit that brings Constraint-Driven Development to IaC — specify what you need, let agents generate it.**

## What is InfraKit?

InfraKit applies **Constraint-Driven Development** to Infrastructure as Code. Instead of writing YAML by hand, you describe what infrastructure you need — InfraKit's AI agent workflow produces production-ready manifests through a structured **spec → plan → implement → review** pipeline.

Each infrastructure resource gets its own **track** under `.infrakit_tracks/tracks/`, containing the spec, plan, and tasks. Multiple tracks can run in parallel, and every step is transparent and user-controlled.

InfraKit supports **Crossplane** (Kubernetes-native IaC) and **Terraform** (HashiCorp IaC). Support for Pulumi, CloudFormation, and OpenTofu is on the roadmap.

## Getting Started

- [Installation Guide](installation.md)
- [Quick Start Guide](quickstart.md)
- [Upgrade Guide](upgrade.md)
- [Local Development](local-development.md)

## Core Philosophy

Constraint-Driven Development for infrastructure means:

- **Spec before YAML** — define *what* the resource must do before any code is written
- **Multi-persona review** — Cloud Solutions Engineer, Cloud Architect, Cloud Security Engineer, and IaC Engineer each own a distinct phase
- **Never guess schemas** — all `apiVersion` and field names are verified against provider documentation
- **Standards enforced** — mandatory tagging, Pipeline mode, and `providerConfigRef` baked in from the start

## Development Phases

| Phase | Focus | Key Activities |
|-------|-------|----------------|
| **Greenfield** | New infrastructure resources | Spec, architect review, security review, plan, implement, code review |
| **Brownfield** | Update existing compositions | Scan existing code, generate update spec, review changes, implement delta |

## Agent Personas

InfraKit uses four specialized AI personas, each with a distinct scope:

| Persona | Role | Phase |
|---------|------|-------|
| **Cloud Solutions Engineer** | Gathers requirements, writes spec | Phase 1 |
| **Cloud Architect** | Reviews architecture, reliability, cost | Phase 2 |
| **Cloud Security Engineer** | Audits against compliance frameworks (SOC2, HIPAA, etc.) | Phase 2.5 |
| **IaC Engineer** | Implements spec to verified Crossplane/Terraform code | Phase 3 |


## Contributing

See the [Contributing Guide](https://github.com/neelneelpurk/infrakit/blob/main/CONTRIBUTING.md) for how to contribute.

## Credits

InfraKit is inspired by and built upon the foundational work of the [speckit](https://github.com/github/speckit) project. We credit `speckit` for providing the base for this project's architecture and methodology.

## Support

Open a [GitHub issue](https://github.com/neelneelpurk/infrakit/issues/new) for support, bug reports, or feature requests.
