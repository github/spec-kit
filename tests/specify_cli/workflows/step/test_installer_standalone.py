"""The step installer module must stay loadable outside the package.

``.github/scripts/validate_community_workflow_step.py`` executes
``step/installer.py`` by file path to reuse its id validator and limits, so the
module may not import anything relative at import time.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

INSTALLER = (
    Path(__file__).resolve().parents[4]
    / "src" / "specify_cli" / "workflows" / "step" / "installer.py"
)


@pytest.fixture
def standalone():
    spec = importlib.util.spec_from_file_location("standalone_step_installer", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_loads_without_its_package(standalone):
    assert "standalone_step_installer" not in sys.modules
    assert standalone.StepInstallError.__name__ == "StepInstallError"


def test_validator_limits_and_excludes_are_available_standalone(standalone):
    standalone.validate_step_id("my-step")
    with pytest.raises(standalone.StepInstallError):
        standalone.validate_step_id("../escape")
    assert standalone._MAX_STEP_PACKAGE_FILES == 512
    assert standalone._MAX_STEP_PACKAGE_BYTES == 50 * 1024 * 1024
    assert standalone._MAX_STEP_PACKAGE_DEPTH == 32
    assert {".git", "__pycache__", ".DS_Store"} == set(standalone.EXCLUDE_NAMES)


def test_exclude_names_agree_with_the_shared_install_module(standalone):
    from specify_cli.workflows import _package_install

    assert set(standalone.EXCLUDE_NAMES) == set(_package_install.EXCLUDE_NAMES)
