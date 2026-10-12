"""Shared fixtures for mirrored integration command tests."""

import pytest

from tests.specify_cli.integrations._helpers import _copy_project_template, _init_project


@pytest.fixture(scope="module")
def status_copilot_template(tmp_path_factory):
    return _init_project(tmp_path_factory.mktemp("status-copilot"), "copilot")

@pytest.fixture(scope="module")
def status_claude_template(tmp_path_factory):
    return _init_project(tmp_path_factory.mktemp("status-claude"), "claude")

@pytest.fixture
def copilot_project(tmp_path, status_copilot_template):
    return _copy_project_template(tmp_path, status_copilot_template)

@pytest.fixture
def claude_project(tmp_path, status_claude_template):
    return _copy_project_template(tmp_path, status_claude_template)
