import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from futedata.collectors.base import BaseCollector, CollectionResult
from futedata.constants import DataSource, STATSBOMB_BASE_URL, STATSBOMB_PRIORITY_COMPETITIONS
from futedata.utils.io import compute_content_hash
from futedata.utils.logging import get_logger

logger = get_logger(__name__)

MAX_MATCHES_TO_FETCH_EVENTS = 50


class StatsBombCollector(BaseCollector):

    source = DataSource.STATSBOMB

    def __init__(self, max_events: int = MAX_MATCHES_TO_FETCH_EVENTS) -> None:
        super().__init__()
        self.max_events = max_events
        self.client = httpx.Client(timeout=30.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _get_json(self, url: str) -> list | dict:
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()

    def _collect_competitions(self) -> CollectionResult:
        url = f"{STATSBOMB_BASE_URL}/competitions.json"
        data = self._get_json(url)

        return CollectionResult(
            data=data,
            rows=len(data),
            endpoint="competitions",
            schema_hash=compute_content_hash(str(data).encode()),
        )

    def _collect_matches(self, competition_id: int, season_id: int) -> CollectionResult:
        url = f"{STATSBOMB_BASE_URL}/matches/{competition_id}/{season_id}.json"
        data = self._get_json(url)

        return CollectionResult(
            data=data,
            rows=len(data),
            endpoint=f"matches/{competition_id}/{season_id}",
            schema_hash=compute_content_hash(str(data).encode()),
            metadata={"competition_id": competition_id, "season_id": season_id},
        )

    def _collect_events(self, match_id: int) -> CollectionResult:
        url = f"{STATSBOMB_BASE_URL}/events/{match_id}.json"
        data = self._get_json(url)

        return CollectionResult(
            data=data,
            rows=len(data),
            endpoint=f"events",
            schema_hash=compute_content_hash(str(data).encode()),
            metadata={"match_id": match_id},
        )

    def _collect_lineups(self, match_id: int) -> CollectionResult:
        url = f"{STATSBOMB_BASE_URL}/lineups/{match_id}.json"
        data = self._get_json(url)

        return CollectionResult(
            data=data,
            rows=len(data),
            endpoint=f"lineups",
            schema_hash=compute_content_hash(str(data).encode()),
            metadata={"match_id": match_id},
        )

    def collect(self) -> list[CollectionResult]:
        results: list[CollectionResult] = []

        logger.info("fetching_competitions")
        competitions = self._collect_competitions()
        results.append(competitions)

        priority_ids = set(STATSBOMB_PRIORITY_COMPETITIONS.keys())
        available_seasons: list[dict] = []
        for comp in competitions.data:
            if comp.get("competition_id") in priority_ids:
                available_seasons.append(comp)

        logger.info("priority_seasons_found", count=len(available_seasons))

        all_match_ids: list[int] = []
        for season in available_seasons[:5]:
            comp_id = season["competition_id"]
            season_id = season["season_id"]
            comp_name = season.get("competition_name", comp_id)
            season_name = season.get("season_name", season_id)

            logger.info("fetching_matches", competition=comp_name, season=season_name)
            try:
                match_result = self._collect_matches(comp_id, season_id)
                results.append(match_result)

                for match in match_result.data:
                    all_match_ids.append(match["match_id"])
            except Exception as e:
                logger.warning("matches_fetch_failed", competition=comp_name, error=str(e))

        matches_to_fetch = all_match_ids[:self.max_events]
        logger.info("fetching_events_and_lineups", total_matches=len(matches_to_fetch))

        for match_id in matches_to_fetch:
            try:
                events = self._collect_events(match_id)
                results.append(events)
            except Exception as e:
                logger.warning("events_fetch_failed", match_id=match_id, error=str(e))

            try:
                lineups = self._collect_lineups(match_id)
                results.append(lineups)
            except Exception as e:
                logger.warning("lineups_fetch_failed", match_id=match_id, error=str(e))

        return results

    def save_raw(self, result: CollectionResult, filename: str | None = None) -> None:
        if filename is None:
            match_id = result.metadata.get("match_id")
            comp_id = result.metadata.get("competition_id")
            season_id = result.metadata.get("season_id")

            if match_id:
                filename = f"{match_id}.json"
            elif comp_id and season_id:
                filename = f"{comp_id}_{season_id}.json"
            else:
                filename = f"{result.endpoint}.json"

        super().save_raw(result, filename)

    def close(self) -> None:
        self.client.close()
