import gzip
import io
import httpx
import pandas as pd

url = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/competitions.csv.gz"
print("Baixando competições...")
response = httpx.get(url, timeout=30.0)
decompressed = gzip.decompress(response.content)
df = pd.read_csv(io.BytesIO(decompressed), low_memory=False)

print(f"Total de competições globais no dataset: {len(df)}")
br_comps = df[df["country_name"] == "Brazil"]
print("\nCompetições Brasileiras disponíveis:")
print(br_comps[["competition_id", "name", "sub_type", "type"]].to_string())

# Quais outros campeonatos secundários grandes existem?
print("\nCompetições na Inglaterra:")
eng_comps = df[df["country_name"] == "England"]
print(eng_comps[["competition_id", "name"]].to_string())
