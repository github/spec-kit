---
description: "Recommend which model tier to use for the next SDD phase based on evaluator findings — enables the portfolio approach (budget for routine, premium for critical)"
---

# Evaluator Route

Analyze evaluator findings and recommend which model tier to use for the next SDD phase. This is the mechanism that enables the **portfolio approach**: budget models for routine generation, standard models for review, premium models for critical decisions.

The recommendation is based on:
- Finding severity distribution (critical/high findings → escalate)
- Evidence quality (unsupported claims → need premium reasoning)
- Phase risk profile (implement is higher risk than specify)
- Cost optimization (budget is sufficient when risk is low)

## User Input

```text
$ARGUMENTS
```

Accept:
1. **Phase** — the next SDD phase to route for (e.g., `phase=plan`, `phase=implement`). Required.
2. **Result files** — evaluator result files to base the recommendation on. If not provided, discover the latest composed result for the current phase.
3. **Budget constraint** — optional maximum USD budget for the next phase. If provided, the recommendation must stay within budget.

## Prerequisites

- **Path safety**: resolve `.specify/extensions/evaluator/results/` — refuse symlinks.
- At least one evaluator result or composed result MUST exist. If none, default to `budget` tier with a note that no evaluation data is available.

## Execution

### 1. Load Evaluation Results

Read the latest composed result or individual evaluator results for the current phase.

### 2. Assess Risk Profile

Score the risk of the next phase based on evaluator findings:

| Factor | Weight | How Measured |
|--------|--------|-------------|
| Critical findings | 40% | Count of `critical` severity findings |
| High findings | 30% | Count of `high` severity findings |
| Evidence gaps | 20% | Count of `unsupported_claim` + `missing_evidence` findings |
| Contradictions | 10% | Count of contradictory finding pairs |

Risk score = weighted sum, normalized to 0.0–1.0.

### 3. Determine Recommended Tier

| Risk Score | Recommended Tier | Rationale |
|-----------|-----------------|-----------|
| 0.0–0.2 | `budget` | Low risk — budget models sufficient |
| 0.2–0.5 | `standard` | Moderate risk — standard quality needed |
| 0.5–0.8 | `premium` | High risk — premium reasoning required |
| 0.8–1.0 | `premium` + escalation | Critical risk — premium + human review |

### 4. Apply Phase Risk Baseline

Each SDD phase has an inherent risk baseline that shifts the threshold:

| Phase | Baseline Risk | Effect |
|-------|--------------|--------|
| `specify` | 0.1 | Slightly lower bar for premium (spec quality matters) |
| `plan` | 0.15 | Moderate — design decisions are costly to undo |
| `tasks` | 0.05 | Lower — task breakdown is mechanical |
| `implement` | 0.2 | Higher — implementation errors are expensive |
| `analyze` | 0.1 | Moderate — cross-artifact analysis |
| `checklist` | 0.0 | Lowest — checklist generation is routine |
| `clarify` | 0.15 | Moderate — clarification needs precision |
| `constitution` | 0.2 | Higher — governance decisions are critical |
| `converge` | 0.15 | Moderate — convergence assessment |

### 5. Apply Budget Constraint (if provided)

If a budget constraint is specified, downgrade the recommendation if the estimated cost exceeds the budget:

1. Calculate estimated tokens for the next phase at the recommended tier
2. Calculate estimated cost at that tier
3. If cost > budget, try the next lower tier
4. If no tier fits the budget, recommend `budget` with a warning

### 6. Produce Model Routing Recommendation

Output a `model_routing` block conforming to the evaluator result schema:

```json
{
  "model_routing": {
    "recommended_tier": "standard",
    "reason": "2 high-severity findings and 1 evidence gap — standard quality recommended for plan phase",
    "escalation_triggers": [
      {
        "condition": "Any new critical finding",
        "escalate_to": "premium"
      },
      {
        "condition": "More than 5 unsupported claims in next evaluation",
        "escalate_to": "premium"
      }
    ],
    "estimated_tokens": 12000,
    "estimated_cost_usd": 0.22,
    "tier_breakdown": {
      "budget": {
        "estimated_tokens": 18000,
        "estimated_cost_usd": 0.01
      },
      "standard": {
        "estimated_tokens": 12000,
        "estimated_cost_usd": 0.22
      },
      "premium": {
        "estimated_tokens": 10000,
        "estimated_cost_usd": 0.90
      }
    }
  }
}
```

### 7. Report

Output:
- The recommended tier and reason
- The risk score breakdown
- Cost comparison across all tiers
- Escalation triggers (conditions that would upgrade the recommendation)
- The estimated savings vs always using premium

## Model Tier Pricing Reference

| Tier | Input $/1M tok | Output $/1M tok | Best For |
|------|---------------|-----------------|----------|
| `budget` | $0.12–$0.25 | $0.50–$1.25 | Routine generation, drafts, bounded tasks |
| `standard` | $3.00 | $15.00 | Review, moderate-complexity work |
| `premium` | $15.00 | $75.00 | Critical decisions, security, governance |
| `portfolio` | ~$1.30 | ~$6.40 | Routed blend (80% budget, 15% standard, 5% premium) |

## Portfolio Approach Rules

1. **Default to budget.** Start every phase at the budget tier. Only escalate when evaluator findings justify it.
2. **Escalate on evidence.** Upgrade when findings show `critical` severity, `insufficient_evidence` uncertainty, or `contradiction` between evaluators.
3. **Downgrade when clean.** If the previous phase had zero high/critical findings, drop back to budget for the next phase.
4. **Never use premium for generation.** Premium models are for evaluation and decision-making, not for drafting specs or writing boilerplate code.
5. **Deterministic evaluators are free.** Schema validators, linters, and static analyzers cost near-zero tokens. Run them always, at every phase.
6. **Model-backed evaluators use budget tier.** Epistemic checks, semantic review, and coverage analysis run on budget models by default. Only escalate the evaluator itself when findings warrant it.

## Guardrails

- Never recommend premium for a phase with zero high/critical findings.
- Never recommend budget when there are unresolved `block` outcomes.
- Always show the cost comparison — let the human see what they're saving.
- The routing recommendation is advisory — the human operator always has final say.
