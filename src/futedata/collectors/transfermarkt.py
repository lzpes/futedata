import gzip
import io

import httpx
import pandas as pd

from futedata.collectors.base import BaseCollector, CollectionResult
from futedata.constants import DataSource, TARGET_COMPETITIONS_TM
from futedata.utils.io import compute_schema_hash, write_csv
from futedata.utils.logging import get_logger

logger = get_logger(__name__)

BASE_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"

DATASETS = [
    "competitions",
    "clubs",
    "players",
    "transfers",
    "player_valuations",
    "appearances",
    "games",
    "game_lineups",
]

# Competições importadas de constants.py


class TransfermarktCollector(BaseCollector):

    source = DataSource.TRANSFERMARKT

    def __init__(self, filter_brasileirao: bool = True) -> None:
        super().__init__()
        self.filter_brasileirao = filter_brasileirao
        self.client = httpx.Client(timeout=120.0)

    def _download_csv(self, name: str) -> pd.DataFrame:
        url = f"{BASE_URL}/{name}.csv.gz"
        logger.info("downloading_dataset", name=name, url=url)

        response = self.client.get(url)
        response.raise_for_status()

        decompressed = gzip.decompress(response.content)
        df = pd.read_csv(io.BytesIO(decompressed), low_memory=False)

        logger.info("dataset_downloaded", name=name, rows=len(df), columns=len(df.columns))
        return df

    def _filter_brazilian(self, df: pd.DataFrame, name: str) -> pd.DataFrame:
        if not self.filter_brasileirao:
            return df

        original_len = len(df)

        if name == "competitions":
            df = df[df["competition_id"].isin(TARGET_COMPETITIONS_TM)]

        elif name == "clubs":
            df = df[df["domestic_competition_id"].isin(TARGET_COMPETITIONS_TM)]

        elif name == "players":
            if hasattr(self, "_club_ids"):
                df = df[df["current_club_id"].isin(self._club_ids)]

        elif name == "transfers":
            if hasattr(self, "_club_ids"):
                df = df[
                    df["from_club_id"].isin(self._club_ids)
                    | df["to_club_id"].isin(self._club_ids)
                ]

        elif name == "player_valuations":
            if hasattr(self, "_player_ids"):
                df = df[df["player_id"].isin(self._player_ids)]

        elif name == "appearances":
            if hasattr(self, "_player_ids"):
                df = df[df["player_id"].isin(self._player_ids)]

        elif name == "games":
            if hasattr(self, "_club_ids"):
                df = df[
                    df["home_club_id"].isin(self._club_ids)
                    | df["away_club_id"].isin(self._club_ids)
                ]

        elif name == "game_lineups":
            if hasattr(self, "_club_ids"):
                df = df[df["club_id"].isin(self._club_ids)]

        logger.info("filtered_brazilian", name=name, before=original_len, after=len(df))
        return df

    def collect(self) -> list[CollectionResult]:
        results: list[CollectionResult] = []

        for name in DATASETS:
            try:
                df = self._download_csv(name)
                df = self._filter_brazilian(df, name)

                if name == "clubs":
                    self._club_ids = set(df["club_id"].dropna().unique())
                elif name == "players":
                    self._player_ids = set(df["player_id"].dropna().unique())

                schema_hash = compute_schema_hash(df)

                results.append(CollectionResult(
                    data=df,
                    rows=len(df),
                    endpoint=name,
                    schema_hash=schema_hash,
                    metadata={"columns": list(df.columns)},
                ))
            except Exception as e:
                logger.error("dataset_failed", name=name, error=str(e))

        return results

    def save_raw(self, result: CollectionResult, filename: str | None = None) -> None:
        endpoint_dir = self.raw_dir / result.endpoint
        endpoint_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            filename = f"{result.endpoint}.csv"

        output_path = endpoint_dir / filename
        write_csv(result.data, output_path)

        logger.info(
            "raw_data_saved",
            source=self.source.value,
            endpoint=result.endpoint,
            path=str(output_path),
            rows=result.rows,
        )

    def close(self) -> None:
        self.client.close()
