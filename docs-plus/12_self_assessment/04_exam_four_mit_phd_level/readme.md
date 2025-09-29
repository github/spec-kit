# Quiz 4

Here’s a **fourth, MIT PhD–level 60-question MCQ quiz** centered on the *concepts* behind GPS Engineering (SDD × PDD × TDD × EDD × ADR × PHR × PR), agent architectures, governance, eval science, and reliability. **Answer key in the answer_key.md file**

---

## Multiple-Choice Questions (MIT PhD Level)

1. In GPS Engineering, which framing best captures **specs as a contract** between generative systems and deterministic components?  
   A) Specs as UI text templates for consistency  
   B) Specs as design docs for managers only  
   C) Specs as Git metadata mirroring code style  
   D) Specs as reference models constraining stochastic generators via externally verifiable obligations  

2. Consider an LLM agent with tools and guardrails. Which **soundness property** is most directly enforced by TDD + contract tests?  
   A) Pareto efficiency of tool selection  
   B) External behavior conformance independent of internal sampling  
   C) Optimal decoding under length penalties  
   D) Model calibration over long horizons  

3. For EDD, which evaluation protocol most robustly **detects regression** across model upgrades?  
   A) Manual spot checks by reviewers  
   B) Randomized seeds with no tracking  
   C) Paired, batched A/B with fixed seeds, multiple replicates, stratified prompts, and nonparametric tests  
   D) Single run with temperature 0.9  

4. Which statement best characterizes **prompt drift** as an empirical phenomenon?  
   A) Only occurs when temperature>1  
   B) Purely UI-driven artifact  
   C) Stationary process with zero variance  
   D) Distributional shift in model outputs given stable inputs due to context accretion or subtle spec leakage  

5. A rigorous **scope discipline** rubric penalizes:  
   A) Lowercase field names  
   B) Omission of optional fields  
   C) Inclusion of unrequested keys or formats even when semantically correct  
   D) Short outputs  

6. When choosing **SSE over WebSocket** for v1, which formal trade-off dominates under GPS?  
   A) Binary frame support for large tensors  
   B) Throughput optimality of bidirectional channels  
   C) Complexity minimization and proxy compatibility for monotonic token emission  
   D) Mandatory server push for images  

7. Which property does **“smallest change to green”** optimize in the presence of flaky behaviors?  
   A) Global optimality of refactor plans  
   B) Semantic coherence of docstrings  
   C) Computational complexity of CI runners  
   D) Causal attribution of test failures to the minimal diff  

8. Under GPS, **model choice** should be governed primarily by:  
   A) Random seed reproducibility only  
   B) IDE popularity  
   C) Spec-linked eval deltas, cost/latency constraints, and stability envelopes  
   D) Marketing and blog posts  

9. Which statement about **PHRs** is most correct in a forensic audit?  
   A) They are transient CI logs  
   B) They duplicate ADRs and can be deleted  
   C) They serve as immutable intent artifacts mapping diffs to prompts and acceptance criteria  
   D) They are optional once code is merged  

10. For adversarial robustness, which **red-team test** belongs in EDD smoke?  
    A) GPU temperature monitoring  
    B) Semantic similarity between comments  
    C) Token count statistics  
    D) Prompt injections targeting tool misuse and field exfiltration scored by policy-violation detectors  

11. In multi-agent orchestration, a **handoff** can be formalized as:  
    A) Intent-conditioned control transfer with invariants on session state and output schema  
    B) Static call graph expansion  
    C) Random walk between agents  
    D) Syntax rewrite rule  

12. A **thin spec** that remains enforceable over time should include:  
    A) Diagram color palettes  
    B) Input/Output contracts, pre/postconditions, error envelopes, and acceptance tests  
    C) Hiring policies  
    D) Implementation pseudocode  

13. Which evaluation design best **bounds variance** in stochastic decoding while estimating performance?  
    A) Unlimited sampling until success  
    B) One sample per item with temperature 0  
    C) Multiple independent samples per item with fixed seeds per version and stratified aggregation  
    D) Randomized seeds each run without logging  

14. What is the **primary epistemic benefit** of ADRs co-located with code?  
    A) Faster merges  
    B) Better syntax highlighting  
    C) Smaller images  
    D) Preservation of decision provenance enabling counterfactual reasoning during incidents  

15. For **reliability**, which metric pair is most diagnostic in GPS dashboards?  
    A) PR description length and emoji density  
    B) Lead time to change and change-failure rate with MTTR overlays  
    C) Lines of code and stars  
    D) Docker layer count and image size  

16. A **governed refactor prompt** should require:  
    A) Maximizing diff size  
    B) Removal of guardrails  
    C) Preservation of public behavior with test invariants; internal restructuring with formal explainer deltas  
    D) Rewriting public contracts  

17. Which **test isolation** strategy is correct for LLM-backed services?  
    A) Tests disabled to reduce variance  
    B) Live calls to frontier models in unit tests  
    C) No mocks, pure integration  
    D) Deterministic mocks for unit/contract tests; model-in-the-loop only in eval stages  

18. The **Spec-Compliance** checkbox in PRs contributes to:  
    A) Enforceable linkage of artifacts: spec→tests/evals→code diffs→PHRs/ADRs  
    B) UI theme consistency  
    C) Faster Docker builds  
    D) Automatic tagging  

19. In PDD, the **Architect prompt** functions as:  
    A) Replacement for ADRs  
    B) Style guide  
    C) Randomizer  
    D) Micro-spec generator capturing scope, constraints, acceptance, and risks pre-implementation  

20. Which is a **valid grounding** for tool-first policy?  
    A) It reduces observability  
    B) It simplifies tracing removal  
    C) It routes deterministic subproblems to verifiable functions, reducing hallucination surface  
    D) It increases temperature  

21. A failure to emit `data:[DONE]` in SSE violates which property?  
    A) Stream termination contract required for client completeness detection  
    B) Linting invariants  
    C) Docker healthcheck  
    D) Safety type system  

22. **Model-agnosticism** at the spec level implies:  
    A) Maintaining contracts and evals that remain valid under provider substitution  
    B) Prohibiting all vendor features  
    C) Fixing one decoding strategy  
    D) Ignoring latency  

23. Which is the **best justification** for “no green, no merge”?  
    A) Converts informal confidence into formal gates that enforce quality before integration  
    B) Removes reviewers  
    C) Encourages larger PRs  
    D) Allows red merges  

24. The **conceptual** benefit of prompt libraries is:  
    A) Increasing token usage  
    B) Standardization of high-leverage patterns with governance and reuse  
    C) Replacing specs  
    D) Removing tests  

25. **Prompt hygiene** avoids:  
    A) Examples  
    B) Ambiguous or bundled tasks that dilute focus  
    C) Clear roles and constraints  
    D) Versioning  

26. **Observability** for agents should record:  
    A) Theme changes  
    B) Tool spans with inputs, outputs, timing, errors  
    C) Only total tokens  
    D) Editor font  

27. **Contract stability** across models is verified by:  
    A) Running the same contract tests and error envelopes after substitution  
    B) Skipping CI  
    C) Asking teammates  
    D) Reading docs  

28. A **governance smell** is when PRs:  
    A) Include EDD artifacts  
    B) Merge on red or without PHR/ADR references  
    C) Are small  
    D) Link specs and ADRs  

29. **Risk triage** in reviews prioritizes:  
    A) Commit puns  
    B) Change surface × criticality with rollback noted  
    C) UI polish first  
    D) Removing CI steps  

30. **Thin slice** heuristic is:  
    A) Large diffs  
    B) Excludes tests  
    C) Spans subsystems  
    D) 1-3 prompts + handful of tests to done  

31. The **governed definition** of GPS Engineering is:  
    A) Governed Prompt Software Engineering unifying specs, prompts, tests, evals, decisions, PR gates  
    B) Single IDE feature  
    C) Prompting technique only  
    D) Dockerfile recipe  

32. A **PHR ID taxonomy** should optimize for:  
    A) Shortest strings only  
    B) Temporal ordering, slice mapping, and diff reproducibility  
    C) Random UUIDs without meaning  
    D) Aesthetic ordering  

33. The **Explainer prompt** contributes to governance by:  
    A) Producing a human-readable rationale and risk notes aligned to diffs and tests  
    B) Hiding ADRs  
    C) Shortening tests  
    D) Removing PR description  

34. Under GPS, which **property** distinguishes tests from evals?  
    A) Tests are optional; evals required  
    B) Tests assert binary conformance; evals assign graded judgments under rubrics  
    C) Tests are stochastic; evals are deterministic  
    D) They are equivalent  

35. An **ADR consequence** should explicitly note:  
    A) Editor shortcut keys  
    B) Font ligatures  
    C) Follow-ups, trade-offs, and triggers that would reopen the decision  
    D) Which memes to use  

36. A sophisticated **scope discipline** eval would:  
    A) Penalize any deviation from declared schema regardless of semantic utility  
    B) Reward additional helpful fields  
    C) Ignore structure  
    D) Reward verbosity  

37. The **causal model** for red→green→refactor is that:  
    A) Incremental isolation raises identifiability of failure sources  
    B) Refactor first reduces entropy  
    C) Big diffs increase discoverability  
    D) Green before red is equivalent  

38. A **model governance smell** is:  
    A) Prompt changes without PHRs or evals  
    B) ADRs linked to PRs  
    C) Specs mapped to tests  
    D) CI artifacts retained  

39. Under GPS, which **artifact pair** provides the most persuasive evidence in a postmortem?  
    A) Number of PR comments  
    B) PHRs with exact prompts plus failing eval artifacts before/after  
    C) Emojis + screenshots  
    D) Code coverage percentage only  

40. Which **calibration** approach is relevant to evals of graded tasks?  
    A) Minifying JSON  
    B) Dark mode  
    C) Isotonic regression or Platt scaling on score distributions across suites  
    D) Increasing temperature  

41. A **privacy-aware** eval design should:  
    A) Include synthetic PII and verify redaction policies under controlled conditions  
    B) Disable logs  
    C) Leak PII to test redaction  
    D) Ignore redaction  

42. **Observability spans** for agent handoffs should include:  
    A) Intent signal, confidence, selected agent, handoff_reason, and tool calls with timing  
    B) File icons  
    C) Only duration  
    D) None; keep silent  

43. A defensible **spec versioning** scheme should:  
    A) Use semantic versioning per contract with migration notes and deprecation windows  
    B) Avoid versions  
    C) Use date emojis  
    D) Overload README headings  

44. What is the **primary statistical risk** of single-run evals on small suites?  
    A) Perfect power  
    B) High variance and Type I/II errors leading to misleading decisions  
    C) Overpowering  
    D) None if seeds fixed  

45. An **LLM safety check** that belongs in EDD smoke is:  
    A) Logo usage  
    B) Restricted tool invocation when policy preconditions unmet  
    C) GPU fan speed  
    D) Tab width  

46. Under GPS, **model substitution** should be accompanied by:  
    A) Only lints  
    B) Re-running behavioral suites with equivalence thresholds and rollback criteria  
    C) New logos  
    D) No action  

47. A **well-posed architect prompt** differs from code requests because it:  
    A) States objectives, constraints, acceptance tests, and non-goals prior to code  
    B) Encourages free writing  
    C) Asks for maximal diffs  
    D) Asks for colors  

48. Which **threat model** is relevant for prompt capture?  
    A) Cache eviction  
    B) Only DoS  
    C) Leakage of secrets or policies via PHRs if not scrubbed and access controlled  
    D) None; prompts are harmless  

49. **Spec creep** should be managed by:  
    A) Turning off evals  
    B) Renegotiating scope with new micro-specs and PRs rather than mutating in-flight slices  
    C) Deleting tests  
    D) Merging big batches  

50. A **maturity signal** for GPS is:  
    A) Ad-hoc CI  
    B) Organization-wide prompt libraries, rules bundles, dashboards, and PR gates  
    C) Unstructured prompts  
    D) Per-dev README forks  

51. For **causal inference** in regressions, which counterfactual is most actionable?  
    A) Random seeds every time  
    B) Re-run previous model on current suite and new model on previous suite under matched seeds  
    C) Only manual QA  
    D) Post-hoc narratives  

52. **Reproducibility** in evals depends most on:  
    A) Fixed datasets, versioned configs, seeds, and execution environment capture  
    B) Proprietary runners  
    C) Large prompts  
    D) Fancy charts  

53. **Policy as code** succeeds when:  
    A) CI enforces lint, tests, eval thresholds, and secret scanning as hard gates  
    B) Guidelines live in slides  
    C) Nothing is automated  
    D) Humans remember rules  

54. A theoretically justified reason to **prefer structured error envelopes** is:  
    A) Extra bytes  
    B) Language-agnostic parseability minimizing client error handling complexity  
    C) Nicer logs  
    D) Aesthetic JSON  

55. The **most general definition** of GPS Engineering is:  
    A) A Docker pattern  
    B) Governed Prompt Software Engineering unifying specs, prompts, tests, evals, decisions, and PR gates  
    C) IDE automation strategy  
    D) A single vendor workflow  

56. A **granularity** heuristic for slices is:  
    A) Require 1,000+ LOC diffs  
    B) Must require a week  
    C) Implementable with one to three prompts and a handful of tests  
    D) Prohibit tests  

57. **Cross-functional review** adds value by:  
    A) Exposing non-functional risks (security, privacy, reliability) early within the same governance loop  
    B) Shortening ADRs  
    C) Beautifying diffs  
    D) Removing CI  

58. **Tool call observability** should log at minimum:  
    A) Tool name, inputs/shape, duration, outcome status, and error class if any  
    B) Terminal theme  
    C) Only success  
    D) None  

59. **Monotonicity** in streaming interfaces refers to:  
    A) Growing Docker layers  
    B) Only increasing bytes over time with consistent framing so clients can reconstruct outputs without backtracking  
    C) Decreasing latency only  
    D) Increasing temperature  

60. The **conceptual shift** from PDD to GPS Engineering is best stated as:  
    A) From specs to intuition  
    B) From tests to diagrams  
    C) From ad-hoc acceleration to governed, auditable velocity with formal contracts and evaluation  
    D) From prompts to code generation only