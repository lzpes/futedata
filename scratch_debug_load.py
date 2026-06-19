import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from futedata.config import settings

password = quote_plus("FuteData@2026!")
db_url = f"mssql+pymssql://sa:{password}@localhost:1433/FuteData"
engine = create_engine(db_url)

parquet_path = settings.data_dir / "gold" / "matches" / "matches.parquet"
df = pd.read_parquet(str(parquet_path))

# Insert row by row to catch the real error
for i, row in df.iterrows():
    try:
        pd.DataFrame([row]).to_sql(name="fact_matches", con=engine, if_exists="append", index=False)
    except Exception as e:
        print(f"Error on row {i} (Match {row['match_id']}): {e}")
        break
