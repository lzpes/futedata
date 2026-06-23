import pymssql
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

def create_views():
    password = quote_plus("FuteData@2026!")
    db_url = f"mssql+pymssql://sa:{password}@localhost:1433/FuteData"
    engine = create_engine(db_url)
    
    print("Criando Wide Table (vw_master_scout)...")
    
    view_sql = """
    CREATE OR ALTER VIEW vw_master_scout AS
    SELECT 
        p.player_id,
        p.name AS player_name,
        p.age,
        p.position,
        p.country_of_citizenship AS nationality,
        c.name AS club_name,
        c.squad_size,
        p.market_value_in_eur,
        p.highest_market_value_in_eur,
        p.total_goals,
        p.total_assists,
        p.total_minutes,
        (p.total_goals + p.total_assists) AS goal_contributions,
        
        -- Metric: Defensive Reliability (Avaliação baseada em desarmes, interceptações e passes certos)
        ROUND(
            (p.tackles_per_90 * 2.0) + (p.interceptions_per_90 * 1.5) + (p.pass_completion_pct / 100.0 * 2.0), 2
        ) AS defensive_reliability,

        -- Metric: Overall Impact Score (Ajustado por Posição combinando Transfermarkt e FBRef)
        ROUND(
            CASE 
                WHEN p.position = 'Attack' THEN (p.total_goals * 2.0 + p.total_assists * 1.5)
                WHEN p.position = 'Midfield' THEN (p.total_goals * 1.5 + p.total_assists * 1.5) + (p.tackles_per_90 * 1.0) + (p.pass_completion_pct / 100.0 * 2.0)
                WHEN p.position = 'Defender' THEN (p.tackles_per_90 * 2.0) + (p.interceptions_per_90 * 1.5) + (p.pass_completion_pct / 100.0 * 2.0)
                WHEN p.position = 'Goalkeeper' THEN (p.pass_completion_pct / 100.0 * 5.0) - (p.total_red * 3.0)
                ELSE (p.total_goals + p.total_assists)
            END, 2
        ) AS impact_score,

        -- Metric: Cost per Impact
        ROUND(
            CAST(p.market_value_in_eur AS FLOAT) / 
            NULLIF(
                CASE 
                    WHEN p.position = 'Attack' THEN (p.total_goals * 2.0 + p.total_assists * 1.5)
                    WHEN p.position = 'Midfield' THEN (p.total_goals * 1.5 + p.total_assists * 1.5) + (p.tackles_per_90 * 1.0) + (p.pass_completion_pct / 100.0 * 2.0)
                    WHEN p.position = 'Defender' THEN (p.tackles_per_90 * 2.0) + (p.interceptions_per_90 * 1.5) + (p.pass_completion_pct / 100.0 * 2.0)
                    WHEN p.position = 'Goalkeeper' THEN (p.pass_completion_pct / 100.0 * 5.0) - (p.total_red * 3.0)
                    ELSE (p.total_goals + p.total_assists)
                END, 0
            ), 0
        ) AS cost_per_impact,
        
        -- Metric: Cost per Goal Contribution (Legacy para atacantes)
        ROUND(
            CAST(p.market_value_in_eur AS FLOAT) / NULLIF((p.total_goals + p.total_assists), 0), 0
        ) AS cost_per_contribution,
        
        -- Metric: GA per 90 mins
        ROUND(
            CAST(p.total_goals + p.total_assists AS FLOAT) / NULLIF(p.total_minutes, 0) * 90, 2
        ) AS contributions_per_90,
        
        -- Metric: Upside Potential (Regra de Negócio: Jogadores > 29 anos não têm upside financeiro de revenda)
        CASE 
            WHEN p.age <= 29 THEN (p.highest_market_value_in_eur - p.market_value_in_eur)
            ELSE 0 
        END AS upside_value,
        
        p.contract_expiration_date,
        p.image_url

    FROM dim_players p
    LEFT JOIN dim_clubs c ON p.current_club_id = c.club_id
    WHERE p.market_value_in_eur > 0;
    """
    
    with engine.begin() as conn:
        conn.execute(text(view_sql))
        
    print("View vw_master_scout criada com sucesso!")

if __name__ == "__main__":
    create_views()
