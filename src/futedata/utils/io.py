"""
I/O utilities for FuteData.

Handles JSON/CSV/Parquet read/write with consistent conventions:
- All writes are atomic (write to temp, then rename).
- All timestamps use ISO 8601 UTC.
- Schema hashes use xxhash for fast, deterministic fingerprinting.
"""

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import xxhash

from futedata.utils.logging import get_logger

logger = get_logger(__name__)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    """Return current UTC datetime as ISO 8601 string."""
    return utcnow().isoformat()


# ============================================================
# JSON I/O
# ============================================================

def read_json(path: Path) -> Any:
    """Read a JSON file and return its content."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(data: Any, path: Path, *, indent: int = 2) -> Path:
    """
    Write data to a JSON file atomically.

    Writes to a temp file first, then renames — prevents partial writes
    from corrupting data if the process is interrupted.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=".json.tmp",
        dir=str(path.parent),
    )
    try:
        with open(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        shutil.move(tmp_path, str(path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    logger.debug("json_written", path=str(path), size_bytes=path.stat().st_size)
    return path


# ============================================================
# CSV I/O
# ============================================================

def read_csv(path: Path, **kwargs: Any) -> pd.DataFrame:
    """Read a CSV file into a pandas DataFrame."""
    return pd.read_csv(path, **kwargs)


def write_csv(df: pd.DataFrame, path: Path, **kwargs: Any) -> Path:
    """Write a DataFrame to CSV atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=".csv.tmp",
        dir=str(path.parent),
    )
    try:
        df.to_csv(tmp_path, index=False, **kwargs)
        shutil.move(tmp_path, str(path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    logger.debug("csv_written", path=str(path), rows=len(df))
    return path


# ============================================================
# Parquet I/O
# ============================================================

def write_parquet(df: pd.DataFrame, path: Path, **kwargs: Any) -> Path:
    """Write a DataFrame to Parquet atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=".parquet.tmp",
        dir=str(path.parent),
    )
    try:
        df.to_parquet(tmp_path, index=False, engine="pyarrow", **kwargs)
        shutil.move(tmp_path, str(path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    logger.debug("parquet_written", path=str(path), rows=len(df))
    return path


def read_parquet(path: Path, **kwargs: Any) -> pd.DataFrame:
    """Read a Parquet file into a pandas DataFrame."""
    return pd.read_parquet(path, engine="pyarrow", **kwargs)


# ============================================================
# Schema Hashing
# ============================================================

def compute_schema_hash(df: pd.DataFrame) -> str:
    """
    Compute a deterministic hash of a DataFrame's schema (column names + dtypes).

    Used to detect schema drift between ingestion runs.
    """
    schema_str = "|".join(f"{col}:{dtype}" for col, dtype in zip(df.columns, df.dtypes))
    return xxhash.xxh64(schema_str.encode()).hexdigest()


def compute_content_hash(data: bytes) -> str:
    """Compute a fast hash of raw content bytes."""
    return xxhash.xxh64(data).hexdigest()
