from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from pyspark.sql.types import FloatType

from futedata.transformers.base import BaseTransformer
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


class TransfersTransformer(BaseTransformer):
    """Transforma o dataset de transferências em Gold, calculando lucro/prejuízo dos clubes."""

    def extract(self) -> dict[str, DataFrame]:
        transfers = self.read_csv("raw/transfermarkt/transfers/transfers.csv")
        players = self.read_csv("raw/transfermarkt/players/players.csv")
        return {"transfers": transfers, "players": players}

    def transform(self, raw: dict[str, DataFrame]) -> DataFrame:
        tr = raw["transfers"]
        players = raw["players"]

        # Enriquecer com dados do jogador
        player_info = players.select(
            F.col("player_id"),
            F.col("position"),
            F.col("sub_position"),
            F.col("country_of_citizenship"),
            F.col("date_of_birth"),
            F.col("current_club_name").alias("current_club"),
        )

        df = tr.join(player_info, on="player_id", how="left")

        # Parsear data da transferência
        df = df.withColumn("transfer_date_parsed", F.to_date(F.col("transfer_date")))

        # Idade do jogador na data da transferência
        df = df.withColumn(
            "age_at_transfer",
            F.floor(F.datediff(F.col("transfer_date_parsed"), F.to_date(F.col("date_of_birth"))) / 365.25)
        )

        # Calcular lucro/prejuízo: fee paga vs. valor de mercado na época
        df = df.withColumn(
            "fee_vs_market_diff",
            F.when(
                F.col("transfer_fee").isNotNull() & F.col("market_value_in_eur").isNotNull(),
                F.round(F.col("transfer_fee") - F.col("market_value_in_eur"), 2)
            ).otherwise(None)
        )

        # Flag: foi empréstimo (fee = 0) ou transferência paga?
        df = df.withColumn(
            "transfer_type",
            F.when(F.col("transfer_fee").isNull(), "unknown")
             .when(F.col("transfer_fee") == 0, "free/loan")
             .otherwise("paid")
        )

        final_cols = [
            "player_id", "player_name", "position", "country_of_citizenship",
            "age_at_transfer",
            "transfer_date_parsed", "transfer_season",
            "from_club_id", "from_club_name",
            "to_club_id", "to_club_name",
            "transfer_fee", "market_value_in_eur",
            "fee_vs_market_diff", "transfer_type",
        ]

        existing = [c for c in final_cols if c in df.columns]
        return df.select(*existing)
