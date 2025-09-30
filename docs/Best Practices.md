### **The Official Guide to Effective Spec-Driven Development with Spec Kit**

#### **Introduction: Beyond Code, Towards Intent**

Spec-Driven Development (SDD), as implemented by Spec Kit, represents a fundamental shift in software creation. It inverts the traditional power dynamic where specifications serve as mere suggestions for the "real work" of coding. In SDD, the specification is not a suggestion; it is the **executable source of truth**. Code becomes the tangible expression of a well-defined, machine-interpretable intent.

This guide consolidates the documented procedures within the Spec Kit repository with the core philosophies shared by its creator. Following these practices will help your team move faster, reduce ambiguity, and build more resilient, maintainable software.

---

### **Core Philosophy: The Principles That Guide SDD**

1.  **The Specification is the Lingua Franca:** The `spec.md` is the most durable and important artifact in the entire workflow. It defines the *what* and the *why*. While technical plans and tasks may change, the spec is the anchor. When drift or confusion occurs, always return to the spec.

2.  **Embrace Iteration and the "Living Document":** No specification is perfect on the first attempt. The SDD process is designed for continuous refinement. Discoveries made during planning or even implementation should be fed back into the `spec.md`. This is not a failure of the process but its greatest strength: ensuring the source of truth is always accurate.

3.  **Git is Your Most Powerful Tool:** The entire SDD workflow is built upon the safety and traceability of Git.
    *   **Branches Isolate Features:** Each `/specify` command creates a dedicated branch, ensuring that new features are developed in a safe, isolated environment.
    *   **Commits Isolate Tasks:** Adhering to the "one commit per task" rule creates an atomic, reversible history. This is not just good practice; it is the mechanism that powers recovery tools like `/rollback-feature`.

4.  **The Constitution is Your Team's Agreement:** The `memory/constitution.md` file is a template for your team's engineering principles. It is meant to be modified. If your team doesn't practice strict TDD, *remove that clause*. Aligning the constitution with your team's actual practices is critical for making the AI a productive partner rather than a source of friction.

---

### **The SDD Workflow: A Step-by-Step Guide**

This workflow applies to both new ("greenfield") and existing ("brownfield") projects.

#### **Phase 1: Initialization and Foundation**

1.  **Initialize the Project:**
    *   For a new project, run `uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>`.
    *   For an existing project, navigate to the root and run `uvx --from git+https://github.com/github/spec-kit.git specify init --here --force`. The `--force` flag is necessary to merge the Spec Kit framework into your existing files.

2.  **Establish Your Constitution (`/constitution`):**
    *   **This is the most important first step.** Before writing any specifications, define your architectural and quality principles.
    *   **Prompt Example:** `/constitution Our project uses Python with FastAPI. All endpoints must have integration tests. We prefer simplicity over unnecessary abstraction.`
    *   This tailors all future AI-generated output to your team's specific standards.

#### **Phase 2: Specification and Refinement**

1.  **Create the Feature Specification (`/specify`):**
    *   Describe the feature in natural language. Focus on user stories and acceptance criteria. **Do not mention technology.**
    *   **For Existing Projects:** Provide context. The AI needs to know about the existing architecture to integrate the new feature.
        *   **Bad Prompt:** `/specify Add a profile page.`
        *   **Good Prompt:** `/specify Add a profile page to our existing Hugo website. The components are in /layouts/partials/ and we use Bootstrap CSS.`

2.  **Clarify Ambiguities (`/clarify`):**
    *   Run this command immediately after `/specify`. The AI will ask you up to five targeted questions to resolve ambiguities in your description.
    *   This is a critical step to prevent the AI from making incorrect assumptions that lead to rework later. Answering these questions solidifies the spec.

#### **Phase 3: Planning**

1.  **Generate the Technical Plan (`/plan`):**
    *   Now, you introduce the technology. Tell the AI *how* to build the feature defined in the spec.
    *   **Prompt Example:** `/plan Implement this using Vue.js for the frontend and a PostgreSQL database. State management should use Pinia.`
    *   The agent will generate a `plan.md` along with `data-model.md`, `contracts/`, and other design artifacts based on your technical direction and the approved `spec.md`.

#### **Phase 4: Tasking and Implementation**

1.  **Generate the Task List (`/tasks`):**
    *   Simply run `/tasks`. The AI will analyze all the artifacts (`spec.md`, `plan.md`, etc.) and produce a granular, ordered, and executable checklist in `tasks.md`.

2.  **Analyze the Plan (Optional but Recommended) (`/analyze`):**
    *   Run `/analyze` for a final consistency check. It acts as a "linter for your entire plan," cross-referencing the spec, plan, and tasks to find gaps or contradictions before you write a single line of code.

3.  **Execute the Implementation (`/implement`):**
    *   Run `/implement`. The AI will now execute the `tasks.md` checklist, writing code, running tests, and committing after each successful task.

---

### **The Quality & Recovery Suite: Your Safety Net**

The new commands are designed to make this workflow resilient.

*   **Before Planning/Tasking (`/diagnose`):** Run this for a quick check to see if you've left any `[NEEDS CLARIFICATION]` markers that will cause the next step to fail.
*   **After Implementation (`/debug`):** Run a full audit of your codebase against the spec and constitution. This is your automated QA.
*   **To Fix Issues (`/align <ID>`):** Use this to surgically fix an issue found by `/debug`.
*   **If `/specify` Goes Wrong (`/rollback-feature`):** This is your undo button. It uses Git to safely revert the last feature setup.
*   **If `/implement` is Interrupted (`/sync-tasks`):** This command intelligently figures out where the process stopped and gives you safe options to resume.