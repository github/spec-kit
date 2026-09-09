"""Unit checks for the deterministic community baseline sampler."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "community_assess_baseline.py"
SPEC = importlib.util.spec_from_file_location("community_assess_baseline", SCRIPT)
assert SPEC and SPEC.loader
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)


def test_bot_and_unsupported_associations_are_excluded() -> None:
    assert baseline.is_community_pr(
        {"author_association": "CONTRIBUTOR", "user": {"login": "human", "type": "User"}}
    )
    assert not baseline.is_community_pr(
        {"author_association": "MEMBER", "user": {"login": "human", "type": "User"}}
    )
    assert not baseline.is_community_pr(
        {"author_association": "CONTRIBUTOR", "user": {"login": "ci[bot]", "type": "Bot"}}
    )


def test_stratified_selection_is_reproducible_and_exact() -> None:
    prs = [
        {"number": i, "state": "open", "author_association": "CONTRIBUTOR"}
        for i in range(1, 81)
    ] + [
        {"number": 100 + i, "state": "closed", "merged_at": "2026-06-10T00:00:00Z", "author_association": "NONE"}
        for i in range(20)
    ]
    first = baseline.select_sample("github/spec-kit", "since", "until", prs, 50)
    second = baseline.select_sample("github/spec-kit", "since", "until", prs, 50)

    assert [pr["number"] for pr in first[0]] == [pr["number"] for pr in second[0]]
    assert len(first[0]) == 50
    assert first[1] == {"merged:NONE": 20, "open:CONTRIBUTOR": 80}
    assert sum(first[2].values()) == 50


def test_allocate_counts_uses_largest_remainder() -> None:
    allocation = baseline.allocate_counts({"small": 1, "large": 9}, 5)
    assert allocation == {"small": 1, "large": 4}
