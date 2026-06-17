"""
Project-wide constants for FuteData.

Centralizes magic values: API URLs, competition codes, file paths, and domain constants.
"""

from enum import StrEnum


# ============================================================
# API Base URLs
# ============================================================

STATSBOMB_BASE_URL = (
    "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
)
FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"

TRANSFERMARKT_KAGGLE_DATASET = "davidcariboo/player-scores"


# ============================================================
# football-data.org — Free Tier Competition Codes
# ============================================================

class CompetitionCode(StrEnum):
    """Competition codes available on football-data.org free tier."""

    CHAMPIONS_LEAGUE = "CL"
    PREMIER_LEAGUE = "PL"
    LA_LIGA = "PD"
    BUNDESLIGA = "BL1"
    SERIE_A = "SA"
    LIGUE_1 = "FL1"
    EREDIVISIE = "DED"
    PRIMEIRA_LIGA = "PPL"
    CHAMPIONSHIP = "ELC"
    BRASILEIRAO = "BSA"
    WORLD_CUP = "WC"
    EURO = "EC"


FREE_TIER_COMPETITIONS: list[str] = [code.value for code in CompetitionCode]


# ============================================================
# StatsBomb — Known Competition/Season IDs with Events Data
# ============================================================

STATSBOMB_PRIORITY_COMPETITIONS: dict[int, str] = {
    11: "La Liga",
    2:  "Premier League",
    16: "Champions League",
    43: "FIFA World Cup",
    3:  "Champions League (Women)",
    37: "FA Women's Super League",
    72: "Women's World Cup",
    49: "NWSL",
    55: "Euro",
    9:  "Bundesliga",
    12: "Serie A",
    7:  "Ligue 1",
}


# ============================================================
# Data Source Identifiers (used in audit logs and tags)
# ============================================================

class DataSource(StrEnum):
    """Identifiers for each data source — used in audit logs and lineage tags."""

    STATSBOMB = "statsbomb"
    FOOTBALL_DATA = "football_data"
    TRANSFERMARKT = "transfermarkt"
    API_FOOTBALL = "api_football"
    WIKIDATA = "wikidata"


# ============================================================
# Player Positions Domain (controlled vocabulary)
# ============================================================

VALID_POSITIONS: set[str] = {
    "Goalkeeper",
    "Right Back", "Right Wing Back", "Right Center Back",
    "Center Back", "Left Center Back",
    "Left Back", "Left Wing Back",
    "Right Defensive Midfield", "Center Defensive Midfield", "Left Defensive Midfield",
    "Right Midfield", "Right Center Midfield", "Center Midfield",
    "Left Center Midfield", "Left Midfield",
    "Right Attacking Midfield", "Center Attacking Midfield", "Left Attacking Midfield",
    "Right Wing", "Left Wing",
    "Right Center Forward", "Striker", "Left Center Forward",
    "Center Forward",
    "Secondary Striker",
}


# ============================================================
# Validation Severity Levels
# ============================================================

class ValidationSeverity(StrEnum):
    """Severity levels for data validation rules."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"


# ============================================================
# Rate Limiting
# ============================================================

FOOTBALL_DATA_RATE_LIMIT_PER_MINUTE = 10
FOOTBALL_DATA_REQUEST_INTERVAL_SECONDS = 6.5  # ~10 req/min with margin

API_FOOTBALL_DAILY_LIMIT_FREE = 100
