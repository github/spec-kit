# Contract-Driven Development

When a component exposes an interface to an external consumer, define the
contract that consumer can rely on. **Contract-driven development** means
agreeing on that contract, implementing each side against it, and verifying
that both sides meet their obligations.

This fits within Spec-Driven Development: product requirements establish the
intended behavior; contracts define how components collaborate to deliver it;
each component's implementation plan describes its internal solution. Define
the interaction boundary first, rather than treating repository boundaries as
the design.

This guide uses existing Spec Kit commands and ordinary versioned artifacts.
It does not introduce automatic contract synchronization, cross-repository
dependency resolution, or release orchestration.

## When to define a contract

"External" means outside the component's implementation boundary, not
necessarily outside its process, repository, or organization. Examples include:

- A website calling a backend API.
- One service calling another or consuming its events.
- An application using a library or plugin interface.
- Automation invoking a CLI and parsing its output.
- Components exchanging files in an agreed format.

The principle applies to monoliths, modular applications, microservices, and
other architectures. Repository layout does not determine whether a contract is
needed. Its form and detail should match the interface: a small library may
need documented signatures and behavior, while a public HTTP API may benefit
from an OpenAPI schema and executable examples. Not every contract needs a
separate schema or a contract registry.

## What the contract defines

Describe the observable obligations that let each side be implemented without
depending on the other's internals:

- Accepted inputs and produced outputs, including formats and validation rules.
- Behavior and side effects, including error cases.
- Relevant interaction guarantees, such as idempotency, event ordering, retries,
  or timeouts.
- Compatibility expectations, versioning, and deprecation policy.
- Examples and verification criteria for providers and consumers.

A schema alone may not capture the full agreement. For example, the shape of an
order request does not explain whether retrying it can create a second order.
Document those semantics too. Do not expose internal database structures or
implementation choices unless they are genuinely part of the public interface.

## One authoritative owner

**One side owns the authoritative contract; the other consumes it.** Usually
the component exposing the interface owns it. Make ownership explicit for each
interface, and have affected consumers participate in agreeing on changes.
Ownership does not mean unilateral changes.

| Situation | How to share the contract |
|-----------|--------------------------|
| Both sides are in the same repository | Reference the same authoritative file or artifact instead of maintaining separate definitions. Independently released components should still record the contract version they support. |
| The sides are in different repositories | Publish a versioned contract artifact/package for consumers to pin, or synchronize a copy into each consuming repository. |
| A consumer keeps a synchronized copy | Record its authoritative source and exact version or commit. Treat the copy as read-only input; propose changes at the source. |

For a vendored copy, an adjacent README can record the source repository, source
path, immutable revision or release artifact digest, and update procedure. A
package dependency can record the equivalent information in its lockfile.
Provide consumers with authorized access to the contract artifact; they need
not receive access to the provider's implementation repository.

Updates are deliberate: agree on a change at the authoritative source, publish
a version, then review the version or copy update in each consumer. Do not
silently synchronize everyone to "latest". A pinned contract identifies an
agreement; it does not guarantee that the deployed provider still supports it.

## Using the Spec Kit workflow

1. **Establish intent and identify the interfaces.** Capture the desired user
   behavior with `/speckit.specify`. Identify which components provide and
   consume each interaction. If no contract exists, defining it is part of the
   work, not a prerequisite that must already have been completed elsewhere.
2. **Agree on the contract before dependent implementation.** During
   `/speckit.plan`, the owner drafts the interface contract and reviews it with
   consumers. Resolve observable behavior and compatibility questions before
   either side implements assumptions about the other. Each side can then
   develop independently against the agreed version.
3. **Supply the agreement to each affected project.** Give the agent the
   contract's exact version and accessible content, along with the relevant
   product requirements. Do not assume that a link makes another repository's
   files available. Each project owns its local `spec.md`, `plan.md`, and
   `tasks.md`; reference the contract rather than copying another project's
   implementation plan.
4. **Plan verification explicitly.** Ask `/speckit.tasks` to include provider
   and consumer contract tests, including negative cases. Test observable
   behavior as well as data shapes. Consumer tests against mocks are useful,
   but do not establish that the real provider conforms; include provider
   verification and integration validation.
5. **Implement and validate each side.** Use `/speckit.implement` in each
   project, then run the agreed checks. If implementation reveals a contract
   problem, revise the authoritative agreement and reconcile the affected
   specs, plans, tests, and consumer versions rather than privately changing a
   copy.
6. **Release compatible implementations.** Track which deployed component
   versions support which contract versions. Sequence rollout and rollback
   around those dependencies. For breaking changes, agree on a migration and
   overlap period before removing behavior consumers still use.

`/speckit.plan` already produces feature-scoped `contracts/` artifacts when
external interfaces are involved. Choose explicitly which artifact is
authoritative: a feature may draft a new contract there, or propose a change to
an established contract elsewhere in the project. Record the approved source
and version in the feature artifacts. Historical snapshots and synchronized
copies are not additional editable sources of truth, and Spec Kit does not
publish or synchronize them automatically.

For artifact evolution after a change, see
[Evolving Specs in Existing Projects](evolving-specs.md).

## Worked example: website checkout across services

Consider a hypothetical checkout feature with a website, an orders service,
and an inventory service, each in its own repository. There are no agreed
contracts yet. The user requirement is: **a customer can place an order only
when its items can be reserved, and retrying a request must not create a
duplicate order or reservation.**

First identify and agree on the two contracts. These are summaries; the
authoritative artifacts must also define the input/output details and other
obligations described above.

| Contract | Owner/provider | Consumer | Observable agreement |
|----------|----------------|----------|----------------------|
| Orders API | Orders service | Website | Accept an order request with an idempotency key; return the order or a defined failure; retries must not create duplicate orders. |
| Inventory API | Inventory service | Orders service | Reserve all requested items or report insufficient stock without a partial reservation; retries must not create duplicate reservations. |

The orders service is a provider on one interface and a consumer on the other.
It owns the Orders API contract, not the Inventory API contract.

One possible layout, using synchronized copies rather than packages:

```text
inventory-repo/
  .specify/
  contracts/inventory-api.yaml     # authoritative Inventory API contract
  specs/001-reserve-inventory/

orders-repo/
  .specify/
  contracts/orders-api.yaml        # authoritative Orders API contract
  contracts/inventory-api.yaml     # read-only copy pinned to Inventory API 1.0.0
  contracts/README.md              # source revision and sync procedure
  specs/001-place-order/

website-repo/
  .specify/
  contracts/orders-api.yaml        # read-only copy pinned to Orders API 1.0.0
  contracts/README.md              # source revision and sync procedure
  specs/001-checkout/
```

The filenames and versions are illustrative, not a required Spec Kit layout.
Each project is initialized independently and uses the usual SDD workflow:

1. The inventory team agrees on Inventory API 1.0.0 with the orders team; the
   orders team agrees on Orders API 1.0.0 with the website team. Each owner
   publishes its approved contract, and consumers pin their copies.
2. Each team specifies and plans its own part of checkout against those
   agreements. The website describes customer interaction, orders describes
   order placement, and inventory describes reservation behavior. The orders
   plan accounts for both contracts and for failures between reservation and
   order creation.
3. Link each local feature spec to the same product-feature issue or roadmap
   entry, and record its contract versions and related provider/consumer specs
   or PRs. Local feature numbers and branches need not match. This is
   traceability, not a shared implementation plan.
4. Implement and verify both interfaces, including retries, insufficient
   stock, and failures. Validate the complete checkout path as well as each
   component's contract obligations.
5. For this initial rollout, make the inventory implementation available
   before enabling the dependent orders implementation, then enable website
   checkout. Record the deployed versions and rollback constraints; publishing
   a contract alone does not make its implementation available.

If Orders API 1.1.0 later adds an optional delivery note, propose and review
that change in `orders-repo`, verify compatibility with existing consumers,
then let the website deliberately adopt the new version. Do not edit the
website's synchronized copy to invent support the orders service has not
agreed to provide.

The same design works if all three components move into one repository:
reference the authoritative contracts directly instead of synchronizing copies.
See [Using Spec Kit in a Monorepo](monorepo.md) for project layout and command
targeting. **The contract connects the implementations; repository layout only
changes how that agreement is shared.**

## Example: control plane, data plane, and integration tests

Consider a control-plane project (`r1`) that manages configuration, a data-plane
project (`r2`) that applies it while processing traffic, and an integration-test
project (`r3`) that verifies their interaction. Each lives in its own repository.
This is another application of the same principle, not a requirement to
organize systems this way.

### Define the interaction first

Suppose the control plane needs to apply a configuration to the data plane,
but no contract exists yet. Agree on the observable behavior before either
side implements assumptions about the other:

| Contract concern | Example agreement |
|------------------|-------------------|
| Inputs | A configuration revision and payload with explicit validation rules. |
| Outputs | An acknowledgement identifying the revision and whether it is accepted or applied; define how the caller observes completion if application is asynchronous. |
| Errors | Defined responses for invalid configuration and stale revisions, with the prior valid configuration left active. |
| Behavior | Retrying the same revision and payload does not apply it twice; reusing a revision with a different payload is rejected. |
| Compatibility | Identify supported contract versions and preserve behavior that existing callers still rely on during migration. |

In this example, `r2` exposes the interface and owns the authoritative contract.
The `r1` team participates in agreeing on it and consumes a pinned version.
The `r3` team uses that same version to verify the interaction, including
invalid input, retries, and compatibility with supported implementations. Tests
are evidence for the agreement, not a competing definition of it.

Each project keeps its own implementation or test plan. Reference the shared
product intent and contract version without requiring an umbrella repository,
matching branch names, or atomic commits across the three repositories.

### Evolve an agreed contract deliberately

The rollout sequence below adapts contract-evolution guidance contributed by
TongyiDai. It assumes the initial interaction contract has already been agreed
and is in use.

Suppose the provider and consumers agree to add a new optional configuration
field. Plan its compatible adoption explicitly:

1. **Publish a compatible change.** Update the authoritative contract in `r2`,
   give it an explicit version, and publish the schema and compatibility
   fixtures. Verify that omitting the field preserves existing behavior.
2. **Deploy support before enabling use.** If `r1` needs new behavior from
   `r2`, deploy `r2` in a mode supporting both old and new consumers first.
   Only then enable the dependent behavior in `r1`. This ordering follows
   the interface dependency, not the repository names or PR merge order.
3. **Prepare version-aware integration tests.** Add `r3` coverage early,
   selecting expectations by supported contract version or explicit capability,
   not branch name. Keep existing compatibility checks required. Make the new
   end-to-end gate required before enabling the feature once compatible
   implementations are available; do not silently skip it after activation.
4. **Track readiness with immutable references.** An existing issue or roadmap
   can link the approved contract, provider and consumer releases, end-to-end
   results, and old-path removal criteria to exact commits or release artifacts.
   Distinguish merged changes from deployed, ready implementations.
5. **Preserve a rollback path.** For this provider-first rollout, disable or
   roll back the consumer's new behavior before rolling back the provider.
   Check persisted-state and configuration compatibility too; reversing deploy
   order alone does not undo data changes. Remove the old contract only in a
   later cleanup after confirming no supported consumers still depend on it.

If a breaking change is unavoidable, expand support to allow migration, move
consumers deliberately, and only then retire the old behavior. Publishing a
versioned contract and recording readiness do not turn separate deployments
into a transaction. These are team-maintained agreements and checks, not a new
Spec Kit dependency resolver or release orchestrator.
