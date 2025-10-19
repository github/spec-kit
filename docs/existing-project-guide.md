# Using Spec Kit in an Existing Project

> You already have a codebase. You want to try Spec Kit without rearranging the furniture. This is a surgical guide: minimum steps, clear checkpoints, easy rollback. This is a **10-minute guide** — pick a realistic scope and save any grand redesigns for later.

---

## 1. Prerequisites

Before starting, you need the Spec Kit CLI tool installed on your machine.

Install the CLI by following the [Installation Guide](installation.md), then jump back here for step 2.

> **Starting a new project?** See the [Quick Start Guide](quickstart.md) instead.

---

## 2. Init

> Spec Kit initializes a **workspace** in the current directory and registers **slash commands** with your coding agent. This workspace holds your **specs, plans, and tasks**.

* Substitute any [supported assistant](../README.md#-supported-ai-agents) (`claude`, `gemini`, `copilot`, `cursor-agent`, etc.) for the `--ai` argument in place of `copilot`.
* When prompted for script type, **pick your flavor** and continue.

### A) If you installed the CLI globally

```bash
specify init --here --ai copilot
```

### B) If you used uvx one-shot

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai copilot
```

### Checkpoint

Spec Kit registers these slash commands in your coding agent:

- `/speckit.constitution`
- `/speckit.specify`
- `/speckit.clarify`
- `/speckit.plan`
- `/speckit.tasks`
- `/speckit.analyze`
- `/speckit.implement`

---

## 3. Constitution

Use the `/speckit.constitution` command to define the project's non-negotiable rules and constraints that AI must follow.

> You'll want to spend serious time here later, but for now write the **high-priority or high-impact** rules you want AI to always follow in your repo.

```markdown
/speckit.constitution Create principles for:
- Quality: tests for all new endpoints; critical-path coverage > 80%.
- Performance/UX: totals update within 200 ms of coupon apply.
- Security/Compliance: log coupon usage with order ID; no PII in logs.
```

---

## 4. Specify

Use `/speckit.specify` inside your coding agent to create a single, focused story. Keep it high-level—what and why. Don’t worry about technical details yet; those come later.

> 💡 **Model selection matters:** Pick a model capable of handling systems-level reasoning, such as `Claude 4.5`, `GPT-5`, or `Gemini 2.5 Pro`. Avoid smaller, lower-capacity models (like `GPT-5-mini` or similar) for systems-level tasks; they can miss context or produce incomplete plans. Use smaller models for narrow, well-defined edits or straightforward refactors.
>
> **This is a 10-minute starter**, so pick something achievable — save the joyrides until your constraints file is complete!

```markdown
/speckit.specify Create story “Apply coupon during checkout.”
Goal: User can enter a valid coupon and see totals update before payment.
Acceptance Criteria:
- Valid coupon → discount applied; totals update before payment.
- Invalid/expired coupon → show reason; totals unchanged.
Constraints: one coupon per order; preserve tax/shipping rules; log coupon usage.
Out of scope: stacking, gift cards, loyalty.
```

### Checkpoint

* Spec Kit automatically creates and checks out a **feature branch**, e.g. `001-checkout-apply-coupon`.
* It also creates a `./specs/001-checkout-apply-coupon/` folder and a set of `.md` files.
* `spec.md` is the specification derived from your prompt — **review it now for accuracy.**

---

## 5. Clarify

If you find any mistakes in your `spec.md` or need to tighten constraints, use the `/speckit.clarify` prompt.

```markdown
/speckit.clarify Tighten ACs: add duplicate-apply and expired-coupon edge cases.
```

Repeat until you’re satisfied — this shapes **the plan**.

---

## 6. Plan

The plan converts your spec into concrete technical decisions—choosing frameworks, databases, and architecture patterns.

You can leave this step blank, or include a **single tech requirement** if one matters; otherwise, AI will make a reasonable attempt.

```markdown
/speckit.plan Tech requirement: preserve existing checkout API contract and return HTTP 422 for invalid coupons.
```

---

## 7. Tasks

This breaks down your plan into a step-by-step checklist of individual coding tasks.

**Taskify** once your plan feels right.

```markdown
/speckit.tasks
```

---

## 8. Analyze (Optional)

Analyze cross-checks your spec, plan, and tasks for consistency issues before implementation begins.

Run analyze as a safety check before touching code:

```markdown
/speckit.analyze
```

---

## 9. Implement

This executes all the tasks from step 7, writing the actual code to implement your feature.

The last step is implementation with the name of your spec. You can include `--dry-run` to see what would be changed without writing any files, or run without it to have AI implement the changes.

```markdown
/speckit.implement 001-checkout-apply-coupon --dry-run # optional: shows planned changes without executing
/speckit.implement 001-checkout-apply-coupon            # execute the implementation
```

---

## Commit strategy

Decide how to organize your git commits—either all-in-one or separating planning from code.

Use **one commit** for the full spike — specs → plan → tasks → code.
If your org enforces separation, use **two commits:** (1) specs + plan + tasks, (2) code changes.

---

## Troubleshooting (quick)

| Symptom | Likely Cause | Fix |
| - | - | - |
| Slash commands not recognized | Init not executed or failed | Re-run init with `--ai copilot` in repo root; restart agent |
| “No such option: --ai” | Missing assistant name | Use `--ai copilot` (or another supported value) |
| Nothing generated after `/speckit.specify` | Missing model creds / provider blocked / init incomplete | Fix credentials; verify init output; retry with a smaller story |
| Implement touches unrelated files | Spec / plan too vague | Tighten scope; add explicit constraints / out-of-scope; re-run plan / tasks |

---

## Next Steps

- **Learn more:** Read the [complete Spec-Driven Development methodology](../spec-driven.md)
- **New projects:** See the [Quick Start Guide](quickstart.md) for greenfield workflows
- **Troubleshooting:** Check the main [README troubleshooting section](../README.md#-troubleshooting)
