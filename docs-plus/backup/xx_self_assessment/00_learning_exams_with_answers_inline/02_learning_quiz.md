# Learning Quiz 2 with Inline Answers

We’ve built a 60-question, graduate-level MCQ quiz that emphasizes concepts (not trivia) from our “Prompt-Driven Development” materials (PHRs, ADRs, PRs, Cursor workflow, TDD/SDD, prompt-driven chatbots, diagram prompts, governance, evals, safety, and the “Prompt Architect” mindset). 

---

# Prompt-Driven Development (PDD) & Prompt Architecting

1. PDD’s primary shift in software practice is best described as:  
* A) Eliminating tests in favor of interactive prototyping  
* B) Moving from code-first to prompt-first workflows that are versioned, verified, and reviewed  
* C) Replacing design with rapid coding  
* D) Outsourcing specs to external vendors  
* **Answer: B**

2. In the AI-compiler analogy, the “Prompt Architect” role most closely aligns with:  
* A) A release manager issuing version tags  
* B) A UI designer creating mockups  
* C) A systems architect specifying intent, interfaces, constraints, and acceptance criteria for AI execution  
* D) A compiler engineer controlling register allocation  
* **Answer: C**

3. Which outcome is *not* a core goal of PDD governance?  
* A) Reproducibility of AI-assisted changes  
* B) Maximizing model temperature for creativity in production  
* C) Traceable intent behind changes  
* D) Stronger review signals on non-deterministic edits  
* **Answer: B**

4. A healthy PDD loop is typically:  
* A) Code → comment → commit → push  
* B) Prompt → verify → record → review → merge  
* C) Ideate → ship → refactor later if needed  
* D) Prototype → demo → freeze  
* **Answer: B**

5. “Vibe coding” is an anti-pattern because it:  
* A) Hides decision context, reduces reproducibility, and bypasses verification  
* B) Produces too many unit tests  
* C) Uses too many small prompts  
* D) Requires complex build systems  
* **Answer: A**

6. Prompt decomposition is most useful when:  
* A) Determinism is guaranteed by the model  
* B) You want a single mega-prompt for every task  
* C) The task mixes policy, tooling, and code-gen concerns that benefit from modular prompts  
* D) You want to minimize version control noise  
* **Answer: C**

7. A good “system” prompt in PDD primarily:  
* A) Establishes role, constraints, safety posture, and evaluation norms across turns  
* B) Reduces token usage only  
* C) Changes API keys dynamically  
* D) Forces deterministic decoding  
* **Answer: A**

8. Model portability in PDD is improved by:  
* A) Hard-coding sampling parameters in code  
* B) Using provider-neutral prompt contracts and keeping tool interfaces stable  
* C) Mixing multiple system prompts at random  
* D) Binding prompts to a single provider’s features  
* **Answer: B**

9. Context-window stewardship is mainly about:  
* A) Turning off function-calling  
* B) Prioritizing high-signal artifacts (specs, contracts, tests) while pruning noisy history  
* C) Always truncating the newest content  
* D) Increasing temperature when the window is full  
* **Answer: B**

10. An effective “prompt contract” is:  
* A) A private note from the PM  
* B) A non-versioned comment block in code  
* C) A stable, testable interface describing inputs, outputs, tools, and acceptance checks  
* D) A temporary scratchpad  
* **Answer: C**

# Prompt History Records (PHRs) & Architecture Decision Records (ADRs)

11. PHRs exist primarily to:  
* A) Capture the exact prompts, intent, and verification for reproducible AI changes  
* B) Track cloud costs  
* C) Store release notes  
* D) Replace unit tests  
* **Answer: A**

12. The most important difference between PHRs and ADRs:  
* A) ADRs are about UI; PHRs are about backend  
* B) PHRs record interactions and edits; ADRs record architectural decisions, context, and consequences  
* C) PHRs are legal documents; ADRs are not  
* D) ADRs are private; PHRs are public  
* **Answer: B**

13. A strong PHR typically includes:  
* A) CI runtime logs only  
* B) The prompt(s), rationale, change summary, verification steps, and links to tests/PRs  
* C) A marketing brief  
* D) Only the final diff  
* **Answer: B**

14. ADR “consequences” are valuable because they:  
* A) Surface trade-offs, risks, and expected impact to guide future decisions  
* B) Reduce repository size  
* C) Make the decision reversible  
* D) Record the refactor backlog for auditors  
* **Answer: A**

15. When a prompt change drives a design shift, you should:  
* A) Update both: ADR for the decision, PHR for the prompt interaction and verification  
* B) Update ADR with decision context and leave PHR empty  
* C) Do neither until after release  
* D) Update PHR only  
* **Answer: A**

16. A minimal ADR usually contains:  
* A) Deployment manifests  
* B) Context, decision, alternatives, consequences  
* C) Test suite listings  
* D) Roadmap and budget  
* **Answer: B**

17. PHRs help PR reviewers by:  
* A) Compressing binaries  
* B) Summarizing intent vs. diff and how correctness was established  
* C) Hiding exploratory prompts  
* D) Replacing code comments  
* **Answer: B**

18. The best place to link a PHR is:  
* A) Only in the README  
* B) Inside compiled artifacts  
* C) In the commit message and PR description  
* D) In a private chat  
* **Answer: C**

# Pull Requests (PRs), Reviews, and CI Gates

19. In PDD, PR templates should emphasize:  
* A) Intent, prompt references, acceptance checks, and regression tests  
* B) Only screenshots  
* C) Colors and fonts  
* D) Branch naming conventions only  
* **Answer: A**

20. A useful PR reviewer mindset for AI changes is:  
* A) “Is intent clear and verified? Are specs/tests sufficient for future maintainers?”  
* B) “Does the diff look clever?”  
* C) “Is the code shorter?”  
* D) “Is the model brand the same?”  
* **Answer: A**

21. A CI gate uniquely important for AI-assisted changes:  
* A) Static type checks only  
* B) Replay of PHR prompts and running acceptance tests to verify deterministically constrained behavior  
* C) Linting only  
* D) Code coverage thresholds only  
* **Answer: B**

22. For non-deterministic generations, a common mitigation is:  
* A) Increase context length automatically  
* B) Fix seeds or lower temperature; constrain with specs/tests and validate semantic equivalence  
* C) Disable tests  
* D) Ignore failures and re-run until green  
* **Answer: B**

23. Shadow deployment of a new AI path means:  
* A) Replacing the data store  
* B) Running the new path in parallel, capturing metrics without user impact  
* C) Turning off old paths  
* D) Manual testing only  
* **Answer: B**

24. A rollback plan in PDD typically relies on:  
* A) Deleting ADRs  
* B) Feature flags, prompt version pins, and immutable artifact promotion  
* C) Hot-fixing in production only  
* D) Force-pushing to main  
* **Answer: B**

# TDD / SDD / Specs and Tests

25. The TDD core loop is:  
* A) Red → Green → Refactor  
* B) Ship → Learn → Repeat  
* C) Plan → Prototype → Present  
* D) Build → Break → Fix  
* **Answer: A**

26. TDD best supports AI-assisted coding when tests:  
* A) Are randomized  
* B) Are small, isolated, and executable quickly to anchor each incremental behavior  
* C) Are replaced by demos  
* D) Are written after generation  
* **Answer: B**

27. In SDD (Spec-Driven Development), the spec functions as:  
* A) A log of CI runs  
* B) The acceptance contract driving generation, tooling, and tests  
* C) Marketing collateral  
* D) A diagram only  
* **Answer: B**

28. “Red tests bundle” usage primarily ensures:  
* A) Fewer PR comments  
* B) There is a failing spec-aligned test suite before generation begins  
* C) Higher latency  
* D) The linter runs first  
* **Answer: B**

29. Unit vs. integration vs. end-to-end tests in PDD:  
* A) Replace ADRs  
* B) Provide layered confidence: small correctness, subsystem interactions, and user-visible flows  
* C) Are unnecessary with LLMs  
* D) Should all be end-to-end only  
* **Answer: B**

30. “Small steps” in TDD matter because they:  
* A) Increase PR size intentionally  
* B) Make failures local, support quick fixes, and preserve momentum with guardrails  
* C) Reduce token usage only  
* D) Delay learning  
* **Answer: B**

31. Given-When-Then scenarios are most directly tied to:  
* A) Acceptance criteria in BDD-style specs  
* B) Prompt caching  
* C) Vendor contracts  
* D) Build scripting  
* **Answer: A**

32. A spec is “good” when it:  
* A) Lists future ideas  
* B) Is minimal, testable, unambiguous about inputs/outputs/constraints  
* C) Contains UI screenshots only  
* D) Is verbose and ambiguous  
* **Answer: B**

# Cursor-centric Workflow & Prompt Hygiene

33. A practical Cursor setup for PDD emphasizes:  
* A) Editing JSON by hand only  
* B) Disabling git  
* C) Project scripts (make/uv), tests wired to hotkeys, model routing, and git integration  
* D) Multiple unrelated workspaces at once  
* **Answer: C**

34. Cursor “rules” in PDD context usually include:  
* A) Randomizing providers  
* B) Demanding PHR capture, running tests after each AI change, and keeping prompts modular  
* C) Allowing AI edits without tests  
* D) Bypassing reviews for small diffs  
* **Answer: B**

35. Multi-model routing helps because:  
* A) It eliminates tests  
* B) Different tasks (analysis, code-gen, refactor) benefit from models optimized for those modes  
* C) It reduces human oversight  
* D) It locks you into one vendor  
* **Answer: B**

36. Prompt hygiene generally *does not* include:  
* A) Bundling unrelated tasks into one mega instruction  
* B) Versioning prompt artifacts  
* C) Using clear roles and constraints  
* D) Including acceptance checks and example IO  
* **Answer: A**

37. Cursor with tests on a hotkey is valuable because:  
* A) It makes the “red→green→refactor” cadence quick and habitual  
* B) It increases PR size  
* C) It hides failures  
* D) It replaces PHRs  
* **Answer: A**

# Prompt-Driven Chatbots & Agents

38. A prompt-driven chatbot architecture typically includes:  
* A) Prompts but no persistence  
* B) LLM core, tool interfaces/actions, retrieval or memory, safety and evaluation layers  
* C) Only a front-end  
* D) A database and nothing else  
* **Answer: B**

39. RAG vs. fine-tuning in this context:  
* A) RAG injects fresh context at inference; fine-tuning changes model weights with curated data  
* B) Fine-tuning is always cheaper  
* C) Both modify weights identically  
* D) RAG requires no indexing  
* **Answer: A**

40. Tool-use in agents should be:  
* A) Declarative with explicit schemas, idempotence concerns, and error handling  
* B) Hidden from tests  
* C) Implicit and undocumented  
* D) Avoided in production  
* **Answer: A**

41. Memory design for agents stresses:  
* A) Selective retention, summarization, and eviction tied to tasks and privacy constraints  
* B) Disabling context updates  
* C) Storing everything forever  
* D) Client-side only  
* **Answer: A**

42. Safety in an agent pipeline is best enforced:  
* A) With layered pre-filters, system policies, tool constraints, and post-hoc evaluation  
* B) In PR description text only  
* C) Only at UI level  
* D) By disabling tools  
* **Answer: A**

43. Evaluation of a chatbot should:  
* A) Vary sampling parameters randomly  
* B) Use spec-aligned test sets, golden answers, and rubric-based graders where possible  
* C) Avoid regression data  
* D) Rely solely on subjective demos  
* **Answer: B**

44. Prompt injection risks are mitigated by:  
* A) Letting the agent “decide later”  
* B) Defining tool call policies, sanitizing inputs, and using allow-lists for actions and domains  
* C) Blindly following user-provided content  
* D) Disabling logs  
* **Answer: B**

# Diagram Prompts & Communication

45. Diagram prompts should emphasize:  
* A) Freehand drawings  
* B) Only color themes  
* C) Clear entities, labeled relationships, constraints, and directionality that map to the architecture  
* D) Decorative shapes  
* **Answer: C**

46. Using diagrams in PDD chiefly helps with:  
* A) Random brainstorming  
* B) Shared mental models across roles (PM, QA, Dev, Sec) and traceability to specs  
* C) Replacing tests  
* D) Token cost only  
* **Answer: B**

47. A good diagram prompt for workflow modeling includes:  
* A) Marketing slogans  
* B) Explicit states, transitions, guards, and error paths  
* C) Only boxes  
* D) Fonts and palettes  
* **Answer: B**

# Reproducibility, Metrics, and Operations

48. Reproducibility of AI changes typically requires:  
* A) Capturing prompts, seeds/params when relevant, data snapshots, and verifications  
* B) Avoiding PRs  
* C) Hard-coding provider IP addresses  
* D) Removing randomness entirely in all stages  
* **Answer: A**

49. Key production metrics for AI features *do not* usually include:  
* A) Blue/green parity and drift  
* B) Latency and cost per call  
* C) Keyboard layout preferences  
* D) Task success rate and guardrail violation rate  
* **Answer: C**

50. Observability for AI systems benefits from:  
* A) Structured logs for prompts, tool calls, errors, and evaluation outcomes with PII minimization  
* B) Ad-hoc debug prints in production  
* C) Suppressing logs  
* D) Screenshots only  
* **Answer: A**

51. A practical caching strategy aims to:  
* A) Cache only failures  
* B) Balance freshness, security, and determinism; cache safe, stable sub-results behind feature flags  
* C) Cache every response forever  
* D) Disable invalidation  
* **Answer: B**

52. Rollout maturity increases when teams:  
* A) Use feature flags, staged exposure, canaries, and automatic rollback criteria  
* B) Merge directly to main  
* C) Disable metrics to reduce noise  
* D) Avoid documentation  
* **Answer: A**

53. Cost control without quality loss often comes from:  
* A) Cutting tests entirely  
* B) Deeper prompt engineering, tool offloading, prompt chaining, and smaller models where acceptable  
* C) Randomly choosing cheaper providers  
* D) Disabling safety layers  
* **Answer: B**

# Ethics, Privacy, and Risk

54. Data privacy in PDD requires:  
* A) Minimizing sensitive data in prompts, redaction, differential access, and regionalization as needed  
* B) Sending everything to third parties for convenience  
* C) Turning off encryption  
* D) Testing only in production  
* **Answer: A**

55. An ethical review for an AI feature should confirm:  
* A) It has the most advanced model  
* B) It respects user consent, explains limitations, and avoids harmful automation risks  
* C) It uses dark patterns to increase engagement  
* D) It is entertaining  
* **Answer: B**

56. Governance alignment means:  
* A) Ignoring audits  
* B) Safety and compliance are codified in specs, tests, CI gates, and PR policy  
* C) Security is a post-merge concern  
* D) Everyone approves manually each time  
* **Answer: B**

# Collaboration & Continuous Improvement

57. Team learning in PDD is amplified by:  
* A) Reusable prompt patterns, shared PHR libraries, and post-mortems tied to ADRs  
* B) Solo experiments  
* C) Private notes only  
* D) Ad-hoc chat threads  
* **Answer: A**

58. When a generation fails evaluation, the next best step is:  
* A) Remove tests that fail  
* B) Inspect failure traces, refine spec or prompt, and re-run tests with smaller scoped changes  
* C) Increase randomness  
* D) Ship anyway if “looks fine”  
* **Answer: B**

59. Cross-functional clarity improves when:  
* A) Design is optional  
* B) ADRs, PHRs, diagrams, and PR templates use consistent vocabulary for artifacts and outcomes  
* C) Specs are hidden from QA  
* D) Only PMs see the plan  
* **Answer: B**

60. A sustainable culture around PDD most relies on:  
* A) Eliminating documentation  
* B) Disciplined artifacts (ADRs, PHRs), testable specs, small steps, and transparent review rituals  
* C) Heroic debugging and late nights  
* D) Outsourcing reviews  
* **Answer: B**