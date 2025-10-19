import json
import fcntl
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone


class GuardRegistry:
    
    def __init__(self, guards_base_path: Path):
        """
        Initialize guard registry with new structure:
        .specify/guards/
        ├── list/           # Individual guard metadata files (G001.json, G002.json, etc.)
        ├── history/        # Guard execution history logs
        └── types/          # Guard type definitions (templates)
        """
        self.base_path = guards_base_path
        self.list_dir = self.base_path / "list"
        self.history_dir = self.base_path / "history"
        
        self.list_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.base_path / "index.json"
        self._ensure_index_exists()
    
    def _ensure_index_exists(self) -> None:
        if not self.index_file.exists():
            self._save_index({"next_id": 1})
    
    def _load_index(self) -> Dict:
        with open(self.index_file, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return data
    
    def _save_index(self, data: Dict) -> None:
        with open(self.index_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def generate_id(self) -> str:
        data = self._load_index()
        next_id = data.get("next_id", 1)
        guard_id = f"G{next_id:03d}"
        data["next_id"] = next_id + 1
        self._save_index(data)
        return guard_id
    
    def add_guard(
        self,
        guard_id: str,
        guard_type: str,
        name: str,
        command: str,
        files: List[str],
        metadata_file: Optional[str] = None
    ) -> None:
        guard_file = self.list_dir / f"{guard_id}.json"
        
        guard_data = {
            "id": guard_id,
            "type": guard_type,
            "name": name,
            "command": command,
            "created": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "status": "active",
            "files": files,
            "last_executed": None,
            "last_result": None,
            "execution_count": 0
        }
        
        with open(guard_file, 'w') as f:
            json.dump(guard_data, f, indent=2)
    
    def get_guard(self, guard_id: str) -> Optional[Dict]:
        guard_file = self.list_dir / f"{guard_id}.json"
        
        if not guard_file.exists():
            return None
        
        with open(guard_file, 'r') as f:
            return json.load(f)
    
    def list_guards(self) -> List[Dict]:
        guards = []
        
        for guard_file in sorted(self.list_dir.glob("G*.json")):
            with open(guard_file, 'r') as f:
                guards.append(json.load(f))
        
        return guards
    
    def update_guard_status(self, guard_id: str, status: str) -> None:
        guard = self.get_guard(guard_id)
        if guard:
            guard["status"] = status
            guard_file = self.list_dir / f"{guard_id}.json"
            with open(guard_file, 'w') as f:
                json.dump(guard, f, indent=2)
    
    def record_execution(
        self,
        guard_id: str,
        result: str,
        exit_code: int,
        duration_ms: float,
        output: str = "",
        notes: str = ""
    ) -> None:
        """Record guard execution in both guard metadata and history.
        
        Args:
            guard_id: The guard ID (e.g., G001)
            result: Result status (pass, fail, timeout)
            exit_code: Process exit code
            duration_ms: Execution duration in milliseconds
            output: Combined stdout/stderr from execution
            notes: AI agent notes about fixes, observations, or learnings
        """
        
        guard = self.get_guard(guard_id)
        if not guard:
            return
        
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        guard["last_executed"] = timestamp
        guard["last_result"] = result
        guard["execution_count"] = guard.get("execution_count", 0) + 1
        
        guard_file = self.list_dir / f"{guard_id}.json"
        with open(guard_file, 'w') as f:
            json.dump(guard, f, indent=2)
        
        history_entry = {
            "guard_id": guard_id,
            "timestamp": timestamp,
            "result": result,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "output": output,
            "notes": notes
        }
        
        history_file = self.history_dir / f"{guard_id}-{timestamp.replace(':', '-')}.json"
        with open(history_file, 'w') as f:
            json.dump(history_entry, f, indent=2)
    
    def get_guard_history(self, guard_id: str, limit: int = 10) -> List[Dict]:
        """Get execution history for a specific guard.
        
        Returns most recent executions first, including agent notes.
        """
        history = []
        
        pattern = f"{guard_id}-*.json"
        for history_file in sorted(self.history_dir.glob(pattern), reverse=True)[:limit]:
            with open(history_file, 'r') as f:
                history.append(json.load(f))
        
        return history
    
    def get_all_history(self, limit: int = 50) -> List[Dict]:
        """Get all guard execution history across all guards.
        
        Useful for agents to learn from past failures/successes.
        """
        history = []
        
        for history_file in sorted(self.history_dir.glob("G*.json"), reverse=True)[:limit]:
            with open(history_file, 'r') as f:
                history.append(json.load(f))
        
        return history
