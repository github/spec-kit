# Crossplane example — `XPostgreSQLInstance`

Reproduce a complete, end-to-end InfraKit run for a Crossplane composite resource against a fictional platform team (Acme Corp) that requires Postgres instances on AWS RDS with per-instance customer-managed KMS keys, env-defaulted Multi-AZ + deletion-protection, and connection-secret publishing into the claiming namespace.

This directory contains everything you need to *re-run* the workflow yourself:

- The Acme project standards under [`.infrakit/`](./.infrakit/) — context, coding style, tagging standard.
- The final composition produced by the run under [`compositions/xpostgresql-instance/`](./compositions/xpostgresql-instance/).

The intermediate artifacts (spec, plan, tasks, reviews) are **not** committed — they're generated when you run the workflow.

---

## Prerequisites

- [InfraKit CLI](https://pypi.org/project/infrakit-cli/) — install with `uv tool install infrakit-cli` (or `pipx install infrakit-cli`).
- An AI coding agent — this guide uses Claude Code; substitute your favourite (see the [supported list](../../README.md#-supported-ai-coding-agents)).
- [`kubectl`](https://kubernetes.io/docs/tasks/tools/) — for YAML syntax validation.
- (Optional, for live testing) a cluster with [Crossplane v1.15+](https://docs.crossplane.io/latest/software/install/) and the `upbound/provider-aws-rds` + `upbound/provider-aws-kms` providers installed. [`kind`](https://kind.sigs.k8s.io/) works locally.
- (Optional) the [`crossplane` CLI](https://docs.crossplane.io/latest/cli/) for `crossplane render`.

---

## Run the workflow against this scenario

### 1. Copy the example into a fresh project

```bash
cp -r examples/crossplane/ /tmp/acme-platform
cd /tmp/acme-platform
```

The `.infrakit/` directory is already populated with Acme's standards. The `compositions/` directory contains the *final* output for reference — feel free to delete it before re-running:

```bash
rm -rf compositions
```

### 2. Bootstrap the project for your AI agent

```bash
infrakit init --here --ai claude --iac crossplane --script sh --force --no-git
```

This is idempotent: existing `.infrakit/*.md` files are preserved. The command writes per-agent slash-command files into `.claude/commands/` (or `.gemini/commands/`, `.github/agents/`, etc.) based on `--ai`.

### 3. Start your AI agent in this directory

```bash
claude              # or: gemini, cursor-agent, copilot, etc.
```

You should see `/infrakit:*` slash commands available.

### 4. Walk through the multi-persona pipeline

Run these commands in order. Each one writes its output to `.infrakit_tracks/tracks/<track-name>/`.

```text
/infrakit:new_composition XPostgreSQLInstance ./compositions/xpostgresql-instance
```

This launches the four-persona pipeline:

- **Cloud Solutions Engineer** — asks clarifying questions about the resource's API group, parameters, connection-secret keys, networking. Use the answers below ("Reference inputs") to reproduce the example.
- **Cloud Architect** — presents 2–3 design options with cost/reliability trade-offs (per-instance KMS vs shared, in-line networking vs caller-supplied subnet/SG). Pick the per-instance KMS option.
- **Cloud Security Engineer** — asks which compliance frameworks apply. For this example, select **SOC 2 + PCI-DSS**.

Once the spec is confirmed:

```text
/infrakit:plan <track-name>
/infrakit:implement <track-name>
/infrakit:analyze <track-name>
/infrakit:architect-review <track-name>
/infrakit:security-review <track-name>
/infrakit:review ./compositions/xpostgresql-instance
```

`<track-name>` follows the format `xpostgresql-instance-<YYYYMMDD-HHMMSS>`.

### 5. Verify the produced composition

```bash
cd compositions/xpostgresql-instance

# Syntactic validation (no cluster needed):
python3 -c 'import yaml,sys; [list(yaml.safe_load_all(open(f))) for f in sys.argv[1:]]' \
  definition.yaml composition.yaml examples/claim-dev.yaml examples/claim-prod.yaml

# Full render (needs the crossplane CLI and function image cached):
crossplane render examples/claim-dev.yaml composition.yaml functions.yaml
```

Note: `functions.yaml` is not produced by InfraKit — it's a single-file manifest declaring `function-patch-and-transform` for the local `crossplane render` step. See the [function-patch-and-transform docs](https://github.com/crossplane-contrib/function-patch-and-transform).

---

## Reference inputs

When the Cloud Solutions Engineer asks clarifying questions, use these answers to reproduce the bundled composition verbatim:

| Question | Answer |
|---|---|
| API group | `database.platform.acme.com` |
| XRD kind / Claim kind | `XPostgreSQLInstance` / `PostgreSQLInstance` |
| Resource type | Claim (namespace-scoped, backed by cluster-scoped XR) |
| Cloud provider / service | AWS RDS PostgreSQL |
| Engine version | `16.3` default; user can override via parameter |
| Encryption | Per-instance customer-managed KMS key, rotation enabled, 30-day deletion window |
| Public access | `publicly_accessible: false`; never overridable |
| Multi-AZ | Defaults from environment (prod = `true`, else `false`); user can override via parameter |
| Deletion protection | Same pattern as Multi-AZ |
| Networking | Caller-supplied `subnetGroupName` + `securityGroupIds` (composition does not create networking) |
| Connection secret keys | `host, port, username, password, database, endpoint` |
| Admin password | Auto-generated via `autoGeneratePassword + passwordSecretRef` (shared `crossplane-system/postgres-admin-credentials` Secret) |
| Logging | CloudWatch log exports for `postgresql` + `upgrade`; Performance Insights with 7-day retention |

The Architect-review step should choose **per-instance KMS key** (option A typically).

The Security-review step should mark SOC 2 CC6.1, CC6.6, CC6.8, CC7.2 and PCI-DSS 3.5, 3.6, 8, 10.5 as `COMPLIANT`. It will likely raise one `MEDIUM` finding around CloudTrail data events on RDS (PCI 10.2) and one `LOW` around enforcing TLS at the engine via a parameter group.

---

## What lands in your project after a complete run

```text
acme-platform/
├── .claude/commands/              # 11 rendered slash commands
├── .infrakit/
│   ├── config.yaml
│   ├── context.md                 # Acme's constitution
│   ├── coding-style.md            # Crossplane coding standards
│   ├── tagging-standard.md
│   ├── agent_personas/            # 4 generic + crossplane_engineer
│   └── memory/
├── .infrakit_tracks/
│   ├── tracks.md
│   └── tracks/xpostgresql-instance-20260415-101500/
│       ├── spec.md                # from /infrakit:new_composition
│       ├── plan.md                # from /infrakit:plan
│       ├── tasks.md               # auto-generated by /infrakit:plan
│       ├── analyze.md             # from /infrakit:analyze
│       ├── architect-review.md
│       ├── security-review.md
│       └── review.md
└── compositions/xpostgresql-instance/
    ├── definition.yaml             # the XRD
    ├── composition.yaml            # Pipeline mode + function-patch-and-transform
    ├── README.md
    └── examples/
        ├── claim-dev.yaml
        └── claim-prod.yaml
```

The `.infrakit_tracks/` directory is the audit trail. Commit it to git alongside the code so future readers can see every decision, every clarifying question, every compliance finding that led to the current implementation.

---

## See also

- [`examples/terraform/`](../terraform/) — the same flow against a Terraform `s3-secure-bucket` module.
- [Methodology notes](../../constraint-driven.md) — how the multi-persona pipeline extends spec-driven development.
