# Complete IDE Tutorial: VS Code, Cursor & Zed

## Table of Contents
1. [Introduction to Modern Code Editors](#introduction)
2. [Visual Studio Code (VS Code)](#vscode)
3. [Cursor](#cursor)
4. [Zed](#zed)
5. [Comparison and Recommendations](#comparison)
6. [Essential Extensions and Plugins](#extensions)
7. [Configuration and Customization](#configuration)
8. [Keyboard Shortcuts](#shortcuts)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Introduction to Modern Code Editors {#introduction}

### What Are These Editors?

**Visual Studio Code (VS Code)**
- Free, open-source editor by Microsoft
- Most popular code editor worldwide
- Extensive extension marketplace
- Excellent for all programming languages
- Strong remote development capabilities

**Cursor**
- AI-first code editor
- Fork of VS Code with built-in AI features
- ChatGPT-like interface in your editor
- AI-powered code generation and editing
- Compatible with VS Code extensions

**Zed**
- Ultra-fast, modern code editor
- Built in Rust for performance
- Collaborative editing built-in
- Minimalist and efficient
- Newer but rapidly growing

### Which Should You Use?

**Choose VS Code if:**
- You want the most mature, stable editor
- You need extensive extension ecosystem
- You're learning or working professionally
- You need maximum compatibility

**Choose Cursor if:**
- You want AI assistance while coding
- You work with AI/LLM development
- You're comfortable with newer tools
- You want VS Code familiarity + AI power

**Choose Zed if:**
- You prioritize speed and performance
- You like minimalist interfaces
- You collaborate in real-time often
- You're on macOS or Linux (limited Windows support)

---

## Visual Studio Code (VS Code) {#vscode}

### Installation

#### Windows (WSL)

**Method 1: Install on Windows, use with WSL (Recommended)**

1. **Download VS Code for Windows:**
   - Visit [code.visualstudio.com](https://code.visualstudio.com)
   - Download Windows installer (.exe)
   - Run installer with default options
   - **Important:** Check "Add to PATH" during installation

2. **Install WSL Extension:**
   - Open VS Code on Windows
   - Press `Ctrl+Shift+X` to open Extensions
   - Search for "WSL"
   - Install "WSL" extension by Microsoft

3. **Connect to WSL:**
   ```bash
   # Open WSL terminal
   wsl
   
   # Navigate to your project
   cd ~/projects/my-project
   
   # Open VS Code connected to WSL
   code .
   ```

   Or click the green button in bottom-left corner → "Connect to WSL"

**Method 2: Install VS Code inside WSL**

```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install wget gpg

# Add Microsoft GPG key
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg

# Add VS Code repository
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'

# Install VS Code
sudo apt update
sudo apt install code

# Launch
code .
```

#### macOS

**Method 1: Download from Website**
1. Visit [code.visualstudio.com](https://code.visualstudio.com)
2. Download for macOS (.zip)
3. Unzip and drag to Applications folder
4. Open VS Code from Applications

**Method 2: Install via Homebrew**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install VS Code
brew install --cask visual-studio-code

# Launch from terminal
code .
```

**Add to PATH (if needed):**
1. Open VS Code
2. Press `Cmd+Shift+P`
3. Type "shell command"
4. Select "Shell Command: Install 'code' command in PATH"

#### Linux

**Ubuntu/Debian:**
```bash
# Method 1: Using official repository
sudo apt update
sudo apt install wget gpg
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code

# Method 2: Download .deb package
wget https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64 -O vscode.deb
sudo dpkg -i vscode.deb
sudo apt-get install -f  # Fix dependencies if needed
```

**Fedora/RHEL/CentOS:**
```bash
# Add repository
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'

# Install
sudo dnf install code
# Or on older systems:
sudo yum install code
```

**Arch Linux:**
```bash
# Install from AUR
yay -S visual-studio-code-bin
# Or
paru -S visual-studio-code-bin
```

### Getting Started with VS Code

#### First Launch

1. **Welcome Screen:**
   - Choose your theme (Dark+, Light+, etc.)
   - Install language support if prompted

2. **Open a Folder:**
   ```bash
   # From terminal
   code /path/to/project
   
   # Or in VS Code: File → Open Folder
   ```

3. **Basic Interface:**
   - **Activity Bar** (left): Explorer, Search, Source Control, Debug, Extensions
   - **Side Bar**: Shows selected activity's content
   - **Editor**: Where you write code
   - **Panel** (bottom): Terminal, Output, Problems, Debug Console
   - **Status Bar** (bottom): Git branch, errors, language mode

#### Essential Features

**Integrated Terminal:**
```bash
# Open terminal: Ctrl+` (backtick) or View → Terminal
# In WSL: Automatically uses WSL bash
# Multiple terminals: Click + icon
# Split terminal: Click split icon
```

**Command Palette:**
- Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
- Access all VS Code commands
- Try: "Format Document", "Change Language Mode", "Git: Commit"

**File Explorer:**
- Click Explorer icon in Activity Bar
- Right-click for context menu
- Create files/folders
- Drag and drop to move

**Search Across Files:**
- Click Search icon or `Ctrl+Shift+F`
- Search and replace across entire project
- Use regex, case-sensitive, whole word options

**Source Control (Git):**
- Click Source Control icon
- View changes
- Stage files (click +)
- Write commit message
- Click ✓ to commit

### Essential VS Code Extensions

Install via Extensions view (`Ctrl+Shift+X`):

**For Python Development:**
```
1. Python (by Microsoft)
2. Pylance (by Microsoft)
3. Python Debugger (by Microsoft)
4. autoDocstring
5. Black Formatter
```

**For Web Development:**
```
1. ESLint
2. Prettier - Code formatter
3. Live Server
4. Auto Rename Tag
5. Path Intellisense
```

**For AI/ML Development:**
```
1. Jupyter
2. Jupyter Keymap
3. Jupyter Notebook Renderers
4. Rainbow CSV
5. Data Wrangler
```

**General Productivity:**
```
1. GitLens — Git supercharged
2. Docker
3. Remote - SSH
4. Live Share (real-time collaboration)
5. Todo Tree
6. Error Lens
7. Bracket Pair Colorizer (or use built-in)
```

### Using VS Code with WSL

**Why Use VS Code with WSL?**
- Edit files in Linux filesystem
- Run Linux tools and compilers
- Better performance than editing Windows files
- True Linux development environment

**Workflow:**
```bash
# In WSL terminal
cd ~/projects/my-ai-agent
code .

# VS Code opens, connected to WSL
# Bottom-left shows: "WSL: Ubuntu"
# Terminal uses bash automatically
# Extensions run in WSL context
```

**Installing Extensions in WSL:**
- Some extensions install in WSL, some in Windows
- Python, Git, etc. should install in WSL
- VS Code will prompt you where to install

### Basic VS Code Settings

Press `Ctrl+,` to open Settings, or edit JSON directly:

**settings.json** (Ctrl+Shift+P → "Preferences: Open Settings (JSON)"):
```json
{
    "editor.fontSize": 14,
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "editor.formatOnSave": true,
    "editor.rulers": [80, 120],
    "editor.minimap.enabled": true,
    "editor.bracketPairColorization.enabled": true,
    "editor.guides.bracketPairs": true,
    
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000,
    "files.trimTrailingWhitespace": true,
    
    "terminal.integrated.fontSize": 13,
    "terminal.integrated.defaultProfile.linux": "bash",
    
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    
    "git.autofetch": true,
    "git.confirmSync": false,
    
    "workbench.colorTheme": "Default Dark+",
    "workbench.iconTheme": "vs-seti"
}
```

---

## Cursor {#cursor}

### What Makes Cursor Special?

Cursor is a fork of VS Code with AI deeply integrated:
- **AI Chat**: ChatGPT-like interface in your editor
- **Inline Editing**: AI suggests code as you type
- **Codebase Understanding**: AI knows your entire project
- **Multi-file Edits**: AI can edit multiple files at once
- **Command K**: Quick AI commands

### Installation

#### Windows (WSL)

1. **Download Cursor:**
   - Visit [cursor.sh](https://cursor.sh)
   - Download Windows installer
   - Run installer

2. **Using with WSL:**
   ```bash
   # In WSL terminal
   cd ~/projects
   cursor .
   
   # Or open Cursor and connect to WSL
   # Click bottom-left → "Connect to WSL"
   ```

#### macOS

**Method 1: Download**
1. Visit [cursor.sh](https://cursor.sh)
2. Download for macOS
3. Unzip and drag to Applications
4. Open from Applications

**Method 2: Homebrew**
```bash
brew install --cask cursor

# Launch
cursor .
```

**Add to PATH:**
1. Open Cursor
2. Cmd+Shift+P
3. "Shell Command: Install 'cursor' command in PATH"

#### Linux

**Ubuntu/Debian:**
```bash
# Download AppImage
wget https://downloader.cursor.sh/linux/appImage/x64 -O cursor.AppImage

# Make executable
chmod +x cursor.AppImage

# Run
./cursor.AppImage

# Or install system-wide
sudo mv cursor.AppImage /usr/local/bin/cursor
```

**Arch Linux:**
```bash
# From AUR
yay -S cursor-appimage
```

### Getting Started with Cursor

#### First Launch

1. **Sign In:**
   - Create account or use GitHub/Google
   - Free tier available, paid plans for more usage

2. **Import VS Code Settings:**
   - Cursor will ask if you want to import VS Code settings
   - Recommended: Yes (brings extensions, settings, keybindings)

3. **Interface:**
   - Identical to VS Code
   - Additional AI chat panel on right

#### Using AI Features

**AI Chat (Ctrl+L or Cmd+L):**
```
You: "How do I read a CSV file in Python?"

Cursor AI: Here's how to read a CSV file in Python:
[Shows code with pandas or csv module]

You: "Add error handling"

Cursor AI: [Updates code with try-except blocks]
```

**Inline AI (Ctrl+K or Cmd+K):**
```python
# Type this comment:
# Function to validate email address

# Press Ctrl+K, AI generates:
def validate_email(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

**Chat with Codebase:**
```
You: "@codebase How does the authentication work?"

Cursor: [Analyzes your entire codebase and explains]

You: "Where is the login function?"

Cursor: [Shows exact file and line numbers]
```

**Multi-file Editing:**
```
You: "Refactor the User class to use dataclasses across all files"

Cursor: [Modifies multiple files, shows diff for each]
```

**Command K Quick Actions:**
- Select code → Press Ctrl+K
- Type: "Add type hints"
- Type: "Write unit tests"
- Type: "Explain this code"
- Type: "Optimize this function"

### Cursor-Specific Features

**Codebase Indexing:**
- Cursor indexes your entire project
- AI understands relationships between files
- Better suggestions based on your code style

**AI Models:**
- Settings → Cursor → AI Model
- Choose: GPT-4, Claude, etc.
- Switch models for different tasks

**Privacy Settings:**
- Settings → Cursor → Privacy
- Control what code is sent to AI
- Enable "Privacy Mode" for sensitive code

### Cursor Configuration

**cursor.settings.json:**
```json
{
    // All VS Code settings work
    "cursor.aiEnabled": true,
    "cursor.aiModel": "gpt-4",
    "cursor.aiCodeCompletion": true,
    "cursor.privacyMode": false,
    
    // VS Code settings
    "editor.fontSize": 14,
    "editor.formatOnSave": true,
    "workbench.colorTheme": "Default Dark+"
}
```

### Best Practices with Cursor

1. **Be Specific in Prompts:**
   ```
   ❌ "Fix this"
   ✅ "Add input validation to check that age is between 0 and 150"
   ```

2. **Use @codebase for Context:**
   ```
   ✅ "@codebase How should I implement the new payment method?"
   ```

3. **Review AI Suggestions:**
   - AI is helpful but not perfect
   - Always review generated code
   - Test thoroughly

4. **Iterate:**
   ```
   You: "Create login function"
   AI: [Generates basic function]
   You: "Add JWT authentication"
   AI: [Adds JWT]
   You: "Add refresh token"
   AI: [Adds refresh token logic]
   ```

---

## Zed {#zed}

### What Makes Zed Special?

- **Blazing Fast**: Built in Rust, instant startup
- **Collaborative**: Built-in real-time collaboration
- **Minimalist**: Clean, distraction-free interface
- **Modern**: Takes advantage of latest technologies
- **AI-Powered**: Built-in AI assistant

### Installation

#### macOS (Primary Platform)

**Method 1: Download**
1. Visit [zed.dev](https://zed.dev)
2. Download for macOS
3. Unzip and drag to Applications
4. Open from Applications

**Method 2: Homebrew**
```bash
brew install --cask zed

# Launch
zed .
```

#### Linux

**Ubuntu/Debian:**
```bash
# Download from website
wget https://zed.dev/api/releases/stable/latest/zed-linux-x86_64.tar.gz

# Extract
tar -xzf zed-linux-x86_64.tar.gz

# Move to /usr/local/bin
sudo mv zed /usr/local/bin/

# Launch
zed .
```

**Arch Linux:**
```bash
# From AUR
yay -S zed-git
```

**From Source:**
```bash
# Install Rust if not installed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Clone and build
git clone https://github.com/zed-industries/zed.git
cd zed
cargo build --release

# Run
./target/release/zed
```

#### Windows (Limited Support)

Currently, Zed has limited Windows support. Use WSL:

```bash
# In WSL
# Follow Linux installation instructions
# Or use VS Code/Cursor for now
```

### Getting Started with Zed

#### First Launch

1. **Welcome Screen:**
   - Clean, minimal interface
   - No overwhelming options

2. **Sign In (Optional):**
   - Sign in for collaboration features
   - GitHub authentication

3. **Interface:**
   - **Project Panel** (left): File tree
   - **Editor**: Central area
   - **Terminal**: Integrated
   - **AI Assistant**: Right panel

#### Basic Operations

**Open Project:**
```bash
# From terminal
zed /path/to/project

# Or: File → Open Folder
```

**Command Palette:**
- Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Linux)
- Access all commands
- Very responsive

**Fuzzy File Search:**
- Press `Cmd+P` (Mac) or `Ctrl+P` (Linux)
- Type filename
- Instant results

**Multi-cursor:**
- `Cmd+Click` (Mac) or `Ctrl+Click` (Linux) to add cursor
- `Cmd+D` to select next occurrence
- Edit multiple places simultaneously

### Collaboration Features

**Start Collaboration:**
1. Click "Share" in top-right
2. Share link with collaborators
3. See their cursors in real-time
4. Edit together simultaneously

**Join Collaboration:**
1. Receive collaboration link
2. Click to join
3. See project and other collaborators

**Benefits:**
- No setup required
- No port forwarding
- Works anywhere
- Low latency

### Zed AI Assistant

**Activate Assistant:**
- Press `Cmd+?` (Mac) or `Ctrl+?` (Linux)
- AI panel opens on right

**Using AI:**
```
You: "Write a function to parse JSON"

Zed AI: [Generates code in editor]

You: "Add error handling"

Zed AI: [Updates code]
```

**Inline Assistance:**
- Select code
- Ask AI to explain, refactor, or optimize
- AI suggests changes inline

### Zed Configuration

**Settings Location:**
- macOS: `~/.config/zed/settings.json`
- Linux: `~/.config/zed/settings.json`

**Example settings.json:**
```json
{
    "theme": "One Dark",
    "buffer_font_family": "JetBrains Mono",
    "buffer_font_size": 14,
    "ui_font_size": 14,
    "tab_size": 4,
    "soft_wrap": "editor_width",
    "show_whitespaces": "selection",
    "autosave": "on_focus_change",
    "format_on_save": "on",
    "terminal": {
        "shell": "bash",
        "font_family": "JetBrains Mono",
        "font_size": 13
    },
    "lsp": {
        "rust-analyzer": {
            "initialization_options": {
                "checkOnSave": {
                    "command": "clippy"
                }
            }
        },
        "pyright": {
            "settings": {
                "python.analysis.typeCheckingMode": "basic"
            }
        }
    },
    "git": {
        "git_gutter": "tracked_files"
    },
    "collaboration_panel": {
        "button": true
    }
}
```

### Language Support

Zed uses Language Server Protocol (LSP):

**Automatic Setup:**
- Zed auto-installs language servers
- Open a Python file → Python LSP installs
- Open a Rust file → rust-analyzer installs

**Supported Languages:**
- Python, JavaScript/TypeScript, Rust
- Go, C/C++, Java, Ruby
- And many more

### Keyboard Shortcuts (Zed)

**Navigation:**
- `Cmd+P`: File finder
- `Cmd+Shift+P`: Command palette
- `Cmd+B`: Toggle project panel
- `Cmd+J`: Toggle terminal

**Editing:**
- `Cmd+D`: Select next occurrence
- `Cmd+/`: Toggle comment
- `Cmd+Shift+F`: Format document
- `Cmd+Click`: Add cursor

**Search:**
- `Cmd+F`: Find in file
- `Cmd+Shift+F`: Find in project
- `Cmd+E`: Go to symbol

### Themes and Appearance

**Built-in Themes:**
- One Dark
- Solarized Dark/Light
- Gruvbox
- Dracula
- Many more

**Change Theme:**
1. `Cmd+Shift+P`
2. Type "theme"
3. Select "Theme: Switch Theme"
4. Choose from list

---

## Comparison and Recommendations {#comparison}

### Feature Comparison

| Feature | VS Code | Cursor | Zed |
|---------|---------|--------|-----|
| **Performance** | Good | Good | Excellent |
| **Extensions** | 50,000+ | VS Code compatible | Growing |
| **AI Features** | Via extensions | Built-in, excellent | Built-in, good |
| **Collaboration** | Via Live Share | Via Live Share | Built-in, excellent |
| **Stability** | Excellent | Very Good | Good |
| **Platform Support** | All | All | Mac/Linux |
| **Learning Curve** | Easy | Easy | Easy |
| **Cost** | Free | Free + Paid tiers | Free |
| **Remote Dev** | Excellent | Excellent | Limited |
| **Customization** | Extensive | Extensive | Moderate |

### Use Case Recommendations

**For Beginners:**
→ **VS Code**: Most documentation, largest community, most stable

**For AI/LLM Development:**
→ **Cursor**: Best AI integration, understands codebases, great for agent development

**For Speed Enthusiasts:**
→ **Zed**: Fastest startup and performance, minimal distraction

**For Professional Teams:**
→ **VS Code**: Industry standard, best tooling, enterprise support

**For Solo Developers:**
→ **Cursor** or **Zed**: Modern features, great productivity

**For Pair Programming:**
→ **Zed**: Built-in collaboration beats all

### My Workflow Recommendation

**Use Multiple Editors:**
1. **VS Code**: Primary for most projects, especially with complex tooling
2. **Cursor**: For AI-heavy tasks, prototyping, learning new codebases
3. **Zed**: For quick edits, collaboration sessions, distraction-free coding

**They coexist well:**
- All use similar keybindings
- Cursor imports VS Code settings
- Zed has familiar interface
- Switch based on task

---

## Essential Extensions and Plugins {#extensions}

### VS Code Essential Extensions

**Install via Command Line:**
```bash
# Python
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.debugpy

# Git
code --install-extension eamodio.gitlens

# General
code --install-extension esbenp.prettier-vscode
code --install-extension dbaeumer.vscode-eslint
code --install-extension ms-vscode-remote.remote-wsl
code --install-extension ms-vscode.live-server
```

**AI Extensions for VS Code:**
```
1. GitHub Copilot (paid)
2. Tabnine (freemium)
3. Codeium (free)
4. Continue (free, open-source)
```

### Cursor Extensions

Cursor uses VS Code extensions:
- Most VS Code extensions work
- Install from Extensions marketplace
- Some AI extensions may conflict with built-in AI

### Zed Extensions

**Built-in Language Support:**
- Most languages work out of box
- Extensions system is newer
- Growing ecosystem

**Install Extensions:**
1. `Cmd+Shift+P`
2. "Extensions: Install Extension"
3. Browse and install

---

## Configuration and Customization {#configuration}

### Unified Settings Approach

All three editors use JSON configuration:

**settings.json locations:**
- **VS Code**: `~/.config/Code/User/settings.json`
- **Cursor**: `~/.config/Cursor/User/settings.json`
- **Zed**: `~/.config/zed/settings.json`

### Universal Settings

**Font Configuration:**
```json
{
    "editor.fontFamily": "'JetBrains Mono', 'Fira Code', monospace",
    "editor.fontSize": 14,
    "editor.fontLigatures": true,
    "editor.lineHeight": 1.5
}
```

**Formatting:**
```json
{
    "editor.formatOnSave": true,
    "editor.formatOnPaste": true,
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true
}
```

**Python-Specific:**
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    },
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true
}
```

### Recommended Fonts

**For Code:**
1. **JetBrains Mono** (free, excellent ligatures)
2. **Fira Code** (free, popular)
3. **Cascadia Code** (free, from Microsoft)
4. **Source Code Pro** (free, clean)
5. **Menlo/Monaco** (built-in on Mac)

**Install JetBrains Mono:**
```bash
# macOS
brew tap homebrew/cask-fonts
brew install --cask font-jetbrains-mono

# Linux
wget https://download.jetbrains.com/fonts/JetBrainsMono-2.304.zip
unzip JetBrainsMono-2.304.zip -d ~/.fonts
fc-cache -f -v

# WSL - install on Windows, works in WSL VS Code
```

### Color Themes

**Popular Themes (VS Code/Cursor):**
1. **One Dark Pro** - `zhuangtongfa.Material-theme`
2. **Dracula Official** - `dracula-theme.theme-dracula`
3. **GitHub Theme** - `GitHub.github-vscode-theme`
4. **Tokyo Night** - `enkia.tokyo-night`
5. **Catppuccin** - `Catppuccin.catppuccin-vsc`

**Install:**
```bash
code --install-extension zhuangtongfa.Material-theme
```

---

## Keyboard Shortcuts {#shortcuts}

### Universal Shortcuts (Work in All Three)

**File Operations:**
- `Ctrl+N` / `Cmd+N`: New file
- `Ctrl+O` / `Cmd+O`: Open file
- `Ctrl+S` / `Cmd+S`: Save
- `Ctrl+Shift+S` / `Cmd+Shift+S`: Save as
- `Ctrl+W` / `Cmd+W`: Close file

**Editing:**
- `Ctrl+C` / `Cmd+C`: Copy
- `Ctrl+X` / `Cmd+X`: Cut
- `Ctrl+V` / `Cmd+V`: Paste
- `Ctrl+Z` / `Cmd+Z`: Undo
- `Ctrl+Shift+Z` / `Cmd+Shift+Z`: Redo
- `Ctrl+/` / `Cmd+/`: Toggle comment
- `Ctrl+D` / `Cmd+D`: Select next occurrence
- `Alt+Up/Down`: Move line up/down
- `Shift+Alt+Up/Down`: Copy line up/down

**Navigation:**
- `Ctrl+P` / `Cmd+P`: Quick file open
- `Ctrl+Shift+P` / `Cmd+Shift+P`: Command palette
- `Ctrl+G` / `Cmd+G`: Go to line
- `Ctrl+Shift+O` / `Cmd+Shift+O`: Go to symbol
- `Ctrl+Tab`: Switch between files

**Search:**
- `Ctrl+F` / `Cmd+F`: Find
- `Ctrl+H` / `Cmd+H`: Replace
- `Ctrl+Shift+F` / `Cmd+Shift+F`: Find in files

**Terminal:**
- ``Ctrl+` `` / ``Cmd+` ``: Toggle terminal
- `Ctrl+Shift+` ` / `Cmd+Shift+` `: New terminal

### VS Code/Cursor Specific

**Multi-cursor:**
- `Ctrl+Alt+Up/Down`: Add cursor above/below
- `Alt+Click`: Add cursor at click

**Folding:**
- `Ctrl+Shift+[`: Fold region
- `Ctrl+Shift+]`: Unfold region

**Zen Mode:**
- `Ctrl+K Z`: Enter Zen Mode (distraction-free)
- `Esc Esc`: Exit Zen Mode

### Customizing Shortcuts

**VS Code/Cursor:**
1. `Ctrl+K Ctrl+S` (or `Cmd+K Cmd+S`)
2. Opens keyboard shortcuts editor
3. Search for command
4. Click to change keybinding

**keybindings.json:**
```json
[
    {
        "key": "ctrl+shift+t",
        "command": "workbench.action.terminal.new"
    },
    {
        "key": "ctrl+shift+c",
        "command": "editor.action.commentLine",
        "when": "editorTextFocus"
    }
]
```

---

## Best Practices {#best-practices}

### Workspace Organization

**Project Structure:**
```
my-project/
├── .vscode/          # VS Code/Cursor settings
│   ├── settings.json # Project-specific settings
│   ├── launch.json   # Debug configurations
│   └── tasks.json    # Build tasks
├── .zed/            # Zed settings (if using)
│   └── settings.json
├── src/
├── tests/