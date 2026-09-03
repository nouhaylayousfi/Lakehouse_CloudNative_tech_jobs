"""
Connector for Indeed (Morocco + France) via Apify misceres/indeed-scraper.
 
Strategy:
  1. Trigger a new Apify run via API with search parameters
  2. Poll until the run reaches SUCCEEDED or FAILED status
  3. Fetch items from the run's dataset
  4. Apply LLM tech filter
  5. Normalize via field_mapper.py
 
Two entry points:
  - IndeedApifyConnector(country="MA") → Indeed Maroc
  - IndeedApifyConnector(country="FR") → Indeed France
"""

import logging
import time
 
import requests
 
from config.settings import APIFY_API_TOKEN, APIFY_INDEED_ACTOR ,TECH_KEYWORDS
from services.ingestion.shared.llm_filter import is_tech_offer_llm
from services.ingestion.normalizers.field_mapper import map_indeed
 
logger = logging.getLogger(__name__)
 
APIFY_BASE_URL = "https://api.apify.com/v2"
POOL_INTERVAL  = 10   # seconds between status checks
MAX_WAIT       = 600  # 10 minutes max before timeout

# ---------------------------------------------------------------------------
# APIFY API HELPERS
# ---------------------------------------------------------------------------
 
def _headers() -> dict:
    return {
        "Authorization": f"Bearer {APIFY_API_TOKEN}",
        "Content-Type": "application/json",
    }

def trigger_run(country: str , max_items: int =100) -> str | None:
    """
    Triggers a new Apify run for the Indeed scraper.
 
    Args:
        country:   ISO country code — "MA" for Morocco, "FR" for France
        max_items: Max number of offers to scrape per keyword
 
    Returns:
        Run ID string if successful, None on failure
    """
    url = f"{APIFY_BASE_URL}/acts/{APIFY_INDEED_ACTOR}/runs"

    position = " OR ".join(TECH_KEYWORDS)
 
    payload = {
        "position": position,
        "country": country,
        "maxItems": max_items, 
        }

    try:
        response = requests.post(url, json=payload , headers=_headers(), timeout=30)
        response.raise_for_status()
        run_id = response.json()["data"]["id"]
        logger.info("Apify run triggered — country=%s run_id=%s", country, run_id)
        return run_id
    except Exception as e:
        logger.error("Failed to trigger Apify run (country=%s): %s", country, e)
        return None

def wait_for_run(run_id: str) -> bool:
    """
    Polls Apify until the run reaches SUCCEEDED or FAILED.
 
    Args:
        run_id: Apify run ID
 
    Returns:
        True if SUCCEEDED, False if FAILED or timeout
    """
    url     = f"{APIFY_BASE_URL}/actor-runs/{run_id}"
    elapsed = 0

    while elapsed < MAX_WAIT:
        try:
            response = requests.get(url, headers=_headers(), timeout=15)
            response.raise_for_status()
            status = response.json()["data"]["status"]
            logger.info(
                "Apify run %s — status: %s (%ds elapsed)",
                run_id, status, elapsed,
            )
            if status == "SUCCEEDED":
                return True
            if status in ("FAILED" ,"ABORTED", "TIMED-OUT"):
                logger.error("Apify run %s ended with status: %s", run_id, status)
                return False

        except Exception as e:
            logger.warning("Error polling run %s: %s", run_id, e)
        
        time.sleep(POOL_INTERVAL)
        elapsed += POOL_INTERVAL

    logger.error("Apify run %s timed out after %ds.", run_id, MAX_WAIT)
    return False

def fetch_run_items(run_id: str) -> list[dict]:
    """
    Fetches all dataset items from a completed Apify run.
 
    Args:
        run_id: Apify run ID
 
    Returns:
        List of raw offer dicts
    """
    url = f"{APIFY_BASE_URL}/actor-runs/{run_id}/dataset/items"

    try:
        response = requests.get(url, headers=_headers(), timeout=30)
        response.raise_for_status()
        items = response.json()
        logger.info("Apify run %s — %d items fetched.", run_id, len(items))
        return items
    except Exception as e:
        logger.error("Failed to fetch items for run %s: %s", run_id, e)
        return []

# ---------------------------------------------------------------------------
# MAIN CONNECTOR CLASS
# ---------------------------------------------------------------------------

class IndeedApifyConnector:
    """
    Connector for Indeed job offers (MA or FR) via Apify.
 
    Workflow:
      1. Trigger a new Apify run
      2. Wait for completion
      3. Fetch items
      4. Apply LLM tech filter
      5. Normalize via field_mapper
    """

    def __init__(self, country: str ="MA", max_items:int =10):
        """
        Args:
            country:   "MA" for Morocco, "FR" for France
            max_items: Max items per keyword search
        """
        self.country = country
        self.max_items = max_items

    def scrape(self) -> list[dict]:
        """
        Main entry point — triggers run, waits, fetches, filters, normalizes.
 
        Returns:
            List of normalized offer dicts ready for Bronze layer ingestion
        """
        # Step1 - Trigger run 
        run_id = trigger_run(country=self.country , max_items = self.max_items)
        if not run_id:
            logger.error("Indeed Apify (%s): run could not be triggered.", self.country)
            return []

        # Step 2 - Wait for completion 
        success = wait_for_run(run_id)
        if not success: 
            logger.error(
                "Indeed Apify (%s): run %s did not succeed.",
                self.country, run_id,
            )
            return []

        # Step 3 - Fetch items 
        raw_items = fetch_run_items(run_id)
        if not raw_items:
            logger.warning("Indeed Apify (%s): no items in dataset.", self.country)
            return []

        # Step 4 - LLM tech filter 
        filtered = []
        for item in raw_items:
            titre = item.get("positionName", "")

            if not is_tech_offer_llm(titre=titre):
                logger.info("Non_tech (LLM) skipped: %s", titre)
                continue 

            filtered.append(item)

        logger.info(
            "Indeed Apify (%s): %d tech offers after LLM filter (out of %d).",
            self.country, len(filtered), len(raw_items),
        )

        # Step 5 - Normalize 
        normalized = []
        for raw in filtered: 
            try : 
                offer = map_indeed(raw, country = self.country)
                normalized.append(offer)
            except Exception as e: 
                logger.warning(
                    "Error normalizing offer %s : %s",
                    raw.get("url", "?"), e,
                )
                continue

        logger.info(
            "Indeed Apify (%s): %d offers normalized successfully.",
            self.country, len(normalized),
        )
        return normalized