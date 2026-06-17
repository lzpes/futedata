import uuid
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from futedata.config import settings
from futedata.constants import DataSource
from futedata.utils.io import utcnow_iso, write_json
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CollectionResult:
    data: Any
    rows: int
    endpoint: str
    schema_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEntry:
    ingestion_id: str
    source: str
    endpoint: str
    execution_timestamp: str
    rows_fetched: int
    rows_written: int
    status: str
    schema_hash: str
    error_message: str | None = None
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ingestion_id": self.ingestion_id,
            "source": self.source,
            "endpoint": self.endpoint,
            "execution_timestamp": self.execution_timestamp,
            "rows_fetched": self.rows_fetched,
            "rows_written": self.rows_written,
            "status": self.status,
            "schema_hash": self.schema_hash,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            **self.metadata,
        }


class BaseCollector(ABC):

    source: DataSource

    def __init__(self) -> None:
        settings.ensure_dirs()
        self.raw_dir = settings.raw_dir / self.source.value
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir = settings.audit_dir
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def collect(self) -> list[CollectionResult]:
        ...

    def save_raw(self, result: CollectionResult, filename: str | None = None) -> Path:
        endpoint_dir = self.raw_dir / result.endpoint
        endpoint_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            timestamp = utcnow_iso().replace(":", "-")
            filename = f"{result.endpoint}_{timestamp}.json"

        output_path = endpoint_dir / filename
        write_json(result.data, output_path)

        logger.info(
            "raw_data_saved",
            source=self.source.value,
            endpoint=result.endpoint,
            path=str(output_path),
            rows=result.rows,
        )
        return output_path

    def log_audit(self, entry: AuditEntry) -> Path:
        log_path = self.audit_dir / "source_audit_log.json"

        existing: list[dict[str, Any]] = []
        if log_path.exists():
            import json
            with open(log_path, encoding="utf-8") as f:
                existing = json.load(f)

        existing.append(entry.to_dict())
        write_json(existing, log_path)

        logger.info(
            "audit_logged",
            source=entry.source,
            endpoint=entry.endpoint,
            status=entry.status,
            rows_fetched=entry.rows_fetched,
        )
        return log_path

    def run(self) -> list[AuditEntry]:
        logger.info("collection_started", source=self.source.value)
        audit_entries: list[AuditEntry] = []

        try:
            results = self.collect()
        except Exception as e:
            entry = AuditEntry(
                ingestion_id=str(uuid.uuid4()),
                source=self.source.value,
                endpoint="*",
                execution_timestamp=utcnow_iso(),
                rows_fetched=0,
                rows_written=0,
                status="error",
                schema_hash="",
                error_message=str(e),
            )
            self.log_audit(entry)
            logger.error("collection_failed", source=self.source.value, error=str(e))
            return [entry]

        for result in results:
            start_time = time.monotonic()
            ingestion_id = str(uuid.uuid4())

            try:
                self.save_raw(result)
                duration = time.monotonic() - start_time

                entry = AuditEntry(
                    ingestion_id=ingestion_id,
                    source=self.source.value,
                    endpoint=result.endpoint,
                    execution_timestamp=utcnow_iso(),
                    rows_fetched=result.rows,
                    rows_written=result.rows,
                    status="success",
                    schema_hash=result.schema_hash,
                    duration_seconds=round(duration, 3),
                    metadata=result.metadata,
                )
            except Exception as e:
                duration = time.monotonic() - start_time
                entry = AuditEntry(
                    ingestion_id=ingestion_id,
                    source=self.source.value,
                    endpoint=result.endpoint,
                    execution_timestamp=utcnow_iso(),
                    rows_fetched=result.rows,
                    rows_written=0,
                    status="error",
                    schema_hash=result.schema_hash,
                    error_message=str(e),
                    duration_seconds=round(duration, 3),
                )
                logger.error(
                    "save_failed",
                    source=self.source.value,
                    endpoint=result.endpoint,
                    error=str(e),
                )

            self.log_audit(entry)
            audit_entries.append(entry)

        success_count = sum(1 for e in audit_entries if e.status == "success")
        total_rows = sum(e.rows_fetched for e in audit_entries)
        logger.info(
            "collection_completed",
            source=self.source.value,
            endpoints_ok=success_count,
            endpoints_total=len(audit_entries),
            total_rows=total_rows,
        )

        return audit_entries
