from typing import Any

from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from pyspark.sql.types import StringType

from futedata.transformers.base import BaseTransformer
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


class MatchesTransformer(BaseTransformer):

    def extract(self) -> dict[str, DataFrame]:
        fd_matches = self.read_json("raw/football_data/matches/matches.json")
        tm_games = self.read_csv("raw/transfermarkt/games/games.csv")

        return {"fd_matches": fd_matches, "tm_games": tm_games}

    def transform(self, raw: dict[str, DataFrame]) -> DataFrame:
        # 1. Football-Data: matches is an array inside the JSON. We need to explode it.
        fd_df = raw["fd_matches"]
        
        if "matches" in fd_df.columns:
            fd_df = fd_df.select(F.explode("matches").alias("m"))
        else:
            # Em caso de estrutura diferente, assume que a raiz já é o array
            fd_df = fd_df.select(F.col("value").alias("m"))

        # Extração de campos do struct aninhado do JSON usando a notação "m.campo"
        df_matches = fd_df.select(
            F.col("m.id").alias("match_id"),
            F.col("m.matchday").alias("matchday"),
            F.col("m.utcDate").alias("utc_date"),
            F.col("m.status").alias("status"),
            F.col("m.homeTeam.id").alias("home_team_id"),
            F.col("m.homeTeam.name").alias("home_team"),
            F.col("m.homeTeam.shortName").alias("home_team_short"),
            F.col("m.homeTeam.crest").alias("home_team_crest"),
            F.col("m.awayTeam.id").alias("away_team_id"),
            F.col("m.awayTeam.name").alias("away_team"),
            F.col("m.awayTeam.shortName").alias("away_team_short"),
            F.col("m.awayTeam.crest").alias("away_team_crest"),
            F.col("m.score.fullTime.home").alias("home_score"),
            F.col("m.score.fullTime.away").alias("away_score"),
            F.col("m.score.winner").alias("winner"),
            F.col("m.season.startDate").alias("season_start"),
            F.col("m.season.endDate").alias("season_end"),
        )

        # 2. Transfermarkt: Preparar o DataFrame de games
        tm_subset = raw["tm_games"].select(
            F.col("game_id").alias("tm_game_id"),
            F.col("date").alias("tm_date"),
            F.col("home_club_name").alias("tm_home_club_name"),
            F.col("stadium"),
            F.col("attendance"),
            F.col("referee"),
            F.col("home_club_formation").alias("home_formation"),
            F.col("away_club_formation").alias("away_formation"),
        )

        # 3. Tratamento para o Join: Parsear data (YYYY-MM-DD) e padronizar nome do time
        
        # Usar Fuzzy Matching global dinâmico!
        from futedata.utils.match_teams import create_fuzzy_team_mapping
        
        fd_team_names = [row["home_team"] for row in df_matches.select("home_team").distinct().collect()]
        tm_team_names = [row["tm_home_club_name"] for row in tm_subset.select("tm_home_club_name").distinct().collect()]
        
        dynamic_mapping = create_fuzzy_team_mapping(fd_team_names, tm_team_names)
        
        from itertools import chain
        mapping_expr = F.create_map([F.lit(x) for x in chain(*dynamic_mapping.items())])

        # Adicionar colunas tratadas no Football-Data (Lado Esquerdo)
        df_matches = df_matches.withColumn("join_date", F.to_date(F.col("utc_date")))
        df_matches = df_matches.withColumn("join_team", F.coalesce(mapping_expr[F.col("home_team")], F.col("home_team")))

        # Adicionar colunas tratadas no Transfermarkt (Lado Direito)
        tm_subset = tm_subset.withColumn("join_date", F.to_date(F.col("tm_date")))
        tm_subset = tm_subset.withColumn("join_team", F.col("tm_home_club_name"))

        # 4. O JOIN! Agora usando Data + Nome do Time Mandante (resolve o bug anterior)
        df_merged = df_matches.join(
            tm_subset,
            on=["join_date", "join_team"],
            how="left"
        )

        # Dropar as colunas de join criadas temporariamente
        df_merged = df_merged.drop("join_date", "join_team", "tm_date", "tm_home_club_name")
        
        # O PySpark lida bem com dropDuplicates se quisermos garantir que não houve explosão
        df_merged = df_merged.dropDuplicates(["match_id"])

        return df_merged
