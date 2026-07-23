"""
rekrute.py
----------
Scraper for Rekrute.com — Morocco's main tech job board.
 
Strategy:
  Step 1 — List page  : extract title, URL and structured fields from each offer card
  Step 2 — Detail page: fetch each offer URL to get full description and skills
  Step 3 — Normalize  : map all fields to the unified schema via field_mapper.py
 
Selectors confirmed from real HTML inspection:
  - Offer card container : li.post-id
  - Title + URL          : a.titreJob
  - Summary              : .info span (first span with color style)
  - Publication date     : em.date spans
  - Structured fields    : ul > li > a (secteur, fonction, expérience, études, contrat)
"""

import hashlib
import logging
import time
from datetime import datetime
 
import requests
from bs4 import BeautifulSoup
 
from config.settings import REKRUTE_BASE_URL, REKRUTE_SEARCH_URL
from services.ingestion.normalizers.field_mapper import map_rekrute
from services.silver.dict_matcher import extract_skills_from_text


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
 
# Browser-like headers to avoid being blocked
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}

#Delay between requests
REQUEST_DELAY = 1.5
#TECH sector ID on Rekrute (s=3 = Informatique Télécom)
TECH_SECTOR_ID = 3
#Max pages to scrape per run : 1 = ~20 offers 
MAX_PAGES = 5 
  

# ---------------------------------------------------------------------------
# HTTP HELPERS
# ---------------------------------------------------------------------------
def fetch_page(url: str) -> BeautifulSoup | None: 
    """
    Fetches a URL and returns a BeautifulSoup object.
    Returns None if the request fails — caller decides what to do.
    """
    try: 
        response = requests.get(url, headers= HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except request.exceptions.HTTPError as e: 
        logger.error("HTTP error fetching %s : %s", url, e)
        return None 
    except request.exceptions.RequestException as e:
        logger.error("Network error fetching %s : %s", url, e)
        return None

# ---------------------------------------------------------------------------
# LIST PAGE PARSING
# ---------------------------------------------------------------------------

def parse_offer_card(card: BeautifulSoup) -> dict: 
    """
    Extracts fields from a single offer card (li.post-id).
 
    Fields available on list page:
      title, url, summary, publication_date,
      secteur, fonction, experience, education, contract_type, remote
    """

    # --- Company name from logo alt (fallback for detail page) ---
    company_img = card.find("img", class_="photo")
    company_img_alt = company_img.get("alt", "").strip() if company_img else ""
    # ^ Example: alt="BTechnologie" or alt="" for confidential companies

    # --- Title and URL ---
    titre_tag = card.find("a", class_="titreJob")
    titre_brut = titre_tag.text.strip() if titre_tag else ""
    url_relative = titre_tag["href"] if titre_tag else ""
    url_full = f"{REKRUTE_BASE_URL}{url_relative}" if url_relative else ""

    # Extract city from title — format is "Job Title | City (Maroc)"
    city_brute = ""
    if "|" in titre_brut:
        city_part = titre_brut.split("|")[-1].strip()
        # Remove "(Maroc)" suffix
        city_brute = city_part.replace("(Maroc)", "").strip()
 
    # Clean title — remove city part
    titre_clean = titre_brut.split("|")[0].strip() if "|" in titre_brut else titre_brut

    # --- Summary ---
    # The summary span has inline style with color #5b5b5b
    summary_tag = card.find("span", style=lambda s: s and "5b5b5b" in s)
    summary = summary_tag.text.strip() if summary_tag else ""

    # --- Publication date ---
    # Format in HTML: "Publication : du 12/06/2026 au 12/08/2026 | Postes proposés: 1"
    date_tag = card.find("em", class_="date")
    date_spans = date_tag.find_all("span") if date_tag else []
    date_publication = date_spans[0].text.strip() if date_spans else ""
    # date_spans[0] = start date, date_spans[1] = end date, date_spans[2] = nb postes

    nombre_postes =""
    if len(date_spans) >=3:
        nombre_postes = date_spans[2].text.strip()

    # --- Structured fields (secteur, fonction, expérience, études, contrat) ---
    # These are in a <ul> inside the card, each <li> contains links <a>
    # We read the text of all <a> tags inside each <li>

    secteur       = []
    fonction      = []
    experience    = []
    education     = []
    contract_type = ""
    remote        = ""

    structured_items = card.find_all("li")
    #Each li has a label pattern we can detect from the link href or text context

    for item in structured_items:
        item_text = item.text.strip()
        links     = item.find_all("a")
        link_texts= [a.text.strip() for a in links if a.text.strip()]
        
        if not link_texts:
            continue 

        #Detect field type by cheking href patterns of the links 
        first_href = links[0].get("href", "") if links else ""

        if "sectorId" in first_href:
            secteur = link_texts # Secteur d'activité

        elif "positionId" in first_href: 
            fonction = link_texts # Fonction

        elif "workExperienceId" in first_href:
            experience = link_texts # Expérience requise 

        elif "studyLevelId" in first_href:
            education = link_texts #Niveau d'étude
        
        elif "contractType" in first_href: 
            contract_type = link_texts[0] if link_texts else ""

        # Remote work - not a link, detected from text
        if "Télétravail" in item_text: 
            # Format : "Type de contract proposé : CDI - Télétravail : Hybride"
            if ":" in item_text: 
                remote = item_text.split("Télétravail :")[-1].strip()
                # Remove trailing content after next separator 
                remote = remote.split("-")[0].strip()
    

    return { 
        "titre_brut":       titre_clean,
        "titre_avec_ville": titre_brut,
        "url":              url_full,
        "company_img_alt": company_img_alt,
        "ville_brute":      city_brute,
        "summary":          summary,
        "date_publication": date_publication,
        "nombre_postes":    nombre_postes,
        "secteur":          secteur,
        "fonction":         fonction,
        "experience":       experience,
        "education":        education,
        "contract_type":    contract_type,
        "remote":           remote,
    }

def scrape_list_page(page_number: int) -> list[dict]:
    """
    Scrapes a single list page and returns raw offer cards data.
 
    Args:
        page_number: Page number (starts at 1)
 
    Returns:
        List of raw offer dicts from the list page
    """
    url = f"{REKRUTE_SEARCH_URL}&p={page_number}"
    logger.info("Scraping list page %d : %s", page_number, url)

    soup = fetch_page(url)
    if not soup:
        return []

    # Find all offer cards 
    cards = soup.find_all("li", class_="post-id")
    logger.info("Found %d offer cards on page %d.", len(cards), page_number)

    results = []
    for card in cards: 
        try: 
            data = parse_offer_card(card)
            results.append(data)
        except Exception as e: 
            logger.warning("Error parsing card: %s", e)
            continue 
    return results

# ---------------------------------------------------------------------------
# DETAIL PAGE PARSING
# ---------------------------------------------------------------------------
 
def parse_detail_page(url: str) -> dict:
    """
    Fetches and parses a single offer detail page.
    Returns description, missions, required skills and company info.
 
    Args:
        url: Full URL of the offer detail page
 
    Returns:
        Dict with detail fields — merged with list page data later
    """
    soup = fetch_page(url)
    if not soup: 
        return {}

    # --- Company name & description ---
    company_name        = ""
    company_description = ""

    #Find the "Entreprise :" section header 
    entreprise_header = soup.find(
        ["h2", "h3"] ,
        string=lambda t: t and "Entreprise" in t
    )

    if entreprise_header:
        #collect all content until next h2/h3
        content_tags = []
        for sibling in entreprise_header.find_next_siblings():
            if sibling.name in ["h2", "h3"]:
                break
            content_tags.append(sibling)

        # Company name - try first <strong> first , then first <p> text 
        first_strong = None 
        first_p_text = ""

        for tag in content_tags:
            if not first_strong:
                strong = tag.find("strong")
                if strong and strong.text.strip():
                    first_strong = strong.text.strip()
                    # Clean non-breaking spaces and special chars 
                    first_strong = first_strong.replace("\xa0", " ").strip()

            if not first_p_text and tag.name == "p" and tag.text.strip():
                first_p_text = tag.text.strip().replace("\xa0", " ").strip()

        company_name = first_strong or first_p_text 

        # Full company description - all text combined 
        company_description = " ".join(
            t.text.replace("\xa0", " ").strip()
            for t in content_tags
            if t.text.strip()
         )       

    # Fallback — use img alt from list page 
    if not company_name:
        company_name = soup.get("company_img_alt", "")

    # --- Missions and required skills ---
    # Rekrute detail page has sections: "Poste :", "Profil recherché :"
    missions        = ""
    required_skills = ""
    profile         = ""

    poste_section = soup.find("h3", string=lambda t: t and "Poste" in t)
    if poste_section:
        for sibling in poste_section.find_next_siblings():
            if sibling.name == "h3":
                break
            missions += sibling.text.strip() + " "
        missions = missions.strip()

    profil_section = soup.find("h3", string=lambda t: t and "Profil" in t)
    if profil_section:
        for sibling in profil_section.find_next_siblings():
            if sibling.name == "h3":
                break
            required_skills += sibling.text.strip() + " "
        required_skills = required_skills.strip()

    # Full description = missions + profile combined
    # Used for skill extraction via dict_matcher
    description = f"{missions} {required_skills}".strip()
 
    return {
        "company_name":        company_name,
        #"company_description": company_description,
        "missions":            missions,
        "required_skills":     required_skills,
        "description":         description,
    }

# ---------------------------------------------------------------------------
# MAIN SCRAPER CLASS
# ---------------------------------------------------------------------------

class RekruteScraper: 
    """
    Full scraper for Rekrute.com tech job offers.
 
    Workflow:
      1. Scrape list pages to get offer URLs and structured fields
      2. For each offer URL, fetch the detail page for full description
      3. Merge list + detail data and normalize via field_mapper
    """
    def __init__(self , max_pages: int = MAX_PAGES, fetch_details: bool = True):
        """
        Args:
            max_pages:      Number of list pages to scrape
            fetch_details:  If True, fetches detail page for each offer
                            Set to False for quick testing (list data only)
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
        seen_urls = set() # dediplicate by url 

        for page in range(1, self.max_pages + 1):
            cards = scrape_list_page(page)

            if not cards: 
                logger.info("No more offers found on page %d - Stopping .", page)
                break
            for card in cards: 
                url = card.get("url", "")
                if url in seen_urls:
                    continue 
                seen_urls.add(url)

                #fetch detail page if enabled 
                if self.fetch_details and url: 
                    time.sleep(REQUEST_DELAY)
                    detail = parse_detail_page(url)
                    card.update(detail) # merge detail into card data 
                
                all_raw.append(card)
            
            # Delay between list pages 
            time.sleep(REQUEST_DELAY)
        
        logger.info("Scraping complete . %d unique offers collected ." ,len(all_raw))

        # Normalize all offers via field_mapper 
        normalized = []
        """for raw in all_raw:
            try:
                offer = map_rekrute(raw)
                normalized.append(offer)
            except Exception as e:
                # Afficher l'erreur exacte au lieu de l'ignorer
                print(f"ERROR normalizing: {e}")
                print(f"Raw data: {raw}")
                break  # stopper au premier problème
        return normalized"""
        for raw in all_raw:
            try: 
                offer = map_rekrute(raw)

                # Extract skills from description 
                skills = extract_skills_from_text(
                    offer.get("description", "") + " " + offer.get("titre_brut", "")
                )
                offer["competences_brutes"] = skills 

                # Filter - keep only offers with at least 1 tech skill 
                if not skills : 
                    logger.debug("Skipping non tech offer : %s", offer["titre_brut"])
                    continue
                
                normalized.append(offer)
            
            except Exception as e: 
                logger.warning("Error normalizing offer : %s", e)
                continue 
        
        logger.info("%d offers normalized successfully." , len(normalized))
        return normalized

    def health_check(self) -> bool: 
        url = f"{REKRUTE_SEARCH_URL}&p=1"
        print("URL used: ", url)
        soup = fetch_page(url)

        if not soup: 
            logger.error("Health check failed - could not fetch Rekrute .")
            return False 
        
        cards = soup.find_all("li", class_="post-id")
        print("Cards found: " , len(cards))

        if not cards: 
            logger.error("STRUCTURE CHANGE DETECTED — li.post-id not found.")
            return False 

        """# Print first card HTML to see what's inside 
        print("First card HTML:")
        print(cards[0].prettify()[:800])

        title = cards[0].find("a", class_="titreJob")
        print("titreJob found:", title)

        if not title:
            logger.error("STRUCTURE CHANGE DETECTED — .titreJob not found.")
            return False"""

        logger.info("Health check passed — %d offer cards found.", len(cards))
        return True

 
# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------
 
if __name__ == "__main__":
    scraper = RekruteScraper(
        max_pages=1,        # only 1 page for testing
        fetch_details=True  # fetch detail for first offer
    )
 
    # Health check first
    if not scraper.health_check():
        print("ERROR: Rekrute structure has changed — check selectors.")
        exit(1)
 
    offers = scraper.scrape()
 
    print(f"\n{'='*55}")
    print(f"  Results : {len(offers)} offers collected")
    print(f"{'='*55}")
 
    if offers:
        first = offers[2]
        print(f"\n  Title       : {first['titre_brut']}")
        print(f"  Company     : {first['entreprise']}")
        print(f"  City        : {first['ville_brute']}")
        print(f"  Contract    : {first['type_contrat']}")
        print(f"  Experience  : {first['niveau_experience']}")
        print(f"  Sector      : {first['secteur_activite']}")
        print(f"  Skills      : {first['competences_brutes'][:5]}")
        print(f"  Description : {first['description'][:150]}...")
        print(f"  ID hash     : {first['id_hash']}")
        print(f"  URL         : {first['url_offre']}")
