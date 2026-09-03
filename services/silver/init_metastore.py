import os
import logging

from services.silver.silver_job import create_spark_session_minio

logger = logging.getLogger(__name__)

SILVER_TABLES = {
    "offres": "s3a://lakehouse/silver/offres",
}

def init_silver_database(spark):
    spark.sql("CREATE DATABASE IF NOT EXISTS silver")
    logger.info("Database 'silver' prête")

def register_silver_table(spark, table_name: str, location:str):
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS silver.{table_name}
        USING DELTA
        LOCATION '{location}'
    """)
    logger.info(f"Table silver.{table_name} enregistrée -> {location}")

def main():
    spark = create_spark_session_minio(
        os.getenv("SPARK_MASTER_URL"),
        os.getenv("MINIO_ENDPOINT"),
        os.getenv("MINIO_ACCESS_KEY"),
        os.getenv("MINIO_SECRET_KEY"),
    )

    init_silver_database(spark)

    for table_name, location in SILVER_TABLES.items():
        register_silver_table(spark, table_name, location)

    spark.sql("SHOW TABLES IN silver").show()
    spark.stop()

if __name__ == "__main__":
    main()
