from typing import Any
from pyspark.sql import DataFrame
import pyspark.sql.functions as F

from futedata.transformers.base import BaseTransformer
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


class StandingsTransformer(BaseTransformer):

    def extract(self) -> dict[str, DataFrame]:
        fd_standings = self.read_json("raw/football_data/standings/standings.json")
        return {"fd_standings": fd_standings}

    def transform(self, raw: dict[str, DataFrame]) -> DataFrame:
        df = raw["fd_standings"]
        
        # O JSON original tem um array "standings", precisamos explodir para pegar as tabelas
        if "standings" in df.columns:
            df = df.select(F.explode("standings").alias("grp"))
        else:
            df = df.select(F.col("value").alias("grp"))
            
        # Filtrar apenas o tipo TOTAL (ignorar HOME/AWAY se houver)
        df = df.filter(F.col("grp.type") == "TOTAL")
        
        # Dentro do group, temos o array "table". Vamos explodir novamente.
        df = df.select(F.explode("grp.table").alias("t"))
        
        df_standings = df.select(
            F.col("t.position").alias("position"),
            F.col("t.team.id").alias("team_id"),
            F.col("t.team.name").alias("team_name"),
            F.col("t.team.shortName").alias("team_short"),
            F.col("t.team.crest").alias("team_crest"),
            F.col("t.playedGames").alias("played"),
            F.col("t.won").alias("won"),
            F.col("t.draw").alias("draw"),
            F.col("t.lost").alias("lost"),
            F.col("t.points").alias("points"),
            F.col("t.goalsFor").alias("goals_for"),
            F.col("t.goalsAgainst").alias("goals_against"),
            F.col("t.goalDifference").alias("goal_difference"),
            F.col("t.form").alias("form"),
        )
        
        return df_standings
