# Learning Quiz 0 with Inline Answers

Here’s a **learning MCQ quiz** (60 questions) covering the full GPS Engineering stack (SDD × PDD × TDD × EDD × ADR × PHR × PR), OpenAI Agents SDK patterns, SSE, CI/CD, dual IDE practice, governance, metrics, and more.
Each item lists options, then the **correct answer inline** with a brief explanation of why it’s correct and why the others are not.

---

1. What is the primary purpose of **Spec-Driven Development (SDD)** in GPS Engineering?  
* A) Convert intent into testable contracts and constraints  
* B) Increase token counts for creativity  
* C) Replace code review entirely  
* D) Reduce CI runtime only  
* **Answer: A.** SDD formalizes behavior, constraints, and acceptance so the system has an executable contract. **C** doesn’t follow—reviews still matter; **B** is unrelated; **D** is a side effect at best, not the goal.

2. In **Prompt-Driven Development (PDD)**, why use “baby steps”?  
* A) To bypass tests when prototyping  
* B) To isolate cause/effect and keep changes reviewable  
* C) To maximize diff size for learning  
* D) To avoid writing ADRs  
* **Answer: B.** Small, scoped prompts make attribution and review easier. **C** undermines control; **A** violates GPS; **D** weakens traceability.

3. The “**No green, no merge**” policy enforces what?  
* A) Fast-tracking large PRs  
* B) Skipping PR reviews on weekends  
* C) Passing tests/evals as gates before integration  
* D) Automatic release to prod on green  
* **Answer: C.** CI gates must be green to merge. **A/B/D** are not implied by the policy.

4. What uniquely distinguishes **EDD** from TDD?  
* A) EDD measures lint quality; TDD measures latency  
* B) EDD replaces tests; TDD becomes optional  
* C) EDD requires GPUs; TDD doesn’t  
* D) EDD checks rubric-based model behaviors; TDD asserts programmatic contracts  
* **Answer: D.** EDD focuses on scenario behaviors and drift; TDD on binary contracts. **A** confuses scopes; **B** wrong—EDD complements; **C** not inherent.

5. A good **ADR** must include:  
* A) Screenshots of the IDE  
* B) Final code snippets  
* C) Context, options, decision, consequences  
* D) Decision only  
* **Answer: C.** ADRs preserve rationale and trade-offs. **D/A/B** omit critical reasoning or are irrelevant.

6. **PHRs** (Prompt History Records) are kept to:  
* A) Preserve prompts, scope, acceptance, outcomes per slice  
* B) Store Docker layers  
* C) Replace commit history  
* D) Track GPU utilization  
* **Answer: A.** PHRs capture intent and evidence for each change. **C/B/D** are unrelated.

7. Why prefer **structured outputs** (e.g., Pydantic models) in AI apps?  
* A) Deterministic parsing and validation downstream  
* B) Better syntax highlighting  
* C) Faster UI rendering  
* D) Larger payloads improve creativity  
* **Answer: A.** Structure enables reliable integration. **B/D/C** are incidental or false.

8. The top-level error envelope for `/chat` on missing user_message is:  
* A) `{"detail":"MISSING_USER_MESSAGE"}`  
* B) `{"error":{"code":"MISSING_USER_MESSAGE"}}`  
* C) `{"status":"MISSING_USER_MESSAGE"}`  
* D) `{"error_code":"MISSING_USER_MESSAGE"}`  
* **Answer: D.** Contract specifies top-level `error_code`. **A/B/C** violate the agreed shape.

9. For SSE, which terminator signals end of stream?  
* A) `data:[END]\n`  
* B) `data:[DONE]\n\n`  
* C) `data:complete\n`  
* D) `event:done\n\n`  
* **Answer: B.** `data:[DONE]` with a blank line is the agreed sentinel. Others aren’t the chosen contract.

10. Which OpenAI **Agents SDK** features we rely on for separation of concerns?  
* A) Ingress controllers  
* B) Sessions only  
* C) Agents, Tools, Sessions, Handoffs, Guardrails  
* D) Lambda layers  
* **Answer: C.** That’s the core SDK set we use. **B/A/D** are incomplete or unrelated.

11. The **tool-first** policy exists to:  
* A) Increase verbosity  
* B) Reduce test counts  
* C) Route math/time to deterministic functions to cut hallucinations  
* D) Force all work into code tools  
* **Answer: C.** Deterministic tools minimize model guessing. **A/B/D** misstate intent.

12. **Cursor** is strongest at:  
* A) Inline tab-completion, predictive multi-file edits, interactive flow  
* B) Repo-wide autonomous refactors without oversight  
* C) License scanning by default  
* D) GPU provisioning  
* **Answer: A.** Cursor shines in interactive editor flows. **B/C/D** not its core value.

13. **VS Code + Codex** is strongest at:  
* A) Uvicorn tuning  
* B) Agentic, repo-scale tasks and PR preparation  
* C) Pure tab-completion  
* D) Managing container registries  
* **Answer: B.** Codex excels at broader agentic tasks. **C/D/A** are not its main strengths.

14. A **thin spec** should avoid:  
* A) Contract examples  
* B) Implementation detail that overconstrains design  
* C) Error envelopes  
* D) Acceptance checks  
* **Answer: B.** Specs state *what*, not detailed *how*. **A/D/C** belong.

15. Why keep tests **offline/mocked** by default?  
* A) To ensure determinism and avoid network/model variance  
* B) To hide bugs  
* C) To skip CI  
* D) To bypass coverage  
* **Answer: A.** Offline tests stabilize signals. **B/C/D** are bad practice.

16. In PDD, the **Architect prompt** should:  
* A) Request code immediately  
* B) Change unrelated files  
* C) State micro-spec, constraints, acceptance, risks before code  
* D) Ask to skip tests  
* **Answer: C.** Architect prompts set scope and checks. **A/B/D** contradict process.

17. The purpose of the **Explainer prompt** is to:  
* A) Summarize diffs, trade-offs, residual risk succinctly  
* B) Replace PR description  
* C) Generate architecture diagrams automatically  
* D) Compile docs  
* **Answer: A.** It clarifies intent and changes. **B/C/D** aren’t the goal.

18. The **smallest change to green** principle primarily reduces:  
* A) CI bill  
* B) Confounding variables in failure diagnosis  
* C) Reviewers needed  
* D) Token usage only  
* **Answer: B.** It improves causal attribution. **A/D/C** are secondary or wrong.

19. In GPS, **refactor** means:  
* A) Changing public contracts routinely  
* B) Skipping evaluations  
* C) Rewriting specs mid-PR  
* D) Improving internals with tests kept green  
* **Answer: D.** Behavior preserved, internals improved. **A/C/B** oppose governance.

20. **Traceability** is best achieved by linking:  
* A) Logs to screenshots  
* B) README ↔ LICENSE only  
* C) Spec ↔ PHR ↔ ADR ↔ PR ↔ CI artifacts  
* D) Branch ↔ Tag alone  
* **Answer: C.** That end-to-end chain is the backbone. Others are partial.

21. The PR template’s **Spec-Compliance** checkbox ensures:  
* A) Implementation matches spec/acceptance (tests/evals)  
* B) Style consistency  
* C) Version bump  
* D) Automatic release notes  
* **Answer: A.** It’s a gate for contract adherence. **B/D/C** not guaranteed.

22. Why choose **SSE** for v1 streaming?  
* A) Binary frame support  
* B) Simplicity, proxy compatibility, low infra complexity  
* C) Built-in compression  
* D) Mandatory bidirectional control  
* **Answer: B.** SSE fits minimal, one-way token flow. **A/D/C** not decisive.

23. Which CI gate most increases reliability for LLM apps?  
* A) Build first, test later  
* B) Only lint  
* C) Post-deploy tests only  
* D) Lint + contract tests + EDD smoke **before** build/publish  
* **Answer: D.** Upfront gates catch issues earlier. Others miss risks.

24. A **scope discipline** eval should:  
* A) Reward extra fields  
* B) Penalize unrequested fields/format drift  
* C) Ignore structure  
* D) Score verbosity higher  
* **Answer: B.** We enforce schema. **A/C/D** conflict with discipline.

25. **Model-agnosticism** at spec level means:  
* A) Hard-coding a vendor  
* B) Ignoring latency  
* C) Contracts/evals valid across providers  
* D) Fixing a single decoding strategy forever  
* **Answer: C.** We keep portability. **A/B/D** narrow or ignore realities.

26. Why keep **PHRs** in the repo (not chat only)?  
* A) Emoji reactions  
* B) Versioned, reviewable, linkable evidence tied to diffs  
* C) Lower token bills  
* D) Better Docker layers  
* **Answer: B.** Governance requires permanence and links. Others are irrelevant.

27. A **good acceptance test** for `/chat` checks:  
* A) Server uptime  
* B) Docker layer count  
* C) Response matches `ChatReply` schema and required fields  
* D) README exists  
* **Answer: C.** Contract tests validate schema/fields. **A/D/B** are orthogonal.

28. The **handoff** concept in agents supports:  
* A) Specialization via intent-conditioned control transfer  
* B) Random switching  
* C) Cache flushing  
* D) Token pooling  
* **Answer: A.** Handoffs route to specialized agents. Others are unrelated.

29. The best reason to **version specs** is to:  
* A) Align behavior changes with artifacts and migrations  
* B) Change IDE shortcuts  
* C) Improve font rendering  
* D) Reduce CI logs  
* **Answer: A.** Versioned specs track evolution and deprecations. Others are cosmetic.

30. Which **metric pair** is most diagnostic for delivery health?  
* A) Lines of code + stars  
* B) Lead time to change + change-failure rate (with MTTR)  
* C) PR emoji count + velocity  
* D) Image size + theme  
* **Answer: B.** Those directly reflect flow and stability. Others are noise.

31. A **red-team EDD** check should include:  
* A) Prompt-injection tests scoring policy violations/tool misuse  
* B) GPU fan speed  
* C) GIFs in PR  
* D) Screenshot diffs  
* **Answer: A.** Safety is a behavior domain. Others are irrelevant.

32. **Offline unit tests** guard primarily against:  
* A) Color themes  
* B) Model/provider outages and nondeterminism  
* C) Spelling errors in comments  
* D) Disk quotas  
* **Answer: B.** They stabilize correctness signals. Others are minor.

33. A **governed refactor prompt** should require:  
* A) Change public contract  
* B) Add new dependencies freely  
* C) Keep tests green, preserve behavior; summarize rationale  
* D) Delete flaky tests  
* **Answer: C.** Preserve interfaces; document intent. Others are anti-patterns.

34. A **governance smell** is when PRs:  
* A) Link specs and ADRs  
* B) Merge on red or without PHR/ADR references  
* C) Include EDD artifacts  
* D) Are small and reviewed  
* **Answer: B.** That breaks gates/traceability. **A/D/C** are good.

35. A **prompt library** should be:  
* A) Screenshots only  
* B) Versioned, ID’d, mapped to specs/tests  
* C) Ephemeral & untracked  
* D) Hidden from reviewers  
* **Answer: B.** Reuse + governance needs versioned prompts. Others defeat purpose.

36. **Observability** for agents should record:  
* A) Theme changes  
* B) Only total tokens  
* C) Spans of tools/handoffs with inputs (shape), outputs, timing, errors  
* D) Editor font  
* **Answer: C.** Observability supports debugging/governance. Others irrelevant.

37. A **thin slice** heuristic:  
* A) Requires large diffs  
* B) Spans multiple subsystems at once  
* C) Always excludes tests  
* D) 1–3 prompts plus a handful of tests to done  
* **Answer: D.** Keep scope small and testable. **A/B/C** are wrong.

38. **Evaluation drift** is best mitigated by:  
* A) Longer prompts  
* B) Versioned suites re-run on changes with thresholds  
* C) Manual screenshots  
* D) Skipping evals after initial pass  
* **Answer: B.** Regularized, versioned evals guard against regressions. Others don’t.

39. A statistically sound eval protocol uses:  
* A) One shot at temp 1.0  
* B) Changing datasets at random  
* C) Replicates with fixed seeds per version and stratified analysis  
* D) No logging  
* **Answer: C.** Replication + controls detect change reliably. Others increase noise.

40. A **privacy-aware** eval should:  
* A) Use synthetic PII and verify redaction policies  
* B) Ignore privacy  
* C) Use real PII in logs  
* D) Disable outputs  
* **Answer: A.** Test redaction safely. **C/B/D** unsafe or useless.

41. **uv** is recommended because it:  
* A) Replaces Docker entirely  
* B) Is a new linter  
* C) Provides fast, reproducible Python dependency management suited for CI  
* D) Generates UML  
* **Answer: C.** uv speeds and locks deps. **A/B/D** are wrong.

42. **SSE** requires the server to set:  
* A) `Content-Type: application/json`  
* B) `Content-Type: text/event-stream`  
* C) `X-Stream: yes`  
* D) `Accept: text/event-stream`  
* **Answer: B.** Server response header must be SSE. **D** is a client request header; **A/C** wrong.

43. A **contract test** ensures:  
* A) Interface stability regardless of internal changes  
* B) Training corpus freshness  
* C) Repo size thresholds  
* D) GPU utilization limits  
* **Answer: A.** That’s the essence of contract tests. Others are not.

44. A **Spec creep** control is to:  
* A) Mutate scope mid-PR  
* B) Delete tests  
* C) Split into new micro-specs and PRs  
* D) Merge everything at once  
* **Answer: C.** Micro-slicing keeps control. Others add risk.

45. Why keep **ADRs next to code**?  
* A) Save repo space  
* B) Decisions co-evolve with implementation; change context is preserved  
* C) Shorter URLs  
* D) Emojis render better  
* **Answer: B.** Co-location aids discovery and maintenance. Others trivial.

46. In GPS, **model substitution** should be accompanied by:  
* A) Re-running suites with equivalence thresholds and rollback rules  
* B) Only lint  
* C) Logo updates  
* D) Skipping tests for speed  
* **Answer: A.** Behavior parity must be verified. Others unsafe.

47. The **dual-environment** recommendation rests on:  
* A) Identical UI skins  
* B) One tool is always superior  
* C) Different cognitive modes (agentic vs interactive) improve productivity  
* D) Avoiding Git  
* **Answer: C.** Each environment is best at different tasks. Others false.

48. The **PR** is the place to:  
* A) Skip description  
* B) Attach links to Spec, PHR IDs, ADR IDs, and CI/EDD artifacts  
* C) Paste raw model dumps only  
* D) Merge on yellow  
* **Answer: B.** PR centralizes traceability. Others degrade governance.

49. **Retry logic** should be used when:  
* A) Guardrails/schema fail and a correction hint is provided  
* B) You want more tokens  
* C) Tests are red for any reason  
* D) The editor lags  
* **Answer: A.** Retries help recover from structured failures. **D/C/B** misuse.

50. A **good scope discipline** failure looks like:  
* A) Matching schema precisely  
* B) Extra keys and formats not requested  
* C) Validated structure  
* D) Exact fields per spec  
* **Answer: B.** Extra fields violate the contract. **D/A/C** are compliant.

51. A **post-mortem** with strongest evidence uses:  
* A) Emojis + screenshots  
* B) Lines of code changed  
* C) PHRs (exact prompts) and before/after eval artifacts  
* D) README diffs  
* **Answer: C.** These directly show cause & effect. Others are weak.

52. **Monotonic streaming** means:  
* A) Append-only token emission with stable framing so clients reconstruct progressively  
* B) Only decreasing latency  
* C) Fixed chunk sizes  
* D) Binary frames only  
* **Answer: A.** That’s the property clients rely on. Others off.

53. A mature **policy-as-code** setup:  
* A) Uses manual checklists only  
* B) Enforces lint/tests/evals/secret scanning as CI merge gates  
* C) Posts guidelines in slides  
* D) Trusts memory  
* **Answer: B.** Automation makes governance reliable. Others stale.

54. A **learning KPI** that indicates slice health:  
* A) Comment length  
* B) Number of files touched  
* C) Frequent small PRs with high pass rate and low rework  
* D) LOC growth  
* **Answer: C.** That correlates with healthy, testable slices. Others are poor proxies.

55. The **Explainer prompt** should:  
* A) Change public API  
* B) Summarize intent, diffs, risks, next steps in ≤8 bullets  
* C) Just restate code  
* D) Increase temperature  
* **Answer: B.** It clarifies impact and risk. Others misapply.

56. **Guardrails** add value by:  
* A) Restricting output to shape/length/policy, enabling retries on violation  
* B) Increasing GPU usage  
* C) Replacing tests  
* D) Removing evals  
* **Answer: A.** They constrain outputs and enable recovery. Others false.

57. **Contract stability** across models is verified by:  
* A) Skipping CI for speed  
* B) Running the same contract tests & error envelopes after substitution  
* C) Asking a teammate  
* D) Reading docs  
* **Answer: B.** Execute contracts to prove stability. Others are anecdotal.

58. A **risk triage** lens for review prioritizes:  
* A) Commit message puns  
* B) UI polish first  
* C) Change surface × component criticality, with rollback noted  
* D) Removing CI steps  
* **Answer: C.** Focus on impact and reversibility. Others distract.

59. The **governed definition** of GPS Engineering is:  
* A) Prompting technique only  
* B) A single IDE feature  
* C) Governed Prompt Software Engineering unifying specs, prompts, tests, evals, decisions, PR gates  
* D) A Dockerfile recipe  
* **Answer: C.** It’s a method combining these artifacts and gates. Others narrow it.

60. The shift from **PDD → GPS** is best described as:  
* A) From tests to drawings  
* B) From speed alone to auditable velocity with formal contracts & evaluation  
* C) From specs to vibes  
* D) From prompts to pure coding  
* **Answer: B.** GPS adds governance and traceability to PDD speed. Others are regressions.

---
