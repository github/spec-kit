---
description: Sync selected user stories or tasks to Azure DevOps
scripts:
  sh: scripts/bash/create-ado-workitems.sh
  ps: scripts/powershell/create-ado-workitems.ps1
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Prerequisites

**CRITICAL**: Before executing this command, verify:

1. Azure CLI is installed (`az --version`)
2. Azure DevOps extension is installed (`az extension list | grep azure-devops`)
3. User has authenticated with Azure CLI (`az account show`)

If Azure CLI is not installed, show error and installation link: <https://aka.ms/installazurecliwindows>
If DevOps extension is missing, auto-install it: `az extension add --name azure-devops`
If not authenticated, prompt: `az login --use-device-code`

## Outline

**CRITICAL WORKFLOW - Follow these steps IN ORDER:**

This command syncs user stories from spec.md OR tasks from tasks.md to Azure DevOps as work items using Azure CLI with OAuth authentication (no PAT tokens required).

**Two modes:**

1. **User Story Mode** (default): Syncs user stories from spec.md as User Story work items
2. **Task Mode** (with `-FromTasks` flag): Syncs tasks from tasks.md as Task work items linked to parent User Stories

### Step 1: Collect Azure DevOps Configuration (ASK USER IN CHAT FIRST)

**DO THIS BEFORE ANYTHING ELSE**: Ask the user for these configuration details **in the chat**:

1. **Check for saved configuration** first:
   - Look for `~/.speckit/ado-config.json` (Windows: `C:\Users\<username>\.speckit\ado-config.json`)
   - If file exists, read and display the saved values

2. **If configuration exists**, ask user:

   ```text
   I found your saved Azure DevOps configuration:
   - Organization: <saved-org>
   - Project: <saved-project>
   - Area Path: <saved-area-path>
   
   Would you like to use these settings? (yes/no)
   ```

3. **If no configuration OR user says no**, ask these questions **ONE BY ONE** in chat:

   ```text
   What is your Azure DevOps Organization name?
   (e.g., "MSFTDEVICES" from https://dev.azure.com/MSFTDEVICES)
   ```

   **Wait for response, then ask:**

   ```text
   What is your Azure DevOps Project name?
   (e.g., "Devices")
   ```

   **Wait for response, then ask:**

   ```text
   What is your Area Path?
   (e.g., "Devices\SW\ASPX\CE\Portals and Services")
   ```

4. **Store the responses** as variables for later use

### Step 2: Locate and Parse Spec File

**If User Story Mode (default):**

1. Find the current feature directory (look for nearest `spec.md` in workspace)
2. Read `spec.md` and extract all user stories using pattern:

   ```markdown
   ### User Story <N> - <Title> (Priority: P<N>)
   ```

3. **Display found stories in chat** like this:

   ```text
   Found 5 user stories in spec.md:
   
   [1] User Story 1 - User Authentication (P1)
   [2] User Story 2 - Profile Management (P1)
   [3] User Story 3 - Password Reset (P2)
   [4] User Story 4 - Session Management (P2)
   [5] User Story 5 - Account Deletion (P3)
   ```

**If Task Mode (with `-FromTasks` argument):**

1. Find the current feature directory (look for nearest `tasks.md` in workspace)
2. Read `tasks.md` and extract all tasks using pattern:

   ```markdown
   - [ ] T001 [P] [US1] Task description
   ```

3. **Display found tasks grouped by User Story** in chat:

   ```text
   Found 25 tasks in tasks.md:
   
   User Story 1 (8 tasks):
     [1] T001 - Setup authentication service
     [2] T002 - Create login endpoint
     [3] T003 - Implement password validation
     ...
   
   User Story 2 (12 tasks):
     [8] T010 - Design user profile schema
     [9] T011 - Create profile API
     ...
   
   No parent (5 unlinked tasks):
     [20] T050 - Update documentation
     ...
   ```

### Step 3: Ask User Which Items to Sync

**CRITICAL: You MUST ask the user which items to sync. DO NOT skip this step!**

**If User Story Mode:**

**Ask user in chat**:

```text
Which user stories would you like to sync to Azure DevOps?

Options:
  • all - Sync all user stories
  • 1,2,3 - Sync specific stories (comma-separated)
  • 1-5 - Sync a range of stories

Your selection:
```

**Wait for user response**, then parse selection:

- "all" → select all stories
- "1,3,5" → select stories 1, 3, and 5
- "1-5" → select stories 1 through 5
- Empty/invalid → prompt again

**If Task Mode (-FromTasks):**

**Ask user in chat**:

```text
Which tasks would you like to sync to Azure DevOps?

You can select by:
  • all - Sync all tasks
  • us1 - All tasks for User Story 1
  • us1,us2 - All tasks for multiple User Stories
  • 1,2,3 - Specific task numbers (comma-separated)
  • 1-10 - Range of task numbers

Your selection:
```

**Wait for user response**, then parse selection:

- "all" → select all tasks
- "us1" → select all tasks linked to User Story 1
- "us1,us3" → select all tasks linked to User Story 1 and 3
- "1,3,5" → select tasks 1, 3, and 5
- "1-10" → select tasks 1 through 10
- Empty/invalid → prompt again

### Step 4: Show Confirmation

**After getting selection, show what will be created**:

```text
You selected X tasks to sync:

User Story 1 (3 tasks):
  - T001 - Setup authentication service
  - T002 - Create login endpoint
  - T003 - Implement password validation

User Story 2 (2 tasks):
  - T005 - Design user profile schema
  - T006 - Create profile API

Is this correct? (yes/no)
```

### Step 5a: Execute Script with Collected Parameters

Now run the PowerShell script with all the parameters collected from chat:

```powershell
.\scripts\powershell\create-ado-workitems-oauth.ps1 `
  -SpecFile "<path-to-spec.md>" `
  -Organization "$orgName" `
  -Project "$projectName" `
  -AreaPath "$areaPath" `
  -Stories "<selection>" `
  -NoConfirm
```

**Note**: Use `-NoConfirm` flag since we already confirmed with the user in chat.

The script will:

1. ✅ Check Azure CLI installation
2. ✅ Verify/install Azure DevOps extension  
3. ✅ Authenticate via `az login` (OAuth) if needed
4. ✅ Create work items using `az boards work-item create`
5. ✅ Return work item IDs and URLs
6. ✅ Save mapping to `.speckit/azure-devops-mapping.json`
7. ✅ Update configuration file `~/.speckit/ado-config.json`

### Step 6a: Display Results

Show the script output which includes:

- Real-time progress for each story
- Created work item IDs and URLs
- Summary table
- Links to Azure DevOps boards

### Step 5b: Prepare Work Items

For each selected user story, prepare work item data:

```javascript
{
  type: "User Story",
  title: `User Story ${storyNumber} - ${storyTitle}`,
  fields: {
    "System.Description": `${description}\n\n**Why this priority**: ${whyPriority}\n\n**Independent Test**: ${independentTest}`,
    "Microsoft.VSTS.Common.AcceptanceCriteria": formatAcceptanceCriteria(scenarios),
    "Microsoft.VSTS.Common.Priority": convertPriority(priority), // P1→1, P2→2, P3→3
    "System.Tags": `spec-kit; ${featureName}; user-story`,
    "System.AreaPath": areaPath || `${project}`,
    "System.IterationPath": `${project}` // Can be enhanced to detect current sprint
  }
}
```

**Acceptance Criteria Formatting**:

```text
Scenario 1:
Given: <given>
When: <when>
Then: <then>

Scenario 2:
Given: <given>
When: <when>
Then: <then>
```

### Step 5c: Execute Script with Collected Parameters

Now run the PowerShell/Bash script with all the parameters collected from chat:

**PowerShell**:

```powershell
.\scripts\powershell\create-ado-workitems-oauth.ps1 `
  -SpecFile "<path-to-spec.md or tasks.md>" `
  -Organization "$orgName" `
  -Project "$projectName" `
  -AreaPath "$areaPath" `
  -Stories "<selection>" `
  -FromTasks  # Only if syncing tasks
```

**Bash**:

```bash
./scripts/bash/create-ado-workitems-oauth.sh \
  --spec-file "<path-to-spec.md or tasks.md>" \
  --organization "$orgName" \
  --project "$projectName" \
  --area-path "$areaPath" \
  --stories "<selection>" \
  --from-tasks  # Only if syncing tasks
```

The script will:

1. ✅ Check Azure CLI installation
2. ✅ Verify/install Azure DevOps extension  
3. ✅ Authenticate via `az login` (OAuth) if needed
4. ✅ Create work items using `az boards work-item create`
5. ✅ Return work item IDs and URLs
6. ✅ Save mapping to `.speckit/azure-devops-mapping.json`
7. ✅ Update configuration file `~/.speckit/ado-config.json`

### Step 6b: Display Results

Show the script output which includes:

- Real-time progress for each story/task
- Created work item IDs and URLs
- Summary table
- Links to Azure DevOps boards

1. **Error handling**:
   - **Authentication failed** → Show re-authentication instructions
   - **Permission denied** → Explain required Azure DevOps permissions (Contributor or higher)
   - **Extension not found** → Guide user to install `ms-daw-tca.ado-productivity-copilot`
   - **Network error** → Show error and suggest retry
   - **Invalid field** → Show error and continue with remaining stories

2. **Real-time feedback**: Display status as each work item is created:

   ```text
   Creating User Story 1 of 3...
   ✓ Created User Story 1: Display Success Notifications (#12345)
   
   Creating User Story 2 of 3...
   ✓ Created User Story 2: Edit Notifications (#12346)
   
   Creating User Story 3 of 3...
   ✗ Failed User Story 3: Delete Notifications (Permission denied)
   ```

### Step 6c: Display Results

Show summary table:

```markdown
## ✅ Azure DevOps Sync Complete

**Organization**: MSFTDEVICES  
**Project**: Devices  
**Feature**: photo-album-management  
**Synced**: 3 of 4 user stories

### Created Work Items

| Story | Title | Priority | Work Item | Status |
|-------|-------|----------|-----------|--------|
| 1 | Create Photo Albums | P1 | [#12345](https://dev.azure.com/MSFTDEVICES/Devices/_workitems/edit/12345) | ✅ Created |
| 2 | Add Photos to Albums | P1 | [#12346](https://dev.azure.com/MSFTDEVICES/Devices/_workitems/edit/12346) | ✅ Created |
| 3 | Delete Albums | P2 | [#12347](https://dev.azure.com/MSFTDEVICES/Devices/_workitems/edit/12347) | ✅ Created |

### View in Azure DevOps

- **Boards**: [https://dev.azure.com/MSFTDEVICES/Devices/_boards](https://dev.azure.com/MSFTDEVICES/Devices/_boards)
- **Work Items**: [https://dev.azure.com/MSFTDEVICES/Devices/_workitems](https://dev.azure.com/MSFTDEVICES/Devices/_workitems)
- **Backlog**: [https://dev.azure.com/MSFTDEVICES/Devices/_backlogs/backlog](https://dev.azure.com/MSFTDEVICES/Devices/_backlogs/backlog)

### Tracking

Saved mapping to: `.speckit/azure-devops-mapping.json`

### Next Steps

Now that your user stories are in Azure DevOps, continue with implementation planning:

1. **Create technical plan**: `/speckit.plan` - Generate implementation plan with research and design artifacts
2. **Generate tasks**: `/speckit.tasks` - Break down the plan into actionable tasks
3. **Sync tasks to Azure DevOps**: `/speckit.adosync -FromTasks` - Create Task work items linked to User Stories

Or you can:
- Review work items in Azure DevOps: [View Boards](https://dev.azure.com/{organization}/{project}/_boards)
- Assign work items to team members
- Add to current sprint/iteration
```

**If any failures occurred**, also show:

```markdown
### ⚠️ Errors

| Story | Title | Error |
|-------|-------|-------|
| 4 | Share Albums | Authentication failed - please re-authenticate with Azure DevOps |
```

### Step 7: Save Mapping

Save work item mapping to `.speckit/azure-devops-mapping.json`:

```json
{
  "feature": "photo-album-management",
  "organization": "MSFTDEVICES",
  "project": "Devices",
  "syncDate": "2026-02-27T10:30:00Z",
  "workItems": [
    {
      "storyNumber": 1,
      "storyTitle": "Create Photo Albums",
      "workItemId": 12345,
      "workItemUrl": "https://dev.azure.com/MSFTDEVICES/Devices/_workitems/edit/12345",
      "priority": "P1",
      "status": "created"
    }
  ]
}
```

This mapping file allows:

- Tracking which stories have been synced
- Preventing duplicate syncs
- Updating existing work items (future enhancement)

## Error Handling

### Authentication Required

```text
❌ Azure CLI Not Authenticated

You need to authenticate with Azure CLI to create work items.

To authenticate:
1. Run: az login --use-device-code
2. Follow the prompts in your browser
3. Return to the terminal and run this command again

The script will automatically prompt for authentication if needed.
```

### No Spec File Found

```text
❌ No Spec File Found

This command requires a spec.md file in your feature directory.

To create a spec file, use:
  /specify <your feature description>

Example:
  /specify Add photo album management with create, edit, and delete capabilities
```

### Invalid Story Selection

```text
❌ Invalid Story Selection

Valid formats:
  • all - Select all user stories
  • 1,2,3 - Comma-separated story numbers
  • 1-5 - Range of story numbers

Your input: "abc"

Please try again with a valid selection.
```

## Key Rules

- Check Azure CLI installed, auto-install DevOps extension if missing
- Use OAuth (`az login`) - no PAT tokens
- Save org/project/area to `~/.speckit/ado-config.json` for reuse
- Title format: User Stories = "User Story {#} - {title}", Tasks = "T{#} - {desc}"
- Priority mapping: P1→1, P2→2, P3→3, P4→4
- Auto-link tasks to parent user stories via `[US#]` references
- Continue on failure, report all errors at end
- Save mapping to `.speckit/azure-devops-mapping.json`

## Example Usage

```bash
# Sync user stories from spec.md
# Agent will prompt for org/project/area interactively
/speckit.adosync

# Sync tasks from tasks.md
/speckit.adosync -FromTasks

# The agent will:
# 1. Ask for Azure DevOps configuration (org, project, area)
# 2. Display found user stories or tasks
# 3. Ask which ones to sync
# 4. Create work items via Azure CLI
# 5. Display results with work item IDs and URLs
```
