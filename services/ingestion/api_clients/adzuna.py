"""
adzuna.py
---------
Client for the Adzuna Jobs API — France coverage only.
 
Adzuna provides a REST API with keyword search and pagination.
No OAuth2 required — just App ID + App Key as query parameters.
 
"""

import hashlib
import logging
import time
from datetime import datetime
import requests

from config.settings import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    ADZUNA_BASE_URL,
    ADZUNA_TECH_KEYWORDS,
)

from services.ingestion.normalizers.field_mapper import map_adzuna

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
 
# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Adzuna conutry code for France 
COUNTRY = "fr"

# Max results per page (Adzuna allows up to 50)
RESULTS_PER_PAGE = 5 

# Max pages per keyword — 50 results x 5 pages = 250 offers per keyword
MAX_PAGES = 5

# Delay between requests
REQUEST_DELAY = 0.5  # seconds

# ---------------------------------------------------------------------------
# CLIENT CLASS
# ---------------------------------------------------------------------------

class AdzunaClient:
    """
    Client for the Adzuna Jobs API.
 
    Handles keyword search, pagination, deduplication and normalization.
    Authentication is done via query parameters (app_id + app_key) —
    no token management needed .
    """
    def __init__(self, app_id: str , app_key: str):
        """
        Args:
            app_id:  Your Adzuna App ID from developer.adzuna.com
            app_key: Your Adzuna App Key from developer.adzuna.com
        """
        self.app_id  = app_id
        self.app_key = app_key

    def _build_url(self, page:int) -> str:
        """
        Builds the search endpoint URL for a given page.
        Adzuna URL format: /v1/api/jobs/{country}/search/{page}
        """
        return f"{ADZUNA_BASE_URL}/{COUNTRY}/search/{page}"

    def fetch_offers(
        self,
        keyword: str,
        max_pages: int = MAX_PAGES,
    ) -> list[dict]:
        """
        Fetches all offers for a given keyword across multiple pages.
 
        Args:
            keyword:   Search term, e.g. "data engineer"
            max_pages: Number of pages to fetch (50 results per page)
 
        Returns:
            List of normalized offer dicts
        """
        results = []
        seen_ids = set() # deduplicate by Adzuna offer ID 

        for page in range(1, max_pages + 1):
            logger.info(
                "Fetching Adzuna page %d/%d  for keyword '%s' ...",
                page , max_pages, keyword
            )

            params = {
                "app_id":           self.app_id,
                "app_key":          self.app_key,
                "what":             keyword, 
                "results_per_page": RESULTS_PER_PAGE,
                "content-type":     "application/json",
                "sort_by":          "date", # Sort by most recent first 
            } 

            try: 
                response = requests.get(
                    self._build_url(page),
                    params=params,
                    timeout=15,
                )
                response.raise_for_status()
                data = response.json()

            except requests.exceptions.HTTPError as e:
                logger.error( "HTTP error on page %d for '%s': %s" ,page, keyword , e)
                break
            
            except requests.exceptions.RequestException as e:
                logger.error("Network error on page %d for '%s': %s",page, keyword, e)
                break
            
            raw_offers = data.get("results", [])

            # Stop if no more results 
            if not raw_offers:
                logger.info("No more results on page %d for '%s' — stopping.",page, keyword)
                break

            for raw in raw_offers:
                offer_id = raw.get("id", "")

                # Skip duplicates - same offer can appear for multiple keywords
                if offer_id in seen_ids: 
                    continue 
                seen_ids.add(offer_id)

                results.append(map_adzuna(raw))
                logger.info("Page %d : %d new offers (total so far: %d).",page, len(raw_offers), len(results))

                # Respect rate limit between pages
                time.sleep(REQUEST_DELAY)
        return results 

    def fetch_all_tech_offers(self) -> list[dict]:
        """
        Fetches offers for all tech keywords defined in settings.
        Deduplicates across keywords using offer ID.
 
        Returns:
            Deduplicated list of all tech offers collected
        """

        all_offers = {} # { id_hash: offer } for deduplication across keywords

        for keyword in ADZUNA_TECH_KEYWORDS:
            offers = self.fetch_offers(keyword)

            for offer in offers: 
                all_offers[offer["id_hash"]] = offer

            logger.info("Keyword '%s' done. Total unique offers so far: %d.",keyword, len(all_offers))
            
            # Pause between keywords
            time.sleep(REQUEST_DELAY)

        result = list(all_offers.values())
        logger.info("All keywords done. Total after deduplication: %d offers.",len(result))
        return result 

# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------
 
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
 
    load_dotenv()
 
    app_id  = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
 
    if not app_id or not app_key:
        print("ERROR: ADZUNA_APP_ID or ADZUNA_APP_KEY missing in .env")
        exit(1)
 
    client = AdzunaClient(app_id=app_id, app_key=app_key)
 
    # Test with single keyword, single page
    offers = client.fetch_offers("data engineer", max_pages=1)
 
    print(f"\n{'='*55}")
    print(f"  Results : {len(offers)} offers retrieved")
    print(f"{'='*55}")
 
    if offers:
        first = offers[3]
        print(f"\n  Title       : {first['titre_brut']}")
        print(f"  Company     : {first['entreprise']}")
        print(f"  City        : {first['ville_brute']}")
        print(f"  Region      : {first['region']}")
        print(f"  Description : {first['description']}...")
        print(f"  Salary pred : {first['salaire_est']}")
        print(f"  skills      : {first['competences_brutes']}")
        print(f"  Created     : {first['date_publication']}")
        print(f"  ID hash     : {first['id_hash']}")
        print(f"  URL         : {first['url_offre']}")