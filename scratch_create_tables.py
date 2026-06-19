from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

password = quote_plus("FuteData@2026!")
db_url = f"mssql+pymssql://sa:{password}@localhost:1433/FuteData"
engine = create_engine(db_url)

ddl = """
DROP TABLE IF EXISTS fact_valuations;
DROP TABLE IF EXISTS fact_transfers;
DROP TABLE IF EXISTS fact_games;

CREATE TABLE fact_valuations (
    player_id VARCHAR(50),
    player_name VARCHAR(255),
    valuation_date DATE,
    market_value_in_eur FLOAT,
    prev_value FLOAT,
    value_change_pct FLOAT,
    current_club_name VARCHAR(255),
    current_club_id VARCHAR(50),
    player_club_domestic_competition_id VARCHAR(50),
    position VARCHAR(100),
    sub_position VARCHAR(100),
    country_of_citizenship VARCHAR(100),
    age_at_valuation INT,
    PRIMARY KEY (player_id, valuation_date)
);

CREATE TABLE fact_transfers (
    player_id VARCHAR(50),
    player_name VARCHAR(255),
    position VARCHAR(100),
    country_of_citizenship VARCHAR(100),
    age_at_transfer INT,
    transfer_date_parsed DATE,
    transfer_season VARCHAR(20),
    from_club_id VARCHAR(50),
    from_club_name VARCHAR(255),
    to_club_id VARCHAR(50),
    to_club_name VARCHAR(255),
    transfer_fee FLOAT,
    market_value_in_eur FLOAT,
    fee_vs_market_diff FLOAT,
    transfer_type VARCHAR(20)
);

CREATE TABLE fact_games (
    game_id VARCHAR(50) PRIMARY KEY,
    competition_id VARCHAR(50),
    season VARCHAR(20),
    round VARCHAR(100),
    game_date DATE,
    home_club_id VARCHAR(50),
    away_club_id VARCHAR(50),
    home_club_name VARCHAR(255),
    away_club_name VARCHAR(255),
    home_club_goals INT,
    away_club_goals INT,
    total_goals INT,
    home_result VARCHAR(10),
    stadium VARCHAR(255),
    attendance INT,
    referee VARCHAR(255),
    home_club_formation VARCHAR(50),
    away_club_formation VARCHAR(50),
    home_club_manager_name VARCHAR(255),
    away_club_manager_name VARCHAR(255),
    total_players_involved INT,
    competition_type VARCHAR(50)
);
"""

with engine.begin() as conn:
    for stmt in ddl.strip().split(";"):
        s = stmt.strip()
        if s:
            conn.execute(text(s))
    print("Tabelas criadas com sucesso!")

    rows = conn.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"))
    for r in rows:
        print(f"  - {r[0]}")
