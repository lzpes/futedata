import logging
from pyspark.sql import SparkSession
from futedata.config import settings

import os
import sys
from delta import configure_spark_with_delta_pip

logger = logging.getLogger(__name__)

def get_spark_session(app_name: str = "FuteDataLakehouse") -> SparkSession:
    """
    Inicia uma SparkSession local configurada para suportar o formato Delta Lake.
    """
    logger.info(f"Initializing PySpark Session with Delta Lake: {app_name}")
    
    # Se estiver rodando dentro de um Cluster Databricks (Serverless ou DBR), a sessão já existe
    active_session = SparkSession.getActiveSession()
    if active_session:
        logger.info("Found active SparkSession. Using it.")
        return active_session
        
    if "DATABRICKS_RUNTIME_VERSION" in os.environ or "DATABRICKS_WORKSPACE_ID" in os.environ:
        logger.info("Running inside Databricks. Using native SparkSession.builder.")
        return SparkSession.builder.getOrCreate()

    # Workaround para Windows local: Forçar IPv4 e Python do .venv
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
    
    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.driver.memory", "4g")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
    )
    
    return configure_spark_with_delta_pip(builder).getOrCreate()
