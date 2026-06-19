from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from pyspark.sql.types import IntegerType, FloatType

from futedata.transformers.base import BaseTransformer
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


class ValuationsTransformer(BaseTransformer):
    """Transforma o histórico de valuations dos jogadores em série temporal Gold."""

    def extract(self) -> dict[str, DataFrame]:
        valuations = self.read_csv("raw/transfermarkt/player_valuations/player_valuations.csv")
        players = self.read_csv("raw/transfermarkt/players/players.csv")
        return {"valuations": valuations, "players": players}

    def transform(self, raw: dict[str, DataFrame]) -> DataFrame:
        val = raw["valuations"]
        players = raw["players"]

        # Enriquecer valuations com dados do jogador (nome, posição, nacionalidade)
        player_info = players.select(
            F.col("player_id"),
            F.col("name").alias("player_name"),
            F.col("position"),
            F.col("sub_position"),
            F.col("country_of_citizenship"),
            F.col("date_of_birth"),
        )

        df = val.join(player_info, on="player_id", how="left")

        # Parsear data da valuation
        df = df.withColumn("valuation_date", F.to_date(F.col("date")))

        # Calcular idade do jogador NA DATA da avaliação (não hoje)
        df = df.withColumn(
            "age_at_valuation",
            F.floor(F.datediff(F.col("valuation_date"), F.to_date(F.col("date_of_birth"))) / 365.25)
        )

        # Calcular variação percentual em relação à avaliação anterior (Window Function)
        from pyspark.sql.window import Window
        w = Window.partitionBy("player_id").orderBy("valuation_date")

        df = df.withColumn("prev_value", F.lag("market_value_in_eur").over(w))
        df = df.withColumn(
            "value_change_pct",
            F.when(F.col("prev_value").isNotNull() & (F.col("prev_value") > 0),
                   F.round((F.col("market_value_in_eur") - F.col("prev_value")) / F.col("prev_value") * 100, 2)
            ).otherwise(None)
        )

        final_cols = [
            "player_id", "player_name", "valuation_date",
            "market_value_in_eur", "prev_value", "value_change_pct",
            "current_club_name", "current_club_id",
            "player_club_domestic_competition_id",
            "position", "sub_position", "country_of_citizenship",
            "age_at_valuation",
        ]

        existing = [c for c in final_cols if c in df.columns]
        return df.select(*existing)
