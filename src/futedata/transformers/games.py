from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from pyspark.sql.types import IntegerType

from futedata.transformers.base import BaseTransformer
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


class GamesTransformer(BaseTransformer):
    """Transforma os 33K jogos do Transfermarkt em Gold, incluindo lineups agregados."""

    def extract(self) -> dict[str, DataFrame]:
        games = self.read_csv("raw/transfermarkt/games/games.csv")
        lineups = self.read_csv("raw/transfermarkt/game_lineups/game_lineups.csv")
        return {"games": games, "lineups": lineups}

    def transform(self, raw: dict[str, DataFrame]) -> DataFrame:
        games = raw["games"]
        lineups = raw["lineups"]

        # Agregar lineups por jogo: contar titulares e reservas por time
        lineup_agg = lineups.groupBy("game_id", "club_id").agg(
            F.sum(F.when(F.col("type") == "starting_lineup", 1).otherwise(0)).alias("starters"),
            F.sum(F.when(F.col("type") == "substitutes", 1).otherwise(0)).alias("subs"),
            F.sum(F.col("team_captain").cast(IntegerType())).alias("captain_count"),
        )

        # Agregar para ter uma visão por jogo (sem duplicar pelo club)
        lineup_game = lineups.groupBy("game_id").agg(
            F.countDistinct("player_id").alias("total_players_involved"),
        )

        df = games.join(lineup_game, on="game_id", how="left")

        # Total de gols no jogo
        df = df.withColumn(
            "total_goals",
            F.coalesce(F.col("home_club_goals"), F.lit(0)) + F.coalesce(F.col("away_club_goals"), F.lit(0))
        )

        # Resultado do ponto de vista mandante
        df = df.withColumn(
            "home_result",
            F.when(F.col("home_club_goals") > F.col("away_club_goals"), "win")
             .when(F.col("home_club_goals") < F.col("away_club_goals"), "loss")
             .otherwise("draw")
        )

        # Parsear data
        df = df.withColumn("game_date", F.to_date(F.col("date")))

        final_cols = [
            "game_id", "competition_id", "season", "round", "game_date",
            "home_club_id", "away_club_id",
            "home_club_name", "away_club_name",
            "home_club_goals", "away_club_goals", "total_goals", "home_result",
            "stadium", "attendance", "referee",
            "home_club_formation", "away_club_formation",
            "home_club_manager_name", "away_club_manager_name",
            "total_players_involved",
            "competition_type",
        ]

        existing = [c for c in final_cols if c in df.columns]
        return df.select(*existing)
