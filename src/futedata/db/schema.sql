CREATE DATABASE FuteData;
GO

USE FuteData;
GO

DROP TABLE IF EXISTS fact_matches;
DROP TABLE IF EXISTS dim_players;
DROP TABLE IF EXISTS dim_clubs;

CREATE TABLE dim_clubs (
    club_id VARCHAR(50) PRIMARY KEY,
    club_code VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    stadium_name VARCHAR(255),
    stadium_seats INT,
    squad_size INT,
    average_age FLOAT,
    player_count INT,
    total_squad_value FLOAT,
    avg_player_value FLOAT,
    avg_age FLOAT,
    foreigners_number INT,
    foreigners_percentage FLOAT,
    national_team_players INT,
    coach_name VARCHAR(255),
    net_transfer_record VARCHAR(50),
    league_position INT
);

CREATE TABLE dim_players (
    player_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    age INT,
    date_of_birth DATE,
    country_of_citizenship VARCHAR(100),
    country_of_birth VARCHAR(100),
    position VARCHAR(100),
    sub_position VARCHAR(100),
    foot VARCHAR(20),
    height_in_cm FLOAT,
    current_club_id VARCHAR(50),
    current_club_name VARCHAR(255),
    market_value_in_eur FLOAT,
    highest_market_value_in_eur FLOAT,
    total_goals INT,
    total_assists INT,
    total_yellow INT,
    total_red INT,
    total_minutes INT,
    total_appearances INT,
    contract_expiration_date DATE,
    agent_name VARCHAR(255),
    image_url VARCHAR(500)
);

-- Tabela Fato
CREATE TABLE fact_matches (
    match_id VARCHAR(50) PRIMARY KEY,
    matchday INT,
    utc_date DATE,
    status VARCHAR(50),
    home_team_id VARCHAR(50),
    home_team VARCHAR(255),
    home_team_short VARCHAR(50),
    home_team_crest VARCHAR(500),
    away_team_id VARCHAR(50),
    away_team VARCHAR(255),
    away_team_short VARCHAR(50),
    away_team_crest VARCHAR(500),
    home_score FLOAT,
    away_score FLOAT,
    winner VARCHAR(50),
    season_start DATE,
    season_end DATE,
    tm_game_id FLOAT,
    stadium VARCHAR(255),
    attendance INT,
    referee VARCHAR(255),
    home_formation VARCHAR(50),
    away_formation VARCHAR(50)
);

-- Índices adicionais para consultas analíticas (OLAP)
CREATE INDEX idx_fact_matches_date ON fact_matches(utc_date);
CREATE INDEX idx_fact_matches_home ON fact_matches(home_team_id);
CREATE INDEX idx_fact_matches_away ON fact_matches(away_team_id);
GO

-- =============================================
-- NOVAS TABELAS: Valuations, Transfers, Games
-- =============================================

DROP TABLE IF EXISTS fact_valuations;
DROP TABLE IF EXISTS fact_transfers;
DROP TABLE IF EXISTS fact_games;

-- Série temporal do valor de mercado dos jogadores (187K registros)
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

-- Histórico de transferências com cálculo de lucro/prejuízo (9.6K registros)
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

-- Jogos detalhados do Transfermarkt com lineups (33K registros)
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

CREATE INDEX idx_valuations_player ON fact_valuations(player_id);
CREATE INDEX idx_valuations_date ON fact_valuations(valuation_date);
CREATE INDEX idx_transfers_player ON fact_transfers(player_id);
CREATE INDEX idx_transfers_to_club ON fact_transfers(to_club_id);
CREATE INDEX idx_games_date ON fact_games(game_date);
CREATE INDEX idx_games_competition ON fact_games(competition_id);
GO
