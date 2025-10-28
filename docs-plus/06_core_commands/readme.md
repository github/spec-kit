# What is [Spec-Driven Development](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)?

Instead of coding first and writing docs later, in spec-driven development, you start with a (you guessed it) spec. This is a contract for how your code should behave and becomes the source of truth your tools and AI agents use to generate, test, and validate code. The result is less guesswork, fewer surprises, and higher-quality code.

In 2025, this matters because:

- AI IDEs and agent SDKs can turn ambiguous prompts into a lot of code quickly. Without a spec, you just get **elegant garbage faster**.
- Agent platforms (e.g., **OpenAI Agents SDK**) make multi-tool, multi-agent orchestration cheap—but the **cost of weak specifications is amplified** at scale.
- The broader ecosystem (e.g., GitHub’s recent “spec-driven” tooling push) is converging on **spec-first workflows** for AI software.

### Why it beats “vibe coding”

- Captures decisions in a **reviewable artifact** instead of buried chat threads.
- **Speeds onboarding** and cross-team collaboration.
- Reduces **rework and drift** because tests/examples anchor behavior.

### Tools & patterns mentioned/adjacent in the ecosystem

- **Spec-Kit Plus** (Panaversity open-source toolkit)
- **Spec-Kit** (GitHub’s open-source toolkit) — templates and helpers for running an SDD loop with your AI tool of choice.
- Broader coverage in recent articles summarizing SDD’s rise and best practices.

## How Spec-Kit Plus Works: Automatic Documentation + Explicit Decision Points

Spec-Kit Plus extends GitHub's Spec Kit with two key innovations:

### 1. **Automatic Prompt History Records (PHR)**

Every significant AI interaction is automatically captured as a structured artifact—no extra commands needed. You work normally, and get complete documentation of your AI-assisted development journey.

**What gets captured automatically:**

- `/sp.constitution` commands → PHR created
- `/sp.specify` commands → PHR created
- `/sp.plan` commands → PHR created + ADR suggestion
- `/sp.tasks` commands → PHR created
- `/implement` commands → PHR created
- Debugging, refactoring, explanations → PHRs created

**You see:** Brief confirmation like `📝 PHR-0003 recorded`

### 2. **Explicit Architecture Decision Records (ADR)**

After planning completes, you get a suggestion to review for architectural decisions. You explicitly run `/adr` when ready to capture significant technical choices.

**Flow:**

```
/plan completes
    ↓
📋 "Review for architectural decisions? Run /adr"
    ↓
(You run /adr when ready)
    ↓
ADRs created in history/adr/ (if decisions are significant)
```

**Why explicit?** Architectural decisions require careful judgment, team discussion, and review of existing patterns. You control when this happens.

---

## Quick Reference: Commands & Automation

| Command             | What It Does                           | PHR Created? | ADR Created?       |
| ------------------- | -------------------------------------- | ------------ | ------------------ |
| `/sp.constitution`  | Define project principles              | ✅ Automatic | ❌ No              |
| `/sp.specify`       | Write feature spec                     | ✅ Automatic | ❌ No              |
| `/sp.plan`          | Design architecture                    | ✅ Automatic | 📋 Suggestion only |
| `/sp.adr`           | Review architectural decisions         | ❌ No\*      | ✅ Explicit        |
| `/sp.tasks`         | Break down implementation              | ✅ Automatic | ❌ No              |
| `/sp.implement`     | Execute TDD cycle                      | ✅ Automatic | ❌ No              |
| `/sp.git.commit_pr` | Generate commits/PR from finished loop | ❌ No        | ❌ No              |
| Debugging           | Fix errors                             | ✅ Automatic | ❌ No              |
| Refactoring         | Clean up code                          | ✅ Automatic | ❌ No              |
| `/sp.phr` (manual)  | Override automatic PHR                 | ✅ Explicit  | ❌ No              |

\* The `/adr` command itself doesn't create a PHR, but the planning session before it does

---

Ready to build muscle memory for spec-driven development? Start Shipping! 🚀

> **Note**: Use `specifyplus` or `sp` commands.

> **Loop reminder:** The core workflow now spans eight steps—wrap every finished feature with `/sp.git.commit_pr` after `/analyze` confirms coverage.

## Official Spec Kit Plus resources

- [Spec Kit Plus GitHub repository](https://github.com/panaversity/spec-kit-plus) — enhanced templates, scripts, and CLI
- [PyPI package](https://pypi.org/project/specifyplus/) — install with `pip install specifyplus`
