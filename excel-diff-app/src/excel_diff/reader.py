from pathlib import Path
import pandas as pd


def read_sheet(path: str, sheet=0) -> pd.DataFrame:
    """Read an Excel sheet into a DataFrame."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return pd.read_excel(p, sheet_name=sheet, engine="openpyxl")
