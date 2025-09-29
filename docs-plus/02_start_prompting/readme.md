# Starting Spec Driven Development (SDD)
This guide helps you choose and try AI coding tools based on your budget while maintaining the same Spec-Driven Development (SDD) methodology across all tiers.

Choose the option that fits your budget; the disciplined loop remains the same: Spec → Plan → Prompt → Test/Evaluate → Refactor → Record → Review.

1. **$0/mo — Qwen Code (CLI) + Gemini CLI**: Start free with two terminal tools. Qwen Code offers strong repo exploration, git automation, and optional vision. Gemini CLI provides large‑context prompting, great for long prompts and scripts.
2. **$20/mo — Cursor Pro**: An AI‑native IDE with Agent Mode, multi‑file awareness, parallel agents, and fast tab completion.
3. **$40+/mo — GPT‑5 Codex + Cursor Pro**: Two Autonoumous AI Agents in Cursor AI Native IDE for parallel, repo‑wide work.
4. **Add‑On (Any budget) — Keep Gemini CLI + Qwen Code alongside anything above**: The free tier of both tools can be used in combination with Cursor Pro or GPT‑5 Codex for extra flexibility at no additional cost.
> Start free, then upgrade as your needs grow.

![Budget-based picks](./image.png)

## Tool Comparison

Below is a comparison of the four SDD tool options, tailored to different budgets, with consistent formatting and focus on their features, strengths, and use cases.


| Aspect              | Qwen Code (CLI) | Gemini CLI | Cursor Pro (AI-First IDE) | GPT-5 Codex (Cloud Agent) |
|---------------------|-----------------|------------|---------------------------|---------------------------|
| **Core Design**     | Terminal-based coding agent with strong repo analysis and optional vision support for multimodal prompts. | Terminal-native assistant with large context windows, ideal for long prompts and scripts. | AI-native IDE (VS Code fork) with seamless UI for inline edits, autocomplete, and multi-file awareness. | Cloud-based agent for agentic coding, focusing on parallel task execution and repo-wide automation. |
| **User Interaction**| CLI prompts for quick tasks, codebase queries, and git automation; runs locally with OAuth/API. | CLI prompts with simple Google auth; optimized for scripting and long, single-flow sessions. | Interactive, local IDE with inline suggestions, previews, and chat integrated with files/projects. | Conversational and autonomous; describe tasks via ChatGPT or CLI, executes with minimal supervision. |
| **Strengths**       | Free with 2K req/day, excels in codebase exploration, vision support, and git utilities. | Free, large context windows, fast setup, ideal for scripting and educational workflows. | Fast daily coding, multi-file edits, Agent Mode, parallel agents, and exclusive tab completion. | Handles complex, parallel, repo-wide tasks; generates PRs with tests/docs; strong automation. |
| **Use Cases**       | Learning, repo audits, architecture reviews, quick refactors via CLI. | Long prompts, scripting, terminal-based workflows, educational tasks. | Individual/team coding, prototyping, iterative development with rapid tab completion. | Large-scale automation, building from scratch, cross-repo tasks with minimal hands-on work. |
| **Pricing**         | Free ($0/mo). | Free ($0/mo). | Pro plan (~$20/mo), limited free tier. | Plus/Enterprise or API (~$40+/mo). |
| **Limitations**     | CLI-only UX; complex edits need editor integration; quotas apply. | CLI-only; fewer repo-wide automation features than Codex/Cursor. | Review needed for refactors; fewer autonomous long-running tasks than Codex. | Slower for simple edits; cloud latency; less interactive in-editor without extensions. |

## Getting Started
1. **Free Tier ($0/mo)**: Use **Qwen Code CLI** for codebase exploration and git automation, paired with **Gemini CLI** for long-context scripting. Ideal for beginners or lightweight projects.
2. **Pro Tier ($20/mo)**: Upgrade to **Cursor Pro** for an AI-native IDE with fast tab completion, Agent Mode, and multi-file editing, perfect for solo developers or small teams.
3. **Premium Tier ($40+/mo)**: Combine **GPT-5 Codex** with **Cursor Pro** for autonomous, repo-wide automation and PR generation, suited for complex projects or teams needing scalability.
4. Start with the free tier and upgrade as your workflow evolves, keeping the SDD method consistent.


## Latest SWE-bench Verified

In short: SWE-bench Verified is the most commonly cited, cleaner benchmark for end-to-end, agentic code fixing on real repositories, scored by passing the project’s tests after your patch.

Here’s an apples-to-apples snapshot of **SWE-bench Verified** results for the four we care about. We list the **most recent, citable scores**, and call out when the number depends on the evaluation harness (single/multi-attempt, custom agent, or 500-turn runs).

| Model / Tool                       | SWE-bench Verified score | Notes (harness / caveats)                                                                                                                                                                                     |
| ---------------------------------- | -----------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Anthropic – Claude Opus 4.1**    |                **74.5%** | Anthropic’s own announcement for Opus 4.1; update over Opus 4.0’s 72.5%.                                                                                                                      |
| **OpenAI – GPT-5 Codex**           |           **74.5–74.9%** | 74.9% stated in GPT-5 launch (initially on 477/500 tasks); follow-up post clarifies reporting; tech press widely quotes **74.5%** for Codex variant. Treat as \~74.5–74.9 depending on harness.  |
| **Google – Gemini 2.5 Pro**        |                **63.8%** | Google/DeepMind blog cites **63.8%** using a **custom agent**; product page also shows **31.6% (single attempt)** / **42.6% (multi-attempt)** without the custom agent.                    |
| **Qwen – Qwen3Max-Coder / Qwen3-Max** |               **≈69.6%** | Reported in multiple roundups for **500-turn** runs; Qwen’s blog claims SOTA among open-source but doesn’t pin a single number. Use \~69.6% as the current ballpark.              |
| **Cursor Pro (IDE)**               |                        — | Not a model—no SWE-bench score; performance depends on which model/agent you run inside Cursor.                                                                                                               |

                                                          
## Practical performance (what you’ll feel day-to-day)

* **GPT-5 Codex** – shows the best *agentic coding* results on public leaderboards; Best at large, multi-file changes and autonomous bug-fix PRs; strongest *SWE-bench Verified* **74.5%**, showing among public numbers right now. Expect better planning + code review abilities.

* **Gemini CLI (2.5 Pro)** – Very capable agentic runs with generous free limits; excels in terminal-centric workflows, huge context, and easy pairing with Google’s Code Assist/MCP. **SWE-bench Verified** \~**63.8%** 

* **Qwen Code (Qwen3Max-Coder)** – Excellent free/open models for local/offline and repo-friendly code gen & repair; top open-source results on classic code benchmarks; for agentic repo-wide tasks you’ll likely pair it with a framework and careful tooling.
* **Cursor Pro** – Big productivity win (indexing, apply-diffs, background agents). Quality maps to the model you choose (GPT-5 Codex, Gemini, Claude, etc.). Pricing is transparent and reasonable for daily use.

---
## Free-Tier Ranking

Here’s a **free-tier ranking** (most to least generous), across the five you’re tracking:

|  Rank | Tool / Model                    | What you get for free                                                                                                                                                       |              |
| ----: | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **1** | **Qwen Code (open-weights)**    | Run locally = **no API fees** (you only pay your own compute). If you use Alibaba’s hosted API, **new users get free token quotas** (e.g., 1M tokens on select Qwen tiers). 2,000 requests/day at no charge for Code|  |
| **2** | **Gemini CLI (Gemini 2.5 Pro)** | Official blog: **up to 60 requests/min and 1,000 requests/day at no charge** for CLI usage.                                                                                 |   |
| **3** | **Claude Code**                 | **Claude Free** tier includes coding features, but with **daily usage limits** (no precise numbers published; resets daily).                                                |   |
| **4** | **Cursor (Hobby)**              | **Free IDE plan** with **limited Agent requests** and **limited tab completions**.                                                                                          |       |
| **5** | **GPT-5 Codex**                 | **No meaningful free tier**: access is via **ChatGPT paid plans** or **paid API**; free ChatGPT doesn’t include GPT-5/Codex.                                                |       |

**Notes**

* If you can run models locally, **Qwen open-weights** is the most “free” (no per-token bill). Hosted Qwen still starts with a **promotional free quota** for new Alibaba Cloud accounts.
* **Gemini CLI**’s free allowance is the most concrete/quantified among hosted options (1,000 req/day).
* **Claude Free** clearly exists, but Anthropic doesn’t publish strict daily numbers; multiple roundups confirm the tier and that heavy users hit caps.
* **Cursor** is an IDE: its Hobby plan is free, but actual **LLM usage limits are tight** until you subscribe—and model tokens are billed by the provider when you connect paid APIs.




---
## Pricing Ranking

Here’s a **price-ranked** comparison (cheapest → most expensive) using current list prices for coding-capable models. We’ve split **API token pricing** (per 1M tokens) from **subscription seats** like Cursor.

### API pricing (per 1M tokens)

|    Rank | Model / Tool                          |       Input |      Output | Notes                                                                |
| ------: | ------------------------------------- | ----------: | ----------: | -------------------------------------------------------------------- |
|       1 | **Qwen3-Coder-Flash** (Alibaba Cloud) | **\$0.144** | **\$0.574** | Tiered by prompt size (0–32k bucket shown).      |
|       2 | **Qwen3-Coder-Plus** (Alibaba Cloud)  |  **\$1.00** |  **\$5.00** | Also tiered by prompt size (0–32k bucket).       |
| 3 (tie) | **OpenAI GPT-5 / GPT-5-Codex**        |  **\$1.25** | **\$10.00** | OpenAI states Codex is **same price as GPT-5**.         |
| 3 (tie) | **Google Gemini 2.5 Pro**             |  **\$1.25** | **\$10.00** | Higher tier for >200k-token prompts.  |
|       5 | **Anthropic Claude Sonnet 4**         |  **\$3.00** | **\$15.00** | Standard (short-context) rates.                      |
|       6 | **Anthropic Claude Opus 4.1**         | **\$15.00** | **\$75.00** | Flagship Claude tier.                              |

> **Note:** Qwen open-weights can be run **locally** (no API fee; you still pay infra). The Alibaba Cloud prices above apply when you use their hosted API. 

### Subscription / seat pricing (not per token)

| Product              |                                                                     Price | What it covers                                                                      |
| -------------------- | ------------------------------------------------------------------------: | ----------------------------------------------------------------------------------- |
| **Cursor Pro (IDE)** | **\$20 / user / month** (individual). Teams from **\$40 / user / month**. | Editor features; LLM usage billed at provider’s API rates you choose. |

---


