# What is [Spec-Driven Development](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)?

Instead of coding first and writing docs later, in spec-driven development, you start with a (you guessed it) spec. This is a contract for how your code should behave and becomes the source of truth your tools and AI agents use to generate, test, and validate code. The result is less guesswork, fewer surprises, and higher-quality code.

In 2025, this matters because:

* AI IDEs and agent SDKs can turn ambiguous prompts into a lot of code quickly. Without a spec, you just get **elegant garbage faster**.
* Agent platforms (e.g., **OpenAI Agents SDK**) make multi-tool, multi-agent orchestration cheap—but the **cost of weak specifications is amplified** at scale.
* The broader ecosystem (e.g., GitHub’s recent “spec-driven” tooling push) is converging on **spec-first workflows** for AI software. 

[Spec-driven AI coding with GitHub’s Spec Kit](https://www.infoworld.com/article/4062524/spec-driven-ai-coding-with-githubs-spec-kit.html)

[From Spec to Deploy: Building an Expense Tracker with SpecKit](https://dev.to/manjushsh/from-spec-to-deploy-building-an-expense-tracker-with-speckit-1hg9)

[Watch: Spec-Driven Development in the Real World](https://www.youtube.com/watch?v=3le-v1Pme44)

Industry is converging on **spec-driven development (SDD)**—writing a durable, reviewable **spec** (intent, behavior, constraints, and success criteria) first, then using AI/tools to implement against it. This moves teams away from “vibe coding” and toward predictable delivery, especially on multi-person, multi-repo work.

### The 3 things you need for SDD to actually work

1. **Alignment first.** Hash out the problem, scope, user journeys, non-goals, risks, and acceptance criteria so everyone (PM, Eng, Design, QA, stakeholders) agrees before code is generated. ([YouTube][1])
2. **Durable artifacts.** Keep the spec, plan, and acceptance tests as living files in the repo (PR-reviewed), not in ephemeral chats. Treat them as the source of truth that survives code churn. ([The New Stack][2])
3. **Integrated enforcement.** Tie the spec to verification: executable examples/tests, CI checks, and traceable tasks so regressions or spec drift are caught automatically. ([apideck.com][3])

### A practical SDD workflow (as shown/discussed)

* **Intent brief → AI-drafted spec → human review loop.** Start from a high-level product brief; let AI expand to a detailed spec; iterate with the team until acceptance criteria are unambiguous.
* **Plan → tasks → implementation.** Break the spec into verifiable tasks; let AI/agents implement; keep the spec and tests side-by-side with the code.
* **Continuous verification.** PRs must cite the spec sections they fulfill and include tests/examples that prove the behavior.

### Why it beats “vibe coding”

* Captures decisions in a **reviewable artifact** instead of buried chat threads.
* **Speeds onboarding** and cross-team collaboration.
* Reduces **rework and drift** because tests/examples anchor behavior. ([The New Stack][2])

### Tools & patterns mentioned/adjacent in the ecosystem

* **Spec-Kit Plus** (Panaversity open-source toolkit)
* **Spec-Kit** (GitHub’s open-source toolkit) — templates and helpers for running an SDD loop with your AI tool of choice.
* Broader coverage in recent articles summarizing SDD’s rise and best practices.

## Walk the [Spec-Kit Plus](https://github.com/panaversity/spec-kit-plus) SDD Cycle

Ready to practice? Follow the step folders in this directory:

1. [Step 1 – Setup Environment](01_setup_speckit_plus/readme.md)
2. [Step 2 – Define Constitution](02_constitution/readme.md)
3. [Step 3 – Specify & Clarify](03_spec/readme.md)
4. [Step 4 – Define Plan](04_plan/readme.md)
5. [Step 5 – Generate Task List](05_tasks/readme.md)
6. [Step 6 – Implement](06_implementation/readme.md)
7. [Step 7 – Capstone Chatbot](08_chatbot_project/readme.md)
8. [Step 8 – Clarify & Analyze Deep Dive](07_spec_analyze_clarify/readme.md)
9. [Step 9 – Operationalize the Nine Articles](09_operationalize_nine_articles/readme.md)

Each guide includes inputs, actions, quality gates, and common pitfalls so you can build muscle memory for spec-driven development.

> **Note**: Use `specifyplus` or `sp` commands.

### Quick start

```bash
# Install from PyPI (recommended)
pip install specifyplus
# or with uv
uv tool install specifyplus

# Use the CLI
specifyplus init my-app
# or alias
sp init my-app

# One-time usage
uvx specifyplus --help
uvx specifyplus init my-app
```

### Take-home checklist

* Start every feature with a **one-page intent brief** and **acceptance criteria**.
* Store **spec.md**, **plan.md**, and **examples/tests** in the repo; review them like code.
* Make every PR link to the spec section it implements; **fail CI** if required examples/tests are missing.
* Periodically **refactor the spec** (not just the code) as understanding evolves. ([The New Stack][2])

---

## Official Spec Kit Plus resources

- [Spec Kit Plus GitHub repository](https://github.com/panaversity/spec-kit-plus) — enhanced templates, scripts, and CLI
- [PyPI package](https://pypi.org/project/specifyplus/) — install with `pip install specifyplus`
- [Original Spec Kit repository](https://github.com/github/spec-kit) — base implementation
- [Spec Kit video overview](https://www.youtube.com/watch?v=a9eR1xsfvHg) — walkthrough of the end-to-end workflow


[1]: https://www.youtube.com/watch?v=3le-v1Pme44&utm_source=chatgpt.com "Spec-Driven Development in the Real World"
[2]: https://thenewstack.io/spec-driven-development-the-key-to-scalable-ai-agents/?utm_source=chatgpt.com "Spec-Driven Development: The Key to Scalable AI Agents"
[3]: https://www.apideck.com/blog/spec-driven-development-part-1?utm_source=chatgpt.com "An introduction to spec-driven API development"
[4]: https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/?utm_source=chatgpt.com "Spec-driven development with AI: Get started with a new ..."
