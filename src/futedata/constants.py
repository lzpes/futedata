from enum import StrEnum


FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
TRANSFERMARKT_KAGGLE_DATASET = "davidcariboo/player-scores"

BRASILEIRAO_CODE = "BSA"
BRASILEIRAO_COMPETITION_ID = 2013


class DataSource(StrEnum):
    FOOTBALL_DATA = "football_data"
    TRANSFERMARKT = "transfermarkt"


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


class ValidationSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"


FOOTBALL_DATA_RATE_LIMIT_PER_MINUTE = 10
FOOTBALL_DATA_REQUEST_INTERVAL_SECONDS = 6.5
