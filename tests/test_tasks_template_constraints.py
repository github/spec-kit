"""Regression test for #4383: tasks.md loses data-model field constraints.

The /speckit.tasks command template maps data-model.md entities to task
descriptions but did not require that field-level constraints (max length,
nullable/required, enum values, validation rules) be carried into the
generated task text verbatim. Without an explicit instruction, the
implementing agent falls back to its own defaults instead of the value
recorded in data-model.md.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TASKS_TEMPLATE = REPO_ROOT / "templates" / "commands" / "tasks.md"


def test_data_model_section_requires_verbatim_field_constraints():
    content = TASKS_TEMPLATE.read_text(encoding="utf-8")

    from_data_model_start = content.index("**From Data Model**")
    next_section_start = content.index("**From Setup/Infrastructure**")
    section = content[from_data_model_start:next_section_start]

    assert "constraint" in section.lower(), (
        "The 'From Data Model' task-organization rules must instruct the "
        "agent to carry field constraints (max length, nullable, enum, "
        "validation rules) from data-model.md into task descriptions."
    )
