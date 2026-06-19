import pandas as pd
from futedata.config import settings
import numpy as np

parquet_path = settings.data_dir / "gold" / "matches" / "matches.parquet"
df = pd.read_parquet(str(parquet_path))

row = df.iloc[0]
columns = list(row.index)
values = []

for val in row.values:
    if pd.isna(val):
        values.append("NULL")
    elif isinstance(val, (int, np.integer, float, np.floating)):
        values.append(str(val))
    else:
        # escape quotes
        val_str = str(val).replace("'", "''")
        values.append(f"'{val_str}'")

sql = f"INSERT INTO fact_matches ({', '.join(columns)}) VALUES ({', '.join(values)});\n"

with open("scratch_insert.sql", "w", encoding="utf-8") as f:
    f.write(sql)
print("Generated scratch_insert.sql")
