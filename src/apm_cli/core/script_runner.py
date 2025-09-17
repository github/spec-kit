"""Script runner for APM NPM-like script execution."""

import os
import re
import subprocess
import time
import yaml
from pathlib import Path
from typing import Dict, Optional

from .token_manager import setup_runtime_environment
from ..output.script_formatters import ScriptExecutionFormatter


class ScriptRunner:
    """Executes APM scripts with auto-compilation of .prompt.md files."""
    
    def __init__(self, compiler=None, use_color: bool = True):
        """Initialize script runner with optional compiler.
        
        Args:
            compiler: Optional prompt compiler instance
            use_color: Whether to use colored output
        """
        self.compiler = compiler or PromptCompiler()
        self.formatter = ScriptExecutionFormatter(use_color=use_color)
    
    def run_script(self, script_name: str, params: Dict[str, str]) -> bool:
        """Run a script from apm.yml with parameter substitution.
        
        Args:
            script_name: Name of the script to run
            params: Parameters for compilation and script execution
            
        Returns:
            bool: True if script executed successfully
        """
        # Display script execution header
        header_lines = self.formatter.format_script_header(script_name, params)
        for line in header_lines:
            print(line)
        
        # Load apm.yml configuration
        config = self._load_config()
        if not config:
            raise RuntimeError("No apm.yml found in current directory")
        
        scripts = config.get('scripts', {})
        if script_name not in scripts:
            available = ', '.join(scripts.keys()) if scripts else 'none'
            raise RuntimeError(f"Script '{script_name}' not found. Available scripts: {available}")
        
        # Get the script command
        command = scripts[script_name]
        
        # Auto-compile any .prompt.md files in the command
        compiled_command, compiled_prompt_files, runtime_content = self._auto_compile_prompts(command, params)
        
        # Show compilation progress if needed
        if compiled_prompt_files:
            compilation_lines = self.formatter.format_compilation_progress(compiled_prompt_files)
            for line in compilation_lines:
                print(line)
        
        # Detect runtime and show execution details
        runtime = self._detect_runtime(compiled_command)
        
        # Execute the final command
        if runtime_content is not None:
            # Show runtime execution details
            execution_lines = self.formatter.format_runtime_execution(
                runtime, compiled_command, len(runtime_content)
            )
            for line in execution_lines:
                print(line)
            
            # Show content preview
            preview_lines = self.formatter.format_content_preview(runtime_content)
            for line in preview_lines:
                print(line)
        
        try:
            # Set up GitHub token environment for all runtimes using centralized manager
            env = setup_runtime_environment(os.environ.copy())
            
            # Show environment setup if relevant
            env_vars_set = []
            if 'GITHUB_TOKEN' in env and env['GITHUB_TOKEN']:
                env_vars_set.append('GITHUB_TOKEN')
            if 'GITHUB_APM_PAT' in env and env['GITHUB_APM_PAT']:
                env_vars_set.append('GITHUB_APM_PAT')
            
            if env_vars_set:
                env_lines = self.formatter.format_environment_setup(runtime, env_vars_set)
                for line in env_lines:
                    print(line)
            
            # Track execution time
            start_time = time.time()
            
            # Check if this command needs subprocess execution (has compiled content)
            if runtime_content is not None:
                # Use argument list approach for all runtimes to avoid shell parsing issues
                result = self._execute_runtime_command(compiled_command, runtime_content, env)
            else:
                # Use regular shell execution for other commands
                result = subprocess.run(compiled_command, shell=True, check=True, env=env)
            
            execution_time = time.time() - start_time
            
            # Show success message
            success_lines = self.formatter.format_execution_success(runtime, execution_time)
            for line in success_lines:
                print(line)
            
            return result.returncode == 0
            
        except subprocess.CalledProcessError as e:
            execution_time = time.time() - start_time
            
            # Show error message
            error_lines = self.formatter.format_execution_error(runtime, e.returncode)
            for line in error_lines:
                print(line)
            
            raise RuntimeError(f"Script execution failed with exit code {e.returncode}")
    
    def list_scripts(self) -> Dict[str, str]:
        """List all available scripts from apm.yml.
        
        Returns:
            Dict mapping script names to their commands
        """
        config = self._load_config()
        return config.get('scripts', {}) if config else {}
    
    def _load_config(self) -> Optional[Dict]:
        """Load apm.yml from current directory."""
        config_path = Path('apm.yml')
        if not config_path.exists():
            return None
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _auto_compile_prompts(self, command: str, params: Dict[str, str]) -> tuple[str, list[str], str]:
        """Auto-compile .prompt.md files and transform runtime commands.
        
        Args:
            command: Original script command
            params: Parameters for compilation
            
        Returns:
            Tuple of (compiled_command, list_of_compiled_prompt_files, runtime_content_or_none)
        """
        # Find all .prompt.md files in the command using regex
        prompt_files = re.findall(r'(\S+\.prompt\.md)', command)
        compiled_prompt_files = []
        runtime_content = None
        
        compiled_command = command
        for prompt_file in prompt_files:
            # Compile the prompt file with current params
            compiled_path = self.compiler.compile(prompt_file, params)
            compiled_prompt_files.append(prompt_file)
            
            # Read the compiled content
            with open(compiled_path, 'r') as f:
                compiled_content = f.read().strip()
            
            # Check if this is a runtime command (copilot, codex, llm) before transformation
            is_runtime_cmd = any(runtime in command for runtime in ['copilot', 'codex', 'llm']) and re.search(re.escape(prompt_file), command)
            
            # Transform command based on runtime pattern
            compiled_command = self._transform_runtime_command(
                compiled_command, prompt_file, compiled_content, compiled_path
            )
            
            # Store content for runtime commands that need subprocess execution
            if is_runtime_cmd:
                runtime_content = compiled_content
        
        return compiled_command, compiled_prompt_files, runtime_content
    
    def _transform_runtime_command(self, command: str, prompt_file: str, 
                                 compiled_content: str, compiled_path: str) -> str:
        """Transform runtime commands to their proper execution format.
        
        Args:
            command: Original command
            prompt_file: Original .prompt.md file path
            compiled_content: Compiled prompt content as string
            compiled_path: Path to compiled .txt file
            
        Returns:
            Transformed command for proper runtime execution
        """
        # Handle environment variables prefix (e.g., "ENV1=val1 ENV2=val2 codex [args] file.prompt.md")
        # More robust approach: split by runtime commands to separate env vars from command
        runtime_commands = ['codex', 'copilot', 'llm']
        
        for runtime_cmd in runtime_commands:
            runtime_pattern = f' {runtime_cmd} '
            if runtime_pattern in command and re.search(re.escape(prompt_file), command):
                parts = command.split(runtime_pattern, 1)
                potential_env_part = parts[0]
                runtime_part = runtime_cmd + ' ' + parts[1]
                
                # Check if the first part looks like environment variables (has = signs)
                if '=' in potential_env_part and not potential_env_part.startswith(runtime_cmd):
                    env_vars = potential_env_part
                    
                    # Extract arguments before and after the prompt file from runtime part
                    runtime_match = re.search(f'{runtime_cmd}\\s+(.*?)(' + re.escape(prompt_file) + r')(.*?)$', runtime_part)
                    if runtime_match:
                        args_before_file = runtime_match.group(1).strip()
                        args_after_file = runtime_match.group(3).strip()
                        
                        # Build the command based on runtime
                        if runtime_cmd == 'codex':
                            if args_before_file:
                                result = f"{env_vars} codex exec {args_before_file}"
                            else:
                                result = f"{env_vars} codex exec"
                        else:
                            # For copilot and llm, keep the runtime name and args
                            result = f"{env_vars} {runtime_cmd}"
                            if args_before_file:
                                # Remove any existing -p flag since we'll handle it in execution
                                cleaned_args = args_before_file.replace('-p', '').strip()
                                if cleaned_args:
                                    result += f" {cleaned_args}"
                        
                        if args_after_file:
                            result += f" {args_after_file}"
                        return result
        
        # Handle individual runtime patterns without environment variables
        
        # Handle "codex [args] file.prompt.md [more_args]" -> "codex exec [args] [more_args]"  
        if re.search(r'codex\s+.*' + re.escape(prompt_file), command):
            match = re.search(r'codex\s+(.*?)(' + re.escape(prompt_file) + r')(.*?)$', command)
            if match:
                args_before_file = match.group(1).strip()
                args_after_file = match.group(3).strip()
                
                result = "codex exec"
                if args_before_file:
                    result += f" {args_before_file}"
                if args_after_file:
                    result += f" {args_after_file}"
                return result
        
        # Handle "copilot [args] file.prompt.md [more_args]" -> "copilot [args] [more_args]"
        elif re.search(r'copilot\s+.*' + re.escape(prompt_file), command):
            match = re.search(r'copilot\s+(.*?)(' + re.escape(prompt_file) + r')(.*?)$', command)
            if match:
                args_before_file = match.group(1).strip()
                args_after_file = match.group(3).strip()
                
                result = "copilot"
                if args_before_file:
                    # Remove any existing -p flag since we'll handle it in execution
                    cleaned_args = args_before_file.replace('-p', '').strip()
                    if cleaned_args:
                        result += f" {cleaned_args}"
                if args_after_file:
                    result += f" {args_after_file}"
                return result
        
        # Handle "llm [args] file.prompt.md [more_args]" -> "llm [args] [more_args]"
        elif re.search(r'llm\s+.*' + re.escape(prompt_file), command):
            match = re.search(r'llm\s+(.*?)(' + re.escape(prompt_file) + r')(.*?)$', command)
            if match:
                args_before_file = match.group(1).strip()
                args_after_file = match.group(3).strip()
                
                result = "llm"
                if args_before_file:
                    result += f" {args_before_file}"
                if args_after_file:
                    result += f" {args_after_file}"
                return result
        
        # Handle bare "file.prompt.md" -> "codex exec" (default to codex)
        elif command.strip() == prompt_file:
            return "codex exec"
        
        # Fallback: just replace file path with compiled path (for non-runtime commands)
        return command.replace(prompt_file, compiled_path)

    def _detect_runtime(self, command: str) -> str:
        """Detect which runtime is being used in the command.
        
        Args:
            command: The command to analyze
            
        Returns:
            Name of the detected runtime (copilot, codex, llm, or unknown)
        """
        command_lower = command.lower().strip()
        if command_lower.startswith('copilot'):
            return 'copilot'
        elif command_lower.startswith('codex'):
            return 'codex'  
        elif command_lower.startswith('llm'):
            return 'llm'
        else:
            return 'unknown'

    def _execute_runtime_command(self, command: str, content: str, env: dict) -> subprocess.CompletedProcess:
        """Execute a runtime command using subprocess argument list to avoid shell parsing issues.
        
        Args:
            command: The simplified runtime command (without content)
            content: The compiled prompt content to pass to the runtime
            env: Environment variables
            
        Returns:
            subprocess.CompletedProcess: The result of the command execution
        """
        import shlex
        
        # Parse the command into arguments
        args = shlex.split(command.strip())
        
        # Handle environment variables at the beginning of the command
        # Extract environment variables (key=value pairs) from the beginning of args
        env_vars = env.copy()  # Start with existing environment
        actual_command_args = []
        
        for arg in args:
            if '=' in arg and not actual_command_args:
                # This looks like an environment variable and we haven't started the actual command yet
                key, value = arg.split('=', 1)
                # Validate environment variable name with restrictive pattern
                # Only allow uppercase letters, numbers, and underscores, starting with letter or underscore
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                    env_vars[key] = value
                    continue
            # Once we hit a non-env-var argument, everything else is part of the command
            actual_command_args.append(arg)
        
        # Determine how to pass content based on runtime
        runtime = self._detect_runtime(' '.join(actual_command_args))
        
        if runtime == 'copilot':
            # Copilot uses -p flag
            actual_command_args.extend(["-p", content])
        elif runtime == 'codex':
            # Codex exec expects content as the last argument
            actual_command_args.append(content)
        elif runtime == 'llm':
            # LLM expects content as argument
            actual_command_args.append(content)
        else:
            # Default: assume content as last argument
            actual_command_args.append(content)
        
        # Show subprocess details for debugging
        subprocess_lines = self.formatter.format_subprocess_details(actual_command_args[:-1], len(content))
        for line in subprocess_lines:
            print(line)
        
        # Show environment variables if any were extracted
        if len(env_vars) > len(env):
            extracted_env_vars = []
            for key, value in env_vars.items():
                if key not in env:
                    extracted_env_vars.append(f"{key}={value}")
            if extracted_env_vars:
                env_lines = self.formatter.format_environment_setup("command", extracted_env_vars)
                for line in env_lines:
                    print(line)
        
        # Execute using argument list (no shell interpretation) with updated environment
        return subprocess.run(actual_command_args, check=True, env=env_vars)


class PromptCompiler:
    """Compiles .prompt.md files with parameter substitution."""
    
    DEFAULT_COMPILED_DIR = Path('.apm/compiled')
    
    def __init__(self):
        """Initialize compiler."""
        self.compiled_dir = self.DEFAULT_COMPILED_DIR
    
    def compile(self, prompt_file: str, params: Dict[str, str]) -> str:
        """Compile a .prompt.md file with parameter substitution.
        
        Args:
            prompt_file: Path to the .prompt.md file
            params: Parameters to substitute
            
        Returns:
            Path to the compiled file
        """
        # Resolve the prompt file path - check local first, then dependencies
        prompt_path = self._resolve_prompt_file(prompt_file)
        
        # Now ensure compiled directory exists
        self.compiled_dir.mkdir(parents=True, exist_ok=True)
        
        with open(prompt_path, 'r') as f:
            content = f.read()
        
        # Parse frontmatter and content
        if content.startswith('---'):
            # Split frontmatter and content
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                main_content = parts[2].strip()
            else:
                main_content = content
        else:
            main_content = content
        
        # Substitute parameters in content
        compiled_content = self._substitute_parameters(main_content, params)
        
        # Generate output file path
        output_name = prompt_path.stem.replace('.prompt', '') + '.txt'
        output_path = self.compiled_dir / output_name
        
        # Write compiled content
        with open(output_path, 'w') as f:
            f.write(compiled_content)
        
        return str(output_path)
    
    def _resolve_prompt_file(self, prompt_file: str) -> Path:
        """Resolve prompt file path, checking local directory first, then dependencies.
        
        Args:
            prompt_file: Relative path to the .prompt.md file
            
        Returns:
            Path: Resolved path to the prompt file
            
        Raises:
            FileNotFoundError: If prompt file is not found in local or dependency modules
        """
        prompt_path = Path(prompt_file)
        
        # First check if it exists in current directory (local)
        if prompt_path.exists():
            return prompt_path
        
        # If not found locally, search in dependency modules
        apm_modules_dir = Path("apm_modules")
        if apm_modules_dir.exists():
            # Search all dependency directories for the prompt file
            for dep_dir in apm_modules_dir.iterdir():
                if dep_dir.is_dir():
                    # Check in the root of the dependency
                    dep_prompt_path = dep_dir / prompt_file
                    if dep_prompt_path.exists():
                        return dep_prompt_path
                    
                    # Also check in common subdirectories
                    for subdir in ['prompts', '.', 'workflows']:
                        sub_prompt_path = dep_dir / subdir / prompt_file
                        if sub_prompt_path.exists():
                            return sub_prompt_path
        
        # If still not found, raise an error with helpful message
        searched_locations = [
            f"Local: {prompt_path}",
        ]
        
        if apm_modules_dir.exists():
            searched_locations.append("Dependencies:")
            for dep_dir in apm_modules_dir.iterdir():
                if dep_dir.is_dir():
                    searched_locations.append(f"  - {dep_dir.name}/{prompt_file}")
        
        raise FileNotFoundError(
            f"Prompt file '{prompt_file}' not found.\n"
            f"Searched in:\n" + "\n".join(searched_locations) + 
            f"\n\nTip: Run 'apm install' to ensure dependencies are installed."
        )
    
    def _substitute_parameters(self, content: str, params: Dict[str, str]) -> str:
        """Substitute parameters in content.
        
        Args:
            content: Content to process
            params: Parameters to substitute
            
        Returns:
            Content with parameters substituted
        """
        result = content
        for key, value in params.items():
            # Replace ${input:key} placeholders
            placeholder = f"${{input:{key}}}"
            result = result.replace(placeholder, str(value))
        return result
