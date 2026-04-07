# Tagging Standard

## Overview

This document defines mandatory tagging requirements for all cloud resources managed by this project.

> Run `/infrakit:setup` to configure your project-specific required tags.

---

## Required Tags (ALL resources)

Every managed resource MUST include these tags:

| Tag Key | Value | Description |
|---------|-------|-------------|
| `managed-by` | IaC tool name (e.g. `terraform`, `crossplane`) | Identifies the IaC tool managing this resource |
| `environment` | Target environment name | Environment tier (e.g. `dev`, `staging`, `prod`) |
[REQUIRED_TAGS]

<!-- Add project-specific required tags here. Examples:
| `cost-center` | Billing unit identifier | Billing allocation |
| `team`        | Owning team name        | Owning team |
| `project`     | Project identifier      | Project grouping |
-->

---

## Optional Tags

| Tag Key | Description |
|---------|-------------|
[OPTIONAL_TAGS]

<!-- Examples:
| `owner`      | Individual owner for escalation |
| `created-by` | CI/CD pipeline or user who created this |
-->

---

## Enforcement

All managed resources MUST carry the required tags above. Missing required tags is a `HIGH` severity violation.

- Never submit infrastructure code without verifying required tags are applied
- Verify tag presence as part of every review and compliance check
- Use provider-level or module-level tag defaults where supported to avoid per-resource repetition

---

## Governance

- Tag keys and allowed values are defined here — do not introduce new required tags without updating this document
- Changes to required tags must be reflected in all affected modules and compositions
