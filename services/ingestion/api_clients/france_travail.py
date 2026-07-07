"""
    France Travail API client.

    This module handles communication with the France Travail API, including
    OAuth2 authentication, job offer retrieval, and data normalization.
    It provides methods to collect job postings based on predefined keywords
"""


import requests 
import time 
import hashlib
import logging 
from datetime import datetime 
from config.settings import FT_TOKEN_URL, FT_API_BASE, FT_SCOPE
from services.ingestion.normalizers.field_mapper import map_france_travail

# SEARCH KEYWORDS
TECH_KEYWORDS = [
    "data engineer",
    "data scientist",
    "développeur python",
    "devops",
    "cloud architect",
    "machine learning",
    "fullstack developer",
    "backend developer",
]

#LOGGER  
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class FranceTravailClient:
    """  
        This class encapsulates all the logic required to communicate with the API.
    
    """

    def __init__(self,client_id:str , client_secret:str):

        """
        Args:
            client_id: The Client ID provided by francetravail.io
            client_secret: The Client Secret provided by francetravail.io

        """

        self.client_id     = client_id 
        self.client_secret = client_secret
        self._token        = None 
        self._token_expiry = 0

    # -----------------------------------------------------------------------
    # PART 1 : AUTHENTIFICATION
    # -----------------------------------------------------------------------

    def _get_token(self) -> str : 

        """
        Returns a valid access token.

        - If a token is already available and will not expire within the next
        30 seconds, it is returned directly (no additional network request).
        - Otherwise, a new token is requested from the France Travail server.
        """
        if self._token and time.time() < self._token_expiry - 30 :
            return self._token

        logger.info("Requesting a new OAuth2 access token...")
        response = requests.post(
            FT_TOKEN_URL, 
            data = {
                "grant_type":    "client_credentials",
                "client_id" :    self.client_id,
                "client_secret": self.client_secret,
                "scope": FT_SCOPE  
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        
        self._token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in",1499)

        logger.info("Access token obtained, valid for %d seconds.", data.get("expires_in", 1499))
        
        return self._token


    def _headers(self) -> dict :
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/json"
        }

    # -----------------------------------------------------------------------
    # PART 2: FETCHING JOB OFFERS
    # -----------------------------------------------------------------------

    def fetch_offers(self, keyword: str , max_results: int = 150) -> list[dict]: 
        """
        Fetches job offers matching the specified keyword.

        Args:
            keyword: The search term, e.g. "data engineer".
            max_results: The maximum number of job offers to retrieve .

        Returns : 
            A list of dictionaries, each containing a normalized job offer.
        """
        logger.info("Searching for job offers for the keyword : '%s'", keyword)

        params = {
            "motsCles": keyword,
            "range": f"0-{min(max_results, 149)}",
        }
        
        try : 
            response = requests.get(
                f"{FT_API_BASE}/offres/search",
                headers = self._headers(),
                params = params, 
                timeout =15,
            )

            if response.status_code == 204 : 
                logger.info("No job offers found for '%s'.", keyword)
                return []

            if response.status_code not in (200, 206):
                response.raise_for_status()

            data = response.json()
            
            raw_offers = data.get("resultats", [])
        
            logger.info("%d offers found for '%s' . ", len(raw_offers), keyword)

            return [map_france_travail(offer) for offer in raw_offers]
        except requests.exceptions.RequestException as e : 
            logger.error ("Network error for '%s' : '%s'", keyword , e)
            return []

    def fetch_all_tech_offers (self, max_per_keyword : int = 150) -> list[dict]:
        """
        Collects job offers for all tech keywords defined in TECH_KEYWORDS.

        Problem to handle:
        The same job posting may appear under multiple keywords.
        For example, a "Data Engineer Python" position may be returned for both
        "data engineer" and "python developer".

        Solution:
        A Python dictionary is used with the job offer's id_hash as the key.
        If the same job offer is retrieved more than once, it simply overwrites
        the existing entry instead of creating a duplicate.

        Returns:
            A deduplicated list of all collected job offers.
        """
        seen_offers = {}
        for keyword in TECH_KEYWORDS: 
            offers = self.fetch_offers(keyword, max_results = max_per_keyword)

            for offer in offers : 
                seen_offers[offer["id_hash"]] = offer 
                time.sleep(0.1)
        
        result = list(seen_offers.values())
        logger.info ("Collection completed. %d job offers remaining after deduplication.",len(result))
        return result 

if __name__ == "__main__":
    import os 
    from dotenv import load_dotenv 
    from services.ingestion.normalizers.field_mapper import map_france_travail

    load_dotenv()

    client_id      = os.getenv("FT_CLIENT_ID")
    client_secret  = os.getenv("FT_CLIENT_SECRET")

    if not client_id or not client_secret : 
        print ("ERROR: FT_CLIENT_ID or FT_CLIENT_SECRET missing in .env")
        exit(1)
    
    client = FranceTravailClient(client_id = client_id, client_secret= client_secret)
    offers = client.fetch_offers("data engineer", max_results=3)

    print(f"\n{'='*55}")
    print(f"  Results : {len(offers)} offers retrieved")
    print(f"{'='*55}")

    if offers:
        first = offers[0]
        print(f"\n  Title       : {first['titre_brut']}")
        print(f"  Company     : {first['entreprise']}")
        print(f"  City        : {first['ville_brute']}")
        print(f"  Contract    : {first['type_contrat']}")
        print(f"  Experience  : {first['niveau_experience']}")
        print(f"  ROME        : {first['code_rome']} - {first['libelle_rome']}")
        print(f"  Skills      : {first['competences_brutes']}")
        print(f"  Salary      : {first['salaire_brut']}")
        print(f"  ID hash     : {first['id_hash']}")  





