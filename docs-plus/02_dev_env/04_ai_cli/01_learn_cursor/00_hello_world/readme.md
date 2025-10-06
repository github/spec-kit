# Building a Python Hello World Project with uv Using Cursor IDE's AI Agent

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Setting up Cursor IDE](#setting-up-cursor-ide)
4. [Installing uv Through Cursor](#installing-uv-through-cursor)
5. [Creating Project with Cursor AI](#creating-project-with-cursor-ai)
6. [Using Cursor Composer](#using-cursor-composer)
7. [AI-Powered Development Workflow](#ai-powered-development-workflow)
8. [Advanced Cursor AI Features](#advanced-cursor-ai-features)
9. [Tips for Maximum Automation](#tips-for-maximum-automation)

## Introduction

This tutorial demonstrates how to build a Python project using **uv** dependency manager while leveraging **Cursor IDE's AI agent** to do most of the work automatically. Instead of typing code manually, you'll learn to use Cursor's AI capabilities to generate, modify, and manage your entire project.

### Why Use Cursor's AI Agent?

Cursor's AI agent can:
- Generate entire project structures
- Write complete code files from descriptions
- Execute terminal commands for you
- Fix errors automatically
- Refactor and improve code
- Add tests and documentation
- Manage dependencies

## Prerequisites

You only need:
- Cursor IDE installed ([download from cursor](https://cursor.com/download))
- Internet connection for AI features

That's it! Cursor will help with everything else.

## Setting up Cursor IDE

### Step 1: Install and Launch Cursor

1. Download Cursor from [https://cursor.com/download](https://cursor.com/download)
2. Install it like any regular application
3. Open Cursor IDE

### Step 2: Enable AI Features

1. When Cursor opens, sign in for full AI capabilities (recommended)
2. You'll get access to ChatGPT, Claude, and other models
3. The AI features will be available immediately

### Step 3: Configure Cursor for Maximum Automation

1. Press `Cmd+,` (Mac) or `Ctrl+,` (Windows/Linux) to open settings
2. Search for "AI" in settings
3. Enable:
   - "Auto-generate commit messages"
   - "Copilot++"
   - "Apply suggestions automatically"

## Installing uv Through Cursor

Instead of installing uv manually, let Cursor do it for you!

### Method 1: Using Cursor's Terminal with AI

1. Open Cursor's integrated terminal: `Ctrl+`` (backtick) or View → Terminal
2. Click the **AI Terminal** button (sparkle icon) or press `Cmd+K` in the terminal
3. Type this request:
   ```
   install uv package manager on my system
   ```
4. Cursor will:
   - Detect your operating system
   - Generate the correct installation command
   - Ask for confirmation to run it
5. Press Enter to execute

### Method 2: Using Cursor Chat

1. Press `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux) to open Cursor Chat
2. Type:
   ```
   Please install uv Python package manager on my system and verify it's working
   ```
3. Cursor will provide the commands
4. Click "Run" button next to each command

## Creating Project with Cursor AI

Now let's create the entire project structure using Cursor's AI:

### Step 1: Create Project Folder with AI

1. Open Cursor Chat (`Cmd+L` / `Ctrl+L`)
2. Type this prompt:
   ```
   Create a new Python project folder called "hello-world-uv" on my desktop,
   open it in Cursor, and initialize it with uv
   ```
3. Cursor will generate and run the necessary commands

### Step 2: Generate Complete Project Structure

In Cursor Chat, use this comprehensive prompt:

```
Please create a complete Python Hello World project with the following:
1. Initialize with uv init
2. Create a main.py file with:
   - A colorful hello world function
   - Input to get user's name
   - Display personalized greeting
   - Use rich and colorama for formatting
3. Add dependencies: rich, colorama, click
4. Create a tests folder with pytest tests
5. Add a README.md with project description
6. Create a .gitignore file for Python projects
7. Set up pre-commit hooks with black and flake8

Execute all necessary commands and create all files.
```

Cursor will:
- Run all uv commands
- Create all files with content
- Install dependencies
- Set up the complete project structure

## Using Cursor Composer

Cursor Composer is the most powerful way to work with multiple files simultaneously:

### Activating Composer

1. Press `Cmd+I` (Mac) or `Ctrl+I` (Windows/Linux)
2. Or click the "Composer" button in the sidebar

### Creating an Entire Application with Composer

In Composer, type this single prompt:

```
Create a complete Python Hello World application with these features:

Project structure:
- src/hello_world/ directory with __init__.py, main.py, greetings.py, utils.py
- tests/ directory with comprehensive pytest tests
- Modern pyproject.toml with uv configuration
- GitHub Actions workflow for CI/CD
- Dockerfile for containerization
- Makefile with common commands

Features:
- Interactive CLI using Click
- Multiple greeting styles (formal, casual, excited)
- Support for multiple languages (English, Spanish, French, Japanese)
- ASCII art banner
- Configuration file support (YAML)
- Logging with colored output
- Progress bars for batch processing
- Export greetings to JSON/CSV

Make it production-ready with:
- Type hints everywhere
- Comprehensive error handling
- 100% test coverage
- Documentation strings
- Performance optimizations

Use these libraries: click, rich, pyyaml, tqdm, colorlog, pandas

Create all files and run all necessary uv commands to set this up.
```

Composer will:
1. Create the entire directory structure
2. Write all Python files with full implementation
3. Generate test files with test cases
4. Create configuration files
5. Set up CI/CD pipeline
6. Install all dependencies
7. Create documentation

### Reviewing Composer's Work

After Composer finishes:
1. It shows all created/modified files in the sidebar
2. You can review each file by clicking on it
3. Accept all changes with "Accept All" or review individually
4. Composer automatically runs necessary terminal commands

## AI-Powered Development Workflow

### 1. Instant Code Generation

Instead of writing code, describe what you want:

**In any Python file, press `Cmd+K` / `Ctrl+K` and type:**
```
Add a function that generates ASCII art text for any input string
```

Cursor will instantly generate the complete function with proper implementation.

### 2. Automatic Error Fixing

When you encounter an error:

1. The error appears in terminal
2. Press `Cmd+K` / `Ctrl+K`
3. Type: "fix this error"
4. Cursor analyzes the error and fixes it automatically

### 3. Instant Refactoring

Select any code and press `Cmd+K` / `Ctrl+K`:
```
Refactor this to use design patterns and make it more maintainable
```

### 4. Generate Tests Automatically

In Cursor Chat:
```
Generate comprehensive pytest tests for all functions in main.py with edge cases and parameterized tests
```

### 5. Add Features Through Natural Language

```
Add a new feature to save greetings history to SQLite database and display the last 10 greetings
```

Cursor will:
- Add necessary dependencies
- Create database module
- Update main code
- Add tests
- Update documentation

## Advanced Cursor AI Features

### 1. Multi-File Edits

Use `Cmd+K` / `Ctrl+K` with specific instructions:
```
@main.py @greetings.py @utils.py 
Refactor these files to use a proper MVC pattern with controllers and models
```

### 2. Codebase-Wide Changes

In Composer:
```
Convert the entire codebase to use async/await pattern with asyncio
```

### 3. Automatic Documentation

```
Generate comprehensive documentation for all modules including:
- Docstrings in Google style
- README with examples
- API documentation
- Architecture diagram in Mermaid
```

### 4. Performance Optimization

```
Analyze and optimize the codebase for performance:
- Add caching where appropriate
- Optimize loops and data structures
- Add performance benchmarks
- Profile the code and show bottlenecks
```

### 5. Security Audit

```
Perform a security audit and fix any issues:
- Check for SQL injection
- Validate all inputs
- Add rate limiting
- Implement proper error handling
- Add security headers
```

## AI Agent Terminal Commands

Cursor can execute complex terminal operations through natural language:

### Package Management
```
"Install all machine learning related packages I might need for data analysis"
```

### Git Operations
```
"Initialize git, create a proper .gitignore, make initial commit with conventional commit message"
```

### Environment Setup
```
"Set up different uv environments for development, testing, and production with appropriate dependencies"
```

### Deployment
```
"Create Docker setup and deploy this to Google Cloud Run with GitHub Actions"
```

## Tips for Maximum Automation

### 1. Use Descriptive Prompts

Instead of:
```
"add a function"
```

Use:
```
"Add a function called create_rainbow_text that takes a string and returns it with each character in a different color using rich library, with proper type hints and docstring"
```

### 2. Chain Commands

In Cursor Chat, you can chain multiple operations:
```
1. Create a new feature branch
2. Implement user authentication with JWT
3. Add tests for the auth module
4. Create migration scripts
5. Update README with auth documentation
6. Commit with conventional commit message
7. Push to GitHub and create PR
```

### 3. Use Context References

Reference files and symbols directly:
```
@main.py Update the greet function to support @config.yaml settings and add the new languages from @locales.json
```

### 4. Leverage Tab Completion

- Start typing and press Tab for AI completions
- Works for:
  - Function implementations
  - Test cases
  - Documentation
  - Import statements
  - Error handling

### 5. Create Custom Commands

In Cursor Chat:
```
Create a Makefile with these commands:
- make install: Set up uv environment and install dependencies
- make test: Run all tests with coverage
- make format: Format code with black and isort
- make lint: Run all linters
- make run: Run the application
- make clean: Clean up generated files
- make docker: Build and run Docker container
- make deploy: Deploy to production

Then create a justfile as an alternative with the same commands
```

### 6. Batch Operations

Process multiple files at once:
```
For all Python files in src/:
1. Add comprehensive type hints
2. Add docstrings if missing
3. Optimize imports
4. Add logging statements
5. Ensure PEP 8 compliance
```

### 7. Smart Refactoring

```
Analyze the codebase and:
1. Identify code smells
2. Suggest design pattern improvements
3. Find duplicate code
4. Implement the DRY principle
5. Apply SOLID principles where needed
```

## Complete Project Setup in One Prompt

Here's the ultimate Cursor Composer prompt to create an entire production-ready project:

```
Create a complete Python Hello World application called "hello-world-uv" with:

INITIAL SETUP:
- Use uv for dependency management
- Python 3.12+
- Create all directories and files

APPLICATION FEATURES:
- CLI with Click featuring subcommands:
  - greet: Interactive greeting with style options
  - batch: Process multiple names from CSV
  - server: FastAPI web server with greeting endpoints
  - export: Export greetings to various formats
- REST API with FastAPI:
  - GET /greet/{name}
  - POST /greet with JSON body
  - WebSocket for real-time greetings
  - OpenAPI documentation
- Web interface:
  - Simple HTML page with Tailwind CSS
  - JavaScript fetch for API calls
  - Real-time updates via WebSocket
- Database:
  - SQLite with SQLAlchemy ORM
  - Store greeting history
  - Analytics on most greeted names

QUALITY ASSURANCE:
- Testing:
  - Pytest with 100% coverage
  - Unit tests for all functions
  - Integration tests for API
  - End-to-end tests
- Code Quality:
  - Pre-commit hooks (black, isort, flake8, mypy)
  - GitHub Actions CI/CD pipeline
  - SonarQube configuration
  - Code coverage reports
- Documentation:
  - Sphinx documentation
  - API documentation with examples
  - Architecture diagrams
  - User guide

DEVOPS:
- Docker:
  - Multi-stage Dockerfile
  - docker-compose.yml for local development
  - Health checks
- Kubernetes:
  - Deployment manifests
  - Service and Ingress
  - ConfigMaps and Secrets
- Monitoring:
  - Prometheus metrics
  - Structured logging with JSON
  - Sentry error tracking setup
- Scripts:
  - Makefile with all common tasks
  - Shell scripts for deployment
  - Python scripts for data migration

DEPENDENCIES (install with uv):
- Web: fastapi, uvicorn, jinja2, websockets
- CLI: click, rich, typer
- Database: sqlalchemy, alembic
- Testing: pytest, pytest-cov, pytest-asyncio, httpx
- Quality: black, isort, flake8, mypy, pre-commit
- Utils: pydantic, python-dotenv, pyyaml
- Monitoring: prometheus-client, structlog, sentry-sdk

CONFIGURATION:
- .env file for environment variables
- config.yaml for application settings
- logging.conf for logging configuration
- pyproject.toml fully configured
- .gitignore for Python projects
- .dockerignore
- .pre-commit-config.yaml

Execute all necessary commands to:
1. Create the project structure
2. Initialize uv and install all dependencies
3. Create all source files with full implementation
4. Set up git repository
5. Run initial tests
6. Start the FastAPI server

Make this production-ready and follow best practices throughout.
```

## Troubleshooting with AI

### When Something Goes Wrong

Simply describe the problem to Cursor:

```
I'm getting an ImportError when running the application. Fix it.
```

Or be more specific:

```
The FastAPI server won't start and shows a port already in use error. 
Find what's using the port and fix it.
```

### Debugging with AI

```
Add comprehensive debug logging to trace the execution flow and find 
why the greeting function returns None sometimes
```

### Performance Issues

```
The application is running slowly. Profile it and optimize the bottlenecks.
```

## Best Practices for AI-Driven Development

### 1. Iterative Development

Start simple and iterate:
```
First: "Create a basic hello world function"
Then: "Add color support"
Then: "Add multiple language support"
Then: "Add database persistence"
```

### 2. Review AI-Generated Code

Always review with:
```
Review the code for:
- Security vulnerabilities
- Performance issues
- Best practices
- Potential bugs
Provide a detailed analysis and fix any issues found
```

### 3. Maintain Consistency

```
Ensure all code follows:
- Same naming conventions
- Consistent error handling
- Uniform logging patterns
- Standard project structure
```

### 4. Documentation as You Go

After each feature:
```
Update documentation for the new feature including:
- README section
- Docstrings
- Usage examples
- Test documentation
```

## Conclusion

With Cursor IDE's AI agent, you can build entire Python projects using natural language commands. The key is to:

1. **Be specific** in your prompts
2. **Use Composer** for multi-file operations
3. **Chain commands** for complex workflows
4. **Let AI handle** repetitive tasks
5. **Focus on describing** what you want, not how to code it

Remember: Cursor's AI can handle everything from project setup to deployment. The more descriptive your prompts, the better the results. You're not just coding faster; you're coding at the speed of thought!

### Next Steps with Cursor AI

Try these advanced prompts:
- "Convert this project to a microservices architecture"
- "Add machine learning features for greeting prediction"
- "Implement a plugin system for extending greetings"
- "Create a mobile app with React Native that uses our API"
- "Set up a complete MLOps pipeline for continuous learning"

The possibilities are endless when you combine uv's powerful dependency management with Cursor's AI capabilities!