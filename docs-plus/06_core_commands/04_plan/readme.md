# **Step 4: Define the Technical [Plan](https://github.com/panaversity/spec-kit-plus/blob/main/spec-driven.md#the-plan-command) (The "How")**

**Goal:** Translate the "what" and "why" from the approved spec into a concrete technical strategy. This phase generates the high-level engineering blueprint, including architecture, data structures, and setup instructions, all while respecting the Constitution.

---

## **Inputs**

-   The **approved and clarified** `spec.md` from the previous step.
-   Your `constitution.md` file.
-   The `/plan` command available in your agent chat.

## The /plan Command
Once a feature specification exists, this command creates a comprehensive implementation plan:

- Specification Analysis: Reads and understands the feature requirements, user stories, and acceptance criteria
- Constitutional Compliance: Ensures alignment with project constitution and architectural principles
- Technical Translation: Converts business requirements into technical architecture and implementation details
- Detailed Documentation: Generates supporting documents for data models, API contracts, and test scenarios
- Quickstart Validation: Produces a quickstart guide capturing key validation scenarios

## **Actions**

1.  **Craft and Run the Plan Prompt:** In your agent chat, run the `/plan` command. Your prompt should clearly state the high-level technical choices for the feature. **Crucially, you must `@mention` the `spec.md` file** so the agent uses it as the source of truth.
    *   **Your Prompt Example (Perfect):**
        ```
        /plan I am going to use Next.js with static site configuration, no databases - data is embedded in the content for the mock episodes. Site is responsive and ready for mobile. @specs/001-i-am-building/spec.md
        ```

2.  **Observe the Agent's Automated Artifact Generation:** The `/plan` command is more than a single action. As your output shows, the agent will now execute a script to scaffold a comprehensive technical foundation for the feature:
    *   It creates the main `plan.md` file, which serves as the central hub for the implementation strategy.
    *   It also generates several **supporting artifacts** inside the feature's `specs/` directory:
        *   `research.md`: Documents initial technical decisions and alternatives considered.
        *   `data-model.md`: Outlines the shape of the data and entities (e.g., the fields for a `PodcastEpisode`).
        *   `contracts/`: A folder that will contain formal data schemas (like JSON Schema) to validate data.
        *   `quickstart.md`: Provides simple, clear instructions for another developer to set up and run this feature locally.
		*	May generate a contracts/ directory as well.

3.  **Human Review of the Entire Plan:** Your job is now to review this collection of generated documents.
    *   **Start with `plan.md`:** Read through it. It will have an Execution Flow, a Summary, and a "Constitution Check" section where the agent confirms its plan aligns with your rules.
    *   **Review Supporting Docs:**
        *   Look at `data-model.md`. Does the data structure make sense? Does it include all the necessary fields?
        *   Look at `quickstart.md`. Are the setup steps clear and correct?
    *   **Iterate with the Agent:** If any part of the plan is incorrect or incomplete, have a conversation with the agent to refine it.
        *   **Example Prompt:** `In @data-model.md, the Episode entity is missing a 'duration' field. Please add it as a string formatted like "MM:SS" and update the document.`

4.  **Version and Commit the Plan:** Once you are satisfied that the plan is complete, actionable, and respects the constitution, mark it as ready.
    *   Manually edit `plan.md`'s header to update its status.
    *   Commit all the newly created and modified plan artifacts to the feature branch.

---

## **Deliverables**

-   A committed `plan.md` file that serves as the technical blueprint.
-   A set of supporting artifacts (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`) that provide deep technical context for the feature.

## **Quality Gates ✅**

-   ✅ The technical plan directly addresses every functional requirement listed in `spec.md`.
-   ✅ The agent's "Constitution Check" within `plan.md` has passed, and you have manually verified its claims.
-   ✅ The generated data models and contracts are accurate and complete.
-   ✅ (For teams) The entire set of plan artifacts has been reviewed and approved in a Pull Request.

## **Common Pitfalls**

-   **Allowing the plan to restate the spec** instead of providing a clear *technical* path forward.
-   **Introducing new scope or features** that were not defined in the original, approved spec.
-   Forgetting about **operational concerns** like testing strategy, deployment, and monitoring, which should be part of the technical plan.
-   **Not reviewing the supporting artifacts** (`data-model.md`, `quickstart.md`, etc.), as they are just as important as the main `plan.md`.

## References

- Spec Kit Plus repo: https://github.com/panaversity/spec-kit-plus
- PyPI package: https://pypi.org/project/specifyplus/
- GitHub blog overview: https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
