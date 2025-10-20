# The Complete Guide to Zed IDE: AI-Powered Development with Claude Code and Gemini CLI

[Docs](https://zed.dev/docs/)

## Introduction to Zed IDE

Zed is a next-generation code editor built for performance and collaboration. Developed by the creators of Atom and Tree-sitter, Zed is written in Rust and designed from the ground up to be blazingly fast, with native GPU-accelerated rendering that makes it feel incredibly responsive even with large codebases.

What sets Zed apart is its modern architecture that embraces the AI era of software development. Unlike traditional editors that bolted on AI features as afterthoughts, Zed was designed with AI-native workflows in mind, making it an ideal companion for AI-powered development tools.

### Key Features

- **Lightning-fast performance** - Instant startup, smooth scrolling, and responsive editing even with massive files
- **Built-in collaboration** - Real-time collaborative editing without plugins
- **AI-first design** - Native integration points for AI assistants and tooling
- **Minimal and focused** - Clean interface that stays out of your way
- **Cross-platform** - Native apps for macOS, Linux, and Windows with seamless WSL integration

## Why Use Zed with AI CLI Tools?

The combination of Zed with AI command-line tools like Claude Code, Codex, and Gemini CLI creates a powerful development environment that augments your coding capabilities:

### 1. **Seamless Workflow Integration**

Zed's integrated terminal and fast file operations mean you can run AI CLI commands and see results instantly. The editor's speed ensures there's no lag when AI tools modify multiple files simultaneously.

### 2. **Better Context Awareness**

AI CLI tools work best when they can access your entire project structure. Zed's lightweight design means you can keep your terminal and editor side-by-side, giving AI tools full visibility into your codebase while you maintain visual oversight.

### 3. **Efficient File Handling**

When Claude Code or Gemini CLI make bulk changes across multiple files, Zed's performance shines. You can quickly review diffs, navigate between modified files, and verify AI-generated changes without the sluggishness of heavier IDEs.

### 4. **Terminal-First Development**

Zed embraces the terminal-centric workflow that AI CLI tools require. Its integrated terminal feels native and responsive, making it natural to interact with AI assistants while coding.

### 5. **Distraction-Free AI Collaboration**

Zed's minimalist interface lets you focus on the conversation with your AI assistant and the code itself, without UI bloat getting in the way of your creative process.

## Installation Guide

### Windows Installation (Recommended Approach)

For Windows users, the best practice is to install Zed natively on Windows and then connect it to WSL. This gives you the best performance and native Windows integration while leveraging WSL for development.

**Step 1: Install WSL 2**

Open PowerShell as Administrator and run:

```powershell
# Install WSL 2
wsl --install

# Install Ubuntu (recommended distribution)
wsl --install -d Ubuntu
```

Restart your computer after installation.

**Step 2: Set up your Linux distribution**

Open Ubuntu from the Start menu and complete the initial setup (create username and password).

**Step 3: Install Zed on Windows**

Download and install Zed for Windows:

1. Visit [https://zed.dev](https://zed.dev)
2. Download the Windows installer
3. Run the installer and follow the prompts

Or use the command line:

```powershell
# Using winget (Windows Package Manager)
winget install Zed.Zed
```

**Step 4: Configure Zed for WSL**

Launch Zed on Windows, then:

1. Open the Command Palette: `Ctrl + Shift + P`
2. Type "WSL" and select "Open Folder in WSL"
3. Navigate to your project directory in WSL (typically under `/home/yourusername/`)

Alternatively, you can configure Zed to always use WSL:

1. Open Settings: `Ctrl + ,`
2. Search for "terminal"
3. Set the default shell to WSL

**Step 5: Verify WSL connection**

Open the integrated terminal in Zed (`Ctrl + `` ` ``) and verify you're in WSL:

```bash
# Check if you're in WSL
uname -a
# Should show Linux

# Check your location
pwd
# Should show a path like /home/yourusername/
```

### macOS Installation

Installing Zed on macOS is straightforward:

```bash
# Using Homebrew
brew install zed

# Or download directly from https://zed.dev
```

After installation, launch Zed:

```bash
# Open current directory
zed .

# Or open a specific folder
zed /path/to/project
```

Create a convenient alias:

```bash
# Add to ~/.zshrc
echo 'alias z="zed ."' >> ~/.zshrc
source ~/.zshrc
```

### Linux Installation

For Linux systems, Zed can be installed via the official script:

```bash
# Download and install Zed
curl -f https://zed.dev/install.sh | sh

# The installer will add Zed to your PATH automatically
```

If needed, manually add to PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Launch Zed:

```bash
zed .
```

## Setting Up Claude Code with Zed

Claude Code is a command-line tool that lets you delegate coding tasks directly to Claude from your terminal.

### Installation

**On Windows (in WSL):**

```bash
# Open WSL terminal in Zed (Ctrl + `)
# Install Node.js if not already installed
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Claude Code
npm install -g @anthropic-ai/claude-code
```

**On macOS:**

```bash
# Install using npm
npm install -g @anthropic-ai/claude-code

# Or using Homebrew (if available)
brew install claude-code
```

**On Linux:**

```bash
# Install Node.js first (if needed)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Claude Code
npm install -g @anthropic-ai/claude-code
```

### Configuration

After installation, configure Claude Code with your API key:

```bash
# Interactive configuration
claude-code configure

# You'll be prompted to enter your Anthropic API key
# Get your API key from: https://console.anthropic.com/
```

Or set the environment variable directly:

```bash
# For bash (Linux/WSL)
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# For zsh (macOS)
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Using Claude Code with Zed

**Step 1: Open your project in Zed**

On Windows, open Zed and connect to WSL:
- Press `Ctrl + Shift + P`
- Select "Open Folder in WSL"
- Navigate to your project

On macOS/Linux:
```bash
cd your-project-directory
zed .
```

**Step 2: Open the integrated terminal**

Press `Ctrl + `` ` `` (backtick) to open the terminal

**Step 3: Run Claude Code commands**

```bash
# Ask Claude to implement a feature
claude-code "Add user authentication to the Express app"

# Request code review
claude-code "Review the code in src/auth.js and suggest improvements"

# Debug an issue
claude-code "Fix the bug causing the login form to crash on submission"

# Refactor code
claude-code "Refactor the database queries to use async/await"

# Generate tests
claude-code "Create unit tests for all functions in utils/validation.js"

# Add documentation
claude-code "Add comprehensive JSDoc comments to all functions in this file"
```

**Step 4: Review changes in Zed**

Claude Code will modify files in your project. Zed automatically detects these changes:

- Files with changes will be highlighted in the file tree
- View diffs by clicking on modified files
- Use `Ctrl + Z` to undo changes if needed
- Navigate between files with `Ctrl + P`

### Advanced Claude Code Workflow

**Interactive mode for conversations:**

```bash
# Start an interactive session
claude-code --interactive

# Have a back-and-forth conversation
> Add error handling to the API routes
> Now add logging for all errors
> Create a custom error class for better error management
> Add unit tests for the error handling
```

**Working with specific files:**

```bash
# Focus on specific files
claude-code --files "src/auth/*.js" "Add input validation to all authentication functions"

# Work with multiple file patterns
claude-code --files "src/**/*.ts" "Convert to use TypeScript strict mode"
```

**Providing context:**

```bash
# Include additional context
claude-code --context "We're using Express.js 4.18 and MongoDB" "Create a user authentication system"
```

## Setting Up Gemini CLI with Zed

Gemini CLI is Google's command-line interface for interacting with Gemini AI models.

### Installation

**On Windows (in WSL):**

```bash
# In Zed's WSL terminal
# Install Python and pip if not already installed
sudo apt update
sudo apt install python3 python3-pip -y

# Install Gemini CLI
pip3 install google-generativeai
```

**On macOS:**

```bash
# Using pip
pip3 install google-generativeai

# Or using Homebrew Python
brew install python3
pip3 install google-generativeai
```

**On Linux:**

```bash
# Install pip if needed
sudo apt update
sudo apt install python3-pip -y

# Install Gemini CLI
pip3 install google-generativeai
```

### Configuration

Set up your Google API key:

```bash
# Set environment variable
export GOOGLE_API_KEY='your-api-key-here'

# Make it persistent
# For bash (Linux/WSL)
echo 'export GOOGLE_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# For zsh (macOS)
echo 'export GOOGLE_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

### Using Gemini CLI with Zed

**Basic usage in Zed's terminal:**

```bash
# Chat with Gemini
python3 -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('How do I optimize React performance?')
print(response.text)
"
```

**Create a helper script for easier use:**

Create a file called `gemini.py` in your project root:

```python
#!/usr/bin/env python3
import google.generativeai as genai
import os
import sys

genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

if len(sys.argv) < 2:
    print("Usage: python3 gemini.py 'your prompt here'")
    sys.exit(1)

prompt = ' '.join(sys.argv[1:])
response = model.generate_content(prompt)
print(response.text)
```

Make it executable:

```bash
chmod +x gemini.py

# Now use it easily
./gemini.py "Explain async/await in JavaScript"
./gemini.py "Review this code for security issues"
```

**Using Gemini for code analysis:**

```bash
# Analyze a file
./gemini.py "Review the code in $(cat src/app.js) and suggest improvements"

# Get explanations
./gemini.py "Explain what this function does: $(cat src/utils/helpers.js)"

# Generate documentation
./gemini.py "Create API documentation for: $(cat src/routes/api.js)"
```

## Optimal Workflow: Zed + AI CLI Tools

Here's how to create an efficient development workflow combining Zed with AI CLI tools:

### 1. **Project Structure Setup**

For Windows users, organize your projects in WSL for best performance:

```bash
# In WSL terminal (via Zed)
mkdir -p ~/projects
cd ~/projects

# Clone or create your project here
git clone your-repo-url
cd your-project

# Open in Zed (if not already open)
# The Windows Zed instance will access WSL files seamlessly
```

### 2. **Split-Screen Setup in Zed**

Configure Zed for maximum efficiency:

- Keep your code in the main editor pane
- Open terminal with `Ctrl + `` ` ``
- Resize terminal to your preference (drag the divider)
- Use `Ctrl + `` ` `` to toggle terminal visibility quickly

### 3. **Version Control Integration**

Always use Git with AI-generated changes:

```bash
# Before running AI commands
git status
git add .
git commit -m "Pre-AI changes: Starting feature X"

# Run your AI CLI tool
claude-code "Implement feature X"

# Review changes in Zed
git diff

# Stage and review file by file if needed
git add -p

# Commit if satisfied
git commit -m "AI: Implemented feature X with Claude Code"

# Or rollback if needed
git reset --hard HEAD^
```

### 4. **Iterative Development with AI**

Use AI CLI tools iteratively for best results:

```bash
# Step 1: Initial implementation
claude-code "Create a REST API for user management with Express.js"

# Step 2: Review in Zed, test manually, then refine
claude-code "Add input validation using Joi to all endpoints"

# Step 3: Add tests
claude-code "Generate Jest integration tests for the user API"

# Step 4: Get alternative perspective
./gemini.py "Review the API implementation in src/routes/users.js and suggest optimizations"

# Step 5: Implement optimizations
claude-code "Implement the suggested optimizations: [paste Gemini's suggestions]"
```

### 5. **Combining Claude Code and Gemini CLI**

Leverage the strengths of both tools:

```bash
# Use Claude Code for implementation (better at following project patterns)
claude-code "Build a JWT-based authentication system"

# Use Gemini for documentation and explanations
./gemini.py "Create comprehensive README documentation for the auth system in src/auth/"

# Use Claude Code for refactoring (better at complex code changes)
claude-code "Refactor auth code to separate concerns into middleware, controllers, and services"

# Use Gemini for quick questions and learning
./gemini.py "What are the security best practices for JWT tokens?"

# Use Claude Code for test generation
claude-code "Generate comprehensive unit and integration tests for all auth modules"
```

### 6. **Essential Zed Keyboard Shortcuts**

Master these shortcuts for faster workflows:

**Navigation:**
- `Ctrl + P` - Quick file navigation (fuzzy search)
- `Ctrl + Shift + F` - Search across entire project
- `Ctrl + G` - Go to line number
- `Ctrl + Click` - Go to definition

**Editing:**
- `Ctrl + D` - Select next occurrence of current word
- `Ctrl + Shift + L` - Select all occurrences
- `Alt + Up/Down` - Move line up/down
- `Ctrl + Shift + K` - Delete line
- `Ctrl + /` - Toggle comment

**Terminal:**
- `Ctrl + `` ` `` - Toggle terminal
- `Ctrl + Shift + `` ` `` - Create new terminal
- `Ctrl + Shift + C` - Copy from terminal
- `Ctrl + Shift + V` - Paste into terminal

**Command Palette:**
- `Ctrl + Shift + P` - Open command palette (access all Zed commands)

**Multi-cursor:**
- `Alt + Click` - Add cursor at click position
- `Ctrl + Alt + Up/Down` - Add cursor above/below

## Platform-Specific Tips

### Windows with WSL

**Best practices for Windows + WSL + Zed:**

```bash
# Keep projects in WSL filesystem for best performance
# Good: ~/projects/myapp
# Avoid: /mnt/c/Users/YourName/projects/myapp

# Access Windows files when needed
cd /mnt/c/Users/YourName/Downloads

# But copy them to WSL for active development
cp -r /mnt/c/Users/YourName/Downloads/project ~/projects/
cd ~/projects/project
```

**Configure Git in WSL:**

```bash
# Set up Git credentials
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Use Windows Credential Manager from WSL
git config --global credential.helper "/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe"
```

**Improve WSL performance:**

Create or edit `C:\Users\YourName\.wslconfig`:

```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
localhostForwarding=true
```

Restart WSL:

```powershell
# In PowerShell
wsl --shutdown
# Then reopen WSL
```

### macOS

**Create useful aliases:**

```bash
# Add to ~/.zshrc
echo 'alias z="zed ."' >> ~/.zshrc
echo 'alias cc="claude-code"' >> ~/.zshrc
echo 'alias g="./gemini.py"' >> ~/.zshrc
source ~/.zshrc

# Now you can use:
# z - Open current directory in Zed
# cc "prompt" - Run Claude Code
# g "prompt" - Run Gemini
```

**Install developer tools:**

```bash
# Install Xcode Command Line Tools if needed
xcode-select --install

# Keep tools updated
brew update
brew upgrade
```

### Linux

**Install build essentials:**

```bash
# Ensure you have necessary build tools
sudo apt update
sudo apt install build-essential git curl -y
```

**Configure GPU acceleration:**

```bash
# For better Zed performance, ensure GPU drivers are current
sudo ubuntu-drivers autoinstall

# Check GPU status
nvidia-smi  # For NVIDIA
glxinfo | grep "OpenGL"  # For general info
```

## Troubleshooting

### Zed Issues

**Zed won't connect to WSL (Windows):**

```bash
# Ensure WSL 2 is running
wsl --list --verbose
# Should show version 2

# Restart WSL if needed
wsl --shutdown
# Then reopen WSL from Zed
```

**Zed won't launch (macOS/Linux):**

```bash
# Check installation
which zed

# Reinstall if needed
curl -f https://zed.dev/install.sh | sh

# Check permissions
ls -la $(which zed)
```

**Slow performance:**

```bash
# On WSL: Move project to WSL filesystem
mv /mnt/c/Users/YourName/project ~/projects/

# Clear Zed cache
# Close Zed, then delete cache directory
# Windows: %APPDATA%\Zed
# macOS: ~/Library/Application Support/Zed
# Linux: ~/.config/zed
```

### Claude Code Issues

**API key errors:**

```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Should show your key, if empty:
export ANTHROPIC_API_KEY='your-key-here'

# Make permanent (Linux/WSL)
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc

# Test Claude Code
claude-code "Say hello"
```

**Command not found:**

```bash
# Check if npm global bin is in PATH
echo $PATH | grep npm

# If not, add it
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or reinstall
npm install -g @anthropic-ai/claude-code
```

**Rate limiting:**

```bash
# Check your API usage at console.anthropic.com
# If rate limited, wait or upgrade your plan
# You can also use --delay flag
claude-code --delay 2000 "your prompt"
```

### Gemini CLI Issues

**Import errors:**

```bash
# Ensure google-generativeai is installed
pip3 list | grep google-generativeai

# Reinstall if needed
pip3 install --upgrade google-generativeai

# Check Python version (needs 3.8+)
python3 --version
```

**API key not recognized:**

```bash
# Verify key is set
echo $GOOGLE_API_KEY

# Test the API key with Python
python3 -c "import os; print('Key found' if os.environ.get('GOOGLE_API_KEY') else 'Key not found')"

# Set if missing
export GOOGLE_API_KEY='your-key-here'
```

**Connection errors:**

```bash
# Test internet connectivity
ping -c 3 google.com

# Check firewall settings (on corporate networks)
# May need to configure proxy

# Try alternative model
# In your gemini.py, change to:
# model = genai.GenerativeModel('gemini-1.5-flash')
```

### WSL-Specific Issues

**File permission errors:**

```bash
# Fix file permissions
chmod -R 755 ~/projects/your-project

# Ensure you own the files
sudo chown -R $USER:$USER ~/projects/your-project
```

**Network issues in WSL:**

```bash
# Reset network in WSL
wsl --shutdown
# Restart WSL

# Or reset networking
sudo rm /etc/resolv.conf
sudo bash -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'
```

## Best Practices

### 1. Always Review AI-Generated Code

AI tools are powerful assistants, not replacements for human judgment:

- Read through every change before committing
- Test the functionality thoroughly
- Check for security vulnerabilities
- Ensure code follows your project's style guide
- Verify that dependencies are properly managed

### 2. Use Descriptive and Contextual Prompts

The quality of AI output depends heavily on input:

```bash
# Poor prompt
claude-code "Add validation"

# Good prompt
claude-code "Add validation to the user registration form in src/components/RegisterForm.jsx using Yup schema. Validate: email format, password strength (min 8 chars, 1 uppercase, 1 number), and username length (3-20 chars)"

# Excellent prompt with context
claude-code "Add validation to the user registration form in src/components/RegisterForm.jsx. We're using Formik + Yup. Validate: email format, password strength (min 8 chars, 1 uppercase, 1 number, 1 special char), username (3-20 chars, alphanumeric only), and terms acceptance. Display validation errors inline below each field. Match the existing error styling in src/styles/forms.css"
```

### 3. Maintain Version Control Discipline

```bash
# Create feature branches for AI work
git checkout -b feature/ai-authentication

# Commit in logical chunks
git add src/auth/
git commit -m "AI: Add authentication middleware"

git add tests/auth/
git commit -m "AI: Add authentication tests"

# Easy to revert specific changes if needed
git revert <commit-hash>
```

### 4. Keep Tools Updated

```bash
# Update Zed (Windows: use winget or download)
# macOS
brew upgrade zed

# Linux
curl -f https://zed.dev/install.sh | sh

# Update Claude Code
npm update -g @anthropic-ai/claude-code

# Update Gemini CLI
pip3 install --upgrade google-generativeai

# Update WSL (Windows)
wsl --update
```

### 5. Leverage Both AI Tools Strategically

Use each tool for its strengths:

**Claude Code excels at:**
- Complex code refactoring
- Following project patterns and conventions
- Multi-file changes
- Maintaining consistency with existing code
- Understanding nuanced requirements

**Gemini CLI excels at:**
- Quick explanations and learning
- Multimodal tasks (when extended)
- Documentation generation
- Alternative perspectives
- Rapid prototyping ideas

### 6. Create Project-Specific AI Guidelines

Create a `.ai-guidelines.md` in your project:

```markdown
# AI Development Guidelines for [Project Name]

## Code Style
- Use ES6+ JavaScript
- Prefer functional components and hooks
- Use async/await over promises
- Follow Airbnb style guide

## Testing
- Write Jest tests for all new functions
- Maintain 80%+ code coverage
- Include edge cases

## Security
- Always validate user input
- Use parameterized queries for database
- Implement rate limiting on APIs

## When using Claude Code or Gemini:
- Always mention we're using [framework/library versions]
- Reference existing patterns in src/patterns/
- Maintain TypeScript strict mode
```

Then reference it in prompts:

```bash
claude-code "Following the guidelines in .ai-guidelines.md, implement a user search feature"
```

### 7. Use Zed's Features Fully

```bash
# Create custom keybindings
# Zed > Settings > Keymap
# Add shortcuts for frequent AI commands

# Use Zed's project search to verify AI changes
# Ctrl + Shift + F to find all occurrences

# Leverage Zed's multi-cursor for manual tweaks
# Select matching text with Ctrl + D

# Use Zed's integrated Git features
# View changes, stage hunks, commit from editor
```

## Advanced Workflows

### Automated Code Review Pipeline

Create a review script `ai-review.sh`:

```bash
#!/bin/bash
# Review all changed files with both AI tools

echo "Running AI code review..."

# Get list of changed files
FILES=$(git diff --name-only)

# Review with Claude
echo "=== Claude Code Review ===" > review.md
claude-code "Review these files for bugs, security issues, and improvements: $FILES" >> review.md

# Get Gemini's perspective
echo -e "\n\n=== Gemini Review ===" >> review.md
./gemini.py "Review the following files for code quality and suggest optimizations: $(git diff)" >> review.md

echo "Review complete! Check review.md"
```

### Continuous AI-Assisted Development

```bash
# Watch mode for AI assistance
# Create watch-and-improve.sh

#!/bin/bash
# Monitors file changes and offers AI improvements

while true; do
    inotifywait -e modify src/
    echo "Files changed. Run AI review? (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        claude-code "Review the recent changes and suggest improvements"
    fi
done
```

### Team Collaboration with AI

```bash
# Share AI prompts in your project
mkdir .ai-prompts

# Create reusable prompt templates
echo "Add unit tests for: [FILE]" > .ai-prompts/add-tests.txt
echo "Refactor [FILE] to improve readability" > .ai-prompts/refactor.txt
echo "Add error handling to: [FILE]" > .ai-prompts/error-handling.txt

# Use them consistently
claude-code "$(cat .ai-prompts/add-tests.txt | sed 's/\[FILE\]/src\/auth.js/')"
```

## Conclusion

Zed IDE, combined with AI CLI tools like Claude Code and Gemini CLI, represents a powerful evolution in software development. This setup gives you:

- **Speed**: Zed's performance keeps you in flow state
- **Intelligence**: AI tools augment your capabilities
- **Flexibility**: Works seamlessly across Windows (via WSL), macOS, and Linux
- **Simplicity**: Minimal setup, maximum productivity

The key to success is treating AI as a collaborative partner, not a replacement. Review everything, maintain good development practices, and use version control religiously. Start with simple tasks, build confidence, and gradually integrate these tools into your daily workflow.

Whether you're building a new feature, refactoring legacy code, or learning a new technology, this combination of Zed and AI CLI tools will accelerate your development while maintaining quality and control.

Happy coding with AI! 🚀