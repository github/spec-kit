import pandas as pd
from typing import List, Tuple


def compare_frames(df_base: pd.DataFrame, df_new: pd.DataFrame, key_cols: List[str]):
    """Return (added_keys, removed_keys, changes_df)

    changes_df columns: ['key','column','base','new','delta']
    """
    base = df_base.set_index(key_cols, drop=False)
    new = df_new.set_index(key_cols, drop=False)

    base_index = base.index
    new_index = new.index

    added = new_index.difference(base_index)
    removed = base_index.difference(new_index)
    common = base_index.intersection(new_index)

    changes = []
    for key in common:
        # base.loc[key] can return a Series (unique) or DataFrame (duplicates); handle both
        b_row = base.loc[key]
        n_row = new.loc[key]

        if isinstance(b_row, pd.DataFrame):
            b = b_row.iloc[0]
        else:
            b = b_row

        if isinstance(n_row, pd.DataFrame):
            n = n_row.iloc[0]
        else:
            n = n_row

        # iterate through non-key columns present in both
        common_cols = [c for c in b.index if c in n.index and c not in key_cols]
        for col in common_cols:
            vb = b[col]
            vn = n[col]
            if pd.isna(vb) and pd.isna(vn):
                continue
            if vb != vn:
                try:
                    delta = float(vn) - float(vb)
                except Exception:
                    delta = None
                changes.append({
                    'key': key,
                    'column': col,
                    'base': vb,
                    'new': vn,
                    'delta': delta,
                })

    changes_df = pd.DataFrame(changes)
    return list(added), list(removed), changes_df
