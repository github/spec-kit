import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent / 'data'
OUT.mkdir(exist_ok=True)

base = pd.DataFrame([
    {'ID': 1, 'Name': 'Alice', 'Value': 100},
    {'ID': 2, 'Name': 'Bob', 'Value': 200},
    {'ID': 3, 'Name': 'Carol', 'Value': 300},
])

new = pd.DataFrame([
    {'ID': 1, 'Name': 'Alice', 'Value': 110},
    {'ID': 2, 'Name': 'Bob', 'Value': 200},
    {'ID': 4, 'Name': 'Dan', 'Value': 50},
])

base.to_excel(OUT / 'fileA.xlsx', index=False)
new.to_excel(OUT / 'fileB.xlsx', index=False)
print('Wrote samples to', OUT)
