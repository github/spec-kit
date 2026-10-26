"""Regression tests for workflow step catalog source ordering."""

import pytest
import yaml

from specify_cli.workflows.step.catalog import StepCatalog


@pytest.mark.parametrize(
    ("priorities", "expected_priorities"),
    [
        ([None, None, None], [1, 2, 3, 4]),
        ([1, None, None], [1, 2, 3, 4]),
        ([10, "20", 30], [10, 20, 30, 31]),
        ([-3, -2, -1], [-3, -2, -1, 0]),
    ],
    ids=["implicit", "mixed", "explicit", "negative"],
)
def test_add_catalog_appends_after_effective_priorities(
    project_dir, monkeypatch, priorities, expected_priorities
):
    monkeypatch.delenv("SPECKIT_STEP_CATALOG_URL", raising=False)
    config_path = project_dir / ".specify" / "step-catalogs.yml"
    entries = [
        {"name": name, "url": f"https://{name}.example/catalog.json"}
        for name in ("first", "second", "third")
    ]
    for entry, priority in zip(entries, priorities):
        if priority is not None:
            entry["priority"] = priority
    config_path.write_text(yaml.safe_dump({"catalogs": entries}), encoding="utf-8")

    catalog = StepCatalog(project_dir)
    assert catalog.add_catalog("https://added.example/catalog.json", "added") == "added"

    configs = StepCatalog(project_dir).get_catalog_configs()
    assert [config["name"] for config in configs] == [
        "first", "second", "third", "added"
    ]
    assert [config["priority"] for config in configs] == expected_priorities
    stored = yaml.safe_load(config_path.read_text(encoding="utf-8"))["catalogs"]
    assert stored[:-1] == entries
    assert stored[-1]["priority"] == expected_priorities[-1]
