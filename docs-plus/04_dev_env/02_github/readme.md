# Git & GitHub for AI-Driven Development

[Git Version Control and Github in Urdu/Hindi Complete Playlist by Zeeshan Hanif](https://www.youtube.com/playlist?list=PLKueo-cldy_HjRnPUL4G3pWHS7FREAizF)

A minimal guide to version control for developers working with AI coding assistants.

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
2. **Use descriptive messages** - "AI added auth" is better than "updates"
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

---

**Need help?** Run `git <command> --help` for any command.