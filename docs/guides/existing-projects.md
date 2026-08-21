# Adopting Spec Kit in an Existing Project

You do not need to recreate an existing system from specifications before using
Spec Kit. Initialize the repository in place, capture the rules that matter,
and use the workflow for the next bounded change.

## 1. Start from a Reviewable Baseline

Before initialization, commit or stash existing work and create a branch for the
adoption. This makes every generated file visible in a normal code review.

Choose the [integration key](../reference/integrations.md) for the coding agent
you use. Then run the command from the repository root:

```bash
specify init --here --force --integration <key>
```

`--here` targets the current directory. `--force` allows initialization in a
non-empty directory and may replace files at conflicting managed paths, so use
it only after creating a reviewable baseline. It does not delete the rest of
your application.

Review the resulting diff before continuing. Initialization adds the shared
`.specify/` project files and the command or skill files required by your
selected integration. It does not rewrite your application or infer
specifications for existing behavior.

> [!NOTE]
> Git initialization and feature branches are optional and are managed by the
> **git** extension. Add it with `specify extension add git` if you want that
> workflow.

## 2. Capture Project Guardrails

Run `/speckit.constitution` with principles that are already true for the
repository or that the team has explicitly agreed to adopt:

```text
/speckit.constitution Preserve public API compatibility. Follow the existing
service boundaries. Every database migration must include a rollback plan.
Run the repository's established unit and integration test suites.
```

Use the repository's README, architecture decisions, contribution guide, and
CI configuration as evidence. Do not invent standards merely to fill the
constitution template. The constitution governs later planning and analysis,
so unrealistic rules create noise instead of useful constraints.

## 3. Choose a Bounded First Change

Start with a feature, bug fix, or modernization slice that can be reviewed
independently. Do not make "document the entire existing system" your first
feature unless that inventory is itself the intended deliverable.

Describe both the requested outcome and the compatibility boundaries that must
remain intact:

```text
/speckit.specify Add CSV export to the existing orders page. Preserve current
filters and authorization behavior. Export only the rows visible to the signed-in
user, and do not change the existing JSON API response.
```

The codebase remains implementation context. The new `spec.md` defines the
change you intend to make, not a retroactive specification of every existing
behavior.

## 4. Plan Against the Repository

Continue through the normal workflow:

1. Run `/speckit.clarify` to resolve uncertain behavior and compatibility
   requirements.
2. Run `/speckit.plan` and verify that the proposed design reuses the existing
   architecture, dependencies, and test conventions.
3. Run `/speckit.tasks`, then `/speckit.analyze` to check consistency before
   implementation.
4. Run `/speckit.implement` and review code and artifact changes together.
5. Run `/speckit.converge` to find remaining gaps. If it adds tasks, repeat
   implementation and convergence until the feature is complete.

For command details and optional quality gates, see the
[Quick Start Guide](../quickstart.md) and
[Agentic SDD reference](../reference/agentic-sdd.md).

## 5. Decide How Specs Will Age

After the first change, agree on how the team will maintain completed feature
artifacts:

- Keep each feature directory as an immutable historical record.
- Maintain `spec.md` as a living contract and regenerate downstream artifacts.
- Allow discoveries to flow back from code, tasks, or plans, then reconcile the
  full artifact set.

The [Spec Persistence Models](../concepts/spec-persistence.md) page compares
these choices. The [Evolving Specs guide](evolving-specs.md) provides the
maintenance loop for each model.

## Existing-Project Examples

The [community walkthroughs](../community/walkthroughs.md) include brownfield
examples across .NET, Java, and Go/React codebases. Community extensions for
architecture discovery and brownfield bootstrapping are listed in the
[extension catalog](../community/extensions.md).
