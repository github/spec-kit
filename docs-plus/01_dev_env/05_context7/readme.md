# Context7 Tutorial: Enhanced AI Context Management

## Table of Contents
1. [Introduction to Context7](#introduction)
2. [Why Use Context7?](#why-context7)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [Integration with Claude Code](#claude-integration)
6. [Integration with Qwen Code](#qwen-integration)
7. [Integration with Gemini CLI](#gemini-integration)
8. [Advanced Features](#advanced-features)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Introduction to Context7 {#introduction}

https://github.com/upstash/context7

### What is Context7?

Context7 is a powerful command-line tool that intelligently gathers and formats your codebase context for AI assistants. Instead of manually copying files or writing long prompts, Context7 automatically:

- **Analyzes your project structure**
- **Selects relevant files** based on your query
- **Formats context** optimally for AI models
- **Respects .gitignore** and similar patterns
- **Handles large codebases** efficiently
- **Provides token counting** to stay within limits

### How It Works

```
Your Question → Context7 → Analyzes Codebase → Formats Context → AI Assistant
```

Context7 acts as a smart intermediary that:
1. Understands your question/task
2. Identifies relevant files in your project
3. Packages them with proper formatting
4. Sends to your AI assistant (Claude, Qwen, or Gemini)
5. Returns the AI's response with full codebase context

### Benefits

**Without Context7:**
```bash
# Manual, tedious approach
claude "Here's my auth.py: $(cat auth.py)
And my models.py: $(cat models.py)
And my config.py: $(cat config.py)
How do I add OAuth support?"
```

**With Context7:**
```bash
# Automatic, intelligent
context7 "How do I add OAuth support to the authentication system?"
# Context7 automatically finds and includes relevant files!
```

---

## Why Use Context7? {#why-context7}

### Problem: AI Assistants Need Context

AI assistants work best when they understand your entire project, but:
- ❌ Manually including files is tedious
- ❌ You might miss important dependencies
- ❌ Easy to exceed token limits
- ❌ Hard to maintain consistent formatting
- ❌ Difficult to update context as project evolves

### Solution: Context7 Automation

Context7 solves these problems by:
- ✅ Automatically discovering relevant files
- ✅ Intelligently selecting what to include
- ✅ Managing token budgets
- ✅ Consistent, optimal formatting
- ✅ Adapting to project changes
- ✅ Working with any AI assistant

### Use Cases

**1. Code Review with Full Context:**
```bash
context7 "Review the authentication module for security issues"
# Includes: auth files, config, dependencies, related tests
```

**2. Feature Implementation:**
```bash
context7 "Add rate limiting to all API endpoints"
# Includes: route files, middleware, config, examples from existing code
```

**3. Debugging:**
```bash
context7 "Why is the payment webhook failing?"
# Includes: webhook handler, payment logic, error logs, config
```

**4. Refactoring:**
```bash
context7 "Refactor the user service to use dependency injection"
# Includes: all user-related files, existing DI patterns, tests
```

**5. Documentation:**
```bash
context7 "Generate API documentation for the user endpoints"
# Includes: route definitions, schemas, existing docs format
```

---

## Installation {#installation}

### Prerequisites

**All Platforms:**
- Python 3.8 or higher
- pip (Python package manager)
- One or more AI assistants (Claude Code, Qwen Code, or Gemini CLI)

### Windows (WSL)

```bash
# Update system
sudo apt update

# Ensure Python and pip are installed
sudo apt install python3 python3-pip -y

# Verify Python version
python3 --version  # Should be 3.8+

# Install Context7 via pip
pip3 install context7

# Or install from source (for latest features)
git clone https://github.com/context7/context7.git
cd context7
pip3 install -e .

# Verify installation
context7 --version

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### macOS

```bash
# Ensure Python 3.8+ is installed
python3 --version

# If not installed, use Homebrew
brew install python@3.11

# Install Context7
pip3 install context7

# Or from source
git clone https://github.com/context7/context7.git
cd context7
pip3 install -e .

# Verify installation
context7 --version

# Add to PATH if needed
echo 'export PATH="$HOME/Library/Python/3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip git -y

# Fedora/RHEL
sudo dnf install python3 python3-pip git -y

# Arch Linux
sudo pacman -S python python-pip git

# Install Context7
pip3 install context7

# Or from source
git clone https://github.com/context7/context7.git
cd context7
pip3 install -e .

# Verify installation
context7 --version

# Add to PATH if needed (usually in ~/.local/bin)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Verify Installation

```bash
# Check Context7 is working
context7 --help

# Should show:
# Usage: context7 [OPTIONS] COMMAND [ARGS]...
# 
# Context7 - Intelligent codebase context for AI assistants
```

---

## Basic Usage {#basic-usage}

### Initialize Context7 in Your Project

```bash
# Navigate to your project
cd ~/projects/my-app

# Initialize Context7
context7 init

# This creates .context7.yaml with default settings
```

**Default .context7.yaml:**
```yaml
# Context7 Configuration

# Files to always include
include:
  - "README.md"
  - "requirements.txt"
  - "package.json"

# Patterns to ignore (in addition to .gitignore)
ignore:
  - "*.pyc"
  - "__pycache__"
  - "node_modules"
  - ".env"
  - "*.log"
  - ".git"
  - "dist"
  - "build"

# Maximum tokens to include (adjust based on your AI model)
max_tokens: 100000

# Default AI provider (claude, qwen, gemini)
default_provider: claude

# File selection strategy
strategy: smart  # Options: smart, all, manual
```

### Basic Commands

**1. Gather Context (without querying AI):**
```bash
# See what context would be included
context7 gather "authentication system"

# Output shows:
# Files selected: 
# - src/auth/login.py
# - src/auth/jwt.py
# - src/models/user.py
# - config/auth.yaml
# Total tokens: 3,542
```

**2. Ask with Context:**
```bash
# Query AI with automatic context
context7 ask "How does the authentication work?"

# Context7 will:
# 1. Find relevant files
# 2. Format them properly
# 3. Send to AI (using default provider)
# 4. Display response
```

**3. Interactive Mode:**
```bash
# Start interactive session
context7 chat

# Now you can have a conversation:
You: Explain the database schema
AI: [Response with full project context]

You: How can I add a new table for comments?
AI: [Response understanding existing schema]

You: exit
# End session
```

### File Selection

Context7 uses intelligent file selection:

**Automatic (Smart Mode):**
```bash
# Context7 analyzes your query and selects files
context7 ask "Add input validation to the user registration endpoint"

# Automatically includes:
# - User registration route
# - User model/schema
# - Existing validation examples
# - Configuration files
```

**Manual Selection:**
```bash
# Specify files explicitly
context7 ask "Review these files" --files src/auth/*.py src/models/user.py

# Include entire directories
context7 ask "Refactor the API layer" --dir src/api/

# Exclude files
context7 ask "Analyze the codebase" --exclude tests/ --exclude docs/
```

**Pattern-based Selection:**
```bash
# Include by pattern
context7 ask "Review all API routes" --pattern "*/routes/*.py"

# Multiple patterns
context7 ask "Check all config files" --pattern "*.yaml" --pattern "*.json"
```

### Token Management

```bash
# Check token count before sending
context7 tokens "Explain the payment processing"

# Output:
# Estimated tokens: 45,234
# Within limit: Yes (max: 100,000)

# Set custom token limit
context7 ask "Review codebase" --max-tokens 50000

# Context7 will prioritize most relevant files within limit
```

---

## Integration with Claude Code {#claude-integration}

### Setup Claude Code with Context7

**1. Configure Context7 for Claude:**

```bash
# Edit .context7.yaml in your project
cat > .context7.yaml << 'EOF'
default_provider: claude

providers:
  claude:
    model: claude-sonnet-4.5-20250514
    api_key_env: ANTHROPIC_API_KEY
    max_tokens: 200000  # Claude's large context window
    temperature: 0.3
EOF
```

**2. Ensure API Key is Set:**

```bash
# Verify API key is in environment
echo $ANTHROPIC_API_KEY

# If not set:
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
```

### Using Context7 with Claude Code

**Basic Usage:**
```bash
cd my-project

# Ask Claude with full project context
context7 ask "Implement user authentication with JWT"

# Context7 automatically:
# 1. Analyzes your codebase
# 2. Selects relevant files (auth-related code)
# 3. Formats context for Claude
# 4. Sends to Claude Sonnet 4.5
# 5. Returns comprehensive response
```

**Feature Implementation:**
```bash
# Add new feature with context awareness
context7 ask "Add rate limiting middleware. Follow the same pattern 
as the existing auth middleware. Apply it to all API routes."

# Claude receives:
# - Existing middleware examples
# - Route definitions
# - Configuration patterns
# - Project structure
# Result: Consistent implementation following your patterns
```

**Code Review:**
```bash
# Review with full codebase understanding
context7 ask "Review the payment processing module for:
- Security vulnerabilities
- Error handling
- Code quality
- Performance issues"

# Claude analyzes:
# - Payment module files
# - Related dependencies
# - Configuration
# - Integration points
# - Security patterns used elsewhere
```

**Debugging:**
```bash
# Debug with complete context
context7 ask "The user login is failing with 500 error. 
Error log: $(tail -50 error.log)
Debug and fix this issue."

# Claude receives:
# - Auth module code
# - Database models
# - Configuration
# - Recent error logs
# - Related middleware
```

**Multi-file Refactoring:**
```bash
# Complex refactoring task
context7 ask "Refactor the monolithic app.py into:
- routes/ directory for all endpoints
- services/ for business logic
- models/ for data models
- middleware/ for middleware
Maintain all functionality and follow Python best practices."

# Claude can see entire structure and refactor safely
```

### Advanced Claude Integration

**Custom Context with Prompt Templates:**

```bash
# Create prompt template
cat > .context7/templates/review.txt << 'EOF'
Review the following code for:
1. Security vulnerabilities
2. Performance issues
3. Code quality and maintainability
4. Best practices compliance

Context:
{{context}}

Focus area: {{focus}}
EOF

# Use template
context7 ask --template review --vars focus="authentication module"
```

**Agentic Tasks with Context7:**

```bash
# Give Claude an autonomous task with full context
context7 ask "Implement a complete CRUD API for a 'Product' resource:
1. Create database model
2. Create Pydantic schemas
3. Create API routes (GET, POST, PUT, DELETE)
4. Add input validation
5. Write unit tests
6. Update API documentation

Follow the patterns used in the existing User resource."

# Claude has full context of:
# - Existing User resource implementation
# - Database setup
# - API structure
# - Testing patterns
# - Documentation format
```

**Incremental Development:**

```bash
# Start chat session for iterative development
context7 chat

You: Create a new Comment model with user_id, post_id, and content fields
Claude: [Creates model following existing patterns]

You: Add the database migration
Claude: [Generates migration using project's migration tool]

You: Create API routes for comments
Claude: [Creates routes following existing route structure]

You: Add tests
Claude: [Writes tests matching existing test patterns]

You: exit
```

---

## Integration with Qwen Code {#qwen-integration}

### Setup Qwen Code with Context7

**1. Configure Context7 for Qwen:**

```bash
# Edit .context7.yaml
cat > .context7.yaml << 'EOF'
default_provider: qwen

providers:
  qwen:
    model: qwen2.5-coder:7b  # or 14b, 32b depending on your resources
    endpoint: http://localhost:11434  # Ollama endpoint
    max_tokens: 32000  # Qwen's context window
    temperature: 0.3
EOF
```

**2. Ensure Qwen Model is Running:**

```bash
# Start Ollama service (if not already running)
ollama serve &

# Verify model is available
ollama list | grep qwen

# Pull model if needed
ollama pull qwen2.5-coder:7b
```

### Using Context7 with Qwen Code

**Basic Usage:**
```bash
cd my-project

# Initialize Context7
context7 init

# Ask Qwen with project context
context7 ask "Write a function to handle file uploads"

# Context7 provides Qwen with:
# - Existing file handling patterns in your project
# - Configuration (storage settings, etc.)
# - Error handling patterns
# - Security measures you use
```

**Advantages of Qwen + Context7:**

1. **Completely Free**: No API costs
2. **Private**: All processing local
3. **Fast**: Local model + smart context selection
4. **Unlimited**: No rate limits or usage caps

**Code Generation with Context:**

```bash
# Generate code matching your style
context7 ask "Create a new API endpoint for uploading user avatars.
Follow the same patterns as existing upload endpoints."

# Qwen receives context showing:
# - How you structure routes
# - File validation you use
# - Storage configuration
# - Error handling patterns
# Result: Code that fits your codebase
```

**Learning from Your Codebase:**

```bash
# Qwen learns your patterns
context7 ask "Add logging to the payment processing function"

# Context7 shows Qwen:
# - How you configure logging elsewhere
# - Log format you use
# - What information you typically log
# Result: Consistent logging implementation
```

**Large Codebase Handling:**

```bash
# Context7 intelligently selects files for token limits
context7 ask "Add caching to the user profile endpoint" --max-tokens 28000

# Context7 prioritizes:
# 1. User profile endpoint code
# 2. Existing caching examples
# 3. Cache configuration
# 4. Related dependencies
# Fits within Qwen's 32k context window
```

### Optimizing Context7 for Qwen

**Adjust for Smaller Context Window:**

```yaml
# .context7.yaml optimized for Qwen
default_provider: qwen

providers:
  qwen:
    model: qwen2.5-coder:7b
    max_tokens: 28000  # Leave buffer for response
    
# Prioritize most relevant files
strategy: smart

# Be more aggressive with exclusions
ignore:
  - "tests/"
  - "docs/"
  - "*.md"
  - "*.log"
  - "__pycache__"
  - "node_modules"
  - ".git"
  
# Only include essentials by default
include:
  - "README.md"
  - "requirements.txt"
```

**Focus Queries for Better Results:**

```bash
# Specific, focused questions work better
context7 ask "Add input validation to the login function in auth.py"
# Better than: "Review entire auth system"

# Explicitly limit scope
context7 ask "Refactor user.py" --files src/models/user.py src/schemas/user.py
# Better than: "Refactor the codebase"
```

### Qwen-Specific Features

**Iterative Development:**

```bash
# Start chat mode
context7 chat

You: Create a simple TODO model
Qwen: [Creates model]

You: Add validation for the title field
Qwen: [Adds validation]

You: Create API routes for TODO CRUD
Qwen: [Creates routes using patterns from context]
```

**Code Review with Context:**

```bash
# Review specific files with surrounding context
context7 ask "Review api/routes/user.py for security issues" \
  --files api/routes/user.py \
  --context models/user.py config/security.py

# Qwen sees:
# - The file to review
# - Related model for understanding
# - Security configuration for reference
```

---

## Integration with Gemini CLI {#gemini-integration}

### Setup Gemini CLI with Context7

**1. Configure Context7 for Gemini:**

```bash
# Edit .context7.yaml
cat > .context7.yaml << 'EOF'
default_provider: gemini

providers:
  gemini:
    model: gemini-2.0-flash-exp  # or gemini-2.5-pro
    api_key_env: GOOGLE_API_KEY
    max_tokens: 1000000  # Gemini's massive context window!
    temperature: 0.3
EOF
```

**2. Ensure API Key is Set:**

```bash
# Verify API key
echo $GOOGLE_API_KEY

# If not set:
export GOOGLE_API_KEY="your-api-key-here"
echo 'export GOOGLE_API_KEY="your-api-key-here"' >> ~/.bashrc
```

### Using Context7 with Gemini CLI

**Leveraging Gemini's Huge Context Window:**

Gemini's 1M+ token context window means you can include much more of your codebase!

```bash
# Include entire project for comprehensive analysis
context7 ask "Analyze the entire codebase architecture and suggest improvements" \
  --max-tokens 500000

# Gemini can handle:
# - Full project structure
# - All source files
# - Documentation
# - Configuration files
# - Tests
```

**Specification Writing with Full Context:**

```bash
# Generate comprehensive specs
context7 ask "Write a technical specification for adding 
real-time notifications to this application. Include:
- Architecture changes needed
- Database schema updates
- API endpoints
- WebSocket implementation
- Security considerations
Based on the current codebase structure."

# Gemini receives entire codebase and generates spec that:
# - Fits your architecture
# - Uses your existing patterns
# - Integrates with current systems
# - Maintains consistency
```

**Product Requirements Documents (PRDs):**

```bash
# Generate PRDs with codebase understanding
context7 ask "Create a PRD for adding multi-tenancy support 
to this SaaS application. Analyze current architecture and 
propose implementation strategy."

# Output: Comprehensive PRD that understands:
# - Your current single-tenant setup
# - Database structure
# - Authentication system
# - API design
# - Deployment setup
```

**Complex Debugging:**

```bash
# Debug with massive context
context7 ask "We're experiencing performance issues with 
the dashboard loading. Analyze the entire request flow from 
frontend to database and identify bottlenecks.

Error logs:
$(tail -200 error.log)

Performance trace:
$(cat performance-trace.json)"

# Gemini analyzes:
# - Frontend code
# - API routes
# - Database queries
# - Caching layer
# - Configuration
# - Recent logs
```

### Gemini-Specific Advantages

**1. Whole-Codebase Understanding:**

```bash
# Ask high-level questions about entire project
context7 ask "How does data flow through this application 
from user input to database storage?"

# Gemini traces through:
# - Frontend forms
# - API endpoints
# - Validation layers
# - Business logic
# - Database models
# - Persistence layer
```

**2. Cross-Module Analysis:**

```bash
# Understand relationships across modules
context7 ask "Map out all the dependencies between modules 
and identify circular dependencies or tight coupling issues"

# Gemini analyzes entire project structure
```

**3. Documentation Generation:**

```bash
# Generate comprehensive documentation
context7 ask "Generate complete API documentation for all 
endpoints, including request/response examples, error codes, 
and authentication requirements"

# Gemini has context of:
# - All route definitions
# - Request/response schemas
# - Error handling
# - Auth mechanisms
```

### Multi-Provider Strategy

**Use Different Providers for Different Tasks:**

```bash
# Use Gemini for planning (large context, free)
context7 ask --provider gemini "Create architecture design 
for microservices migration" > architecture.md

# Use Claude for implementation (best code quality)
context7 ask --provider claude "Implement the user service 
according to architecture.md"

# Use Qwen for quick tasks (free, local)
context7 ask --provider qwen "Add input validation to signup"
```

**Configure Multiple Providers:**

```yaml
# .context7.yaml
default_provider: claude

providers:
  claude:
    model: claude-sonnet-4.5-20250514
    api_key_env: ANTHROPIC_API_KEY
    max_tokens: 200000
    temperature: 0.3
    
  gemini:
    model: gemini-2.0-flash-exp
    api_key_env: GOOGLE_API_KEY
    max_tokens: 1000000
    temperature: 0.3
    
  qwen:
    model: qwen2.5-coder:7b
    endpoint: http://localhost:11434
    max_tokens: 32000
    temperature: 0.3
```

**Switch Providers Per Query:**

```bash
# Use Gemini for specs
context7 ask --provider gemini "Write technical spec for payment integration"

# Use Claude for coding
context7 ask --provider claude "Implement the payment integration"

# Use Qwen for testing
context7 ask --provider qwen "Write unit tests for payment module"
```

---

## Advanced Features {#advanced-features}

### Context Filtering and Selection

**1. Smart File Selection:**

```bash
# Context7 analyzes your query and selects relevant files
context7 ask "Add email verification to registration"

# Automatically includes:
# ✓ Registration code
# ✓ Email sending utilities
# ✓ User model
# ✓ Configuration (email settings)
# ✗ Unrelated payment code
# ✗ Admin dashboard
```

**2. Manual Override:**

```bash
# Force include specific files
context7 ask "Refactor authentication" \
  --include src/auth/*.py \
  --include config/auth.yaml \
  --include tests/test_auth.py

# Force exclude
context7 ask "Review codebase" \
  --exclude "tests/" \
  --exclude "migrations/" \
  --exclude "*.md"
```

**3. Dependency Tracking:**

```bash
# Include dependencies automatically
context7 ask "Modify the User model" --include-deps

# Context7 includes:
# - User model
# - Files that import User
# - Files User imports
# - Database configuration
```

### Context Templates

**Create Reusable Context Patterns:**

```bash
# Create template directory
mkdir -p .context7/templates

# Create review template
cat > .context7/templates/security-review.yaml << 'EOF'
name: security-review
description: Security review with relevant context
include:
  - "src/**/*.py"
  - "config/**/*.yaml"
  - "requirements.txt"
exclude:
  - "tests/"
  - "docs/"
max_tokens: 150000
prompt_template: |
  Perform a comprehensive security review focusing on:
  1. Authentication and authorization
  2. Input validation
  3. SQL injection prevention
  4. XSS prevention
  5. CSRF protection
  6. Secure configuration
  7. Dependency vulnerabilities
  
  Codebase context:
  {{context}}
EOF

# Use template
context7 ask --template security-review
```

**Common Templates:**

```yaml
# .context7/templates/feature.yaml
name: feature
description: Implementing new feature
include:
  - "src/**/*.py"
  - "config/"
  - "README.md"
max_tokens: 100000
prompt_template: |
  Implement the following feature: {{feature_description}}
  
  Requirements:
  - Follow existing code patterns
  - Add appropriate error handling
  - Include docstrings
  - Maintain code quality
  
  Codebase: {{context}}
```

```yaml
# .context7/templates/debug.yaml
name: debug
description: Debugging with logs
include:
  - "src/**/*.py"
  - "config/"
exclude:
  - "tests/"
max_tokens: 80000
prompt_template: |
  Debug the following issue:
  
  Error: {{error_description}}
  
  Logs:
  {{logs}}
  
  Codebase: {{context}}
```

**Using Templates:**

```bash
# Use feature template
context7 ask --template feature \
  --vars feature_description="Add user profile picture upload"

# Use debug template
context7 ask --template debug \
  --vars error_description="500 error on login" \
  --vars logs="$(tail -100 error.log)"
```

### Context Caching

**Speed Up Repeated Queries:**

```bash
# Enable context caching
context7 cache enable

# First query builds cache
context7 ask "Explain authentication system"
# Takes 5 seconds to gather context

# Subsequent queries use cache
context7 ask "Add MFA to authentication"
# Uses cached context, instant!

# Clear cache when files change
context7 cache clear

# Auto-clear cache on file changes (watch mode)
context7 cache --watch
```

### Git Integration

**Context Based on Git State:**

```bash
# Include only changed files
context7 ask "Review my changes" --git-diff

# Include files changed in last N commits
context7 ask "Explain recent changes" --git-log 5

# Include files in current branch
context7 ask "Review feature branch" --git-branch

# Include uncommitted changes
context7 ask "Should I commit these changes?" --git-staged
```

**Pre-commit Hook:**

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Review staged changes with Context7
context7 ask "Review these changes for:
- Code quality
- Potential bugs
- Security issues
Should I commit?" --git-staged

read -p "Proceed with commit? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

### Collaborative Features

**Shared Context Configuration:**

```bash
# Team shares .context7.yaml in repo
git add .context7.yaml
git commit -m "Add Context7 config for team"

# Everyone gets same context behavior
# Ensures consistency across team
```

**Context Documentation:**

```bash
# Document important files for Context7
cat > .context7/README.md << 'EOF'
# Context7 Guide for This Project

## Important Files

- `src/core/` - Core business logic
- `src/api/` - REST API endpoints
- `config/` - Configuration files
- `src/models/` - Database models

## Common Queries

```bash
# Review authentication
context7 ask "Review auth system" --include src/auth/ src/models/user.py

# Add new feature
context7 ask --template feature --vars feature_description="your feature"

# Debug production issue
context7 ask --template debug --vars error_description="..." --vars logs="..."
```

## Best Practices

- Use templates for common tasks
- Keep context focused (exclude tests/ for code review)
- Use git integration for reviews
- Clear cache after major refactors
EOF
```

---

## Best Practices {#best-practices}

### 1. Project Initialization

**Always Initialize Context7:**

```bash
# In every project
cd my-project
context7 init

# Customize .context7.yaml for project needs
vim .context7.yaml

# Commit to repo for team consistency
git add .context7.yaml
git commit -m "Add Context7 configuration"
```

### 2. Query Formulation

**Be Specific:**

```bash
# ❌ Vague
context7 ask "Fix the bug"

# ✅ Specific
context7 ask "Fix the NoneType error in user.py line 42 
when email is not provided"
```

**Provide Context in Query:**

```bash
# ❌ Lacks context
context7 ask "Add validation"

# ✅ Provides context
context7 ask "Add email format validation to the user 
registration endpoint, similar to how we validate 
passwords in the password reset function"
```

### 3. Token Management

**Monitor Token Usage:**

```bash
# Check before asking
context7 tokens "Review entire codebase"

# If too large, focus query
context7 tokens "Review authentication module"
```

**Use Appropriate Provider:**

```bash
# Small focused task - use Qwen (32k context)
context7 ask --provider qwen "Add docstring to function"

# Medium task - use Claude (200k context)
context7 ask --provider claude "Implement feature"

# Large architectural task - use Gemini (1M context)
context7 ask --provider gemini "Design system architecture"
```

### 4. File Selection Strategy

**Trust Smart Selection:**

```bash
# Let Context7 choose files
context7 ask "Add caching to user profile"
# Context7 finds relevant files automatically
```

**Override When Needed:**

```bash
# When you know exactly what's needed
context7 ask "Review security" \
  --include "src/auth/" \
  --include "src/middleware/security.py" \
  --include "config/security.yaml"
```

### 5. Iterative Development

**Use Chat Mode for Multi-Step Tasks:**

```bash
context7 chat

You: Create a Comment model
AI: [Creates model]

You: Add database migration
AI: [Creates migration]

You: Create API routes
AI: [Creates routes]

You: Add tests
AI: [Adds tests]

You: exit
```

### 6. Version Control Integration

**Review Before Committing:**

```bash
# Before git commit
context7 ask "Review my changes" --git-staged

# Before merging PR
context7 ask "Review this feature branch" --git-diff main
```

### 7. Documentation

**Keep Context7 Docs:**

```bash
# Document common queries in README
cat >> README.md << 'EOF'

## AI-Assisted Development

We use Context7 for AI assistance:

```bash
# Review changes
context7 ask "Review my changes" --git-staged

# Add feature
context7 ask --template feature --vars feature_description="..."

# Debug
context7 ask --template debug --vars error_description="..."
```
EOF