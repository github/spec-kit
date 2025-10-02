# 0001 - Initialize hello-world-qwen project with uv

## Original Prompt

Create a Python 3.12 project called 'hello-world-qwen' using uv. Print the exact shell commands and then run them.

1. Initialize with uv init hello-world-qwen
2. Update main.py at project root file with:
   - A colorful hello world function using rich library (for consistent styling)
   - Input to get user's name
   - Display personalized greeting using rich library
3. Add dependencies: rich
4. Create a tests folder with pytest tests
5. Add a README.md with project description
6. Create a .gitignore file for Python projects
7. Set up pre-commit hooks with black and flake8

Execute all necessary commands and create all files. After completion document this prompt and the output in /prompts/** directory. Create a Numbered file i.e: 0001-init-project.prompt.md

## Shell Commands Executed

```bash
# 1. Initialize the project
uv init hello-world-qwen

# 2. Update main.py with colorful hello world function
# (Content updated via edit tool)

# 3. Add rich dependency
cd hello-world-qwen && uv add rich

# 4. Create tests folder and add pytest
mkdir -p hello-world-qwen/tests && touch hello-world-qwen/tests/__init__.py
# Created test file via write_file tool
cd hello-world-qwen && uv add --dev pytest

# 5. Add README.md
# (Content created via write_file tool)

# 6. Create .gitignore
# (Content created via write_file tool)

# 7. Set up pre-commit hooks with black and flake8
cd hello-world-qwen && uv add --dev pre-commit black flake8
# Created .pre-commit-config.yaml via write_file tool
cd hello-world-qwen && pre-commit install
```

## Project Structure Created

```
hello-world-qwen/
├── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── README.md
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── uv.lock
└── .venv/
```

## Dependencies Added

- rich (runtime dependency)
- pytest, pre-commit, black, flake8 (dev dependencies)

## Files Created

- main.py: Contains colorful hello world function with rich library
- tests/test_main.py: Contains pytest tests for main.py
- README.md: Project description and usage instructions
- .gitignore: Standard Python git ignore rules
- .pre-commit-config.yaml: Configuration for black and flake8 pre-commit hooks