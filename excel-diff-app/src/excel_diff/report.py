import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


def write_diff_csv(changes_df: pd.DataFrame, out_path: str):
    p = Path(out_path)
    changes_df.to_csv(p, index=False)


def chart_numeric_deltas(changes_df: pd.DataFrame, out_path: str):
    if changes_df is None or changes_df.empty:
        print("No changes to chart")
        return
    num = changes_df.dropna(subset=['delta'])
    if num.empty:
        print("No numeric deltas to chart.")
        return
    agg = num.groupby('column')['delta'].sum().reset_index()
    plt.figure(figsize=(8,4))
    sns.barplot(data=agg, x='column', y='delta')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Saved chart to {out_path}")


def write_diff_excel(changes_df: pd.DataFrame, out_path: str):
    p = Path(out_path)
    with pd.ExcelWriter(p, engine='openpyxl') as w:
        changes_df.to_excel(w, sheet_name='changes', index=False)
        # Add a summary sheet for numeric deltas
        num = changes_df.dropna(subset=['delta'])
        if not num.empty:
            agg = num.groupby('column')['delta'].sum().reset_index()
            agg.to_excel(w, sheet_name='summary', index=False)
    print(f"Saved Excel diff to {out_path}")
