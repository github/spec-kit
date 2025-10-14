# Complete Bash Tutorial: WSL, Mac & Linux

## Table of Contents
1. [Getting Started with Bash](#getting-started)
2. [Why Use Bash?](#why-bash)
3. [Platform-Specific Setup](#setup)
4. [Bash Fundamentals](#fundamentals)
5. [WSL Fundamentals for Beginners] {#beginners}
6. [Essential Commands](#essential-commands)
7. [File Operations](#file-operations)
8. [Text Processing](#text-processing)
9. [Scripting Basics](#scripting)
10. [Advanced Techniques](#advanced)
11. [Practical Examples for AI Development](#ai-examples)

---

## Getting Started with Bash {#getting-started}

Bash (Bourne Again Shell) is a command-line interpreter that provides a powerful interface to your operating system. It's the default shell on most Linux distributions and macOS, and available on Windows through WSL.

### What You'll Learn
- Navigate and manipulate files and directories
- Process text and data efficiently
- Automate repetitive tasks with scripts
- Chain commands together for powerful workflows
- Manage processes and system resources

---

## Why Use Bash? {#why-bash}

### 1. **Universal Availability**
Bash is available on virtually every Unix-like system. Scripts you write work across platforms without modification.

### 2. **Automation Power**
Automate repetitive tasks with simple scripts. What takes 100 mouse clicks can become a single command.

### 3. **Text Processing Excellence**
Bash excels at manipulating text, logs, CSV files, and configuration files—critical for AI development and data processing.

### 4. **Composability**
The Unix philosophy: small tools that do one thing well, combined through pipes into powerful workflows.

### 5. **Efficiency**
Once mastered, command-line operations are faster than GUI equivalents. Batch operations become trivial.

### 6. **Remote Access**
SSH into remote servers and work exactly as you do locally. Essential for cloud deployments.

### 7. **Reproducibility**
Scripts document exactly what you did and can be version-controlled, shared, and repeated.

### 8. **System Control**
Direct access to system resources, processes, and configuration without abstraction layers.

---

## Platform-Specific Setup {#setup}

### Windows (WSL)

**Installing WSL 2:**

1. Open PowerShell as Administrator and run:
```powershell
wsl --install
```

* Windows 10 (version 2004 or later) or any Windows 11.

2. Restart your computer when prompted

3. After restart, WSL will complete installation and ask you to create a username and password

4. Update WSL to the latest version:
```powershell
wsl --update
```

**Accessing Bash:**
- Open "Ubuntu" from the Start menu, or
- Type `wsl` in PowerShell/Command Prompt, or
- Use Windows Terminal (recommended)

**Installing Windows Terminal (Recommended):**
- Install from Microsoft Store: "Windows Terminal"
- Provides tabs, Unicode support, and better appearance

**File System Access:**
- Windows files accessible at `/mnt/c/`, `/mnt/d/`, etc.
- Linux files stored in `\\wsl$\Ubuntu\home\yourusername\`
- **Best Practice:** Keep project files in Linux filesystem for better performance

### macOS

**Accessing Bash/Zsh:**

1. Open Terminal (Applications > Utilities > Terminal, or press `Cmd + Space` and type "Terminal")

2. macOS Catalina and later use Zsh by default, but Bash is still available

**Installing Homebrew (Recommended):**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Switching to Bash (if desired):**
```bash
chsh -s /bin/bash
```

**Recommended Terminal Apps:**
- Built-in Terminal (good)
- iTerm2 (excellent, feature-rich)

### Linux

**Accessing Bash:**
- Usually Bash is the default shell
- Open terminal with `Ctrl + Alt + T` (most distributions)
- Or search for "Terminal" in your application menu

**Checking Your Shell:**
```bash
echo $SHELL
```

**Setting Bash as Default (if needed):**
```bash
chsh -s /bin/bash
```

---

## Bash Fundamentals {#fundamentals}

### The Command Prompt

When you open a terminal, you'll see a prompt like:
```
username@hostname:~$
```

- `username`: Your user account
- `hostname`: Your computer's name
- `~`: Current directory (~ means home directory)
- `$`: Regular user prompt (`#` for root/admin)

### Basic Command Structure

```bash
command [options] [arguments]
```

Example:
```bash
ls -la /home
```
- `ls`: command (list directory contents)
- `-la`: options (long format, all files)
- `/home`: argument (directory to list)

### Getting Help

Every command has built-in documentation:

```bash
# View manual page
man ls

# Quick help
ls --help

# Search manual pages
man -k search_term
```

### Command History

Bash remembers your commands:

```bash
# View history
history

# Repeat last command
!!

# Repeat command #42 from history
!42

# Search history (press Ctrl+R, then type)
# Press Ctrl+R repeatedly to cycle through matches

# Navigate history with arrow keys
# Up/Down arrows
```

---


## WSL Fundamentals for Beginners {#beginners}

Here’s a **complete beginner-friendly setup + first commands** guide to get you learning Bash *the right way* on Windows.

## 🪟 **STEP 1: Install WSL (Windows Subsystem for Linux)**

### 🧰 Requirements:

* Windows 10 (version 2004 or later) or any Windows 11.

### ⚙️ Install via Command Prompt or PowerShell:

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

This will:

* Enable the Linux subsystem
* Download **Ubuntu** by default
* Set it up automatically

🕒 After installation → Restart your PC.

---

## 🐧 **STEP 2: Open and Set Up Ubuntu**

After restart:

1. Open **Start → search “Ubuntu” → open it**
2. It will initialize and ask for:

   * A **UNIX username** (e.g., `zia`)
   * A **password** (type it carefully; it won’t show as you type)

You now have a **real Linux terminal** inside Windows 🎉

---

## 🧱 **STEP 3: Update Your System**

Run these commands first:

```bash
sudo apt update
sudo apt upgrade -y
```

(`sudo` means “run as admin/root”.)

---

## ⚡ **STEP 4: Your First 10 Bash Commands**

Here’s your essential starter pack ⬇️

| Command | Purpose                     | Example                   |
| ------- | --------------------------- | ------------------------- |
| `pwd`   | Show current directory      | `pwd`                     |
| `ls`    | List files                  | `ls -l`                   |
| `cd`    | Change directory            | `cd /home`                |
| `mkdir` | Create folder               | `mkdir testdir`           |
| `touch` | Create file                 | `touch notes.txt`         |
| `cat`   | Show file contents          | `cat notes.txt`           |
| `cp`    | Copy files                  | `cp notes.txt backup.txt` |
| `mv`    | Move or rename              | `mv notes.txt old.txt`    |
| `rm`    | Remove files                | `rm old.txt`              |
| `echo`  | Print text or write to file | `echo "Hello" > hi.txt`   |

👉 Try chaining commands:

```bash
ls | grep txt
```

(This finds all `.txt` files.)

---

## ✍️ **STEP 5: Create and Run a Simple Bash Script**

1. Create a file:

   ```bash
   nano hello.sh
   ```

2. Type this inside:

   ```bash
   #!/bin/bash
   echo "Hello, $(whoami)! Today is $(date)."
   ```

3. Save with `Ctrl + O`, then `Enter`, then `Ctrl + X`.

4. Make it executable:

   ```bash
   chmod +x hello.sh
   ```

5. Run it:

   ```bash
   ./hello.sh
   ```

You’ve now written and executed your **first Bash script** ✅

---

## 🧠 **STEP 6: (Optional) Learn More**

To go deeper, explore:

* `man <command>` → manual for any command (`man ls`)
* `history` → see all commands you’ve run
* `grep`, `awk`, `sed` → text processing tools
* `for`, `if`, `while` → scripting logic

And install more tools:

```bash
sudo apt install vim curl git tree
```


---

## Essential Commands {#essential-commands}

### Navigation

```bash
# Print working directory (where am I?)
pwd

# Change directory
cd /path/to/directory
cd ~              # Go to home directory
cd ..             # Go up one directory
cd -              # Go to previous directory

# List directory contents
ls                # Basic listing
ls -l             # Long format (detailed)
ls -a             # Show hidden files (starting with .)
ls -lh            # Human-readable file sizes
ls -lt            # Sort by modification time
ls -R             # Recursive (include subdirectories)
```

### File and Directory Management

```bash
# Create directory
mkdir my_directory
mkdir -p path/to/nested/directory  # Create parent directories

# Create empty file or update timestamp
touch filename.txt

# Copy files
cp source.txt destination.txt
cp -r source_dir/ dest_dir/        # Copy directory recursively
cp -i file.txt backup.txt          # Interactive (ask before overwrite)

# Move/rename files
mv oldname.txt newname.txt
mv file.txt /path/to/destination/
mv *.txt documents/                # Move all .txt files

# Remove files
rm file.txt
rm -r directory/                   # Remove directory recursively
rm -i file.txt                     # Interactive (ask confirmation)
rm -f file.txt                     # Force (no confirmation)

# Remove empty directory
rmdir empty_directory
```

### Viewing File Contents

```bash
# Display entire file
cat file.txt

# Display with line numbers
cat -n file.txt

# View file page by page
less file.txt                      # Use space/arrow keys, q to quit
more file.txt                      # Simpler pager

# View first lines
head file.txt                      # First 10 lines
head -n 20 file.txt                # First 20 lines

# View last lines
tail file.txt                      # Last 10 lines
tail -n 20 file.txt                # Last 20 lines
tail -f logfile.txt                # Follow (watch for new lines)
```

### File Permissions

```bash
# View permissions
ls -l

# Change permissions (numeric)
chmod 755 script.sh                # rwxr-xr-x
chmod 644 file.txt                 # rw-r--r--

# Change permissions (symbolic)
chmod +x script.sh                 # Add execute permission
chmod u+w file.txt                 # User can write
chmod go-r file.txt                # Group/others cannot read

# Change ownership
chown user:group file.txt
sudo chown root:root file.txt      # Change to root (requires sudo)
```

### Searching

```bash
# Find files
find . -name "*.txt"               # Find all .txt files
find /path -type f -name "test*"   # Find files starting with "test"
find . -mtime -7                   # Modified in last 7 days
find . -size +100M                 # Larger than 100MB

# Search inside files
grep "search_term" file.txt
grep -r "pattern" directory/       # Recursive search
grep -i "case_insensitive" file    # Ignore case
grep -n "show_line_numbers" file   # Show line numbers
grep -v "exclude_lines" file       # Invert match (show non-matching)

# Advanced search
grep -E "regex|pattern" file       # Extended regex
grep -A 3 "pattern" file           # Show 3 lines after match
grep -B 3 "pattern" file           # Show 3 lines before match
```

---

## File Operations {#file-operations}

### Redirection and Pipes

**Output Redirection:**
```bash
# Redirect output to file (overwrite)
echo "Hello" > file.txt
ls -l > directory_listing.txt

# Append to file
echo "More text" >> file.txt

# Redirect errors
command 2> error.log

# Redirect both output and errors
command > output.log 2>&1
command &> combined.log            # Shorter syntax
```

**Input Redirection:**
```bash
# Read from file
sort < unsorted.txt

# Here document (multi-line input)
cat << EOF > file.txt
Line 1
Line 2
Line 3
EOF
```

**Pipes (Chain Commands):**
```bash
# Send output of one command to another
ls -l | grep ".txt"
cat file.txt | grep "error" | wc -l

# Complex pipeline
ps aux | grep python | awk '{print $2}' | xargs kill
```

### Working with Archives

```bash
# Create tar archive
tar -czf archive.tar.gz directory/
tar -cjf archive.tar.bz2 directory/

# Extract tar archive
tar -xzf archive.tar.gz
tar -xjf archive.tar.bz2

# View archive contents
tar -tzf archive.tar.gz

# Zip files
zip -r archive.zip directory/
unzip archive.zip
```

### Downloading Files

```bash
# Download with wget
wget https://example.com/file.zip
wget -O custom_name.zip https://example.com/file.zip

# Download with curl
curl -O https://example.com/file.zip
curl -o custom_name.zip https://example.com/file.zip
curl -L https://example.com/redirect  # Follow redirects
```

---

## Text Processing {#text-processing}

### Essential Text Tools

**Word Count:**
```bash
wc file.txt                        # Lines, words, characters
wc -l file.txt                     # Count lines only
wc -w file.txt                     # Count words only
```

**Sort:**
```bash
sort file.txt                      # Alphabetical sort
sort -n numbers.txt                # Numeric sort
sort -r file.txt                   # Reverse sort
sort -u file.txt                   # Unique (remove duplicates)
sort -k2 file.txt                  # Sort by 2nd column
```

**Unique:**
```bash
uniq file.txt                      # Remove adjacent duplicates
sort file.txt | uniq               # Remove all duplicates
uniq -c file.txt                   # Count occurrences
uniq -d file.txt                   # Show only duplicates
```

**Cut (Extract Columns):**
```bash
cut -d',' -f1,3 data.csv           # Extract columns 1 and 3
cut -c1-10 file.txt                # Extract characters 1-10
echo "user:password" | cut -d':' -f1
```

**Paste (Merge Lines):**
```bash
paste file1.txt file2.txt          # Merge side by side
paste -d',' file1.txt file2.txt    # Use comma delimiter
```

**AWK (Pattern Processing):**
```bash
# Print specific columns
awk '{print $1, $3}' file.txt
awk -F',' '{print $2}' data.csv    # CSV with comma delimiter

# Filter and process
awk '$3 > 100' data.txt            # Lines where column 3 > 100
awk '/error/ {print $0}' log.txt   # Lines containing "error"

# Calculate
awk '{sum += $1} END {print sum}' numbers.txt
```

**SED (Stream Editor):**
```bash
# Replace text
sed 's/old/new/' file.txt          # First occurrence per line
sed 's/old/new/g' file.txt         # All occurrences
sed -i 's/old/new/g' file.txt      # Edit file in-place

# Delete lines
sed '5d' file.txt                  # Delete line 5
sed '/pattern/d' file.txt          # Delete lines matching pattern

# Extract lines
sed -n '10,20p' file.txt           # Print lines 10-20
sed -n '/start/,/end/p' file.txt   # Between patterns
```

---

## Scripting Basics {#scripting}

### Your First Script

Create a file called `hello.sh`:

```bash
#!/bin/bash
# This is a comment

echo "Hello, World!"
echo "Current directory: $(pwd)"
echo "Current user: $USER"
```

Make it executable and run:
```bash
chmod +x hello.sh
./hello.sh
```

### Variables

```bash
#!/bin/bash

# Define variables (no spaces around =)
name="Alice"
age=30
PROJECT_DIR="/home/user/projects"

# Use variables with $
echo "Name: $name"
echo "Age: $age"

# Command substitution
current_date=$(date +%Y-%m-%d)
file_count=$(ls | wc -l)

echo "Date: $current_date"
echo "Files: $file_count"

# Environment variables
echo "Home: $HOME"
echo "Path: $PATH"
echo "User: $USER"
```

### User Input

```bash
#!/bin/bash

# Simple input
echo "What is your name?"
read name
echo "Hello, $name!"

# Input with prompt
read -p "Enter your age: " age
echo "You are $age years old"

# Silent input (for passwords)
read -sp "Enter password: " password
echo  # New line after password
```

### Command Line Arguments

```bash
#!/bin/bash

# $0 = script name
# $1, $2, etc. = arguments
# $# = number of arguments
# $@ = all arguments

echo "Script name: $0"
echo "First argument: $1"
echo "Second argument: $2"
echo "Number of arguments: $#"
echo "All arguments: $@"

# Example usage: ./script.sh arg1 arg2 arg3
```

### Conditionals

```bash
#!/bin/bash

# If statement
if [ "$1" == "hello" ]; then
    echo "You said hello!"
elif [ "$1" == "goodbye" ]; then
    echo "You said goodbye!"
else
    echo "Unknown greeting"
fi

# File tests
if [ -f "file.txt" ]; then
    echo "file.txt exists"
fi

if [ -d "directory" ]; then
    echo "directory exists"
fi

if [ -r "file.txt" ]; then
    echo "file.txt is readable"
fi

# Numeric comparisons
if [ $age -gt 18 ]; then
    echo "Adult"
elif [ $age -eq 18 ]; then
    echo "Just turned adult"
else
    echo "Minor"
fi

# String comparisons
if [ -z "$var" ]; then      # Empty string
    echo "Variable is empty"
fi

if [ -n "$var" ]; then      # Non-empty string
    echo "Variable has content"
fi
```

### Loops

**For Loop:**
```bash
#!/bin/bash

# Iterate over list
for color in red green blue; do
    echo "Color: $color"
done

# Iterate over files
for file in *.txt; do
    echo "Processing: $file"
    wc -l "$file"
done

# C-style loop
for ((i=1; i<=5; i++)); do
    echo "Number: $i"
done

# Iterate over command output
for user in $(cat users.txt); do
    echo "Creating account for $user"
done
```

**While Loop:**
```bash
#!/bin/bash

# Basic while loop
counter=1
while [ $counter -le 5 ]; do
    echo "Count: $counter"
    ((counter++))
done

# Read file line by line
while read line; do
    echo "Line: $line"
done < file.txt

# Infinite loop
while true; do
    echo "Press Ctrl+C to stop"
    sleep 1
done
```

### Functions

```bash
#!/bin/bash

# Define function
greet() {
    local name=$1  # Local variable
    echo "Hello, $name!"
}

# Function with return value
add() {
    local sum=$(($1 + $2))
    echo $sum
}

# Function with multiple returns
check_file() {
    if [ -f "$1" ]; then
        return 0  # Success
    else
        return 1  # Failure
    fi
}

# Call functions
greet "Alice"

result=$(add 5 3)
echo "Sum: $result"

if check_file "test.txt"; then
    echo "File exists"
else
    echo "File not found"
fi
```

---

## Advanced Techniques {#advanced}

### Process Management

```bash
# View running processes
ps aux
ps aux | grep python

# Interactive process viewer
top
htop  # More user-friendly (may need installation)

# Kill processes
kill PID
kill -9 PID        # Force kill
killall python     # Kill all processes named python

# Background jobs
long_command &     # Run in background
jobs               # List background jobs
fg                 # Bring to foreground
bg                 # Resume in background
Ctrl+Z            # Suspend current process
```

### Environment Variables

```bash
# View all environment variables
env
printenv

# Set variable for session
export API_KEY="your-key-here"
export PATH="$PATH:/new/directory"

# Permanent variables (add to ~/.bashrc or ~/.bash_profile)
echo 'export API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc   # Reload configuration

# Use in scripts
#!/bin/bash
echo "API Key: $API_KEY"
```

### Bash Configuration Files

```bash
# ~/.bashrc - Runs for interactive non-login shells
# Add aliases, functions, and customizations

# ~/.bash_profile or ~/.profile - Runs for login shells
# Sets up environment variables

# Example ~/.bashrc
alias ll='ls -lah'
alias gs='git status'
alias python=python3

export EDITOR=vim
export PATH="$HOME/.local/bin:$PATH"

# Custom prompt
PS1='\[\e[32m\]\u@\h:\w\$\[\e[0m\] '
```

### Advanced Scripting

**Error Handling:**
```bash
#!/bin/bash

# Exit on error
set -e

# Exit on undefined variable
set -u

# Exit on pipe failure
set -o pipefail

# Custom error handling
if ! command_that_might_fail; then
    echo "Error: Command failed" >&2
    exit 1
fi

# Trap errors
trap 'echo "Error on line $LINENO"' ERR
```

**Arrays:**
```bash
#!/bin/bash

# Define array
fruits=("apple" "banana" "cherry")

# Access elements
echo ${fruits[0]}      # First element
echo ${fruits[@]}      # All elements
echo ${#fruits[@]}     # Array length

# Iterate over array
for fruit in "${fruits[@]}"; do
    echo "Fruit: $fruit"
done

# Add to array
fruits+=("date")
```

**String Manipulation:**
```bash
#!/bin/bash

text="Hello, World!"

# Length
echo ${#text}

# Substring
echo ${text:0:5}       # "Hello"
echo ${text:7}         # "World!"

# Replace
echo ${text/World/Bash}    # "Hello, Bash!"
echo ${text//l/L}          # "HeLLo, WorLd!"

# Upper/lowercase
echo ${text^^}         # "HELLO, WORLD!"
echo ${text,,}         # "hello, world!"

# Remove prefix/suffix
filename="script.sh"
echo ${filename%.sh}   # "script"
echo ${filename#*.}    # "sh"
```

---

## Practical Examples for AI Development {#ai-examples}

### Setting Up Python Environments

```bash
#!/bin/bash

# Create project structure
mkdir -p my_ai_project/{data,models,scripts,notebooks}
cd my_ai_project

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On WSL, Mac, Linux
# Note: Windows cmd would use venv\Scripts\activate.bat

# Install dependencies
pip install --upgrade pip
pip install torch transformers langchain openai

# Save dependencies
pip freeze > requirements.txt

# Later: Install from requirements
pip install -r requirements.txt
```

### Processing Training Data

```bash
#!/bin/bash

# Count total lines in all CSV files
find data/ -name "*.csv" -exec wc -l {} + | tail -1

# Remove duplicates from dataset
sort data/raw.csv | uniq > data/clean.csv

# Split data into train/test
total_lines=$(wc -l < data/clean.csv)
train_lines=$((total_lines * 80 / 100))

head -n $train_lines data/clean.csv > data/train.csv
tail -n +$((train_lines + 1)) data/clean.csv > data/test.csv

# Extract specific columns from CSV
awk -F',' '{print $1","$3}' data/full.csv > data/subset.csv

# Filter rows based on condition
awk -F',' '$2 > 100' data/metrics.csv > data/filtered.csv
```

### Log Analysis

```bash
#!/bin/bash

# Find all errors in logs
grep -r "ERROR" logs/ > errors.txt

# Count errors by type
grep "ERROR" app.log | cut -d':' -f2 | sort | uniq -c | sort -nr

# Extract API response times
grep "Response time" app.log | awk '{print $NF}' | \
    awk '{sum+=$1; count++} END {print "Average:", sum/count}'

# Monitor log file in real-time
tail -f app.log | grep --color=auto "ERROR\|WARNING"

# Find slow requests (> 1000ms)
awk '/Response time/ && $NF > 1000' app.log
```

### Model Management

```bash
#!/bin/bash

# Download models
download_model() {
    local model_name=$1
    local output_dir="models/${model_name}"
    
    mkdir -p "$output_dir"
    echo "Downloading $model_name..."
    
    # Example with HuggingFace
    python3 << EOF
from transformers import AutoModel, AutoTokenizer
model = AutoModel.from_pretrained("$model_name")
tokenizer = AutoTokenizer.from_pretrained("$model_name")
model.save_pretrained("$output_dir")
tokenizer.save_pretrained("$output_dir")
EOF
    
    echo "Downloaded to $output_dir"
}

# List all models
list_models() {
    echo "Available models:"
    ls -lh models/
}

# Clean old models
clean_old_models() {
    find models/ -type d -mtime +30 -exec rm -rf {} +
    echo "Cleaned models older than 30 days"
}
```

### Experiment Tracking

```bash
#!/bin/bash

# Create experiment directory
run_experiment() {
    local exp_name=$1
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local exp_dir="experiments/${exp_name}_${timestamp}"
    
    mkdir -p "$exp_dir"
    
    # Save configuration
    cat > "$exp_dir/config.txt" << EOF
Experiment: $exp_name
Date: $(date)
Model: $MODEL_NAME
Learning Rate: $LEARNING_RATE
Batch Size: $BATCH_SIZE
EOF
    
    # Run training
    python3 train.py \
        --model "$MODEL_NAME" \
        --lr "$LEARNING_RATE" \
        --batch-size "$BATCH_SIZE" \
        --output "$exp_dir" \
        2>&1 | tee "$exp_dir/training.log"
    
    echo "Experiment saved to $exp_dir"
}

# Compare experiments
compare_experiments() {
    echo "Experiment Results:"
    for dir in experiments/*/; do
        echo "---"
        echo "Experiment: $(basename $dir)"
        grep "Final accuracy" "$dir/training.log" || echo "Not completed"
    done
}
```

### Deployment Automation

```bash
#!/bin/bash

# Deploy AI model to server
deploy_model() {
    local model_path=$1
    local server=$2
    
    # Create deployment package
    tar -czf model_package.tar.gz "$model_path" requirements.txt

    # Upload to server
    scp model_package.tar.gz "$server:/opt/models/"
    
    # SSH and deploy
    ssh "$server" << 'EOF'
cd /opt/models
tar -xzf model_package.tar.gz
pip install -r requirements.txt
systemctl restart ai-service
EOF
    
    echo "Deployment complete"
}

# Health check
check_service() {
    local endpoint=$1
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint/health")
    
    if [ "$response" == "200" ]; then
        echo "Service is healthy"
        return 0
    else
        echo "Service is down (HTTP $response)"
        return 1
    fi
}
```

### Batch Processing

```bash
#!/bin/bash

# Process multiple files with AI model
batch_process() {
    local input_dir=$1
    local output_dir=$2
    
    mkdir -p "$output_dir"
    
    # Count total files
    total=$(find "$input_dir" -name "*.txt" | wc -l)
    current=0
    
    # Process each file
    find "$input_dir" -name "*.txt" | while read -r file; do
        ((current++))
        filename=$(basename "$file")
        
        echo "Processing $current/$total: $filename"
        
        python3 process.py \
            --input "$file" \
            --output "$output_dir/$filename" \
            --model gpt-4
        
        # Rate limiting
        sleep 1
    done
    
    echo "Batch processing complete: $total files processed"
}

# Parallel processing
parallel_process() {
    local input_dir=$1
    local output_dir=$2
    local max_jobs=4
    
    mkdir -p "$output_dir"
    
    find "$input_dir" -name "*.txt" | \
    parallel -j $max_jobs \
    python3 process.py --input {} --output "$output_dir/{/}"
}
```

### Git and Version Control

```bash
#!/bin/bash

# Initialize project with Git
setup_git_project() {
    git init
    
    # Create .gitignore
    cat > .gitignore << 'EOF'
__pycache__/
*.pyc
.env
venv/
.vscode/
*.log
models/*.bin
data/raw/
experiments/
EOF
    
    git add .
    git commit -m "Initial commit"
}

# Common Git aliases in ~/.bashrc
alias ga='git add'
alias gc='git commit -m'
alias gp='git push'
alias gs='git status'
alias gl='git log --oneline --graph'
alias gd='git diff'
```

---

## Practice Exercises

### Exercise 1: File Organization
Create a script that organizes files by extension:
```bash
#!/bin/bash
# Sort files into directories by extension

for file in *.*; do
    ext="${file##*.}"
    mkdir -p "$ext"
    mv "$file" "$ext/"
done
```

### Exercise 2: Log Analyzer
Create a script to analyze web server logs:
```bash
#!/bin/bash
# Analyze Apache/Nginx logs

log_file=$1

echo "Top 10 IP addresses:"
awk '{print $1}' "$log_file" | sort | uniq -c | sort -nr | head -10

echo -e "\nTop 10 requested URLs:"
awk '{print $7}' "$log_file" | sort | uniq -c | sort -nr | head -10

echo -e "\nHTTP status code distribution:"
awk '{print $9}' "$log_file" | sort | uniq -c | sort -nr
```

### Exercise 3: Backup Script
Create an automated backup script:
```bash
#!/bin/bash
# Backup important directories

BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
DIRS_TO_BACKUP=("$HOME/projects" "$HOME/documents")

for dir in "${DIRS_TO_BACKUP[@]}"; do
    dir_name=$(basename "$dir")
    tar -czf "$BACKUP_DIR/${dir_name}_${DATE}.tar.gz" "$dir"
    echo "Backed up $dir"
done

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
```

---

## Tips for Mastery

### 1. **Use Tab Completion**
Press Tab to autocomplete filenames, commands, and paths. Press Tab twice to see all options.

### 2. **Learn Keyboard Shortcuts**
- `Ctrl + C`: Cancel current command
- `Ctrl + D`: Exit shell/end input
- `Ctrl + L`: Clear screen
- `Ctrl + A`: Move to beginning of line
- `Ctrl + E`: Move to end of line
- `Ctrl + U`: Delete to beginning of line
- `Ctrl + K`: Delete to end of line
- `Ctrl + R`: Search command history

### 3. **Read the Manual**
Before asking how to use a command, try `man command_name`.

### 4. **Practice Regular Expressions**
Regex makes text processing powerful. Start simple and build up.

### 5. **Version Control Everything**
Put scripts in Git repositories. Your future self will thank you.

### 6. **Write Reusable Scripts**
Create a personal scripts directory in your PATH for frequently used tools.

### 7. **Learn from Others**
Read shell scripts in open source projects. See how experts write maintainable code.

### 8. **Test Safely**
Use `echo` before destructive operations:
```bash
# Test first
find . -name "*.tmp" -type f -exec echo rm {} \;

# Then execute
find . -name "*.tmp" -type f -exec rm {} \;
```

---

## Conclusion

Bash is a powerful tool that becomes more valuable as you master it. Start with basic commands, gradually incorporate scripting, and soon you'll be automating complex workflows effortlessly.

For AI development specifically, Bash skills enable you to:
- Automate data preprocessing pipelines
- Manage experiments efficiently
- Deploy models reliably
- Monitor systems in production
- Process logs and debug issues quickly

The investment in learning Bash pays compound returns throughout your career. Every minute spent mastering these skills saves hours of manual work later.

**Next Steps:**
1. Work through the exercises
2. Create your own utility scripts for daily tasks
3. Contribute scripts to your team's repositories
4. Explore advanced topics: process substitution, co-processes, network programming

Happy scripting!