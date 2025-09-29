# Step 9: Operationalize the Nine Articles 🧭

**Goal:** embed the [Nine Articles of Development](https://github.com/github/spec-kit/blob/main/spec-driven.md#the-nine-articles-of-development) into your day-to-day loops so SDD stays simple, observable, and test-first as work scales.

## The Nine Articles of Development: A Quick Refresher

Here are the core ideas behind the Nine Articles of Development.

*   **Article I: Library-First Principle:** All new features must start as standalone libraries, never directly inside application code. This enforces modularity from the outset.
*   **Article II: CLI Interface Mandate:** Every library must be accessible through a command-line interface (CLI) that accepts and produces text (like JSON), ensuring observability and testability.
*   **Article III: Test-First Imperative:** This is a non-negotiable rule. Tests must be written, validated, and confirmed to fail *before* any implementation code is written. This follows the Red-Green-Refactor cycle of Test-Driven Development (TDD).
*   **Article IV & V (Implied):** While not detailed in the summary, these likely relate to versioning and dependency management, crucial for a library-first approach.
*   **Article VI (Implied):** This could cover documentation standards, ensuring that libraries and CLIs are usable.
*   **Articles VII & VIII: Simplicity and Anti-Abstraction:** These articles work together to fight over-engineering. They mandate using a minimal project structure (e.g., max 3 projects initially) and trusting the underlying framework directly instead of adding unnecessary abstraction layers.
*   **Article IX: Integration-First Testing:** This principle prioritizes testing in realistic environments. It favors using real databases and services over mocks and requires contract tests to be written before implementation begins.

## Operationalizing the Articles: A Step-by-Step Learning Guide

Here’s how to apply the process you shared, enriched with the context from the articles themselves.

### 1. Map the Articles to Your Artifacts

This first action is about making the abstract principles tangible by connecting them to your daily work.

*   **Article I (Library-First):** When you look at your task board, does every task for a new feature point to the creation or modification of a library? If a task is about "adding a button to the user page," it should be rephrased as "create a `user-profile` library with a `render-button` function." This forces a clear separation of concerns.
*   **Article II (CLI Interfaces):** Before writing the library, define its CLI. How would you use it from a terminal? For the `user-profile` library, you might define a command like `user-profile --render-button --user-id 123`. This contract becomes the guide for your implementation.
*   **Article III (Test-First):** Your `tasks.md` or branch checklist should explicitly list:
    1.  Write failing test for `render-button`.
    2.  Write implementation to make the test pass.
    3.  Refactor the code.
    This makes the TDD loop a required part of the workflow.
*   **Remaining Articles (Simplicity, Integration-First, etc.):** Embed these as checkboxes in your `spec.md` or pull request templates. For instance:
    *   `[ ]` **Simplicity Check (Art. VII):** Does this feature use the minimum number of projects?
    *   `[ ]` **Integration-First Check (Art. IX):** Are contract tests written and passing against a real service?

### 2. Run the Article Review Ritual

This is about building a shared understanding and accountability within the team.

*   **At Kickoff:** Start your project or sprint by reviewing the `constitution.md`. Go through each article and ask:
    *   "What does 'Library-First' mean for this new chat feature?"
    *   "How can we ensure our tests for this feature are 'Integration-First'?"
*   **Log Violations in an "Article Drift" Table:** No process is perfect. If you need to bypass an article, document it. For example:
| Who | Violated Article | Why? | Mitigation Plan |
| :--- | :--- | :--- | :--- |
| Alice | Article I | Urgent hotfix required; no time to create a separate library. | Create follow-up task to refactor into a library within 2 weeks. |

This log prevents "temporary" exceptions from becoming permanent bad habits.

### 3. Wire Articles into Automation

This step uses tools to enforce discipline, reducing the mental overhead for developers.

*   **Continuous Integration (CI):** Your CI pipeline should be the first line of defense.
    *   Add a script that fails the build if a pull request adds implementation files without corresponding test files (enforcing **Article III**).
    *   Run contract tests automatically to validate service interactions (enforcing **Article IX**).
*   **PR Templates:** Enhance your pull request template with article checkpoints:
    *   "**Article II Compliance:** Please paste a transcript of the CLI for this library in action."
    *   "**Article VII Check:** Justify any new abstractions introduced in this PR."

### 4. Close the Loop Continuously

This final step ensures the system learns and improves over time.

*   **Reconcile with the Drift Table:** After a feature is deployed, review the `/analyze` reports. Did the hotfix that violated Article I lead to a production issue? This data helps reinforce why the articles are important.
*   **Feed Learnings Back:** If you consistently find yourselves making exceptions to a specific article, it might be a sign that your `constitution.md` needs refinement for your team's context. The constitution is meant to be a living document.

By following these steps, the Nine Articles become more than just a list of rules; they become an active, automated, and shared framework for building high-quality, maintainable software.


## Common Pitfalls

- Treating the articles as theory instead of hooking them into backlog items and automation
- Allowing “temporary” exceptions to linger without documentation or follow-up
- Focusing on Articles I–III while ignoring observability (Article IX) and simplicity (Article VII) pressure valves

## References

- Spec Kit Nine Articles: https://github.com/github/spec-kit/blob/main/spec-driven.md#the-nine-articles-of-development
- Spec Kit repo: https://github.com/github/spec-kit
- Spec Kit video overview: https://www.youtube.com/watch?v=a9eR1xsfvHg
