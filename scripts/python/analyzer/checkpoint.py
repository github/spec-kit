"""
Checkpoint system for incremental analysis of large codebases.

Allows analysis to be paused and resumed, preventing data loss for
projects with 500K+ LOC that may take hours to analyze.
"""

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


@dataclass
class AnalysisCheckpoint:
    """Container for checkpoint data."""

    phase: str
    timestamp: float
    data: Dict[str, Any]
    progress_percentage: float = 0.0
    estimated_time_remaining: Optional[float] = None


class CheckpointManager:
    """
    Manage analysis checkpoints for large projects.

    Saves progress after each phase and allows resuming from last successful checkpoint.
    """

    def __init__(self, checkpoint_dir: Path):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.phases = [
            "discovery",
            "dependencies",
            "code_metrics",
            "security",
            "architecture",
            "scoring",
            "reporting",
        ]

        self.start_time = time.time()

    def save_checkpoint(self, phase: str, data: Dict[str, Any], progress: float = 0.0) -> Path:
        """
        Save checkpoint after completing a phase.

        Args:
            phase: Name of completed phase
            data: Data to save
            progress: Overall progress percentage (0-100)

        Returns:
            Path to saved checkpoint file
        """
        checkpoint_file = self.checkpoint_dir / f"{phase}-checkpoint.json"

        checkpoint = AnalysisCheckpoint(
            phase=phase,
            timestamp=time.time(),
            data=data,
            progress_percentage=progress,
            estimated_time_remaining=self._estimate_time_remaining(progress),
        )

        with open(checkpoint_file, "w") as f:
            json.dump(asdict(checkpoint), f, indent=2, default=str)

        # Also save a "latest" symlink/marker
        latest_file = self.checkpoint_dir / "latest-checkpoint.txt"
        with open(latest_file, "w") as f:
            f.write(phase)

        return checkpoint_file

    def load_checkpoint(self, phase: Optional[str] = None) -> Optional[AnalysisCheckpoint]:
        """
        Load checkpoint from a specific phase or the latest checkpoint.

        Args:
            phase: Specific phase to load, or None for latest

        Returns:
            AnalysisCheckpoint if found, None otherwise
        """
        if phase is None:
            # Load latest checkpoint
            latest_file = self.checkpoint_dir / "latest-checkpoint.txt"
            if not latest_file.exists():
                return None

            with open(latest_file, "r") as f:
                phase = f.read().strip()

        checkpoint_file = self.checkpoint_dir / f"{phase}-checkpoint.json"

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, "r") as f:
                data = json.load(f)

            return AnalysisCheckpoint(
                phase=data["phase"],
                timestamp=data["timestamp"],
                data=data["data"],
                progress_percentage=data.get("progress_percentage", 0.0),
                estimated_time_remaining=data.get("estimated_time_remaining"),
            )
        except Exception:
            return None

    def get_resume_point(self) -> Optional[str]:
        """
        Get the phase to resume from.

        Returns:
            Next phase to execute, or None if starting fresh
        """
        latest = self.load_checkpoint()

        if not latest:
            return None  # Start from beginning

        # Find next phase after latest checkpoint
        try:
            current_phase_idx = self.phases.index(latest.phase)
            if current_phase_idx + 1 < len(self.phases):
                return self.phases[current_phase_idx + 1]
            else:
                return None  # Analysis complete
        except ValueError:
            return None

    def list_checkpoints(self) -> list[AnalysisCheckpoint]:
        """
        List all available checkpoints.

        Returns:
            List of checkpoints ordered by phase
        """
        checkpoints = []

        for phase in self.phases:
            checkpoint = self.load_checkpoint(phase)
            if checkpoint:
                checkpoints.append(checkpoint)

        return checkpoints

    def clear_checkpoints(self) -> None:
        """Remove all checkpoint files."""
        for checkpoint_file in self.checkpoint_dir.glob("*-checkpoint.json"):
            checkpoint_file.unlink()

        latest_file = self.checkpoint_dir / "latest-checkpoint.txt"
        if latest_file.exists():
            latest_file.unlink()

    def get_progress_report(self) -> Dict[str, Any]:
        """
        Get current progress report.

        Returns:
            Dictionary with progress information
        """
        checkpoints = self.list_checkpoints()

        if not checkpoints:
            return {
                "status": "not_started",
                "progress": 0.0,
                "phases_completed": 0,
                "phases_total": len(self.phases),
            }

        latest = checkpoints[-1]

        return {
            "status": "in_progress",
            "progress": latest.progress_percentage,
            "phases_completed": len(checkpoints),
            "phases_total": len(self.phases),
            "latest_phase": latest.phase,
            "elapsed_time": time.time() - self.start_time,
            "estimated_time_remaining": latest.estimated_time_remaining,
            "timestamp": datetime.fromtimestamp(latest.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _estimate_time_remaining(self, progress: float) -> Optional[float]:
        """Estimate time remaining based on progress."""
        if progress <= 0:
            return None

        elapsed = time.time() - self.start_time
        total_estimated = elapsed / (progress / 100.0)
        remaining = total_estimated - elapsed

        return max(remaining, 0.0)


class StreamingReporter:
    """
    Generate reports incrementally as analysis progresses.

    Instead of waiting for full analysis to complete, this generates
    report sections as soon as data is available.
    """

    def __init__(self, output_dir: Path):
        """
        Initialize streaming reporter.

        Args:
            output_dir: Directory to save partial reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_section(self, report_name: str, section_name: str, content: str) -> None:
        """
        Write a section to a report file.

        Args:
            report_name: Name of report (e.g., "analysis-report.md")
            section_name: Section identifier (e.g., "executive-summary")
            content: Markdown content to write
        """
        report_file = self.output_dir / report_name

        # Append to file
        with open(report_file, "a") as f:
            f.write(content)
            f.write("\n\n")

    def update_progress_indicator(self, progress: float, status: str) -> None:
        """
        Update progress indicator file.

        Args:
            progress: Progress percentage (0-100)
            status: Current status message
        """
        progress_file = self.output_dir / ".progress"

        with open(progress_file, "w") as f:
            json.dump({
                "progress": progress,
                "status": status,
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2)


def main():
    """Example usage of checkpoint system."""
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python checkpoint.py <checkpoint_dir>")
        sys.exit(1)

    checkpoint_dir = Path(sys.argv[1])
    manager = CheckpointManager(checkpoint_dir)

    # Example: Save a checkpoint
    print("Saving checkpoint...")
    manager.save_checkpoint(
        phase="discovery",
        data={"files_scanned": 1000, "languages": ["python", "javascript"]},
        progress=20.0
    )

    # Load checkpoint
    print("\nLoading checkpoint...")
    checkpoint = manager.load_checkpoint("discovery")
    if checkpoint:
        print(f"Phase: {checkpoint.phase}")
        print(f"Progress: {checkpoint.progress_percentage}%")
        print(f"Data: {checkpoint.data}")

    # Get progress report
    print("\nProgress report:")
    report = manager.get_progress_report()
    for key, value in report.items():
        print(f"  {key}: {value}")

    # Get resume point
    print(f"\nResume from: {manager.get_resume_point()}")


if __name__ == "__main__":
    main()
