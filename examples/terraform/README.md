# Terraform example — `s3-secure-bucket`

Reproduce a complete, end-to-end InfraKit run for a Terraform module against a fictional platform team (Northwind Logistics) that requires KMS-encrypted S3 buckets with all the usual security gates: public-access blocked, TLS-only access, lifecycle on non-current versions, and optional cross-region replication for prod.

This directory contains everything you need to *re-run* the workflow yourself:

- The Northwind project standards under [`.infrakit/`](./.infrakit/) — context, coding style, tagging standard.
- The final module produced by the run under [`modules/s3-secure-bucket/`](./modules/s3-secure-bucket/).

The intermediate artifacts (spec, plan, tasks, reviews) are **not** committed — they're generated when you run the workflow.

---

## Prerequisites

- [InfraKit CLI](https://pypi.org/project/infrakit-cli/) — install with `uv tool install infrakit-cli` (or `pipx install infrakit-cli`).
- An AI coding agent — this guide uses Claude Code; substitute your favourite (see the [supported list](../../README.md#-supported-ai-coding-agents)).
- [OpenTofu](https://opentofu.org/) or [Terraform](https://developer.hashicorp.com/terraform/install) (for `tofu fmt -check` / `tofu validate`).

---

## Run the workflow against this scenario

### 1. Copy the example into a fresh project

```bash
cp -r examples/terraform/ /tmp/northwind-platform
cd /tmp/northwind-platform
```

The `.infrakit/` directory is already populated with Northwind's standards. The `modules/` directory contains the *final* output for reference — feel free to delete it before re-running:

```bash
rm -rf modules
```

### 2. Bootstrap the project for your AI agent

```bash
infrakit init --here --ai claude --iac terraform --script sh --force --no-git
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
/infrakit:create_terraform_code s3-secure-bucket ./modules/s3-secure-bucket
```

This launches the four-persona pipeline:

- **Cloud Solutions Engineer** — asks clarifying questions about the bucket's purpose, environment, data classification, replication needs. Use the answers below ("Reference inputs") to reproduce the example.
- **Cloud Architect** — presents 2–3 design options with cost/reliability trade-offs (storage tier, KMS key choice, replication topology). Pick the default.
- **Cloud Security Engineer** — asks which compliance frameworks apply. For this example, select **SOC 2 + PCI-DSS**.

Once the spec is confirmed:

```text
/infrakit:plan <track-name>
/infrakit:implement <track-name>
/infrakit:analyze <track-name>
/infrakit:architect-review <track-name>
/infrakit:security-review <track-name>
/infrakit:review ./modules/s3-secure-bucket
```

`<track-name>` follows the format `s3-secure-bucket-<YYYYMMDD-HHMMSS>`.

### 5. Verify the produced module

```bash
cd modules/s3-secure-bucket
tofu fmt -check -diff
tofu init -backend=false
tofu validate
```

All three should pass.

---

## Reference inputs

When the Cloud Solutions Engineer asks clarifying questions, use these answers to reproduce the bundled module verbatim:

| Question | Answer |
|---|---|
| Bucket purpose | Application data storage |
| Environment | flexible — caller provides via `var.environment` |
| Data classification | flexible — caller provides via `var.data_classification` |
| Encryption | Customer-managed KMS key, rotation enabled, 30-day deletion window |
| Public access | All four `block_public_*` flags `true`; never overridable |
| Object ownership | `BucketOwnerEnforced` (ACLs disabled) |
| TLS | Bucket policy denies `aws:SecureTransport == false` |
| Versioning | Always enabled |
| Lifecycle | Non-current → IA at 30d, GLACIER at 90d, expire at 365d (all configurable, all gated on `>0`) |
| Cross-region replication | Optional; allowed only when `environment == "prod"`; caller supplies destination bucket ARN + KMS key ARN |
| `force_destroy` | Hard-coded `false`; not exposed as a variable |

The Architect-review step should choose the **per-instance KMS key** design (option A typically).

The Security-review step should mark CC6.1, CC6.7, CC6.8, PCI 3.5, PCI 4.2 as `COMPLIANT` with two `LOW` notes (access logging and Object Lock are explicitly out of scope for this module).

---

## What lands in your project after a complete run

```text
northwind-platform/
├── .claude/commands/              # 11 rendered slash commands
├── .infrakit/
│   ├── config.yaml
│   ├── context.md                 # Northwind's constitution
│   ├── coding-style.md            # Terraform coding standards
│   ├── tagging-standard.md
│   ├── agent_personas/            # 4 generic + terraform_engineer
│   └── memory/
├── .infrakit_tracks/
│   ├── tracks.md
│   └── tracks/s3-secure-bucket-20260415-093000/
│       ├── spec.md                # from /infrakit:create_terraform_code
│       ├── plan.md                # from /infrakit:plan
│       ├── tasks.md               # auto-generated by /infrakit:plan
│       ├── analyze.md             # from /infrakit:analyze
│       ├── architect-review.md
│       ├── security-review.md
│       └── review.md
└── modules/s3-secure-bucket/
    ├── versions.tf
    ├── variables.tf
    ├── main.tf
    ├── outputs.tf
    └── README.md
```

The `.infrakit_tracks/` directory is the audit trail. Commit it to git alongside the code so future readers can see every decision, every clarifying question, every compliance finding that led to the current implementation.

---

## See also

- [`examples/crossplane/`](../crossplane/) — the same flow against a Crossplane `XPostgreSQLInstance`.
- [Methodology notes](../../constraint-driven.md) — how the multi-persona pipeline extends spec-driven development.
