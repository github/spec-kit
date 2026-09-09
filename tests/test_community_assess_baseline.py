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


def test_status_and_review_metrics_are_cut_off_at_observation_time() -> None:
    class FakeAPI:
        repo = "github/spec-kit"

        def paginate(self, path: str, params=None):
            values = []
            page = 1
            while True:
                chunk = self.get(path, {"page": page, "per_page": 100})
                values.extend(chunk)
                if len(chunk) < 100:
                    return values
                page += 1

        def get(self, path: str, params=None):
            if path.endswith("/pulls/7"):
                return {
                    "number": 7,
                    "html_url": "https://github.com/github/spec-kit/pull/7",
                    "title": "example",
                    "author_association": "CONTRIBUTOR",
                    "user": {"login": "human"},
                    "state": "closed",
                    "created_at": "2026-09-01T00:00:00Z",
                    "closed_at": "2026-09-10T00:00:00Z",
                    "merged_at": None,
                    "base": {"sha": "base"},
                    "head": {"sha": "head"},
                    "labels": [],
                }
            if path.endswith("/pulls/7/reviews"):
                return [
                    {"submitted_at": "2026-09-08T00:00:00Z", "state": "COMMENTED"},
                    {"submitted_at": "2026-09-10T00:00:00Z", "state": "APPROVED"},
                ] if (params or {}).get("page") == 1 else []
            if path.endswith("/issues/7/comments"):
                return []
            if path.endswith("/check-runs"):
                page = (params or {}).get("page")
                values = [{"id": index} for index in range(100)] if page == 1 else [{"id": 100}]
                return {"total_count": 101, "check_runs": values}
            if path.endswith("/status"):
                page = (params or {}).get("page")
                values = [{"id": index} for index in range(100)] if page == 1 else [{"id": 100}]
                return {"total_count": 101, "statuses": values}
            raise AssertionError(path)

    record = baseline.enrich_pr(FakeAPI(), {"number": 7}, "2026-09-09T00:00:00Z")

    assert record["status"] == "open"
    assert record["first_submitted_review_at"] == "2026-09-08T00:00:00Z"
    assert record["review_count"] == 1
    assert record["check_run_count"] == 101
    assert record["status_count"] == 101
    assert record["time_to_terminal_or_observation_minutes"] == 11520.0


def test_selection_uses_observed_status_for_future_closure() -> None:
    prs = [
        {
            "number": 1,
            "state": "closed",
            "closed_at": "2026-09-10T00:00:00Z",
            "author_association": "CONTRIBUTOR",
        },
        {
            "number": 2,
            "state": "closed",
            "closed_at": "2026-09-08T00:00:00Z",
            "author_association": "CONTRIBUTOR",
        },
    ]
    _, population, _ = baseline.select_sample(
        "github/spec-kit",
        "2026-09-01T00:00:00+00:00",
        "2026-09-11T00:00:00+00:00",
        prs,
        1,
        "2026-09-09T00:00:00Z",
    )

    assert population == {"closed-unmerged:CONTRIBUTOR": 1, "open:CONTRIBUTOR": 1}
