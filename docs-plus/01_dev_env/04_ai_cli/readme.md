# Complete AI CLI Tutorial: Gemini, Qwen & Claude Code

## Table of Contents
1. [Introduction to AI Coding Assistants](#introduction)
2. [Gemini CLI](#gemini-cli)
3. [Qwen Code](#qwen-code)
4. [Claude Code](#claude-code)
5. [Comparison and Use Cases](#comparison)
6. [Workflow Integration](#workflow)
7. [Best Practices](#best-practices)
8. [Advanced Usage](#advanced)
9. [Troubleshooting](#troubleshooting)

---

## Introduction to AI Coding Assistants {#introduction}

### What Are Terminal-Based AI Assistants?

Terminal-based AI coding assistants bring the power of Large Language Models (LLMs) directly into your command line, allowing you to:
- Generate code without leaving the terminal
- Get bash commands and git operations on demand
- Debug issues by asking questions
- Write documentation and specifications
- Learn shell commands with explanations
- Refactor and optimize code
- Execute complex command pipelines safely

### Why Use Terminal AI Assistants?

**Advantages:**
- **Speed**: No context switching between browser and terminal
- **Integration**: Works with your existing terminal workflow
- **Command Generation**: Instantly get bash, git, and system commands
- **Privacy**: Some can run locally (Qwen Code)
- **Efficiency**: Pipe output to files, chain commands
- **Learning**: Understand commands with AI explanations
- **Focus**: Stay in flow state without distractions

### Tool Comparison Overview

| Feature | Gemini CLI | Qwen Code | Claude Code |
|---------|------------|-----------|-------------|
| **Cost** | Free (generous) | Free (local) | $20/month |
| **Quality** | Excellent | Very Good | Best |
| **Speed** | Fast | Very Fast | Fast |
| **Context** | Large | Medium | Very Large |
| **Best For** | Specs, PRDs, Debugging | Coding (free) | Professional Coding |
| **Offline** | No | Yes | No |
| **Model** | Gemini 2.5 Pro | Qwen 3 Coder | Claude Sonnet 4.5 |
| **Bash/Git Help** | Excellent | Very Good | Excellent |

### Our Recommendations

**For Specification Writing & PRD Drafting:**
→ **Gemini CLI** (Gemini 2.5 Pro)
- Excellent at understanding complex requirements
- Great for documentation and planning
- Generous free tier
- Strong reasoning capabilities
- Excellent at generating shell scripts and automation

**For Coding (Budget Option):**
→ **Qwen Code 3**
- Completely free, runs locally
- Surprisingly good code quality
- Fast inference on modern hardware
- No API costs
- Good at bash commands and git workflows

**For Professional Coding:**
→ **Claude Code** (Sonnet 4.5)
- Best code quality and reasoning
- Excellent at understanding context
- Superior debugging capabilities
- Worth $20/month for professionals
- Best at complex shell automation and system tasks

---

## Gemini CLI {#gemini-cli}

### What is Gemini CLI?

Google's Gemini CLI brings the powerful Gemini 2.5 Pro model to your terminal. It excels at:
- Understanding complex requirements
- Writing detailed specifications
- Generating bash commands and scripts
- Git workflow assistance
- Debugging intricate issues
- Long-form documentation
- System administration tasks
- Multi-turn conversations

### Installation

Check Steps in this directory

### Basic Usage

**Single Query:**
```bash
# Ask a question
gemini "Explain asyncio in Python"

# Generate code
gemini "Write a Python function to validate email addresses"

# Get bash commands
gemini "How do I find all Python files modified in the last 7 days?"
# Output: find . -name "*.py" -mtime -7

# Get git commands
gemini "Git command to squash last 3 commits"
# Output: git rebase -i HEAD~3

# Debug code
gemini "Why does this give IndexError: $(cat buggy.py)"
```

**Interactive Chat:**
```bash
# Start chat mode
gemini

# Then interact:
You: Write a PRD for a task management app
Gemini: [Generates detailed PRD]

You: Add authentication requirements
Gemini: [Updates PRD with auth specs]

# Ask for commands:
You: How do I recursively change permissions of all .sh files?
Gemini: find . -name "*.sh" -type f -exec chmod +x {} \;

# Type 'exit' to quit
```

**Piping and Redirection:**
```bash
# Save response to file
gemini "Create API documentation template" > api-template.md

# Use file content as context
gemini "Review this code: $(cat app.py)"

# Get command suggestions
gemini "Command to check which process is using port 8000"
# Output: lsof -i :8000 or netstat -tulpn | grep 8000

# Chain with other commands
cat error.log | tail -20 | xargs -I {} gemini "Explain this error: {}"
```

### Bash and Git Command Generation with Gemini

**File Operations:**
```bash
# Get file manipulation commands
gemini "How do I copy all .py files to a backup directory preserving structure?"
# Output: rsync -av --include='*.py' --include='*/' --exclude='*' . backup/

gemini "Find and delete all __pycache__ directories"
# Output: find . -type d -name "__pycache__" -exec rm -rf {} +

gemini "Command to find the 10 largest files"
# Output: du -ah . | sort -rh | head -10
```

**Git Workflows:**
```bash
# Get git commands
gemini "How do I create a branch from main and push it?"
# Output: git checkout main && git pull && git checkout -b feature-name && git push -u origin feature-name

gemini "I accidentally committed to main. How do I move it to a new branch?"
# Output step-by-step:
# git branch feature-branch
# git reset --hard HEAD~1
# git checkout feature-branch

gemini "Show commits by author in last month"
# Output: git log --author="Name" --since="1 month ago" --oneline
```

**Text Processing:**
```bash
# Get pipeline commands
gemini "Extract email addresses from a log file"
# Output: grep -Eo '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' logfile.txt

gemini "Count unique IP addresses in nginx log"
# Output: awk '{print $1}' access.log | sort | uniq -c | sort -rn
```

**Safe Command Execution:**
```bash
# SAFE: Review before executing
command=$(gemini "Command to backup /etc directory")
echo "$command"  # Review the command first!
# If it looks good:
eval "$command"

# SAFE: Ask for explanation
gemini "Explain this command: tar -czf backup.tar.gz --exclude='*.log' /data"

# Create helper function for safety
cmd() {
    echo "=== AI Suggestion ==="
    gemini "$*"
    echo "=== Review before executing! ==="
}

# Usage:
cmd "backup all Python files modified today"
```

### Use Cases for Gemini CLI

#### 1. Writing Product Requirements Documents (PRDs)

```bash
# Create interactive session
gemini

You: Write a comprehensive PRD for an AI-powered coding assistant
     that helps developers write better code. Include:
     - Executive summary
     - Problem statement
     - User personas
     - Features and requirements
     - Technical specifications
     - Success metrics

Gemini: [Generates detailed 5-10 page PRD]

You: Add a section on security and privacy considerations

Gemini: [Adds comprehensive security section]

# Save to file
gemini "Generate final PRD for AI coding assistant with all sections" > prd-coding-assistant.md
```

#### 2. Writing Technical Specifications

```bash
gemini "Write technical specification for a REST API that manages 
user authentication with JWT tokens. Include:
- API endpoints
- Request/response formats
- Error handling
- Security considerations
- Database schema" > api-spec.md
```

#### 3. System Administration Tasks

```bash
# Get complex system commands
gemini "How do I set up a cron job to backup database daily at 2am?"
# Output: 0 2 * * * /usr/local/bin/backup-db.sh

gemini "Command to monitor disk usage and alert if over 80%"
# Output: [Provides monitoring script]

gemini "How do I check which services are listening on network ports?"
# Output: netstat -tulpn or ss -tulpn
```

#### 4. Debugging Complex Issues

```bash
# Debug with full context
gemini "I'm getting this error in my Django app:

$(cat error.log)

Here's the relevant code:

$(cat views.py)

And the model:

$(cat models.py)

What's causing this error and how do I fix it?"
```

#### 5. Creating Shell Scripts

```bash
# Generate automation scripts
gemini "Write a bash script that:
- Takes a directory as argument
- Finds all .log files older than 30 days
- Compresses them with gzip
- Moves to archive directory
- Sends email notification" > cleanup.sh

chmod +x cleanup.sh

# Ask for improvements
gemini "Add error handling and logging to: $(cat cleanup.sh)"
```

#### 6. Generating Documentation

```bash
# Generate README
gemini "Create a comprehensive README.md for a Python project that:
- Uses FastAPI
- Has PostgreSQL database
- Implements JWT auth
- Has Docker setup
Include installation, usage, and API documentation" > README.md
```

### Advanced Gemini CLI Features

**Enhanced Script with File Context:**

```bash
cat > ~/gemini-cli-advanced.py << 'EOF'
#!/usr/bin/env python3

import google.generativeai as genai
import os
import sys
import argparse

api_key = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

def read_file(filepath):
    """Read file content"""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {filepath}: {e}"

def main():
    parser = argparse.ArgumentParser(description='Gemini CLI with file support')
    parser.add_argument('prompt', nargs='*', help='Prompt for Gemini')
    parser.add_argument('-f', '--file', action='append', help='Include file content')
    parser.add_argument('-c', '--chat', action='store_true', help='Chat mode')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('--cmd', action='store_true', help='Command mode (for bash/git help)')
    
    args = parser.parse_args()
    
    # Build prompt with file contents
    prompt_parts = []
    
    if args.file:
        for filepath in args.file:
            content = read_file(filepath)
            prompt_parts.append(f"Content of {filepath}:\n```\n{content}\n```\n")
    
    if args.prompt:
        prompt_text = ' '.join(args.prompt)
        if args.cmd:
            prompt_text = f"Provide only the command(s) to: {prompt_text}"
        prompt_parts.append(prompt_text)
    
    if args.chat or (not args.prompt and not args.file):
        # Chat mode
        chat = model.start_chat(history=[])
        print("Gemini CLI - Chat Mode (bash/git commands supported!)")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() == 'exit':
                    break
                response = chat.send_message(user_input)
                print(f"\nGemini: {response.text}")
            except KeyboardInterrupt:
                break
    else:
        # Single query
        full_prompt = '\n'.join(prompt_parts)
        response = model.generate_content(full_prompt)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(response.text)
            print(f"Response saved to {args.output}")
        else:
            print(response.text)

if __name__ == "__main__":
    main()
EOF

chmod +x ~/gemini-cli-advanced.py
echo 'alias gai="python3 ~/gemini-cli-advanced.py"' >> ~/.bashrc
source ~/.bashrc
```

**Usage:**
```bash
# Include file content
gai -f app.py "Review this code for security issues"

# Multiple files
gai -f models.py -f views.py "Explain how these files work together"

# Save output
gai "Write unit tests for authentication" -o tests.py

# Command mode (concise output)
gai --cmd "find all files larger than 100MB"
# Output: find . -type f -size +100M

gai --cmd "git command to undo last commit keeping changes"
# Output: git reset --soft HEAD~1
```

---

## Qwen Code {#qwen-code}

### What is Qwen Code?

Qwen Code is a powerful, open-source coding model that runs locally on your machine:
- **Completely Free**: No API costs, unlimited usage
- **Private**: All processing happens on your machine
- **Fast**: Optimized for coding tasks
- **Capable**: Qwen 2.5 Coder rivals paid models
- **Bash/Git Support**: Good at shell commands and git workflows

### System Requirements

**Minimum:**
- 16GB RAM (for 7B model)
- 32GB RAM recommended (for 14B model)
- Modern CPU or GPU (GPU strongly recommended)

**Recommended:**
- NVIDIA GPU with 8GB+ VRAM (RTX 3060 or better)
- 32GB+ RAM
- SSD storage

### Installation

#### Step 1: Install Ollama (All Platforms)

Ollama makes running local LLMs easy.

**Windows (WSL):**
```bash
# In WSL terminal
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

**macOS:**
```bash
# Download from ollama.com or use:
curl -fsSL https://ollama.com/install.sh | sh

# Or via Homebrew
brew install ollama

# Verify
ollama --version
```

**Linux:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify
ollama --version

# Start Ollama service (if needed)
sudo systemctl start ollama
sudo systemctl enable ollama
```

#### Step 2: Download Qwen Code Model

```bash
# Download Qwen 2.5 Coder 7B (recommended for most users)
ollama pull qwen2.5-coder:7b

# Or for better quality (requires more RAM):
ollama pull qwen2.5-coder:14b

# Or smaller model for limited resources:
ollama pull qwen2.5-coder:3b

# Verify model is downloaded
ollama list
```

#### Step 3: Test Installation

```bash
# Test the model
ollama run qwen2.5-coder:7b "Write a Python function to reverse a string"

# Test with bash command
ollama run qwen2.5-coder:7b "Command to find all Python files modified today"

# Should generate code immediately
```

### Basic Usage

**Interactive Mode:**
```bash
# Start interactive session
ollama run qwen2.5-coder:7b

# Now chat with the model
>>> Write a function to calculate fibonacci numbers

[Model generates code]

>>> Add memoization to make it faster

[Model improves the code]

>>> How do I check disk usage in Linux?

[Model provides: df -h]

>>> /bye
# Exit
```

**Single Query:**
```bash
# Quick one-off query
ollama run qwen2.5-coder:7b "Explain Python decorators with examples"

# Generate code
ollama run qwen2.5-coder:7b "Create a FastAPI endpoint for user login"

# Get bash commands
ollama run qwen2.5-coder:7b "Command to compress all .log files"
```

**With File Context:**
```bash
# Include file content in prompt
ollama run qwen2.5-coder:7b "Review this code: $(cat app.py)"

# Debug with context
ollama run qwen2.5-coder:7b "Fix the bug in this code:
$(cat buggy_script.py)"

# Get git help
ollama run qwen2.5-coder:7b "How do I revert this commit: $(git log -1)"
```

### Creating Qwen Code CLI Helper

**Create convenient wrapper script:**

```bash
cat > ~/qwen-code.sh << 'EOF'
#!/bin/bash

MODEL="qwen2.5-coder:7b"

# Function to run query
query() {
    echo "$1" | ollama run "$MODEL"
}

# Interactive mode
interactive() {
    echo "Qwen Code - Interactive Mode (Ctrl+D to exit)"
    echo "Ask about code, bash commands, git workflows, or anything!"
    ollama run "$MODEL"
}

# Command mode - for bash/git commands
cmd() {
    query "Provide only the command(s) to: $1"
}

# Git helper mode
git-help() {
    query "Git command to: $1"
}

# Code review mode
review() {
    if [ -f "$1" ]; then
        content=$(cat "$1")
        query "Review this code for issues and suggest improvements:

\`\`\`
$content
\`\`\`"
    else
        echo "Error: File '$1' not found"
        exit 1
    fi
}

# Explain mode
explain() {
    if [ -f "$1" ]; then
        content=$(cat "$1")
        query "Explain what this code does in detail:

\`\`\`
$content
\`\`\`"
    else
        # Could be a command to explain
        query "Explain this command: $1"
    fi
}

# Debug mode
debug() {
    if [ -f "$1" ]; then
        content=$(cat "$1")
        query "Debug this code and identify issues:

\`\`\`
$content
\`\`\`"
    else
        echo "Error: File '$1' not found"
        exit 1
    fi
}

# Main script logic
case "$1" in
    -i|--interactive)
        interactive
        ;;
    -r|--review)
        review "$2"
        ;;
    -e|--explain)
        explain "$2"
        ;;
    -d|--debug)
        debug "$2"
        ;;
    -c|--cmd)
        shift
        cmd "$*"
        ;;
    -g|--git)
        shift
        git-help "$*"
        ;;
    -h|--help)
        echo "Qwen Code CLI Helper"
        echo ""
        echo "Usage:"
        echo "  qwen [prompt]              - Ask a question"
        echo "  qwen -i, --interactive     - Interactive mode"
        echo "  qwen -c, --cmd [task]      - Get bash command"
        echo "  qwen -g, --git [task]      - Get git command"
        echo "  qwen -r, --review [file]   - Review code"
        echo "  qwen -e, --explain [file|cmd] - Explain code or command"
        echo "  qwen -d, --debug [file]    - Debug code"
        echo "  qwen -h, --help            - Show this help"
        ;;
    "")
        interactive
        ;;
    *)
        query "$*"
        ;;
esac
EOF

chmod +x ~/qwen-code.sh

# Create alias
echo 'alias qwen="~/qwen-code.sh"' >> ~/.bashrc
source ~/.bashrc
```

**Usage Examples:**
```bash
# Quick query
qwen "Write a binary search function in Python"

# Get bash command
qwen --cmd "find all files larger than 100MB"
# Output: find . -type f -size +100M

# Get git command
qwen --git "undo last commit but keep changes"
# Output: git reset --soft HEAD~1

# Explain a command
qwen --explain "tar -xzvf archive.tar.gz"

# Interactive mode
qwen -i

# Review code
qwen --review app.py

# Explain code
qwen --explain complex_algorithm.py

# Debug
qwen --debug broken_script.py
```

### Bash and Git Command Generation with Qwen

**File Operations:**
```bash
# Get file commands
qwen --cmd "recursively change permissions of .sh files to executable"
# Output: find . -name "*.sh" -type f -exec chmod +x {} \;

qwen --cmd "count number of lines in all Python files"
# Output: find . -name "*.py" -exec wc -l {} + | tail -1

qwen --cmd "find files modified in last 24 hours"
# Output: find . -type f -mtime -1
```

**Git Workflows:**
```bash
# Get git commands
qwen --git "create feature branch from main"
# Output: git checkout main && git pull && git checkout -b feature/name

qwen --git "view commit history with graph"
# Output: git log --graph --oneline --all

qwen --git "show changes in last commit"
# Output: git show HEAD

qwen --git "amend last commit message"
# Output: git commit --amend
```

**System Tasks:**
```bash
# System monitoring
qwen --cmd "show disk usage sorted by size"
# Output: du -sh * | sort -h

qwen --cmd "find process using most CPU"
# Output: ps aux --sort=-%cpu | head -5

qwen --cmd "check open network connections"
# Output: netstat -tuln or ss -tuln
```

**Text Processing:**
```bash
# Pipeline commands
qwen --cmd "extract unique email addresses from file"
# Output: grep -Eo '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' file.txt | sort -u

qwen --cmd "count occurrences of each word in file"
# Output: tr -cs '[:alnum:]' '\n' < file.txt | sort | uniq -c | sort -rn
```

### Use Cases for Qwen Code

#### 1. Code Generation (Free Alternative)

```bash
# Generate complete functions
qwen "Create a Python class for a binary search tree with insert, 
      search, and delete methods"

# Generate with tests
qwen "Write a function to validate credit card numbers and include 
      unit tests"

# Generate API endpoints
qwen "Create FastAPI endpoints for CRUD operations on a User model"
```

#### 2. Code Review and Improvement

```bash
# Review your code
qwen --review authentication.py

# Get suggestions
qwen "How can I improve this code:
$(cat inefficient.py)"

# Security review
qwen "Check this code for security vulnerabilities:
$(cat user_handler.py)"
```

#### 3. Learning Shell Commands

```bash
# Learn command patterns
qwen --cmd "backup directory with timestamp"
qwen --explain "rsync -avz source/ dest/"

# Understand complex pipelines
qwen --explain "ps aux | grep python | awk '{print \$2}' | xargs kill"

# Get variations
qwen "Show me 3 different ways to count lines in all Python files"
```

#### 4. Git Workflow Assistance

```bash
# Complex git operations
qwen --git "rebase feature branch onto main"
qwen --git "cherry-pick commit from another branch"
qwen --git "find which commit introduced a bug"

# Understand git commands
qwen --explain "git rebase -i HEAD~3"
```

### Advanced Qwen Code Configuration

**Customize Model Parameters:**

```bash
# Create Modelfile for custom behavior
cat > ~/QwenCoder.modelfile << 'EOF'
FROM qwen2.5-coder:7b

# Set temperature (0 = focused, 1 = creative)
PARAMETER temperature 0.3

# Set context window
PARAMETER num_ctx 4096

# System message
SYSTEM You are an expert programmer and system administrator. 
Provide clear, concise, well-commented code. 
For bash commands, provide the command followed by a brief explanation.
For git commands, explain what the command does.
Follow best practices and prioritize security.
EOF

# Create custom model
ollama create qwen-coder-custom -f ~/QwenCoder.modelfile

# Use custom model
ollama run qwen-coder-custom "Write sorting algorithm"
```

**GPU Acceleration:**

```bash
# Check if GPU is available
ollama run qwen2.5-coder:7b --verbose "test"

# For NVIDIA GPUs, Ollama auto-detects and uses CUDA
# Verify GPU usage:
nvidia-smi

# Should show ollama using GPU memory
```

---

## Claude Code {#claude-code}

### What is Claude Code?

Claude Code is Anthropic's terminal-based coding assistant powered by Claude Sonnet 4.5:
- **Best Code Quality**: Industry-leading reasoning and code generation
- **Large Context**: Understands entire codebases
- **Agentic**: Can autonomously complete multi-step coding tasks
- **Professional**: Worth the $20/month for serious developers
- **Excellent Command Generation**: Best at complex shell scripts and git workflows

### Prerequisites

**Requirements:**
- Node.js 18+ (for Claude Code CLI)
- Anthropic API key (requires payment)
- Credit card for $20/month subscription

**Get API Key:**
1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Sign up / Log in
3. Go to "API Keys"
4. Click "Create Key"
5. Copy your API key (starts with `sk-ant-...`)
6. Add credits or set up billing ($20/month recommended)

### Installation

#### Windows (WSL)

```bash
# Install Node.js if not installed
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify Node.js
node --version
npm --version

# Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# Set up API key
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
claude-code --version
```

#### macOS

```bash
# Install Node.js via Homebrew
brew install node

# Or download from nodejs.org

# Verify
node --version
npm --version

# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Set up API key
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.zshrc
source ~/.zshrc

# Verify
claude-code --version
```

#### Linux

```bash
# Install Node.js (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Fedora/RHEL
sudo dnf install nodejs

# Arch
sudo pacman -S nodejs npm

# Verify
node --version
npm --version

# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Set up API key
echo 'export