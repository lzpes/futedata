from typing import Any
from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from pyspark.sql.types import StringType

from futedata.transformers.base import BaseTransformer
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


class ClubsTransformer(BaseTransformer):

    def extract(self) -> dict[str, DataFrame]:
        tm_clubs = self.read_csv("raw/transfermarkt/clubs/clubs.csv")
        tm_players = self.read_csv("raw/transfermarkt/players/players.csv")
        fd_standings = self.read_json("raw/football_data/standings/standings.json")
        return {
            "tm_clubs": tm_clubs,
            "tm_players": tm_players,
            "fd_standings": fd_standings,
        }

    def transform(self, raw: dict[str, DataFrame]) -> DataFrame:
        clubs = raw["tm_clubs"]
        players = raw["tm_players"]
        standings_raw = raw["fd_standings"]

        # 1. Calcular estatísticas do elenco a partir da tabela de jogadores
        player_stats = players.groupBy("current_club_id").agg(
            F.count("player_id").alias("player_count"),
            F.sum("market_value_in_eur").alias("total_squad_value"),
            F.avg("market_value_in_eur").alias("avg_player_value"),
            F.avg(F.datediff(F.current_date(), F.to_date("date_of_birth")) / 365.25).alias("avg_age")
        ).withColumnRenamed("current_club_id", "club_id")

        # Join clubes com as métricas calculadas
        df = clubs.join(player_stats, on="club_id", how="left")

        # 2. Extrair classificação do JSON do Football-Data
        if "standings" in standings_raw.columns:
            st_df = standings_raw.select(F.explode("standings").alias("grp"))
        else:
            st_df = standings_raw.select(F.col("value").alias("grp"))
            
        st_df = st_df.filter(F.col("grp.type") == "TOTAL")
        st_df = st_df.select(F.explode("grp.table").alias("t"))
        
        st_extracted = st_df.select(
            F.col("t.team.name").alias("fd_name"),
            F.col("t.position").alias("league_position")
        )

        # Usar Fuzzy Matching global dinâmico!
        from futedata.utils.match_teams import create_fuzzy_team_mapping
        
        # Puxamos a lista única de nomes em memória (é pequeno)
        fd_team_names = [row["fd_name"] for row in st_extracted.select("fd_name").distinct().collect()]
        tm_team_names = [row["name"] for row in clubs.select("name").distinct().collect()]
        
        dynamic_mapping = create_fuzzy_team_mapping(fd_team_names, tm_team_names)
        
        from itertools import chain
        mapping_expr = F.create_map([F.lit(x) for x in chain(*dynamic_mapping.items())])
        
        st_extracted = st_extracted.withColumn("tm_name", F.coalesce(mapping_expr[F.col("fd_name")], F.col("fd_name")))
        
        # 3. Join da posição na liga com a tabela de clubes
        df = df.join(
            st_extracted.select("tm_name", "league_position"),
            df["name"] == st_extracted["tm_name"],
            how="left"
        ).drop("tm_name")

        final_cols = [
            "club_id", "club_code", "name",
            "stadium_name", "stadium_seats",
            "squad_size", "average_age",
            "player_count", "total_squad_value", "avg_player_value", "avg_age",
            "foreigners_number", "foreigners_percentage",
            "national_team_players",
            "coach_name",
            "net_transfer_record",
            "league_position",
        ]
        
        existing_cols = [c for c in final_cols if c in df.columns]
        return df.select(*existing_cols)
