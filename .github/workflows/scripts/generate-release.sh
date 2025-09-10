#!/bin/bash
# generate-release.sh: Script to generate release artifacts for spec-kit
# Usage: ./generate-release.sh --version-bump [patch|minor|major] [--package] [--notes] [--github-release]

set -e

# Default values
VERSION_BUMP="patch"
DO_PACKAGE=false
DO_NOTES=false
DO_GITHUB_RELEASE=false

DO_CLEANUP=false

# Configuration
SPECKIT_DIR=".speckit"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --version-bump)
      VERSION_BUMP="$2"
      shift 2
      ;;
    --package)
      DO_PACKAGE=true
      shift
      ;;
    --notes)
      DO_NOTES=true
      shift
      ;;
    --github-release)
      DO_GITHUB_RELEASE=true
      shift
      ;;
    --pyproject-update)
      DO_PYPROJECT_UPDATE=true
      shift
      ;;
    --cleanup)
      DO_CLEANUP=true
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

cleanup() {
  echo "Cleaning up generated folders and zip files..."
  rm -rf sdd-base-package sdd-*-package
  rm -f spec-kit-template-*.zip
  echo "✓ Cleanup complete."
}

# Step 1: Calculate new version
echo "Calculating new version..."
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
VERSION=$(echo $LATEST_TAG | sed 's/v//')
IFS='.' read -ra VERSION_PARTS <<< "$VERSION"
MAJOR=${VERSION_PARTS[0]:-0}
MINOR=${VERSION_PARTS[1]:-0}
PATCH=${VERSION_PARTS[2]:-0}

case "$VERSION_BUMP" in
  major)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  patch)
    PATCH=$((PATCH + 1))
    ;;
  *)
    echo "Invalid version bump: $VERSION_BUMP"
    exit 1
    ;;
esac

NEW_VERSION="v$MAJOR.$MINOR.$PATCH"
echo "New version will be: $NEW_VERSION (was $LATEST_TAG)"

# Step 2: Create release package
if $DO_PACKAGE; then
  echo "Creating release packages..."
  mkdir -p sdd-base-package
  mkdir -p sdd-base-package/$SPECKIT_DIR
  SPECKIT_PATH="sdd-base-package/$SPECKIT_DIR"
  if [ -d "memory" ]; then
    cp -r memory "$SPECKIT_PATH"
    echo "✓ Copied memory folder ($(find memory -type f | wc -l) files)"
  else
    echo "⚠️ memory folder not found"
  fi
  if [ -d "scripts" ]; then
    cp -r scripts "$SPECKIT_PATH"
    echo "✓ Copied scripts folder ($(find scripts -type f | wc -l) files)"
  else
    echo "⚠️ scripts folder not found"
  fi
  if [ -d "templates" ]; then
    cp -r templates "$SPECKIT_PATH"
    if [ -d "$SPECKIT_PATH/templates/commands" ]; then
      rm -rf "$SPECKIT_PATH/templates/commands"
      echo "✓ Removed commands subfolder from templates"
    fi
    echo "✓ Copied templates folder (excluding commands directory)"
  fi

  # Generate command files for each agent from source templates
  generate_commands() {
    local agent=$1
    local ext=$2
    local arg_format=$3
    local output_dir=$4
    
    mkdir -p "$output_dir"
    
    for template in templates/commands/*.md; do
      if [[ -f "$template" ]]; then
        name=$(basename "$template" .md)
        description=$(awk '/^description:/ {gsub(/^description: *"?/, ""); gsub(/"$/, ""); print; exit}' "$template" | tr -d '\r')
        content=$(awk '/^---$/{if(++count==2) start=1; next} start' "$template" | sed "s/{ARGS}/$arg_format/g")
        
        case $ext in
          "toml")
            {
              echo "description = \"$description\""
              echo ""
              echo "prompt = \"\"\""
              echo "$content"
              echo "\"\"\""
            } > "$output_dir/$name.$ext"
            ;;
          "md")
            echo "$content" > "$output_dir/$name.$ext"
            ;;
          "prompt.md")
            {
              echo "# $(echo "$description" | sed 's/\. .*//')"
              echo ""
              echo "$content"
            } > "$output_dir/$name.$ext"
            ;;
        esac
      fi
    done
  }
  
  # Function to update speckit path in scripts (if needed)
  update_speckit_path() {
    local target_dir="$1"
    
    if [ -z "$target_dir" ]; then
      echo "Error: target_dir parameter is required"
      return 1
    fi
    
    if [ ! -d "$target_dir" ]; then
      echo "Error: target directory $target_dir does not exist"
      return 1
    fi
    
    echo "Updating speckit paths in $target_dir..."
    
    # Array of folders to rename
    local folders=("memory" "scripts" "templates")
    
    # Build sed expressions for each folder
    local sed_expressions=()
    # Use '#' as the sed delimiter to avoid confusion with '/' in patterns.
    # Patterns:
    #   - /folder/      → /$SPECKIT_DIR/folder/
    #   - /folder"      → /$SPECKIT_DIR/folder"
    #   - /folder<space>→ /$SPECKIT_DIR/folder<space>
    #   - /folder$      → /$SPECKIT_DIR/folder
    for folder in "${folders[@]}"; do
      sed_expressions+=("-e" "s#/$folder/#/$SPECKIT_DIR/$folder/#g")
      sed_expressions+=("-e" "s#/$folder\"#/$SPECKIT_DIR/$folder\"#g") 
      sed_expressions+=("-e" "s#/$folder #/$SPECKIT_DIR/$folder #g")
      sed_expressions+=("-e" "s#/$folder\$#/$SPECKIT_DIR/$folder#g")
    done
    
    # Find all files and update paths
    find "$target_dir" -type f \( -name "*.md" -o -name "*.py" -o -name "*.sh" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.txt" \) -print0 | xargs -0 sed -i.bak "${sed_expressions[@]}"
    
    # Clean up backup files
    find "$target_dir" -name "*.bak" -delete
    
    echo "✓ Updated speckit paths in $(find "$target_dir" -type f \( -name "*.md" -o -name "*.py" -o -name "*.sh" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.txt" \) | wc -l) files"
  }

  # Create Claude Code package
  mkdir -p sdd-claude-package
  cp -r sdd-base-package/. sdd-claude-package/
  mkdir -p sdd-claude-package/.claude/commands
  generate_commands "claude" "md" "\$ARGUMENTS" "sdd-claude-package/.claude/commands"
  echo "✓ Created Claude Code package"
  
  # Create Gemini CLI package  
  mkdir -p sdd-gemini-package
  cp -r sdd-base-package/. sdd-gemini-package/
  mkdir -p sdd-gemini-package/.gemini/commands
  generate_commands "gemini" "toml" "{{args}}" "sdd-gemini-package/.gemini/commands"
  if [ -f "agent_templates/gemini/GEMINI.md" ]; then
    cp agent_templates/gemini/GEMINI.md sdd-gemini-package/GEMINI.md
  fi
  echo "✓ Created Gemini CLI package"
  
  # Create GitHub Copilot package
  mkdir -p sdd-copilot-package
  cp -r sdd-base-package/. sdd-copilot-package/
  mkdir -p sdd-copilot-package/.github/prompts
  generate_commands "copilot" "prompt.md" "\$ARGUMENTS" "sdd-copilot-package/.github/prompts"
  echo "✓ Created GitHub Copilot package"
  
  # Update speckit paths in all packages
  update_speckit_path "sdd-base-package"
  update_speckit_path "sdd-claude-package"
  update_speckit_path "sdd-gemini-package"
  update_speckit_path "sdd-copilot-package"

  # Create archive files for each package
  cd sdd-claude-package && zip -r ../spec-kit-template-claude-${NEW_VERSION}.zip . && cd ..
  cd sdd-gemini-package && zip -r ../spec-kit-template-gemini-${NEW_VERSION}.zip . && cd ..
  cd sdd-copilot-package && zip -r ../spec-kit-template-copilot-${NEW_VERSION}.zip . && cd ..
  
  # List contents for verification
  echo ""
  echo "📦 Packages created:"
  echo "Claude package contents:"
  unzip -l spec-kit-template-claude-${NEW_VERSION}.zip | head -10
  echo "Gemini package contents:"
  unzip -l spec-kit-template-gemini-${NEW_VERSION}.zip | head -10
  echo "Copilot package contents:"
  unzip -l spec-kit-template-copilot-${NEW_VERSION}.zip | head -10
fi

# Step 3: Generate release notes
if $DO_NOTES; then
  echo "Generating release notes..."
  LAST_TAG=$LATEST_TAG
  if [ "$LAST_TAG" = "v0.0.0" ]; then
    # Check how many commits we have and use that as the limit
    COMMIT_COUNT=$(git rev-list --count HEAD)
    if [ "$COMMIT_COUNT" -gt 10 ]; then
      COMMITS=$(git log --oneline --pretty=format:"- %s" HEAD~10..HEAD)
    else
      COMMITS=$(git log --oneline --pretty=format:"- %s" HEAD~$COMMIT_COUNT..HEAD 2>/dev/null || git log --oneline --pretty=format:"- %s")
    fi
  else
    COMMITS=$(git log --oneline --pretty=format:"- %s" $LAST_TAG..HEAD)
  fi
  cat > release_notes.md << EOF
Template release $NEW_VERSION

Updated specification-driven development templates for GitHub Copilot, Claude Code, and Gemini CLI.

Download the template for your preferred AI assistant:
- spec-kit-template-copilot-${NEW_VERSION}.zip
- spec-kit-template-claude-${NEW_VERSION}.zip
- spec-kit-template-gemini-${NEW_VERSION}.zip  
EOF
  echo "✓ Release notes generated: release_notes.md"
fi

# Step 4: Create GitHub Release
if $DO_GITHUB_RELEASE; then
  echo "Creating GitHub Release..."
  VERSION_NO_V=${NEW_VERSION#v}
  gh release create $NEW_VERSION \
    spec-kit-template-copilot-${NEW_VERSION}.zip \
    spec-kit-template-claude-${NEW_VERSION}.zip \
    spec-kit-template-gemini-${NEW_VERSION}.zip \
    --title "Spec Kit Templates - $VERSION_NO_V" \
    --notes-file release_notes.md
  echo "✓ GitHub Release created"
fi

if $DO_CLEANUP; then
  cleanup
fi
# Step 5: Update pyproject.toml
if $DO_PYPROJECT_UPDATE; then
  echo "Updating pyproject.toml..."
  PYTHON_VERSION=${NEW_VERSION#v}
  if [ -f "pyproject.toml" ]; then
    # Cross-platform in-place sed (macOS vs Linux)
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s/version = \".*\"/version = \"$PYTHON_VERSION\"/" pyproject.toml
    else
      sed -i "s/version = \".*\"/version = \"$PYTHON_VERSION\"/" pyproject.toml
    fi
    echo "✓ Updated pyproject.toml version to $PYTHON_VERSION (for release artifacts only)"
  fi
fi
