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
        
        -- Metric: Cost per Goal Contribution
        ROUND(
            CAST(p.market_value_in_eur AS FLOAT) / NULLIF((p.total_goals + p.total_assists), 0), 0
        ) AS cost_per_contribution,
        
        -- Metric: GA per 90 mins
        ROUND(
            CAST(p.total_goals + p.total_assists AS FLOAT) / NULLIF(p.total_minutes, 0) * 90, 2
        ) AS contributions_per_90,
        
        -- Metric: Upside Potential
        (p.highest_market_value_in_eur - p.market_value_in_eur) AS upside_value,
        
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
