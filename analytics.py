import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

def run_analytics():
    password = quote_plus("FuteData@2026!")
    db_url = f"mssql+pymssql://sa:{password}@localhost:1433/FuteData"
    engine = create_engine(db_url)

    # ================================================================
    # ANALISE 1: Joias Subvalorizadas (Core do projeto)
    # Cruza: Desempenho + Idade + Minutos + Valor de Mercado
    # ================================================================
    print("="*70)
    print("ANALISE 1: Joias Subvalorizadas Globais")
    print("  Cruza: Gols/Assists + Idade + Minutos + Valor de Mercado")
    print("="*70)
    q1 = """
        SELECT TOP 15
            p.name AS Jogador,
            p.age AS Idade,
            p.position AS Posicao,
            p.current_club_name AS Clube,
            p.country_of_citizenship AS Pais,
            (p.total_goals + p.total_assists) AS Participacoes_Gol,
            p.total_minutes AS Minutos,
            p.market_value_in_eur / 1000000.0 AS Valor_Mi_EUR,
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
    print(pd.read_sql(q1, engine).to_string(index=False))

    # ================================================================
    # ANALISE 2: Jogadores que mais valorizaram nos ultimos anos
    # Usa: fact_valuations (187K registros de serie temporal)
    # ================================================================
    print("\n" + "="*70)
    print("ANALISE 2: Jogadores com MAIOR Valorizacao Historica")
    print("  Usa: Serie temporal de 187K avaliacoes de mercado")
    print("="*70)
    q2 = """
        WITH primeiro_ultimo AS (
            SELECT 
                v.player_id,
                v.player_name,
                v.position,
                v.country_of_citizenship,
                MIN(v.valuation_date) AS primeira_data,
                MAX(v.valuation_date) AS ultima_data,
                MIN(CASE WHEN v.valuation_date = sub.min_date THEN v.market_value_in_eur END) AS valor_inicial,
                MAX(CASE WHEN v.valuation_date = sub.max_date THEN v.market_value_in_eur END) AS valor_final
            FROM fact_valuations v
            INNER JOIN (
                SELECT player_id, MIN(valuation_date) AS min_date, MAX(valuation_date) AS max_date
                FROM fact_valuations
                GROUP BY player_id
            ) sub ON v.player_id = sub.player_id 
                AND (v.valuation_date = sub.min_date OR v.valuation_date = sub.max_date)
            GROUP BY v.player_id, v.player_name, v.position, v.country_of_citizenship
        )
        SELECT TOP 15
            player_name AS Jogador,
            position AS Posicao,
            country_of_citizenship AS Pais,
            valor_inicial / 1000000.0 AS Valor_Inicial_Mi,
            valor_final / 1000000.0 AS Valor_Final_Mi,
            (valor_final - valor_inicial) / 1000000.0 AS Ganho_Mi,
            ROUND((valor_final - valor_inicial) * 100.0 / NULLIF(valor_inicial, 0), 1) AS Valorizacao_Pct
        FROM primeiro_ultimo
        WHERE valor_inicial > 0 AND valor_final > valor_inicial
          AND valor_inicial <= 5000000
        ORDER BY Valorizacao_Pct DESC;
    """
    print(pd.read_sql(q2, engine).to_string(index=False))

    # ================================================================
    # ANALISE 3: ROI de Transferencias - Melhores negocios do mundo
    # Usa: fact_transfers (9.6K registros)
    # ================================================================
    print("\n" + "="*70)
    print("ANALISE 3: Melhores Negocios (Transferencias com maior ROI)")
    print("  Cruza: Fee paga vs Valor de mercado na epoca")
    print("="*70)
    q3 = """
        SELECT TOP 15
            t.player_name AS Jogador,
            t.position AS Posicao,
            t.country_of_citizenship AS Pais,
            t.age_at_transfer AS Idade_Na_Transf,
            t.from_club_name AS De,
            t.to_club_name AS Para,
            t.transfer_season AS Temporada,
            t.transfer_fee / 1000000.0 AS Fee_Mi_EUR,
            t.market_value_in_eur / 1000000.0 AS Valor_Mercado_Mi,
            t.fee_vs_market_diff / 1000000.0 AS Lucro_Clube_Vendedor_Mi,
            t.transfer_type AS Tipo
        FROM fact_transfers t
        WHERE t.transfer_fee > 0
          AND t.market_value_in_eur > 0
          AND t.fee_vs_market_diff > 0
        ORDER BY t.fee_vs_market_diff DESC;
    """
    print(pd.read_sql(q3, engine).to_string(index=False))

    # ================================================================
    # ANALISE 4: Jogadores de Contrato Expirando (Pechincha Real)
    # Cruza: dim_players (contrato) + desempenho
    # ================================================================
    print("\n" + "="*70)
    print("ANALISE 4: Jogadores Bons com Contrato Expirando (Oportunidade)")
    print("  Cruza: Data de expiracao + Gols/Assists + Valor")
    print("="*70)
    q4 = """
        SELECT TOP 15
            name AS Jogador,
            age AS Idade,
            position AS Posicao,
            current_club_name AS Clube,
            country_of_citizenship AS Pais,
            (total_goals + total_assists) AS Participacoes_Gol,
            total_minutes AS Minutos,
            market_value_in_eur / 1000000.0 AS Valor_Mi_EUR,
            contract_expiration_date AS Contrato_Ate
        FROM dim_players
        WHERE contract_expiration_date <= '2026-12-31'
          AND contract_expiration_date >= '2026-01-01'
          AND total_minutes >= 1000
          AND (total_goals + total_assists) >= 5
          AND market_value_in_eur >= 1000000
        ORDER BY market_value_in_eur DESC;
    """
    print(pd.read_sql(q4, engine).to_string(index=False))

    # ================================================================
    # ANALISE 5: Clubes que mais LUCRAM vendendo jogadores
    # Usa: fact_transfers agregado por clube vendedor
    # ================================================================
    print("\n" + "="*70)
    print("ANALISE 5: Clubes que Mais Lucram com Vendas de Jogadores")
    print("  Agrega: Transferencias por clube vendedor")
    print("="*70)
    q5 = """
        SELECT TOP 15
            from_club_name AS Clube_Vendedor,
            COUNT(*) AS Total_Vendas,
            SUM(transfer_fee) / 1000000.0 AS Total_Arrecadado_Mi,
            AVG(transfer_fee) / 1000000.0 AS Ticket_Medio_Mi,
            SUM(fee_vs_market_diff) / 1000000.0 AS Lucro_Total_Mi
        FROM fact_transfers
        WHERE transfer_type = 'paid'
          AND transfer_fee > 0
        GROUP BY from_club_name
        HAVING COUNT(*) >= 3
        ORDER BY Total_Arrecadado_Mi DESC;
    """
    print(pd.read_sql(q5, engine).to_string(index=False))

    # ================================================================
    # ANALISE 6: Ligas com mais gols por jogo (Entretenimento)
    # Usa: fact_games (33K jogos detalhados)
    # ================================================================
    print("\n" + "="*70)
    print("ANALISE 6: Ligas com Mais Gols por Jogo (Espetaculo)")
    print("  Agrega: 33K jogos por competicao")
    print("="*70)
    q6 = """
        SELECT
            competition_id AS Liga,
            COUNT(*) AS Total_Jogos,
            SUM(total_goals) AS Total_Gols,
            ROUND(AVG(CAST(total_goals AS FLOAT)), 2) AS Media_Gols_Jogo,
            ROUND(AVG(CAST(attendance AS FLOAT)), 0) AS Media_Publico,
            SUM(CASE WHEN home_result = 'win' THEN 1 ELSE 0 END) * 100 / COUNT(*) AS Pct_Vitoria_Mandante
        FROM fact_games
        WHERE competition_type = 'domestic_league'
          AND total_goals IS NOT NULL
        GROUP BY competition_id
        ORDER BY Media_Gols_Jogo DESC;
    """
    print(pd.read_sql(q6, engine).to_string(index=False))

    # ================================================================
    # ANALISE 7: Evolucao de Valor - Quem ta subindo agora?
    # Usa: fact_valuations (ultimas avaliacoes vs anteriores)
    # ================================================================
    print("\n" + "="*70)
    print("ANALISE 7: Jogadores em ALTA agora (Tendencia de Valorizacao)")
    print("  Filtra: Ultimas 3 avaliacoes com crescimento consistente")
    print("="*70)
    q7 = """
        WITH recentes AS (
            SELECT 
                player_id, player_name, position, country_of_citizenship,
                valuation_date, market_value_in_eur, value_change_pct,
                ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY valuation_date DESC) AS rn
            FROM fact_valuations
            WHERE value_change_pct IS NOT NULL
        )
        SELECT TOP 15
            player_name AS Jogador,
            position AS Posicao,
            country_of_citizenship AS Pais,
            market_value_in_eur / 1000000.0 AS Valor_Atual_Mi,
            value_change_pct AS Ultima_Variacao_Pct,
            valuation_date AS Data_Avaliacao
        FROM recentes
        WHERE rn = 1
          AND value_change_pct > 20
          AND market_value_in_eur <= 10000000
          AND market_value_in_eur >= 500000
        ORDER BY value_change_pct DESC;
    """
    print(pd.read_sql(q7, engine).to_string(index=False))

    print("\n" + "="*70)
    print("  RESUMO DO BANCO DE DADOS")
    print("="*70)
    q_summary = """
        SELECT 'dim_clubs' AS Tabela, COUNT(*) AS Registros FROM dim_clubs
        UNION ALL SELECT 'dim_players', COUNT(*) FROM dim_players
        UNION ALL SELECT 'fact_matches', COUNT(*) FROM fact_matches
        UNION ALL SELECT 'fact_valuations', COUNT(*) FROM fact_valuations
        UNION ALL SELECT 'fact_transfers', COUNT(*) FROM fact_transfers
        UNION ALL SELECT 'fact_games', COUNT(*) FROM fact_games;
    """
    print(pd.read_sql(q_summary, engine).to_string(index=False))


if __name__ == "__main__":
    run_analytics()
