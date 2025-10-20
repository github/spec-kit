"""
Guard Executor - Execute guards and manage run history

Handles guard execution, output parsing, and history tracking.
"""

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from specify_cli.guards.types import Comment, GuardRun


class GuardExecutor:
    """
    Executes guards using guard type definitions and params.
    
    Guards are Python files that accept params and return structured JSON:
    {
        "passed": bool,
        "analysis": str,
        "details": {...}
    }
    """
    
    def __init__(self, guard_id: str, command: Optional[str] = None, timeout: int = 300, registry=None):
        self.guard_id = guard_id
        self.command = command
        self.timeout = timeout
        self.registry = registry
        self.guard_data = None
        self.guard_type = None
        
        # Load guard data and type from registry
        if registry:
            self.guard_data = registry.get_guard(guard_id)
            if self.guard_data:
                guard_type_id = self.guard_data.get("guard_type")
                if guard_type_id:
                    self.guard_type = registry.get_guard_type(guard_type_id)
                
                # Use command from guard.yaml if not provided
                if not self.command:
                    self.command = self.guard_data.get("command")
    
    def execute(self) -> GuardRun:
        """
        Execute guard and return structured result.
        
        Execution flow:
        1. Build command from guard type invocation pattern + params
        2. Execute guard (Python file that returns JSON)
        3. Parse structured JSON output
        4. Validate against guard type output schema
        5. Store in history
        
        Returns:
            GuardRun with execution details
        """
        start_time = time.time()
        
        # Build execution command
        command = self._build_command()
        if not command:
            raise ValueError(f"Could not build execution command for guard {self.guard_id}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Parse structured JSON output
            guard_output = self._parse_guard_output(result.stdout, result.stderr, result.returncode)
            
            # Extract fields from structured output
            passed = guard_output.get("passed", result.returncode == 0)
            analysis = guard_output.get("analysis", self._fallback_analysis(result.stdout, result.stderr, passed))
            
            # Create result
            run_result = GuardRun(
                guard_id=self.guard_id,
                run_id=f"{self.guard_id}-R{int(time.time())}",
                timestamp=datetime.now(timezone.utc),
                passed=passed,
                exit_code=result.returncode,
                duration_ms=duration_ms,
                stdout=result.stdout,
                stderr=result.stderr,
                analysis=analysis,
                comments=[]
            )
            
            # Store in history if registry available
            if self.registry:
                self._save_run(run_result)
            
            return run_result
        
        except subprocess.TimeoutExpired as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            run_result = GuardRun(
                guard_id=self.guard_id,
                run_id=f"{self.guard_id}-R{int(time.time())}",
                timestamp=datetime.now(timezone.utc),
                passed=False,
                exit_code=124,
                duration_ms=duration_ms,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "Guard execution timed out",
                analysis="Execution exceeded timeout limit",
                comments=[]
            )
            
            if self.registry:
                self._save_run(run_result)
            
            return run_result
    
    def _build_command(self) -> Optional[str]:
        """
        Build execution command from guard type + params.
        
        Guards are Python files that accept params as JSON and return JSON.
        Command: python .specify/guards/G001/G001.py '{"param1": "value1"}'
        
        Returns:
            Command string to execute
        """
        if not self.guard_data:
            raise ValueError(f"No guard data found for {self.guard_id}")
        
        guard_file = self._get_guard_file()
        if not guard_file or not guard_file.exists():
            raise ValueError(f"Guard implementation file not found: {guard_file}")
        
        params = self.guard_data.get("params", {})
        params_json = json.dumps(params)
        
        # Execute guard Python file with params as JSON argument
        return f"python3 {guard_file} '{params_json}'"
    
    def _get_guard_file(self) -> Optional[Path]:
        """Get path to guard Python implementation file."""
        if not self.registry:
            return None
        
        guard_dir = self.registry.base_path / self.guard_id
        guard_file = guard_dir / f"{self.guard_id}.py"
        
        return guard_file if guard_file.exists() else None
    
    def _parse_guard_output(self, stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
        """
        Parse structured JSON output from guard.
        
        Guards should return JSON with:
        {
            "passed": bool,
            "analysis": str,
            "details": {...}
        }
        
        Args:
            stdout: Standard output (should be JSON)
            stderr: Standard error
            exit_code: Process exit code
        
        Returns:
            Parsed output dict or empty dict if parse fails
        """
        # Try to parse entire stdout as JSON
        if stdout.strip():
            try:
                output = json.loads(stdout)
                # Validate required fields
                if isinstance(output, dict) and "passed" in output:
                    return output
            except json.JSONDecodeError:
                pass
        
        # No valid JSON found - return empty dict
        # (will fall back to exit code for passed/failed)
        return {}
    
    def _fallback_analysis(self, stdout: str, stderr: str, passed: bool) -> str:
        """
        Generate analysis when guard doesn't return structured JSON.
        This indicates the guard is not properly implemented.
        """
        if stderr:
            return f"Guard error: {stderr[:200]}"
        
        if passed:
            return "Guard passed but did not return structured output"
        else:
            return "Guard failed but did not return structured output"
    
    def _save_run(self, run_result: GuardRun) -> None:
        """
        Save run to history file.
        
        Args:
            run_result: GuardRun to save
        """
        if not self.registry:
            return
        
        # Get history file path
        guard_dir = self.registry.base_path / self.guard_id
        guard_dir.mkdir(parents=True, exist_ok=True)
        history_file = guard_dir / "history.json"
        
        # Load existing history
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Add new run
        run_dict = {
            "run_id": run_result.run_id,
            "guard_id": run_result.guard_id,
            "timestamp": run_result.timestamp.isoformat(),
            "passed": run_result.passed,
            "exit_code": run_result.exit_code,
            "duration_ms": run_result.duration_ms,
            "stdout": run_result.stdout,
            "stderr": run_result.stderr,
            "analysis": run_result.analysis,
            "comments": [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "category": c.category.value,
                    "note": {
                        "done": c.note.done,
                        "expected": c.note.expected,
                        "todo": c.note.todo
                    }
                }
                for c in run_result.comments
            ]
        }
        
        history.append(run_dict)
        
        # Save history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def parse_pytest_output(self, stdout: str, stderr: str) -> Dict:
        """Parse pytest output (feature 001 compatibility)."""
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        
        for line in stdout.split('\n'):
            if 'passed' in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'passed' in part.lower() and i > 0:
                        try:
                            tests_passed = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
            
            if 'failed' in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'failed' in part.lower() and i > 0:
                        try:
                            tests_failed = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
        
        tests_run = tests_passed + tests_failed
        
        return {
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed
        }


class GuardHistory:
    """
    Manages guard execution history with comment lineage.
    """
    
    def __init__(self, guard_id: str, registry):
        """
        Initialize history manager.
        
        Args:
            guard_id: Guard ID
            registry: GuardRegistry instance
        """
        self.guard_id = guard_id
        self.registry = registry
        self.history_file = registry.base_path / guard_id / "history.json"
    
    def get_lineage(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get execution history with comments.
        
        Args:
            limit: Maximum number of runs to return (most recent first)
        
        Returns:
            List of run dictionaries with comments
        """
        if not self.history_file.exists():
            return []
        
        with open(self.history_file, 'r') as f:
            history = json.load(f)
        
        # Sort by timestamp (most recent first)
        history.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        
        if limit:
            history = history[:limit]
        
        return history
    
    def add_comment(
        self,
        comment: Comment,
        run_id: Optional[str] = None
    ) -> None:
        """
        Add comment to a run.
        
        Args:
            comment: Comment to add
            run_id: Specific run ID (defaults to latest)
        """
        if not self.history_file.exists():
            raise ValueError(f"No history found for guard {self.guard_id}")
        
        with open(self.history_file, 'r') as f:
            history = json.load(f)
        
        if not history:
            raise ValueError(f"No runs found for guard {self.guard_id}")
        
        # Find target run
        if run_id:
            target_run = next((r for r in history if r["run_id"] == run_id), None)
            if not target_run:
                raise ValueError(f"Run {run_id} not found")
        else:
            # Use most recent run
            history.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
            target_run = history[0]
        
        # Add comment
        comment_dict = {
            "timestamp": comment.timestamp.isoformat(),
            "category": comment.category.value,
            "note": {
                "done": comment.note.done,
                "expected": comment.note.expected,
                "todo": comment.note.todo
            }
        }
        
        if "comments" not in target_run:
            target_run["comments"] = []
        
        target_run["comments"].append(comment_dict)
        
        # Save history
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
