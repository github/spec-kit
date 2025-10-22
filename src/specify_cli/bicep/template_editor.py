"""
Interactive Bicep template editor with guided assistance.

This module provides an interactive editing experience for Bicep templates,
including real-time validation, intelligent suggestions, and guided modifications.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import json
import re
from dataclasses import dataclass, field
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

from .mcp_client import MCPClient
from .arm_validator import ARMValidator
from .security_analyzer import SecurityAnalyzer

logger = logging.getLogger(__name__)
console = Console()


class EditMode(str, Enum):
    """Template editing modes."""
    
    INTERACTIVE = "interactive"
    GUIDED = "guided" 
    EXPERT = "expert"


class EditAction(str, Enum):
    """Available edit actions."""
    
    ADD_RESOURCE = "add_resource"
    MODIFY_RESOURCE = "modify_resource"
    REMOVE_RESOURCE = "remove_resource"
    ADD_PARAMETER = "add_parameter"
    MODIFY_PARAMETER = "modify_parameter"
    REMOVE_PARAMETER = "remove_parameter"
    ADD_OUTPUT = "add_output"
    MODIFY_OUTPUT = "modify_output"
    REMOVE_OUTPUT = "remove_output"
    SET_METADATA = "set_metadata"
    VALIDATE = "validate"
    PREVIEW = "preview"
    SAVE = "save"
    EXIT = "exit"


@dataclass
class EditSuggestion:
    """A suggested edit for the template."""
    
    id: str
    title: str
    description: str
    action_type: EditAction
    
    # Target information
    target_path: str  # JSON path to the element being edited
    target_name: Optional[str] = None
    
    # Edit details
    new_content: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    
    # Metadata
    confidence: float = 1.0  # 0-1
    risk_level: str = "low"  # low, medium, high
    
    def apply_to_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Apply this suggestion to a template."""
        # Implementation would modify the template based on the suggestion
        # This is a simplified version
        result = template.copy()
        
        if self.action_type == EditAction.ADD_RESOURCE:
            if 'resources' not in result:
                result['resources'] = []
            result['resources'].append(self.new_content)
        
        elif self.action_type == EditAction.ADD_PARAMETER:
            if 'parameters' not in result:
                result['parameters'] = {}
            result['parameters'].update(self.new_content)
        
        return result


@dataclass
class EditSession:
    """An editing session for a Bicep template."""
    
    template_path: Path
    original_content: str
    current_content: str
    
    # Session state
    session_id: str
    start_time: datetime
    mode: EditMode
    
    # Edit history
    edit_history: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[EditSuggestion] = field(default_factory=list)
    
    # Validation results
    last_validation: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = field(default_factory=list)
    
    def add_edit(self, action: EditAction, description: str, content: str):
        """Add an edit to the session history."""
        edit_entry = {
            'timestamp': datetime.utcnow(),
            'action': action.value,
            'description': description,
            'old_content': self.current_content,
            'new_content': content
        }
        self.edit_history.append(edit_entry)
        self.current_content = content
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return len(self.edit_history) > 0
    
    def undo_last_edit(self) -> bool:
        """Undo the last edit."""
        if not self.can_undo():
            return False
        
        last_edit = self.edit_history.pop()
        self.current_content = last_edit['old_content']
        return True


class TemplateEditor:
    """
    Interactive Bicep template editor with guided assistance.
    
    Provides real-time validation, intelligent suggestions, and guided
    modifications for Bicep templates.
    """
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self.validator = ARMValidator()
        self.security_analyzer = SecurityAnalyzer()
        
        # Active sessions
        self.active_sessions: Dict[str, EditSession] = {}
        
        # Editor configuration
        self.auto_validate = True
        self.show_suggestions = True
        self.expert_mode = False
    
    async def edit_template(
        self,
        template_path: Path,
        mode: EditMode = EditMode.INTERACTIVE
    ) -> bool:
        """
        Start an interactive editing session for a Bicep template.
        
        Args:
            template_path: Path to the Bicep template file
            mode: Editing mode (interactive, guided, expert)
            
        Returns:
            True if template was saved, False if cancelled
        """
        console.print(f"\n[bold blue]Opening template editor for:[/bold blue] {template_path}")
        
        # Load template
        if not template_path.exists():
            console.print(f"[red]Error:[/red] Template file not found: {template_path}")
            return False
        
        original_content = template_path.read_text(encoding='utf-8')
        
        # Create editing session
        session = EditSession(
            template_path=template_path,
            original_content=original_content,
            current_content=original_content,
            session_id=f"edit_{datetime.utcnow().timestamp()}",
            start_time=datetime.utcnow(),
            mode=mode
        )
        
        self.active_sessions[session.session_id] = session
        
        try:
            # Initial validation
            await self._validate_template(session)
            
            # Start editing loop based on mode
            if mode == EditMode.INTERACTIVE:
                result = await self._interactive_edit_loop(session)
            elif mode == EditMode.GUIDED:
                result = await self._guided_edit_loop(session)
            else:  # EXPERT
                result = await self._expert_edit_loop(session)
            
            return result
        
        finally:
            # Clean up session
            if session.session_id in self.active_sessions:
                del self.active_sessions[session.session_id]
    
    async def _interactive_edit_loop(self, session: EditSession) -> bool:
        """Run interactive editing loop with menu-driven interface."""
        
        while True:
            # Display current status
            self._display_session_status(session)
            
            # Show available actions
            actions = self._get_available_actions(session)
            action = self._prompt_for_action(actions)
            
            if action == EditAction.EXIT:
                if self._has_unsaved_changes(session):
                    if Confirm.ask("You have unsaved changes. Exit anyway?"):
                        return False
                else:
                    return False
            
            elif action == EditAction.SAVE:
                if await self._save_template(session):
                    console.print("[green]✓[/green] Template saved successfully!")
                    return True
            
            elif action == EditAction.VALIDATE:
                await self._validate_template(session)
            
            elif action == EditAction.PREVIEW:
                self._preview_template(session)
            
            elif action == EditAction.ADD_RESOURCE:
                await self._add_resource_interactive(session)
            
            elif action == EditAction.MODIFY_RESOURCE:
                await self._modify_resource_interactive(session)
            
            elif action == EditAction.REMOVE_RESOURCE:
                await self._remove_resource_interactive(session)
            
            elif action == EditAction.ADD_PARAMETER:
                await self._add_parameter_interactive(session)
            
            elif action == EditAction.MODIFY_PARAMETER:
                await self._modify_parameter_interactive(session)
            
            # Handle other actions...
    
    async def _guided_edit_loop(self, session: EditSession) -> bool:
        """Run guided editing with step-by-step assistance."""
        
        console.print("\n[bold green]Welcome to Guided Template Editing![/bold green]")
        console.print("I'll help you improve your template step by step.\n")
        
        # Generate suggestions
        await self._generate_suggestions(session)
        
        while session.suggestions:
            suggestion = session.suggestions[0]
            
            # Display suggestion
            self._display_suggestion(suggestion)
            
            # Ask user what to do
            choice = Prompt.ask(
                "What would you like to do?",
                choices=["apply", "skip", "explain", "exit"],
                default="apply"
            )
            
            if choice == "apply":
                await self._apply_suggestion(session, suggestion)
                session.suggestions.pop(0)
                
            elif choice == "skip":
                session.suggestions.pop(0)
                
            elif choice == "explain":
                self._explain_suggestion(suggestion)
                continue
                
            elif choice == "exit":
                return await self._save_template(session) if self._has_unsaved_changes(session) else False
        
        console.print("\n[green]✓[/green] All suggestions processed!")
        return await self._save_template(session) if self._has_unsaved_changes(session) else False
    
    async def _expert_edit_loop(self, session: EditSession) -> bool:
        """Run expert mode with direct template editing."""
        
        console.print("\n[bold yellow]Expert Mode:[/bold yellow] Direct template editing")
        console.print("Available commands: validate, save, exit, undo")
        
        while True:
            try:
                # Show current validation status
                if session.validation_errors:
                    console.print(f"\n[red]Validation Errors ({len(session.validation_errors)}):[/red]")
                    for error in session.validation_errors:
                        console.print(f"  • {error}")
                
                # Get command from user
                command = Prompt.ask("\nEnter command", default="validate").lower().strip()
                
                if command == "exit":
                    return False
                elif command == "save":
                    return await self._save_template(session)
                elif command == "validate":
                    await self._validate_template(session)
                elif command == "undo":
                    if session.undo_last_edit():
                        console.print("[green]✓[/green] Edit undone")
                        await self._validate_template(session)
                    else:
                        console.print("[yellow]No edits to undo[/yellow]")
                elif command == "preview":
                    self._preview_template(session)
                else:
                    console.print(f"[red]Unknown command:[/red] {command}")
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
                continue
    
    def _display_session_status(self, session: EditSession):
        """Display current session status."""
        
        # Create status panel
        status_text = f"File: {session.template_path.name}\n"
        status_text += f"Mode: {session.mode.value.title()}\n"
        status_text += f"Edits: {len(session.edit_history)}\n"
        
        if session.validation_errors:
            status_text += f"[red]Validation Errors: {len(session.validation_errors)}[/red]\n"
        else:
            status_text += "[green]Validation: Passed[/green]\n"
        
        console.print(Panel(status_text, title="Template Editor", border_style="blue"))
    
    def _get_available_actions(self, session: EditSession) -> List[EditAction]:
        """Get list of available actions for current session state."""
        
        actions = [
            EditAction.VALIDATE,
            EditAction.PREVIEW,
            EditAction.ADD_RESOURCE,
            EditAction.ADD_PARAMETER,
            EditAction.ADD_OUTPUT,
        ]
        
        # Add modify/remove actions if content exists
        if self._template_has_resources(session):
            actions.extend([EditAction.MODIFY_RESOURCE, EditAction.REMOVE_RESOURCE])
        
        if self._template_has_parameters(session):
            actions.extend([EditAction.MODIFY_PARAMETER, EditAction.REMOVE_PARAMETER])
        
        # Always available
        actions.extend([EditAction.SAVE, EditAction.EXIT])
        
        return actions
    
    def _prompt_for_action(self, actions: List[EditAction]) -> EditAction:
        """Prompt user to select an action."""
        
        # Display menu
        table = Table(title="Available Actions")
        table.add_column("Option", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        
        action_map = {
            EditAction.ADD_RESOURCE: "Add a new Azure resource",
            EditAction.MODIFY_RESOURCE: "Modify an existing resource",
            EditAction.REMOVE_RESOURCE: "Remove a resource",
            EditAction.ADD_PARAMETER: "Add a new parameter",
            EditAction.MODIFY_PARAMETER: "Modify an existing parameter",
            EditAction.REMOVE_PARAMETER: "Remove a parameter",
            EditAction.ADD_OUTPUT: "Add a new output",
            EditAction.VALIDATE: "Validate the template",
            EditAction.PREVIEW: "Preview the template",
            EditAction.SAVE: "Save changes",
            EditAction.EXIT: "Exit editor"
        }
        
        choices = []
        for i, action in enumerate(actions, 1):
            table.add_row(str(i), action_map.get(action, action.value.replace('_', ' ').title()))
            choices.append(str(i))
        
        console.print(table)
        
        while True:
            try:
                choice = Prompt.ask("Select action", choices=choices)
                return actions[int(choice) - 1]
            except (ValueError, IndexError):
                console.print("[red]Invalid selection. Please try again.[/red]")
    
    async def _validate_template(self, session: EditSession):
        """Validate the current template content."""
        
        console.print("\n[blue]Validating template...[/blue]")
        
        try:
            # Parse current content as JSON (assuming it's ARM template format)
            import json
            template_data = json.loads(session.current_content)
            
            # Run ARM validation
            validation_result = await self.validator.validate_template(template_data)
            
            session.last_validation = validation_result
            session.validation_errors.clear()
            
            if validation_result.is_valid:
                console.print("[green]✓[/green] Template validation passed")
            else:
                console.print(f"[red]✗[/red] Template validation failed with {len(validation_result.errors)} errors")
                
                for error in validation_result.errors[:5]:  # Show first 5 errors
                    session.validation_errors.append(error.message)
                    console.print(f"  [red]•[/red] {error.message}")
                
                if len(validation_result.errors) > 5:
                    console.print(f"  [yellow]... and {len(validation_result.errors) - 5} more errors[/yellow]")
        
        except json.JSONDecodeError as e:
            session.validation_errors = [f"JSON parsing error: {str(e)}"]
            console.print(f"[red]✗[/red] Template has JSON syntax errors: {str(e)}")
        
        except Exception as e:
            session.validation_errors = [f"Validation error: {str(e)}"]
            console.print(f"[red]✗[/red] Validation failed: {str(e)}")
    
    def _preview_template(self, session: EditSession):
        """Show template preview with syntax highlighting."""
        
        console.print("\n[bold blue]Template Preview:[/bold blue]")
        
        # Try to format as JSON for better display
        try:
            import json
            template_data = json.loads(session.current_content)
            formatted_content = json.dumps(template_data, indent=2)
            syntax = Syntax(formatted_content, "json", theme="monokai", line_numbers=True)
        except:
            # Fall back to plain text
            syntax = Syntax(session.current_content, "text", theme="monokai", line_numbers=True)
        
        console.print(Panel(syntax, title="Template Content", border_style="blue"))
    
    async def _add_resource_interactive(self, session: EditSession):
        """Interactive resource addition."""
        
        console.print("\n[bold green]Add New Resource[/bold green]")
        
        # Get resource type
        resource_type = Prompt.ask("Enter Azure resource type (e.g., Microsoft.Web/sites)")
        
        if not resource_type:
            console.print("[yellow]Operation cancelled[/yellow]")
            return
        
        # Get resource name
        resource_name = Prompt.ask("Enter resource name")
        
        if not resource_name:
            console.print("[yellow]Operation cancelled[/yellow]")
            return
        
        # Get location
        location = Prompt.ask("Enter location", default="[resourceGroup().location]")
        
        try:
            # Get schema information from MCP
            schema_info = await self.mcp_client.get_resource_schema(resource_type)
            
            # Create basic resource template
            new_resource = {
                "type": resource_type,
                "apiVersion": schema_info.get("defaultApiVersion", "2021-01-01"),
                "name": resource_name,
                "location": location,
                "properties": {}
            }
            
            # Add to template
            template_data = json.loads(session.current_content)
            if 'resources' not in template_data:
                template_data['resources'] = []
            
            template_data['resources'].append(new_resource)
            
            # Update session
            new_content = json.dumps(template_data, indent=2)
            session.add_edit(EditAction.ADD_RESOURCE, f"Added resource {resource_name}", new_content)
            
            console.print(f"[green]✓[/green] Added resource '{resource_name}' of type '{resource_type}'")
            
            # Auto-validate if enabled
            if self.auto_validate:
                await self._validate_template(session)
        
        except Exception as e:
            console.print(f"[red]Error adding resource:[/red] {str(e)}")
    
    async def _add_parameter_interactive(self, session: EditSession):
        """Interactive parameter addition."""
        
        console.print("\n[bold green]Add New Parameter[/bold green]")
        
        # Get parameter details
        param_name = Prompt.ask("Enter parameter name")
        if not param_name:
            return
        
        param_type = Prompt.ask(
            "Enter parameter type",
            choices=["string", "int", "bool", "array", "object"],
            default="string"
        )
        
        param_description = Prompt.ask("Enter parameter description", default="")
        
        try:
            template_data = json.loads(session.current_content)
            if 'parameters' not in template_data:
                template_data['parameters'] = {}
            
            # Create parameter definition
            param_def = {"type": param_type}
            if param_description:
                param_def["metadata"] = {"description": param_description}
            
            template_data['parameters'][param_name] = param_def
            
            # Update session
            new_content = json.dumps(template_data, indent=2)
            session.add_edit(EditAction.ADD_PARAMETER, f"Added parameter {param_name}", new_content)
            
            console.print(f"[green]✓[/green] Added parameter '{param_name}' of type '{param_type}'")
            
        except Exception as e:
            console.print(f"[red]Error adding parameter:[/red] {str(e)}")
    
    async def _generate_suggestions(self, session: EditSession):
        """Generate intelligent editing suggestions."""
        
        console.print("\n[blue]Analyzing template for improvement suggestions...[/blue]")
        
        try:
            template_data = json.loads(session.current_content)
            
            # Get resources for analysis
            resources = template_data.get('resources', [])
            
            # Run security analysis
            security_assessment = await self.security_analyzer.analyze_deployment_security(resources)
            
            # Convert security findings to edit suggestions
            for finding in security_assessment.get_findings_by_severity("high"):
                if finding.recommended_configuration:
                    suggestion = EditSuggestion(
                        id=f"security_{finding.id}",
                        title=f"Fix: {finding.title}",
                        description=finding.description,
                        action_type=EditAction.MODIFY_RESOURCE,
                        target_name=finding.resource_name,
                        target_path=f"resources[name='{finding.resource_name}'].properties",
                        new_content=finding.recommended_configuration,
                        reason=f"Security: {finding.impact_description}",
                        confidence=0.9,
                        risk_level="low"
                    )
                    session.suggestions.append(suggestion)
            
            console.print(f"[green]✓[/green] Generated {len(session.suggestions)} suggestions")
            
        except Exception as e:
            console.print(f"[red]Error generating suggestions:[/red] {str(e)}")
    
    def _display_suggestion(self, suggestion: EditSuggestion):
        """Display a suggestion to the user."""
        
        panel_content = f"[bold]{suggestion.title}[/bold]\n\n"
        panel_content += f"{suggestion.description}\n\n"
        panel_content += f"[dim]Reason: {suggestion.reason}[/dim]\n"
        panel_content += f"[dim]Risk Level: {suggestion.risk_level}[/dim]\n"
        panel_content += f"[dim]Confidence: {suggestion.confidence:.1%}[/dim]"
        
        console.print(Panel(
            panel_content,
            title="💡 Suggestion",
            border_style="green"
        ))
    
    def _explain_suggestion(self, suggestion: EditSuggestion):
        """Provide detailed explanation of a suggestion."""
        
        explanation = f"[bold]Detailed Explanation for: {suggestion.title}[/bold]\n\n"
        explanation += f"[blue]What this does:[/blue]\n{suggestion.description}\n\n"
        explanation += f"[blue]Why this is recommended:[/blue]\n{suggestion.reason}\n\n"
        explanation += f"[blue]Risk assessment:[/blue]\n"
        explanation += f"• Risk Level: {suggestion.risk_level}\n"
        explanation += f"• Confidence: {suggestion.confidence:.1%}\n\n"
        
        if suggestion.new_content:
            explanation += f"[blue]Proposed changes:[/blue]\n"
            explanation += json.dumps(suggestion.new_content, indent=2)
        
        console.print(Panel(explanation, title="📖 Explanation", border_style="blue"))
    
    async def _apply_suggestion(self, session: EditSession, suggestion: EditSuggestion):
        """Apply a suggestion to the template."""
        
        try:
            template_data = json.loads(session.current_content)
            
            # Apply the suggestion (simplified implementation)
            # In a real implementation, this would use the target_path to navigate
            # and apply the changes precisely
            
            if suggestion.action_type == EditAction.MODIFY_RESOURCE:
                resources = template_data.get('resources', [])
                for resource in resources:
                    if resource.get('name') == suggestion.target_name:
                        # Merge the suggested configuration
                        if 'properties' not in resource:
                            resource['properties'] = {}
                        resource['properties'].update(suggestion.new_content)
                        break
            
            # Update session
            new_content = json.dumps(template_data, indent=2)
            session.add_edit(
                suggestion.action_type,
                f"Applied suggestion: {suggestion.title}",
                new_content
            )
            
            console.print(f"[green]✓[/green] Applied suggestion: {suggestion.title}")
            
            # Auto-validate
            if self.auto_validate:
                await self._validate_template(session)
        
        except Exception as e:
            console.print(f"[red]Error applying suggestion:[/red] {str(e)}")
    
    async def _save_template(self, session: EditSession) -> bool:
        """Save the current template content."""
        
        try:
            # Validate before saving
            if session.validation_errors:
                if not Confirm.ask("Template has validation errors. Save anyway?"):
                    return False
            
            # Write content to file
            session.template_path.write_text(session.current_content, encoding='utf-8')
            
            console.print(f"[green]✓[/green] Saved template to {session.template_path}")
            return True
            
        except Exception as e:
            console.print(f"[red]Error saving template:[/red] {str(e)}")
            return False
    
    def _has_unsaved_changes(self, session: EditSession) -> bool:
        """Check if session has unsaved changes."""
        return session.current_content != session.original_content
    
    def _template_has_resources(self, session: EditSession) -> bool:
        """Check if template has resources."""
        try:
            template_data = json.loads(session.current_content)
            return bool(template_data.get('resources'))
        except:
            return False
    
    def _template_has_parameters(self, session: EditSession) -> bool:
        """Check if template has parameters."""
        try:
            template_data = json.loads(session.current_content)
            return bool(template_data.get('parameters'))
        except:
            return False
    
    async def _modify_resource_interactive(self, session: EditSession):
        """Interactive resource modification."""
        console.print("\n[yellow]Resource modification not yet implemented[/yellow]")
    
    async def _remove_resource_interactive(self, session: EditSession):
        """Interactive resource removal."""
        console.print("\n[yellow]Resource removal not yet implemented[/yellow]")
    
    async def _modify_parameter_interactive(self, session: EditSession):
        """Interactive parameter modification."""
        console.print("\n[yellow]Parameter modification not yet implemented[/yellow]")