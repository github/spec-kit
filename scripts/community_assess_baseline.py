"""Build the observable retrospective baseline required by the community pilot.

The selection is deterministic for a fixed repository, window, and sample size.
It deliberately records maintainer-time measures as unknown: GitHub exposes
timestamps and review activity, but not the minutes a maintainer spent on
triage or clarification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


COMMUNITY_ASSOCIATIONS = {
    "NONE",
    "FIRST_TIMER",
    "FIRST_TIME_CONTRIBUTOR",
    "CONTRIBUTOR",
}
STRATUM_STATUS_ORDER = ("merged", "closed-unmerged", "open")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="github/spec-kit")
    parser.add_argument("--since", required=True, help="Inclusive ISO-8601 UTC date/time")
    parser.add_argument("--until", required=True, help="Exclusive ISO-8601 UTC date/time")
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path)
    parser.add_argument("--api-url", default="https://api.github.com")
    return parser.parse_args(argv)


def parse_timestamp(value: str) -> datetime:
    """Parse GitHub's UTC timestamp or a date-only argument."""

    if len(value) == 10:
        value = f"{value}T00:00:00Z"
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso(value: str | None) -> str | None:
    return value.replace("Z", "+00:00") if value else None


def minutes_between(start: str, end: str | None) -> float | None:
    if not end:
        return None
    return round(
        (parse_timestamp(end).timestamp() - parse_timestamp(start).timestamp()) / 60,
        3,
    )


class GitHubAPI:
    def __init__(self, api_url: str, token: str) -> None:
        self.api_url = api_url.rstrip("/")
        self.token = token

    def get(self, path: str, params: dict[str, str | int] | None = None) -> Any:
        query = urllib.parse.urlencode(params or {})
        url = f"{self.api_url}{path}" + (f"?{query}" if query else "")
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "spec-kit-community-assess-baseline",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"GitHub API {error.code} for {path}: {detail}") from error

    def paginate(self, path: str, params: dict[str, str | int] | None = None) -> list[Any]:
        result: list[Any] = []
        page = 1
        while True:
            page_params = dict(params or {})
            page_params.update(per_page=100, page=page)
            chunk = self.get(path, page_params)
            if not isinstance(chunk, list):
                raise RuntimeError(f"Expected a paginated list from {path}")
            result.extend(chunk)
            if len(chunk) < 100:
                return result
            page += 1


def list_window_prs(api: GitHubAPI, repo: str, since: datetime, until: datetime) -> list[dict[str, Any]]:
    """List the complete fixed window without GitHub search's 1,000-result cap."""

    result: list[dict[str, Any]] = []
    page = 1
    while True:
        chunk = api.get(
            f"/repos/{repo}/pulls",
            {"state": "all", "sort": "created", "direction": "desc", "per_page": 100, "page": page},
        )
        if not chunk:
            return result
        oldest = None
        for item in chunk:
            created = parse_timestamp(item["created_at"])
            oldest = created if oldest is None or created < oldest else oldest
            if since <= created < until:
                result.append(item)
        if oldest is not None and oldest < since:
            return result
        page += 1


def is_community_pr(item: dict[str, Any]) -> bool:
    association = item.get("author_association")
    user = item.get("user") or {}
    login = str(user.get("login") or "")
    return (
        association in COMMUNITY_ASSOCIATIONS
        and str(user.get("type") or "User") != "Bot"
        and not login.endswith("[bot]")
    )


def status_group(pr: dict[str, Any]) -> str:
    if pr.get("merged_at"):
        return "merged"
    if pr.get("state") == "closed":
        return "closed-unmerged"
    return "open"


def stratum_key(pr: dict[str, Any]) -> str:
    return f"{status_group(pr)}:{pr.get('author_association', 'UNKNOWN')}"


def deterministic_order(repo: str, since: str, until: str, pr: dict[str, Any]) -> tuple[str, int]:
    seed = f"{repo}|{since}|{until}|{pr['number']}".encode("utf-8")
    return hashlib.sha256(seed).hexdigest(), int(pr["number"])


def allocate_counts(population: dict[str, int], sample_size: int) -> dict[str, int]:
    if sample_size <= 0:
        raise ValueError("sample size must be positive")
    total = sum(population.values())
    if total < sample_size:
        raise ValueError(f"population has {total} records, cannot sample {sample_size}")
    exact = {key: count * sample_size / total for key, count in population.items()}
    allocation = {key: min(population[key], int(value)) for key, value in exact.items()}
    remaining = sample_size - sum(allocation.values())
    # Resolve equal remainders by the caller's deterministic mapping order.
    # This keeps allocation reproducible without making the tie break depend
    # on a second, unrelated lexical ordering.
    order = {key: index for index, key in enumerate(population)}
    ranking = sorted(
        population,
        key=lambda key: (-(exact[key] - int(exact[key])), order[key]),
    )
    while remaining:
        for key in ranking:
            if allocation[key] < population[key]:
                allocation[key] += 1
                remaining -= 1
                if not remaining:
                    break
    return allocation


def select_sample(
    repo: str,
    since: str,
    until: str,
    prs: Iterable[dict[str, Any]],
    sample_size: int,
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, int]]:
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pr in prs:
        by_stratum[stratum_key(pr)].append(pr)
    population = {key: len(value) for key, value in sorted(by_stratum.items())}
    allocation = allocate_counts(population, sample_size)
    sample: list[dict[str, Any]] = []
    for key, records in by_stratum.items():
        records.sort(key=lambda pr: deterministic_order(repo, since, until, pr))
        sample.extend(records[: allocation[key]])
    sample.sort(key=lambda pr: int(pr["number"]))
    return sample, population, allocation


def enrich_pr(api: GitHubAPI, pr: dict[str, Any], measurement_at: str) -> dict[str, Any]:
    number = int(pr["number"])
    detail = api.get(f"/repos/{api.repo}/pulls/{number}")
    reviews = api.paginate(f"/repos/{api.repo}/pulls/{number}/reviews")
    comments = api.paginate(f"/repos/{api.repo}/issues/{number}/comments")
    head_sha = detail.get("head", {}).get("sha")
    check_runs: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []
    if head_sha:
        check_runs = api.get(
            f"/repos/{api.repo}/commits/{head_sha}/check-runs",
            {"per_page": 100},
        ).get("check_runs", [])
        statuses = api.get(
            f"/repos/{api.repo}/commits/{head_sha}/status",
            {"per_page": 100},
        ).get("statuses", [])
    submitted = sorted(
        review["submitted_at"]
        for review in reviews
        if review.get("submitted_at") and review.get("state") not in {"PENDING"}
    )
    first_review_at = submitted[0] if submitted else None
    created_at = detail["created_at"]
    close_at = detail.get("merged_at") or detail.get("closed_at") or measurement_at
    terminal_minutes = minutes_between(created_at, close_at)
    first_review_minutes = minutes_between(created_at, first_review_at)
    review_states = Counter(
        str(review.get("state", "UNKNOWN"))
        for review in reviews
        if review.get("submitted_at")
    )
    return {
        "number": number,
        "url": detail["html_url"],
        "title": detail.get("title", ""),
        "author_association": detail.get("author_association"),
        "author_login": detail.get("user", {}).get("login"),
        "status": status_group(detail),
        "state": detail.get("state"),
        "created_at": created_at,
        "closed_at": detail.get("closed_at"),
        "merged_at": detail.get("merged_at"),
        "measurement_at": measurement_at,
        "base_sha": detail.get("base", {}).get("sha"),
        "head_sha": head_sha,
        "labels": sorted(label["name"] for label in detail.get("labels", [])),
        "comment_count": len(comments),
        "review_count": len(submitted),
        "review_states": dict(sorted(review_states.items())),
        "first_review_at": first_review_at,
        "first_review_minutes": first_review_minutes,
        "check_run_count": len(check_runs),
        "status_count": len(statuses),
        "time_to_terminal_minutes": terminal_minutes,
        # GitHub has no field for these human-time measures.
        "clarification_rounds": None,
        "triage_minutes": None,
    }


def median(values: Iterable[float | None]) -> float | None:
    numbers = [value for value in values if value is not None]
    return round(statistics.median(numbers), 3) if numbers else None


def render_summary(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    lines = [
        "# Community assessment retrospective baseline",
        "",
        f"Captured at `{payload['captured_at']}` for `{payload['repo']}`.",
        f"The reproducible window is `{payload['window']['since']}` inclusive through `{payload['window']['until']}` exclusive. The population contains **{payload['population']['community_pr_count']}** eligible non-bot community PRs; the deterministic stratified sample contains **{payload['sample_size']}** records.",
        "",
        "## Selection contract",
        "",
        "Community PRs use GitHub `author_association` values `NONE`, `FIRST_TIMER`, `FIRST_TIME_CONTRIBUTOR`, or `CONTRIBUTOR`; accounts whose type is `Bot` or whose login ends in `[bot]` are excluded. Strata are the Cartesian grouping of status (`merged`, `closed-unmerged`, `open`) and author association. Within each stratum, SHA-256 of the repository, window, and PR number determines the sample order.",
        "",
        "| Stratum | Population | Sample |",
        "|---|---:|---:|",
    ]
    for key in sorted(payload["strata"]):
        lines.append(f"| `{key}` | {payload['strata'][key]['population']} | {payload['strata'][key]['sample']} |")
    lines += [
        "",
        "## Observable measurements",
        "",
        f"- Median time from creation to merged/closed or the fixed measurement time for open PRs: **{metrics['median_time_to_terminal_days']} days** (observable timestamp proxy).",
        f"- Median time from creation to the first submitted review: **{metrics['median_first_review_minutes']} minutes** across {metrics['first_review_observation_count']} sampled PRs with a submitted review.",
        f"- Sampled PRs with at least one check run: **{metrics['sample_with_check_runs']}**; with commit statuses: **{metrics['sample_with_statuses']}**.",
        f"- Sampled review states: `{json.dumps(metrics['review_states'], sort_keys=True)}`; sampled labels and comment counts are retained in the JSON artifact.",
        "",
        "## Required unknowns",
        "",
        "GitHub does not expose maintainer triage minutes or a reliable clarification-round field. `triage_minutes` and `clarification_rounds` are therefore `null` for every record; no self-reported or inferred time is presented as a baseline. The pilot must collect those fields from maintainers under a separately defined measurement protocol before claiming the success thresholds.",
        "",
        "The JSON artifact retains the exact window, strata, sample numbers, revision SHAs, observable timestamps, review/check counts, and API method needed to reproduce the selection.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    since = parse_timestamp(args.since)
    until = parse_timestamp(args.until)
    if until <= since:
        raise SystemExit("--until must be later than --since")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN or GITHUB_TOKEN is required; it is never written to the output")
    api = GitHubAPI(args.api_url, token)
    api.repo = args.repo  # type: ignore[attr-defined]
    last_inclusive_date = (until - timedelta(days=1)).date().isoformat()
    query = f"repo:{args.repo} is:pr created:{since.date().isoformat()}..{last_inclusive_date}"
    search_items = list_window_prs(api, args.repo, since, until)
    candidates = [item for item in search_items if is_community_pr(item)]
    sample, population, allocation = select_sample(
        args.repo,
        since.isoformat(),
        until.isoformat(),
        candidates,
        args.sample_size,
    )
    measurement_at = until.isoformat().replace("+00:00", "Z")
    records = [enrich_pr(api, pr, measurement_at) for pr in sample]
    strata: dict[str, dict[str, int]] = {}
    for key, count in population.items():
        strata[key] = {"population": count, "sample": allocation[key]}
    review_states = Counter()
    for record in records:
        review_states.update(record["review_states"])
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "repo": args.repo,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "window": {
            "since": since.isoformat().replace("+00:00", "Z"),
            "until": until.isoformat().replace("+00:00", "Z"),
            "measurement_at_for_open_prs": measurement_at,
        },
        "api": {
            "base_url": args.api_url,
            "query": query,
            "list_items_returned": len(search_items),
            "pagination": "pull request list sorted by created descending until the window start; detail/reviews/comments endpoints paginated at 100",
        },
        "eligibility": {
            "author_association": sorted(COMMUNITY_ASSOCIATIONS),
            "exclude_bots": True,
            "status_groups": list(STRATUM_STATUS_ORDER),
        },
        "population": {
            "candidate_pr_count": len(search_items),
            "community_pr_count": len(candidates),
        },
        "sample_size": len(records),
        "strata": strata,
        "records": records,
        "metrics": {
            "median_time_to_terminal_days": (
                round(
                    median(record["time_to_terminal_minutes"] for record in records) / 1440,
                    3,
                )
                if records
                else None
            ),
            "median_first_review_minutes": median(record["first_review_minutes"] for record in records),
            "first_review_observation_count": sum(record["first_review_minutes"] is not None for record in records),
            "sample_with_check_runs": sum(record["check_run_count"] > 0 for record in records),
            "sample_with_statuses": sum(record["status_count"] > 0 for record in records),
            "review_states": dict(sorted(review_states.items())),
            "triage_minutes": "unknown",
            "clarification_rounds": "unknown",
        },
        "boundaries": [
            "Observable timestamps, labels, reviews, comments, check runs, and commit statuses are evidence; they are not maintainer-time measurements.",
            "The fixed window and deterministic hash order reproduce the sample, while current GitHub API fields may change if records are edited or deleted.",
            "No PR body, comment, diff, or contributor command is executed by this baseline collector.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.summary_output:
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output.write_text(render_summary(payload), encoding="utf-8")
    print(json.dumps({"population": len(candidates), "sample": len(records), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
