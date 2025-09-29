# Quiz 3

Here’s a **third, graduate-level 60-question MCQ quiz** focused on the **concepts** (not example particulars) from our GPS Engineering method: SDD × PDD × TDD × EDD × ADR × PHR × PR, agent architectures, evaluation, governance, metrics, and dual-environment practice. **Answer key in the file answer_key.md**

---

## Multiple-Choice Questions (Concept-Focused)

1. The most fundamental purpose of **SDD** in AI-assisted engineering is to:  
   A) Maximize model creativity  
   B) Replace code review meetings  
   C) Convert intent into testable contracts and constraints  
   D) Eliminate refactoring  

2. Compared to ad-hoc prompting, **PDD** primarily improves outcomes by:  
   A) Raising temperature  
   B) Sequencing prompts with scope, constraints, and acceptance checks  
   C) Removing tests  
   D) Enlarging diffs  

3. The **governance gap** addressed by GPS Engineering is best defined as:  
   A) Missing UI mockups  
   B) Lack of GPUs  
   C) Insufficient logs  
   D) Speed without traceability and quality gates  

4. **TDD** in LLM systems is most valuable because it:  
   A) Encodes behavioral expectations independent of the model  
   B) Guarantees perfect model outputs  
   C) Eliminates the need for specs  
   D) Removes the need for evaluation  

5. **EDD** supplements TDD by focusing on:  
   A) Scenario-level behavior and drift across versions  
   B) CPU usage metrics  
   C) Binary serialization formats  
   D) Editor ergonomics  

6. A well-formed **ADR** should capture:  
   A) A single screenshot  
   B) Context, options, decision, and consequences  
   C) Only the winning option  
   D) Team bios  

7. **PHRs** are essential because they:  
   A) Eliminate the need for tests  
   B) Replace version control  
   C) Serve as marketing copy  
   D) Preserve prompt intent, scope, and outcomes as auditable artifacts  

8. The **Spec-Compliance** check in PRs mainly ensures:  
   A) Larger PRs  
   B) Implementation aligns with written contracts and acceptance criteria  
   C) Branding consistency  
   D) Integration without reviewers  

9. The principle of **“smallest change to green”** reduces:  
   A) Confounding variables during diagnosis and review  
   B) CI duration only  
   C) Lint warnings  
   D) Reviewer count  

10. In agentic systems, **handoff** primarily supports:  
    A) Separation of concerns via specialization  
    B) Random agent selection  
    C) Token pooling  
    D) Cache warming  

11. **Guardrails** provide value because they:  
    A) Increase verbosity  
    B) Disable retries  
    C) Constrain outputs to shape, bounds, and policies  
    D) Replace authorization  

12. **Structured outputs** in LLM apps are desirable primarily to:  
    A) Disable caching  
    B) Enable deterministic downstream handling and validation  
    C) Increase token usage  
    D) Improve font rendering  

13. **Offline tests** are emphasized because they:  
    A) Improve GPU throughput  
    B) Generate diagrams  
    C) Replace CI  
    D) Reduce cloud costs and remove nondeterminism from network dependencies  

14. The conceptual difference between **tests** and **evals** is that:  
    A) Tests are visual; evals are numeric  
    B) Tests assert program behaviors; evals score model behaviors against rubrics  
    C) They are identical  
    D) Tests are optional; evals are mandatory  

15. In a governed process, **traceability** is best achieved by linking:  
    A) Logs to screenshots  
    B) README ↔ LICENSE  
    C) Spec ↔ PHR ↔ ADR ↔ PR ↔ CI  
    D) Branch ↔ Tag only  

16. A **thin spec** should avoid:  
    A) Contract examples  
    B) Behavior, constraints, acceptance  
    C) Implementation detail that overconstrains design  
    D) Input/output definitions  

17. A key risk of **vibe coding** in multi-agent systems is:  
    A) Too many unit tests  
    B) Architecture drift due to ambiguous, shifting prompts  
    C) Excessive type hints  
    D) Short ADRs  

18. The **dual-environment** recommendation (e.g., interactive editor + agentic tool) reflects that:  
    A) Both must be cloud-only  
    B) Different environments optimize different cognitive modes  
    C) Only one can run tests  
    D) One editor is always superior  

19. **Evaluation drift** is best mitigated by:  
    A) Removing guardrails  
    B) Longer prompts  
    C) Versioned behavior suites and periodic re-runs  
    D) Disabling test retries  

20. **Spec versioning** matters because:  
    A) It situates behavior changes and keeps artifacts aligned in time  
    B) JSON is unstable  
    C) It prevents CI runners from caching  
    D) It changes IDE shortcuts  

21. In GPS Engineering, **refactor** should:  
    A) Change public contracts  
    B) Preserve behaviors and interfaces while improving internals  
    C) Rewrite ADRs  
    D) Remove tests after green  

22. The **primary advantage** of small PRs is:  
    A) More merge conflicts  
    B) Bigger coverage gaps  
    C) Faster, higher-quality review with clearer scope  
    D) Stylish diffs  

23. **Model-agnosticism** is important because it:  
    A) Enables portability and comparability across providers  
    B) Eliminates EDD  
    C) Locks a vendor  
    D) Reduces PHRs  

24. The **objective** of an architect prompt is to:  
    A) Change CI runners  
    B) Produce code immediately  
    C) Establish micro-spec, constraints, and acceptance before generation  
    D) Edit unrelated files  

25. **Scope discipline** in evals should penalize:  
    A) Using structured outputs  
    B) Matching schema exactly  
    C) Returning only requested fields  
    D) Adding fields or formats not specified  

26. A governance smell is when PRs:  
    A) Link spec and ADRs  
    B) Merge on red or without PHR/ADR references  
    C) Pass CI with evals  
    D) Are small and reviewed  

27. The **most resilient** secrets policy is:  
    A) Use environment variables and rotate routinely  
    B) Commit to VCS for convenience  
    C) Embed keys within prompts  
    D) Store in README  

28. A **metric** suited to assess slice health is:  
    A) Lines of code added  
    B) Lead time to change for small diffs  
    C) Number of comments per PR  
    D) Refactor count  

29. The primary reason to **prefer structured contracts** in AI services is:  
    A) Enables typed validation and safer integration points  
    B) More tokens  
    C) Easier CSS theming  
    D) Lazier clients  

30. The **PHR ID convention** helps teams:  
    A) Collapse histories  
    B) Avoid CI  
    C) Reference precise change intents in reviews and retros  
    D) Hide prompts  

31. A **responsible** use of retries in LLM flows is to:  
    A) Disable caching  
    B) Retry boundedly when guardrails or schema validation fails  
    C) Retry indefinitely  
    D) Reset CI  

32. **Thin slices** matter because they:  
    A) Increase flakiness  
    B) Reduce cognitive load and limit blast radius of mistakes  
    C) Replace documentation  
    D) Inflate diffs  

33. The most conceptual reason to **store ADRs with code** is:  
    A) Co-evolution of decisions with implementation  
    B) Easier emojis  
    C) Cheaper hosting  
    D) Larger PDFs  

34. An **effective prompt library** should be:  
    A) Only screenshots  
    B) Versioned, reusable, mapped to specs and evals  
    C) Ephemeral and private  
    D) Untagged and ad-hoc  

35. In agent design, **tool-first** policy aims to:  
    A) Prevent deterministic operations from being free-form generations  
    B) Remove tools entirely  
    C) Raise temperature  
    D) Reduce observability  

36. The **best** conceptual justification for small diffs is:  
    A) They isolate causality, therefore speed up learning and review  
    B) They look elegant  
    C) They produce more merges  
    D) They pass CI faster by magic  

37. **Observability** in LLM workflows is primarily to:  
    A) Style dashboards  
    B) Increase token usage  
    C) Reveal steps, tool calls, and routing for debugging and governance  
    D) Decrease test coverage  

38. The term **auditable velocity** means:  
    A) Fast iteration with recorded specs, prompts, and decisions under green gates  
    B) Unreviewed speed  
    C) Merge on failure  
    D) Bypass CI  

39. **Contract tests** in AI apps ensure:  
    A) Stability of interfaces despite internal changes  
    B) Training data freshness  
    C) Diagram accuracy  
    D) GPU savings  

40. A **graduate-level** failure mode for eval suites is:  
    A) Running nightly  
    B) Overfitting prompts to eval fixtures rather than general behaviors  
    C) Too many rubrics  
    D) Using numeric scoring  

41. The most conceptual value of **PR templates** is:  
    A) Muting reviewers  
    B) Normalizing governance and traceability checklists across all changes  
    C) Auto-merging code  
    D) Design aesthetics  

42. **Ethical source handling** in AI development emphasizes:  
    A) Maximizing token counts  
    B) Avoiding documentation  
    C) Attribution, license compliance, and data governance  
    D) Copy-pasting licenses  

43. **Handoffs** should log routing metadata because it:  
    A) Impresses dashboards  
    B) Adds latency  
    C) Supports post-hoc analysis of decision quality and debugging  
    D) Lowers coverage  

44. A **graduate signal** of GPS maturity is:  
    A) High spec/test alignment with short lead times and low change failure rate  
    B) Single-step merges  
    C) Massive PRs  
    D) Random evals  

45. **Retry prompts** should be used when:  
    A) The editor theme changes  
    B) Any flakiness occurs anywhere  
    C) Guardrails or contract checks fail and a correction hint is available  
    D) The UI is slow  

46. **Diff-only** responses from AI assistants help because they:  
    A) Minimize accidental changes and encourage focused review  
    B) Hide the spec  
    C) Increase token usage  
    D) Lower coverage  

47. **Model choice** should be treated as:  
    A) A personal preference  
    B) A replaceable dependency governed by specs and evals  
    C) Irrelevant to behavior  
    D) A permanent decision  

48. **Cross-functional reviews** are helpful because they:  
    A) Replace tests  
    B) Slow teams  
    C) Surface non-functional concerns like security, privacy, and reliability  
    D) Remove ADRs  

49. **Version pinning** of dependencies and models primarily serves:  
    A) Reproducibility for tests and evals  
    B) UI previews  
    C) Branding  
    D) Token budget  

50. **Prompt hygiene** includes:  
    A) Hidden rules  
    B) Long narratives  
    C) Clear scope, constraints, inputs/outputs, and acceptance mapping  
    D) Unbounded edits  

51. **Spec creep** can be contained by:  
    A) Micro-slicing and renegotiating scope via new specs and PRs  
    B) Disabling evals  
    C) Merging early  
    D) Deleting tests  

52. The conceptual benefit of **structured error envelopes** is:  
    A) Fancier logs  
    B) Consistent failure handling across clients and languages  
    C) Removal of tests  
    D) Larger payloads  

53. **Behavioral KPIs** for GPS include:  
    A) File size  
    B) Lead time, change-failure rate, MTTR, coverage, ADR density  
    C) Color scheme  
    D) Window size  

54. **Test isolation** matters because it:  
    A) Reduces CI workers  
    B) Prevents interdependence and flakiness from shared state  
    C) Forces GPU usage  
    D) Rewrites diffs  

55. **Reproducibility** in evals requires:  
    A) Non-determinism  
    B) Elastic prompts  
    C) Fixed seeds, fixed suites, and versioned configs  
    D) Hidden rubrics  

56. **Governed refactor prompts** should specify:  
    A) Skip documentation  
    B) Any change you like  
    C) Preserve public behavior, keep tests green, summarize rationale  
    D) Remove tests to move fast  

57. **Risk triage** in PRs conceptually prioritizes:  
    A) Font settings  
    B) Surface area of change vs criticality of touched components  
    C) Number of comments  
    D) UI polish  

58. **Causality** in GPS is enhanced by:  
    A) Smaller, independent slices with explicit acceptance  
    B) Nightly merges  
    C) Hidden diffs  
    D) Larger batches  

59. **Policy as code** for governance succeeds when:  
    A) CI enforces lint, tests, and evals as merge gates  
    B) It is optional  
    C) It is manual  
    D) It is documented only  

60. The overarching conceptual shift from PDD to **GPS Engineering** is:  
    A) From tests to diagrams  
    B) From speed alone to speed with formalized governance, traceability, and evaluation  
    C) From prompts to programming languages  
    D) From tools to intuition