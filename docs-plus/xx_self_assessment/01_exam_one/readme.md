# Quiz 1

Here’s a **60-question MCQ quiz** that spans everything we covered: SDD, PDD, TDD, EDD, ADR, PHR, PR gates, GPS Engineering, Cursor vs VS Code + Codex, OpenAI Agents SDK, SSE, error handling, CI, metrics, roadmap, repo layout, and more. Each item has 4 options with varied lengths. The **answer key** is in the file `answer_key.md`.

---

### Multiple-Choice Questions

1. In GPS Engineering, what primarily turns intent into an executable contract?  
   A) Commit messages  
   B) Prompt history  
   C) Unit tests  
   D) ADRs  

2. Which pairing best describes GPS Engineering in one line?  
   A) Linting plus CI gates only  
   B) Prompts governed by specs, tests, evals, decisions, PRs  
   C) IDE automation without review  
   D) Specs plus prompts without testing  

3. Which artifact captures **why** a decision was made?  
   A) README  
   B) PHR  
   C) ADR  
   D) CI log  

4. The **Spec-Compliance** checkbox in PRs mainly enforces:  
   A) Contract adherence  
   B) Commit naming  
   C) Docker image size  
   D) Coding style  

5. In the PDD loop, which ordered trio is correct?  
   A) Red → Refactor → Green  
   B) Explain → Red → Green  
   C) Green → Red → Refactor  
   D) Architect → Red → Green  

6. Which belongs to **EDD**?  
   A) Ruff configuration  
   B) promptfoo behavior suites  
   C) Uvicorn reload flag  
   D) .env.sample variables  

7. “No green, no merge” refers to:  
   A) Branch protection removal  
   B) Local dev only  
   C) Passing tests and gates  
   D) Lint warnings  

8. A thin SDD spec for `/chat` should primarily include:  
   A) UI mockups only  
   B) Cloud billing charts  
   C) Behavior, constraints, acceptance criteria  
   D) Full code samples  

9. In our service, the 400 error for missing `user_message` must be:  
   A) `{"error": {"code": "MISSING_USER_MESSAGE"}}`  
   B) `{"status": "MISSING_USER_MESSAGE"}`  
   C) `{"detail": "MISSING_USER_MESSAGE"}`  
   D) `{"error_code": "MISSING_USER_MESSAGE"}`  

10. For SSE, the correct end-of-stream marker is:  
    A) `data:complete\n`  
    B) `event: done\n\n`  
    C) `data:[DONE]\n\n`  
    D) `data:[EOF]\n`  

11. Cursor is strongest at:  
    A) Build artifact signing  
    B) Inline tab completion and predictive multi-file edits  
    C) Autonomous multi-repo refactors without review  
    D) License scanning  

12. VS Code + GPT-5 Codex shines for:  
    A) Container runtime tweaks  
    B) Repo-wide agentic tasks and PR prep  
    C) GPU provisioning  
    D) Animated UML export  

13. Which **tooling** belongs to the OpenAI Agents SDK use in our design?  
    A) Controllers, Sagas, Repositories, DTOs  
    B) Pods, Services, Ingress, CRDs  
    C) Lambdas, Layers, Gateways, Groups  
    D) Agents, Tools, Sessions, Handoffs, Guardrails  

14. Guardrails in our chatbot ensure:  
    A) URL routing rules  
    B) Output shape and length constraints  
    C) Model version pinning only  
    D) Horizontal autoscaling  

15. In TDD, “Red” means:  
    A) Refactor step finished  
    B) CI rerun needed  
    C) All tests skipped  
    D) Failing tests introduced first  

16. The **PHR** primarily stores:  
    A) Exact prompts, scope, acceptance, outcome  
    B) Binary logs  
    C) Docker layers  
    D) GPU configs  

17. For `/chat` SSE, the **response header** must include:  
    A) `Accept: text/event-stream`  
    B) `Content-Type: application/json`  
    C) `Content-Type: text/event-stream`  
    D) `Cache-Control: immutable`  

18. The PR template’s governance role is to:  
    A) Pin dependencies  
    B) Auto-deploy to production  
    C) Gate merges with traceability and checks  
    D) Replace unit tests  

19. Our repo uses **uv** to:  
    A) Sign commits  
    B) Manage Python env and dependencies  
    C) Serve static files  
    D) Render docs  

20. “Baby steps” in PDD means:  
    A) Commit squashing only  
    B) Minimal, test-scoped changes  
    C) Large diffs after week-long cycles  
    D) Refactor without tests  

21. ADR-0002 recorded the choice of:  
    A) Frontend theme  
    B) Database engine  
    C) Streaming protocol (SSE vs WS vs long-poll)  
    D) ORM frameworks  

22. A **traceability** chain in GPS links:  
    A) Secrets → Key vault → Token  
    B) Linter → Formatter → Type checker  
    C) README → Dockerfile → Makefile  
    D) Spec → PHR → ADR → PR → CI  

23. The ChatReply model includes:  
    A) `message`, `tool`, `stage`  
    B) `body`, `selected_tool`, `route`  
    C) `text`, `used_tool?`, `handoff`  
    D) `content`, `tooling`, `state`  

24. EDD smoke on PRs is for:  
    A) GPG verification  
    B) Behavior drift detection  
    C) Load testing  
    D) Traffic shaping  

25. The **best place** for SDD specs is:  
    A) `tests/`  
    B) `docs/specs/`  
    C) `app/guards/`  
    D) `evals/datasets/`  

26. For secrets, the rule is:  
    A) Stored only in README  
    B) In git submodules  
    C) In `.env` with `.env.sample`  
    D) Inline in code for speed  

27. A correct SSE event line is:  
    A) `line token\n`  
    B) `emit:token\n\n`  
    C) `token:<data>\n`  
    D) `data:<token>\n\n`  

28. “Smallest change to green” discourages:  
    A) Prompt capture  
    B) Any CI usage  
    C) Over-refactoring before tests pass  
    D) Any unit tests  

29. Cursor “Rules for AI” should encode:  
    A) Branch naming regex  
    B) SDD×PDD×TDD×EDD guardrails  
    C) Editor font size  
    D) GPU driver versions  

30. In the dual setup, **switching tools** is easiest because:  
    A) Identical UI skins  
    B) Git-synced repo and shared artifacts  
    C) They share local caches  
    D) Both use the same license server  

31. The **400** error envelope shape is validated by:  
    A) Contract tests  
    B) Lint rules  
    C) Docker entrypoint  
    D) Mermaid diagrams  

32. Which metric is a GPS KPI?  
    A) API spelling count  
    B) IDE open time  
    C) Lead time to change  
    D) Pixels per chart  

33. “No green, no merge” typically sits between:  
    A) Lint and Publish  
    B) Tests/EDD and Build  
    C) Build and Publish  
    D) ADR and PR  

34. Prompt library reuse helps by:  
    A) Eliminating tests  
    B) Standardizing high-leverage prompts  
    C) Replacing specs entirely  
    D) Avoiding reviews  

35. The repo map places **SSE helpers** in:  
    A) `.githooks/`  
    B) `docs/diagrams/`  
    C) `app/streaming.py`  
    D) `evals/behavior/`  

36. An example EDD check we used:  
    A) TLS renegotiation  
    B) Tool-first math/time policy  
    C) IPv6 routing  
    D) Container UID mapping  

37. ADRs typically include:  
    A) Unit test reports  
    B) Decision, context, options, consequences  
    C) Binary artifacts  
    D) Sprint velocity charts only  

38. PHRs should be kept:  
    A) In CI caches  
    B) In `docs/prompts/` with IDs  
    C) Inside compiled wheels  
    D) In ephemeral chat only  

39. A minimal `/healthz` endpoint primarily:  
    A) Executes tools  
    B) Streams tokens  
    C) Returns `{ "status": "ok" }`  
    D) Returns service config  

40. A correct JSON ChatReply example is:  
    A) `{"say":"hi","flag":false}`  
    B) `{"message":"hi","tool":"x","route":"y"}`  
    C) `{"content":"hi","meta":{}}`  
    D) `{"text":"hi","handoff":false,"used_tool":null}`  

41. Which belongs in **CI** for our starter?  
    A) DB schema migrations  
    B) UI snapshot diffs only  
    C) Ruff + Pytest (+ optional EDD)  
    D) GPU kernel updates  

42. Nano Banana diagrams help mainly with:  
    A) Token caching  
    B) Team visualization and onboarding  
    C) Binary compression  
    D) Executable code generation  

43. SSE is preferred over WS for v1 because:  
    A) Needs binary frames  
    B) Simplicity and easy proxying  
    C) Full-duplex messaging is required  
    D) Mandatory backpressure  

44. Which acceptance test ensures error contract?  
    A) `test_streaming_emits_json`  
    B) `test_readme_renders`  
    C) `test_chat_missing_user_message_returns_400_top_level_error_code`  
    D) `test_healthz_ok`  

45. “Tool-first” means the agent should:  
    A) Disable handoffs  
    B) Use tools for math/time requests  
    C) Avoid any function calls  
    D) Guess times and math  

46. The **Spec → PHR → ADR → PR → CI** chain enables:  
    A) Theme switching  
    B) Auditable change history  
    C) Static linking  
    D) Faster GPU clocks  

47. The `Accept: text/event-stream` header is sent by:  
    A) Docker daemon  
    B) Client request  
    C) Server  
    D) CI workflow  

48. The SSE `Content-Type` is set by:  
    A) Promptfoo  
    B) Git hooks  
    C) Client only  
    D) Server response  

49. In GPS, refactoring should occur:  
    A) Only in main branch  
    B) After green, keeping tests passing  
    C) Before tests exist  
    D) Without any tests  

50. A **thin** SDD spec avoids:  
    A) Contract examples  
    B) Behavior and constraints  
    C) Over-detailed implementation  
    D) Acceptance criteria  

51. The starter’s error helper lives in:  
    A) `docs/adr/`  
    B) `app/http_errors.py`  
    C) `.github/workflows/`  
    D) `evals/behavior/`  

52. The PR template adds which governance item?  
    A) Editor themes  
    B) Billing approvals  
    C) GPU utilization table  
    D) **Spec-Compliance** checkbox  

53. Which is true about PHRs?  
    A) Stored in Docker registry  
    B) One per repo only  
    C) One per slice or step with IDs  
    D) Optional for governance  

54. An example of **progressive slicing** we used is:  
    A) EDD before unit tests always  
    B) JSON `/chat`, then SSE streaming  
    C) Docker before specs  
    D) SSE first, then JSON  

55. In dual IDE use, Codex is better for:  
    A) Managing .env  
    B) Mermaid export  
    C) Parallel agentic tasks and PR prep  
    D) Inline tab completions  

56. The **EDD smoke** suite runs:  
    A) On client browsers  
    B) On PRs to catch behavior drift  
    C) After deployment only  
    D) Only on main branch  

57. A correct “done” condition for a slice is:  
    A) Docker image built  
    B) Spec acceptance tests + unit tests green  
    C) Explainer written only  
    D) Diagram exported  

58. “No secrets in prompts” is enforced by:  
    A) Docker healthcheck  
    B) Unit test fixture  
    C) Team policy + PR checks  
    D) Editor theme  

59. The minimal SSE tokenizer used in the green zip:  
    A) Performs subword BPE  
    B) Uses external API  
    C) Streams fixed words like “Hello”, “ from”, “ SSE”  
    D) Requires GPU  

60. A key migration milestone within 90 days is:  
    A) Disable CI  
    B) Delete ADRs  
    C) Publish internal rules bundles and prompt libraries  
    D) Remove all tests