#!/usr/bin/env bash
# Create Azure DevOps work items using Azure CLI with OAuth (no PAT required)
# Requires: Azure CLI with devops extension

set -e

# Parse arguments
SPEC_FILE=""
ORGANIZATION=""
PROJECT=""
STORIES="all"
AREA_PATH=""
FROM_TASKS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --spec-file)
            SPEC_FILE="$2"
            shift 2
            ;;
        --organization)
            ORGANIZATION="$2"
            shift 2
            ;;
        --project)
            PROJECT="$2"
            shift 2
            ;;
        --stories)
            STORIES="$2"
            shift 2
            ;;
        --area-path)
            AREA_PATH="$2"
            shift 2
            ;;
        --from-tasks)
            FROM_TASKS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$SPEC_FILE" ]]; then
    echo "Error: --spec-file is required"
    exit 1
fi

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI not found. Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: jq not found. This script requires jq for JSON parsing."
    echo "Install jq:"
    echo "  - Ubuntu/Debian: sudo apt-get install jq"
    echo "  - macOS: brew install jq"
    echo "  - More info: https://stedolan.github.io/jq/download/"
    exit 1
fi

# Check if devops extension is installed
if ! az extension list --output json | grep -q "azure-devops"; then
    echo "Installing Azure DevOps extension for Azure CLI..."
    az extension add --name azure-devops
fi

# Check authentication
echo "Checking Azure authentication..."
if ! az account show &> /dev/null; then
    echo "Not authenticated. Running 'az login' with OAuth..."
    az login --use-device-code
fi

# Config file path
CONFIG_DIR="$HOME/.speckit"
CONFIG_FILE="$CONFIG_DIR/ado-config.json"

# Load saved config if exists
if [[ -f "$CONFIG_FILE" ]]; then
    SAVED_ORG=$(jq -r '.Organization // empty' "$CONFIG_FILE")
    SAVED_PROJECT=$(jq -r '.Project // empty' "$CONFIG_FILE")
    SAVED_AREA=$(jq -r '.AreaPath // empty' "$CONFIG_FILE")
fi

# Get organization and project from command-line args, environment, or saved config
if [[ -z "$ORGANIZATION" ]]; then
    ORGANIZATION="${AZURE_DEVOPS_ORG}"
    if [[ -z "$ORGANIZATION" ]] && [[ -n "$SAVED_ORG" ]]; then
        ORGANIZATION="$SAVED_ORG"
    fi
fi
if [[ -z "$PROJECT" ]]; then
    PROJECT="${AZURE_DEVOPS_PROJECT}"
    if [[ -z "$PROJECT" ]] && [[ -n "$SAVED_PROJECT" ]]; then
        PROJECT="$SAVED_PROJECT"
    fi
fi
if [[ -z "$AREA_PATH" ]] && [[ -n "$SAVED_AREA" ]]; then
    AREA_PATH="$SAVED_AREA"
fi

# Validate required parameters
if [[ -z "$ORGANIZATION" ]]; then
    echo "Error: Organization parameter is required. Please provide --organization parameter."
    exit 1
fi
if [[ -z "$PROJECT" ]]; then
    echo "Error: Project parameter is required. Please provide --project parameter."
    exit 1
fi
if [[ -z "$AREA_PATH" ]]; then
    echo "Error: AreaPath parameter is required. Please provide --area-path parameter."
    exit 1
fi

# Save configuration for future reference
CONFIG_DIR="$HOME/.speckit"
CONFIG_FILE="$CONFIG_DIR/ado-config.json"

# Escape backslashes for JSON
AREA_PATH_ESCAPED="${AREA_PATH//\\/\\\\}"

mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_FILE" <<EOF
{
  "Organization": "$ORGANIZATION",
  "Project": "$PROJECT",
  "AreaPath": "$AREA_PATH_ESCAPED",
  "LastUpdated": "$(date '+%Y-%m-%d %H:%M:%S')"
}
EOF

echo "Using Azure DevOps configuration:"
echo "  Organization: $ORGANIZATION"
echo "  Project: $PROJECT"
echo "  Area Path: $AREA_PATH"
echo ""

# Parse user stories from spec.md
parse_user_stories() {
    local file="$1"
    local story_count=0
    
    # Extract all user stories using grep and awk
    while IFS= read -r line; do
        if [[ $line =~ ^###[[:space:]]+User[[:space:]]+Story[[:space:]]+([0-9]+)[[:space:]]*-[[:space:]]*(.+)[[:space:]]*\(Priority:[[:space:]]*P([0-9]+)\) ]]; then
            story_count=$((story_count + 1))
            
            STORY_NUMBERS+=("${BASH_REMATCH[1]}")
            STORY_TITLES+=("${BASH_REMATCH[2]}")
            STORY_PRIORITIES+=("${BASH_REMATCH[3]}")
            
            # Extract story content until next ### or ## section
            local start_line=$(grep -n "### User Story ${BASH_REMATCH[1]}" "$file" | cut -d: -f1)
            local end_line=$(tail -n +$((start_line + 1)) "$file" | grep -n -E "^(###|##)[[:space:]]" | head -1 | cut -d: -f1)
            
            if [[ -z "$end_line" ]]; then
                end_line=$(wc -l < "$file")
            else
                end_line=$((start_line + end_line - 1))
            fi
            
            local content=$(sed -n "${start_line},${end_line}p" "$file")
            
            # Extract description (text after priority line until "**Why")
            local desc=$(echo "$content" | sed -n '/Priority: P[0-9]\+)/,/\*\*Why this priority/p' | sed '1d;$d' | tr '\n' ' ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            STORY_DESCRIPTIONS+=("$desc")
            
            # Extract acceptance criteria
            local accept=$(echo "$content" | sed -n '/\*\*Acceptance Scenarios\*\*:/,/^##/p' | sed '1d;$d' | tr '\n' ' ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            STORY_ACCEPTANCE+=("$accept")
        fi
    done < "$file"
}

# Parse tasks from tasks.md
parse_tasks() {
    local file="$1"
    local task_count=0
    
    # Extract all tasks matching the pattern: - [ ] T### [P?] [US#?] Description
    while IFS= read -r line; do
        if [[ $line =~ ^-[[:space:]]\[[[:space:]]\][[:space:]]+T([0-9]+)[[:space:]]+(\[P\][[:space:]]+)?(\[US([0-9]+)\][[:space:]]+)?(.+)$ ]]; then
            task_count=$((task_count + 1))
            
            TASK_NUMBERS+=("${BASH_REMATCH[1]}")
            TASK_PARALLEL+=("${BASH_REMATCH[2]}")
            TASK_STORY+=("${BASH_REMATCH[4]}")  # User story number
            TASK_DESCRIPTIONS+=("${BASH_REMATCH[5]}")
        fi
    done < "$file"
}

# Arrays to store story/task data
declare -a STORY_NUMBERS
declare -a STORY_TITLES
declare -a STORY_PRIORITIES
declare -a STORY_DESCRIPTIONS
declare -a STORY_ACCEPTANCE
declare -a TASK_NUMBERS
declare -a TASK_PARALLEL
declare -a TASK_STORY
declare -a TASK_DESCRIPTIONS

# Parse stories or tasks based on mode
FEATURE_NAME=$(basename $(dirname "$SPEC_FILE"))

if [[ "$FROM_TASKS" == true ]]; then
    parse_tasks "$SPEC_FILE"
    STORY_COUNT="${#TASK_NUMBERS[@]}"
    echo "Found $STORY_COUNT tasks"
else
    parse_user_stories "$SPEC_FILE"
    STORY_COUNT="${#STORY_NUMBERS[@]}"
    echo "Found $STORY_COUNT user stories"
fi

# Filter stories/tasks based on selection
if [[ "$STORIES" == "all" ]]; then
    if [[ "$FROM_TASKS" == true ]]; then
        SELECTED_STORIES=("${TASK_NUMBERS[@]}")
    else
        SELECTED_STORIES=("${STORY_NUMBERS[@]}")
    fi
else
    IFS=',' read -ra SELECTED_STORIES <<< "$STORIES"
fi

if [[ "$FROM_TASKS" == true ]]; then
    echo "Syncing ${#SELECTED_STORIES[@]} tasks"
else
    echo "Syncing ${#SELECTED_STORIES[@]} user stories"
fi
echo ""

# Create work items
declare -a CREATED_IDS
declare -a CREATED_URLS
declare -a CREATED_STORY_REFS
declare -a CREATED_TITLES
declare -a CREATED_PRIORITIES

# Load parent story mappings if in FROM_TASKS mode
declare -A PARENT_MAPPING
if [[ "$FROM_TASKS" == true ]]; then
    MAPPING_FILE="$(dirname "$SPEC_FILE")/.speckit/azure-devops-mapping.json"
    if [[ -f "$MAPPING_FILE" ]]; then
        echo "Loading parent user story mappings..."
        while IFS= read -r line; do
            story_num=$(echo "$line" | jq -r '.storyNumber')
            work_item_id=$(echo "$line" | jq -r '.workItemId')
            PARENT_MAPPING[$story_num]=$work_item_id
        done < <(jq -c '.workItems[]' "$MAPPING_FILE")
        echo "Loaded ${#PARENT_MAPPING[@]} parent stories"
        echo ""
    fi
fi

for selected in "${SELECTED_STORIES[@]}"; do
    if [[ "$FROM_TASKS" == true ]]; then
        # Handle task creation
        # Normalize selected number to remove leading zeros for comparison
        normalized_selected=$((10#$selected))
        
        for i in "${!TASK_NUMBERS[@]}"; do
            # Normalize task number to remove leading zeros
            normalized_task=$((10#${TASK_NUMBERS[$i]}))
            
            if [[ "$normalized_task" == "$normalized_selected" ]]; then
                num="${TASK_NUMBERS[$i]}"
                desc="${TASK_DESCRIPTIONS[$i]}"
                story_ref="${TASK_STORY[$i]}"
                
                work_item_title="T${num} - $desc"
                item_type="Task"
                
                # Clean field values
                clean_title="${work_item_title//\"/\"\"}"
                clean_desc=$(echo "$desc" | tr '\n' ' ' | sed 's/"/\\"/g')
                
                tags="spec-kit;$FEATURE_NAME;task"
                if [[ -n "$story_ref" ]]; then
                    tags="$tags;US$story_ref"
                fi
                
                echo "Creating Task $num: ${desc:0:60}..."
                
                # Build az command (temporarily disable set -e for error handling)
                set +e
                result=$(az boards work-item create \
                    --type "Task" \
                    --title "$clean_title" \
                    --organization "https://dev.azure.com/$ORGANIZATION" \
                    --project "$PROJECT" \
                    --fields \
                        "System.Description=$clean_desc" \
                        "System.Tags=$tags" \
                        "System.AssignedTo=" \
                        "Microsoft.VSTS.Scheduling.OriginalEstimate=0" \
                        ${AREA_PATH:+"System.AreaPath=$AREA_PATH"} \
                    --output json 2>&1)
                exit_code=$?
                set -e
                
                if [[ $exit_code -eq 0 ]] && [[ ! "$result" =~ ERROR ]]; then
                    work_item_id=$(echo "$result" | jq -r '.id')
                    work_item_url="https://dev.azure.com/$ORGANIZATION/$PROJECT/_workitems/edit/$work_item_id"
                    
                    echo "  [OK] Created work item #$work_item_id"
                    echo "  -> $work_item_url"
                    echo ""
                    
                    CREATED_IDS+=("$work_item_id")
                    CREATED_URLS+=("$work_item_url")
                    CREATED_STORY_REFS+=("$story_ref")
                    CREATED_TITLES+=("$desc")
                    CREATED_PRIORITIES+=("N/A")
                else
                    echo "  [FAIL] Failed to create work item"
                    echo "  Error: $result"
                    echo ""
                fi
                
                break
            fi
        done
    else
        # Handle user story creation (original logic)
        for i in "${!STORY_NUMBERS[@]}"; do
            if [[ "${STORY_NUMBERS[$i]}" == "$selected" ]]; then
                num="${STORY_NUMBERS[$i]}"
                title="${STORY_TITLES[$i]}"
                priority="${STORY_PRIORITIES[$i]}"
                desc="${STORY_DESCRIPTIONS[$i]}"
                accept="${STORY_ACCEPTANCE[$i]}"
                
                work_item_title="User Story $num - $title"
                item_type="User Story"
                
                # Clean field values (remove newlines and escape quotes)
                # For title: double quotes for Azure CLI
                clean_title="${work_item_title//\"/\"\"}"
                clean_desc=$(echo "$desc" | tr '\n' ' ' | sed 's/"/\\"/g')
                clean_accept=$(echo "$accept" | tr '\n' ' ' | sed 's/"/\\"/g')
                
                tags="spec-kit;$FEATURE_NAME;user-story"
                
                echo "Creating User Story $num: $title..."
                
                # Build az command (temporarily disable set -e for error handling)
                set +e
                result=$(az boards work-item create \
                    --type "User Story" \
                    --title "$clean_title" \
                    --organization "https://dev.azure.com/$ORGANIZATION" \
                --project "$PROJECT" \
                --fields \
                    "System.Description=$clean_desc" \
                    "Microsoft.VSTS.Common.Priority=$priority" \
                    "System.Tags=$tags" \
                    "Microsoft.VSTS.Common.AcceptanceCriteria=$clean_accept" \
                    "System.AssignedTo=" \
                    ${AREA_PATH:+"System.AreaPath=$AREA_PATH"} \
                --output json 2>&1)
            exit_code=$?
            set -e
            
            if [[ $exit_code -eq 0 ]] && [[ ! "$result" =~ ERROR ]]; then
                work_item_id=$(echo "$result" | jq -r '.id')
                work_item_url="https://dev.azure.com/$ORGANIZATION/$PROJECT/_workitems/edit/$work_item_id"
                
                echo "  [OK] Created work item #$work_item_id"
                echo "  -> $work_item_url"
                echo ""
                
                CREATED_IDS+=("$work_item_id")
                CREATED_URLS+=("$work_item_url")
                CREATED_TITLES+=("$title")
                CREATED_PRIORITIES+=("$priority")
            else
                echo "  [FAIL] Failed to create work item"
                echo "  Error: $result"
                echo ""
            fi
            
            break
        fi
    done
    fi
done

# Link tasks to parent user stories if in FROM_TASKS mode
if [[ "$FROM_TASKS" == true ]] && [[ ${#PARENT_MAPPING[@]} -gt 0 ]] && [[ ${#CREATED_IDS[@]} -gt 0 ]]; then
    echo "Linking tasks to parent user stories..."
    echo ""
    
    for i in "${!CREATED_IDS[@]}"; do
        story_ref="${CREATED_STORY_REFS[$i]}"
        if [[ -n "$story_ref" ]] && [[ -n "${PARENT_MAPPING[$story_ref]}" ]]; then
            parent_id="${PARENT_MAPPING[$story_ref]}"
            task_id="${CREATED_IDS[$i]}"
            
            echo -n "  Linking Task #$task_id -> User Story #$parent_id..."
            
            link_result=$(az boards work-item relation add \
                --id "$task_id" \
                --relation-type "Parent" \
                --target-id "$parent_id" \
                --organization "https://dev.azure.com/$ORGANIZATION" \
                --output json 2>&1)
            
            if [[ $? -eq 0 ]]; then
                echo " [OK]"
            else
                echo " [FAIL]"
                echo "    Error: $link_result"
            fi
        fi
    done
    echo ""
fi

# Summary
if [[ ${#CREATED_IDS[@]} -gt 0 ]]; then
    echo ""
    echo "=============================================="
    echo "[SUCCESS] Azure DevOps Sync Complete"
    echo "=============================================="
    echo ""
    echo "Organization: $ORGANIZATION"
    echo "Project: $PROJECT"
    echo "Feature: $FEATURE_NAME"
    
    if [[ "$FROM_TASKS" == true ]]; then
        echo "Created: ${#CREATED_IDS[@]} of ${#SELECTED_STORIES[@]} tasks"
    else
        echo "Created: ${#CREATED_IDS[@]} of ${#SELECTED_STORIES[@]} user stories"
    fi
    echo ""
    echo "Created Work Items:"
    echo ""
    
    for i in "${!CREATED_IDS[@]}"; do
        if [[ "$FROM_TASKS" == true ]]; then
            echo "  Task [${SELECTED_STORIES[$i]}]: ${CREATED_TITLES[$i]}"
            if [[ -n "${CREATED_STORY_REFS[$i]}" ]]; then
                echo "      Parent: US${CREATED_STORY_REFS[$i]}"
            fi
        else
            echo "  [${SELECTED_STORIES[$i]}] ${CREATED_TITLES[$i]} (P${CREATED_PRIORITIES[$i]})"
        fi
        echo "      Work Item: #${CREATED_IDS[$i]}"
        echo "      Link: ${CREATED_URLS[$i]}"
        echo ""
    done
    
    echo "View in Azure DevOps:"
    echo "  Boards: https://dev.azure.com/$ORGANIZATION/$PROJECT/_boards"
    echo "  Work Items: https://dev.azure.com/$ORGANIZATION/$PROJECT/_workitems"
    echo ""
    
    # Save mapping
    SPEC_DIR=$(dirname "$SPEC_FILE")
    SPECKIT_DIR="$SPEC_DIR/.speckit"
    mkdir -p "$SPECKIT_DIR"
    
    MAPPING_FILE="$SPECKIT_DIR/azure-devops-mapping.json"
    echo "{" > "$MAPPING_FILE"
    echo "  \"organization\": \"$ORGANIZATION\"," >> "$MAPPING_FILE"
    echo "  \"project\": \"$PROJECT\"," >> "$MAPPING_FILE"
    echo "  \"feature\": \"$FEATURE_NAME\"," >> "$MAPPING_FILE"
    echo "  \"workItems\": [" >> "$MAPPING_FILE"
    
    for i in "${!CREATED_IDS[@]}"; do
        comma=""
        [[ $i -lt $((${#CREATED_IDS[@]} - 1)) ]] && comma=","
        echo "    {" >> "$MAPPING_FILE"
        echo "      \"storyNumber\": ${SELECTED_STORIES[$i]}," >> "$MAPPING_FILE"
        echo "      \"workItemId\": ${CREATED_IDS[$i]}," >> "$MAPPING_FILE"
        echo "      \"url\": \"${CREATED_URLS[$i]}\"" >> "$MAPPING_FILE"
        echo "    }$comma" >> "$MAPPING_FILE"
    done
    
    echo "  ]" >> "$MAPPING_FILE"
    echo "}" >> "$MAPPING_FILE"
    
    echo "Mapping saved: $MAPPING_FILE"
fi
