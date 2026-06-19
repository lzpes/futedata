from pathlib import Path
from typing import Any
import pandas as pd
import json

from futedata.config import settings
from futedata.constants import DataSource
from futedata.utils.logging import get_logger

logger = get_logger(__name__)


class RawValidator:
    """
    Valida a integridade básica dos arquivos brutos coletados
    antes de promovê-los para a camada 'validated'.
    """

    def __init__(self) -> None:
        self.settings = settings
        self.raw_dir = Path(self.settings.data_dir) / "raw"
        self.val_dir = Path(self.settings.data_dir) / "validated"

    def run(self) -> dict[str, Any]:
        logger.info("validation_started")
        if self.settings.use_s3:
            logger.info("using_s3_validation", bucket=self.settings.s3_raw_bucket)
            results = {
                "transfermarkt": self._validate_s3_transfermarkt(),
                "football_data": self._validate_s3_football_data(),
            }
        else:
            results = {
                "transfermarkt": self._validate_transfermarkt(),
                "football_data": self._validate_football_data(),
            }
        logger.info("validation_completed", results=results)
        return results

    def _validate_s3_transfermarkt(self) -> dict[str, Any]:
        import boto3
        s3 = boto3.client("s3")
        bucket = self.settings.s3_raw_bucket
        prefix = f"raw/{DataSource.TRANSFERMARKT.value}/"
        
        valid_files = 0
        failed_files = 0
        
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                if obj['Key'].endswith('.csv'):
                    try:
                        s3_path = f"s3://{bucket}/{obj['Key']}"
                        df = pd.read_csv(s3_path, low_memory=False, storage_options={"anon": False})
                        if df.empty:
                            logger.warning("empty_csv_s3", file=obj['Key'])
                            failed_files += 1
                        else:
                            self._promote_file_s3(obj['Key'])
                            valid_files += 1
                    except Exception as e:
                        logger.error("csv_s3_validation_failed", file=obj['Key'], error=str(e))
                        failed_files += 1

        return {"valid": valid_files, "failed": failed_files}

    def _validate_s3_football_data(self) -> dict[str, Any]:
        import boto3
        s3 = boto3.client("s3")
        bucket = self.settings.s3_raw_bucket
        prefix = f"raw/{DataSource.FOOTBALL_DATA.value}/"
        
        valid_files = 0
        failed_files = 0
        
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                if obj['Key'].endswith('.json'):
                    try:
                        resp = s3.get_object(Bucket=bucket, Key=obj['Key'])
                        data = json.loads(resp['Body'].read().decode('utf-8'))
                        if not data:
                            logger.warning("empty_json_s3", file=obj['Key'])
                            failed_files += 1
                        else:
                            self._promote_file_s3(obj['Key'])
                            valid_files += 1
                    except Exception as e:
                        logger.error("json_s3_validation_failed", file=obj['Key'], error=str(e))
                        failed_files += 1

        return {"valid": valid_files, "failed": failed_files}

    def _promote_file_s3(self, src_key: str) -> None:
        """Copia o objeto do bucket raw para o bucket validated."""
        import boto3
        s3 = boto3.client("s3")
        
        target_bucket = self.settings.s3_validated_bucket
        
        # Copia mantendo a estrutura da chave
        copy_source = {'Bucket': self.settings.s3_raw_bucket, 'Key': src_key}
        s3.copy_object(CopySource=copy_source, Bucket=target_bucket, Key=src_key)
        logger.debug("file_promoted_s3", src=src_key, target_bucket=target_bucket)

    def _validate_transfermarkt(self) -> dict[str, Any]:
        tm_dir = self.raw_dir / DataSource.TRANSFERMARKT.value
        if not tm_dir.exists():
            return {"status": "skipped", "reason": "dir_not_found"}

        valid_files = 0
        failed_files = 0

        for file_path in tm_dir.rglob("*.csv"):
            try:
                df = pd.read_csv(file_path, low_memory=False)
                if df.empty:
                    logger.warning("empty_csv", file=file_path.name)
                    failed_files += 1
                else:
                    self._promote_file(file_path, DataSource.TRANSFERMARKT.value)
                    valid_files += 1
            except Exception as e:
                logger.error("csv_validation_failed", file=file_path.name, error=str(e))
                failed_files += 1

        return {"valid": valid_files, "failed": failed_files}

    def _validate_football_data(self) -> dict[str, Any]:
        fd_dir = self.raw_dir / DataSource.FOOTBALL_DATA.value
        if not fd_dir.exists():
            return {"status": "skipped", "reason": "dir_not_found"}

        valid_files = 0
        failed_files = 0

        for file_path in fd_dir.rglob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Check basic payload
                if not data:
                    logger.warning("empty_json", file=file_path.name)
                    failed_files += 1
                else:
                    self._promote_file(file_path, DataSource.FOOTBALL_DATA.value)
                    valid_files += 1
            except Exception as e:
                logger.error("json_validation_failed", file=file_path.name, error=str(e))
                failed_files += 1

        return {"valid": valid_files, "failed": failed_files}

    def _promote_file(self, src_path: Path, source_name: str) -> None:
        """Copia o arquivo validado para a camada 'validated'."""
        import shutil
        
        target_dir = self.val_dir / source_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = target_dir / src_path.name
        shutil.copy2(src_path, target_path)
        logger.debug("file_promoted", src=src_path.name, target=str(target_path))
