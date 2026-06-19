from typing import Any
from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from pyspark.sql.types import IntegerType

from futedata.transformers.base import BaseTransformer
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


class PlayersTransformer(BaseTransformer):

    def extract(self) -> dict[str, DataFrame]:
        tm_players = self.read_csv("raw/transfermarkt/players/players.csv")
        tm_appearances = self.read_csv("raw/transfermarkt/appearances/appearances.csv")
        return {
            "tm_players": tm_players,
            "tm_appearances": tm_appearances,
        }

    def transform(self, raw: dict[str, DataFrame]) -> DataFrame:
        tm = raw["tm_players"]
        apps = raw["tm_appearances"]

        # Agregação distribuída (PySpark GroupBy)
        agg = apps.groupBy("player_id").agg(
            F.sum("goals").alias("total_goals"),
            F.sum("assists").alias("total_assists"),
            F.sum("yellow_cards").alias("total_yellow"),
            F.sum("red_cards").alias("total_red"),
            F.sum("minutes_played").alias("total_minutes"),
            F.count("appearance_id").alias("total_appearances"),
        )

        # Join dos jogadores com as estatísticas agregadas
        df = tm.join(agg, on="player_id", how="left")

        # FillNA e cast para Integer (tratar Nulls como 0 para métricas)
        metric_cols = [
            "total_goals", "total_assists", "total_yellow", 
            "total_red", "total_minutes", "total_appearances"
        ]
        for col in metric_cols:
            df = df.withColumn(col, F.coalesce(F.col(col), F.lit(0)).cast(IntegerType()))

        # Cálculo de Idade com Funções de Data do Spark
        if "date_of_birth" in df.columns:
            df = df.withColumn(
                "age",
                F.floor(F.datediff(F.current_date(), F.to_date(F.col("date_of_birth"))) / 365.25)
            )
        else:
            df = df.withColumn("age", F.lit(None).cast(IntegerType()))

        # Selecionar e ordenar as colunas finais
        final_cols = [
            "player_id", "name", "first_name", "last_name",
            "age", "date_of_birth",
            "country_of_citizenship", "country_of_birth",
            "position", "sub_position", "foot",
            "height_in_cm",
            "current_club_id", "current_club_name",
            "market_value_in_eur", "highest_market_value_in_eur",
            "total_goals", "total_assists",
            "total_yellow", "total_red",
            "total_minutes", "total_appearances",
            "contract_expiration_date", "agent_name",
            "image_url",
        ]
        
        # Manter apenas as colunas que realmente existem no DataFrame
        existing_cols = [c for c in final_cols if c in df.columns]
        return df.select(*existing_cols)
