from __future__ import annotations
import os 
import logging 
from datetime import datetime
from airflow.sdk import dag , task 
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

logger = logging.getLogger(__name__)


@dag(
    dag_id="scrape_jobs",
    schedule="0 8 * * *",
    start_date=datetime(2024,1,1),
    catchup=False,
    tags=["ingestion", "bronze", "jobs"],
    doc_md="""
    ## DAG : scrape_jobs
    Scrape tech job offers from 4 sources in parallel 
    and writes them to the Bronze layer
    **Sources:** France Travail - Adzuna - Rekrute - Emploi.ma
    **Schedule:** Daily at 08:00
    **Layer:** Bronze
    """
)
def scrape_jobs():

    @task(task_id="ingest_france_travail")
    def ingest_france_travail() -> list[dict]:
        from services.ingestion.api_clients.france_travail import FranceTravailClient
        from services.ingestion.producers.bronze_writer import write_to_bronze
        client_id = os.getenv("FT_CLIENT_ID")
        client_secret = os.getenv("FT_CLIENT_SECRET")

        client = FranceTravailClient(client_id=client_id, client_secret=client_secret)
        offers = client.fetch_all_tech_offers()

        logger.info("France Travail : %d offers collected", len(offers))
        key = write_to_bronze(offers, source="france_travail")
        logger.info("France Travail : written to %s", key)
        return key

    @task(task_id="ingest_adzuna")
    def ingest_adzuna() -> list[dict]:
        from services.ingestion.api_clients.adzuna import AdzunaClient
        from services.ingestion.producers.bronze_writer import write_to_bronze

        app_id  = os.getenv("ADZUNA_APP_ID")
        app_key = os.getenv("ADZUNA_APP_KEY")

        client = AdzunaClient(app_id=app_id, app_key=app_key)
        offers = client.fetch_all_tech_offers()

        logger.info("Adzuna : %d offers collected", len(offers))

        key = write_to_bronze(offers, source="adzuna")
        logger.info("Adzuna : written to %s", key)
        return key

    @task(task_id="ingest_rekrute")
    def ingest_rekrute() -> list[dict]:
        from services.ingestion.scrapers.rekrute import RekruteScraper
        from services.ingestion.producers.bronze_writer import write_to_bronze

        scraper = RekruteScraper()
        offers  = scraper.scrape()

        logger.info("Rekrute : %d offers collected", len(offers))
        key = write_to_bronze(offers, source="rekrute")
        logger.info("Rekrute : written to %s", key)
        return key


    @task(task_id="ingest_indeed_ma")
    def ingest_indeed_ma() -> str:
        from services.ingestion.scrapers.indeed import IndeedApifyConnector
        from services.ingestion.producers.bronze_writer import write_to_bronze

        connector = IndeedApifyConnector(country="MA", max_items=10)
        offers = connector.scrape()

        logger.info("Indeed MA (Apify) : %d offers collected", len(offers))
        key = write_to_bronze(offers, source="indeed_ma")
        logger.info("Indeed MA (Apify) : written to %s", key)
        return key

    
    @task(task_id="ingest_indeed_fr")
    def ingest_indeed_fr() -> str:
        from services.ingestion.scrapers.indeed import IndeedApifyConnector
        from services.ingestion.producers.bronze_writer import write_to_bronze
    
        connector = IndeedApifyConnector(country="FR", max_items=10)
        offers    = connector.scrape()
    
        logger.info("Indeed FR (Apify) : %d offers collected", len(offers))
        key = write_to_bronze(offers, source="indeed_fr")
        logger.info("Indeed FR (Apify) : written to %s", key)
        return key

    @task(task_id="collcet_bronze_keys")
    def collect_bronze_keys(keys: list[str]) -> list[str]:
        return [k for k in keys if k]

    ft_key = ingest_france_travail()
    adzuna_key = ingest_adzuna()
    rekrute_key = ingest_rekrute()
    indeed_ma_key = ingest_indeed_ma()
    indeed_fr_key = ingest_indeed_fr()

    rekrute_key >> indeed_ma_key >> indeed_fr_key

    all_keys = collect_bronze_keys([ft_key, adzuna_key, rekrute_key, indeed_ma_key, indeed_fr_key])

    trigger_silver = TriggerDagRunOperator(
        task_id="trigger_silver_layer",
        trigger_dag_id="silver_layer",
        conf={"bronze_keys": all_keys} # will be transmitted to the Silver DAG
    )

    all_keys >> trigger_silver

@dag(
    dag_id="silver_layer",
    schedule=None,
    start_date=datetime(2024,1,1),
    catchup=False,
    tags=["silver", "transformations", "jobs"],
    doc_md="""
    
    """
)
def silver_layer():

    @task(task_id="transform_silver")
    def transform_silver(**context) -> str:
        from services.silver.silver_job import run_silver_job, create_spark_session_minio
        from services.silver.silver_writer import write_to_silver
        import os

        bronze_keys = context["dag_run"].conf.get("bronze_keys", [])
        if not bronze_keys:
            logger.warning("No new Bronze files to process - skipping Silver run")
            return ""

        bucket = os.getenv("MINIO_BUCKET")
        paths = [f"s3a://{bucket}/{key}" for key in bronze_keys]
        spark = create_spark_session_minio(
            os.getenv('SPARK_MASTER_URL'),
            os.getenv('MINIO_ENDPOINT'),
            os.getenv('MINIO_ACCESS_KEY'),
            os.getenv('MINIO_SECRET_KEY')
        )
        df_bronze = spark.read.option("multiline", "true").json(paths)
        df_silver = run_silver_job(df_bronze)

        result_path = write_to_silver(df_silver, source="offres", mode="append")
        logger.info("Silver :written to %s", result_path)
        return result_path

    transform_silver()
    

scrape_jobs()
silver_layer()