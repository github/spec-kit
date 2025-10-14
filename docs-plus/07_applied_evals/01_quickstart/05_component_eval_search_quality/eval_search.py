import re
import sys
import json
from pathlib import Path
from typing import Tuple, List, Set

import typer
import yaml


app = typer.Typer(add_completion=False)


def extract_urls(text: str) -> List[str]:
    pattern = re.compile(r"https?://[^\s\]\)>\}]+", flags=re.IGNORECASE)
    return pattern.findall(text or "")


def load_domains(domains_path: Path) -> Set[str]:
    data = yaml.safe_load(domains_path.read_text(encoding="utf-8")) or []
    return {str(x).strip().lower() for x in data if str(x).strip()}


def evaluate_preferred(domains: Set[str], raw: str, min_ratio: float) -> Tuple[bool, str]:
    urls = extract_urls(raw)
    if not urls:
        return False, (
            "### Evaluation — Preferred Domains\n"
            "No URLs detected in the provided text.\n"
            "Please include links in your research results.\n"
        )

    total = len(urls)
    preferred_count = 0
    detail_lines = []
    for url in urls:
        try:
            domain = url.split("/")[2].lower()
        except Exception:
            domain = ""
        preferred = any(d in domain for d in domains)
        if preferred:
            preferred_count += 1
        detail_lines.append(f"- {url} → {'✅ PREFERRED' if preferred else '❌ NOT PREFERRED'}")

    ratio = preferred_count / total if total else 0.0
    flag = ratio >= min_ratio
    report = (
        f"### Evaluation — Preferred Domains\n"
        f"- Total results: {total}\n"
        f"- Preferred results: {preferred_count}\n"
        f"- Ratio: {ratio:.2%}\n"
        f"- Threshold: {min_ratio:.0%}\n"
        f"- Status: {'✅ PASS' if flag else '❌ FAIL'}\n\n"
        f"**Details:**\n" + "\n".join(detail_lines)
    )
    return flag, report


@app.command()
def main(
    raw: str = typer.Option("", help="Raw text containing URLs to evaluate."),
    raw_file: Path = typer.Option(None, help="Path to file containing raw results."),
    domains: Path = typer.Option(
        Path(__file__).with_name("preferred_domains.yml"), help="YAML list of trusted domains"
    ),
    min_ratio: float = typer.Option(0.4, min=0.0, max=1.0, help="Minimum preferred ratio to pass"),
    output_json: Path = typer.Option(None, help="Optional path to write JSON result"),
):
    if raw_file and raw_file.exists():
        raw = raw_file.read_text(encoding="utf-8")
    if not raw:
        typer.echo("Provide --raw or --raw-file", err=True)
        raise typer.Exit(code=2)

    domain_set = load_domains(domains)
    flag, report = evaluate_preferred(domain_set, raw, min_ratio)
    print(report)

    if output_json:
        output_json.write_text(json.dumps({"pass": flag, "report": report}, indent=2))

    raise typer.Exit(code=0 if flag else 1)


if __name__ == "__main__":
    try:
        app()
    except SystemExit as e:
        sys.exit(e.code)


