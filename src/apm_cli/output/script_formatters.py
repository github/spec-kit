"""Professional CLI output formatters for APM script execution."""

from typing import Dict, List, Optional
from pathlib import Path

try:
    from rich.console import Console
    from rich.text import Text
    from rich.panel import Panel
    from rich.tree import Tree
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ScriptExecutionFormatter:
    """Professional formatter for script execution output following CLI UX design plan."""
    
    def __init__(self, use_color: bool = True):
        """Initialize formatter.
        
        Args:
            use_color: Whether to use colors and rich formatting.
        """
        self.use_color = use_color and RICH_AVAILABLE
        self.console = Console() if self.use_color else None
    
    def format_script_header(self, script_name: str, params: Dict[str, str]) -> List[str]:
        """Format the script execution header with parameters.
        
        Args:
            script_name: Name of the script being executed
            params: Parameters passed to the script
            
        Returns:
            List of formatted lines
        """
        lines = []
        
        # Main header
        if self.use_color:
            lines.append(self._styled(f"🚀 Running script: {script_name}", "cyan bold"))
        else:
            lines.append(f"🚀 Running script: {script_name}")
        
        # Parameters tree if any exist
        if params:
            for param_name, param_value in params.items():
                param_line = f"  - {param_name}: {param_value}"
                if self.use_color:
                    lines.append(self._styled(param_line, "dim"))
                else:
                    lines.append(param_line)
        
        return lines
    
    def format_compilation_progress(self, prompt_files: List[str]) -> List[str]:
        """Format prompt compilation progress.
        
        Args:
            prompt_files: List of prompt files being compiled
            
        Returns:
            List of formatted lines
        """
        if not prompt_files:
            return []
        
        lines = []
        
        if len(prompt_files) == 1:
            if self.use_color:
                lines.append(self._styled("Compiling prompt...", "cyan"))
            else:
                lines.append("Compiling prompt...")
        else:
            if self.use_color:
                lines.append(self._styled(f"Compiling {len(prompt_files)} prompts...", "cyan"))
            else:
                lines.append(f"Compiling {len(prompt_files)} prompts...")
        
        # Show each file being compiled
        for prompt_file in prompt_files:
            file_line = f"├─ {prompt_file}"
            if self.use_color:
                lines.append(self._styled(file_line, "dim"))
            else:
                lines.append(file_line)
        
        # Change last ├─ to └─
        if lines and len(lines) > 1:
            lines[-1] = lines[-1].replace("├─", "└─")
        
        return lines
    
    def format_runtime_execution(self, runtime: str, command: str, content_length: int) -> List[str]:
        """Format runtime command execution with content preview.
        
        Args:
            runtime: Name of the runtime (copilot, codex, llm)
            command: The command being executed
            content_length: Length of the content being passed
            
        Returns:
            List of formatted lines
        """
        lines = []
        
        # Runtime detection and styling
        runtime_colors = {
            'copilot': 'blue',
            'codex': 'green', 
            'llm': 'magenta',
            'unknown': 'white'
        }
        
        runtime_color = runtime_colors.get(runtime, 'white')
        
        # Execution header
        if self.use_color:
            lines.append(self._styled(f"Executing {runtime} runtime...", f"{runtime_color} bold"))
        else:
            lines.append(f"Executing {runtime} runtime...")
        
        # Command structure
        command_line = f"├─ Command: {command}"
        if self.use_color:
            lines.append(self._styled(command_line, "dim"))
        else:
            lines.append(command_line)
        
        # Content size
        content_line = f"└─ Prompt content: {content_length:,} characters"
        if self.use_color:
            lines.append(self._styled(content_line, "dim"))
        else:
            lines.append(content_line)
        
        return lines
    
    def format_content_preview(self, content: str, max_preview: int = 200) -> List[str]:
        """Format content preview with professional styling.
        
        Args:
            content: The full content to preview
            max_preview: Maximum characters to show in preview
            
        Returns:
            List of formatted lines
        """
        lines = []
        
        # Content preview
        content_preview = content[:max_preview] + "..." if len(content) > max_preview else content
        
        if self.use_color:
            lines.append(self._styled("Prompt preview:", "cyan"))
        else:
            lines.append("Prompt preview:")
        
        # Content in a box for better readability
        if self.use_color and RICH_AVAILABLE and self.console:
            try:
                panel = Panel(
                    content_preview, 
                    title=f"Content ({len(content):,} characters)",
                    border_style="dim",
                    title_align="left"
                )
                with self.console.capture() as capture:
                    self.console.print(panel)
                panel_output = capture.get()
                if panel_output.strip():
                    lines.extend(panel_output.split('\n'))
            except:
                # Fallback to simple formatting
                lines.append("─" * 50)
                lines.append(content_preview)
                lines.append("─" * 50)
        else:
            # Simple text fallback
            lines.append("─" * 50)
            lines.append(content_preview)
            lines.append("─" * 50)
        
        return lines
    
    def format_environment_setup(self, runtime: str, env_vars_set: List[str]) -> List[str]:
        """Format environment setup information.
        
        Args:
            runtime: Name of the runtime
            env_vars_set: List of environment variables that were set
            
        Returns:
            List of formatted lines
        """
        if not env_vars_set:
            return []
        
        lines = []
        
        if self.use_color:
            lines.append(self._styled("Environment setup:", "cyan"))
        else:
            lines.append("Environment setup:")
        
        for env_var in env_vars_set:
            env_line = f"├─ {env_var}: configured"
            if self.use_color:
                lines.append(self._styled(env_line, "dim"))
            else:
                lines.append(env_line)
        
        # Change last ├─ to └─
        if lines and len(lines) > 1:
            lines[-1] = lines[-1].replace("├─", "└─")
        
        return lines
    
    def format_execution_success(self, runtime: str, execution_time: Optional[float] = None) -> List[str]:
        """Format successful execution result.
        
        Args:
            runtime: Name of the runtime that executed
            execution_time: Optional execution time in seconds
            
        Returns:
            List of formatted lines
        """
        lines = []
        
        success_msg = f"✅ {runtime.title()} execution completed successfully"
        if execution_time is not None:
            success_msg += f" ({execution_time:.2f}s)"
        
        if self.use_color:
            lines.append(self._styled(success_msg, "green bold"))
        else:
            lines.append(success_msg)
        
        return lines
    
    def format_execution_error(self, runtime: str, error_code: int, error_msg: Optional[str] = None) -> List[str]:
        """Format execution error result.
        
        Args:
            runtime: Name of the runtime that failed
            error_code: Exit code from the failed execution
            error_msg: Optional error message
            
        Returns:
            List of formatted lines
        """
        lines = []
        
        error_header = f"✗ {runtime.title()} execution failed (exit code: {error_code})"
        if self.use_color:
            lines.append(self._styled(error_header, "red bold"))
        else:
            lines.append(error_header)
        
        if error_msg:
            # Format error message with proper indentation
            error_lines = error_msg.split('\n')
            for line in error_lines:
                if line.strip():
                    formatted_line = f"  {line}"
                    if self.use_color:
                        lines.append(self._styled(formatted_line, "red"))
                    else:
                        lines.append(formatted_line)
        
        return lines
    
    def format_subprocess_details(self, args: List[str], content_length: int) -> List[str]:
        """Format subprocess execution details for debugging.
        
        Args:
            args: The subprocess arguments (without content)
            content_length: Length of content being passed
            
        Returns:
            List of formatted lines
        """
        lines = []
        
        if self.use_color:
            lines.append(self._styled("Subprocess execution:", "cyan"))
        else:
            lines.append("Subprocess execution:")
        
        # Show command structure
        args_display = " ".join(f'"{arg}"' if " " in arg else arg for arg in args)
        command_line = f"├─ Args: {args_display}"
        if self.use_color:
            lines.append(self._styled(command_line, "dim"))
        else:
            lines.append(command_line)
        
        # Show content info
        content_line = f"└─ Content: +{content_length:,} chars appended"
        if self.use_color:
            lines.append(self._styled(content_line, "dim"))
        else:
            lines.append(content_line)
        
        return lines
    
    def _styled(self, text: str, style: str) -> str:
        """Apply styling to text with rich fallback."""
        if self.use_color and RICH_AVAILABLE and self.console:
            styled_text = Text(text)
            styled_text.style = style
            with self.console.capture() as capture:
                self.console.print(styled_text, end="")
            return capture.get()
        else:
            return text