"""End-to-end bash test for the script continuation dispatcher (#4551).

Proves the runtime chain actually executes correctly, not just that the
resolver computes the right file list: installs two "wrap" script
presets over a core script, invokes the *canonical* materialized script
exactly as a coding agent would (via its fixed frontmatter path), and
checks the process actually ran outer-before -> inner-before -> core ->
inner-after -> outer-after, with args and exit status propagated.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from specify_cli.presets import PresetManager

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
CONTINUATION_RUNNER_SH = PROJECT_ROOT / "scripts" / "bash" / "continuation-runner.sh"

# The `specify` console script must be resolvable from the bash
# subprocess's PATH, since the dispatcher shells out to `specify preset
# script-chain`. Resolve it relative to the running interpreter rather
# than assuming a particular PATH setup, so this works the same way in a
# venv, in CI, or via `pip install -e .` locally.
_BIN_DIR = str(Path(sys.executable).parent)


def _clean_env() -> dict:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    env["PATH"] = _BIN_DIR + os.pathsep + env.get("PATH", "")
    return env


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / ".specify" / "templates" / "scripts").mkdir(parents=True)
    (project / ".specify" / "scripts" / "bash").mkdir(parents=True)
    shutil.copy(COMMON_SH, project / ".specify" / "scripts" / "bash" / "common.sh")
    shutil.copy(
        CONTINUATION_RUNNER_SH,
        project / ".specify" / "scripts" / "bash" / "continuation-runner.sh",
    )
    return project


def _install_wrap_layer(
    project_dir: Path,
    temp_dir: Path,
    pack_id: str,
    priority: int,
    script_name: str,
    label: str,
) -> None:
    pack_dir = temp_dir / pack_id
    (pack_dir / "scripts").mkdir(parents=True)
    (pack_dir / "scripts" / f"{script_name}.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -e\n"
        f'echo "{label}-before $*"\n'
        '"$CORE_SCRIPT" "$@"\n'
        f'echo "{label}-after"\n'
    )
    manifest = {
        "schema_version": "1.0",
        "preset": {
            "id": pack_id,
            "name": pack_id,
            "version": "0.1.0",
            "description": "test",
            "author": "Test Author",
            "repository": "https://github.com/test/test-pack",
            "license": "MIT",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "templates": [
                {
                    "type": "script",
                    "name": script_name,
                    "file": f"scripts/{script_name}.sh",
                    "strategy": "wrap",
                }
            ]
        },
    }
    (pack_dir / "preset.yml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    manager = PresetManager(project_dir)
    manager.install_from_directory(pack_dir, "0.1.0", priority=priority)


@requires_bash
def test_two_layer_continuation_runs_in_priority_order(
    project_dir: Path, tmp_path: Path
) -> None:
    core_script = project_dir / ".specify" / "templates" / "scripts" / "chained.sh"
    core_script.write_text(
        '#!/usr/bin/env bash\necho "core $*"\n'
    )

    temp_dir = tmp_path / "packs"
    temp_dir.mkdir()
    # priority 1 (outer, checked first) and priority 5 (inner)
    _install_wrap_layer(project_dir, temp_dir, "outer-pack", 1, "chained", "outer")
    _install_wrap_layer(project_dir, temp_dir, "inner-pack", 5, "chained", "inner")

    canonical = project_dir / ".specify" / "scripts" / "bash" / "chained.sh"
    assert canonical.is_file(), "install should have written the dispatcher stub"

    result = subprocess.run(
        ["bash", str(canonical), "arg1", "arg2"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines == [
        "outer-before arg1 arg2",
        "inner-before arg1 arg2",
        "core arg1 arg2",
        "inner-after",
        "outer-after",
    ]


@requires_bash
def test_priority_change_takes_effect_without_reinstall(
    project_dir: Path, tmp_path: Path
) -> None:
    """The whole point of the continuation model (#4551): swapping
    priority must change execution order on the *next invocation*,
    without touching the canonical file at all."""
    core_script = project_dir / ".specify" / "templates" / "scripts" / "reorder.sh"
    core_script.write_text('#!/usr/bin/env bash\necho "core"\n')

    temp_dir = tmp_path / "packs"
    temp_dir.mkdir()
    _install_wrap_layer(project_dir, temp_dir, "layer-a", 1, "reorder", "a")
    _install_wrap_layer(project_dir, temp_dir, "layer-b", 5, "reorder", "b")

    canonical = project_dir / ".specify" / "scripts" / "bash" / "reorder.sh"
    before_bytes = canonical.read_bytes()

    manager = PresetManager(project_dir)
    manager.registry.update("layer-a", {"priority": 20})

    # The dispatcher file itself must be byte-for-byte unchanged —
    # reordering must not require rewriting it.
    assert canonical.read_bytes() == before_bytes

    result = subprocess.run(
        ["bash", str(canonical)],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines == ["b-before ", "a-before ", "core", "a-after", "b-after"]


@requires_bash
def test_nonzero_exit_status_propagates_through_the_chain(
    project_dir: Path, tmp_path: Path
) -> None:
    core_script = project_dir / ".specify" / "templates" / "scripts" / "failing.sh"
    core_script.write_text('#!/usr/bin/env bash\nexit 7\n')

    temp_dir = tmp_path / "packs"
    temp_dir.mkdir()
    _install_wrap_layer(project_dir, temp_dir, "wrap-pack", 1, "failing", "w")

    canonical = project_dir / ".specify" / "scripts" / "bash" / "failing.sh"
    result = subprocess.run(
        ["bash", str(canonical)],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 7
