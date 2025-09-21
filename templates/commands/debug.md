---
description: Systematically debug and diagnose problems using root cause analysis methodology.
---

# Debug Issue - Root Cause Analysis

**Problem Description**: $ARGUMENTS

## Systematic Debugging Process

### 1. Reproduce the Issue
- **Get exact steps to reproduce**
  - Document user actions that trigger the problem
  - Note environment conditions (browser, OS, data state)
  - Capture exact error messages or unexpected behaviors
- **Verify reproduction**
  - Can you consistently reproduce the issue?
  - Does it happen in different environments?
- **Document expected vs actual behavior**
  - What should happen?
  - What actually happens?
  - When did this behavior change (if known)?

### 2. Gather Information

```bash
# Check recent changes that might have introduced the issue
git log --oneline -10
git diff HEAD~5 HEAD

# Look for related error patterns in logs
# Search for similar error messages in codebase
```

**Information to collect**:
- Recent commits (especially near the problem area)
- System logs and application logs
- Database state (if applicable)
- External service status
- Environment configuration differences

### 3. Isolate the Problem

**Binary Search Approach**:
- Comment out code sections to narrow down the source
- Test with minimal reproducible example
- Use git bisect if the issue is recent: `git bisect start`

**Strategic Logging**:
- Add logging at key decision points
- Log input values and intermediate states
- Trace execution flow through the problematic path

**Use Context Engineering**:
- Check ai_docs/library_gotchas.md for known issues
- Review similar features that work correctly
- Look for related patterns in the codebase

### 4. Apply Problem-Specific Strategies

#### For Runtime Errors
- **Read the complete stack trace**
  - Identify the exact line and file causing the error
  - Trace back through the call stack to find root cause
- **Verify assumptions about data**
  - Check variable types and values at error point
  - Validate input data meets expected format
- **Test boundary conditions**
  - Empty strings, null values, zero/negative numbers
  - Maximum values, edge cases

#### For Logic Errors
- **Add checkpoint logging**
  - Log intermediate values at each step
  - Verify each calculation produces expected results
- **Test with simple cases first**
  - Use minimal data that should work
  - Gradually increase complexity
- **Validate business logic assumptions**
  - Are the requirements correctly understood?
  - Do the calculations match specifications?

#### For Performance Issues
- **Add timing measurements**
  - Measure execution time of suspected slow operations
  - Profile database queries and external API calls
- **Look for N+1 problems**
  - Check for repeated queries in loops
  - Review database access patterns
- **Examine algorithms**
  - Is the chosen algorithm optimal for the data size?
  - Can operations be cached or batched?

#### For Integration Issues
- **Test external dependencies**
  - Verify services are accessible and responding
  - Check authentication credentials and permissions
- **Validate request/response formats**
  - Compare actual vs expected data structures
  - Test with curl or API clients first
- **Check configuration**
  - Environment variables and config files
  - Network settings and firewall rules

### 5. Root Cause Analysis

**ULTRATHINK**: Before applying standard debugging techniques, deeply analyze:
- What systemic conditions enabled this problem to manifest?
- What assumptions in the original design were flawed or incomplete?
- How do organizational processes contribute to this class of problem?
- What are the second and third-order effects of potential solutions?
- What would a bulletproof solution look like, and why wasn't it built initially?

**Why Analysis** (5 Whys technique):
1. **Why did this specific failure occur?**
2. **Why wasn't this caught earlier?**
3. **Why do similar issues exist elsewhere?**
4. **Why wasn't this prevented by existing safeguards?**
5. **Why don't we have better detection for this class of problems?**

**System Analysis**:
- Is this a symptom of a deeper architectural issue?
- Are there related problems waiting to surface?
- What assumptions were incorrect?

### 6. Implement Fix

**Fix the Root Cause**:
- Address the fundamental issue, not just symptoms
- Consider if the fix might introduce other problems
- Keep the fix minimal and focused (KISS principle)

**Add Defensive Programming**:
- Input validation to prevent similar issues
- Error handling for edge cases discovered
- Logging to help diagnose future related problems

**Follow Spec Kit Constitution**:
- Write tests that fail before implementing the fix
- Ensure fix aligns with architectural principles
- Update documentation if patterns changed

### 7. Verify Resolution

**Confirmation Testing**:
- [ ] Original issue is resolved
- [ ] No regression in related functionality
- [ ] Edge cases identified during debug are handled
- [ ] Fix works across different environments

**Test Coverage**:
- [ ] Add test cases that reproduce the original bug
- [ ] Test the boundary conditions discovered
- [ ] Ensure tests fail without the fix

### 8. Prevention & Learning

**Document Findings**:
```markdown
## Debug Summary
**Issue**: [Brief description]
**Root Cause**: [What actually caused the problem]
**Fix Applied**: [What was changed]
**Prevention**: [How to avoid this class of problem]
**Monitoring**: [How to detect similar issues early]
```

**Update Documentation**:
- Add gotchas to ai_docs/library_gotchas.md if library-related
- Update team knowledge base with lessons learned
- Consider if architectural patterns need adjustment

**Improve Detection**:
- Add monitoring/alerting if appropriate
- Consider if this problem class needs automated testing
- Update code review checklists to catch similar issues

## Debug Report Template

Use this template to document your findings:

```markdown
# Debug Report: [Issue Summary]

## Problem Statement
[Clear description of what went wrong]

## Root Cause
[What actually caused the issue - be specific]

## Investigation Steps
[Key steps taken to isolate the problem]

## Solution Applied
[What was changed to fix the issue]

## Tests Added
[What tests were added to prevent regression]

## Prevention Measures
[What can be done to prevent this class of issue]

## Related Issues
[Any similar problems that might exist]
```

Remember: The goal is not just to fix the immediate problem, but to prevent similar issues and improve the system's overall reliability.