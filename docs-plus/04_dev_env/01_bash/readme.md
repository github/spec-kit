# Bash Essentials for AI CLI Development

A minimal guide to get you productive with AI development tools like Claude Code, Cursor, and other AI CLIs.

## Navigation & File Management

### Where am I?
```bash
pwd                    # Print working directory (shows current location)
```

### Moving around
```bash
cd project-name        # Go into a folder
cd ..                  # Go up one level
cd ~                   # Go to home directory
cd -                   # Go back to previous directory
```

### Seeing what's here
```bash
ls                     # List files
ls -la                 # List all files (including hidden) with details
tree                   # Show directory structure (may need to install)
```

### Creating & removing
```bash
mkdir my-project       # Create directory
touch file.txt         # Create empty file
rm file.txt            # Delete file
rm -rf folder/         # Delete folder and contents (use carefully!)
```

## Working with Files

### Reading files
```bash
cat file.txt           # Show entire file
head file.txt          # Show first 10 lines
tail file.txt          # Show last 10 lines
tail -f log.txt        # Follow file updates (great for logs)
less file.txt          # Browse file (q to quit, / to search)
```

### Editing files
```bash
nano file.txt          # Simple editor (Ctrl+X to exit)
```

### Copying & moving
```bash
cp source.txt dest.txt           # Copy file
cp -r source-dir/ dest-dir/      # Copy directory
mv old-name.txt new-name.txt     # Rename/move file
```

## Process Management

### Running commands
```bash
command                # Run in foreground
command &              # Run in background
Ctrl+C                 # Stop current process
Ctrl+Z                 # Pause process
```

### Seeing what's running
```bash
ps aux                 # List all processes
top                    # Interactive process viewer (q to quit)
kill 12345             # Stop process with PID 12345
killall process-name   # Stop all processes with that name
```

## AI CLI Essentials

### Environment variables (API keys, etc.)
```bash
export API_KEY="your-key-here"         # Set for current session
echo $API_KEY                          # View variable
env                                    # See all environment variables
```

### Making variables permanent
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export ANTHROPIC_API_KEY="your-key"
```
Then reload:
```bash
source ~/.bashrc       # Reload bash config
```

### Command history
```bash
history                # See past commands
!123                   # Run command #123 from history
!!                     # Run last command
Ctrl+R                 # Search command history (type to search)
```

## Pipes & Redirection

### Connecting commands
```bash
command1 | command2    # Send output of command1 to command2
cat file.txt | grep "error"        # Find "error" in file
ls | wc -l                          # Count files in directory
```

### Saving output
```bash
command > file.txt     # Save output to file (overwrite)
command >> file.txt    # Append output to file
command 2> errors.txt  # Save errors to file
```

## Package Management

### macOS (Homebrew)
```bash
brew install package-name
brew update
brew upgrade
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install package-name
```

### Python packages
```bash
pip install package-name
pip install -r requirements.txt
```

### Node packages
```bash
npm install package-name
npm install              # Install from package.json
```

## Useful Shortcuts

```bash
Tab                    # Auto-complete
Tab Tab                # Show all options
Ctrl+A                 # Go to start of line
Ctrl+E                 # Go to end of line
Ctrl+U                 # Clear line
Ctrl+L                 # Clear screen (or type 'clear')
Ctrl+D                 # Exit terminal/shell
```

## Finding Things

```bash
find . -name "*.py"              # Find Python files
grep "search-term" file.txt      # Search in file
grep -r "search-term" .          # Search in all files recursively
which python                     # Find program location
```

## Permissions (when you get "permission denied")

```bash
chmod +x script.sh     # Make file executable
sudo command           # Run with admin privileges
```

## Common Patterns for AI CLI Work

### Check what's installed
```bash
which claude           # Check if Claude CLI is installed
python --version       # Check Python version
node --version         # Check Node version
```

### Create project structure
```bash
mkdir -p project/{src,tests,docs}    # Create nested folders
cd project && git init               # Initialize git repo
touch README.md .gitignore           # Create essential files
```

### Monitor AI CLI output
```bash
claude code "task" | tee output.log  # Show output AND save to file
```

### Chain AI operations
```bash
claude analyze code.py > analysis.txt && cat analysis.txt
```

## Quick Troubleshooting

**Command not found?**
- Check if installed: `which command-name`
- Check PATH: `echo $PATH`
- Reinstall or add to PATH

**Permission denied?**
- Try `chmod +x filename` for scripts
- Use `sudo` for system operations
- Check file ownership: `ls -la`

**API key not working?**
- Check it's set: `echo $API_KEY`
- Reload config: `source ~/.bashrc`
- Check for typos in variable name

## Pro Tips

1. Use `!!` to quickly rerun the last command with sudo: `sudo !!`
2. Use `Ctrl+R` to search history - huge time saver
3. Create aliases for common commands in `~/.bashrc`:
   ```bash
   alias ll='ls -la'
   alias gs='git status'
   ```
4. Use `man command` to read documentation for any command
5. When copying commands from AI, understand what they do before running

## Next Steps

This covers 90% of what you'll need for AI-driven development. As you work:
- Commands will become muscle memory
- You'll discover shortcuts specific to your workflow
- Your AI assistant can help with complex one-liners when needed

**Remember:** You don't need to memorize everything. Keep this guide handy and refer back as needed. The AI tools you're using can also help explain bash commands when you're stuck!

## Appendix: Natural Language Prompts for AI CLI Tools

This appendix provides natural language prompts you can use with AI CLI tools like Claude Code, Gemini CLI, and similar assistants to execute the commands covered in the tutorial. The format shows the bash command first, followed by natural language prompts you can use to have the AI execute that command.

---

## Navigation & File Management

### Finding Your Location

Instead of: `pwd`

```
Prompt: "Show me my current directory path"
Prompt: "Where am I right now in the filesystem?"
Prompt: "What's my current working directory?"
```

### Moving Around

Instead of: `cd project-name`

```
Prompt: "Go into the project-name folder"
Prompt: "Navigate to the project-name directory"
Prompt: "Change to the project-name directory"
```

Instead of: `cd ..`

```
Prompt: "Navigate to the parent directory"
Prompt: "Go up one level"
Prompt: "Move to the directory above this one"
```

Instead of: `cd ~`

```
Prompt: "Take me to my home directory"
Prompt: "Go to my home folder"
Prompt: "Navigate to my user home directory"
```

Instead of: `cd -`

```
Prompt: "Go back to the previous directory I was in"
Prompt: "Switch back to where I just came from"
Prompt: "Return to my last directory"
```

### Listing Files

Instead of: `ls`

```
Prompt: "List all files in the current directory"
Prompt: "Show me what's in this folder"
Prompt: "Display the contents of this directory"
```

Instead of: `ls -la`

```
Prompt: "Show me all files including hidden ones with full details"
Prompt: "Give me a detailed listing of everything here, including hidden files"
Prompt: "List all files with permissions, owners, and sizes including hidden ones"
```

Instead of: `tree`

```
Prompt: "Display the directory structure as a tree"
Prompt: "Show me the folder hierarchy"
Prompt: "Visualize the directory tree structure"
```

### Creating Files and Directories

Instead of: `mkdir my-project`

```
Prompt: "Create a new directory called my-project"
Prompt: "Make a folder named my-project"
Prompt: "Create a directory for my-project"
```

Instead of: `touch file.txt`

```
Prompt: "Make a new empty file named file.txt"
Prompt: "Create an empty file called file.txt"
Prompt: "Create a blank file.txt"
```

### Deleting Files and Directories

Instead of: `rm file.txt`

```
Prompt: "Delete the file named file.txt"
Prompt: "Remove file.txt"
Prompt: "Delete file.txt from the current directory"
```

Instead of: `rm -rf folder/`

```
Prompt: "Remove the folder named old-project and everything inside it"
Prompt: "Permanently delete the directory temp-data with all its contents"
Prompt: "Delete the folder recursively including all files"
```

---

## Working with Files

### Reading File Contents

Instead of: `cat file.txt`

```
Prompt: "Show me the entire contents of file.txt"
Prompt: "Display what's in file.txt"
Prompt: "Print the contents of file.txt"
```

Instead of: `head file.txt`

```
Prompt: "Display the first 10 lines of data.log"
Prompt: "Show me the beginning of file.txt"
Prompt: "Give me the first few lines of the file"
```

Instead of: `tail file.txt`

```
Prompt: "Show me the last 10 lines of error.log"
Prompt: "Display the end of file.txt"
Prompt: "Show the most recent entries in the log file"
```

Instead of: `tail -f log.txt`

```
Prompt: "Monitor server.log and show new lines as they're added in real-time"
Prompt: "Follow the application.log file and display updates live"
Prompt: "Watch log.txt for new entries"
```

Instead of: `less file.txt`

```
Prompt: "Open readme.txt in a scrollable viewer"
Prompt: "Let me browse through documentation.md with search capability"
Prompt: "Open file.txt in a paginated viewer"
```

### Editing Files

Instead of: `nano file.txt`

```
Prompt: "Open config.txt in a simple text editor"
Prompt: "Let me edit settings.conf using nano"
Prompt: "Edit file.txt in the terminal"
```

### Copying and Moving Files

Instead of: `cp source.txt dest.txt`

```
Prompt: "Copy source.txt to dest.txt"
Prompt: "Make a copy of data.json and name it backup.json"
Prompt: "Duplicate source.txt as dest.txt"
```

Instead of: `cp -r source-dir/ dest-dir/`

```
Prompt: "Copy the entire src directory to backup-src including all contents"
Prompt: "Duplicate the configs folder with everything inside to configs-old"
Prompt: "Recursively copy source-dir to dest-dir"
```

Instead of: `mv old-name.txt new-name.txt`

```
Prompt: "Rename old-name.txt to new-name.txt"
Prompt: "Change the name of old-name.txt to new-name.txt"
Prompt: "Move and rename old-name.txt to new-name.txt"
```

---

## Process Management

### Running and Controlling Processes

Instead of: `command &`

```
Prompt: "Run this script in the background so I can keep using the terminal"
Prompt: "Execute the build process in the background"
Prompt: "Start this command in the background"
```

Instead of: `ps aux`

```
Prompt: "Show me all currently running processes on the system"
Prompt: "List all processes with their IDs and resource usage"
Prompt: "Display all active processes"
```

Instead of: `top`

```
Prompt: "Open an interactive process monitor"
Prompt: "Show me real-time system resource usage and processes"
Prompt: "Start the process viewer"
```

Instead of: `kill 12345`

```
Prompt: "Kill the process with ID 12345"
Prompt: "Terminate process 9876"
Prompt: "Stop the process with PID 12345"
```

Instead of: `killall process-name`

```
Prompt: "Stop all processes named node"
Prompt: "Kill all python processes running on the system"
Prompt: "Terminate all instances of process-name"
```

---

## Environment Variables

### Setting and Viewing Variables

Instead of: `export API_KEY="abc123"`

```
Prompt: "Set an environment variable called API_KEY with value abc123 for this session"
Prompt: "Create a temporary environment variable DATABASE_URL set to localhost:5432"
Prompt: "Export API_KEY as abc123"
```

Instead of: `echo $API_KEY`

```
Prompt: "Show me the value of the API_KEY variable"
Prompt: "Display what's stored in the PATH variable"
Prompt: "Print the value of API_KEY"
```

Instead of: `env`

```
Prompt: "List all environment variables currently set"
Prompt: "Show me all the environment variables in my current session"
Prompt: "Display all exported variables"
```

### Making Variables Permanent

Instead of: Edit `~/.bashrc` and add `export ANTHROPIC_API_KEY="your-key"`

```
Prompt: "Add ANTHROPIC_API_KEY to my bash config so it persists across sessions"
Prompt: "Make NODE_ENV=production permanent in my shell configuration"
Prompt: "Configure my bashrc to export API_KEY on startup"
```

Instead of: `source ~/.bashrc`

```
Prompt: "Reload my bash configuration file to apply new changes"
Prompt: "Refresh my zsh settings after editing the config"
Prompt: "Apply the changes I made to my bashrc"
```

---

## Command History

Instead of: `history`

```
Prompt: "Show me my command history"
Prompt: "Display all the commands I've run recently"
Prompt: "List my previous commands"
```

Instead of: `!123`

```
Prompt: "Run command number 123 from my history"
Prompt: "Execute history entry 123"
Prompt: "Rerun the command at position 123"
```

Instead of: `!!`

```
Prompt: "Execute the last command I ran again"
Prompt: "Repeat my previous command"
Prompt: "Run the last command again"
```

Instead of: `sudo !!`

```
Prompt: "Run the last command again but with sudo this time"
Prompt: "Execute the previous command with administrator privileges"
Prompt: "Rerun the last command as root"
```

---

## Pipes & Redirection

### Combining Commands

Instead of: `cat file.txt | grep "error"`

```
Prompt: "Search for the word 'error' in file.txt"
Prompt: "Find all lines containing 'error' in file.txt"
Prompt: "Filter file.txt to show only lines with 'error'"
```

Instead of: `ls | wc -l`

```
Prompt: "Count how many files are in this directory"
Prompt: "Tell me the total number of items in the current folder"
Prompt: "How many files and folders are here?"
```

### Saving Output

Instead of: `command > output.txt`

```
Prompt: "Save the output of this command to output.txt, overwriting if it exists"
Prompt: "Write the directory listing to files.txt"
Prompt: "Redirect the output to output.txt"
```

Instead of: `command >> output.txt`

```
Prompt: "Append the command output to log.txt without deleting existing content"
Prompt: "Add the current date to the end of timeline.txt"
Prompt: "Append output to log.txt"
```

Instead of: `command 2> errors.txt`

```
Prompt: "Save any error messages to errors.txt"
Prompt: "Redirect errors to error-log.txt while showing normal output"
Prompt: "Capture error output to errors.txt"
```

---

## Package Management

### macOS (Homebrew)

Instead of: `brew install package-name`

```
Prompt: "Install wget using Homebrew"
Prompt: "Use brew to install package-name"
Prompt: "Add package-name via Homebrew"
```

Instead of: `brew update`

```
Prompt: "Update Homebrew's package list"
Prompt: "Refresh the Homebrew package database"
Prompt: "Update brew"
```

Instead of: `brew upgrade`

```
Prompt: "Upgrade all installed Homebrew packages"
Prompt: "Update all brew packages to latest versions"
Prompt: "Upgrade everything installed with Homebrew"
```

### Ubuntu/Debian

Instead of: `sudo apt update`

```
Prompt: "Update the package database on Ubuntu"
Prompt: "Refresh apt package lists"
Prompt: "Update available package information"
```

Instead of: `sudo apt install package-name`

```
Prompt: "Install curl on Debian/Ubuntu"
Prompt: "Install the latest version of git using apt"
Prompt: "Add package-name using apt"
```

### Python Packages

Instead of: `pip install package-name`

```
Prompt: "Install the requests Python package"
Prompt: "Install pandas using pip"
Prompt: "Add package-name via pip"
```

Instead of: `pip install -r requirements.txt`

```
Prompt: "Install all Python packages listed in requirements.txt"
Prompt: "Install dependencies from requirements.txt"
Prompt: "Use pip to install everything in requirements.txt"
```

### Node Packages

Instead of: `npm install package-name`

```
Prompt: "Install express using npm"
Prompt: "Add react to my Node.js project"
Prompt: "Install package-name with npm"
```

Instead of: `npm install`

```
Prompt: "Install all dependencies from package.json"
Prompt: "Install project dependencies"
Prompt: "Set up all npm packages for this project"
```

---

## Finding Things

### Searching for Files

Instead of: `find . -name "*.py"`

```
Prompt: "Find all Python files in the current directory and subdirectories"
Prompt: "Search for all JavaScript files starting from here"
Prompt: "Locate all JSON files in this project"
```

### Searching Within Files

Instead of: `grep "search-term" file.txt`

```
Prompt: "Search for 'TODO' in app.py"
Prompt: "Find lines containing 'search-term' in file.txt"
Prompt: "Look for 'error' in the log file"
```

Instead of: `grep -r "search-term" .`

```
Prompt: "Search for 'function main' in all files recursively"
Prompt: "Find which files contain the text 'API_KEY' in this directory tree"
Prompt: "Search the entire project for 'search-term'"
```

### Finding Programs

Instead of: `which command-name`

```
Prompt: "Where is the python executable located?"
Prompt: "Show me the path to the node binary"
Prompt: "Find where git is installed"
Prompt: "Check if docker is installed and show its location"
```

---

## Permissions

Instead of: `chmod +x script.sh`

```
Prompt: "Make script.sh executable"
Prompt: "Give execute permissions to deploy.sh"
Prompt: "Allow script.sh to be run as a program"
```

Instead of: `sudo command`

```
Prompt: "Run this command with administrator privileges"
Prompt: "Install this package with root permissions"
Prompt: "Execute this command as superuser"
```

---

## Common Patterns for AI CLI Work

### Checking Installations

Instead of: `which claude`

```
Prompt: "Check if Claude CLI is installed"
Prompt: "Verify that claude is available"
Prompt: "Is the claude command installed?"
```

Instead of: `python --version`

```
Prompt: "What version of Python do I have?"
Prompt: "Show me my Node.js version"
Prompt: "Display the npm version installed"
```

### Creating Project Structure

Instead of: `mkdir -p project/{src,tests,docs}`

```
Prompt: "Create a project folder with src, tests, and docs subdirectories"
Prompt: "Set up a new project directory with standard folders"
Prompt: "Make a project structure with multiple subdirectories"
```

Instead of: `touch README.md .gitignore`

```
Prompt: "Create README.md and .gitignore files"
Prompt: "Make empty README and gitignore files"
Prompt: "Set up basic project files"
```

### Monitoring Output

Instead of: `command | tee output.log`

```
Prompt: "Run the Claude analysis and save output to a log while showing it on screen"
Prompt: "Execute this command and both display and log the results"
Prompt: "Show output and save to file simultaneously"
```

### Chaining Commands

Instead of: `command1 && command2`

```
Prompt: "Analyze the code and then display the results if successful"
Prompt: "Build the project and if successful, run the tests"
Prompt: "Install dependencies, then start the development server"
```

---

## Troubleshooting Scenarios

### Command Not Found

Instead of: `which command-name`

```
Prompt: "Check if the 'aws' command is installed on my system"
Prompt: "Verify that python3 is available"
Prompt: "Is command-name installed?"
```

Instead of: `echo $PATH`

```
Prompt: "Show me what's in my PATH variable"
Prompt: "Display my PATH environment variable"
Prompt: "What directories are in my PATH?"
```

### Permission Issues

Instead of: `chmod +x script.sh`

```
Prompt: "Make this script executable so I can run it"
Prompt: "Fix permission denied error on script.sh"
Prompt: "Add execute permission to this script"
```

Instead of: `ls -la filename`

```
Prompt: "Check the ownership and permissions of this file"
Prompt: "Show me file permissions and owner"
Prompt: "Display detailed info about this file"
```

### API Key Issues

Instead of: `echo $ANTHROPIC_API_KEY`

```
Prompt: "Check if my ANTHROPIC_API_KEY environment variable is set"
Prompt: "Verify that my API key environment variable exists"
Prompt: "Show me the value of my API key"
```

Instead of: `env | grep API_KEY`

```
Prompt: "Find all environment variables containing API_KEY"
Prompt: "Search my environment for API key variables"
Prompt: "List all API key environment variables"
```

---

## Advanced Prompt Patterns

### Combining Multiple Operations

Instead of: `mkdir backup && cp *.py backup/ && ls backup/`

```
Prompt: "Create a backup directory, copy all Python files to it, and list the results"
Prompt: "Make a backup folder and copy all code files there"
Prompt: "Set up a backup with all Python files"
```

Instead of: `find . -name "*.log" -mtime +7 -delete`

```
Prompt: "Find all log files older than 7 days and delete them"
Prompt: "Clean up old log files from more than a week ago"
Prompt: "Remove log files that haven't been modified in 7 days"
```

Instead of: `find src -name "*.py" -exec wc -l {} + | tail -1`

```
Prompt: "Count how many lines of Python code are in my src directory"
Prompt: "Get total line count for all Python files in src"
Prompt: "How many lines of code do I have in Python files?"
```

### Process Management

Instead of: `ps aux | grep node`

```
Prompt: "Show me all Python processes running"
Prompt: "Find the process ID of the node server"
Prompt: "List all node processes"
```

Instead of: `ps aux --sort=-%mem | head`

```
Prompt: "List processes sorted by memory usage"
Prompt: "Show me the top memory-consuming processes"
Prompt: "Which processes are using the most RAM?"
```

### File Operations

Instead of: `find . -type f -size +100M`

```
Prompt: "Find all files larger than 100MB in the current directory"
Prompt: "Show me large files over 100 megabytes"
Prompt: "List files bigger than 100MB"
```

Instead of: `find . -type f -mtime -1`

```
Prompt: "Search for files modified in the last 24 hours"
Prompt: "Find files changed today"
Prompt: "Show recently modified files"
```

Instead of: `du -ah . | sort -rh | head -10`

```
Prompt: "Show me the 10 largest files in this directory tree"
Prompt: "Find the biggest files and folders here"
Prompt: "What's taking up the most space?"
```

---

## End of Appendix

Use these natural language prompts as a reference when working with AI CLI tools. The AI will understand your intent and execute the appropriate bash commands. Feel free to adapt these prompts to your natural speaking style - AI assistants are designed to understand variations in phrasing.