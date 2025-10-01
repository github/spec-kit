---

## PRE-EXECUTION: Check for Implicit PHR

Before executing the main command workflow below, determine if implicit PHR applies:

**Create Implicit PHR After:**
- Spec Kit commands: /constitution, /specify, /plan, /tasks, /implement
- Technical questions producing code/design
- Debugging or fixing errors  
- Code explanations or architecture
- Refactoring or optimization
- Documentation or diagrams
- General feature work

**NEVER Create Implicit PHR:**
- /phr or /adr commands themselves
- Clarifying questions (no artifacts)
- Failed attempts (no output)
- User says "don't record this"

If implicit PHR applies: execute main command, then create PHR in POST-EXECUTION.

---

## EXECUTE MAIN COMMAND WORKFLOW

Execute the main command workflow defined below.

---

## POST-EXECUTION: Create Implicit PHR

After successfully completing main command, if implicit PHR applies:

### Step Z.1: Detect Stage from Work Context

Map work type to stage:

- constitution → Constitution/principles
- spec → Specification
- architect → Planning/design
- green → Implementation
- red → Debugging/fixing
- refactor → Code cleanup
- explainer → Explanations/documentation
- general → General feature work

### Step Z.2: Load and Execute PHR Command Workflow

Find and load the PHR command file using pattern: `.**/commands/phr.md`

Execute the full workflow defined in that file with these parameters:

- `$ARGUMENTS` = The user input from the command above (FULL multiline text)
- Stage = `<detected-stage>` from Step Z.1
- Title = Generate 3-7 word title summarizing work completed
- Mode = Implicit (skip Step 1 "Execute User's Request" - already done)

Follow all instructions in phr.md exactly, including:

- Run create-phr.sh script
- Fill ALL {{PLACEHOLDERS}}
- Show completion report

After PHR creation, if command was /plan:
Show: `📋 Planning complete! Review for architectural decisions? Run /adr`

**On Error:**

- Show: `❌ Implicit PHR failed: {error}`
- Do NOT block command completion
- Suggest: `Run /phr manually`

---

## Error Handling for Implicit Behaviors

**If constitution.md exists but is malformed:**

- Log warning: "⚠️ Constitution exists but couldn't parse implicit rules"
- Continue with command execution (no implicit behaviors)
- Do NOT fail the command

**If create-phr.sh fails during implicit creation:**

- Show error: "❌ Implicit PHR creation failed: {error}"
- Continue (do not block main command completion)
- Suggest manual `/phr` command

**If constitution.md doesn't exist:**

- Skip all implicit behaviors silently
- No warnings (this is normal for projects without constitution)

---

## Design Principles

1. **Opt-In by Design:** Implicit behaviors only active when constitution exists
2. **Non-Blocking:** Errors in implicit actions never block main command
3. **Graceful Degradation:** Missing constitution = explicit commands only
4. **Minimal Friction:** One-line confirmations, no interruptions
5. **Transparent:** Users can see what's happening via brief messages

---

**End of Universal Command Pre-Execution Rules**

---
