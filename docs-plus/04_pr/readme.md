# What is a Pull Request?

In our software/dev context, **PR = [Pull Request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests)**.

It’s a proposal to merge your changes from one branch into another (e.g., `feature/x` → `main`) on platforms like GitHub/GitLab/Bitbucket. A PR bundles:

* the **diff/commits**
* a **description** of what/why (often linking issues/ADRs)
* **checks** (CI tests, linters)
* **code review** comments/approvals

**Typical PR flow:** push branch → open PR → CI runs → reviewers comment/request changes → you push fixes → approvals → merge → PR closes.

**Good PR etiquette (the “suit on” version):**

* Small, focused scope; clear title & summary
* Link to ADRs/issues; include screenshots or curl examples if relevant
* Passing tests/linters; add/adjust tests for new behavior
* Note breaking changes and rollout steps

(Outside dev, PR can also mean **Public Relations**, but here we mean **Pull Request**.)


Of course\! Here’s a simple tutorial on how to make a pull request on GitHub.

A **pull request** (often called a PR) is how you propose changes to someone else's project on GitHub. You're essentially *requesting* that the project owner *pull* your changes into their main codebase. It's the heart of collaborative coding. 🤝

-----

## The Big Picture: A Simple Analogy

Imagine a friend has a public cookbook. You can't write in their original copy directly. So, you make a photocopy (**fork**), write your new recipe on a new page in your copy (**branch**), and then show it to your friend. If they like your recipe, they'll add it to their original cookbook (**merge the pull request**).

-----

## Step-by-Step Guide to Making a Pull Request (by Forking)

Follow these steps to contribute to any public project on GitHub.

### Step 1: Fork the Repository

First, you need your own copy of the project.

1.  Navigate to the main page of the repository you want to contribute to.
2.  In the top-right corner of the page, click the **Fork** button. This creates a personal copy of the entire project under your GitHub account.

### Step 2: Clone Your Forked Repository

Now, you need to get that copy onto your computer to work on it.

1.  On your forked repository's page, click the green **\<\> Code** button.
2.  Copy the URL provided (HTTPS is usually the easiest).
3.  Open your terminal or command prompt and run the following command, replacing `URL` with the one you just copied:
    ```bash
    git clone URL
    ```
4.  This downloads the project into a new folder on your computer. Navigate into it:
    ```bash
    cd repository-name
    ```

### Step 3: Create a New Branch

It's a best practice to make your changes on a separate branch. This keeps your changes organized and separate from the main project code (`main` or `master` branch).

1.  Create a new branch with a descriptive name. For example, if you're fixing a typo, you could name it `fix-readme-typo`.
    ```bash
    git checkout -b fix-readme-typo
    ```
    This command both creates and switches you to the new branch.

### Step 4: Make Your Changes 💻

Now for the fun part\! Open the project in your favorite code editor and make your desired changes. You can add new files, edit existing ones, or delete files. Save your work once you're done.

### Step 5: Commit and Push Your Changes

After making changes, you need to save them to your branch's history and send them up to your fork on GitHub.

1.  **Stage your changes:** This tells Git which files you want to include in your next save point (commit). To add all changed files, use:
    ```bash
    git add .
    ```
2.  **Commit your changes:** This saves a snapshot of your staged files. Write a clear, concise commit message describing what you did.
    ```bash
    git commit -m "Fix: Corrected a typo in the README file"
    ```
3.  **Push your changes:** This uploads your committed changes from your computer to your forked repository on GitHub.
    ```bash
    git push origin fix-readme-typo
    ```
    Replace `fix-readme-typo` with the name of your branch.

### Step 6: Open the Pull Request ✨

You're almost there\! The final step is to create the actual pull request on GitHub.

1.  Go to your forked repository on the GitHub website.
2.  You'll likely see a yellow banner with your recently pushed branch and a button that says **"Compare & pull request"**. Click it.
3.  If you don't see the banner, click on the **"Pull requests"** tab and then the green **"New pull request"** button.
4.  On the "Open a pull request" page, make sure the **base repository** is the original project you forked and the **head repository** is your fork and branch.
5.  Give your pull request a clear title and a detailed description of the changes you made and *why* you made them.
6.  Click the **"Create pull request"** button.

Congratulations\! 🎉 You've successfully submitted your first pull request. The project maintainer will now be notified. They can review your changes, ask questions, request modifications, and hopefully, merge your contribution into their project.


## ## Step-by-Step Guide to Making a Pull Request (by Branching)

If you have write access to a repository, creating a branch is the standard and recommended way to make a pull request. Forking is primarily for external contributors who do not have permission to create branches directly on the main project.

The process is simpler and keeps all work consolidated within the main repository.

-----

### The Collaborator Workflow: Branching

This is the method you use when you are a member of the team or have been given write access to a project.

#### Step 1: Clone the Repository

If you don't have it locally, clone the main repository to your computer.

```bash
git clone URL_OF_MAIN_REPO
```

#### Step 2: Create a New Branch

Navigate into the repository's directory and create a new branch for your changes. This keeps your work isolated from the main codebase until it's ready.

```bash
git checkout -b my-new-feature
```

#### Step 3: Make, Commit, and Push Changes

Make your code changes, then commit them with a clear message. When you're ready, push your new branch up to the main repository.

```bash
# Make your changes...
git add .
git commit -m "Add new feature for user profiles"
git push -u origin my-new-feature
```

The `-u` flag sets your local branch to track the remote branch, so in the future, you can just use `git push`.

#### Step 4: Open the Pull Request

Go to the repository on GitHub. You will see a banner prompting you to create a pull request from your recently pushed branch. Click it, fill out the details, and submit your PR for review.

-----

### Branching vs. Forking: When to Use Which

Here’s a simple breakdown to clarify the two workflows.

#### **Branching (You have access ✅)**

  * **Who:** Core team members and collaborators with write permissions.
  * **Why:** It's the most direct workflow. All work happens within one central repository, making it easier to manage and track.
  * **Analogy:** You're a co-author of a book. To suggest a new chapter, you simply start writing it in a new document within the shared project folder.

#### **Forking (You don't have access ❌)**

  * **Who:** External developers, open-source contributors, and anyone without write permissions.
  * **Why:** It allows you to make a personal copy of a project that you don't have access to. You can freely make changes on your copy and then submit them back to the original project as a suggestion (the pull request).
  * **Analogy:** You want to suggest a new chapter for a book you bought at a store. You make a photocopy (**fork**), write your suggested chapter on the copy, and then mail it to the original author for consideration.

---

## Github Desktop-Centric Flow

Almost the whole PR workflow can be done with GitHub Desktop, with a few bits (forking + the review page) happening in your browser.

Here’s the Desktop-centric flow for both cases:


## The Role of Pull Requests in AI-Assisted Programming

In AI-assisted programming, a pull request (PR) acts as the essential human checkpoint for AI-generated code. It ensures that every small, incremental change suggested by an AI is reviewed for quality, security, and alignment with the project's goals before being merged into the main codebase.

-----

## The Core Concept: Your AI's Co-Pilot Needs a Human Editor

Think of an AI coding assistant as a brilliant but junior programmer who is incredibly fast but lacks deep contextual understanding. A pull request is the formal review process where a senior developer (you) checks the AI's work before it goes live. Even if you have direct access to the main repository, forcing all changes—especially AI-generated ones—through a PR process is a cornerstone of modern, safe AI-assisted development.

This process is critical for several reasons:

  * **Quality Assurance ✅:** AI can misunderstand nuances, produce inefficient code, or create solutions that don't fit the project's architecture. The PR is where you catch these errors.
  * **Security and Compliance 🛡️:** AI models are trained on vast datasets and can inadvertently introduce security vulnerabilities or code that violates licenses. Human review is the last line of defense.
  * **Knowledge Sharing 🧠:** When you review a PR, you understand what's being changed. It prevents parts of the codebase from becoming "black boxes" that only the AI understands.
  * **Maintaining Control 🕹️:** It keeps the human developer firmly in control, using AI as a tool to accelerate work rather than blindly accepting its output.

-----

## The AI-Assisted Pull Request Workflow

Spec-driven development means giving the AI a very clear, small, and specific task (the "spec"). You then use the PR process to validate the result. Here’s how it works in practice.

### Step 1: Define the Spec (The Human Prompt)

Before writing any code, clearly define the small, incremental task. Your instruction to the AI is the "specification."

  * **Bad Spec:** "Improve the user login." (Too vague)
  * **Good Spec:** "Add client-side validation to the email input field on the login form. It should check for a valid email format using regex and display the error message 'Please enter a valid email address.' in a red `<span>` tag below the input."

### Step 2: Generate Code with Your AI Assistant

Use your AI programming tool (like GitHub Copilot, Gemini in your IDE, etc.) to generate the code based on your precise spec. You are the navigator, guiding the AI to produce the desired output for this one small change.

### Step 3: Branch, Commit, and Push

Even though the change is small, follow proper Git hygiene.

1.  **Create a descriptive branch:**
    ```bash
    git checkout -b feature/login-email-validation
    ```
2.  **Add and commit the change:** Your commit message should reference the spec.
    ```bash
    git add .
    git commit -m "Feat: Add client-side email validation to login form"
    ```
3.  **Push the branch to the remote repository:**
    ```bash
    git push origin feature/login-email-validation
    ```

### Step 4: Open the Pull Request & Use AI for the Description

Navigate to GitHub to open the PR. Modern tools can now help here, too\!

  * **AI-Generated PR Descriptions:** Many platforms now have AI features that automatically analyze your code changes (the "diff") and write a summary for your PR description. This saves time and ensures clarity for reviewers. Click the "auto-generate" button if available.
  * **Link to the Spec:** In the description, link back to the original task or spec (e.g., a ticket in Jira or a GitHub Issue).

### Step 5: The Human-in-the-Loop Review (The Crucial Part)

This is the most important step. Now, you or a teammate must review the AI's work with a critical eye. Do not just skim it.

Check for the following:

  * **Does it meet the spec?** Does the code do *exactly* what you asked for, with no more and no less?
  * **Is it secure?** Did the AI use a safe regex? Did it introduce any injection vulnerabilities?
  * **Is it efficient?** Is this the most performant way to solve the problem?
  * **Does it fit the codebase?** Does it match the existing coding style, naming conventions, and architectural patterns?
  * **Are there side effects?** Could this small change unintentionally break something else?

### Step 6: Iterate and Merge

If the code isn't perfect, provide feedback, make changes, and push new commits to the branch. The PR will update automatically. Once it passes the human review and any automated checks (like tests or linting), you can confidently **merge** it.

-----

## Best Practices for AI-Assisted PRs

  * **One PR, One Spec:** Keep your pull requests small and focused on a single, atomic change. This makes them easy and fast to review.
  * **Trust, but Verify:** Never blindly accept AI-generated code. Always treat it as a suggestion that requires rigorous human validation.
  * **Review the AI's "Reasoning":** If your AI tool explains *why* it chose a certain approach, read it. It helps you spot flawed logic.
  * **Embrace AI for the Whole Process:** Use AI to help write clear specs, generate code, and summarize your PR descriptions. This maximizes efficiency while maintaining safety.
