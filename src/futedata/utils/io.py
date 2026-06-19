import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import xxhash
import boto3

from futedata.utils.logging import get_logger
from futedata.config import settings

logger = get_logger(__name__)

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def utcnow_iso() -> str:
    return utcnow().isoformat()

def _get_s3_key(path: Path) -> str:
    """Calcula a chave (caminho relativo) do S3 para manter a estrutura."""
    try:
        rel_path = path.relative_to(settings.data_dir)
    except ValueError:
        rel_path = path.name
    return str(rel_path).replace("\\", "/")

def write_json(data: Any, path: Path, *, indent: int = 2) -> Path:
    if settings.use_s3:
        s3 = boto3.client("s3")
        s3_key = _get_s3_key(path)
        # Assumindo que dados em raw vao pro s3_raw_bucket
        bucket = settings.s3_raw_bucket
        if "audit" in str(path):
            bucket = settings.s3_audit_bucket
            
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=json.dumps(data, ensure_ascii=False, indent=indent, default=str),
            ContentType="application/json"
        )
        logger.debug("json_written_to_s3", bucket=bucket, key=s3_key)
        # Não damos return aqui para que o código continue e grave o arquivo localmente

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
    if settings.use_s3:
        bucket = settings.s3_raw_bucket
        s3_key = _get_s3_key(path)
        return pd.read_csv(f"s3://{bucket}/{s3_key}", storage_options={"anon": False}, **kwargs)
    return pd.read_csv(path, **kwargs)


def write_csv(df: pd.DataFrame, path: Path, **kwargs: Any) -> Path:
    if settings.use_s3:
        bucket = settings.s3_raw_bucket
        s3_key = _get_s3_key(path)
        s3_path = f"s3://{bucket}/{s3_key}"
        df.to_csv(s3_path, index=False, storage_options={"anon": False}, **kwargs)
        logger.debug("csv_written_to_s3", bucket=bucket, key=s3_key, rows=len(df))
        # Sem return para continuar e gravar no disco

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
    if settings.use_s3:
        bucket = settings.s3_raw_bucket
        s3_key = _get_s3_key(path)
        s3_path = f"s3://{bucket}/{s3_key}"
        df.to_parquet(s3_path, index=False, engine="pyarrow", storage_options={"anon": False}, **kwargs)
        logger.debug("parquet_written_to_s3", bucket=bucket, key=s3_key, rows=len(df))
        # Sem return para continuar e gravar no disco

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
    if settings.use_s3:
        bucket = settings.s3_raw_bucket
        s3_key = _get_s3_key(path)
        return pd.read_parquet(f"s3://{bucket}/{s3_key}", engine="pyarrow", storage_options={"anon": False}, **kwargs)
    return pd.read_parquet(path, engine="pyarrow", **kwargs)


def compute_schema_hash(df: pd.DataFrame) -> str:
    schema_str = "|".join(f"{col}:{dtype}" for col, dtype in zip(df.columns, df.dtypes))
    return xxhash.xxh64(schema_str.encode()).hexdigest()


def compute_content_hash(data: bytes) -> str:
    return xxhash.xxh64(data).hexdigest()
