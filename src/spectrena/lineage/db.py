#!/usr/bin/env python3
"""
Spectrena Lineage with SurrealDB
"""

from surrealdb import AsyncSurreal
from pathlib import Path
from contextlib import asynccontextmanager
from typing import cast


class LineageDB:
    """SurrealDB-backed lineage tracking."""

    db_path: Path
    connection_string: str

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = Path.cwd() / ".spectrena" / "lineage.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection_string = f"surrealkv://{self.db_path}"

    @asynccontextmanager
    async def connect(self):
        """Async context manager for database connection."""
        async with AsyncSurreal(self.connection_string) as db:
            await db.use("spectrena", "lineage")
            yield db

    async def init_schema(self, schema_path: Path):
        """Initialize database with schema."""
        schema = schema_path.read_text()
        async with self.connect() as db:
            _ = await db.query(schema)

    # -------------------------------------------------------------------------
    # Spec Operations
    # -------------------------------------------------------------------------

    async def register_spec(
        self,
        spec_id: str,
        title: str,
        spec_path: str,
        component: str | None = None,
        weight: str = "STANDARD",
    ) -> dict[str, object]:
        """Register a new specification."""
        record_id = spec_id.replace("-", "_")

        async with self.connect() as db:
            result = await db.create(
                f"spec:{record_id}",
                {
                    "id": spec_id,
                    "title": title,
                    "spec_path": spec_path,
                    "component": component,
                    "weight": weight,
                    "status": "draft",
                },
            )
            # SurrealDB create returns a dict for single record creation
            if isinstance(result, dict):
                return cast(dict[str, object], result)
            return cast(dict[str, object], result[0])

    async def add_dependency(
        self, from_spec: str, to_spec: str, dependency_type: str = "hard"
    ) -> dict[str, object]:
        """Add spec dependency edge."""
        from_id = from_spec.replace("-", "_")
        to_id = to_spec.replace("-", "_")

        async with self.connect() as db:
            result = await db.query(
                f"""
                RELATE spec:{from_id}->depends_on->spec:{to_id}
                SET dependency_type = $type
            """,
                {"type": dependency_type},
            )
            if isinstance(result, dict):
                return cast(dict[str, object], result)
            return cast(dict[str, object], result[0]) if result else {}

    async def get_blocked_by(self, spec_id: str) -> list[object]:
        """Get all specs that would be blocked if this spec slips."""
        record_id = spec_id.replace("-", "_")

        async with self.connect() as db:
            result = await db.query(
                f"""
                SELECT
                    id, title, status, component
                FROM spec
                WHERE ->depends_on->spec CONTAINS spec:{record_id}
            """
            )
            if isinstance(result, list):
                return cast(list[object], result)
            return [cast(object, result)]

    async def get_ready_specs(self) -> list[object]:
        """Get specs ready to work on (all deps completed)."""
        async with self.connect() as db:
            result = await db.query(
                """
                SELECT id, title, component
                FROM spec
                WHERE status IN ['draft', 'approved']
                AND (
                    count(->depends_on->spec) = 0
                    OR array::all(->depends_on->spec.status, |$v| $v = 'completed')
                )
            """
            )
            if isinstance(result, list):
                return cast(list[object], result)
            return [cast(object, result)]

    # -------------------------------------------------------------------------
    # Task Operations
    # -------------------------------------------------------------------------

    async def start_task(self, task_id: str) -> dict[str, object]:
        """Mark task as active and update phase state."""
        record_id = task_id.replace("-", "_")

        async with self.connect() as db:
            # Update task status
            _ = await db.query(
                f"""
                UPDATE task:{record_id} SET
                    status = 'active',
                    started_at = time::now()
            """
            )

            # Update phase state
            _ = await db.query(
                f"""
                DELETE current_task WHERE in = phase_state:current;
                RELATE phase_state:current->current_task->task:{record_id}
            """
            )

            # Log status change
            _ = await db.create(
                "status_change",
                {
                    "entity_type": "task",
                    "entity_id": task_id,
                    "old_status": "pending",
                    "new_status": "active",
                    "changed_by": "claude",
                },
            )

            return {"status": "started", "task_id": task_id}

    async def complete_task(
        self, task_id: str, actual_minutes: int | None = None
    ) -> dict[str, object]:
        """Mark task as completed."""
        record_id = task_id.replace("-", "_")

        async with self.connect() as db:
            _ = await db.query(
                f"""
                UPDATE task:{record_id} SET
                    status = 'completed',
                    completed_at = time::now(),
                    actual_minutes = $minutes
            """,
                {"minutes": actual_minutes},
            )

            return {"status": "completed", "task_id": task_id}

    # -------------------------------------------------------------------------
    # Context Building (for Claude)
    # -------------------------------------------------------------------------

    async def get_task_context(self, task_id: str) -> dict[str, object] | None:
        """
        Build full context for implementing a task.

        Returns everything Claude needs to know.
        """
        record_id = task_id.replace("-", "_")

        async with self.connect() as db:
            result = await db.query(
                f"""
                SELECT
                    *,
                    <-belongs_to<-plan.* AS plan,
                    <-belongs_to<-plan->implements->spec.* AS spec,
                    ->task_depends->task.* AS prerequisite_tasks,
                    ->modifies->symbol.* AS target_symbols,
                    ->modifies->symbol->references->symbol.* AS related_symbols
                FROM task:{record_id}
            """
            )

            if isinstance(result, list) and result:
                return cast(dict[str, object], result[0])
            if isinstance(result, dict):
                return cast(dict[str, object], result)
            return None

    async def get_current_context(self) -> dict[str, object] | None:
        """Get current phase state with full context."""
        async with self.connect() as db:
            result = await db.query(
                """
                SELECT
                    current_phase,
                    ->current_spec->spec.* AS spec,
                    ->current_task->task.* AS task,
                    ->current_session->session.* AS session
                FROM phase_state:current
            """
            )
            if isinstance(result, list) and result:
                return cast(dict[str, object], result[0])
            if isinstance(result, dict):
                return cast(dict[str, object], result)
            return None

    # -------------------------------------------------------------------------
    # Code Change Recording
    # -------------------------------------------------------------------------

    async def record_change(
        self,
        task_id: str,
        file_path: str,
        change_type: str,
        symbol_fqn: str | None = None,
        lines_added: int = 0,
        lines_removed: int = 0,
        commit_sha: str | None = None,
    ) -> dict[str, object]:
        """Record a code change linked to a task."""
        import uuid

        change_id = f"ch_{uuid.uuid4().hex[:8]}"
        task_record_id = task_id.replace("-", "_")

        async with self.connect() as db:
            # Create change record
            _ = await db.create(
                f"change:{change_id}",
                {
                    "id": change_id,
                    "change_type": change_type,
                    "file_path": file_path,
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "commit_sha": commit_sha,
                },
            )

            # Link to task
            _ = await db.query(
                f"""
                RELATE change:{change_id}->performed_in->task:{task_record_id}
            """
            )

            # Link to symbol if provided
            if symbol_fqn:
                symbol_id = (
                    symbol_fqn.replace("::", "_").replace(".", "_").replace("/", "_")
                )

                # Create symbol if not exists
                _ = await db.query(
                    f"""
                    CREATE symbol:{symbol_id} CONTENT {{
                        fqn: $fqn,
                        name: $name,
                        file_path: $path,
                        kind: 'unknown'
                    }} ON DUPLICATE KEY UPDATE updated_at = time::now()
                """,
                    {
                        "fqn": symbol_fqn,
                        "name": symbol_fqn.split("::")[-1],
                        "path": file_path,
                    },
                )

                # Link change to symbol
                _ = await db.query(
                    f"""
                    RELATE change:{change_id}->records->symbol:{symbol_id}
                """
                )

                # Link task to symbol
                _ = await db.query(
                    f"""
                    RELATE task:{task_record_id}->modifies->symbol:{symbol_id}
                    SET change_type = $type
                """,
                    {"type": change_type},
                )

            return {"change_id": change_id}

    # -------------------------------------------------------------------------
    # Analytics
    # -------------------------------------------------------------------------

    async def get_velocity(self, days: int = 14) -> list[object]:
        """Get task completion velocity over time."""
        async with self.connect() as db:
            result = await db.query(
                f"""
                SELECT
                    time::floor(completed_at, 1d) AS day,
                    count() AS completed,
                    math::sum(actual_minutes) AS total_minutes
                FROM task
                WHERE completed_at > time::now() - {days}d
                GROUP BY day
                ORDER BY day
            """
            )
            if isinstance(result, list):
                return cast(list[object], result)
            return [cast(object, result)]

    async def get_spec_progress(self, spec_id: str) -> dict[str, object] | None:
        """Get detailed progress for a spec."""
        record_id = spec_id.replace("-", "_")

        async with self.connect() as db:
            result = await db.query(
                f"""
                SELECT
                    id,
                    title,
                    status,
                    count(<-implements<-plan<-belongs_to<-task) AS total_tasks,
                    count(<-implements<-plan<-belongs_to<-task[WHERE status = 'completed']) AS completed,
                    count(<-implements<-plan<-belongs_to<-task[WHERE status = 'active']) AS active,
                    count(<-implements<-plan<-belongs_to<-task[WHERE status = 'blocked']) AS blocked,
                    math::sum(<-implements<-plan<-belongs_to<-task.actual_minutes) AS minutes_spent
                FROM spec:{record_id}
            """
            )
            if isinstance(result, list) and result:
                return cast(dict[str, object], result[0])
            if isinstance(result, dict):
                return cast(dict[str, object], result)
            return None


# -----------------------------------------------------------------------------
# MCP Server Integration
# -----------------------------------------------------------------------------


def create_mcp_server():
    """Create FastMCP server with SurrealDB backend."""
    from fastmcp import FastMCP

    mcp = FastMCP("spectrena")
    db = LineageDB()

    @mcp.tool()
    async def phase_get() -> dict[str, object] | None:
        """Get current workflow phase and context."""
        return await db.get_current_context()

    @mcp.tool()
    async def task_start(task_id: str) -> dict[str, object]:
        """Start working on a task."""
        return await db.start_task(task_id)

    @mcp.tool()
    async def task_complete(
        task_id: str, actual_minutes: int | None = None
    ) -> dict[str, object]:
        """Complete a task."""
        return await db.complete_task(task_id, actual_minutes)

    @mcp.tool()
    async def task_context(task_id: str) -> dict[str, object] | None:
        """Get full context for implementing a task."""
        return await db.get_task_context(task_id)

    @mcp.tool()
    async def record_change(
        task_id: str, file_path: str, change_type: str, symbol_fqn: str | None = None
    ) -> dict[str, object]:
        """Record a code change linked to current task."""
        return await db.record_change(task_id, file_path, change_type, symbol_fqn)

    @mcp.tool()
    async def impact_analysis(spec_id: str) -> dict[str, object]:
        """Find all specs that depend on this one."""
        blocked = await db.get_blocked_by(spec_id)
        return {"spec_id": spec_id, "blocked_specs": blocked}

    @mcp.tool()
    async def ready_specs() -> list[object]:
        """List specs ready to work on."""
        return await db.get_ready_specs()

    @mcp.tool()
    async def velocity(days: int = 14) -> list[object]:
        """Get task completion velocity."""
        return await db.get_velocity(days)

    @mcp.tool()
    async def dep_graph_analyze() -> dict[str, object]:
        """
        Analyze all specs and return suggested dependency graph.
        
        Call this when user asks to analyze or create dependency graph.
        Returns all specs for Claude to analyze and generate Mermaid graph.
        """
        from pathlib import Path
        
        specs_dir = Path.cwd() / "specs"
        specs = []
        
        if not specs_dir.exists():
            return {
                "specs": [],
                "instruction": "No specs directory found. Run 'spectrena init' first."
            }
        
        for spec_dir in sorted(specs_dir.iterdir()):
            if not spec_dir.is_dir():
                continue
            spec_md = spec_dir / "spec.md"
            if spec_md.exists():
                content = spec_md.read_text()
                # Extract just the first 1000 chars for analysis
                specs.append({
                    "id": spec_dir.name,
                    "content": content[:1000]
                })
        
        return {
            "specs": specs,
            "count": len(specs),
            "instruction": "Analyze these specs and determine dependencies. Output a Mermaid graph where SPEC-ID --> DEPENDENCY-ID means 'spec depends on dependency'."
        }
    
    @mcp.tool()
    async def dep_graph_save(mermaid_graph: str) -> dict[str, object]:
        """
        Save a Mermaid dependency graph to deps.mermaid.
        
        Args:
            mermaid_graph: The Mermaid graph content (without ```mermaid fences)
        """
        from pathlib import Path
        
        deps_file = Path.cwd() / "deps.mermaid"
        
        # Ensure it starts with graph TD
        if not mermaid_graph.strip().startswith("graph"):
            mermaid_graph = "graph TD\n" + mermaid_graph
        
        deps_file.write_text(mermaid_graph.strip() + "\n")
        
        # Count edges for confirmation
        edge_count = mermaid_graph.count("-->")
        
        # Also sync to lineage DB if enabled
        # TODO: Parse and store edges in database
        
        return {
            "status": "saved",
            "path": str(deps_file),
            "edge_count": edge_count,
            "message": f"Saved dependency graph with {edge_count} edges to {deps_file}"
        }

    return mcp
