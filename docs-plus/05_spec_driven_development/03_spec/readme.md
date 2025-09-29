# **Step 3: [Specify](https://github.com/panaversity/spec-kit-plus/blob/main/spec-driven.md#the-specify-command) the Feature (The "What" and "Why")**

**Goal:** Translate a high-level user need into a detailed, unambiguous, and reviewable specification. This artifact becomes the shared source of truth for the feature before any technical planning begins.

---

### **Inputs**

- The approved `constitution.md` file.
- A clear idea of the user problem you are solving (your "product intent brief").
- The `/specify` slash command, which is now available in your agent's chat.

---

### The /specify Command

This command transforms a simple feature description (the user-prompt) into a complete, structured specification with automatic repository management:
- Automatic Feature Numbering: Scans existing specs to determine the next feature number (e.g., 001, 002, 003)
- Branch Creation: Generates a semantic branch name from your description and creates it automatically
- Template-Based Generation: Copies and customizes the feature specification template with your requirements
- Directory Structure: Creates the proper specs/[branch-name]/ structure for all related documents

### **Actions**

Setup a new project `sp init hello_spp`, constitution and follow along:

1.  **Craft and Run the Specify Prompt:** In your agent chat, run the `/specify` command. Provide a clear, user-focused description of the feature. **Crucially, include a reference to your `constitution.md` file** to ensure the AI's output adheres to your project's rules.
    *   **Your Prompt Example (Perfect):**
        ```
        /specify @constitution.md I am building a modern podcast website. I want it to look sleek, something that would stand out. Should have a landing page with one featured episode, an about page, and a FAQ page. Should have 20 episodes, and the data is mocked - you do not need to pull anything from any real feed.
        ```

2.  **Observe the Agent's Automated Scaffolding:** The AI agent will now execute its `specify` script. It will perform several actions automatically:
    *   It creates a new, isolated Git branch for the feature (e.g., `001-i-am-building`).
    *   It generates a new folder inside `specs/` for all of this feature's artifacts.
    *   It creates a `spec/**.md` file inside that folder, populating it based on your prompt and a template.
    *   It performs an initial validation of the spec against your constitution.
    *   You must Verify and Approve the Generated .md file. You can further iterate manualy or using your AI Companion as well.
    ```
    For things you need clarification use the best guess you think is reasonable. Update acceptance checklist after.
    ```

3.  **Human Review & Clarification Loop (The Most Important Part):** The agent has provided a first draft. Now, your role as the developer is to refine it into a final, complete specification.
    *   Open the newly generated `spec.md` file.
    *   **Resolve Ambiguities:** Search the document for any `[NEEDS CLARIFICATION]` markers. For each one, have a conversation with your agent to resolve it.
        *   **Example Prompt:** `In @spec.md, it asks about episode ordering. Let's make it reverse chronological (newest first). Please update the document and remove the clarification marker.`
    *   **Tighten Scope:** Review the generated user stories and functional requirements. Are they accurate? Add explicit non-goals to prevent scope creep.
        *   **Example Prompt:** `In @spec.md, under non-goals, please add that this feature will not include user comments or real-time playback analytics.`
    *   **Ensure Testability:** Read the Acceptance Scenarios. Are they clear, measurable, and written in a way that can be easily turned into automated tests (like Given/When/Then)?
        *   **Example Prompt:** `The acceptance scenario for the landing page is good, but please add a new scenario: "Given I am on the landing page, When I click the 'View All Episodes' button, Then I am taken to the '/episodes' page."`

4.  **Version and Commit the Spec:** Once the `spec.md` is clear, complete, and agreed upon, update its status.
    *   Manually edit the `spec.md` header from `Status: Draft` to `Status: Ready for Planning`.
    *   Commit the finalized `spec.md` to its feature branch.

---

### **Deliverables**

- A new Git branch dedicated to the feature.
- A final, reviewed, and committed `spec.md` file that serves as the unambiguous source of truth for what you are building.

**Next step: run the /plan command when ready.**

### **Quality Gates ✅**

- ✅ All `[NEEDS CLARIFICATION]` markers have been resolved.
- ✅ The spec includes clear, testable Acceptance Scenarios for all primary user flows.
- ✅ The spec aligns with the project rules defined in `constitution.md`.
- ✅ (For teams) The spec has been reviewed and approved by relevant stakeholders (e.g., in a Pull Request).

### **Common Pitfalls**

- **Moving to the `/plan` step too early**, before all ambiguities in the spec are resolved. This is the #1 mistake to avoid.
- Writing a `/specify` prompt that describes *how* to build it, not *what* to build (e.g., "create a React component" vs. "show the user a list of episodes").
- Forgetting to `@mention` the constitution in your prompt, which can lead to the AI ignoring your core rules.

## References

- Spec Kit Plus repo: https://github.com/panaversity/spec-kit-plus
- PyPI package: https://pypi.org/project/specifyplus/
- Original Spec Kit repo: https://github.com/github/spec-kit
