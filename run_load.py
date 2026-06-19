import os
import subprocess
import sys
import pandas as pd
from futedata.config import settings

def load_data_to_sql_server():
    print("Instalando dependências nativas (sqlalchemy, pymssql) para carga no SQL Server...")
    subprocess.run([sys.executable, "-m", "pip", "install", "sqlalchemy", "pymssql"], check=True)

    from sqlalchemy import create_engine
    from urllib.parse import quote_plus
    
    # Credenciais e URL do banco Docker local via SQLAlchemy
    password = quote_plus("FuteData@2026!")
    db_url = f"mssql+pymssql://sa:{password}@localhost:1433/FuteData"
    print(f"\nConectando ao SQL Server via SQLAlchemy Engine...")
    engine = create_engine(db_url)

    tables_to_load = {
        "clubs": "dim_clubs",
        "players": "dim_players",
        "matches": "fact_matches",
        "valuations": "fact_valuations",
        "transfers": "fact_transfers",
        "games": "fact_games",
    }

    print("\nIniciando carga (Load) dos dados Gold para o SQL Server nativamente...\n")

    from sqlalchemy import text
    with engine.begin() as conn:
        print("Limpando tabelas antigas...")
        conn.execute(text("DELETE FROM fact_games"))
        conn.execute(text("DELETE FROM fact_transfers"))
        conn.execute(text("DELETE FROM fact_valuations"))
        conn.execute(text("DELETE FROM fact_matches"))
        conn.execute(text("DELETE FROM dim_players"))
        conn.execute(text("DELETE FROM dim_clubs"))

    for gold_table, sql_table in tables_to_load.items():
        parquet_path = settings.data_dir / "gold" / gold_table / f"{gold_table}.parquet"
        
        if not os.path.exists(parquet_path):
            print(f"[{gold_table}] Arquivo não encontrado: {parquet_path}")
            continue
            
        print(f"[{gold_table}] Lendo Parquet e enviando para a tabela '{sql_table}'...")
        pd_df = pd.read_parquet(str(parquet_path))
        
        # Deduplicar por chave primária para evitar IntegrityError
        pk_map = {
            "dim_clubs": "club_id",
            "dim_players": "player_id",
            "fact_matches": "match_id",
            "fact_games": "game_id",
        }
        if sql_table in pk_map:
            before = len(pd_df)
            pd_df = pd_df.drop_duplicates(subset=[pk_map[sql_table]], keep="first")
            if len(pd_df) < before:
                print(f"  [{gold_table}] Dedup: {before} -> {len(pd_df)} ({before - len(pd_df)} duplicatas removidas)")

        # Faz a inserção bypassando os problemas de rede/Py4J do Spark no Windows
        try:
            pd_df.to_sql(name=sql_table, con=engine, if_exists="append", index=False)
            print(f"[{gold_table}] Sucesso! {len(pd_df)} registros carregados.")
        except Exception as e:
            print(f"[{gold_table}] ERRO: {e}")

if __name__ == "__main__":
    load_data_to_sql_server()
