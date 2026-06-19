"""
FuteData ML Models
==================
Modelos preditivos treinados com os dados do Star Schema.

Modelo 1: Prever valor futuro de jogadores (Potencial)
Modelo 2: Prever total de gols numa partida entre dois times
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")


def get_engine():
    password = quote_plus("FuteData@2026!")
    return create_engine(f"mssql+pymssql://sa:{password}@localhost:1433/FuteData")


# ================================================================
# MODELO 1: Prever Valor Futuro de Jogadores
# ================================================================
def train_player_value_model():
    """
    Treina um modelo de Gradient Boosting para prever o proximo
    valor de mercado de um jogador baseado em:
    - Idade atual
    - Posicao (encoded)
    - Gols, Assistencias, Minutos, Aparicoes
    - Valor de mercado atual
    - Maior valor historico
    """
    engine = get_engine()
    
    print("="*70)
    print("MODELO 1: Preditor de Valor Futuro de Jogadores")
    print("="*70)
    
    # Buscar dados dos jogadores com stats
    df = pd.read_sql("""
        SELECT 
            player_id, name, age, position, 
            total_goals, total_assists, total_minutes, total_appearances,
            total_yellow, total_red,
            market_value_in_eur, highest_market_value_in_eur,
            height_in_cm
        FROM dim_players
        WHERE market_value_in_eur > 0
          AND age IS NOT NULL
          AND total_minutes > 0
    """, engine)
    
    print(f"  Jogadores no dataset de treino: {len(df)}")
    
    # Feature Engineering
    df["goals_per_90"] = (df["total_goals"] / df["total_minutes"] * 90).fillna(0)
    df["assists_per_90"] = (df["total_assists"] / df["total_minutes"] * 90).fillna(0)
    df["ga_per_90"] = df["goals_per_90"] + df["assists_per_90"]
    df["minutes_per_appearance"] = (df["total_minutes"] / df["total_appearances"].replace(0, 1)).fillna(0)
    df["value_ratio"] = (df["market_value_in_eur"] / df["highest_market_value_in_eur"].replace(0, 1)).fillna(0)
    df["cards_per_90"] = ((df["total_yellow"] + df["total_red"]) / df["total_minutes"] * 90).fillna(0)
    
    # Encode posicao
    le_pos = LabelEncoder()
    df["position_enc"] = le_pos.fit_transform(df["position"].fillna("Unknown"))
    
    features = [
        "age", "position_enc", "total_goals", "total_assists",
        "total_minutes", "total_appearances",
        "goals_per_90", "assists_per_90", "ga_per_90",
        "minutes_per_appearance", "value_ratio", "cards_per_90",
        "height_in_cm",
    ]
    
    # Target: Prever o highest_market_value como proxy do "potencial maximo"
    # (representa o teto do jogador baseado no historico)
    target = "highest_market_value_in_eur"
    
    df_clean = df.dropna(subset=features + [target])
    df_clean["height_in_cm"] = df_clean["height_in_cm"].fillna(df_clean["height_in_cm"].median())
    
    X = df_clean[features]
    y = df_clean[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42
    )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"  Metricas do Modelo:")
    print(f"    R2 Score:           {r2:.4f}")
    print(f"    MAE (Erro Medio):   EUR {mae:,.0f}")
    
    # Feature Importance
    importances = sorted(zip(features, model.feature_importances_), key=lambda x: -x[1])
    print(f"\n  Top 5 Features mais importantes:")
    for feat, imp in importances[:5]:
        print(f"    {feat:30s} {imp:.4f}")
    
    # PREVISAO: Joias com maior potencial de valorizacao
    print(f"\n  {'='*70}")
    print(f"  PREVISAO: Top 15 Jogadores com MAIOR Potencial de Valorizacao")
    print(f"  {'='*70}")
    
    df_clean["predicted_peak_value"] = model.predict(X)
    df_clean["upside"] = df_clean["predicted_peak_value"] - df_clean["market_value_in_eur"]
    df_clean["upside_pct"] = (df_clean["upside"] / df_clean["market_value_in_eur"] * 100)
    
    # Filtrar jovens com alto upside
    joias = df_clean[
        (df_clean["age"] <= 23) & 
        (df_clean["market_value_in_eur"] <= 10_000_000) &
        (df_clean["upside"] > 0) &
        (df_clean["total_minutes"] >= 1000)
    ].nlargest(15, "upside_pct")
    
    result = joias[["name", "age", "position", "market_value_in_eur", "predicted_peak_value", "upside_pct"]].copy()
    result.columns = ["Jogador", "Idade", "Posicao", "Valor_Atual_EUR", "Valor_Previsto_EUR", "Potencial_Pct"]
    result["Valor_Atual_EUR"] = (result["Valor_Atual_EUR"] / 1_000_000).round(2)
    result["Valor_Previsto_EUR"] = (result["Valor_Previsto_EUR"] / 1_000_000).round(2)
    result["Potencial_Pct"] = result["Potencial_Pct"].round(1)
    
    print(result.to_string(index=False))
    
    return model, le_pos, features


# ================================================================
# MODELO 2: Prever Total de Gols numa Partida
# ================================================================
def train_match_goals_model():
    """
    Treina um modelo para prever o total de gols numa partida
    baseado no historico ofensivo/defensivo dos dois times.
    """
    engine = get_engine()
    
    print(f"\n\n{'='*70}")
    print("MODELO 2: Preditor de Total de Gols por Partida")
    print("="*70)
    
    # Calcular stats historicas de cada time
    team_stats = pd.read_sql("""
        WITH home_stats AS (
            SELECT 
                home_club_id AS club_id,
                home_club_name AS club_name,
                AVG(CAST(home_club_goals AS FLOAT)) AS avg_goals_scored_home,
                AVG(CAST(away_club_goals AS FLOAT)) AS avg_goals_conceded_home,
                COUNT(*) AS home_games
            FROM fact_games
            WHERE competition_type = 'domestic_league'
            GROUP BY home_club_id, home_club_name
        ),
        away_stats AS (
            SELECT 
                away_club_id AS club_id,
                AVG(CAST(away_club_goals AS FLOAT)) AS avg_goals_scored_away,
                AVG(CAST(home_club_goals AS FLOAT)) AS avg_goals_conceded_away,
                COUNT(*) AS away_games
            FROM fact_games
            WHERE competition_type = 'domestic_league'
            GROUP BY away_club_id
        )
        SELECT 
            h.club_id, h.club_name,
            h.avg_goals_scored_home, h.avg_goals_conceded_home, h.home_games,
            a.avg_goals_scored_away, a.avg_goals_conceded_away, a.away_games,
            (h.avg_goals_scored_home + a.avg_goals_scored_away) / 2.0 AS overall_attack,
            (h.avg_goals_conceded_home + a.avg_goals_conceded_away) / 2.0 AS overall_defense
        FROM home_stats h
        JOIN away_stats a ON h.club_id = a.club_id
        WHERE h.home_games >= 10 AND a.away_games >= 10
    """, engine)
    
    print(f"  Times com historico suficiente: {len(team_stats)}")
    
    # Buscar todos os jogos para treino
    games = pd.read_sql("""
        SELECT game_id, home_club_id, away_club_id, total_goals, attendance
        FROM fact_games
        WHERE competition_type = 'domestic_league'
          AND total_goals IS NOT NULL
    """, engine)
    
    # Merge com stats dos times
    games = games.merge(
        team_stats[["club_id", "avg_goals_scored_home", "avg_goals_conceded_home", "overall_attack", "overall_defense"]],
        left_on="home_club_id", right_on="club_id", how="inner"
    ).rename(columns={
        "avg_goals_scored_home": "home_attack",
        "avg_goals_conceded_home": "home_defense",
        "overall_attack": "home_overall_attack",
        "overall_defense": "home_overall_defense",
    }).drop(columns=["club_id"])
    
    games = games.merge(
        team_stats[["club_id", "avg_goals_scored_away", "avg_goals_conceded_away", "overall_attack", "overall_defense"]],
        left_on="away_club_id", right_on="club_id", how="inner"
    ).rename(columns={
        "avg_goals_scored_away": "away_attack",
        "avg_goals_conceded_away": "away_defense",
        "overall_attack": "away_overall_attack",
        "overall_defense": "away_overall_defense",
    }).drop(columns=["club_id"])
    
    features = [
        "home_attack", "home_defense", "home_overall_attack", "home_overall_defense",
        "away_attack", "away_defense", "away_overall_attack", "away_overall_defense",
    ]
    
    games_clean = games.dropna(subset=features + ["total_goals"])
    
    X = games_clean[features]
    y = games_clean["total_goals"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = GradientBoostingRegressor(
        n_estimators=150, max_depth=4, learning_rate=0.1, random_state=42
    )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"  Jogos no dataset de treino: {len(games_clean)}")
    print(f"  Metricas do Modelo:")
    print(f"    R2 Score:         {r2:.4f}")
    print(f"    MAE (Erro Medio): {mae:.2f} gols")
    
    # Funcao de previsao interativa
    def predict_match(home_name: str, away_name: str):
        home = team_stats[team_stats["club_name"].str.contains(home_name, case=False, na=False)]
        away = team_stats[team_stats["club_name"].str.contains(away_name, case=False, na=False)]
        
        if home.empty:
            print(f"  Time '{home_name}' nao encontrado. Times disponiveis:")
            print("  " + ", ".join(team_stats["club_name"].head(20).tolist()))
            return
        if away.empty:
            print(f"  Time '{away_name}' nao encontrado.")
            return
            
        home = home.iloc[0]
        away = away.iloc[0]
        
        x = pd.DataFrame([{
            "home_attack": home["avg_goals_scored_home"],
            "home_defense": home["avg_goals_conceded_home"],
            "home_overall_attack": home["overall_attack"],
            "home_overall_defense": home["overall_defense"],
            "away_attack": away["avg_goals_scored_away"],
            "away_defense": away["avg_goals_conceded_away"],
            "away_overall_attack": away["overall_attack"],
            "away_overall_defense": away["overall_defense"],
        }])
        
        predicted_goals = model.predict(x)[0]
        
        # Estimar distribuicao provavel de gols
        home_expected = home["avg_goals_scored_home"] * (away["avg_goals_conceded_away"] / team_stats["avg_goals_conceded_away"].mean())
        away_expected = away["avg_goals_scored_away"] * (home["avg_goals_conceded_home"] / team_stats["avg_goals_conceded_home"].mean())
        
        print(f"\n  {'='*50}")
        print(f"  PREVISAO: {home['club_name']} vs {away['club_name']}")
        print(f"  {'='*50}")
        print(f"  Total de gols previsto:  {predicted_goals:.1f}")
        print(f"  Gols esperados mandante: {home_expected:.1f}")
        print(f"  Gols esperados visitante:{away_expected:.1f}")
        print(f"  Placar mais provavel:    {round(home_expected)}-{round(away_expected)}")
        
        if predicted_goals >= 3.5:
            print(f"  Tendencia: JOGO ABERTO (muitos gols esperados)")
        elif predicted_goals >= 2.5:
            print(f"  Tendencia: JOGO EQUILIBRADO")
        else:
            print(f"  Tendencia: JOGO FECHADO (poucos gols)")
    
    return model, team_stats, predict_match


if __name__ == "__main__":
    # Treinar Modelo 1: Potencial de Jogadores
    player_model, le_pos, player_features = train_player_value_model()
    
    # Treinar Modelo 2: Gols por Partida
    goals_model, team_stats, predict_match = train_match_goals_model()
    
    # Demonstracoes de previsao
    print(f"\n\n{'='*70}")
    print("DEMONSTRACAO: Previsoes de Partidas")
    print("="*70)
    
    # Simulacoes de confrontos
    predict_match("Bayern", "Dortmund")
    predict_match("Barcelona", "Real Madrid")
    predict_match("Liverpool", "Arsenal")
    predict_match("Flamengo", "Palmeiras")
    predict_match("Napoli", "Inter")
    predict_match("Paris Saint-Germain", "Marseille")
