# **Step 6: Implement, Test, and Validate**

**Goal:** Direct the AI agent to execute the entire task list, turning the specification and plan into a fully functional, tested, and verifiable piece of software. In this phase, your role shifts from writer to director and quality assurance.

---

## **Inputs**

- The complete and finalized `tasks.md` checklist from the previous step.
- The full context of the feature directory (`spec.md`, `plan.md`, `constitution.md`).
- Your agent chat (Cursor, Gemini CLI, etc.) with a running terminal.

## **Actions**

1.  **Initiate the Implementation:** Give the AI agent a single, clear command to begin the work. You are handing it the entire checklist and authorizing it to proceed.

    - **Your Prompt Example (Perfect):**
      ```
      /implement Implement the tasks for this project and update the task list as you go. @tasks.md
      ```

2.  **Monitor the Agent's Execution:** Your primary role now is to observe. The AI will announce what it's doing, following the `tasks.md` file as its script. You will see a flurry of activity in the terminal and in your file tree as the agent:

    - **Sets up the environment** (e.g., runs `npm install`, configures `tsconfig.json`).
    - **Writes failing tests first** (adhering to the TDD principle in your constitution).
    - **Implements the core logic** to make the tests pass.
    - **Creates all necessary files:** components, pages, utility functions, data files, and stylesheets.
    - **Refines and polishes** the code based on instructions in the task list.

3.  **Perform the Interactive Review Loop:** The agent will not run completely on its own. It will periodically stop and present you with a set of file changes. This is your critical review checkpoint.

    - For each set of changes, review the code diff.
    - **Ask yourself:** Does this code correctly implement the specific task? Does it adhere to our Constitution? Is it clean and maintainable?
    - Click **"Keep"** to approve the changes and let the agent continue to the next task. If something is wrong, click "Undo" and provide a corrective prompt.

4.  **Final Validation (The Human's Turn):** After the agent reports that all tasks are complete (as seen in your example output), you perform the final verification. Do not blindly trust the AI's summary.

    - **Run the Tests Yourself:** In the terminal, run the test suite to get an objective confirmation that everything works as specified.
      ```bash
      npm test
      ```
    - **Run the Application:** Start the development server and interact with the feature yourself.
      ```bash
      npm run dev
      ```
      Open the browser and click around. Does it look and feel like the experience you envisioned in your `spec.md`? This is the ultimate test.

5.  **Commit the Working Software:** Once you are fully satisfied, commit all the work to the feature branch.
    - **Example Commit Message (from your output):**
      ```
      git commit -m "feat(podcast): implement modern podcast website"
      ```

---

## **Deliverables**

- A complete, working, and tested implementation of the feature on its own Git branch.
- An updated `tasks.md` file where all tasks are checked off, providing a clear audit trail of the work performed.

## **Quality Gates ✅**

- ✅ All automated tests created during the process pass successfully in CI and locally.
- ✅ You have manually reviewed the agent's code at each step of the implementation loop.
- ✅ You have manually run and interacted with the final application, confirming it meets the user experience outlined in the `spec.md`.

## **Common Pitfalls**

- **"Fire and Forget":** Giving the `/implement` command and not actively monitoring and reviewing the agent's progress. This can lead to the agent going down the wrong path.
- **Ignoring Failing Tests:** If the agent's implementation fails a test and it can't fix it, it's your job to intervene, diagnose the problem, and provide guidance.
- **Skipping the Final Manual Review:** Relying solely on automated tests might miss visual bugs, awkward user flows, or other user experience issues. Always look at the final product.

## References

- Spec Kit Plus repo: https://github.com/panaversity/spec-kit-plus
- PyPI package: https://pypi.org/project/specifyplus/
- Original Spec Kit repo: https://github.com/github/spec-kit

## Next Step

When implementation is complete and you have verified the work locally, continue to [Step 8: Ship with `/sp.git.commit_pr`](../09_git_commit_pr/readme.md) to package the branch into commits and a pull request.
