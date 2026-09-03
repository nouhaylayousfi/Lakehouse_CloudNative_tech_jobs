import logging
import os
from dotenv import load_dotenv
from pyspark.conf import SparkConf
from pyspark.sql import SparkSession
import argparse
import json

from services.silver.schema import build_silver_schema
from services.silver.dedup import deduplicate, deduplicate_cross_source
from services.silver.dates import normalize_dates
from services.silver.skills import extract_and_normalize_skills
from services.silver.salaire import apply_salaire_parsing
from services.silver.parsers import apply_experience_parsing, apply_education_parsing
from services.silver.contrat import normalize_type_contrat
from services.silver.entreprise import clean_entreprise
from services.silver.data_quality import validate_silver
from services.silver.silver_writer import write_to_silver

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
load_dotenv()

def create_spark_session_minio(spark_master_url , s3_url ,s3_access_key ,s3_secret_key):
    conf = SparkConf()
    conf.set('spark.hadoop.fs.s3a.endpoint', s3_url)
    conf.set('spark.hadoop.fs.s3a.access.key', s3_access_key)
    conf.set('spark.hadoop.fs.s3a.secret.key', s3_secret_key)
    conf.set('spark.hadoop.fs.s3a.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem')
    conf.set('spark.hadoop.fs.s3a.path.style.access', 'true')

    PROJECT_JARS_DIR = os.getenv("PROJECT_JARS_DIR", "/opt/spark/project/jars") 

    conf.set('spark.jars', ",".join([
        f"{PROJECT_JARS_DIR}/hadoop-aws-3.3.4.jar",
        f"{PROJECT_JARS_DIR}/aws-java-sdk-bundle-1.12.262.jar",
        f"{PROJECT_JARS_DIR}/delta-spark_2.12-3.2.0.jar",
        f"{PROJECT_JARS_DIR}/delta-storage-3.2.0.jar",
    ]))

    conf.set('spark.executorEnv.PYTHONPATH', '/opt/spark/project')

    conf.set('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension')
    conf.set('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog')
    conf.set('hive.metastore.uris', 'thrift://hive-metastore:9083')
    spark = (
        SparkSession.builder
        .appName("tech project")
        .master(spark_master_url)
        .config(conf=conf)
        .enableHiveSupport()
        .getOrCreate()
    )
    return spark

# Read data from bronze layer
def read_data_from_bronze(spark: SparkSession ):
    """Read the entire Bronze history — used only for backfilling."""
    return (
        spark.read
            .option("multiline", "true")
            .json("s3a://lakehouse/bronze/*/*.json")
    )

def read_new_bronze_files(spark: SparkSession, bronze_keys: list[str]):
    """Reads only the explicitly specified past Bronze files — used in incremental mode."""
    bucket = os.getenv("MINIO_BRONZE_BUCKET")
    paths = [f"s3a://{bucket}/{key}" for key in bronze_keys]
    return spark.read.option("multiline", "true").json(paths)

def run_silver_job(df):
    df = build_silver_schema(df)
    df = deduplicate(df)
    df = deduplicate_cross_source(df)
    df = normalize_dates(df)
    df = extract_and_normalize_skills(df)
    df = apply_salaire_parsing(df)
    df = apply_experience_parsing(df)
    df = apply_education_parsing(df)
    df = normalize_type_contrat(df)
    df = clean_entreprise(df)

    validate_silver(df)

    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bronze_keys", type=str, default=None,
                         help="JSON list of Bronze keys to process incrementally")
    parser.add_argument("--backfill", action="store_true",
                         help="Process the entire Bronze history instead of new files only")
    args = parser.parse_args()

    spark = create_spark_session_minio(
        os.getenv('SPARK_MASTER_URL'),
        os.getenv('MINIO_ENDPOINT'),
        os.getenv('MINIO_ACCESS_KEY'),
        os.getenv('MINIO_SECRET_KEY'),
    )

    if args.backfill:
        logger.info("Running FULL BACKFILL — reading entire Bronze history")
        df_bronze = read_data_from_bronze(spark)
        write_mode = "overwrite"
    else:
        bronze_keys = json.loads(args.bronze_keys) if args.bronze_keys else []
        if not bronze_keys:
            logger.warning("No new Bronze files to process - skipping Silver run")
            exit(0)
        logger.info("Running INCREMENTAL — %d new Bronze file(s)", len(bronze_keys))
        df_bronze = read_new_bronze_files(spark, bronze_keys)
        write_mode = "append"

    df_silver = run_silver_job(df_bronze)
    df_silver.printSchema()

    path = write_to_silver(df_silver, source="offres", mode=write_mode)
    logger.info("Silver written to %s (mode=%s)", path, write_mode)