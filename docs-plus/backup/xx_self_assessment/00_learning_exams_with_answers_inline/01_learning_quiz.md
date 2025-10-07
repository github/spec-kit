# Learning Quiz 1 with Inline Answers

Here’s a **graduate-level, concept-focused learning MCQ quiz** (60 questions) spanning everything we covered: **GPS Engineering** (SDD × PDD × TDD × EDD × ADR × PHR × PR), agent handoffs & guardrails, structured contracts, SSE, governance, metrics, dual-environment practice (Cursor vs VS Code + Codex), policy-as-code, and observability.
Each item includes 4 options, followed by the **correct answer inline** with **detailed explanations** (why correct; why others are wrong).

---

1. What is the primary purpose of **Spec-Driven Development (SDD)** in GPS Engineering?  
* A) Reduce CI runtime only  
* B) Convert intent into testable contracts and constraints  
* C) Increase token counts for creativity  
* D) Replace code review entirely  
* **Answer: B.** SDD formalizes behavior, constraints, and acceptance so the system has an executable contract. **D** doesn’t follow—reviews still matter; **C** is unrelated; **A** is a side effect at best, not the goal.

2. In **Prompt-Driven Development (PDD)**, why use “baby steps”?  
* A) To isolate cause/effect and keep changes reviewable  
* B) To bypass tests when prototyping  
* C) To avoid writing ADRs  
* D) To maximize diff size for learning  
* **Answer: A.** Small, scoped prompts make attribution and review easier. **D** undermines control; **B** violates GPS; **C** weakens traceability.

3. The “**No green, no merge**” policy enforces what?  
* A) Passing tests/evals as gates before integration  
* B) Automatic release to prod on green  
* C) Fast-tracking large PRs  
* D) Skipping PR reviews on weekends  
* **Answer: A.** CI gates must be green to merge. **C/D/B** are not implied by the policy.

4. What uniquely distinguishes **EDD** from TDD?  
* A) EDD checks rubric-based model behaviors; TDD asserts programmatic contracts  
* B) EDD measures lint quality; TDD measures latency  
* C) EDD requires GPUs; TDD doesn’t  
* D) EDD replaces tests; TDD becomes optional  
* **Answer: A.** EDD focuses on scenario behaviors and drift; TDD on binary contracts. **B** confuses scopes; **D** wrong—EDD complements; **C** not inherent.

5. A good **ADR** must include:  
* A) Decision only  
* B) Screenshots of the IDE  
* C) Context, options, decision, consequences  
* D) Final code snippets  
* **Answer: C.** ADRs preserve rationale and trade-offs. **A/B/D** omit critical reasoning or are irrelevant.

6. **PHRs** (Prompt History Records) are kept to:  
* A) Track GPU utilization  
* B) Preserve prompts, scope, acceptance, outcomes per slice  
* C) Store Docker layers  
* D) Replace commit history  
* **Answer: B.** PHRs capture intent and evidence for each change. **D/C/A** are unrelated.

7. Why prefer **structured outputs** (e.g., Pydantic models) in AI apps?  
* A) Larger payloads improve creativity  
* B) Better syntax highlighting  
* C) Faster UI rendering  
* D) Deterministic parsing and validation downstream  
* **Answer: D.** Structure enables reliable integration. **B/A/C** are incidental or false.

8. The top-level error envelope for `/chat` on missing user_message is:  
* A) `{"error_code":"MISSING_USER_MESSAGE"}`  
* B) `{"status":"MISSING_USER_MESSAGE"}`  
* C) `{"detail":"MISSING_USER_MESSAGE"}`  
* D) `{"error":{"code":"MISSING_USER_MESSAGE"}}`  
* **Answer: A.** Contract specifies top-level `error_code`. **C/D/B** violate the agreed shape.

9. For SSE, which terminator signals end of stream?  
* A) `event:done\n\n`  
* B) `data:complete\n`  
* C) `data:[DONE]\n\n`  
* D) `data:[END]\n`  
* **Answer: C.** `data:[DONE]` with a blank line is the agreed sentinel. Others aren’t the chosen contract.

10. Which OpenAI **Agents SDK** features we rely on for separation of concerns?  
* A) Agents, Tools, Sessions, Handoffs, Guardrails  
* B) Lambda layers  
* C) Ingress controllers  
* D) Sessions only  
* **Answer: A.** That’s the core SDK set we use. **D/C/B** are incomplete or unrelated.

11. The **tool-first** policy exists to:  
* A) Route math/time to deterministic functions to cut hallucinations  
* B) Force all work into code tools  
* C) Increase verbosity  
* D) Reduce test counts  
* **Answer: A.** Deterministic tools minimize model guessing. **C/D/B** misstate intent.

12. **Cursor** is strongest at:  
* A) GPU provisioning  
* B) Inline tab-completion, predictive multi-file edits, interactive flow  
* C) Repo-wide autonomous refactors without oversight  
* D) License scanning by default  
* **Answer: B.** Cursor shines in interactive editor flows. **C/D/A** not its core value.

13. **VS Code + Codex** is strongest at:  
* A) Pure tab-completion  
* B) Managing container registries  
* C) Agentic, repo-scale tasks and PR preparation  
* D) Uvicorn tuning  
* **Answer: C.** Codex excels at broader agentic tasks. **A/B/D** are not its main strengths.

14. A **thin spec** should avoid:  
* A) Acceptance checks  
* B) Contract examples  
* C) Implementation detail that overconstrains design  
* D) Error envelopes  
* **Answer: C.** Specs state *what*, not detailed *how*. **B/A/D** belong.

15. Why keep tests **offline/mocked** by default?  
* A) To bypass coverage  
* B) To ensure determinism and avoid network/model variance  
* C) To hide bugs  
* D) To skip CI  
* **Answer: B.** Offline tests stabilize signals. **C/D/A** are bad practice.

16. In PDD, the **Architect prompt** should:  
* A) Ask to skip tests  
* B) State micro-spec, constraints, acceptance, risks before code  
* C) Request code immediately  
* D) Change unrelated files  
* **Answer: B.** Architect prompts set scope and checks. **C/D/A** contradict process.

17. The purpose of the **Explainer prompt** is to:  
* A) Compile docs  
* B) Generate architecture diagrams automatically  
* C) Summarize diffs, trade-offs, residual risk succinctly  
* D) Replace PR description  
* **Answer: C.** It clarifies intent and changes. **D/B/A** aren’t the goal.

18. The **smallest change to green** principle primarily reduces:  
* A) Token usage only  
* B) Confounding variables in failure diagnosis  
* C) CI bill  
* D) Reviewers needed  
* **Answer: B.** It improves causal attribution. **C/A/D** are secondary or wrong.

19. In GPS, **refactor** means:  
* A) Improving internals with tests kept green  
* B) Rewriting specs mid-PR  
* C) Changing public contracts routinely  
* D) Skipping evaluations  
* **Answer: A.** Behavior preserved, internals improved. **C/B/D** oppose governance.

20. **Traceability** is best achieved by linking:  
* A) Branch ↔ Tag alone  
* B) Spec ↔ PHR ↔ ADR ↔ PR ↔ CI artifacts  
* C) Logs to screenshots  
* D) README ↔ LICENSE only  
* **Answer: B.** That end-to-end chain is the backbone. Others are partial.

21. The PR template’s **Spec-Compliance** checkbox ensures:  
* A) Automatic release notes  
* B) Style consistency  
* C) Implementation matches spec/acceptance (tests/evals)  
* D) Version bump  
* **Answer: C.** It’s a gate for contract adherence. **B/D/A** not guaranteed.

22. Why choose **SSE** for v1 streaming?  
* A) Mandatory bidirectional control  
* B) Simplicity, proxy compatibility, low infra complexity  
* C) Binary frame support  
* D) Built-in compression  
* **Answer: B.** SSE fits minimal, one-way token flow. **C/A/D** not decisive.

23. Which CI gate most increases reliability for LLM apps?  
* A) Lint + contract tests + EDD smoke **before** build/publish  
* B) Only lint  
* C) Build first, test later  
* D) Post-deploy tests only  
* **Answer: A.** Upfront gates catch issues earlier. Others miss risks.

24. A **scope discipline** eval should:  
* A) Penalize unrequested fields/format drift  
* B) Score verbosity higher  
* C) Reward extra fields  
* D) Ignore structure  
* **Answer: A.** We enforce schema. **C/D/B** conflict with discipline.

25. **Model-agnosticism** at spec level means:  
* A) Fixing a single decoding strategy forever  
* B) Contracts/evals valid across providers  
* C) Hard-coding a vendor  
* D) Ignoring latency  
* **Answer: B.** We keep portability. **C/D/A** narrow or ignore realities.

26. Why keep **PHRs** in the repo (not chat only)?  
* A) Better Docker layers  
* B) Versioned, reviewable, linkable evidence tied to diffs  
* C) Emoji reactions  
* D) Lower token bills  
* **Answer: B.** Governance requires permanence and links. Others are irrelevant.

27. A **good acceptance test** for `/chat` checks:  
* A) Response matches `ChatReply` schema and required fields  
* B) README exists  
* C) Server uptime  
* D) Docker layer count  
* **Answer: A.** Contract tests validate schema/fields. **C/B/D** are orthogonal.

28. The **handoff** concept in agents supports:  
* A) Token pooling  
* B) Random switching  
* C) Specialization via intent-conditioned control transfer  
* D) Cache flushing  
* **Answer: C.** Handoffs route to specialized agents. Others are unrelated.

29. The best reason to **version specs** is to:  
* A) Reduce CI logs  
* B) Improve font rendering  
* C) Align behavior changes with artifacts and migrations  
* D) Change IDE shortcuts  
* **Answer: C.** Versioned specs track evolution and deprecations. Others are cosmetic.

30. Which **metric pair** is most diagnostic for delivery health?  
* A) Lead time to change + change-failure rate (with MTTR)  
* B) Image size + theme  
* C) Lines of code + stars  
* D) PR emoji count + velocity  
* **Answer: A.** Those directly reflect flow and stability. Others are noise.

31. A **red-team EDD** check should include:  
* A) Screenshot diffs  
* B) Prompt-injection tests scoring policy violations/tool misuse  
* C) GIFs in PR  
* D) GPU fan speed  
* **Answer: B.** Safety is a behavior domain. Others are irrelevant.

32. **Offline unit tests** guard primarily against:  
* A) Disk quotas  
* B) Model/provider outages and nondeterminism  
* C) Color themes  
* D) Spelling errors in comments  
* **Answer: B.** They stabilize correctness signals. Others are minor.

33. A **governed refactor prompt** should require:  
* A) Delete flaky tests  
* B) Keep tests green, preserve behavior; summarize rationale  
* C) Add new dependencies freely  
* D) Change public contract  
* **Answer: B.** Preserve interfaces; document intent. Others are anti-patterns.

34. A **governance smell** is when PRs:  
* A) Are small and reviewed  
* B) Include EDD artifacts  
* C) Merge on red or without PHR/ADR references  
* D) Link specs and ADRs  
* **Answer: C.** That breaks gates/traceability. **D/A/B** are good.

35. A **prompt library** should be:  
* A) Versioned, ID’d, mapped to specs/tests  
* B) Hidden from reviewers  
* C) Ephemeral & untracked  
* D) Screenshots only  
* **Answer: A.** Reuse + governance needs versioned prompts. Others defeat purpose.

36. **Observability** for agents should record:  
* A) Spans of tools/handoffs with inputs (shape), outputs, timing, errors  
* B) Editor font  
* C) Only total tokens  
* D) Theme changes  
* **Answer: A.** Observability supports debugging/governance. Others irrelevant.

37. A **thin slice** heuristic:  
* A) 1–3 prompts plus a handful of tests to done  
* B) Always excludes tests  
* C) Spans multiple subsystems at once  
* D) Requires large diffs  
* **Answer: A.** Keep scope small and testable. **D/C/B** are wrong.

38. **Evaluation drift** is best mitigated by:  
* A) Skipping evals after initial pass  
* B) Versioned suites re-run on changes with thresholds  
* C) Manual screenshots  
* D) Longer prompts  
* **Answer: B.** Regularized, versioned evals guard against regressions. Others don’t.

39. A statistically sound eval protocol uses:  
* A) No logging  
* B) Replicates with fixed seeds per version and stratified analysis  
* C) One shot at temp 1.0  
* D) Changing datasets at random  
* **Answer: B.** Replication + controls detect change reliably. Others increase noise.

40. A **privacy-aware** eval should:  
* A) Ignore privacy  
* B) Use real PII in logs  
* C) Disable outputs  
* D) Use synthetic PII and verify redaction policies  
* **Answer: D.** Test redaction safely. **B/A/C** unsafe or useless.

41. **uv** is recommended because it:  
* A) Provides fast, reproducible Python dependency management suited for CI  
* B) Generates UML  
* C) Replaces Docker entirely  
* D) Is a new linter  
* **Answer: A.** uv speeds and locks deps. **C/D/B** are wrong.

42. **SSE** requires the server to set:  
* A) `Content-Type: text/event-stream`  
* B) `X-Stream: yes`  
* C) `Accept: text/event-stream`  
* D) `Content-Type: application/json`  
* **Answer: A.** Server response header must be SSE. **C** is a client request header; **D/B** wrong.

43. A **contract test** ensures:  
* A) GPU utilization limits  
* B) Training corpus freshness  
* C) Interface stability regardless of internal changes  
* D) Repo size thresholds  
* **Answer: C.** That’s the essence of contract tests. Others are not.

44. A **Spec creep** control is to:  
* A) Merge everything at once  
* B) Split into new micro-specs and PRs  
* C) Delete tests  
* D) Mutate scope mid-PR  
* **Answer: B.** Micro-slicing keeps control. Others add risk.

45. Why keep **ADRs next to code**?  
* A) Decisions co-evolve with implementation; change context is preserved  
* B) Emojis render better  
* C) Shorter URLs  
* D) Save repo space  
* **Answer: A.** Co-location aids discovery and maintenance. Others trivial.

46. In GPS, **model substitution** should be accompanied by:  
* A) Skipping tests for speed  
* B) Re-running suites with equivalence thresholds and rollback rules  
* C) Only lint  
* D) Logo updates  
* **Answer: B.** Behavior parity must be verified. Others unsafe.

47. The **dual-environment** recommendation rests on:  
* A) Different cognitive modes (agentic vs interactive) improve productivity  
* B) Avoiding Git  
* C) One tool is always superior  
* D) Identical UI skins  
* **Answer: A.** Each environment is best at different tasks. Others false.

48. The **PR** is the place to:  
* A) Merge on yellow  
* B) Paste raw model dumps only  
* C) Attach links to Spec, PHR IDs, ADR IDs, and CI/EDD artifacts  
* D) Skip description  
* **Answer: C.** PR centralizes traceability. Others degrade governance.

49. **Retry logic** should be used when:  
* A) The editor lags  
* B) Guardrails/schema fail and a correction hint is provided  
* C) You want more tokens  
* D) Tests are red for any reason  
* **Answer: B.** Retries help recover from structured failures. **A/D/C** misuse.

50. A **good scope discipline** failure looks like:  
* A) Exact fields per spec  
* B) Extra keys and formats not requested  
* C) Matching schema precisely  
* D) Validated structure  
* **Answer: B.** Extra fields violate the contract. **A/C/D** are compliant.

51. A **post-mortem** with strongest evidence uses:  
* A) PHRs (exact prompts) and before/after eval artifacts  
* B) Emojis + screenshots  
* C) Lines of code changed  
* D) README diffs  
* **Answer: A.** These directly show cause & effect. Others are weak.

52. **Monotonic streaming** means:  
* A) Binary frames only  
* B) Append-only token emission with stable framing so clients reconstruct progressively  
* C) Fixed chunk sizes  
* D) Only decreasing latency  
* **Answer: B.** That’s the property clients rely on. Others off.

53. A mature **policy-as-code** setup:  
* A) Enforces lint/tests/evals/secret scanning as CI merge gates  
* B) Trusts memory  
* C) Uses manual checklists only  
* D) Posts guidelines in slides  
* **Answer: A.** Automation makes governance reliable. Others stale.

54. A **learning KPI** that indicates slice health:  
* A) Frequent small PRs with high pass rate and low rework  
* B) LOC growth  
* C) Number of files touched  
* D) Comment length  
* **Answer: A.** That correlates with healthy, testable slices. Others are poor proxies.

55. The **Explainer prompt** should:  
* A) Increase temperature  
* B) Just restate code  
* C) Change public API  
* D) Summarize intent, diffs, risks, next steps in ≤8 bullets  
* **Answer: D.** It clarifies impact and risk. Others misapply.

56. **Guardrails** add value by:  
* A) Replacing tests  
* B) Restricting output to shape/length/policy, enabling retries on violation  
* C) Increasing GPU usage  
* D) Removing evals  
* **Answer: B.** They constrain outputs and enable recovery. Others false.

57. **Contract stability** across models is verified by:  
* A) Reading docs  
* B) Running the same contract tests & error envelopes after substitution  
* C) Asking a teammate  
* D) Skipping CI for speed  
* **Answer: B.** Execute contracts to prove stability. Others are anecdotal.

58. A **risk triage** lens for review prioritizes:  
* A) Change surface × component criticality, with rollback noted  
* B) Removing CI steps  
* C) UI polish first  
* D) Commit message puns  
* **Answer: A.** Focus on impact and reversibility. Others distract.

59. The **governed definition** of GPS Engineering is:  
* A) A Dockerfile recipe  
* B) Governed Prompt Software Engineering unifying specs, prompts, tests, evals, decisions, PR gates  
* C) Prompting technique only  
* D) A single IDE feature  
* **Answer: B.** It’s a method combining these artifacts and gates. Others narrow it.

60. The shift from **PDD → GPS** is best described as:  
* A) From prompts to pure coding  
* B) From speed alone to auditable velocity with formal contracts & evaluation  
* C) From specs to vibes  
* D) From tests to drawings  
* **Answer: B.** GPS adds governance and traceability to PDD speed. Others are regressions.

---
