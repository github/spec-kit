import csv
from pathlib import Path
from collections import Counter

import typer


app = typer.Typer(add_completion=False)


@app.command()
def main(
    input_csv: Path = typer.Option(..., exists=True, help="CSV with columns: example_id,component,error"),
):
    counts = Counter()
    with input_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("error", "").strip().lower() in ("yes", "true", "1"):
                counts[row.get("component", "unknown")] += 1

    print("Component Error Tally:")
    for comp, n in counts.most_common():
        print(f"- {comp}: {n}")


if __name__ == "__main__":
    main()


