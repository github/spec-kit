---
description: Attack a functional specification with parallel adversarial lens agents before `/speckit.plan` locks in architecture. Aggregates findings and walks the maintainer through resolution into one of four categories.
handoffs:
  - label: Proceed to planning
    agent: speckit.plan
    prompt: "Create a plan for the spec, which has now been red-team-reviewed and hardened."
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before red team)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_red_team` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

Goal: Run an adversarial review of a functional spec using project-configured lenses. Produce a structured findings report at `specs/<feature-id>/red-team-findings-<YYYY-MM-DD>[-NN].md`; walk the maintainer through per-finding resolution. Do NOT auto-apply spec changes. Complementary to `/speckit.clarify` (correctness) and `/speckit.analyze` (consistency) — the red team is the adversarial layer.

**Schema references**: a concrete schema for the lens catalog (`.specify/red-team-lenses.yml`) and the findings report format is **TODO — to be added as sibling template files in a follow-up PR if this core approach lands**. Until then, the minimal required lens-catalog shape is inline in §2 preconditions and the findings-report sections are enumerated in §6.5 below.

Invocation: `/speckit.red-team <target-spec-path> [--yes] [--lenses name1,name2,...] [--dry-run] [--session-suffix NN]`

## 1. Invocation parsing

Parse `$ARGUMENTS` into:

- `<target-spec-path>` (positional, required): path relative to repo root of the functional spec to attack. Examples: `specs/<NNN-feature-slug>/spec.md` (SpecKit working record), or a project-specific canonical location for graduated specs (e.g. `04_Functional_Specs/<Component>_Functional_Spec_v0.1_DRAFT.md` in repos that use a graduated docs tree). Both are valid inputs.
- `--yes` (flag): auto-confirm the proposed lens selection when >5 lenses match triggers. Required for non-interactive / CI invocations.
- `--lenses <comma-separated-names>` (flag with value): explicit override of the lens set. Skips trigger-matching; runs exactly the listed lenses.
- `--dry-run` (flag): report which lenses would run and why, without dispatching adversary agents.
- `--session-suffix <NN>` (flag with value): override the session ID's trailing ordinal when multiple sessions occur on the same day.

If `$ARGUMENTS` is empty OR the target spec path is missing, print the usage block above and STOP. Do NOT try to infer the target from context.

## 2. Preconditions check

Before dispatching any adversary, verify in order. Fail fast on the first failure.

1. **Target spec exists**. Resolve the given path relative to repo root. If not found, print: `ERROR: target spec not found at <path>` and STOP.
2. **Lens catalog exists** at `<repo-root>/.specify/red-team-lenses.yml`. If not found, print the error below and STOP:
   ```
   ERROR: no lens catalog at .specify/red-team-lenses.yml
   Minimal required shape:
     version: v1
     lenses:
       - name: <lens-name>
         description: <one-sentence description of the adversarial angle>
         core_questions:
           - <attack question 1>
           - <attack question 2>
         trigger_match: [<one or more of: money_path, regulatory_path, ai_llm, immutability_audit, multi_party, contracts>]
         severity_weight: <integer, default 5>    # optional
         finding_bound: <integer, default 5>       # optional
   Define at least 1 lens covering each trigger category your project cares about.
   ```
3. **Lens catalog parses**. Read the YAML. If parse fails, print: `ERROR: .specify/red-team-lenses.yml failed to parse: <error>` and STOP.
4. **Catalog non-empty**. If top-level `lenses` list is missing or empty, print: `ERROR: lens catalog has no lenses defined` and STOP.
5. **Each lens entry has required fields**: `name`, `description`, `core_questions`, `trigger_match`. Entries missing any of these are skipped with a warning — session proceeds on the remainder. If ALL entries are malformed, fail the catalog check.
6. **Project declares trigger criteria** (soft check — warn, don't fail). Read `<repo-root>/.specify/memory/constitution.md`. Search for a `## Red Team Trigger Criteria` section (or equivalent). If absent, print: `WARNING: constitution does not yet declare red team trigger criteria (expected at ## Red Team Trigger Criteria). Proceeding in bootstrap mode using the six default categories enumerated in the lens catalog schema.` and continue. The six default categories (money_path, regulatory_path, ai_llm, immutability_audit, multi_party, contracts) are used for §3 trigger matching. If `--lenses` was passed, trigger matching is bypassed entirely and this check is a no-op.

## 3. Trigger matching

Skip this section entirely if `--lenses` was passed (jump to §4 using the explicit list).

Otherwise:

1. **Read the target spec** content (full file).
2. **Scan for trigger evidence** against the six trigger categories:
   - `money_path` — keywords/patterns: fee, amount, $, currency, rate, allocation, commitment size, AUM, price, cost, transfer.
   - `regulatory_path` — keywords/patterns: KYC, AML, compliance, regulator, audit, GDPR, SEC, SFC, FCA, jurisdiction, kill filter, fee structure regulatory.
   - `ai_llm` — keywords/patterns: LLM, Claude, GPT, prompt, scoring, classification (when LLM-based), summary generation, hallucination.
   - `immutability_audit` — keywords/patterns: immutable, audit trail, permanent, never deleted, append-only, version preserved.
   - `multi_party` — keywords/patterns: partner, IC, approval, analyst, maintainer, role, authority, sign-off, gate.
   - `contracts` — keywords/patterns: upstream, downstream, API, interface, input from, output to, handoff, integration, document pipeline.
3. **Judgement call**: keyword presence is a heuristic. The final decision is the agent's — if the spec genuinely touches the concern described in the category, include it. If the keyword is incidental (e.g., "audit" in a non-audit sentence), exclude it.
4. **Emit matched-trigger list**. If zero triggers match AND `--lenses` was not passed, print: `INFO: target spec matches no trigger categories — no red team required. Pass --lenses to run voluntarily.` and STOP (not an error — this is the opt-in voluntary path working correctly).

## 4. Lens selection (propose-and-confirm)

Given the matched-triggers list (from §3) or explicit `--lenses` list (from §1):

### If explicit `--lenses` was passed

Resolve each name against the catalog. Unknown names produce a warning and are dropped. If all are dropped, fail with: `ERROR: none of the specified lenses exist in the catalog`. Otherwise proceed to §5 with the resolved list as `selected_lenses`.

### If trigger-matched

1. **Filter the catalog** to lenses where `trigger_match` intersects the matched-triggers list. Call this `matched_lenses`.
2. **If `len(matched_lenses) == 0`**: No lens in the catalog covers the matched triggers. Print: `ERROR: lens catalog has no lens covering the matched triggers <list>. Extend the catalog or pass --lenses explicitly.` and STOP.
3. **If `len(matched_lenses) <= 5`**: Use all of them as `selected_lenses` with `selection_method: auto`. Skip to §5.
4. **If `len(matched_lenses) > 5`**: Enter the propose-and-confirm flow:
   - **Rank** by: primary — count of overlapping trigger-matches with the spec's triggers (higher = preferred); tie-breaker — `severity_weight` from the catalog (higher = preferred); final tie-breaker — alphabetical by name.
   - **Propose the top 5** as the default selection.
   - **Show the maintainer**:
     - The matched-triggers list.
     - The proposed top-5 default with, for each, a one-line rationale (which triggers it covers + severity_weight).
     - The dropped lenses with the reason they ranked below.
   - **If `--yes` was passed**: auto-accept the proposed default. Set `selection_method: auto` in the session record with a note that --yes was used. Skip to §5.
   - **If `--yes` was NOT passed AND the invocation is non-interactive**: FAIL FAST. Print: `ERROR: more than 5 lenses match; interactive confirmation required. Re-run with --yes to accept the proposed default, or --lenses to specify explicitly.` and STOP.
   - **If interactive**: ask the maintainer to respond:
     - "accept" / "yes" → use proposed default; `selection_method: proposed-and-confirmed`.
     - "swap A for B" → swap a default lens with a dropped lens; `selection_method: swapped`.
     - "expand to N" (N > 5) → run more than 5 lenses (maintainer opts into the cost); `selection_method: expanded`.
     - Anything else → re-prompt with the three options above.

Write the final `selected_lenses` list. Validate 3 ≤ `len(selected_lenses)` ≤ 5 (unless `selection_method == expanded`). If below 3, warn the maintainer that lens diversity is weak — offer to abort.

## 5. Parallel adversary dispatch

### If `--dry-run` was passed

Print:
```
DRY RUN — no agents dispatched.
Target: <target-spec-path>
Matched triggers: <list>
Selected lenses: <list>
Selection method: <method>
Proposed session ID: RT-<feature-id>-<YYYY-MM-DD>-<NN>
```
and STOP.

### Otherwise

1. **Compute session ID**: `RT-<feature-id>-<YYYY-MM-DD>[-<NN>]` where `<feature-id>` is derived from the target path (e.g., `<NNN-feature-slug>` from `specs/<NNN-feature-slug>/spec.md`, or the containing feature when attacking a graduated spec — best-effort match; if ambiguous, derive from the filename).
2. **Build adversary-agent prompts**. For each selected lens, construct a prompt with:
   - The lens's `description`.
   - The lens's `core_questions` as the attack brief.
   - The target spec file path (the agent reads it directly).
   - Supporting context paths (if the target is a graduated spec, automatically include its SpecKit working directory — `specs/<feature-id>/plan.md`, `tasks.md`, `contracts/` — if present).
   - Instruction: return ≤`finding_bound` findings ranked by severity (CRITICAL > HIGH > MEDIUM > LOW), each with: location in the spec (section or FR ref), 1-4 sentence finding description, 1-2 sentence suggested resolution.
   - Output format: strict JSON or fenced-code markdown table so aggregation is deterministic.
3. **Dispatch all adversary agents in a single parallel batch** using the host agent's sub-agent / task-dispatch primitive (e.g., Claude Code's Agent tool). All calls go in the same tool-use message so they run concurrently.
4. **Record per-lens start/end times** for wall-clock tracking. Project-level success criteria SHOULD target under 30 minutes for a mid-sized functional spec (roughly 500 lines, 4–6 user stories, 20–30 FRs). Larger specs warrant a proportionally larger budget.

## 6. Findings aggregation

Collect the responses from all dispatched agents.

1. **Parse each response** into structured findings per the findings-report schema:
   - `id`: assigned here — format `F-<session_id>-<NNN>` zero-padded ordinal, monotonic across the whole session.
   - `lens`: name of originating lens.
   - `severity`: one of CRITICAL / HIGH / MEDIUM / LOW.
   - `location`: section or FR reference in the target spec.
   - `description`: the finding.
   - `suggested_resolution`: adversary's proposed fix.
   - `status`: blank (filled in §7).
2. **Enforce per-lens finding bound**. For each lens, retain only the top `finding_bound` findings by severity (default 5 per catalog). Drop the rest. Record dropped count in session metadata.
3. **Detect and handle lens failures**. If an agent returned no findings, returned an error, or the response could not be parsed:
   - Record the failure in session metadata with the lens name and reason.
   - Continue with other lenses — do NOT abort the session.
   - Flag the failed lens as a candidate for `--lenses <name>` re-run after refinement.
4. **Build the aggregated findings table** in markdown. Group by lens; within each lens sub-order by severity descending.
5. **Write the initial report file** at `specs/<feature-id>/red-team-findings-<YYYY-MM-DD>[-NN].md` with:
   - Header block (session ID, target, date, maintainer, lenses, selection method, supporting context, wall-clock)
   - §1 Session Summary: placeholder for maintainer to fill post-review.
   - §2 Findings table: fully populated.
   - §3 Resolutions Log: empty stubs per finding ID.
   - §4 Validation Decision: include ONLY if this is a designated dogfood session (a first-run validation of the protocol against a real project spec; the target spec for a given project is declared in that project's constitution or extension-adoption docs).
   - §5 Session metadata YAML block per the session-record schema.
6. **Announce completion**: print summary (count by lens, count by severity, path to report) and transition to §7.

## 7. Resolution flow

### ⚠️ HARD-AND-FAST RULE — Historical SpecKit records are NEVER modified

**Before editing any file during resolution, classify it using this decision procedure. No exceptions.**

| Path pattern | Category | Editable during resolution? |
|---|---|---|
| `04_Functional_Specs/*` (or project-equivalent graduated docs tree) | **Forward-facing canonical spec** | ✅ Yes — this is where spec-fix edits land |
| `03_Product_Requirements/PRD_*` | **Forward-facing canonical spec** | ✅ Yes |
| `02_System_Architecture/*` | **Forward-facing canonical spec** | ✅ Yes |
| `01_Business_Overview/*` | **Forward-facing canonical spec** | ✅ Yes |
| `.specify/memory/constitution.md` | **Forward-facing governance** | ✅ Yes (via the constitution-amendment pathway; not a normal spec-fix) |
| `.specify/templates/*` | **Forward-facing tooling config** | ✅ Yes |
| `specs/<feature-id>/spec.md` | **HISTORICAL SpecKit working record** | ❌ **NO — never edit** |
| `specs/<feature-id>/plan.md` | **HISTORICAL SpecKit working record** | ❌ **NO — never edit** |
| `specs/<feature-id>/tasks.md` | **HISTORICAL SpecKit working record** | ❌ **NO — never edit** |
| `specs/<feature-id>/research.md` | **HISTORICAL SpecKit working record** | ❌ **NO — never edit** |
| `specs/<feature-id>/data-model.md` | **HISTORICAL SpecKit working record** | ❌ **NO — never edit** |
| `specs/<feature-id>/contracts/*` | **HISTORICAL SpecKit working record** | ❌ **NO — never edit** |
| `specs/<feature-id>/quickstart.md` | **HISTORICAL SpecKit working record** | ❌ **NO — never edit** |
| `specs/<feature-id>/checklists/*` | **HISTORICAL SpecKit working record** | ❌ **NO — never edit** |
| `specs/<feature-id>/red-team-findings-*.md` | **Session artefact** (created by THIS skill) | ✅ Yes — this skill owns it |
| `99_Archive/*` | **Archived historical** | ❌ **NO — never edit** |

**Rationale**: SpecKit working records in `specs/<feature-id>/` capture a point-in-time decision state. They serve as the audit trail of "what was decided at time T." Rewriting them destroys that audit trail. If the correct fix for a red team finding would require editing one of these files, the correct resolution category is:

- **spec-fix** — land the fix in the **forward-facing canonical** location instead (graduated functional-specs tree, product-requirements tree, system-architecture tree), OR
- **out-of-scope** — cross-reference a different forward-facing spec that owns the concern, OR
- **accepted-risk** — record the risk on the forward-facing spec's `## Accepted Risks` section and move on.

**Before applying ANY edit, the skill MUST check the target path against this table and refuse (with a clear error message pointing the maintainer at this section) if the target is a historical SpecKit working record.** If the maintainer insists the edit is necessary, the skill redirects them: "The fix belongs in the forward-facing equivalent. Which graduated canonical doc should land this change?"

### Finding-by-finding walk

Walk the maintainer through each finding. For each finding in the table (group by lens, severity descending):

1. **Display the finding**: ID, lens, severity, location, description, suggested resolution.
2. **Ask for resolution category**: one of —
   - **spec-fix** — edit the **forward-facing canonical** spec. Before proposing any edit, apply the Editable-File classification above. If the suggested resolution references a historical SpecKit working record, redirect the edit to the corresponding forward-facing location and announce this redirect to the maintainer. Prompt the maintainer for a specific diff or description. Record a `downstream_ref` (commit SHA after the maintainer applies + commits, OR a line-ranged description if deferred). The `downstream_ref` MUST reference a forward-facing path.
   - **new-OQ** — route to the target spec's `## Open Questions` section. The "target spec" here is the forward-facing canonical doc, not the SpecKit working record. Prompt for owner name + what it blocks. Compose the OQ entry and offer to insert it; maintainer confirms. Record assigned OQ ID (format `OQ-<feature-id>-<NN>`) as `downstream_ref`.
   - **accepted-risk** — route to the target spec's `## Accepted Risks` section on the forward-facing canonical doc. Prompt for rationale; auto-detect `[regulatory-review]` tag candidates by scanning the finding description for regulated-domain signals (money path, regulatory path, compliance-critical guarantees, disclosure surfaces — as defined by the project's constitution). Offer to insert the AR entry with the next sequential `AR-NNN`. Record AR ID as `downstream_ref`. If tagged, add a reminder about the project's governance-confirmation requirement.
   - **out-of-scope** — finding belongs to a different spec, or the fix belongs in a forward-facing doc that does not yet exist (in which case create a placeholder `specs/<next-feature-id>/README.md` and cross-reference it). Prompt for the owning spec path. Record the cross-reference in the resolution log only; do not edit the other spec.
3. **`/speckit.analyze` cross-reference rule**: for each finding, detect overlap with `/speckit.analyze` output if a recent analyze report is present in the feature directory. If overlap is detected, ASK the maintainer: "This finding appears to overlap with analyze finding <ref>. Cross-reference instead of duplicating? (yes/no)". If yes, record as `resolution.downstream_ref: analyze:<ref>` and SKIP creating a new OQ/AR entry — the analyze finding is authoritative.
4. **MUST NOT auto-apply spec changes**. For spec-fix resolutions, the skill may PROPOSE an edit diff but the maintainer applies it themselves. For AR/OQ insertions, the skill may draft the entry text but the maintainer confirms before the Edit tool actually writes.
5. **MUST NOT edit historical SpecKit working records** (the hard-and-fast rule above). If the maintainer directs the skill to edit such a file, the skill refuses and proposes a forward-facing alternative. If the finding genuinely cannot be resolved at a forward-facing location, the correct category is **accepted-risk** (recording the historical-record gap as an accepted risk) or **out-of-scope** (pointing at a future feature that will do the work properly).
6. **Update the findings table** (`status` column) and append the resolution block to §3 Resolutions Log as each finding is categorised.
7. **After all findings resolved**: update §5 session metadata YAML with final counts per resolution category and `unresolved: 0`. If the maintainer chose to defer some findings, record `unresolved: N` with a note.
8. **For dogfood sessions only**: after all findings resolved, prompt the maintainer to write §4 Validation Decision. Outcome: `proceed-to-codification` / `refine-and-retry` / `abandon`. For `proceed-to-codification`, enforce: at least one meaningful finding (severity ≥ HIGH AND novel adversarial angle) with explicit reason existing tooling couldn't have caught it.

## 8. Failure-mode handling

| Condition | Behaviour |
|---|---|
| Target spec missing | Fail fast with `ERROR: target spec not found at <path>`. No session created. |
| Lens catalog missing | Fail fast with the minimal-required-shape error printed in §2.2 above (no external doc references). |
| Catalog unparseable | Fail fast with `ERROR: .specify/red-team-lenses.yml failed to parse: <error>`. |
| Catalog empty (no `lenses` list) | Fail fast with `ERROR: lens catalog has no lenses defined`. |
| Individual lens entry malformed | Warn, skip that lens, proceed with the rest. If ALL entries malformed, fail. |
| Constitution lacks trigger criteria | Warn and proceed in bootstrap mode using the six default categories. UNLESS `--lenses` was passed (bypass). |
| Target spec matches zero triggers AND no `--lenses` | Print info message and STOP. Not an error. |
| No lens in catalog covers matched triggers | Fail fast — asks maintainer to extend catalog or pass --lenses. |
| >5 matches in non-interactive without `--yes` | Fail fast. Maintainer must re-run with `--yes` or `--lenses`. |
| Individual adversary agent fails (timeout, parse error, empty response) | Record failure in session metadata with lens name + reason. Continue with other lenses. Flag for re-run via `--lenses`. Do NOT abort the session. |
| Overwhelming findings (e.g., >50 HIGH after aggregation) | After §6 completes, if total findings exceed a threshold (default: ≥25 HIGH+CRITICAL), warn the maintainer the spec may not be ready for red team and offer an abort path. Abort records session state for later resumption. |
| Spec was updated since prior red team | On session start, check for prior findings report in the feature dir. If present and older than a material-change threshold (heuristic: target spec has new FRs or section count changed), warn the maintainer and ask whether to proceed or abort. |
| Session interrupted mid-resolution | Report file is saved atomically after every resolution update. On re-invocation with same session ID, offer to resume from last-resolved finding. |

All fail-fast conditions MUST produce actionable error messages — naming the file, the expected location, and pointing at the README or architecture doc for recovery.
