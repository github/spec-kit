## Prompt

```
Create a Python 3.12 project called 'hello-world-gemini' using uv. Print the exact shell commands and then run them.

1. Initialize with uv init hello-world-gemini
2. Update main.py at project root file with:
   - A colorful hello world function using rich library (for consistent styling)
   - Input to get user's name
   - Display personalized greeting using rich library
3. Add dependencies: rich
4. Create a tests folder with pytest tests
5. Add a README.md with project description
6. Create a .gitignore file for Python projects
7. Set up pre-commit hooks with black and flake8

Execute all necessary commands and create all files. Use CLI commands where it;s efficient istead of writing files i.e: when creating a new project use uv init <proj_name> tog et boilerplate code. After completion document this prompt and the output in /prompts/** directory. Create a Numbered file i.e: 0001-init-project.prompt.md
```

## Output

```
> uv init hello-world-gemini
Initialized project `hello-world-gemini` at `/Users/mjs/Documents/code/panaversity-official/learn-agentic-ai/06_prompt_driven_development/02_start_prompt_driven_development/03_gemini_cli/hello-world-gemini`

> write_file(path='/Users/mjs/Documents/code/panaversity-official/learn-agentic-ai/06_prompt_driven_development/02_start_prompt_driven_development/03_gemini_cli/hello-world-gemini/main.py', ...)

> uv add rich pytest
Using CPython 3.13.1
Creating virtual environment at: .venv
Resolved 10 packages in 419ms
Installed 8 packages in 48ms
 + iniconfig==2.1.0
 + markdown-it-py==4.0.0
 + mdurl==0.1.2
 + packaging==25.0
 + pluggy==1.6.0
 + pygments==2.19.2
 + pytest==8.4.2
 + rich==14.1.0

> mkdir tests

> write_file(path='/Users/mjs/Documents/code/panaversity-official/learn-agentic-ai/06_prompt_driven_development/02_start_prompt_driven_development/03_gemini_cli/hello-world-gemini/tests/test_main.py', ...)

> write_file(path='/Users/mjs/Documents/code/panaversity-official/learn-agentic-ai/06_prompt_driven_development/02_start_prompt_driven_development/03_gemini_cli/hello-world-gemini/README.md', ...)

> web_fetch(prompt='https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore')

> write_file(path='/Users/mjs/Documents/code/panaversity-official/learn-agentic-ai/06_prompt_driven_development/02_start_prompt_driven_development/03_gemini_cli/hello-world-gemini/.gitignore', ...)

> uv pip install pre-commit
Resolved 9 packages in 6ms
Installed 9 packages in 20ms
 + cfgv==3.4.0
 + distlib==0.4.0
 + filelock==3.19.1
 + identify==2.6.14
 + nodeenv==1.9.1
 + platformdirs==4.4.0
 + pre-commit==4.3.0
 + pyyaml==6.0.2
 + virtualenv==20.34.0

> write_file(path='/Users/mjs/Documents/code/panaversity-official/learn-agentic-ai/06_prompt_driven_development/02_start_prompt_driven_development/03_gemini_cli/hello-world-gemini/.pre-commit-config.yaml', ...)

> pre-commit install
pre-commit installed at .git/hooks/pre-commit

> mkdir prompts

> write_file(path='/Users/mjs/Documents/code/panaversity-official/learn-agentic-ai/06_prompt_driven_development/02_start_prompt_driven_development/03_gemini_cli/prompts/0001-init-project.prompt.md', ...)
```
