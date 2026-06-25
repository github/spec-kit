# Thinking in SDD

*A field guide to Spec-Driven Development for engineers who already know the
work is in the judgment, not the typing.*

> This is not a tour of Spec Kit's commands. The command list is at the bottom in
> one table; you'll learn it in an afternoon. What takes years is knowing **what
> to distrust, when to go backwards, and which mistakes to make cheaply** — and
> that's what SDD is actually for. This guide teaches the thinking. The demo in
> the middle goes wrong on purpose, because that's where the lessons live.
>
> Prompts are shown in full (they're what you type). Generated artifacts are
> shown as captions — you should learn their *shape*, not memorize someone else's
> spec.

---

## The one idea everything else hangs on

You are working with a collaborator that is **fast, fluent, tireless, and
confidently wrong in predictable ways**. It optimizes for *plausibility* — output
that looks like what a good answer looks like — not for *correctness*. It will
hand you a spec that reads beautifully and solves the wrong problem. It will
propose an architecture that's clean, conventional, and two layers heavier than
your problem needs. It will agree with whatever you said last. And it never tells
you what it doesn't know unless you force it to.

Given that collaborator, the value of SDD is not "specs generate code." It's
this: **SDD front-loads disagreement to the cheapest possible layer.** A wrong
assumption caught in `spec.md` costs a sentence. The same assumption caught in
code costs a day. Caught in production, it costs a customer. Every loop in the
process — clarify, checklist, analyze, converge — exists to drag a future
expensive mistake forward into a present cheap one.

So the senior's stance toward the whole apparatus is **adversarial, not
compliant.** You are not filling out a workflow. You are running a series of cheap
experiments designed to find out where you and the model are wrong *before* it's
expensive to be wrong. If a step isn't surfacing disagreement, you're doing it as
theater.

Three corollaries fall out of this, and the rest of the guide is just these three
applied:

1. **Every artifact the model produces is a suspect, not a deliverable.** Your
   job when you read a generated spec or plan is to attack it: *what did it assume
   that I didn't say? what failure mode does this gloss? where is it being
   plausible instead of right?*

2. **The process is non-linear because discovery is non-linear.** You will learn
   things during planning that invalidate the spec, and things during
   implementation that invalidate the plan. A senior expects this and *instruments
   for it*. Going backwards isn't failure; refusing to is.

3. **The hardest part isn't writing the spec — it's knowing what you actually
   want, and you usually don't, at the start.** The real problem is often not the
   one you typed. The process's job is to help you find the real one before you've
   built the wrong one.

---

## What the model is good at, and what is yours alone

Keep this division sharp, because most wasted effort comes from blurring it.

| The model is genuinely good at | Which means you should | And it is bad at | Which means you must never |
| --- | --- | --- | --- |
| Producing a complete, well-structured first draft fast | Let it draft everything; never start from a blank page | Knowing what's worth building | Outsource the "what" or the "why" |
| Surfacing options and conventions | Use it to widen your view of the solution space | Saying "I don't know" or "this is risky" | Trust silence as a sign of safety |
| Filling in plausible detail | Let it handle mechanism once intent is fixed | Distinguishing plausible from correct | Accept an artifact because it reads well |
| Tireless, consistent mechanical work | Hand it the decomposition and the typing | Holding a large design in coherent context | Let it one-shot a big feature |

The work that is *yours, irreducibly*: deciding what problem is real, deciding
what "correct" means here, deciding what must never happen, deciding what to cut,
and noticing when the beautiful artifact in front of you is solving a problem you
don't have. SDD doesn't reduce that work. It *clears the noise away from it* so
you can spend your scarce judgment there instead of on boilerplate.

---

## The build that went sideways (and what each turn taught)

> Deniz is shipping **Redaktör**: a tool that masks personal data (PII) in
> Turkish documents so a compliance team can share them safely. It's a good
> teaching case because "correct" here is adversarial, non-obvious, and carries
> real liability — exactly the conditions under which plausible-but-wrong is
> dangerous. Watch the *reasoning*, not the commands. Several turns are mistakes,
> caught at different costs.

### t0 — The first framing is wrong, and finding that out is the whole job

Deniz's first instinct is "build a PII masker." He's about to type that into
`/speckit.specify`. He stops, because he's been burned by exactly this: a clean
spec for the wrong product.

He asks the question that the tool will never ask for him: **what is the real
failure here?** Not "the model misses a phone number" — the real failure is *a
compliance officer signs off on a document, and PII leaks anyway, and now it's
their name on the breach.* The product isn't an NLP problem. It's a **trust and
liability** problem. The reviewer has to trust an AI's redaction enough to put
their signature on it. That reframing changes everything downstream: it means
auditability, explainability, and a hard human gate matter *more* than detection
F1.

⟶ **Lesson.** The most expensive mistakes are made before you touch the tool, in
the gap between the problem you typed and the problem you have. No command catches
this. It's the one part that is entirely you, and it's the part most people skip.

He does *not* start with the constitution as a vague "code quality, testing, UX"
prompt (the kind of boilerplate that fails no plan). He writes principles that
encode the *liability* framing as hard gates:

```text
# A constitution earns its place only if you can imagine a plan FAILING it.
# These are written to fail plans, not to decorate the repo.
/speckit.constitution Establish gates that a plan must pass or carry a written
exception: (1) Every masked document is reproducible from its audit record alone —
if we can't reconstruct what was redacted and why, the plan fails. (2) The human
reviewer is the last authority; no irreversible export without an explicit
approval action — an "auto-approve high confidence" feature fails this gate by
construction. (3) Raw document text never enters logs, traces, or error messages.
(4) Every model-based component carries an eval set and a regression threshold;
"we tried it and it looked good" is not acceptance. Bias toward fewer moving parts:
a plan that adds a service must justify why a function wouldn't do.
```

⟶ **Lesson.** A constitution is not values; it's a set of trip-wires. Principle
(2) is written so that a *specific tempting feature* — auto-approve — is dead on
arrival. That's what makes it load-bearing instead of inspirational.

### Specify — the model writes a good spec for the wrong product

He describes the *what*, deliberately omitting stack, and gets back a clean
`spec.md`. It reads well. That's the trap.

```text
/speckit.specify A reviewer uploads a Turkish document; the system detects PII
(names, T.C. national IDs, IBANs, phones, addresses), shows each detection with a
confidence level, lets the reviewer accept/reject/edit inline, and on confirmation
returns a masked copy plus an audit record. Export is blocked while any
high-confidence detection is unresolved.
```

> *(Caption — the spec the model produced:)* tidy user stories, requirements
> organized around **detection accuracy and the masking flow**, sensible edge
> cases. Looks done.

Deniz reads it adversarially and the smell hits immediately: **the spec is
optimizing detection, but his real problem was trust.** The model did exactly what
he asked and nothing he meant. There's no requirement about *why a reviewer would
believe a mask is correct*, nothing about what happens when the model and the
reviewer disagree, nothing about the liability trail beyond a vague "audit
record." It's a spec for a demo, not for someone's signature.

He doesn't tweak it. He rewrites the intent, because a spec aimed at the wrong
target can't be patched into the right one:

```text
# Re-aim the spec at the real problem: reviewer trust and defensible sign-off.
/speckit.specify Reframe: the user is a compliance officer who must personally
attest that a document is safe to share. The system's job is to make that
attestation FAST and DEFENSIBLE, not just to detect PII. Requirements should cover:
how a reviewer sees what is under a mask without exposing it to anyone else; how
disagreements between the model and the reviewer are recorded; what the audit
record must contain to defend the decision later; and what the reviewer is and
isn't allowed to do (e.g., no bulk auto-accept). Detection is necessary but not the
point — the point is a sign-off the reviewer can stand behind.
```

⟶ **Lesson.** "The model gave me a clean spec" is a warning, not a win. A clean
artifact aimed at the wrong problem is more dangerous than a messy one aimed at
the right problem, because the cleanliness lowers your guard. Read every generated
spec by asking *what problem is this actually solving, and is it mine?*

### Clarify — the questions it asks matter less than the one it doesn't

```text
/speckit.clarify
```

The model asks five questions. Deniz's read:

```text
# Two are real, three are filler. The filler tells me where the model is pattern-
# matching instead of thinking — and the GAP tells me more than the questions.
Q: Confidence threshold for "high"?           → real. ≥0.85 blocks export.
Q: Masking token format?                      → real. Category tokens: [TCKN], [IBAN].
Q: Supported file types?                      → filler. Doesn't change the design.
Q: Max document size?                         → filler. Pick 20 pages, move on.
Q: Light or dark theme?                       → noise.
```

The signal isn't in the answers. It's that **the model did not ask the question
that actually decides the product**: *when the model flags PII the reviewer thinks
is fine — or misses PII the reviewer spots — what happens, and who owns that
decision in the audit trail?* That's the entire trust mechanism, and the tool was
blind to it because it's not a pattern that shows up in training; it's specific to
his liability framing.

So he injects it himself, into the spec, by hand-driving the clarification:

```text
/speckit.clarify Record this decision explicitly in the spec: every reviewer
override of a model detection (accept-despite-low-confidence, reject-despite-high,
manual-add) is a first-class audited event with reviewer identity and timestamp.
The model's opinion and the reviewer's decision are both stored; on conflict, the
reviewer's decision governs the export but the model's dissent is retained in the
record. This is the core trust mechanism — make it a requirement, not an
implementation detail.
```

⟶ **Lesson.** Clarify is not "answer the model's quiz." It's a prompt to ask
*yourself* what's underspecified. The model's questions map what's *conventional*
to underspecify; your job is to find what's *uniquely* dangerous to leave
unsaid here. Often the most important clarification is one the tool never raised.

### Plan — reading the smell of a plausible over-design

Now stack and constraints are fair game.

```text
/speckit.plan FastAPI + Python 3.12 backend; React + TypeScript reviewer UI with
SSE streaming of detections; Postgres for audit records. Detection engine must be
an importable library, testable without the web layer. Structured logging with a
redaction filter. Eval harness over a labeled Turkish corpus.
```

The model returns a confident, conventional plan — and Deniz reads two smells:

**Smell 1: it reached for an LLM-as-judge verification pass over every detection.**
Plausible (more checking = better, right?), and wrong for v1. He reasons about the
*cost*, which the model never does unprompted: the judge roughly doubles latency
and per-document cost, and — worse — adds a *second non-deterministic component he
now has to eval and keep from regressing.* For what? Marginal recall on categories
that are already strong. He cuts it, and crucially **writes down why**, so the
next engineer (or the next agent) doesn't helpfully "fix" the omission:

```text
/speckit.plan Remove the LLM-judge pass for v1 and record the rationale in plan.md:
it doubles latency/cost and adds a second model to eval for marginal recall on
categories already covered. Revisit only if eval shows a recall gap that determinism
and a single extractor can't close. Keep the architecture as flat as the problem
allows — no message queue, no service split; this is one process until proven
otherwise.
```

**Smell 2 — and this is the real insight — the architecture is upside down.**
While reviewing `research.md`, Deniz notices that T.C. national IDs and IBANs have
*checksums*. The highest-liability categories don't need a model at all; a few
lines of deterministic validation are more accurate than any LLM and trivially
auditable. That inverts the design: **this is mostly a deterministic system, with
AI used only where determinism fails (names, free-form addresses).** The "AI
product" is 80% boring code, and that's a feature — boring code is auditable, and
auditability is the actual requirement.

```text
/speckit.plan Restructure detection around determinism-first: regex + checksum
validators own T.C. IDs, IBANs, and phones (these are exact and auditable). The
LLM extractor handles only names and free-form addresses, where determinism fails.
Make the validator path the default and the model path the exception. Note in
plan.md: this is deliberate — the most legally sensitive categories must be
explainable without invoking a model.
```

⟶ **Lesson.** Two senior reflexes here. First: **the model never volunteers the
cost of its suggestions** — latency, money, a new failure surface, eval burden —
so you must price every "let's also add…" yourself and often decline. Second: the
best architectural insight in an AI product is frequently *use less AI* — push
work onto deterministic, auditable code wherever it actually works, and reserve
the model for the irreducibly fuzzy part. Read `research.md` and `plan.md` like a
design review, because that's the last place a bad structure is cheap to kill.

He overrides one of the simplicity-gate's own suggestions (it wanted a separate
validation microservice "for scalability") with a one-line documented exception —
*premature; one process until load data says otherwise.* Gates inform; they don't
command. A senior overrides them **with a written reason**, which is different from
ignoring them.

### Tasks & analyze — using the cheap audit as a real gate

```text
/speckit.tasks Break the plan into tasks
/speckit.analyze Run a project analysis for consistency
```

`analyze` is read-only and catches one thing that matters: the override-audit
requirement Deniz injected during clarify has **no task**. It would have silently
not been built — and it's the core trust mechanism. He adds it and re-runs until
clean.

⟶ **Lesson.** A requirement with no task is a feature that won't exist, and nobody
will notice until it's missing in production. `analyze` is a near-free adversarial
reader; treating "clean analyze" as a hard gate before implementing is one of the
highest-leverage habits in the whole method. The cost of running it is a minute;
the cost of the gap it finds is a postmortem.

### Implement — it drifts, and the process (not your vigilance) catches it

He never one-shots this. He scopes by phase, because he knows the model degrades
as context fills — it starts strong and hallucinates around the edges of a long
run:

```text
# Foundation first; nothing else can be trusted until the engine + evals exist.
/speckit.implement execute the Setup and Foundational phases only, then stop and
report
```

He runs the eval harness himself before going further, because for a model
component **"the unit tests pass" and "it actually detects well" are different
claims**, and only the eval set speaks to the second.

Then, mid-build around task 7, the model does something very on-brand: in a new
error handler, it logs the offending document snippet to help debugging. That
violates constitution principle (3) — raw text in logs. Deniz doesn't catch it by
reading every line; nobody reliably does that. He catches it because he'd written
a test that greps emitted logs for PII patterns. **The failure mode he predicted,
he instrumented for.**

```text
# He'd added this as a foundational task precisely because he knew the model
# would eventually "helpfully" log raw text. The test is the guard, not his eyes.
/speckit.implement the log-redaction test is failing on the new error handler —
fix the handler to log a reference id, not document content, and confirm the test
passes
```

⟶ **Lesson.** You cannot out-vigilance a tireless collaborator by reading harder.
You beat its predictable failures by **building the trap before it walks into
them**: a test that fails on the exact mistake you know it tends to make. The
constitution names the invariant; a test makes the invariant self-enforcing. That
pairing is the difference between a principle and a hope.

### The spec was *still* wrong — and here's where SDD pays for itself

Foundation, detection, review UI, audit — all built, all green, demo to the
compliance team. It fails. Not on a bug. The reviewers won't sign off, because
**they can't see what's under a mask without un-masking the whole document**, and
un-masking in front of others is exactly the exposure they're trying to avoid. The
product is technically correct and practically useless. The trust mechanism Deniz
was so proud of is unusable in the room where trust actually happens.

This is the expensive discovery — the kind that, in a code-first project, means a
painful rewrite. Here it's a *spec* problem (he never specified *how* a reviewer
inspects a mask safely), so he fixes it where it's cheap: he edits intent, then
lets convergence find the delta between the new intent and the built reality.

```text
# Fix the SPEC, then reconcile reality to it. Not a hand-patch in the UI —
# the change has to live in intent so it survives the next person.
/speckit.clarify Add the missing requirement: a reviewer must be able to inspect
the original value behind a single mask, in place, visible only to them, without
exposing the rest of the document or persisting the reveal. Specify the audit
consequence: each reveal is itself an audited event.

/speckit.converge Assess the codebase against the updated spec and append the
missing work as tasks.

/speckit.implement execute the newly appended tasks
```

⟶ **Lesson.** This is the entire argument for SDD in one event. You *will* discover
late that the spec was wrong — that's not a process failure, it's the nature of
building things for real humans, whose needs you can't fully know in advance. The
question SDD answers is: **when that discovery lands, does it cost a paragraph or a
rewrite?** Because the intent lived in a spec the system regenerates from, a
demo-day catastrophe became an afternoon. That's the payoff — not the clean happy
path, but the cheap recovery from the inevitable wrong turn.

### Ship — the gate that lets him sleep

CI runs tests *and* the eval suite; a recall regression below threshold fails the
build, so the model can't silently get worse over time. The log-PII test and the
export-block test are non-negotiable gates. The human approval step is the actual
product. None of this is ceremony — each one is a specific way the system could
have hurt someone, turned into a wall.

⟶ **Lesson.** "Done" for an AI product isn't "it works." It's "I know the specific
ways this can fail, and each one is now something that fails the build instead of
failing a customer." That confidence is what you're actually shipping.

---

## Reading generated artifacts adversarially: a smell guide

The single most valuable skill SDD demands is reading the model's output like a
hostile reviewer. Concrete tells, by artifact:

**In a spec:**

- It optimizes a *metric* (accuracy, speed) when your real problem is a
  *property* (trust, safety, defensibility). → It solved the legible problem, not
  yours.
- Edge cases are all the *easy* ones (empty input, too long). The expensive edge
  cases — conflict, disagreement, partial failure, liability — are absent. →
  The model lists what's conventional, not what's dangerous *here*.
- It reads complete and you can't find a single `[NEEDS CLARIFICATION]`. → It
  guessed confidently instead of flagging the unknowns. Suspicious, not
  reassuring.

**In a plan:**

- An extra service, queue, cache, or abstraction "for scale/flexibility" with no
  number justifying it. → Plausible over-engineering; make it justify itself or cut
  it.
- A new non-deterministic component added "to be safe." → Price the latency, cost,
  and *new eval burden* it creates. Usually not worth it.
- Heavy machinery where a checksum, a regex, or a constraint would be exact and
  auditable. → The best move is often *less* sophistication, not more.

**In tasks:**

- A requirement you fought for during clarify has no corresponding task. →
  `analyze` exists to catch exactly this; gate on it.
- A task you can't imagine writing a test for. → It's underspecified upstream; the
  vagueness is in the spec, not the task.

The meta-tell across all three: **fluency where there should be friction.** If the
hard, contested part of your problem came out smooth and confident, the model
papered over it. Go look there first.

---

## Where SDD fights you, and what a senior does about it

Pretending the method is all upside is its own kind of decoration. The honest
failure modes:

- **It can make wrong decisions feel settled.** A beautifully formatted spec
  carries false authority. Counter: treat every artifact as a draft under
  suspicion until *you've* attacked it, regardless of how finished it looks.
- **Clarify and analyze can devolve into pedantry** — asking about themes,
  flagging trivia. Counter: take the two questions that matter, ignore the noise,
  and supply the one they missed. The commands serve your judgment, not the
  reverse.
- **The structure can seduce you into completing the workflow instead of solving
  the problem.** Running all ten commands feels productive. Counter: if a step
  isn't surfacing disagreement or reducing risk, skip it. Ceremony is the enemy.
- **Long `implement` runs rot.** The model loses the plan as context fills.
  Counter: scope every run to a phase or a task range; review between; let the
  `[X]` markers resume you. Never one-shot anything large.
- **The spec can drift from the code** the moment you hand-patch. Counter: route
  changes through the spec → `converge` → `implement`. The instant the spec stops
  matching reality, it stops being load-bearing and you've silently reverted to
  code-as-truth.

### Calibration: how much process is the right amount

| Situation | What a senior actually does |
| --- | --- |
| Throwaway spike, learning something | Skip the apparatus. One tight `/speckit.implement` prompt or just write it. |
| Small change to a known system | specify → plan → tasks → implement. Skip the wrappers; the risk is low. |
| Load-bearing feature, real consequences | Full adversarial pass: clarify, checklist on the risky domain, gate on clean analyze, scope implement, review per phase against evals. |
| You're not sure what you're even building | *Stop.* Spend the t0 thinking. The tool can't do this part and will happily build the wrong thing. |
| Requirements changed on a live feature | Edit the spec → converge → implement. Never a stray commit. |

The skill isn't running more steps. It's spending exactly enough structure to keep
yourself honest, and not one step of theater past that.

---

## If you remember five things

1. **The model is a fast, confident, predictably-wrong collaborator.** Your stance
   is adversarial: every artifact is a suspect until you've attacked it.
2. **SDD's value is cheap, early disagreement.** Every loop drags a future
   expensive mistake into a present cheap one. A step that surfaces no
   disagreement is theater.
3. **The real problem usually isn't the one you typed.** The t0 reframing — done
   by you, before any command — prevents the most expensive class of mistake.
4. **Instrument for the failures you can predict.** Don't out-vigilance the tool;
   build the test that fails on the mistake you know it'll make, and let the
   constitution name the invariant.
5. **Going backwards is the method working.** You will discover the spec was wrong
   late. The win condition isn't avoiding that — it's that fixing intent and
   regenerating costs a paragraph instead of a rewrite.

---

## Appendix — the commands, compressed

You'll learn these by using them. They are instruments for the thinking above, not
the point of it.

| Command | Its job | The senior question it serves |
| --- | --- | --- |
| `constitution` | Binding principles, enforced as plan-time gates | *Which tempting wrong decisions do I want dead on arrival?* |
| `specify` | Natural language → structured spec (+ feature branch) | *What problem am I actually solving — and is this spec aimed at it?* |
| `clarify` | Up to 5 questions; answers encoded into the spec | *What's uniquely dangerous to leave unsaid here — including what it didn't ask?* |
| `plan` | Spec + stack → technical design, research, contracts | *What does each choice cost, and where is this over-built?* |
| `checklist` | "Unit tests for the requirements" — quality, not behavior | *Are the requirements in my risky domain actually airtight?* |
| `tasks` | Plan → ordered, `[P]`-parallelizable task list | *Is every hard-won requirement represented as buildable, testable work?* |
| `analyze` | Read-only cross-artifact consistency audit | *What did we say we'd build that has no task — or build with no reason?* |
| `taskstoissues` | Tasks → dependency-ordered GitHub issues | *How do humans and agents share this work with full context?* |
| `implement` | Executes tasks, marking `[X]`; scope it by phase | *How do I keep context healthy and review before it drifts?* |
| `converge` | Reconcile code-on-disk with intent; append the delta | *Reality changed — how do I make the spec true again instead of patching code?* |

Customization that lets the method match *your* SDLC rather than the default:
**extensions** (`git`, `bug` for spec-driven debugging, `agent-context`),
**presets** (`lean` trims the pipeline), and **bundles** (developer / PM / BA /
security role setups).

*Deeper reading in this repo: [`spec-driven.md`](../../spec-driven.md),
[`docs/concepts/sdd.md`](../concepts/sdd.md),
[`docs/concepts/complex-features.md`](../concepts/complex-features.md),
[`docs/guides/evolving-specs.md`](./evolving-specs.md).*
