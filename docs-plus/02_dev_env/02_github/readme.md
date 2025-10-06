# Complete GitHub Tutorial: WSL, Mac & Linux

## Table of Contents
1. [Introduction to GitHub](#introduction)
2. [Setting Up Git](#setup)
3. [GitHub Account Setup](#account)
4. [Basic Git Concepts](#concepts)
5. [Essential Git Commands](#commands)
6. [Working with GitHub Repositories](#repositories)
7. [Branching and Merging](#branching)
8. [Pull Requests](#pull-requests)
9. [Collaboration Workflows](#collaboration)
10. [Advanced GitHub Features](#advanced)
11. [Best Practices](#best-practices)
12. [Common Issues and Solutions](#troubleshooting)

---

## Introduction to GitHub {#introduction}

### What is Git?
Git is a distributed version control system that tracks changes in your code. It allows you to:
- Save snapshots of your project at any point
- Collaborate with others without conflicts
- Experiment safely in separate branches
- Revert to previous versions if needed

### What is GitHub?
GitHub is a cloud-based platform for hosting Git repositories. It adds:
- Remote backup of your code
- Collaboration tools (pull requests, issues, project boards)
- Code review capabilities
- CI/CD integration
- Documentation hosting (GitHub Pages)
- Social coding features

### Why Use GitHub?
- **Portfolio**: Showcase your projects to employers
- **Collaboration**: Work with teams globally
- **Open Source**: Contribute to public projects
- **Backup**: Never lose your code
- **Learning**: Study code from experts

---

## Setting Up Git {#setup}

### Windows (WSL)

**Install Git:**
```bash
# Update package list
sudo apt update

# Install Git
sudo apt install git -y

# Verify installation
git --version
```

**Configure Git:**
```bash
# Set your name (appears in commits)
git config --global user.name "Your Name"

# Set your email (must match GitHub email)
git config --global user.email "your.email@example.com"

# Set default branch name to main
git config --global init.defaultBranch main

# Set default text editor
git config --global core.editor "vim"
# Or use nano: git config --global core.editor "nano"

# View all settings
git config --list
```

### macOS

**Install Git:**

Git often comes pre-installed on macOS. Check first:
```bash
git --version
```

If not installed, you'll be prompted to install Xcode Command Line Tools. Or install via Homebrew:
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Git
brew install git

# Verify
git --version
```

**Configure Git:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main
git config --global core.editor "vim"
```

### Linux

**Install Git:**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install git -y
```

**Fedora/RHEL/CentOS:**
```bash
sudo dnf install git -y
# Or older systems:
sudo yum install git -y
```

**Arch Linux:**
```bash
sudo pacman -S git
```

**Verify:**
```bash
git --version
```

**Configure Git:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main
git config --global core.editor "vim"
```

---

## GitHub Account Setup {#account}

### Creating a GitHub Account

1. Go to [github.com](https://github.com)
2. Click "Sign up"
3. Follow the registration process
4. Verify your email address

### SSH Key Setup (Recommended)

SSH keys provide secure, password-less authentication to GitHub.

**Generate SSH Key:**
```bash
# Generate a new SSH key (use your GitHub email)
ssh-keygen -t ed25519 -C "your.email@example.com"

# Press Enter to accept default location (~/.ssh/id_ed25519)
# Enter a passphrase (optional but recommended)
```

**Start SSH Agent:**
```bash
# Start the ssh-agent in the background
eval "$(ssh-agent -s)"

# Add your SSH private key to the ssh-agent
ssh-add ~/.ssh/id_ed25519
```

**Add SSH Key to GitHub:**
```bash
# Display your public key
cat ~/.ssh/id_ed25519.pub

# Copy the output (starts with ssh-ed25519)
```

1. Go to GitHub.com → Settings (click your profile picture)
2. Click "SSH and GPG keys" in the left sidebar
3. Click "New SSH key"
4. Give it a title (e.g., "WSL Laptop")
5. Paste your public key
6. Click "Add SSH key"

**Test Connection:**
```bash
ssh -T git@github.com

# You should see:
# Hi username! You've successfully authenticated...
```

### Personal Access Token (Alternative)

If you prefer HTTPS over SSH:

1. GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token
3. Select scopes: `repo`, `workflow`, `gist`
4. Copy the token (you won't see it again!)
5. Use this token as your password when pushing

---

## Basic Git Concepts {#concepts}

### Repository (Repo)
A folder tracked by Git, containing your project files and their history.

### Commit
A snapshot of your project at a specific point in time. Like a save point in a game.

### Branch
An independent line of development. Like parallel universes for your code.

### Remote
A version of your repository hosted on GitHub (or another server).

### Clone
Creating a local copy of a remote repository.

### Push
Sending your local commits to a remote repository.

### Pull
Downloading changes from a remote repository to your local copy.

### Merge
Combining changes from different branches.

### Pull Request (PR)
A request to merge your changes into another branch (GitHub feature, not Git).

---

## Essential Git Commands {#commands}

### Starting a Repository

**Create a New Repository:**
```bash
# Create project directory
mkdir my-project
cd my-project

# Initialize Git repository
git init

# Create a README
echo "# My Project" > README.md

# Check status
git status
```

**Clone an Existing Repository:**
```bash
# Clone via SSH (recommended)
git clone git@github.com:username/repository.git

# Clone via HTTPS
git clone https://github.com/username/repository.git

# Clone into specific directory
git clone git@github.com:username/repo.git my-folder

# Clone specific branch
git clone -b branch-name git@github.com:username/repo.git
```

### Basic Workflow

**Check Status:**
```bash
# See which files are modified, staged, or untracked
git status

# Short format
git status -s
```

**Stage Changes:**
```bash
# Stage a specific file
git add filename.txt

# Stage all changes in current directory
git add .

# Stage all changes in repository
git add -A

# Stage specific file types
git add *.py

# Interactively stage changes
git add -p
```

**Commit Changes:**
```bash
# Commit with message
git commit -m "Add user authentication feature"

# Commit with detailed message
git commit -m "Add login functionality" -m "Implemented JWT-based authentication with refresh tokens"

# Stage and commit in one step
git commit -am "Fix bug in payment processing"

# Amend last commit (add forgotten files or fix message)
git commit --amend
```

**View History:**
```bash
# View commit history
git log

# Compact view
git log --oneline

# Graphical view with branches
git log --oneline --graph --all

# Last n commits
git log -n 5

# Commits by author
git log --author="John Doe"

# Commits in date range
git log --since="2024-01-01" --until="2024-12-31"

# Changes in each commit
git log -p
```

**View Changes:**
```bash
# See unstaged changes
git diff

# See staged changes
git diff --staged

# Compare branches
git diff main..feature-branch

# Changes in specific file
git diff filename.txt
```

---

## Working with GitHub Repositories {#repositories}

### Creating a Repository on GitHub

**Via Web Interface:**
1. Click the "+" icon → "New repository"
2. Enter repository name
3. Add description (optional)
4. Choose public or private
5. Initialize with README (optional)
6. Add .gitignore (select language)
7. Choose license (optional)
8. Click "Create repository"

**Connect Local Repository to GitHub:**
```bash
# After creating repo on GitHub, connect it to local repo
git remote add origin git@github.com:username/repository.git

# Verify remote
git remote -v

# Push initial commit
git branch -M main
git push -u origin main
```

### Pushing Changes

```bash
# Push to remote repository
git push

# Push to specific remote and branch
git push origin main

# Push and set upstream (first time)
git push -u origin main

# Push all branches
git push --all

# Push tags
git push --tags

# Force push (use with caution!)
git push --force
```

### Pulling Changes

```bash
# Fetch and merge changes from remote
git pull

# Pull from specific remote and branch
git pull origin main

# Pull with rebase instead of merge
git pull --rebase

# Fetch without merging
git fetch

# Fetch all remotes
git fetch --all
```

### Syncing Your Fork

```bash
# Add upstream remote (original repository)
git remote add upstream git@github.com:original-owner/repository.git

# Fetch upstream changes
git fetch upstream

# Merge upstream changes into your main branch
git checkout main
git merge upstream/main

# Push updates to your fork
git push origin main
```

---

## Branching and Merging {#branching}

### Why Use Branches?

Branches allow you to:
- Develop features in isolation
- Experiment without breaking main code
- Work on multiple features simultaneously
- Collaborate without conflicts

### Branch Commands

**Create and Switch Branches:**
```bash
# Create new branch
git branch feature-login

# Switch to branch
git checkout feature-login

# Create and switch in one command
git checkout -b feature-login

# Modern syntax (Git 2.23+)
git switch feature-login
git switch -c feature-login  # Create and switch

# List branches
git branch                    # Local branches
git branch -r                 # Remote branches
git branch -a                 # All branches

# Rename branch
git branch -m old-name new-name

# Delete branch
git branch -d feature-login   # Safe delete (only if merged)
git branch -D feature-login   # Force delete
```

**Working with Branches:**
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature-payment

# Make changes and commit
git add .
git commit -m "Add payment processing"

# Push branch to GitHub
git push -u origin feature-payment

# Switch back to main
git checkout main

# View which branch you're on
git branch --show-current
```

### Merging Branches

**Local Merge:**
```bash
# Switch to branch you want to merge INTO
git checkout main

# Merge feature branch
git merge feature-login

# If there are conflicts, Git will notify you
# Resolve conflicts, then:
git add .
git commit -m "Merge feature-login into main"

# Push merged changes
git push origin main

# Delete merged branch
git branch -d feature-login
git push origin --delete feature-login
```

**Merge Strategies:**
```bash
# Fast-forward merge (default when possible)
git merge feature-branch

# Create merge commit even if fast-forward possible
git merge --no-ff feature-branch

# Squash all commits into one
git merge --squash feature-branch
git commit -m "Add entire feature"
```

### Resolving Merge Conflicts

When Git can't automatically merge changes:

```bash
# After git merge shows conflicts
git status  # See conflicted files

# Open conflicted file - you'll see:
<<<<<<< HEAD
Your changes
=======
Their changes
>>>>>>> feature-branch

# Edit file to resolve conflict
# Remove conflict markers
# Keep what you want

# Stage resolved files
git add conflicted-file.txt

# Complete merge
git commit -m "Resolve merge conflicts"
```

### Rebasing (Alternative to Merging)

Rebasing rewrites history to create a linear progression:

```bash
# From feature branch
git checkout feature-branch
git rebase main

# If conflicts occur, resolve them
git add resolved-file.txt
git rebase --continue

# Skip a commit if needed
git rebase --skip

# Abort rebase
git rebase --abort

# Push rebased branch (requires force)
git push --force-with-lease origin feature-branch
```

**When to Rebase vs Merge:**
- **Rebase**: For cleaning up your feature branch before merging
- **Merge**: For combining branches, especially on shared branches
- **Never rebase public/shared branches!**

---

## Pull Requests {#pull-requests}

Pull Requests (PRs) are GitHub's way of proposing changes and conducting code reviews.

### Creating a Pull Request

**Step 1: Create Feature Branch**
```bash
# Create and switch to feature branch
git checkout -b feature-add-search

# Make your changes
# Edit files...

# Stage and commit
git add .
git commit -m "Add search functionality with filters"

# Push to GitHub
git push -u origin feature-add-search
```

**Step 2: Open PR on GitHub**

1. Go to your repository on GitHub
2. Click "Pull requests" → "New pull request"
3. Select base branch (usually `main`) and compare branch (`feature-add-search`)
4. Review the changes
5. Click "Create pull request"
6. Add title and description:
   - **Title**: Clear, concise summary
   - **Description**: Explain what changed and why
   - Link related issues (#123)
   - Add screenshots if UI changes
7. Assign reviewers
8. Add labels (bug, enhancement, etc.)
9. Click "Create pull request"

### Pull Request Description Template

```markdown
## Description
Brief summary of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123

## Changes Made
- Added search bar to navigation
- Implemented filter by category
- Added unit tests for search function

## Testing
- [ ] Unit tests pass
- [ ] Manual testing completed
- [ ] Tested on multiple browsers

## Screenshots (if applicable)
[Add screenshots here]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

### Reviewing Pull Requests

**As a Reviewer:**

```bash
# Fetch PR branch to test locally
git fetch origin pull/42/head:pr-42
git checkout pr-42

# Test changes
# Run the code, check functionality

# Return to main
git checkout main
```

**On GitHub:**
1. Go to Pull Requests → Select PR
2. Review "Files changed" tab
3. Click line numbers to add comments
4. Use "Add single comment" or "Start a review"
5. Finish review:
   - **Comment**: General feedback
   - **Approve**: Looks good to merge
   - **Request changes**: Needs work

**Review Comments Best Practices:**
```markdown
# Specific and actionable
❌ "This could be better"
✅ "Consider extracting this logic into a separate function for reusability"

# Explain the "why"
❌ "Use a dict here"
✅ "A dictionary would be more efficient here (O(1) lookup vs O(n))"

# Be respectful
❌ "This is wrong"
✅ "I think there might be an edge case here when input is empty"

# Use suggestions feature
```suggestion
def calculate_total(items):
    return sum(item.price for item in items)
```
```

### Updating a Pull Request

**After receiving feedback:**

```bash
# Make changes on your feature branch
git checkout feature-add-search

# Edit files based on feedback
# ...

# Commit changes
git add .
git commit -m "Address review feedback: improve error handling"

# Push updates
git push origin feature-add-search

# The PR automatically updates!
```

**Squashing Commits (Clean History):**
```bash
# Interactive rebase to squash commits
git rebase -i HEAD~3  # Last 3 commits

# In editor, change 'pick' to 'squash' (or 's') for commits to combine
# Save and exit

# Edit commit message
# Save and exit

# Force push (only on your feature branch!)
git push --force-with-lease origin feature-add-search
```

### Merging a Pull Request

**On GitHub (Recommended):**

1. Ensure all checks pass (CI/CD, reviews)
2. Resolve any merge conflicts
3. Click "Merge pull request"
4. Choose merge type:
   - **Create a merge commit**: Preserves all commits
   - **Squash and merge**: Combines all commits into one
   - **Rebase and merge**: Applies commits individually
5. Confirm merge
6. Delete branch (GitHub will prompt)

**Via Command Line:**
```bash
# Checkout main
git checkout main

# Pull latest changes
git pull origin main

# Merge feature branch
git merge --no-ff feature-add-search

# Push to GitHub
git push origin main

# Delete remote branch
git push origin --delete feature-add-search

# Delete local branch
git branch -d feature-add-search
```

### Draft Pull Requests

Use draft PRs for work-in-progress:

```bash
# Create PR as normal, but click "Create draft pull request"
# Or convert existing PR to draft

# When ready:
# Click "Ready for review" on GitHub
```

---

## Collaboration Workflows {#collaboration}

### Forking Workflow (Open Source)

**1. Fork Repository:**
- Go to repository on GitHub
- Click "Fork" button
- Creates copy under your account

**2. Clone Your Fork:**
```bash
git clone git@github.com:your-username/repository.git
cd repository

# Add upstream remote
git remote add upstream git@github.com:original-owner/repository.git

# Verify remotes
git remote -v
```

**3. Create Feature Branch:**
```bash
# Update main from upstream
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature-improvement

# Make changes
# ...

# Commit
git add .
git commit -m "Add improvement"

# Push to your fork
git push origin feature-improvement
```

**4. Create Pull Request:**
- Go to your fork on GitHub
- Click "Contribute" → "Open pull request"
- Base repository: original repo's main
- Head repository: your fork's feature branch
- Create PR

**5. Keep Fork Updated:**
```bash
# Fetch upstream changes
git fetch upstream

# Merge into main
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

### Feature Branch Workflow (Teams)

**Daily Workflow:**
```bash
# Morning: Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature-user-profile

# Work on feature
# Make commits throughout the day

# End of day: Push work
git push -u origin feature-user-profile

# Next morning: Update from main
git checkout main
git pull origin main
git checkout feature-user-profile
git merge main  # Or rebase: git rebase main

# Continue work
```

### Gitflow Workflow (Releases)

Branches:
- `main`: Production code
- `develop`: Development integration
- `feature/*`: New features
- `release/*`: Release preparation
- `hotfix/*`: Emergency fixes

```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/new-api

# Work and commit
# ...

# Merge back to develop
git checkout develop
git merge --no-ff feature/new-api
git push origin develop
git branch -d feature/new-api

# Create release
git checkout develop
git pull origin develop
git checkout -b release/1.2.0

# Finalize release
# Update version numbers, docs

# Merge to main
git checkout main
git merge --no-ff release/1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin main --tags

# Merge back to develop
git checkout develop
git merge --no-ff release/1.2.0
git push origin develop
git branch -d release/1.2.0
```

---

## Advanced GitHub Features {#advanced}

### GitHub Issues

**Creating an Issue:**
1. Repository → Issues → New issue
2. Add title and description
3. Assign to team member
4. Add labels (bug, enhancement, question)
5. Link to project or milestone
6. Submit issue

**Linking Issues to PRs:**
```markdown
# In PR description
Closes #42
Fixes #123
Resolves #456

# In commit message
git commit -m "Fix login bug

Closes #42"
```

### GitHub Actions (CI/CD)

Create `.github/workflows/test.yml`:

```yaml
name: Run Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest
    
    - name: Run linter
      run: |
        flake8 .
```

### GitHub Projects

Organize work with Kanban boards:
1. Repository → Projects → New project
2. Choose template (Kanban, etc.)
3. Add issues and PRs as cards
4. Drag between columns (Todo, In Progress, Done)

### Protecting Branches

**Settings → Branches → Add rule:**
- Require pull request reviews
- Require status checks (CI)
- Require signed commits
- Include administrators
- Restrict who can push

### .gitignore

Create `.gitignore` to exclude files:

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/

# IDEs
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Secrets
.env
*.key
*.pem

# AI/ML
*.h5
*.pkl
models/
data/raw/

# Logs
*.log
logs/
```

### Git Tags

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# List tags
git tag

# Push tags
git push origin v1.0.0
git push --tags  # All tags

# Delete tag
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Checkout tag
git checkout v1.0.0
```

---

## Best Practices {#best-practices}

### Commit Messages

**Format:**
```
Short summary (50 chars or less)

More detailed explanation (wrap at 72 chars).
Explain the problem this commit solves and why
you chose this solution.

- Bullet points are fine
- Use present tense ("Add feature" not "Added")
- Reference issues: Fixes #123
```

**Good Examples:**
```
Add user authentication with JWT

Implement JWT-based authentication to replace
session-based auth. This improves scalability
and enables mobile app support.

- Add login endpoint
- Implement token refresh
- Add middleware for protected routes

Closes #45
```

**Conventional Commits:**
```
feat: add search functionality
fix: resolve payment processing bug
docs: update README with installation steps
style: format code with black
refactor: extract validation logic to utils
test: add unit tests for auth module
chore: update dependencies
```

### Branching Strategy

```bash
# Branch naming conventions
feature/user-authentication
bugfix/payment-error
hotfix/critical-security-patch
release/v1.2.0
docs/api-documentation
```

### Code Review Guidelines

**As Author:**
- Keep PRs small (< 400 lines when possible)
- Write clear description
- Self-review before requesting review
- Respond to feedback promptly
- Don't take criticism personally

**As Reviewer:**
- Review within 24 hours
- Be constructive and specific
- Ask questions instead of demanding
- Approve when it's "good enough"
- Focus on: correctness, maintainability, performance

### Commit Hygiene

```bash
# Commit often, push less frequently
git add specific-file.py
git commit -m "Add validation"

git add another-file.py
git commit -m "Add tests"

# Clean up before pushing
git rebase -i HEAD~5  # Interactive rebase
# Squash or reorder commits

# Then push
git push origin feature-branch
```

---

## Common Issues and Solutions {#troubleshooting}

### "Fatal: Not a git repository"

```bash
# You're not in a Git repository
# Initialize one:
git init

# Or navigate to existing repository:
cd /path/to/repository
```

### "Permission denied (publickey)"

```bash
# SSH key not configured
# Generate and add SSH key (see setup section)

# Or use HTTPS instead:
git remote set-url origin https://github.com/username/repo.git
```

### "Merge conflict"

```bash
# View conflicted files
git status

# Edit conflicted files
# Remove <<<<<<, =======, >>>>>> markers
# Keep desired changes

# Stage resolved files
git add .

# Complete merge
git commit
```

### "Your branch is ahead/behind"

```bash
# Ahead: You have local commits not pushed
git push origin main

# Behind: Remote has commits you don't have
git pull origin main

# Diverged: Both have unique commits
git pull --rebase origin main
# Or merge instead of rebase:
git pull origin main
```

### Undo Last Commit (Keep Changes)

```bash
# Undo commit, keep changes staged
git reset --soft HEAD~1

# Undo commit, keep changes unstaged
git reset HEAD~1

# Undo commit, discard changes (dangerous!)
git reset --hard HEAD~1
```

### Undo Changes to File

```bash
# Discard unstaged changes
git checkout -- filename.txt

# Modern syntax
git restore filename.txt

# Discard all unstaged changes
git checkout -- .
git restore .
```

### Accidentally Committed to Wrong Branch

```bash
# On wrong-branch
git log  # Note the commit hash

# Switch to correct branch
git checkout correct-branch

# Apply commit
git cherry-pick <commit-hash>

# Return to wrong branch and remove commit
git checkout wrong-branch
git reset --hard HEAD~1
```

### Remove Sensitive Data

```bash
# If not yet pushed
git reset HEAD~1
# Edit file, remove sensitive data
git add .
git commit

# If already pushed (requires force push)
# Remove from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/sensitive-file" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (warning: rewrites history)
git push --force --all

# Better: Use BFG Repo-Cleaner for large repos
# https://rtyley.github.io/bfg-repo-cleaner/
```

### Large Files

```bash
# Git doesn't handle large files well (>50MB)
# Use Git LFS (Large File Storage)

# Install Git LFS
git lfs install

# Track large files
git lfs track "*.psd"
git lfs track "*.zip"
git lfs track "models/*.h5"

# Commit .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS"

# Use normally
git add large-file.zip
git commit -m "Add large file"
git push
```

---

## Quick Reference Cheat Sheet

### Setup
```bash
git config --global user.name "Name"
git config --global user.email "email@example.com"
```

### Create
```bash
git init
git clone <url>
```

### Changes
```bash
git status
git diff
git add <file>
git add .
git commit -m "message"
```

### Branching
```bash
git branch
git branch <name>
git checkout <branch>
git checkout -b <branch>
git merge <branch>
git branch -d <branch>
```

### Remote
```bash
git remote add origin <url>
git push -u origin main
git push
git pull
git fetch
```

### Undo
```bash
git checkout -- <file>
git reset HEAD <file>
git reset --soft HEAD~1
git revert <commit>
```

### Information
```bash
git log
git log --oneline
git show <commit>
git blame <file>
```

---

## Practice Exercises

### Exercise 1: Create Your First Repository

```bash
# 1. Create directory
mkdir my-first-repo
cd my-first-repo

# 2. Initialize Git
git init

# 3. Create README
echo "# My First Repository" > README.md
echo "Learning Git and GitHub!" >> README.md

# 4. Make first commit
git add README.md
git commit -m "Initial commit: Add README"

# 5. Create GitHub repository
# (Do this on GitHub.com)

# 6. Connect and push
git remote add origin git@github.com:your-username/my-first-repo.git
git branch -M main
git push -u origin main
```

### Exercise 2: Feature Branch Workflow

```bash
# 1. Create feature branch
git checkout -b feature-add-license

# 2. Create LICENSE file
echo "MIT License" > LICENSE
echo "Copyright (c) 2025" >> LICENSE

# 3. Commit
git add LICENSE
git commit -m "Add MIT license"

# 4. Push and create PR
git push -u origin feature-add-license

# 5. On GitHub: Create pull request

# 6. Merge PR on GitHub

# 7. Update local main
git checkout main
git pull origin main

# 8. Delete feature branch
git branch -d feature-add-license
```

### Exercise 3: Collaboration

```bash
# 1. Fork a public repository on GitHub

# 2. Clone your fork
git clone git@github.com:your-username/forked-repo.git
cd forked-repo

# 3. Add upstream
git remote add upstream git@github.com:original-owner/original-repo.git

# 4. Create feature branch
git checkout -b improve-documentation

# 5. Make improvements to README
# Edit README.md

# 6. Commit changes
git add README.md
git commit -m "docs: improve installation instructions"

# 7. Push to your fork
git push origin improve-documentation

# 8. Create pull request to original repo
```

---

## Additional Resources

### Official Documentation
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com)
- [GitHub Skills](https://skills.github.com)

### Interactive Learning
- [Learn Git Branching](https://learngitbranching.js.org)
- [GitHub Learning Lab](https://lab.github.com)

### GUI Clients (Optional)
- GitHub Desktop
- GitKraken
- SourceTree
- VS Code built-in Git

### Books
- Pro Git (free online)
- Git Pocket Guide

---

## Conclusion

Git and GitHub are essential tools for modern software development. By mastering these tools, you'll:
- Collaborate effectively with teams worldwide
- Maintain a portfolio of your work
- Contribute to open source projects
- Never lose your code
- Work confidently with version control

**Key Takeaways:**
1. Commit early and often
2. Write clear commit messages
3. Use branches for features
4. Create pull requests for code review
5. Keep your main branch stable
6. Sync regularly with remote