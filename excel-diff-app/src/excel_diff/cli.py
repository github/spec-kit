from typing import List

import typer

from .reader import read_sheet
from .compare import compare_frames
from .report import write_diff_csv, chart_numeric_deltas, write_diff_excel

app = typer.Typer()


@app.command()
def main(
    base: str = typer.Option(..., help="Path to base Excel file"),
    compare: str = typer.Option(..., help="Path to compare Excel file"),
    key: List[str] = typer.Option(..., '--key', help='Key column(s) to match rows'),
    sheet: str = typer.Option('0', help='Sheet name or index'),
    out_diff: str = typer.Option('diff.csv', help='Path for diff CSV or Excel'),
    out_chart: str = typer.Option('diff.png', help='Path for chart PNG'),
    format: str = typer.Option('csv', help='Output format: csv|excel|both'),
    threshold: float = typer.Option(None, help='Optional numeric threshold to exit non-zero if sum of absolute deltas exceeds this')
):
    """Compare two Excel files and produce a diff and an optional chart."""
    # coerce sheet
    try:
        sheet_val = int(sheet)
    except Exception:
        sheet_val = sheet

    df_base = read_sheet(base, sheet_val)
    df_new = read_sheet(compare, sheet_val)

    added, removed, changes = compare_frames(df_base, df_new, key)

    # write outputs according to format
    if format in ('csv', 'both'):
        out_csv = out_diff if format == 'csv' else out_diff + '.csv'
        write_diff_csv(changes, out_csv)
    if format in ('excel', 'both'):
        excel_path = out_diff if out_diff.lower().endswith('.xlsx') else out_diff + '.xlsx'
        write_diff_excel(changes, excel_path)

    chart_numeric_deltas(changes, out_chart)

    total_abs_delta = 0.0
    if not changes.empty:
        num = changes.dropna(subset=['delta'])
        if not num.empty:
            total_abs_delta = num['delta'].abs().sum()

    if threshold is not None and total_abs_delta > threshold:
        typer.echo(f"Total absolute delta {total_abs_delta} exceeds threshold {threshold}")
        raise typer.Exit(code=2)

    typer.echo(f"Added: {len(added)}, Removed: {len(removed)}, Changed cells: {len(changes)}")


if __name__ == '__main__':
    app()
