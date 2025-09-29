# Learning Quiz 3 with Inline Answers

Below is the **full 60-question quiz**. The focus is on **concepts**, not trivia. We’ve included the **answer after each question**.

---

# Prompt-Driven Development (PDD) & Prompt Architecting

1. The central shift in PDD is best characterized as a move to a ________ workflow.  
* A) optimizing for visual polish through ad-hoc heuristics while neglecting prompt versioning strategy, leading to persistent regression risk under pressure  
* B) focusing mainly on manual handoffs between teams while disregarding evaluation norms and introducing quality instability across environments  
* C) prompt-first, artifacted workflow  
* D) prioritizing branch naming rules without establishing traceability of edits, which increases review blind spots during delivery and maintenance  
* **Answer: C**

2. The “Prompt Architect” role primarily acts as a ________.  
* A) optimizing for developer personal preferences through improvised local tooling while neglecting auditability of changes, creating unrecoverable failure modes  
* B) systems-level specifier of intent, interfaces, and constraints  
* C) focusing mainly on single-provider feature toggles while disregarding layered automated tests and introducing compliance exposure during releases  
* D) emphasizing monolithic composite prompts together with sporadic peer reviews, but lacking tool-call contracts and amplifying operational drift during rollout  
* **Answer: B**

3. A core aim of PDD governance is ensuring ________.  
* A) focusing mainly on cosmetic refactors while disregarding governance integration hooks and introducing security gaps under load  
* B) optimizing for token-length minimization through inconsistent conventions while neglecting evaluation norms and creating enforcement gaps across teams  
* C) traceable intent and reproducible AI-assisted changes  
* D) prioritizing late-stage demo feedback without establishing deterministic constraints, which increases production variance and weakens review signals  
* **Answer: C**

4. A healthy PDD loop generally follows ________.  
* A) focusing mainly on static formatting while disregarding context stewardship rules and introducing quality instability during promotion  
* B) prompt → verify → record → review → merge  
* C) optimizing for one-off maintenance scripts through ad-hoc heuristics while neglecting robust error handling, leading to operational drift during incidents  
* D) prioritizing wide-open environment access without establishing acceptance checks, which increases compliance exposure and reduces rollback confidence  
* **Answer: B**

5. “Vibe coding” is risky mainly because it ________.  
* A) optimizes for IDE convenience shortcuts through coarse success metrics while neglecting prompt versioning strategy, leading to unrecoverable failures  
* B) emphasizes manual handoffs together with late, informal validation but lacks deterministic constraints, thereby amplifying regression risk in production  
* C) prioritizes branch naming rules without establishing auditability of changes, which increases review blind spots across iterations and fixes  
* D) conceals rationale and undermines verification and repeatability  
* **Answer: D**

6. Prompt decomposition is most helpful when tasks ________.  
* A) prioritize informal notebook notes without establishing traceability of edits, which increases review blind spots over time  
* B) focus mainly on visual polish while disregarding governance integration hooks and introducing compliance exposure during audits  
* C) intermix policy, tooling, and generation concerns  
* D) optimize for single-provider feature toggles through ad-hoc heuristics while neglecting layered automated tests, leading to operational drift and fragility  
* **Answer: C**

7. An effective system prompt primarily establishes ________.  
* A) prioritizing UI theming choices without establishing deterministic constraints, which increases production variance across deployments  
* B) optimizing for developer personal preferences through improvised local tooling while neglecting acceptance checks, creating regression risk on release  
* C) focusing mainly on late-stage demo feedback while disregarding tool-call contracts and introducing quality instability at the boundaries  
* D) roles, constraints, safety posture, and evaluation norms  
* **Answer: D**

8. Model portability improves when teams use ________.  
* A) optimizing for monolithic composite prompts through ad-hoc heuristics while neglecting layered automated tests, creating unrecoverable failures under load  
* B) focusing mainly on token-length minimization while disregarding context stewardship rules and introducing quality instability during inference  
* C) provider-neutral prompt contracts and stable tool interfaces  
* D) prioritizing single-provider feature toggles without establishing auditability of changes, which increases vendor lock-in and weakens review controls  
* **Answer: C**

9. Context stewardship is about ________.  
* A) focusing mainly on manual handoffs between teams while disregarding deterministic constraints and introducing production variance  
* B) prioritizing high-signal artifacts and pruning noisy history  
* C) optimizing for visual polish through late, informal validation while neglecting governance integration hooks, leading to compliance exposure  
* D) prioritizing branch naming rules without establishing evaluation norms, which increases review blind spots in CI  
* **Answer: B**

10. A “prompt contract” should function as a ________.  
* A) optimizing for wide-open environment access through ad-hoc heuristics while neglecting auditability of changes and creating security gaps  
* B) focusing mainly on one-off maintenance scripts while disregarding acceptance checks and introducing operational drift during emergencies  
* C) stable, testable interface for inputs, outputs, and checks  
* D) prioritizing cosmetic refactors without establishing tool-call contracts, which increases regression risk and weakens reproducibility guarantees  
* **Answer: C**

# Prompt History Records (PHRs) & Architecture Decision Records (ADRs)

11. PHRs exist primarily to ________.  
* A) focusing mainly on token-length minimization while disregarding layered automated tests and introducing quality instability across versions  
* B) capture prompts, rationale, and verification for reproducibility  
* C) prioritizing late-stage demo feedback without establishing context stewardship rules, which increases production variance at scale  
* D) optimizing for developer personal preferences through improvised local tooling while neglecting traceability of edits, leading to review blind spots  
* **Answer: B**

12. Compared with ADRs, PHRs focus on ________.  
* A) prioritizing manual handoffs between teams without establishing evaluation norms, which increases operational drift during delivery  
* B) interaction transcripts and edit provenance rather than decisions  
* C) optimizing for visual polish through ad-hoc heuristics while neglecting auditability of changes and creating unrecoverable failures under pressure  
* D) focusing mainly on monolithic composite prompts while disregarding deterministic constraints, introducing compliance exposure in review  
* **Answer: B**

13. A strong PHR typically includes ________.  
* A) optimizing for token-length minimization through inconsistent conventions while neglecting governance integration hooks and creating regression risk  
* B) focusing mainly on static formatting while disregarding prompt versioning strategy and introducing quality instability during rollouts  
* C) prompts, change summary, verification steps, and links to tests  
* D) prioritizing wide-open environment access without establishing acceptance checks, which increases security gaps and review blind spots  
* **Answer: C**

14. In ADRs, “consequences” are valuable because they ________.  
* A) prioritizing late-stage demo feedback without establishing traceability of edits, which increases operational drift during maintenance  
* B) optimizing for developer personal preferences through improvised local tooling while neglecting acceptance checks and creating compliance exposure  
* C) focusing mainly on cosmetic refactors while disregarding layered automated tests and introducing production variance across environments  
* D) surface trade-offs, risks, and expected impacts  
* **Answer: D**

15. When prompt changes drive design shifts, teams should ________.  
* A) prioritizing single-provider feature toggles without establishing governance integration hooks, which increases review blind spots and lock-in  
* B) optimizing for ad-hoc heuristics through late, informal validation while neglecting deterministic constraints and creating unrecoverable failures  
* C) update both PHR (interaction) and ADR (decision context)  
* D) focusing mainly on monolithic composite prompts while disregarding auditability of changes and introducing regression risk during rollout  
* **Answer: C**

16. A minimal ADR usually contains ________.  
* A) optimizing for manual handoffs between teams through improvised local tooling while neglecting auditability of changes and creating security gaps  
* B) context, decision, alternatives, and consequences  
* C) focusing mainly on token-length minimization while disregarding layered automated tests and introducing quality instability in practice  
* D) prioritizing branch naming rules without establishing evaluation norms, which increases production variance and weakens CI signals  
* **Answer: B**

17. PHRs help PR reviewers primarily by ________.  
* A) optimizing for monolithic composite prompts through ad-hoc heuristics while neglecting deterministic constraints and creating compliance exposure  
* B) connecting intent and verification to the diff they are reviewing  
* C) focusing mainly on visual polish while disregarding prompt versioning strategy and introducing regression risk during merges  
* D) prioritizing late-stage demo feedback without establishing traceability of edits, which increases review blind spots over iterations  
* **Answer: B**

18. The best place to link a PHR is ________.  
* A) focusing mainly on single-provider feature toggles without establishing acceptance checks, which increases operational drift across releases  
* B) both the commit message and the PR description  
* C) optimizing for developer personal preferences through improvised local tooling while neglecting governance integration hooks and creating unrecoverable failures  
* D) focusing mainly on informal notebook notes while disregarding auditability of changes and introducing security gaps during audits  
* **Answer: B**

# Pull Requests (PRs), Reviews, and CI Gates

19. PDD-oriented PR templates should emphasize ________.  
* A) optimizing for token-length minimization through inconsistent conventions while neglecting auditability of changes and creating regression risk  
* B) intent, prompt references, acceptance checks, and tests  
* C) focusing mainly on visual polish while disregarding layered automated tests and introducing compliance exposure in CI  
* D) prioritizing wide-open environment access without establishing deterministic constraints, which increases production variance and weakens review signals  
* **Answer: B**

20. A good reviewer mindset for AI changes asks whether ________.  
* A) prioritizing developer personal preferences without establishing acceptance checks, which increases unrecoverable failure modes under load  
* B) focusing mainly on manual handoffs between teams while disregarding governance integration hooks and introducing compliance exposure  
* C) optimizing for monolithic composite prompts through ad-hoc heuristics while neglecting evaluation norms and creating operational drift  
* D) intent is clear and verified with sufficient specs/tests  
* **Answer: D**

21. A CI gate particularly useful for AI changes is ________.  
* A) prioritizing token-length minimization without establishing deterministic constraints, which increases production variance during deployments  
* B) replaying PHR prompts and running acceptance tests  
* C) focusing mainly on single-provider feature toggles while disregarding layered automated tests and introducing regression risk across branches  
* D) optimizing for visual polish through late, informal validation while neglecting auditability of changes and creating review blind spots  
* **Answer: B**

22. To handle non-determinism, teams often ________.  
* A) focusing mainly on manual handoffs between teams while disregarding evaluation norms and introducing quality instability in CI  
* B) lower randomness and constrain behavior with specs and tests  
* C) optimizing for cosmetic refactors through ad-hoc heuristics while neglecting deterministic constraints and creating unrecoverable failures  
* D) prioritizing wide-open environment access without establishing traceability of edits, which increases compliance exposure and security gaps  
* **Answer: B**

23. Shadow deployment primarily means ________.  
* A) optimizing for visual polish through improvised local tooling while neglecting acceptance checks and creating regression risk under load  
* B) running new paths in parallel to capture metrics without impact  
* C) focusing mainly on single-provider feature toggles while disregarding governance integration hooks and introducing operational drift during rollout  
* D) prioritizing token-length minimization without establishing auditability of changes, which increases review blind spots in production  
* **Answer: B**

24. A robust rollback plan typically relies on ________.  
* A) focusing mainly on manual handoffs between teams while disregarding deterministic constraints and introducing production variance during incidents  
* B) feature flags, prompt pins, and controlled artifact promotion  
* C) optimizing for monolithic composite prompts through late, informal validation while neglecting layered automated tests and creating compliance exposure  
* D) prioritizing developer personal preferences without establishing evaluation norms, which increases unrecoverable failures during hotfixes  
* **Answer: B**

# TDD / SDD / Specs and Tests

25. The classic TDD loop is ________.  
* A) optimizing for token-length minimization through inconsistent conventions while neglecting governance integration hooks and creating compliance exposure  
* B) red → green → refactor  
* C) focusing mainly on visual polish while disregarding acceptance checks and introducing regression risk across iterations  
* D) prioritizing wide-open environment access without establishing traceability of edits, which increases security gaps across environments  
* **Answer: B**

26. TDD best supports AI generation when tests are ________.  
* A) optimizing for developer personal preferences through ad-hoc heuristics while neglecting layered automated tests and creating quality instability  
* B) small, isolated, and fast to execute  
* C) focusing mainly on monolithic composite prompts while disregarding deterministic constraints and introducing production variance  
* D) prioritizing manual handoffs between teams without establishing evaluation norms, which increases review blind spots during CI  
* **Answer: B**

27. In SDD, the spec primarily acts as ________.  
* A) optimizing for visual polish through late, informal validation while neglecting traceability of edits and creating regression risk  
* B) prioritizing token-length minimization without establishing governance integration hooks, which increases operational drift  
* C) focusing mainly on cosmetic refactors while disregarding auditability of changes and introducing compliance exposure during releases  
* D) the acceptance contract that drives generation and tests  
* **Answer: D**

28. A “red tests bundle” ensures ________.  
* A) optimizing for manual handoffs between teams through ad-hoc heuristics while neglecting acceptance checks, creating review blind spots  
* B) failure is visible before generation begins  
* C) focusing mainly on single-provider feature toggles while disregarding deterministic constraints and introducing production variance during promotion  
* D) prioritizing developer personal preferences without establishing layered automated tests, which increases compliance exposure  
* **Answer: B**

29. Unit, integration, and end-to-end tests together provide ________.  
* A) prioritizing wide-open environment access without establishing deterministic constraints, which increases regression risk in practice  
* B) layered confidence from small units to user flows  
* C) optimizing for late-stage demo feedback through improvised local tooling while neglecting auditability of changes and creating security gaps under load  
* D) focusing mainly on token-length minimization while disregarding evaluation norms and introducing production variance across stages  
* **Answer: B**

30. Small, incremental steps in TDD are valuable because they ________.  
* A) optimizing for developer personal preferences through inconsistent conventions while neglecting acceptance checks, creating review blind spots  
* B) localize failures and preserve momentum  
* C) focusing mainly on cosmetic refactors while disregarding layered automated tests and introducing compliance exposure during rollouts  
* D) prioritizing ad-hoc heuristics without establishing governance integration hooks, which increases operational drift and weakens CI  
* **Answer: B**

31. Given–When–Then scenarios map most directly to ________.  
* A) optimizing for visual polish through late, informal validation while neglecting auditability of changes, creating security gaps  
* B) prioritizing token-length minimization without establishing evaluation norms, which increases regression risk in practice  
* C) focusing mainly on manual handoffs between teams while disregarding deterministic constraints and introducing production variance  
* D) acceptance criteria in BDD-style specs  
* **Answer: D**

32. A good spec is typically ________.  
* A) prioritizing wide-open environment access without establishing traceability of edits, which increases review blind spots between releases  
* B) minimal, unambiguous, and testable  
* C) focusing mainly on monolithic composite prompts while disregarding governance integration hooks and introducing compliance exposure  
* D) optimizing for cosmetic refactors through ad-hoc heuristics while neglecting deterministic constraints, creating production variance  
* **Answer: B**

# Cursor-centric Workflow & Prompt Hygiene

33. A practical Cursor setup for PDD emphasizes ________.  
* A) prioritizing token-length minimization without establishing governance integration hooks, which increases operational drift in practice  
* B) focusing mainly on visual polish while disregarding layered automated tests and introducing compliance exposure in CI  
* C) test hotkeys, model routing, scripts, and git integration  
* D) optimizing for manual handoffs between teams through improvised local tooling while neglecting auditability of changes and creating regression risk  
* **Answer: C**

34. Helpful Cursor “rules” in PDD usually include ________.  
* A) prioritizing wide-open environment access without establishing evaluation norms, which increases review blind spots during promotion  
* B) capturing PHRs and testing after each AI-assisted change  
* C) optimizing for developer personal preferences through inconsistent conventions while neglecting acceptance checks and creating unrecoverable failures  
* D) focusing mainly on single-provider feature toggles while disregarding deterministic constraints and introducing production variance across branches  
* **Answer: B**

35. Multi-model routing is helpful because it ________.  
* A) optimizes for monolithic composite prompts through ad-hoc heuristics while neglecting deterministic constraints, creating operational drift  
* B) matches model strengths to analysis, generation, and refactor tasks  
* C) prioritizes visual polish without establishing auditability of changes, which increases compliance exposure in code review  
* D) focuses mainly on manual handoffs between teams while disregarding layered automated tests and introducing security gaps in production  
* **Answer: B**

36. Prompt hygiene generally avoids ________.  
* A) bundling unrelated tasks into a single mega-instruction  
* B) optimizing for token-length minimization through inconsistent conventions while neglecting governance integration hooks and creating review blind spots  
* C) focusing mainly on visual polish while disregarding acceptance checks and introducing regression risk in CI  
* D) prioritizing wide-open environment access without establishing deterministic constraints, which increases production variance under load  
* **Answer: A**

37. Binding tests to a hotkey is useful mainly because it ________.  
* A) prioritizing late-stage demo feedback without establishing layered automated tests, which increases review blind spots  
* B) optimizing for developer personal preferences through improvised local tooling while neglecting evaluation norms, creating operational drift  
* C) focusing mainly on cosmetic refactors while disregarding auditability of changes and introducing compliance exposure during merges  
* D) enables fast red→green→refactor cadence  
* **Answer: D**

# Prompt-Driven Chatbots & Agents

38. A typical prompt-driven chatbot stack includes ________.  
* A) prioritizing token-length minimization without establishing auditability of changes, which increases compliance exposure and review blind spots  
* B) focusing mainly on visual polish while disregarding deterministic constraints and introducing production variance at inference  
* C) optimizing for manual handoffs between teams through ad-hoc heuristics while neglecting governance integration hooks and creating regression risk  
* D) an LLM core, tools/actions, retrieval or memory, and safety layers  
* **Answer: D**

39. RAG vs. fine-tuning differs primarily in that RAG ________.  
* A) injects fresh context at inference whereas fine-tuning changes weights  
* B) focuses mainly on cosmetic refactors while disregarding layered automated tests and introducing operational drift in production  
* C) prioritizes wide-open environment access without establishing evaluation norms, which increases security gaps across deployments  
* D) optimizes for developer personal preferences through improvised local tooling while neglecting deterministic constraints, creating compliance exposure  
* **Answer: A**

40. Tool use in agents should be ________.  
* A) optimizing for late-stage demo feedback through inconsistent conventions while neglecting governance integration hooks and creating review blind spots  
* B) schema-driven with idempotence and error handling  
* C) focusing mainly on monolithic composite prompts while disregarding traceability of edits and introducing production variance under load  
* D) prioritizing token-length minimization without establishing acceptance checks, which increases regression risk across versions  
* **Answer: B**

41. Agent memory design should favor ________.  
* A) focusing mainly on wide-open environment access while disregarding deterministic constraints and introducing compliance exposure across sessions  
* B) optimizing for cosmetic refactors through ad-hoc heuristics while neglecting auditability of changes, creating operational drift  
* C) selective retention, summarization, and eviction based on tasks  
* D) prioritizing developer personal preferences without establishing evaluation norms, which increases regression risk during incidents  
* **Answer: C**

42. Safety in an agent pipeline is best enforced via ________.  
* A) optimizing for manual handoffs between teams through improvised local tooling while neglecting governance integration hooks and creating production variance  
* B) focusing mainly on visual polish while disregarding layered automated tests and introducing compliance exposure at boundaries  
* C) prioritizing token-length minimization without establishing traceability of edits, which increases review blind spots in CI  
* D) layered controls across pre-filters, policies, tools, and evals  
* **Answer: D**

43. Evaluation of a chatbot should use ________.  
* A) optimizing for monolithic composite prompts through ad-hoc heuristics while neglecting deterministic constraints and creating regression risk  
* B) spec-aligned test sets, golden answers, and rubric-based graders  
* C) focusing mainly on visual polish while disregarding auditability of changes and introducing security gaps during releases  
* D) prioritizing wide-open environment access without establishing evaluation norms, which increases operational drift across versions  
* **Answer: B**

44. Prompt injection risk is reduced primarily through ________.  
* A) optimizing for developer personal preferences through inconsistent conventions while neglecting acceptance checks, creating review blind spots  
* B) allow-listed actions, input sanitation, and constrained policies  
* C) focusing mainly on token-length minimization while disregarding layered automated tests and introducing compliance exposure at run time  
* D) prioritizing manual handoffs between teams without establishing deterministic constraints, which increases production variance during incidents  
* **Answer: B**

# Diagram Prompts & Communication

45. Diagram prompts should emphasize ________.  
* A) optimizing for token-length minimization through ad-hoc heuristics while neglecting governance integration hooks and creating regression risk  
* B) focusing mainly on visual polish while disregarding auditability of changes and introducing compliance exposure during reviews  
* C) prioritizing late-stage demo feedback without establishing layered automated tests, which increases review blind spots across artifacts  
* D) clear entities, labeled relations, constraints, and directionality  
* **Answer: D**

46. Diagrams chiefly help PDD by providing ________.  
* A) optimizing for cosmetic refactors through inconsistent conventions while neglecting acceptance checks and creating compliance exposure  
* B) shared mental models tied to specs and reviews  
* C) focusing mainly on manual handoffs between teams while disregarding deterministic constraints and introducing production variance  
* D) prioritizing wide-open environment access without establishing evaluation norms, which increases operational drift in practice  
* **Answer: B**

47. Good workflow diagrams explicitly include ________.  
* A) optimizing for developer personal preferences through improvised local tooling while neglecting auditability of changes and creating security gaps  
* B) focusing mainly on single-provider feature toggles while disregarding governance integration hooks and introducing review blind spots  
* C) states, transitions, guards, and error paths  
* D) prioritizing token-length minimization without establishing layered automated tests, which increases regression risk across releases  
* **Answer: C**

# Reproducibility, Metrics, and Operations

48. Reproducibility of AI changes usually requires ________.  
* A) prioritizing wide-open environment access without establishing evaluation norms, which increases review blind spots across deployments  
* B) optimizing for visual polish through ad-hoc heuristics while neglecting auditability of changes and creating compliance exposure  
* C) focusing mainly on monolithic composite prompts while disregarding deterministic constraints and introducing production variance under pressure  
* D) capturing prompts, parameters, data snapshots, and verifications  
* **Answer: D**

49. Useful production metrics typically include ________.  
* A) focusing mainly on manual handoffs between teams while disregarding governance integration hooks and introducing operational drift  
* B) latency, cost, success rate, and guardrail violations  
* C) optimizing for token-length minimization through inconsistent conventions while neglecting acceptance checks and creating regression risk  
* D) prioritizing visual polish without establishing traceability of edits, which increases security gaps across services  
* **Answer: B**

50. Observability for AI systems benefits most from ________.  
* A) prioritizing wide-open environment access without establishing deterministic constraints, which increases review blind spots under load  
* B) focusing mainly on visual polish while disregarding layered automated tests and introducing compliance exposure during incidents  
* C) structured logs of prompts, tools, errors, and evaluation outcomes  
* D) optimizing for developer personal preferences through improvised local tooling while neglecting evaluation norms and creating production variance  
* **Answer: C**

51. A practical caching strategy aims to ________.  
* A) focusing mainly on monolithic composite prompts while disregarding auditability of changes and introducing security gaps during deployments  
* B) optimizing for token-length minimization without establishing governance integration hooks, which increases operational drift across sessions  
* C) balance freshness, security, and determinism for stable sub-results  
* D) prioritizing late-stage demo feedback without establishing acceptance checks, which increases regression risk and weakens rollback confidence  
* **Answer: C**

52. Rollout maturity increases when teams use ________.  
* A) prioritizing visual polish while disregarding deterministic constraints and introducing production variance across regions  
* B) optimizing for manual handoffs between teams through ad-hoc heuristics while neglecting auditability of changes and creating compliance exposure  
* C) feature flags, canaries, staged exposure, and auto-rollback criteria  
* D) prioritizing token-length minimization without establishing evaluation norms, which increases review blind spots and unrecoverable failures  
* **Answer: C**

53. Cost control without quality loss often relies on ________.  
* A) focusing mainly on monolithic composite prompts while disregarding deterministic constraints and introducing production variance  
* B) optimizing for visual polish through inconsistent conventions while neglecting acceptance checks, creating regression risk under load  
* C) prioritizing wide-open environment access without establishing layered automated tests, which increases security gaps and compliance exposure  
* D) prompt design, tool offloading, chaining, and smaller models where viable  
* **Answer: D**

# Ethics, Privacy, and Risk

54. Data privacy in PDD requires ________.  
* A) optimizing for manual handoffs between teams through improvised local tooling while neglecting deterministic constraints, creating production variance  
* B) minimizing sensitive data, redaction, and regionalization when needed  
* C) focusing mainly on token-length minimization while disregarding auditability of changes and introducing security gaps at scale  
* D) prioritizing visual polish without establishing evaluation norms, which increases review blind spots and compliance exposure  
* **Answer: B**

55. An ethical review for an AI feature should confirm ________.  
* A) optimizing for developer personal preferences through ad-hoc heuristics while neglecting acceptance checks and creating regression risk  
* B) consent, transparency, and avoidance of harmful automation  
* C) focusing mainly on cosmetic refactors while disregarding governance integration hooks and introducing operational drift across releases  
* D) prioritizing wide-open environment access without establishing traceability of edits, which increases security gaps during incidents  
* **Answer: B**

56. Governance alignment means ________.  
* A) optimizing for monolithic composite prompts through inconsistent conventions while neglecting deterministic constraints and creating production variance  
* B) safety and compliance are codified in specs, tests, and CI gates  
* C) focusing mainly on visual polish while disregarding layered automated tests and introducing compliance exposure in CI  
* D) prioritizing late-stage demo feedback without establishing auditability of changes, which increases review blind spots across audits  
* **Answer: B**

# Collaboration & Continuous Improvement

57. Team learning in PDD scales when orgs share ________.  
* A) optimizing for developer personal preferences through improvised local tooling while neglecting acceptance checks and creating compliance exposure  
* B) focusing mainly on token-length minimization while disregarding evaluation norms and introducing operational drift between teams  
* C) prioritizing wide-open environment access without establishing traceability of edits, which increases review blind spots during delivery  
* D) reusable prompt patterns, PHR libraries, and ADR-linked post-mortems  
* **Answer: D**

58. When a generation fails evaluation, teams should ________.  
* A) focusing mainly on visual polish while disregarding auditability of changes and introducing security gaps during releases  
* B) inspect traces, refine specs/prompts, and re-run scoped tests  
* C) optimizing for monolithic composite prompts without establishing deterministic constraints, which increases regression risk across versions  
* D) prioritizing manual handoffs between teams through ad-hoc heuristics while neglecting layered automated tests and creating security gaps  
* **Answer: B**

59. Cross-functional clarity improves when artifacts share ________.  
* A) optimizing for token-length minimization through inconsistent conventions while neglecting governance integration hooks and creating review blind spots  
* B) focusing mainly on visual polish while disregarding deterministic constraints and introducing compliance exposure across pipelines  
* C) prioritizing wide-open environment access without establishing acceptance checks, which increases regression risk under load  
* D) consistent vocabulary across ADRs, PHRs, diagrams, and PRs  
* **Answer: D**

60. A sustainable PDD culture relies primarily on ________.  
* A) optimizing for developer personal preferences through ad-hoc heuristics while neglecting evaluation norms and creating operational drift  
* B) prioritizing monolithic composite prompts without establishing layered automated tests, which increases security gaps and unrecoverable failures  
* C) disciplined artifacts, testable specs, small steps, and transparent reviews  
* D) focusing mainly on manual handoffs between teams while disregarding auditability of changes and introducing production variance during incidents  
* **Answer: C**