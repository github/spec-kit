import pandas as pd
from excel_diff.compare import compare_frames


def test_simple_change():
    a = pd.DataFrame([
        {'ID':1, 'Value':10},
        {'ID':2, 'Value':20},
    ])
    b = pd.DataFrame([
        {'ID':1, 'Value':15},
        {'ID':3, 'Value':30},
    ])
    added, removed, changes = compare_frames(a, b, ['ID'])
    assert set(added) == {3}
    assert set(removed) == {2}
    assert len(changes) == 1
    row = changes.iloc[0]
    assert row['column'] == 'Value'
    assert row['delta'] == 5
