import json
import os
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
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    return utcnow().isoformat()


def write_json(data: Any, path: Path, *, indent: int = 2) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=".json.tmp",
        dir=str(path.parent),
    )
    os.close(tmp_fd)
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        shutil.move(tmp_path, str(path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    logger.debug("json_written", path=str(path), size_bytes=path.stat().st_size)
    return path


def read_csv(path: Path, **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(path, **kwargs)


def write_csv(df: pd.DataFrame, path: Path, **kwargs: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=".csv.tmp",
        dir=str(path.parent),
    )
    os.close(tmp_fd)
    try:
        df.to_csv(tmp_path, index=False, **kwargs)
        shutil.move(tmp_path, str(path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    logger.debug("csv_written", path=str(path), rows=len(df))
    return path


def write_parquet(df: pd.DataFrame, path: Path, **kwargs: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=".parquet.tmp",
        dir=str(path.parent),
    )
    os.close(tmp_fd)
    try:
        df.to_parquet(tmp_path, index=False, engine="pyarrow", **kwargs)
        shutil.move(tmp_path, str(path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    logger.debug("parquet_written", path=str(path), rows=len(df))
    return path


def read_parquet(path: Path, **kwargs: Any) -> pd.DataFrame:
    return pd.read_parquet(path, engine="pyarrow", **kwargs)


def compute_schema_hash(df: pd.DataFrame) -> str:
    schema_str = "|".join(f"{col}:{dtype}" for col, dtype in zip(df.columns, df.dtypes))
    return xxhash.xxh64(schema_str.encode()).hexdigest()


def compute_content_hash(data: bytes) -> str:
    return xxhash.xxh64(data).hexdigest()
