"""
emploi_ma.py
------------
Scraper for Emploi.ma — Morocco's generalist job board.
 
Strategy:
  Step 1 — List page  : extract title, URL, company and summary from each card
  Step 2 — Detail page: fetch each offer URL to get structured fields
                        (city, contract, experience, sector, education)
                        and full description for skill extraction
  Step 3 — Normalize  : map all fields to unified schema via field_mapper.py
 
Selectors are confirmed from real HTML inspection
  
"""

import hashlib
import logging
import time
from datetime import datetime
 
import requests
from bs4 import BeautifulSoup
import os
 
from config.settings import EMPLOIMA_BASE_URL, EMPLOIMA_SEARCH_URL ,GROQ_API_KEY ,GROQ_URL
from services.ingestion.normalizers.field_mapper import map_emploima
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


 
# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
 
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}
 
REQUEST_DELAY = 1.5  # seconds between requests
MAX_PAGES     = 5    # 1 page = ~25 offers

# ---------------------------------------------------------------------------
# HTTP HELPER
# ---------------------------------------------------------------------------
 
def fetch_page(url: str) -> BeautifulSoup | None:
    """Fetches a URL and returns BeautifulSoup. Returns None on failure."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error fetching %s : %s", url, e)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Network error fetching %s : %s", url, e)
        return None

# ---------------------------------------------------------------------------
# STRUCTURED FIELD EXTRACTOR
# ---------------------------------------------------------------------------

def extract_structured_field(soup: BeautifulSoup, label: str) -> str:
    """
    Extracts the value of a structured field from the detail page.
 
    The pattern on Emploi.ma is consistent across all fields:
      <li>
        <strong>Label</strong> : <span>Value</span>
      </li>
 
    Args:
        soup:  BeautifulSoup of the detail page
        label: The field label to look for, e.g. "Ville", "Type de contrat"
 
    Returns:
        The text value of the field, or empty string if not found
    """

    # Find the <strong> tag containning the label 
    strong_tag = soup.find("strong", string=lambda t: t and label in str(t))

    if not strong_tag: 
        return ""

    # The value is in the <span> sibling inside the same <li> 
    parent_li = strong_tag.parent # <li> 
    span      = parent_li.find("span") if parent_li else None 

    if not span: 
        return ""
    
    return span.text.strip()


def is_tech_offer_llm(titre: str, secteur: str = "") -> bool:
    """
    Classify the job offer using Groq (llama-3.1-8b-instant) .
    """
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — skipping LLM filter")
        return True  # safe default

    prompt = (
        f"Est-ce que ce poste est un emploi dans le domaine tech / "
        f"informatique / data / digital / développement ?\n"
        f"Titre : {titre}\n"
        f"Secteur : {secteur or 'non précisé'}\n\n"
        f"Réponds UNIQUEMENT par OUI ou NON, rien d'autre."
    )

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 5,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }

    try:
        response = requests.post(
            GROQ_URL,
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        answer = (
            response.json()
            ["choices"][0]
            ["message"]["content"]
            .strip()
            .upper()
        )
        logger.debug("LLM [%s] → %s", titre, answer)
        return answer.startswith("OUI")

    except Exception as e:
        logger.warning("Groq classification failed '%s': %s", titre, e)
        return True  # safe default 

# ---------------------------------------------------------------------------
# LIST PAGE PARSING
# ---------------------------------------------------------------------------

def parse_offer_card(card: BeautifulSoup) -> dict: 
    """
    Extracts basic fields from a single offer card (div.card.card-job).
 
    Fields available on list page:
      url, title, company, summary
    """

    # --- URL ---
    # Available as data-href attribute on the card div itself
    url = card.get("data-href", "")

    # --- Title ---
    title_tag = card.select_one("h3 > a")
    titre_brut = title_tag.text.strip() if title_tag else ""

    # -- Company --- 
    company_tag = card.select_one("a.card-job-company")
    company     = company_tag.text.strip() if company_tag else ""

    # --- Summary ---
    summary_tag = card.select_one("div.card-job-description p")
    summary     = summary_tag.text.strip() if summary_tag else ""

    # --- Company logo alt (fallback for company name) ---
    img_tag         = card.select_one("picture img")
    company_img_alt = img_tag.get("alt", "").strip() if img_tag else ""

    return {
        "url":             url,
        "titre_brut":      titre_brut,
        "entreprise":      company or company_img_alt,
        "summary":         summary,
    }

def scrape_list_page(page_number: int) -> list[dict]:
    """
    Scrapes a single list page and returns basic offer data.
 
    Emploi.ma pagination pattern: ?page=1, ?page=2, etc.
    Page 0 = first page (no ?page parameter needed)
 
    Args:
        page_number: Page index (starts at 0)
 
    Returns:
        List of basic offer dicts from the list page
    """
    # Page 0 has no query param — subsequent pages use ?page=N
    url = EMPLOIMA_SEARCH_URL if page_number == 0 else f"{EMPLOIMA_SEARCH_URL}?page={page_number}"

    logger.info("Scraping list page %d : %s", page_number, url)

    soup = fetch_page(url)
    if not soup: 
        return[]

    # Find all offer cards
    cards = soup.select("div.card.card-job")
    logger.info("Found %d offer cards on page %d.", len(cards), page_number)

    results = []

    for card in cards: 
        try: 
            data = parse_offer_card(card)
            if data.get("url"): # skip cards without URL
                results.append(data)
        except Exception as e: 
            logger.warning("Error parsing card %s",e)
            continue 

    return results

# ---------------------------------------------------------------------------
# DETAIL PAGE PARSING
# ---------------------------------------------------------------------------

def parse_detail_page(url: str) -> dict:
    soup = fetch_page(url)
    if not soup:
        return {}

    # --- Full description ---
    desc_tag    = soup.select_one(".job-description")
    description = desc_tag.text.strip() if desc_tag else ""

    def get_withicon(icon_class: str) -> str:
        """
        Search for a <li> element whose class contains icon_class. 
        Tolerate variations in prefixes (withicon, icon-, fa-, etc.).
        """
        # Broad search: any <li> element whose class contains the fragment.
        li = soup.find(
            "li",
            class_=lambda c: c and any(icon_class in cls for cls in c.split())
        )
        if not li:
            return ""
        span = li.find("span")
        if not span:
            # Fallback: raw text from the <li> element without the <strong> label.
            strong = li.find("strong")
            if strong:
                strong.decompose()
            return li.get_text(strip=True).lstrip(": ")
        field_item = span.select_one(".field-item")
        return field_item.text.strip() if field_item else span.text.strip()

    def get_by_label(label: str) -> str:
        """
        Search for a <strong> element containing 
        the label (case-insensitive and tolerant to apostrophe variations: ' U+2019, ´ U+00B4, ' U+0027).
        """
        def normalize(t: str) -> str:
            return t.lower().replace("\u00b4", "'").replace("\u2019", "'")

        strong = soup.find(
            "strong",
            string=lambda t: t and label.lower() in normalize(str(t))
        )
        if not strong:
            return ""
        parent = strong.parent  # <li>
        if not parent:
            return ""

        # Try .field-item first (some listings), otherwise use the <span> directly.
        field_item = parent.select_one(".field-item")
        if field_item:
            return field_item.text.strip()
        
        span = parent.find("span")
        if span:
            return span.text.strip()

        # Last resort: raw text from the <li> element without the label.
        strong_text = strong.get_text()
        return parent.get_text(strip=True).replace(strong_text, "").lstrip(" :´'")

    # Try withicon first, fall back to the label if empty.
    def get_field(icon_class: str, label: str) -> str:
        value = get_withicon(icon_class)
        if not value:
            value = get_by_label(label)
        return value

    
    salaire      = get_by_label("Salaire")
    ville        = get_by_label("Ville")
    experience   = get_by_label("Niveau d'expérience")
    education    = get_by_label("Niveau d'études")
    type_contrat = get_by_label("Type de contrat")
    remote       = get_by_label("Travail à distance")
    fonction     = get_by_label("Métier")
    secteur      = get_by_label("Secteur")
    region       = get_by_label("Région")
    nb_postes    = get_by_label("Nombre de poste(s)")

    # --- Date de publication  ---
    date_pub = ""

    details_div = soup.select_one("div.page-application-details")
    if details_div: 
        for p in details_div.find_all("p"):
            text = p.get_text(strip=True)
            if "Publiée le" in text: 
                date_pub = text.replace("Publiée le", "").strip()
                break 
    
    if date_pub:
        try:
            date_pub = datetime.strptime(date_pub, "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            pass  

        return {
            "description":    description,
            "ville_brute":    ville,
            "type_contrat":   type_contrat,
            "experience":     experience,
            "education":      education,
            "secteur":        secteur,
            "fonction":       fonction,
            "remote":         remote,
            "salaire_brut":   salaire,
            "date_publication": date_pub,
            "nb_postes":        nb_postes,
        }

# ---------------------------------------------------------------------------
# MAIN SCRAPER CLASS
# ---------------------------------------------------------------------------

class EmploiMaScraper:
    """
    Full scraper for Emploi.ma tech job offers.
 
    Workflow:
      1. Scrape list pages to get offer URLs and basic fields
      2. For each offer URL, fetch the detail page for structured data
      3. Merge list + detail data and normalize via field_mapper
    """

    def __init__(self, max_pages: int = MAX_PAGES , fetch_details: bool = True):
        """
        Args:
            max_pages:      Number of list pages to scrape
            fetch_details:  If True, fetches detail page for each offer
                            Set to False for quick testing
        """
        self.max_pages     = max_pages
        self.fetch_details = fetch_details

    def scrape(self) -> list[dict]:
        """
        Main entry point — scrapes all pages and returns normalized offers.
 
        Returns:
            List of normalized offer dicts ready for Kafka / Bronze layer
        """
        all_raw = []
        seen_urls = set()

        for page in range(0,self.max_pages):
            cards = scrape_list_page(page)

            if not cards: 
                logger.info("No more offers on page %d — stopping", page)
                break

            for card in cards: 
                url = card.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                if not is_tech_offer_llm(
                    titre=card.get("titre_brut", ""),
                    secteur=card.get("summary", "")
                ):
                    logger.info("Non-tech (LLM) skipped : %s", card.get("titre_brut"))
                    continue  

                # Fetch detail if tech is confirmed
                if self.fetch_details and url:
                    time.sleep(REQUEST_DELAY)
                    detail = parse_detail_page(url)
                    card.update(detail)

                all_raw.append(card)
            
            time.sleep(REQUEST_DELAY)

        logger.info("Scraping complete. %d unique offers collected.", len(all_raw))

        # Normalize 
        normalized = []
        for raw in all_raw:
            try: 
                offer = map_emploima(raw)
                normalized.append(offer)
            except Exception as e: 
                logger.warning("Error normalizing offer %s : %s", raw.get("url", "?"), e)
                continue

        logger.info("%d offers normalized successfully.", len(normalized))
        return normalized

    def health_check(self) -> bool:
        """
        Checks if Emploi.ma HTML structure is still as expected.
 
        Returns:
            True if structure intact, False if site changed
        """
        soup = fetch_page(EMPLOIMA_SEARCH_URL)
 
        if not soup:
            logger.error("Health check failed — could not fetch Emploi.ma.")
            return False
 
        cards = soup.select("div.card.card-job")
        if not cards:
            logger.error(
                "STRUCTURE CHANGE DETECTED — div.card.card-job not found."
            )
            return False
 
        title = cards[0].select_one("h3 > a")
        if not title:
            logger.error(
                "STRUCTURE CHANGE DETECTED — h3 > a not found in card."
            )
            return False
 
        logger.info("Health check passed — %d offer cards found.", len(cards))
        return True

# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------
 
if __name__ == "__main__":
    scraper = EmploiMaScraper(max_pages=1, fetch_details=True)
 
    if not scraper.health_check():
        print("ERROR: Emploi.ma structure has changed — check selectors.")
        exit(1)
 
    offers = scraper.scrape()
 
    print(f"\n{'='*55}")
    print(f"  Results : {len(offers)} offers collected") 
    print(f"{'='*55}")
 
    if offers:
        first = offers[0]
        print(f"\n  Title       : {first['titre_brut']}")
        print(f"  Company     : {first['entreprise']}")
        print(f"  City        : {first['ville_brute']}")
        print(f"  Contract    : {first['type_contrat']}")
        print(f"  salaire     : {first['salaire_brut']}")
        print(f"  Experience  : {first['niveau_experience']}")
        print(f"  nb_postes   : {first['nombre_postes']}")
        print(f"  Sector      : {first['secteur_activite']}")
        print(f"  Skills      : {first['competences_brutes']}")
        print(f"  Langues     : {first['langues']}")
        print(f"  quality pro     : {first['qualites_pro']}")
        print(f"  Description : {first['description'][:150]}...")
        print(f"  ID hash     : {first['id_hash']}")
        print(f"  Date de pub         : {first['date_publication']}")
        print(f"  URL         : {first['url_offre']}")