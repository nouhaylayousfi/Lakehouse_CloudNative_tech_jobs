import hashlib
from datetime import datetime
import os
import json
import requests
import time

def map_france_travail(raw: dict) -> dict: 
    """Maps raw France Travail API response to unified schema."""

    lieu        = raw.get("lieuTravail", {})
    salaire     = raw.get("salaire", {})
    entreprise  = raw.get("entreprise", {})
    description = raw.get("description", "")

    # Skills — "exigence" S=souhaitée, E=exigée — we keep both label and level
    competences = [
        {
            "libelle": c.get("libelle", ""),
            "exigence": c.get("exigence", "")
        }
        for c in raw.get("competences", [])
    ]

    #competences_texte = extract_skills_from_text(description)

    # Soft skills - optional fiels , not always present 
    qualites = [ 
        q.get("libelle", "")
        for q in raw.get("qualitesProfessionnelles", [])
    ]

    #Languages required - also optional 
    langues = [ 
        { 
            "libelle": l.get("libelle", ""), 
            "exigence" : l.get("exigence", "")
        }
        for l in raw.get("langues", [])
    ]

    # Salary — field exists but libelle is NOT guaranteed , sometimes only "commentaire" is present, sometimes nothing
    salaire_brut = salaire.get("libelle") or salaire.get("commentaire") or ""

    #Unique hash ID 
    id_source = raw.get("id", "")
    id_hash   = hashlib.md5(f"france_travail_{id_source}".encode()).hexdigest()

    return {
        #Identification 
        "id_hash":              id_hash,
        "id_source":            id_source,
        "source":               "france_travail",
        "pays":                 "FR",

        # Job
        "titre_brut":           raw.get("intitule", ""),
        "description":          raw.get("description", ""),
        "type_contrat":         raw.get("typeContratLibelle", ""),
        "nature_contrat":       raw.get("natureContrat", ""),
        "niveau_experience":    raw.get("experienceLibelle", ""),
        "qualification":        raw.get("qualificationLibelle", ""),

        # Location
        "ville_brute":          lieu.get("libelle", ""),
        "code_postal":          lieu.get("codePostal", ""),
        "latitude":             lieu.get("latitude"),
        "longitude":            lieu.get("longitude"),

        # Company
        "entreprise":           entreprise.get("nom", ""),
        "secteur_activite":     raw.get("secteurActiviteLibelle", ""),
        "tranche_effectif":     raw.get("trancheEffectifEtab", ""),

        # Salary
        "salaire_brut":         salaire_brut,
        "salaire_min":          None,
        "salaire_max":          None,

        # Skills
        "competences_rome":     competences,
        "competences_brutes":   [],
        "qualites_pro":         qualites,
        "langues":              langues,

        #ROME reference 
        "code_rome":            raw.get("romeCode", ""),
        "libelle_rome":         raw.get("romeLibelle", ""),
        "appellation_rome":     raw.get("appellationlibelle", ""),

        # Metadata
        "date_publication":     raw.get("dateCreation", ""),
        "date_actualisation":   raw.get("dateActualisation", ""),
        "date_ingestion":       datetime.utcnow().isoformat(),
        "url_offre":            raw.get("origineOffre", {}).get("urlOrigine", ""),
        "nombre_postes":        raw.get("nombrePostes", 1),
        "langue":               "fr",
    }


def map_rekrute(raw: dict) -> dict:
    """Maps raw Rekrute scraper output to unified schema."""

    # Generate unique hash from URL
    url       = raw.get("url", "")
    id_hash   = hashlib.md5(f"rekrute_{url}".encode()).hexdigest()

    # Skills extracted from description via dict_matcher (called separately)
    # For now we store the raw description — extraction happens in Silver layer
    description = raw.get("description", "")

    return {
        # Identification
        "id_hash":            id_hash,
        "id_source":          url,
        "source":             "rekrute",
        "pays":               "MA",

        # Job
        "titre_brut":         raw.get("titre_brut", ""),
        "description":        description,
        "type_contrat":       raw.get("contract_type", ""),
        "niveau_experience":  " | ".join(raw.get("experience", [])),
        "education":          " | ".join(raw.get("education", [])),

        # Location
        "ville_brute":        raw.get("ville_brute", ""),
        "code_postal":        None,
        "latitude":           None,
        "longitude":          None,

        # Company
        "entreprise":         raw.get("company_name", ""),
        "secteur_activite":   " | ".join(raw.get("secteur", [])),
        "tranche_effectif":   None,

        # Salary — not available on Rekrute
        "salaire_brut":       None,
        "salaire_min":        None,
        "salaire_max":        None,

        # Skills — extracted from description text
        "competences_brutes": [],
        # ^ will be populated by dict_matcher in Silver layer

        "qualites_pro":       [],
        "langues":            [],

        # ROME — not available on Rekrute
        "code_rome":          None,
        "libelle_rome":       None,
        "appellation_rome":   None,

        # Remote
        "remote":             raw.get("remote", ""),

        # Metadata
        "date_publication":   raw.get("date_publication", ""),
        "date_actualisation": None,
        "date_ingestion":     datetime.utcnow().isoformat(),
        "url_offre":          url,
        "nombre_postes":      raw.get("nombre_postes", ""),
        "langue":             "fr",
    }


def map_adzuna(raw: dict) -> dict:
    """Maps raw Adzuna API response to unified schema."""

    # --- Location ---
    # Adzuna returns location as a hierarchy list:
    # ["France", "Hauts-De-France", "Nord", "Lille", "Villeneuve-d'Ascq"]
    location     = raw.get("location", {})
    area         = location.get("area", [])
    display_name = location.get("display_name", "")
    ville_brute  = display_name if display_name else (area[-1] if area else "")
    region       = area[1]  if len(area) >= 2 else ""

    # --- Salary ---
    # salary_is_predicted = "1" means Adzuna estimated it — not declared by employer
    # salary_is_predicted = "0" means no salary info at all
    salary_min       = raw.get("salary_min")
    salary_max       = raw.get("salary_max")
    salary_predicted = raw.get("salary_is_predicted", "0") == "1"
    # ^ True = estimated by Adzuna algorithm, False = not available

    # --- Company ---
    company = raw.get("company", {})

    # --- ID ---
    id_source = raw.get("id", "")
    id_hash   = hashlib.md5(f"adzuna_{id_source}".encode()).hexdigest()

    description = raw.get("description", "")
    titre       = raw.get("title", "")

    """# Extract skills from title + truncated description
    competences = extract_skills_from_text(f"{titre} {description}")"""


    return {
        # Identification
        "id_hash":            id_hash,
        "id_source":          id_source,
        "source":             "adzuna",
        "pays":               "FR",

        # Job
        "titre_brut":         raw.get("title", ""),
        "description":        raw.get("description", ""),
        # ^ Truncated to ~200 chars by Adzuna — no full text available

        "type_contrat":       "",
        # ^ Not available in Adzuna API

        "niveau_experience":  "",
        # ^ Not available in Adzuna API

        # Location
        "ville_brute":        ville_brute,
        "region":             region,
        "latitude":           raw.get("latitude"),
        "longitude":          raw.get("longitude"),
        # ^ GPS coordinates available — useful for geo analysis

        # Company
        "entreprise":         company.get("display_name", ""),
        "secteur_activite":   raw.get("category", {}).get("label", ""),
        "tranche_effectif":   None,

        # Salary
        "salaire_brut":       None,
        "salaire_min":        salary_min,
        "salaire_max":        salary_max,
        "salaire_est":        salary_predicted,
        # ^ Flag : True = Adzuna estimation, False = not available

        # Skills — extracted from description via dict_matcher in Silver
        "competences_brutes": [],
        "qualites_pro":       [],
        "langues":            [],

        # ROME — not available in Adzuna
        "code_rome":          None,
        "libelle_rome":       None,
        "appellation_rome":   None,

        # Metadata
        "date_publication":   raw.get("created", ""),
        "date_actualisation": None,
        "date_ingestion":     datetime.utcnow().isoformat(),
        "url_offre":          raw.get("redirect_url", ""),
        "nombre_postes":      None,
        "langue":             "fr",
    }

def map_emploima(raw: dict) -> dict:
    """Maps raw Emploi.ma scraper output to unified schema."""
    url         = raw.get("url", "")
    id_hash     = hashlib.md5(f"emploima_{url}".encode()).hexdigest()
    description = raw.get("description", "")
    titre       = raw.get("titre_brut", "")

    """# 1. Dict matcher — extraction technique
    competences_dict = extract_skills_from_text(f"{titre} {description}")

    # 2. LLM enrichment — Complete what the dictionary missed.
    enriched = enrich_with_llm(titre, description, competences_dict)

    # 3. Merge without duplicates.
    competences_dict_lower = {c.lower() for c in competences_dict}
    competences_llm_new    = [
        c for c in enriched["competences_llm"]
        if c.lower() not in competences_dict_lower
    ]
    competences_finales = competences_dict + competences_llm_new"""

    return {
        # Identification
        "id_hash":            id_hash,
        "id_source":          url,
        "source":             "emploima",
        "pays":               "MA",

        # Job
        "titre_brut":         titre,
        "description":        description,
        "type_contrat":       raw.get("type_contrat", ""),
        "niveau_experience":  raw.get("experience", ""),
        "education":          raw.get("education", ""),

        # Location
        "ville_brute":        raw.get("ville_brute", ""),
        "region":             "",
        # ^ not available on Emploi.ma
        "latitude":           None,
        "longitude":          None,

        # Company
        "entreprise":         raw.get("entreprise", ""),
        "secteur_activite":   raw.get("secteur", ""),
        "tranche_effectif":   None,

        # Salary — not available on Emploi.ma
        "salaire_brut": raw.get("salaire_brut", None),
        "salaire_min":        None,
        "salaire_max":        None,
        "salaire_est":        False,

        # ROME — not available
        "code_rome":          None,
        "libelle_rome":       None,
        "appellation_rome":   None,

        # Remote — not available on Emploi.ma
        "remote":       raw.get("remote", ""),

        # Metadata
        "date_publication": raw.get("date_publication", ""),
        "date_actualisation": None,
        "date_ingestion":     datetime.utcnow().isoformat(),
        "url_offre":          url,
        "nombre_postes":      raw.get("nb_postes"),
        "langue":             "fr",

        # Skills
        "competences_brutes": [],
        "qualites_pro":       [],
        "langues":            [],
    }

def map_indeed(raw: dict, country: str = "MA") -> dict:
    """Maps raw Apify Indeed scraper output to unified schema."""

    url     = raw.get("url", "")
    id_hash = hashlib.md5(f"indeed_{url}".encode()).hexdigest()

    # jobType is a list e.g. ["Full-time"]
    job_types    = raw.get("jobType") or []
    type_contrat = " | ".join(job_types)

    # salary
    salaire_brut = raw.get("salary") or ""

    # company size from companyInfo
    company_info     = raw.get("companyInfo") or {}
    tranche_effectif = None
    size = company_info.get("companySize")
    if size and size.get("min") and size.get("max"):
        tranche_effectif = f"{size['min']}-{size['max']}"

    # date — keep YYYY-MM-DD only
    date_pub = ""
    raw_date = raw.get("postingDateParsed") or raw.get("postedAt") or ""
    if raw_date and "T" in raw_date:
        date_pub = raw_date[:10]

    # source tag differs by country
    source = "indeed_ma" if country == "MA" else "indeed_fr"
    pays   = country  # "MA" or "FR"

    return {
        # Identification
        "id_hash":            id_hash,
        "id_source":          raw.get("id", url),
        "source":             source,
        "pays":               pays,

        # Job
        "titre_brut":         raw.get("positionName", ""),
        "description":        raw.get("description", ""),
        "type_contrat":       type_contrat,
        "niveau_experience":  "",
        "education":          "",

        # Location
        "ville_brute":        raw.get("location", ""),
        "code_postal":        None,
        "latitude":           None,
        "longitude":          None,

        # Company
        "entreprise":         raw.get("company", ""),
        "secteur_activite":   "",
        "tranche_effectif":   tranche_effectif,

        # Salary
        "salaire_brut":       salaire_brut,
        "salaire_min":        None,
        "salaire_max":        None,

        # Skills — extracted in Silver layer
        "competences_brutes": [],
        "qualites_pro":       [],
        "langues":            [],

        # ROME — not available on Indeed
        "code_rome":          None,
        "libelle_rome":       None,
        "appellation_rome":   None,

        # Remote
        "remote":             "",

        # Metadata
        "date_publication":   date_pub,
        "date_actualisation": None,
        "date_ingestion":     datetime.utcnow().isoformat(),
        "url_offre":          url,
        "nombre_postes":      "",
        "langue":             "fr",
    }