from abc import ABC, abstractmethod
from typing import Any
from pyspark.sql import DataFrame

from futedata.config import settings
from futedata.spark import get_spark_session
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


class BaseTransformer(ABC):

    layer: str = "gold"

    def __init__(self) -> None:
        self.spark = get_spark_session("FuteData_Transformers")

    def read_json(self, path: str) -> DataFrame:
        """Lê JSON de forma distribuída localmente."""
        full_path = settings.data_dir / path
        return self.spark.read.option("multiline", "true").json(str(full_path))

    def read_csv(self, path: str) -> DataFrame:
        """Lê CSV inferindo schema."""
        full_path = settings.data_dir / path
        return self.spark.read.csv(str(full_path), header=True, inferSchema=True)

    @abstractmethod
    def extract(self) -> dict[str, DataFrame]:
        ...

    @abstractmethod
    def transform(self, raw: dict[str, DataFrame]) -> DataFrame:
        ...

    def load(self, df: DataFrame, name: str) -> None:
        """Salva no formato Parquet localmente contornando o OutputCommitter do Hadoop no Windows."""
        import os
        out_dir = settings.data_dir / self.layer / name
        os.makedirs(out_dir, exist_ok=True)
        out_file = out_dir / f"{name}.parquet"
        
        # Converte para Pandas e salva (Bypass completo do hadoop.dll no Windows)
        pd_df = df.toPandas()
        pd_df.to_parquet(str(out_file), index=False)
        logger.info("parquet_written_pandas", path=str(out_file), rows=len(pd_df))


    def run(self) -> DataFrame:
        logger.info("transform_started", transformer=self.__class__.__name__)
        raw = self.extract()
        df = self.transform(raw)
        
        # O nome da tabela Delta será o nome da classe sem a palavra "Transformer"
        table_name = self.__class__.__name__.replace("Transformer", "").lower()
        self.load(df, table_name)
        
        logger.info("transform_completed", transformer=self.__class__.__name__, rows=df.count())
        return df
