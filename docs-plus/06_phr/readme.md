# Module 06 – Prompt History Records (PHR)

> **Turn every AI exchange into a first-class artifact that compounds your learning and accelerates your team.**

## The Problem: Lost Knowledge

Every day, developers have hundreds of AI conversations that produce valuable code, insights, and decisions. But this knowledge disappears into chat history, leaving you to:

- **Reinvent solutions** you already figured out
- **Debug without context** of why code was written that way  
- **Miss patterns** in what prompts actually work
- **Lose traceability** for compliance and code reviews

## The Solution: Prompt History Records

**PHRs capture every meaningful AI exchange as a structured artifact** that lives alongside your code, creating a searchable, reviewable history of your AI-assisted development.

### Core Learning Science Principles

| Principle | How PHRs Apply | Daily Benefit |
|-----------|----------------|---------------|
| **Spaced Repetition** | Revisit PHRs weekly to reinforce successful strategies | Build muscle memory for effective prompting |
| **Metacognition** | Reflect on what worked/didn't work in each exchange | Develop better prompting intuition |
| **Retrieval Practice** | Search PHRs when facing similar problems | Access proven solutions instantly |
| **Interleaving** | Mix different types of prompts (architect/red/green) | Strengthen transfer across contexts |

## 3-File Drop-In Kit

**Copy these 3 files into any project and start capturing AI knowledge immediately:**

| File | Purpose | Location |
|------|---------|----------|
| `create-phr.sh` | Creates numbered PHR files with metadata | `scripts/` |
| `phr.toml` | Universal slash command for all IDEs | `.<YOUR_AI_CODE>/commands/` |
| `phr-template.prompt.md` | Defines PHR structure | `.specify/templates/` (with Spec Kit) or `prompts/` (without) |

## Quick Start (5 Minutes)

### Step 1: Drop in the 3 PHR Files

**With Spec Kit (Recommended):**
```bash
# Copy the PHR kit to your Spec Kit project
mkdir -p scripts .gemini/commands .specify/templates
cp 06_prompt_driven_development/06_phr/kit/create-phr.sh scripts/
cp 06_prompt_driven_development/06_phr/kit/commands/phr.toml .gemini/commands/
cp 06_prompt_driven_development/06_phr/kit/phr-template.prompt.md .specify/templates/
chmod +x scripts/create-phr.sh
```

**Without Spec Kit (Fallback):**
```bash
# Copy the PHR kit to any project
mkdir -p scripts prompts docs/prompts .gemini/commands
cp 06_prompt_driven_development/06_phr/kit/create-phr.sh scripts/
cp 06_prompt_driven_development/06_phr/kit/commands/phr.toml .gemini/commands/
cp 06_prompt_driven_development/06_phr/kit/phr-template.prompt.md prompts/
chmod +x scripts/create-phr.sh
```

**For Other IDEs:**
```bash
# Cursor IDE
cp 06_prompt_driven_development/06_phr/kit/commands/phr.toml .cursor/commands/

# VS Code
cp 06_prompt_driven_development/06_phr/kit/commands/phr.toml .vscode/commands/
```

### Step 2: Use /phr for Everything
```bash
# Instead of separate commands, use /phr for everything:
/phr Create a user authentication system
/phr Fix the login bug in auth.py
/phr Plan the database schema for user management
/phr Write tests for the payment module

# The agent will:
# 1. Execute your request (do the actual work)
# 2. Record the exchange as a PHR automatically
# 3. Provide both the solution AND the learning record
```

### Feature Detection Strategy

**With Spec Kit, the script intelligently finds the right feature:**

1. **Branch Matching**: If you're on branch `001-user-auth`, it looks for `specs/001-user-auth/`
2. **Latest Numbered**: Falls back to the highest numbered feature (e.g., `specs/003-payment/`)
3. **Manual Override**: Use `--feature` to specify exactly which feature

**Examples:**
```bash
# Auto-detects based on current branch
git checkout 001-user-auth
./scripts/create-phr.sh --prompt "Fix login bug"
# → Creates: specs/001-user-auth/prompts/0001-fix-login-bug.red.prompt.md

# Manual override
./scripts/create-phr.sh --feature 002-payment --prompt "Add Stripe integration"
# → Creates: specs/002-payment/prompts/0001-add-stripe-integration.green.prompt.md
```

**That's it!** Every AI exchange is now captured, searchable, and reviewable.

## Daily Workflow

### Morning: Context Loading (2 minutes)

**With Spec Kit:**
```bash
# Read yesterday's PHRs to rehydrate context
ls specs/*/prompts/*.prompt.md | tail -5 | xargs cat
```

**Without Spec Kit:**
```bash
# Read yesterday's PHRs to rehydrate context
ls docs/prompts/*.prompt.md | tail -5 | xargs cat
```

### During Work: Capture Everything (automatic)
```bash
# After any meaningful AI interaction, the agent automatically runs:
# /phr --stage red --title "Fix login bug" --files "auth.py,test_auth.py"
# (No manual intervention needed)
```

### Evening: Reflect & Learn (3 minutes)

**With Spec Kit:**
```bash
# Review today's PHRs and note what worked
grep -r "Reflection:" specs/*/prompts/ | tail -3
```

**Without Spec Kit:**
```bash
# Review today's PHRs and note what worked
grep -r "Reflection:" docs/prompts/ | tail -3
```

## What You Get

### PHR Files Live in Your Project

**With Spec Kit (Recommended):**
```
your-project/
├── .specify/templates/
│   └── phr-template.prompt.md        ← Template
├── specs/
│   └── 001-user-auth/
│       ├── spec.md
│       ├── plan.md
│       └── prompts/                  ← Feature-specific PHRs
│           ├── 0001-plan-auth.architect.prompt.md
│           ├── 0002-implement-login.green.prompt.md
│           └── 0003-fix-bug.red.prompt.md
├── scripts/
│   └── create-phr.sh
└── .gemini/commands/
    └── phr.toml
```

**Without Spec Kit (Fallback):**
```
your-project/
├── prompts/
│   ├── phr-template.prompt.md        ← Template
│   ├── 0001-plan-auth.architect.prompt.md
│   ├── 0002-implement-login.green.prompt.md
│   └── 0003-fix-bug.red.prompt.md
├── scripts/
│   └── create-phr.sh
└── .gemini/commands/
    └── phr.toml
```

### Each PHR Contains
- **What you asked** (the prompt)
- **What AI responded** (the response)  
- **What you built** (files changed, tests run)
- **What you learned** (reflection notes)
- **What's next** (follow-up prompts)

### Searchable Knowledge Base

**With Spec Kit:**
   ```bash
# Find all prompts about authentication
grep -r "auth" specs/*/prompts/

# Find all red-stage prompts (debugging)
find specs -name "*.red.prompt.md"

# Find prompts that touched specific files
grep -r "auth.py" specs/*/prompts/
```

**Without Spec Kit:**
   ```bash
# Find all prompts about authentication
grep -r "auth" docs/prompts/

# Find all red-stage prompts (debugging)
find docs/prompts -name "*.red.prompt.md"

# Find prompts that touched specific files
grep -r "auth.py" docs/prompts/
```

## Why This Works (Learning Science)

### Spaced Repetition
- **Weekly PHR reviews** reinforce successful prompting patterns
- **Searching past PHRs** when facing similar problems builds retrieval strength
- **Pattern recognition** emerges from reviewing your own prompt history

### Metacognition  
- **Reflection prompts** in each PHR force you to think about what worked
- **"Next prompts"** section helps you plan follow-up actions
- **Outcome tracking** shows the connection between prompts and results

### Interleaving
- **Stage tagging** (architect/red/green) mixes different types of thinking
- **Context switching** between planning, coding, and debugging strengthens transfer
- **Cross-domain learning** happens when you apply patterns from one area to another

## Advanced Usage

### Team Knowledge Sharing

**With Spec Kit:**
```bash
# Share PHRs in code reviews
git add specs/*/prompts/ && git commit -m "Add PHR-0001: auth implementation"

# Create team prompt library
mkdir team-prompts && cp specs/*/prompts/*.prompt.md team-prompts/
```

**Without Spec Kit:**
```bash
# Share PHRs in code reviews
git add docs/prompts/ && git commit -m "Add PHR-0001: auth implementation"

# Create team prompt library
mkdir team-prompts && cp docs/prompts/*.prompt.md team-prompts/
```

### Compliance & Auditing

**With Spec Kit:**
```bash
# Generate audit trail
find specs -name "*.prompt.md" -exec grep -l "security\|auth\|payment" {} \;

# Track decision rationale
grep -r "Decision:" specs/*/prompts/
```

**Without Spec Kit:**
```bash
# Generate audit trail
find docs/prompts -name "*.prompt.md" -exec grep -l "security\|auth\|payment" {} \;

# Track decision rationale
grep -r "Decision:" docs/prompts/
```

### Performance Optimization

**With Spec Kit:**
```bash
# Find your most effective prompts
grep -r "✅ Impact:" specs/*/prompts/ | grep -v "recorded for traceability"

# Identify patterns in failed prompts
grep -r "❌" specs/*/prompts/
```

**Without Spec Kit:**
```bash
# Find your most effective prompts
grep -r "✅ Impact:" docs/prompts/ | grep -v "recorded for traceability"

# Identify patterns in failed prompts
grep -r "❌" docs/prompts/
```

## Success Metrics

After 1 week of using PHRs, you should have:
- [ ] 20+ PHRs capturing your AI interactions
- [ ] 3+ successful prompt patterns you can reuse
- [ ] 1+ debugging session where PHRs saved you time
- [ ] Clear understanding of what prompts work for your domain

**The goal:** Turn AI assistance from ad-hoc to systematic, building a compounding knowledge base that makes you more effective every day.

## Troubleshooting

### Common Issues

**"No feature specified and no existing feature directories found"**
- **Cause**: You're in a Spec Kit project but no features exist yet
- **Solution**: Create a feature first using your Spec Kit workflow, or use `--feature general` for standalone mode

**"Template not found"**
- **Cause**: Template file is missing or in wrong location
- **Solution**: Ensure `phr-template.prompt.md` is in `.specify/templates/` (Spec Kit) or `prompts/` (standalone)

**"Feature directory not found"**
- **Cause**: Specified feature doesn't exist in `specs/`
- **Solution**: Check available features with `ls specs/` or create the feature first

**PHRs not being created automatically**
- **Cause**: Agent not configured to use `/phr` command
- **Solution**: Copy `phr.toml` to your IDE's commands directory:
  - **Gemini CLI**: `.gemini/commands/phr.toml`
  - **Cursor IDE**: `.cursor/commands/phr.toml`
  - **VS Code**: `.vscode/commands/phr.toml`

**Command Not Executing (Most Common Issue)**
- **Cause**: AI agent generates command content instead of executing the script
- **Solution**: The universal command now includes explicit execution instructions:
  - Commands must include "You MUST do BOTH - execute the work AND create the PHR record"
  - Commands follow the execution flow: Execute Request → Extract Info → Create PHR → Validate
  - Commands use `$ARGUMENTS` placeholder for user input handling

**Work Not Being Done**
- **Cause**: Agent only records but doesn't execute the actual request
- **Solution**: The command explicitly requires BOTH actions:
  - First: Execute the user's actual request (do the work)
  - Second: Record the exchange as a PHR (capture for learning)

### Getting Help

- Check the script output for specific error messages
- Verify file permissions: `chmod +x scripts/create-phr.sh`
- Test manually: `./scripts/create-phr.sh --help`
