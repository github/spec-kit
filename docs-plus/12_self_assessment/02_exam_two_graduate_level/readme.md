# Quiz 2

Here’s a **second, graduate-level 60-question MCQ quiz** covering the full session (GPS Engineering: SDD × PDD × TDD × EDD × ADR × PHR × PR; OpenAI Agents SDK; SSE; dual IDE setup; CI/CD; metrics; governance). **Answer key is in the file answer_key.md**

---

## Multiple-Choice Questions (Graduate Level)

1. In GPS Engineering, what is the **primary mechanism** to prevent prompt drift across iterations?  
   A) Larger model context windows  
   B) Frequent refactors without tests  
   C) SDD specs with acceptance criteria mapped to tests and evals  
   D) High-entropy prompts with creative temperature  

2. Which statement best captures the **contractual difference** between TDD and EDD?  
   A) TDD verifies code behavior; EDD verifies model behaviors against scenario rubrics  
   B) TDD checks model tokens; EDD checks HTTP headers  
   C) TDD validates CI; EDD validates Docker  
   D) TDD only linting; EDD only formatting  

3. An ADR choosing **SSE over WebSocket** in v1 is mostly justified by:  
   A) Full-duplex need and binary frames  
   B) Simpler infra and easy proxy compatibility for token streams  
   C) TLS renegotiation requirements  
   D) Mandatory client push channels  

4. For `/chat`, the spec requires a top-level 400 envelope. Which property enforces **client simplicity** most?  
   A) Free-form error messages  
   B) Nested error objects  
   C) HTML error bodies  
   D) Top-level `{"error_code": "..."}`  

5. Which describes **PHR’s** governance role most precisely?  
   A) Dependency lockfile  
   B) Immutable record of prompts, scope, acceptance, and outcome per slice  
   C) Mypy configuration  
   D) Build cache  

6. In a PR, **Spec-Compliance** should be checked when:  
   A) Linter passes regardless of behavior  
   B) The README compiles  
   C) The Docker image is minimal size  
   D) Acceptance criteria in spec are demonstrably satisfied by tests/evals  

7. A **graduate-level risk** of vibe coding in multi-agent systems is:  
   A) Unbounded architectural drift under ambiguous prompts  
   B) Too few environment variables  
   C) Too many comments  
   D) Excessive type hints  

8. What is the **most defensible order** for a new slice in GPS Engineering?  
   A) Green → Red → Explain → Merge  
   B) Architect → Red → Green → Refactor → Explainer → PR  
   C) PR → Red → Green → Architect  
   D) Refactor → Architect → Merge  

9. Which **traceability edge** is essential for audits?  
   A) Linter → ADR linkage  
   B) Mermaid → CI linkage  
   C) PHR → PR linkage with exact prompt IDs  
   D) Dockerfile → PR linkage  

10. Why is **offline testing** emphasized in TDD for LLM-backed services?  
    A) Faster GPUs locally  
    B) Easier to leak secrets  
    C) Improves container size  
    D) Determinism and stability without network/model variance  

11. A subtle pitfall when writing specs for LLM systems is:  
    A) Ambiguous behavioral constraints that models interpret inconsistently  
    B) Over-specifying UI colors  
    C) Too many acceptance tests  
    D) Too short ADRs  

12. Which OpenAI Agents SDK feature most directly supports **separation of concerns**?  
    A) Handoffs to specialized agents  
    B) Disabling guardrails  
    C) Sessions only  
    D) Single monolithic tool  

13. A test asserts SSE emits `data:[DONE]`. What **failure mode** does this detect?  
    A) Wrong HTTP verb  
    B) Early stream termination without a terminator  
    C) Missing .env file  
    D) Linter failure  

14. The **tool-first policy** is primarily designed to:  
    A) Force math/time tasks into deterministic functions before generation  
    B) Disable handoffs entirely  
    C) Increase token counts for creativity  
    D) Reduce Pydantic imports  

15. In dual-environment practice, when should **Codex** be preferred over Cursor?  
    A) Quick tab completion mid-function  
    B) Wide, agentic, repo-scale transformations and PR preparation  
    C) Inline micro-edits  
    D) Changing theme settings  

16. A sophisticated **EDD smoke** test for scope discipline should:  
    A) Sort imports  
    B) Evaluate image size  
    C) Penalize hallucinated fields or extraneous tools not in spec  
    D) Ensure CI runs on ARM  

17. What is a **graduate-level criterion** indicating an ADR is warranted?  
    A) Any file rename  
    B) Comment typo fix  
    C) Choice impacting protocol, data contract, or reliability guarantees  
    D) Changing a docstring  

18. The **smallest change to green** principle primarily reduces:  
    A) PR frequency  
    B) Confounding variables during failure diagnosis  
    C) Docs length  
    D) CPU usage  

19. In the repo, placing **SSE helpers** in a separate module improves:  
    A) Cohesion and testability of streaming logic  
    B) Prompt tokenization  
    C) Docker layer caching only  
    D) Coupling  

20. A **well-formed spec** for `/chat` would **not** include:  
    A) Error envelopes and codes  
    B) Request/response shape  
    C) Hand-written code samples for all branches  
    D) Limits and acceptance checks  

21. For secrets, the most robust operational control is:  
    A) Using `.env`/env vars and rotating keys with zero-downtime  
    B) Checking API keys into git  
    C) Printing them to logs  
    D) Putting secrets in README  

22. When adopting GPS across teams, which metric best indicates **governance maturity**?  
    A) Higher token counts in prompts  
    B) Average PR size decreasing while pass rates hold  
    C) More branches per developer  
    D) More Docker layers  

23. If **SSE** is chosen for v1, a **future ADR** might most likely reconsider:  
    A) Monorepo vs polyrepo  
    B) JSON schema version  
    C) README license badge  
    D) Upgrade to WebSocket for bidirectional tool UIs  

24. A **PHR ID convention** helps with:  
    A) Docker digest shortening  
    B) GPU pinning  
    C) Deterministic referencing in PRs, CI logs, and retrospectives  
    D) Git LFS usage  

25. In EDD, a behavior suite for **tool-first math** should score:  
    A) Neutral regardless of method  
    B) Higher when long narratives are produced  
    C) Lower when math is not solved via the calculator tool  
    D) Higher when the model guesses mental arithmetic  

26. A **graduate-level anti-pattern** for PDD is:  
    A) Combining multiple features in one Green prompt creating large diffs  
    B) Red tests isolated from network  
    C) Architect prompts that specify acceptance tests  
    D) Explainer summaries under 8 bullets  

27. Which **CI gate** increases reliability most for LLM apps?  
    A) Build first, test later  
    B) Contract tests + EDD smoke + lint before build  
    C) Release before CI  
    D) Single linter  

28. What’s the **strongest reason** to keep tests offline by default even with mocks of the SDK?  
    A) Model providers mandate it  
    B) Improves typing speed  
    C) Prevent nondeterminism from model changes and rate limits  
    D) Enables larger logs  

29. For `/chat`, why is `Content-Type: text/event-stream` essential?  
    A) Reduces latency via HTTP/3  
    B) Enables SSE framing semantics for chunk handling by clients  
    C) Triggers JSON parsing  
    D) Prevents DNS caching  

30. A **governed refactor** should be executed:  
    A) After Green, with tests unchanged and still passing  
    B) Before tests exist  
    C) Only if CI is disabled  
    D) Only on main  

31. A rigorous spec often improves **model controllability** by:  
    A) Increasing inference temperature  
    B) Disabling retries  
    C) Tightening output structure and constraints  
    D) Removing guardrails  

32. “No green, no merge” impacts org culture by:  
    A) Encouraging speculative merges  
    B) Eliminating reviews  
    C) Lowering the social cost of requesting changes early  
    D) Making tests optional  

33. In the OpenAI Agents SDK, **handoff** is appropriate when:  
    A) Intent requires specialized skills the primary agent shouldn’t emulate  
    B) The request is static text  
    C) Any answer is short  
    D) The model wants fewer tokens  

34. An EDD rubric for **scope discipline** should penalize:  
    A) Matching the spec  
    B) Using structured outputs  
    C) Returning exactly the requested fields  
    D) Adding unrequested fields or formats  

35. Cursor “Rules for AI” should **not** include:  
    A) Security posture and secret handling  
    B) Model-agnosticism  
    C) Personal editor theme color  
    D) PDD loop and constraints  

36. A mature GPS rollout often introduces **which** artifact library?  
    A) Only Mermaid exports  
    B) Single monolithic ADR  
    C) Prompt libraries (architect, red, green, refactor, explainer) with IDs  
    D) Binary wheels for all prompts  

37. A reason to store **PHRs** in-repo rather than in chat logs is:  
    A) Easier emoji reactions  
    B) Versioned, reviewable, linkable evidence for each code delta  
    C) Lower token costs  
    D) Better Docker layers  

38. For `/chat`, the most **defensible** contract decision is to:  
    A) Encode errors as CSV  
    B) Use top-level `error_code` for minimal parsing  
    C) Place error code under a nested `detail` field  
    D) Return HTML  

39. A **graduate design smell** in SSE handling is:  
    A) Using a generator for event lines  
    B) Missing final sentinel `data:[DONE]`  
    C) Testing with mocks  
    D) Returning 200  

40. The **dual IDE** recommendation yields productivity because:  
    A) Each environment optimizes for a different cognitive mode (agentic vs interactive)  
    B) Only one supports Python  
    C) They share the same proprietary engine  
    D) One eliminates PRs  

41. A nuanced reason to adopt **uv** is:  
    A) It replaces Docker  
    B) It compiles C extensions  
    C) Deterministic, fast dependency resolution suited for CI reproducibility  
    D) It runs browsers  

42. A **graduate governance** signal in PRs is:  
    A) Linkage to Spec, PHRs, ADRs and passing CI/EDD annotations  
    B) GIFs of terminals  
    C) Fonts configured in editor  
    D) Screenshots only  

43. An ADR’s **Consequences** section should cover:  
    A) Emoji usage  
    B) Screenshot galleries  
    C) Trade-offs, follow-ups, and migration triggers  
    D) Random links  

44. The **best** reason to gate merges on EDD smoke is:  
    A) It catches behavioral drift that unit tests may miss in LLM flows  
    B) It measures coverage  
    C) It speeds Docker builds  
    D) It simplifies secrets  

45. A solid acceptance test for `/chat` JSON path asserts:  
    A) The README exists  
    B) Docker layer count  
    C) The server uptime  
    D) Response matches `ChatReply` schema and field presence  

46. In Prompt-Driven Development, **Architect prompts** should primarily:  
    A) Change the Docker base image  
    B) Express micro-specs, constraints, acceptance checks, and scope  
    C) Alter CI runners  
    D) Demand code immediately  

47. A rigorous **Refactor prompt** must:  
    A) Change public contracts  
    B) Add new dependencies  
    C) Keep public behavior and tests green while improving internals  
    D) Delete tests  

48. When should a new **ADR** be rejected?  
    A) If it lists consequences  
    B) If it cites trade-offs  
    C) If it repeats an existing accepted decision without new context  
    D) If it mentions options  

49. “Auditable velocity” in GPS means:  
    A) Fast iteration with recorded specs/prompts/decisions and green gates  
    B) Raw speed without checks  
    C) Skipping PHRs  
    D) Merging on red  

50. A subtle way to **overfit** PDD to a single model is to:  
    A) Use structured outputs  
    B) Use tools for math  
    C) Bake model-specific stopwords into contracts  
    D) Keep specs model-agnostic  

51. A **graduate-level** CI smell in LLM apps is:  
    A) Missing behavior evals while shipping prompt changes  
    B) Using ruff  
    C) Unit tests only  
    D) Too many small PRs  

52. A metric indicating **healthy slice sizing** is:  
    A) One monthly PR that changes everything  
    B) Frequent small PRs with high pass rates and low rework  
    C) Constant hotfixes  
    D) Average PR > 2,000 lines  

53. For **SSE buffering** behind proxies, a mitigation is to:  
    A) Convert to HTML  
    B) Use binary frames  
    C) Only send `[DONE]`  
    D) Increase event chunk frequency and disable compression if needed  

54. A **graduate** reason to prefer top-level `error_code` over nested objects is:  
    A) Parsing cost and failure-mode isolation for clients in multiple languages  
    B) JSON aesthetics  
    C) Easier to add emojis  
    D) Faster Docker builds  

54. A resilient **prompt library** should be:  
    A) Versioned, ID’d, and mapped to specs/tests  
    B) Encrypted and hidden  
    C) Written as screenshots  
    D) Stored in ephemeral docs  

56. A defensible **go-live checklist** item for GPS is:  
    A) Skip behavior tests  
    B) Merge on red to save time  
    C) Ensure ADR links in PR, CI green, EDD smoke passing, and secrets rotated  
    D) Delete specs after deploy  

57. A **graduate** streaming test might additionally assert:  
    A) README size  
    B) Correct headers, at least one data event, and a termination sentinel with no trailing junk  
    C) Dockerfile presence  
    D) Line endings only  

58. Handoffs should log **handoff_reason** to:  
    A) Amuse reviewers  
    B) Enable tracing of agent routing decisions for debuggability and governance  
    C) Warm caches  
    D) Reduce tokens  

59. A nuanced **metrics pitfall** is to:  
    A) Track lead time and change-failure rate together  
    B) Optimize for coverage alone without scenario quality  
    C) Use ADR density as a proxy for decisions  
    D) Track MTTR  

60. A 90-day **institutionalization** milestone for GPS is to:  
    A) Remove CI for speed  
    B) Centralize all prompts in private chats  
    C) Skip PR reviews  
    D) Publish rules bundles, prompt libraries, and dashboards org-wide