from __future__ import annotations
import os 
import logging 
from datetime import datetime
from airflow.sdk import dag , task 

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

    @task(task_id="ingest_emploima")
    def ingest_emploima() -> list[dict]:
        from services.ingestion.scrapers.emploi_ma import EmploiMaScraper
        from services.ingestion.producers.bronze_writer import write_to_bronze
        
        scraper = EmploiMaScraper(max_pages=5)
        offers  = scraper.scrape()

        logger.info("Emploi.ma : %d offers collected", len(offers))
        key = write_to_bronze(offers, source="emploi_ma")
        logger.info("Emploi.ma : written to %s", key)
        return key

    ingest_france_travail()
    ingest_adzuna()
    ingest_rekrute()
    ingest_emploima()


scrape_jobs()