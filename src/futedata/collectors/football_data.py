import time

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from futedata.collectors.base import BaseCollector, CollectionResult
from futedata.constants import (
    TARGET_COMPETITIONS_FD,
    DataSource,
    FOOTBALL_DATA_BASE_URL,
    FOOTBALL_DATA_REQUEST_INTERVAL_SECONDS,
)
from futedata.config import settings
from futedata.utils.io import compute_content_hash
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


class FootballDataCollector(BaseCollector):

    source = DataSource.FOOTBALL_DATA

    def __init__(self) -> None:
        super().__init__()
        if not settings.football_data_api_key:
            raise ValueError("FOOTBALL_DATA_API_KEY not set in .env")

        self.client = httpx.Client(
            base_url=FOOTBALL_DATA_BASE_URL,
            headers={"X-Auth-Token": settings.football_data_api_key},
            timeout=30.0,
        )

    def _rate_limit(self) -> None:
        time.sleep(FOOTBALL_DATA_REQUEST_INTERVAL_SECONDS)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    def _get(self, endpoint: str) -> dict:
        response = self.client.get(endpoint)
        response.raise_for_status()
        return response.json()

    def _collect_competition(self) -> CollectionResult:
        all_comps = []
        for code in TARGET_COMPETITIONS_FD:
            data = self._get(f"/competitions/{code}")
            all_comps.append(data)
            self._rate_limit()
        return CollectionResult(
            data={"competitions": all_comps},
            rows=len(all_comps),
            endpoint="competition",
            schema_hash=compute_content_hash(str(all_comps).encode()),
        )

    def _collect_matches(self) -> CollectionResult:
        all_matches = []
        for code in TARGET_COMPETITIONS_FD:
            data = self._get(f"/competitions/{code}/matches")
            all_matches.extend(data.get("matches", []))
            self._rate_limit()
        return CollectionResult(
            data={"matches": all_matches},
            rows=len(all_matches),
            endpoint="matches",
            schema_hash=compute_content_hash(str(all_matches).encode()),
        )

    def _collect_standings(self) -> CollectionResult:
        all_standings = []
        for code in TARGET_COMPETITIONS_FD:
            data = self._get(f"/competitions/{code}/standings")
            all_standings.extend(data.get("standings", []))
            self._rate_limit()
        return CollectionResult(
            data={"standings": all_standings},
            rows=len(all_standings),
            endpoint="standings",
            schema_hash=compute_content_hash(str(all_standings).encode()),
        )

    def _collect_teams(self) -> CollectionResult:
        all_teams = []
        for code in TARGET_COMPETITIONS_FD:
            data = self._get(f"/competitions/{code}/teams")
            all_teams.extend(data.get("teams", []))
            self._rate_limit()
        return CollectionResult(
            data={"teams": all_teams},
            rows=len(all_teams),
            endpoint="teams",
            schema_hash=compute_content_hash(str(all_teams).encode()),
        )

    def _collect_scorers(self) -> CollectionResult:
        all_scorers = []
        for code in TARGET_COMPETITIONS_FD:
            data = self._get(f"/competitions/{code}/scorers")
            all_scorers.extend(data.get("scorers", []))
            self._rate_limit()
        return CollectionResult(
            data={"scorers": all_scorers},
            rows=len(all_scorers),
            endpoint="scorers",
            schema_hash=compute_content_hash(str(all_scorers).encode()),
        )

    def collect(self) -> list[CollectionResult]:
        results: list[CollectionResult] = []

        steps = [
            ("competition", self._collect_competition),
            ("matches", self._collect_matches),
            ("standings", self._collect_standings),
            ("teams", self._collect_teams),
            ("scorers", self._collect_scorers),
        ]

        for name, fn in steps:
            logger.info("fetching_endpoint", endpoint=name, source="football_data")
            try:
                result = fn()
                results.append(result)
                logger.info("endpoint_fetched", endpoint=name, rows=result.rows)
            except Exception as e:
                logger.error("endpoint_failed", endpoint=name, error=str(e))

        return results

    def save_raw(self, result: CollectionResult, filename: str | None = None) -> None:
        if filename is None:
            filename = f"{result.endpoint}.json"
        super().save_raw(result, filename)

    def close(self) -> None:
        self.client.close()
