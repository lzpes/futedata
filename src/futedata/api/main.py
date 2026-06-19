import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Para garantir que futedata é resolúvel
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

password = quote_plus("FuteData@2026!")
db_url = f"mssql+pymssql://sa:{password}@localhost:1433/FuteData"
engine = create_engine(db_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup if needed
    yield
    # Teardown if needed

app = FastAPI(title="FuteData API", lifespan=lifespan)

# Libera o CORS para o frontend (Vite porta 5173 e 4173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Para desenvolvimento local apenas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_query(query: str):
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    # Limpa valores nulos e converte para dicionario nativo
    df = df.fillna("") 
    return df.to_dict(orient="records")

class QueryRequest(BaseModel):
    query: str

@app.post("/api/query")
def execute_free_query(req: QueryRequest):
    # Endpoint para o SQL Studio
    try:
        # Apenas limitando segurança trivial para um projeto local (idealmente não fazer isso em prod)
        q = req.query.strip()
        if q.upper().startswith("DROP") or q.upper().startswith("DELETE") or q.upper().startswith("TRUNCATE") or q.upper().startswith("UPDATE") or q.upper().startswith("INSERT"):
            raise HTTPException(status_code=400, detail="Somente operações de leitura (SELECT) são permitidas.")
        
        result = run_query(q)
        return {"data": result, "columns": list(result[0].keys()) if result else []}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/summary")
def get_summary():
    q = """
        SELECT 'Clubes' AS Metric, COUNT(*) AS Total FROM dim_clubs
        UNION ALL SELECT 'Jogadores', COUNT(*) FROM dim_players
        UNION ALL SELECT 'Avaliações de Mercado', COUNT(*) FROM fact_valuations
        UNION ALL SELECT 'Transferências', COUNT(*) FROM fact_transfers
        UNION ALL SELECT 'Jogos', COUNT(*) FROM fact_games;
    """
    return run_query(q)

@app.get("/api/undervalued-players")
def get_undervalued_players():
    q = """
        SELECT TOP 15
            p.name AS Jogador,
            p.age AS Idade,
            p.position AS Posicao,
            p.current_club_name AS Clube,
            p.country_of_citizenship AS Pais,
            (p.total_goals + p.total_assists) AS Participacoes_Gol,
            p.total_minutes AS Minutos,
            ROUND(p.market_value_in_eur / 1000000.0, 2) AS Valor_Mi_EUR,
            ROUND(CAST(p.total_goals + p.total_assists AS FLOAT) / NULLIF(p.total_minutes, 0) * 90, 2) AS Gol_Assist_Per_90min,
            ROUND(p.market_value_in_eur / NULLIF(p.total_goals + p.total_assists, 0), 0) AS Custo_Por_GA
        FROM dim_players p
        WHERE p.age <= 25
          AND p.total_minutes >= 2000
          AND (p.total_goals + p.total_assists) >= 10
          AND p.market_value_in_eur <= 5000000
          AND p.market_value_in_eur > 0
        ORDER BY Gol_Assist_Per_90min DESC;
    """
    return run_query(q)

@app.get("/api/top-transfers-roi")
def get_top_transfers_roi():
    q = """
        SELECT TOP 10
            t.player_name AS Jogador,
            t.position AS Posicao,
            t.age_at_transfer AS Idade,
            t.from_club_name AS De_Clube,
            t.to_club_name AS Para_Clube,
            ROUND(t.transfer_fee / 1000000.0, 2) AS Fee_Mi_EUR,
            ROUND(t.market_value_in_eur / 1000000.0, 2) AS Valor_Mercado_Mi_EUR,
            ROUND(t.fee_vs_market_diff / 1000000.0, 2) AS Lucro_Mi_EUR
        FROM fact_transfers t
        WHERE t.transfer_fee > 0 AND t.market_value_in_eur > 0 AND t.fee_vs_market_diff > 0
        ORDER BY t.fee_vs_market_diff DESC;
    """
    return run_query(q)

@app.get("/api/expiring-contracts")
def get_expiring_contracts():
    q = """
        SELECT TOP 10
            name AS Jogador,
            age AS Idade,
            position AS Posicao,
            current_club_name AS Clube,
            (total_goals + total_assists) AS Participacoes_Gol,
            ROUND(market_value_in_eur / 1000000.0, 2) AS Valor_Mi_EUR,
            CAST(contract_expiration_date AS VARCHAR) AS Contrato_Ate
        FROM dim_players
        WHERE contract_expiration_date <= '2026-12-31' AND contract_expiration_date >= '2026-01-01'
          AND total_minutes >= 1000 AND (total_goals + total_assists) >= 5 AND market_value_in_eur >= 1000000
        ORDER BY market_value_in_eur DESC;
    """
    return run_query(q)

@app.get("/api/league-stats")
def get_league_stats():
    q = """
        SELECT
            competition_id AS Liga,
            COUNT(*) AS Total_Jogos,
            SUM(total_goals) AS Total_Gols,
            ROUND(AVG(CAST(total_goals AS FLOAT)), 2) AS Media_Gols,
            ROUND(AVG(CAST(attendance AS FLOAT)), 0) AS Media_Publico,
            SUM(CASE WHEN home_result = 'win' THEN 1 ELSE 0 END) * 100 / COUNT(*) AS Pct_Vitoria_Mandante
        FROM fact_games
        WHERE competition_type = 'domestic_league' AND total_goals IS NOT NULL
        GROUP BY competition_id
        ORDER BY Media_Gols DESC;
    """
    return run_query(q)

@app.get("/api/trending-players")
def get_trending_players():
    q = """
        WITH recentes AS (
            SELECT 
                player_id, player_name, position, country_of_citizenship,
                valuation_date, market_value_in_eur, value_change_pct,
                ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY valuation_date DESC) AS rn
            FROM fact_valuations
            WHERE value_change_pct IS NOT NULL
        )
        SELECT TOP 10
            player_name AS Jogador,
            position AS Posicao,
            ROUND(market_value_in_eur / 1000000.0, 2) AS Valor_Atual_Mi_EUR,
            value_change_pct AS Variacao_Pct,
            CAST(valuation_date AS VARCHAR) AS Data_Avaliacao
        FROM recentes
        WHERE rn = 1 AND value_change_pct > 20 AND market_value_in_eur <= 10000000 AND market_value_in_eur >= 500000
        ORDER BY value_change_pct DESC;
    """
    return run_query(q)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
