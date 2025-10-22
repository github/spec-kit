# Git & GitHub for AI-Driven Development

[Git Version Control and Github in Urdu/Hindi Complete Playlist by Zeeshan Hanif](https://www.youtube.com/playlist?list=PLKueo-cldy_HjRnPUL4G3pWHS7FREAizF)

A minimal guide to version control for developers working with AI coding assistants.

**[Appendix: Natural Language Prompts for AI CLI Tools](#appendix-natural-language-prompts-for-ai-cli-tools)**

## Why Git Matters with AI Tools

When AI tools like Claude Code, or Gemini CLI, generate code, you need Git to:
- **Save your work** before letting AI make changes
- **Undo AI mistakes** quickly
- **Track what changed** when AI modifies files
- **Collaborate** when sharing AI-generated code

---

## Essential Setup (5 minutes)

### 1. Install Git
```bash
# Check if already installed
git --version

# If not installed:
# Mac: brew install git
# Windows: Download from git-scm.com
# Linux: sudo apt install git
```

### 2. Configure Git
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3. Create GitHub Account
Go to [github.com](https://github.com) and sign up (free).

---

## The 5 Commands You'll Use Daily

### Starting a Project

```bash
# Create new repository
git init

# Or clone an existing one
git clone https://github.com/username/repo-name.git
```

### The Basic Workflow

```bash
# 1. Check what changed (do this often!)
git status

# 2. Stage files to save
git add .                    # Add all changes
git add filename.js          # Add specific file

# 3. Save changes with a message
git commit -m "Add login feature"

# 4. Upload to GitHub
git push

# 5. Download updates from GitHub
git pull
```

**Typical AI Development Flow:**
1. `git status` - See current state
2. Let AI generate/modify code
3. `git add .` - Stage AI's changes
4. `git commit -m "Implement feature X with AI"` - Save checkpoint
5. `git push` - Backup to GitHub

---

## Safety Net: Undoing Changes

```bash
# Discard changes in a file (before git add)
git checkout -- filename.js

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - use carefully!
git reset --hard HEAD~1

# See what changed
git diff                     # Show unstaged changes
git log --oneline           # Show commit history
```

**Pro tip:** Before letting AI make major changes, always commit your working code first!

---

## Branches: Your Experimentation Playground

Branches let you try AI-generated solutions without breaking your main code.

```bash
# Create and switch to new branch
git checkout -b feature-name

# Switch between branches
git checkout main
git checkout feature-name

# Merge branch into main
git checkout main
git merge feature-name

# Delete branch after merging
git branch -d feature-name
```

**AI Workflow with Branches:**
1. `git checkout -b ai-experiment` - Create safe space
2. Ask AI to implement feature
3. Test the results
4. If good: merge to main. If bad: delete branch and start over

---

## Pull Requests: Sharing & Reviewing AI Code

Pull Requests (PRs) let you propose changes, get feedback, and merge code safely. Essential for team projects and contributing to open source.

### Why Pull Requests Matter with AI

- **Review AI changes** before they hit production
- **Get teammate feedback** on AI-generated code
- **Document what changed** and why
- **Run tests automatically** before merging
- **Learn from others** reviewing your AI code

### Creating Your First Pull Request

**Step 1: Create a Branch with Changes**
```bash
git checkout -b add-payment-feature
# Let AI help build the feature
git add .
git commit -m "Add Stripe payment integration"
git push -u origin add-payment-feature
```

**Step 2: Open PR on GitHub**
1. Go to your repo on GitHub
2. Click "Compare & pull request" (appears after pushing)
3. Add description:
   ```
   ## What Changed
   - Added Stripe payment processing
   - Created checkout form component
   - Added payment confirmation page
   
   ## AI Assistance
   Used Claude to generate initial Stripe integration code
   
   ## Testing
   - [ ] Tested with test credit card
   - [ ] Verified error handling
   - [ ] Checked mobile responsive design
   ```
4. Click "Create pull request"

**Step 3: Address Review Comments**
```bash
# Make requested changes
git add .
git commit -m "Address review feedback: add error logging"
git push
# PR updates automatically!
```

**Step 4: Merge the PR**
- On GitHub, click "Merge pull request"
- Delete the branch (GitHub offers this)
- Update your local repo:
```bash
git checkout main
git pull
```

### PR Best Practices for AI Development

**Write Clear Descriptions**
```markdown
## Summary
Added user authentication system

## AI Tools Used
- Claude generated initial auth routes
- GitHub Copilot suggested test cases

## Changes
- New: login/signup endpoints
- Modified: user model with password hashing
- Added: JWT token generation

## How to Test
1. Run `npm install` for new dependencies
2. Start server: `npm start`
3. Test login at http://localhost:3000/login
```

**Request Reviews from Teammates**
- Click "Reviewers" on the PR
- Tag people: "Hey @teammate, can you review the auth logic?"
- Be specific: "Please check the error handling in `auth.js`"

**Use Draft PRs for Work in Progress**
- Click dropdown on "Create pull request" → "Create draft pull request"
- Shows you're not ready for review yet
- Great for getting early feedback on AI-generated approaches

### Common PR Workflows

**Individual Developer**
```bash
# Feature branch → PR → Review yourself → Merge
git checkout -b feature
# Code with AI
git push -u origin feature
# Create PR, review changes, merge on GitHub
git checkout main
git pull
```

**Team Project**
```bash
# Feature branch → PR → Team review → Merge
git checkout -b feature
# Code with AI
git push -u origin feature
# Create PR, wait for approval, merge
git checkout main
git pull
```

**Contributing to Open Source**
1. Fork the repo on GitHub
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/repo.git`
3. Create branch: `git checkout -b fix-bug`
4. Make changes (with AI help)
5. Push to your fork: `git push -u origin fix-bug`
6. Create PR from your fork to original repo
7. Respond to maintainer feedback

### Reviewing Others' PRs

**On GitHub:**
1. Go to "Pull requests" tab
2. Click the PR to review
3. Click "Files changed" to see code
4. Add comments by clicking line numbers
5. Submit review: "Approve" or "Request changes"

**Common Review Comments for AI Code:**
- "Can you add error handling here?"
- "This function needs tests"
- "Can we simplify this AI-generated logic?"
- "Add a comment explaining why we did this"

**Pull Locally to Test:**
```bash
# Test someone's PR on your machine
git fetch origin
git checkout pr-branch-name
npm install
npm test
```

### Handling Merge Conflicts

When your PR conflicts with main branch:

```bash
git checkout your-branch
git pull origin main         # Get latest main
# Fix conflicts in your editor
git add .
git commit -m "Resolve merge conflicts"
git push
```

GitHub shows which files conflict. Edit them, look for:
```
<<<<<<< HEAD
your code
=======
their code
>>>>>>> main
```
Keep what you want, delete the markers, save, commit.

### PR Templates

Create `.github/pull_request_template.md` in your repo:

```markdown
## Description
Brief summary of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## AI Assistance
- [ ] AI-generated code (specify tool)
- [ ] AI-reviewed for security
- [ ] Human-verified

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manually tested

## Checklist
- [ ] Code follows project style
- [ ] Comments added for complex logic
- [ ] Documentation updated
```

---

## GitHub: Your Code Backup & Portfolio

### Connecting Local Code to GitHub

```bash
# Create repo on github.com first, then:
git remote add origin https://github.com/username/repo-name.git
git branch -M main
git push -u origin main

# Future pushes are just:
git push
```

### GitHub Authentication

Modern GitHub requires a **Personal Access Token** (not password):

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Save it securely (you won't see it again)
4. Use token as password when pushing

**Better option:** Set up SSH keys ([guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh))

---

## Essential .gitignore

Create a `.gitignore` file to avoid committing junk:

```
# Dependencies
node_modules/
venv/
__pycache__/

# Environment variables (NEVER commit these!)
.env
.env.local

# IDE files
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db

# AI tool caches
.cursor/
.continue/
```

---

## Common AI Development Scenarios

### Scenario 1: AI Made Too Many Changes
```bash
git status                   # See what AI changed
git diff                     # Review specific changes
git checkout -- file.js      # Undo changes to specific file
# Or
git reset --hard            # Undo ALL changes (nuclear option)
```

### Scenario 2: Testing AI's Big Refactor
```bash
git checkout -b ai-refactor  # Create test branch
# Let AI refactor code
git add .
git commit -m "AI refactor attempt"
# Test thoroughly
# If good:
git checkout main
git merge ai-refactor
# If bad:
git checkout main
git branch -D ai-refactor    # Delete the experiment
```

### Scenario 3: Sharing Code with AI Tools
```bash
git add .
git commit -m "Current state before AI changes"
git push                     # Now it's backed up
# Let AI make changes
# If something breaks, you can always roll back
```

### Scenario 4: Getting AI Feature Reviewed
```bash
git checkout -b ai-feature
# Let AI build feature
git add .
git commit -m "AI generated user dashboard"
git push -u origin ai-feature
# Create PR on GitHub for team review
# Address feedback
git add .
git commit -m "Fix issues from PR review"
git push
# Merge on GitHub after approval
```

---

## Quick Reference Card

```
SAVE CHECKPOINT:    git add . → git commit -m "message" → git push
CHECK STATUS:       git status
UNDO CHANGES:       git checkout -- filename
NEW EXPERIMENT:     git checkout -b branch-name
CREATE PR:          git push -u origin branch-name → Open PR on GitHub
SAFE TO MAIN:       git checkout main → git merge branch-name
GET UPDATES:        git pull
TIME TRAVEL:        git log → git reset --hard COMMIT_HASH
```

---

## Pro Tips for AI Development

1. **Commit before major AI changes** - Always have a rollback point
2. **Use descriptive messages with [AI] prefix** - "[AI] prefix followed by tool name and descriptive message" is the standard best practice.
3. **Commit small, commit often** - Easier to identify when AI broke something
4. **Review AI changes** - Use `git diff` before committing
5. **Branch for experiments** - Main branch should always work
6. **Push daily** - GitHub is your backup and portfolio

---

## Next Steps

- Learn `git rebase` for cleaner history (later)
- Explore GitHub Actions for automation (later)
- Use `git blame` to see who/what changed lines (helpful with AI edits)

**Remember:** Git is your safety net. When working with AI, commit early and often. You can always undo, but you can't recover uncommitted changes!

**Need help?** Run `git <command> --help` for any command.


## Appendix: Natural Language Prompts for AI CLI Tools

This appendix provides natural language prompts you can use with AI CLI tools (Claude Code, Gemini CLI, Codex, etc.) to execute Git commands and workflows. These prompts translate the technical commands from the tutorial into conversational requests.

### Setup and Configuration

**Instead of:** `git config --global user.name "Your Name"`
```
Prompt: "Configure my Git username to be John Smith globally"
Prompt: "Set up my Git user email as john@example.com for all repositories"
Prompt: "Check what my current Git username and email are configured as"
```

**Instead of:** `git init`
```
Prompt: "Initialize a new Git repository in the current directory"
Prompt: "Start version control in this folder"
Prompt: "Create a new Git repo here"
```

**Instead of:** `git clone https://github.com/username/repo.git`
```
Prompt: "Clone the repository at https://github.com/facebook/react into my current directory"
Prompt: "Download and set up the project from https://github.com/username/awesome-project"
Prompt: "Get me a local copy of the repository at [URL]"
```

---

### Daily Workflow Commands

**Instead of:** `git status`
```
Prompt: "Show me what files have changed in my working directory"
Prompt: "What's the current state of my Git repository?"
Prompt: "List all modified, staged, and untracked files"
Prompt: "Tell me what I need to commit"
```

**Instead of:** `git add .`
```
Prompt: "Stage all my changes for commit"
Prompt: "Add all modified files to the staging area"
Prompt: "Prepare all changes to be committed"
Prompt: "Stage everything that's changed"
```

**Instead of:** `git add filename.js`
```
Prompt: "Stage only the file called auth.js"
Prompt: "Add just the changes in components/Header.jsx to staging"
Prompt: "Prepare only the utils/validation.py file for commit"
```

**Instead of:** `git commit -m "Add login feature"`
```
Prompt: "Commit my staged changes with the message 'Add user authentication system'"
Prompt: "Create a commit with message 'Fix bug in payment processing'"
Prompt: "Save these changes with the description 'Refactor database queries for performance'"
```

**Instead of:** `git push`
```
Prompt: "Push my commits to the remote repository"
Prompt: "Upload my local commits to GitHub"
Prompt: "Send my committed changes to the remote server"
Prompt: "Sync my local commits to origin"
```

**Instead of:** `git pull`
```
Prompt: "Pull the latest changes from the remote repository"
Prompt: "Download and merge updates from GitHub"
Prompt: "Get the newest code from the remote server"
Prompt: "Sync my local repo with the remote changes"
```

---

### Viewing Changes and History

**Instead of:** `git diff`
```
Prompt: "Show me exactly what changed in my unstaged files"
Prompt: "Display the differences between my working directory and last commit"
Prompt: "What are the specific line-by-line changes I've made?"
```

**Instead of:** `git diff filename.js`
```
Prompt: "Show me what changed in the server.js file specifically"
Prompt: "Display the differences in components/Dashboard.jsx"
```

**Instead of:** `git log --oneline`
```
Prompt: "Show me a brief history of all commits"
Prompt: "List the recent commits in a compact format"
Prompt: "Display commit history with just the hash and message"
```

**Instead of:** `git log`
```
Prompt: "Show me the detailed commit history"
Prompt: "Display all commits with full information including author and date"
Prompt: "Give me the complete log of all changes"
```

---

### Undoing Changes

**Instead of:** `git checkout -- filename.js`
```
Prompt: "Discard my changes to the database.js file"
Prompt: "Revert the config.json file back to the last committed version"
Prompt: "Undo modifications to components/Navbar.jsx"
Prompt: "Restore api/routes.js to its previous state"
```

**Instead of:** `git reset --soft HEAD~1`
```
Prompt: "Undo my last commit but keep the changes staged"
Prompt: "Remove the most recent commit while preserving my work"
Prompt: "Take back my last commit without losing any code"
```

**Instead of:** `git reset --hard HEAD~1`
```
Prompt: "Completely undo my last commit and discard all changes"
Prompt: "Remove the last commit and delete all modifications"
Prompt: "Reset to the previous commit and throw away everything after it"
```

**Instead of:** `git reset --hard`
```
Prompt: "Discard all my uncommitted changes and reset to last commit"
Prompt: "Throw away everything I haven't committed yet"
Prompt: "Completely reset my working directory to the last clean state"
```

**Instead of:** `git reset --hard abc123`
```
Prompt: "Reset my repository to commit hash abc123 and discard everything after"
Prompt: "Time travel to commit abc123 and erase all later commits"
Prompt: "Roll back to the commit with hash abc123"
```

---

### Branch Management

**Instead of:** `git checkout -b feature-name`
```
Prompt: "Create a new branch called user-authentication and switch to it"
Prompt: "Make a new branch named payment-integration and check it out"
Prompt: "Start a new branch for the dashboard-redesign feature"
```

**Instead of:** `git checkout main`
```
Prompt: "Switch to the main branch"
Prompt: "Go back to the main branch"
Prompt: "Check out my main development branch"
```

**Instead of:** `git checkout feature-branch`
```
Prompt: "Switch to the feature-authentication branch"
Prompt: "Check out the branch called bug-fix-login"
Prompt: "Move to the api-refactor branch"
```

**Instead of:** `git branch`
```
Prompt: "List all my local branches"
Prompt: "Show me what branches exist in this repository"
Prompt: "Which branches do I have?"
```

**Instead of:** `git merge feature-branch`
```
Prompt: "Merge the user-authentication branch into my current branch"
Prompt: "Integrate changes from the api-updates branch here"
Prompt: "Combine the bug-fixes branch with main"
```

**Instead of:** `git branch -d feature-branch`
```
Prompt: "Delete the completed-feature branch"
Prompt: "Remove the old-experiment branch locally"
Prompt: "Clean up the merged-feature branch"
```

**Instead of:** `git branch -D feature-branch`
```
Prompt: "Force delete the failed-experiment branch even if not merged"
Prompt: "Remove the abandoned-feature branch regardless of merge status"
```

---

### Working with Pull Requests

**Instead of:** `git push -u origin feature-branch`
```
Prompt: "Push my new-feature branch to GitHub and set up tracking"
Prompt: "Upload the authentication-system branch to origin and track it"
Prompt: "Send the api-refactor branch to remote and set upstream"
```

**Instead of:** `git fetch origin`
```
Prompt: "Download information about all remote branches without merging"
Prompt: "Get the latest remote branch information from GitHub"
Prompt: "Fetch updates from origin without changing my local code"
```

**Instead of:** `git checkout pr-branch-name`
```
Prompt: "Switch to the pull request branch called feature-payment to test it"
Prompt: "Check out the PR branch named bugfix-validation locally"
```

**Instead of:** Handling merge conflicts
```
Prompt: "I have merge conflicts in auth.js - show me the conflict markers and help me understand what's conflicting"
Prompt: "Pull the latest changes from main into my current feature branch"
Prompt: "My PR has conflicts with main - help me resolve them by merging main into my branch"
```

---

### Remote Repository Management

**Instead of:** `git remote add origin https://github.com/username/repo.git`
```
Prompt: "Connect my local repository to the GitHub remote at https://github.com/myuser/myproject.git"
Prompt: "Add a remote called origin pointing to https://github.com/company/app.git"
Prompt: "Link this repo to the remote repository at [URL]"
```

**Instead of:** `git remote -v`
```
Prompt: "Show me what remote repositories are configured"
Prompt: "List all remote connections and their URLs"
Prompt: "What remote servers is this repository connected to?"
```

**Instead of:** `git push --set-upstream origin main`
```
Prompt: "Push the main branch to origin and set it as the default upstream"
Prompt: "Upload main branch to GitHub and configure tracking"
```

---

### Inspecting and Searching

**Instead of:** `git blame filename.js`
```
Prompt: "Show me who last modified each line in the auth.js file"
Prompt: "Display line-by-line authorship for components/Header.jsx"
Prompt: "Who changed what in the database.py file?"
```

**Instead of:** `git show commit-hash`
```
Prompt: "Show me the details of commit abc123"
Prompt: "Display the full changes from commit hash def456"
Prompt: "What did commit abc123 change?"
```

**Instead of:** `git stash`
```
Prompt: "Temporarily save my uncommitted changes so I can switch branches"
Prompt: "Stash my current work without committing"
Prompt: "Set aside my changes for now"
```

**Instead of:** `git stash pop`
```
Prompt: "Restore my most recently stashed changes"
Prompt: "Bring back the work I stashed earlier"
Prompt: "Apply and remove my latest stash"
```

---

### Advanced Workflow Prompts

**Complete Feature Development Workflow:**
```
Prompt: "I want to start working on a new authentication feature. Create a branch called 'add-auth', 
switch to it, and prepare me to start coding."

After coding:
Prompt: "I've finished the authentication feature. Stage all my changes, commit them with message 
'Implement JWT authentication system', and push to GitHub with tracking."

Before merging:
Prompt: "Create a pull request from my add-auth branch to main. Then show me how to merge it after approval."
```

**AI Code Review Workflow:**
```
Prompt: "An AI tool just modified 5 files in my project. Show me what changed, help me review the 
differences, and if it looks good, commit everything with message 'AI-generated improvements to error handling'."

Safety check:
Prompt: "Before I let the AI refactor my code, create a safety commit with message 'Safe checkpoint before 
AI refactoring' and confirm it's pushed to GitHub."
```

**Emergency Rollback:**
```
Prompt: "The AI made breaking changes to my code. Show me the last 10 commits, then help me roll back 
to the commit before the AI changes while keeping my files in the working directory so I can see what went wrong."
```

**Team Collaboration:**
```
Prompt: "My teammate created a PR for a new feature. Help me fetch their branch called 'dashboard-update', 
check it out locally, and run it so I can test before approving."

After review:
Prompt: "The PR looks good. Switch back to main, merge the dashboard-update branch, delete the branch 
locally, and push the merged code to GitHub."
```

**Open Source Contribution:**
```
Prompt: "I want to contribute to the repository at https://github.com/original/project. Help me fork it, 
clone my fork, create a branch called 'fix-typo', and set everything up for making a pull request."
```

---

### Troubleshooting Prompts

**When things go wrong:**
```
Prompt: "I accidentally committed sensitive API keys. Help me remove the last commit, add the keys to 
.gitignore, and tell me what else I need to do about the exposed keys."

Prompt: "My repository is in a weird state and I don't know what's happening. Run diagnostics and 
tell me what's wrong."

Prompt: "I tried to push but got rejected because the remote has changes I don't have. Help me safely 
pull and merge the remote changes."

Prompt: "I made commits on the wrong branch. Show me how to move my last 3 commits to a new branch 
called 'correct-branch'."

Prompt: "I have uncommitted changes but need to switch branches urgently. Stash my changes, switch 
to the main branch, then remind me how to get my changes back later."
```

---

### File Management Prompts

**Instead of:** Creating .gitignore
```
Prompt: "Create a .gitignore file for a Node.js project that excludes node_modules, .env files, 
and common IDE directories."

Prompt: "Generate a Python .gitignore that excludes virtual environments, __pycache__, .env files, 
and .pyc files."

Prompt: "Make a .gitignore for a React project with TypeScript."
```

**Instead of:** Creating PR templates
```
Prompt: "Create a pull request template in .github/pull_request_template.md that includes sections 
for description, type of change, AI assistance used, testing done, and a checklist."
```

---

### Combining Commands in Natural Language

**Complex workflows:**
```
Prompt: "I need to safely test an AI-generated refactoring. Create a new branch called 'ai-refactor-test', 
commit my current work as 'Pre-refactor checkpoint', let me know when it's safe to proceed, and after 
I test, help me decide whether to merge or discard."

Prompt: "My feature is done. Stage everything, commit with message 'Complete user profile feature', 
push to GitHub with tracking on branch 'user-profile', and walk me through creating a PR."

Prompt: "I need to sync my fork with the original repository. Add the original repo as upstream, 
fetch changes, merge them into main, and push to my fork."

Prompt: "Create a comprehensive commit of all my changes with a detailed message listing the three 
main files I modified: auth.js (added OAuth), database.js (optimized queries), and api/routes.js 
(new endpoints). Then push to origin."
```

---

### Tips for Using AI CLI Tools with Git

**Best Practices:**

1. **Be Specific About Context:**
   - Good: "Stage the authentication.js file in the src/utils directory"
   - Less Good: "Stage the auth file"

2. **Ask for Explanations:**
   - "Explain what this will do before executing: merge feature-branch into main"
   - "What are the risks of running git reset --hard?"

3. **Request Safety Checks:**
   - "Before making changes, show me the current status and warn me of any risks"
   - "Is it safe to run this command, or should I commit first?"

4. **Combine with AI Code Generation:**
   - "Generate a .gitignore for my Python Flask project, create it, and stage it for commit"
   - "Write a good commit message describing these changes" (after AI reviews your diff)

5. **Ask for Verification:**
   - "After pushing, verify that my changes appear on GitHub"
   - "Check if my branch is properly tracking the remote"

6. **Request Multi-Step Workflows:**
   - "Guide me through the complete process of creating a feature branch, making changes, 
   and opening a PR with best practices"

**Example Conversations with AI CLI:**

```
You: "I'm about to let you refactor my entire codebase. What should I do first?"
AI: "Let me create a safety checkpoint. I'll commit your current work and push to GitHub..."

You: "The refactoring is done. How do I review what changed?"
AI: "I'll show you the diff, then help you commit if it looks good..."

You: "Something broke. Take me back to before the refactoring."
AI: "I'll reset to your safety checkpoint commit..."
```

---

### Converting Tutorial Scenarios to Prompts

**Scenario 1: AI Made Too Many Changes**
```
Prompt: "Show me everything the AI just changed in my repository"
Prompt: "I don't like what the AI did to server.js - revert just that file"
Prompt: "Actually, revert everything the AI just did - all uncommitted changes"
```

**Scenario 2: Testing AI's Big Refactor**
```
Prompt: "Create a test branch called 'ai-refactor' so I can safely experiment with AI changes"
Prompt: "I've tested the refactor and it's good - merge it back to main and clean up the test branch"
Prompt: "The refactor failed - delete the ai-refactor branch and go back to main"
```

**Scenario 3: Sharing Code with AI Tools**
```
Prompt: "Commit everything as 'Safe state before AI modifications' and push to GitHub"
Prompt: "Now that I have a backup, tell me it's safe to let the AI make big changes"
```

**Scenario 4: Getting AI Feature Reviewed**
```
Prompt: "Create a PR branch called 'ai-dashboard-feature', commit the AI-generated code with 
a detailed message, push it, and tell me the next steps for creating a pull request on GitHub"
```

---

**Remember:** AI CLI tools understand context. You can have conversations:
- "What did my last command do?"
- "Show me a safer way to do that"
- "Walk me through fixing this step by step"
- "What would happen if I ran [command]?"

The more context you provide, the better the AI can help you with Git operations!
---

