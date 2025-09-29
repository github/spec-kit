# **Step 5: Generate the Actionable [Task](https://github.com/panaversity/spec-kit-plus/blob/main/spec-driven.md#the-tasks-command) List**

**Goal:** Deconstruct the technical plan into a sequence of small, verifiable, and testable tasks. This `tasks.md` file is the final blueprint that the AI agent will follow to build the feature, turning the strategic "how" into a tactical "how-to."

---

## **Inputs**

-   The approved `spec.md`.
-   The approved `plan.md` and all its supporting artifacts (`data-model.md`, etc.).
-   Your `constitution.md` (specifically, any rules on task sizing).
-   The `/tasks` slash command in your agent chat.

## The /tasks Command
After a plan is created, this command analyzes the plan and related design documents to generate an executable task list:

- Inputs: Reads plan.md (required) and, if present, data-model.md, contracts/, and research.md
- Task Derivation: Converts contracts, entities, and scenarios into specific tasks
- Parallelization: Marks independent tasks [P] and outlines safe parallel groups
- Output: Writes tasks.md in the feature directory, ready for execution by a Task agent

## **Actions**

1.  **Generate the Initial Task Breakdown:** In your agent chat, run the `/tasks` command. You can give it the context of the entire feature directory to ensure it has all the necessary information.
    *   **Your Prompt Example (Perfect):**
        ```
        /tasks Follow and break this down into tasks@specs/001-i-am-building/
        ```

2.  **Observe the Agent's Task Generation:** The AI will now process the spec, plan, and constitution. It will generate a single, comprehensive `tasks.md` file inside the feature's directory. As your output shows, it will:
    *   **Structure the Work:** Break down the project into logical phases (e.g., Phase 3.1: Setup, Phase 3.2: Tests First, Phase 3.3: Core Implementation).
    *   **Define Individual Tasks:** Create specific, actionable tasks with unique IDs (e.g., `T001`, `T002`). Each task will map to a concrete action, like "Initialize Next.js app skeleton" or "Create contract validation script."
    *   **Suggest an Execution Strategy:** It may provide guidance on which tasks can be run in parallel `[P]` versus those that must be run sequentially.

3.  **Human Review and Refinement:** This is your final chance to review the construction plan before the "building" starts.
    *   Open the newly generated `tasks.md` file.
    *   **Check for Completeness:** Read through the task list. Does it cover every functional requirement from the spec and every technical component from the plan? Did the agent forget anything (like documentation or final cleanup)?
    *   **Validate the Order:** Does the sequence of tasks make sense? For a TDD project, the "Tests First" tasks should come before the "Core Implementation" tasks.
    *   **Check Task Size:** Is any single task too large? For instance, if you see a task like `T015: Implement entire frontend`, that's a red flag. You should instruct the agent to break it down further.
        *   **Example Prompt:** `"The task T015 is too large. Break it down into separate tasks for creating the header, the footer, the hero component, and the episode list component. Update tasks.md."`
    *   **Add Non-Code Tasks:** The agent might forget process-oriented tasks. Manually add them to the list if needed:
        ```markdown
        - [ ] T0XX: Create a PR for review once all coding tasks are complete.
        ```

4.  **Commit the Final Task List:** Once you are confident the `tasks.md` is complete and actionable, commit it to the feature branch. This document now becomes the locked-down "script" for the implementation phase.

---

## **Deliverables**

-   A final, reviewed, and committed `tasks.md` file that provides a clear, step-by-step implementation checklist.

## **Quality Gates ✅**

-   ✅ The task list completely covers all requirements from the `spec.md` and `plan.md`.
-   ✅ Each task is small, well-defined, and has a clear "definition of done" (often, passing a specific test).
-   ✅ The task sequence is logical and respects dependencies.
-   ✅ (For teams) The `tasks.md` file has been approved by the tech lead or relevant team members.

## **Common Pitfalls**

-   **Accepting the agent-generated list without review.** AI agents can sometimes create vague ("polish the UI") or overlapping tasks.
-   **Forgetting to include tasks for crucial non-feature work,** such as running tests, creating documentation (`README.md`), and setting up CI/CD.
-   **Creating tasks that are too large**, which makes them difficult to review and validate, defeating the purpose of the incremental loop.

## References

- Spec Kit Plus repo: https://github.com/panaversity/spec-kit-plus
- PyPI package: https://pypi.org/project/specifyplus/
- Original Spec Kit repo: https://github.com/github/spec-kit