# Your First Spec: Complete Walkthrough

This guide walks you through creating your first real project using Spec-Driven Development, from initial idea to implementation.

## What You'll Build

A **Photo Album Organizer** - a simple web application that lets users organize their photos into albums. It's complex enough to showcase the methodology but simple enough to complete as a first project.

## Prerequisites

- [Spec Kit installed](./installation.md)
- An AI coding agent ([Claude Code](https://www.anthropic.com/claude-code), [Copilot](https://github.com/features/copilot), [Gemini CLI](https://github.com/google-gemini/gemini-cli))
- 30-45 minutes

## Step 1: Initialize Your Project

```bash
# Create a new project directory
cd ~/projects
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init photo-album --ai claude
```

This creates:
- `.specify/` - Configuration and templates
- `specs/` - Where your specifications live
- `.claude/commands/` - AI agent commands for Claude Code

## Step 2: Open in Your AI Agent

Navigate to the project and open it in Claude Code or your AI agent:

```bash
cd photo-album
code .  # Opens in VS Code
```

You should now see commands available:
- `/specify` - Create feature specifications
- `/plan` - Create implementation plans
- `/tasks` - Break down work items
- `/implement` - Execute the implementation

## Step 3: Create Your First Specification

Run the `/specify` command and describe what you want to build:

```
/specify Build a photo album organizer. Users can organize photos into named albums.
Albums show a grid of photo thumbnails. Users can add photos by selecting files from
their computer. Each album can contain any number of photos. Users can create, rename,
and delete albums. When viewing an album, users can see all photos in a grid layout
with basic lightbox functionality to view full-size photos. Photos cannot be deleted
individually once added to an album.
```

**What happens:**
1. Claude Code will create a new branch: `username/proj-XXX.photo-album-organizer`
2. A specification will be generated at `specs/proj-XXX.photo-album-organizer/spec.md`
3. You'll see a structured spec with:
   - User stories
   - Functional requirements
   - Non-functional requirements
   - Success criteria
   - Review & acceptance checklist

## Step 4: Review and Refine the Spec

Read through the generated specification. Ask Claude Code to clarify anything unclear:

```
/specify Please add more detail about the lightbox functionality. What features should
it have? (next/previous buttons? keyboard navigation? close button?)
```

Continue refining until you're satisfied with the requirements.

## Step 5: Validate the Specification

Ask Claude Code to validate the spec against the checklist:

```
/specify Read the Review & Acceptance Checklist and check off each item that passes.
Leave empty if it doesn't.
```

This ensures all key requirements are captured before moving to implementation.

## Step 6: Create Your Implementation Plan

Now that requirements are locked down, create the technical plan:

```
/plan Build this with vanilla JavaScript, HTML, and CSS. Store photos and album data
in the browser's IndexedDB. No backend server needed. Make it work offline. Support
drag-and-drop for adding photos.
```

**What happens:**
1. Claude Code generates a detailed implementation plan
2. Technical documents are created:
   - `plan.md` - Implementation approach and architecture
   - `data-model.md` - Database schema and structure
   - `research.md` - Technology research and rationale
   - `quickstart.md` - Quick reference guide

## Step 7: Review the Implementation Plan

Examine the generated documents:

```bash
# View the plan
cat specs/proj-XXX.photo-album-organizer/plan.md

# View the data model
cat specs/proj-XXX.photo-album-organizer/data-model.md

# Check research findings
cat specs/proj-XXX.photo-album-organizer/research.md
```

Ask Claude Code to audit the plan:

```
/plan Read through the entire plan and identify any missing pieces or potential issues.
Do the technical decisions align with the spec? Are there any dependencies missing?
```

## Step 8: Create Task Breakdown

Break down the work into manageable tasks:

```
/tasks Create a task list for implementing this photo album organizer.
```

This generates `tasks.md` with:
- Ordered list of implementation tasks
- Dependencies between tasks
- Effort estimates
- Clear success criteria for each task

## Step 9: Implement!

Now you're ready to build:

```
implement specs/proj-XXX.photo-album-organizer/plan.md
```

Claude Code will:
1. Create the necessary file structure
2. Implement features based on the plan
3. Run tests to validate functionality
4. Commit changes to your branch

## Step 10: Review and Iterate

After implementation:
1. Test the application in your browser
2. If issues arise, share them with Claude Code
3. Ask for refinements or bug fixes
4. Once satisfied, create a PR to merge to `main`

## What You've Learned

✅ Writing clear specifications
✅ Creating technical implementation plans
✅ Breaking work into actionable tasks
✅ Leveraging AI for structured development
✅ The Spec-Driven Development workflow

## Next Steps

Now that you've completed one project:

- **Read [Guides](/guides/)** to learn workflows for different scenarios
- **Study [Concepts](/concepts/)** to understand the methodology deeply
- **Check [Reference](/reference/)** for command and template details
- **Build more projects!** Each one will feel smoother

## Tips for Success

1. **Be specific in specs** - More detail = better code
2. **Focus on "what" not "how"** - Let the plan handle technical decisions
3. **Validate at each step** - Review specs and plans before implementing
4. **Use atomic commits** - Each commit should be logical and testable
5. **Keep specs versioned** - They're documentation for your team

## Troubleshooting

**"Commands not available?"**
- Ensure you've run `specify init` in the project directory
- Check that your AI agent is Claude Code/Copilot/Gemini CLI

**"Spec seems incomplete?"**
- Use `/specify` again with more details or clarifications
- Ask Claude Code: "What's missing from this spec?"

**"Implementation failing?"**
- Share error messages with Claude Code
- Ask it to debug and fix issues iteratively

## Working with Existing Specs

### Resuming Work on an Existing Spec

If you've already created a spec and branch, **don't run `/specify` again** - it will prompt you about overwriting:

```bash
# DON'T: Run /specify again
/specify user-authentication  # ⚠️ Will prompt about existing spec

# DO: Just checkout the branch and continue
git checkout username/user-authentication

# Your spec is already at:
ls specs/user-authentication/spec.md

# Continue with other commands:
/plan user-authentication
/tasks cap-001
```

### Behavior with Existing Specs

**If spec exists:**
- `/specify` will warn and prompt: "Continue with existing spec? (y/N)"
- Choose **N** to abort (recommended - avoid accidentally overwriting)
- Choose **Y** to continue (keeps existing spec, but overwrites if you proceed)

**If branch exists:**
- `/specify` will automatically checkout the existing branch (no prompt)
- No new branch is created
- You can continue working immediately

### Multi-Developer Scenarios

**Multiple people working on same spec:**

```bash
# Person A:
/specify shared-feature
# Works on specs/shared-feature/spec.md
git push origin username-a/shared-feature

# Person B (later):
git fetch origin
git checkout username-a/shared-feature
# Spec at specs/shared-feature/spec.md is already there
/plan shared-feature  # Continue from here
```

### When to Create New Specs vs. Resume

**Create new spec (`/specify`):**
- Starting a completely new feature
- No spec directory exists yet
- No branch exists yet

**Resume existing (`git checkout` + other commands):**
- Spec already created
- Branch already exists
- Just want to continue work
- Don't want to risk overwriting the spec

**Safe practice:** Always check if spec/branch exists before running `/specify`:
```bash
# Check if spec exists
ls specs/my-feature/spec.md

# Check if branch exists
git branch -a | grep my-feature

# If both exist, just checkout the branch instead of using /specify
```

## Common Questions

**Q: Can I modify the spec after creating a plan?**
A: Yes, but be intentional. Small clarifications are fine. Major changes should flow through the process again.

**Q: How long should a spec be?**
A: As long as needed to be clear. Usually 1-3 pages for simple features, more for complex systems.

**Q: When should I decompose into capabilities?**
A: When your feature is estimated at >1000 LOC total. Break into atomic units (400-1000 LOC each).

**Q: Can I use this for existing codebases?**
A: Yes! `/specify` and `/plan` work great for adding new features to existing projects.

---

**Ready for the next challenge?** Check out the [Guides](/guides/) section for workflows covering complex features, multi-repo projects, and team collaboration.
