import hashlib
from datetime import datetime
from services.ingestion.skill_extraction.dict_matcher import extract_skills_from_text
import os
import json
import logging
import requests
import time


logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"



_last_groq_call = 0.0  # timestamp du dernier appel Groq

def call_groq_with_retry(payload: dict, headers: dict, max_retries: int = 3) -> str:
    global _last_groq_call

    # Garantit minimum 2s entre chaque appel
    elapsed = time.time() - _last_groq_call
    if elapsed < 2.0:
        time.sleep(2.0 - elapsed)

    for attempt in range(max_retries):
        try:
            _last_groq_call = time.time()
            response = requests.post(
                GROQ_URL,
                json=payload,
                headers=headers,
                timeout=15
            )
            if response.status_code == 429:
                wait = 3 * (2 ** attempt)  # 3s, 6s, 12s
                logger.warning(
                    "Groq 429 — retry %d/%d après %ds",
                    attempt + 1, max_retries, wait
                )
                time.sleep(wait)
                continue

            response.raise_for_status()
            return (
                response.json()
                ["choices"][0]
                ["message"]["content"]
                .strip()
            )

        except requests.exceptions.RequestException as e:
            logger.warning("Groq request error attempt %d: %s", attempt + 1, e)
            time.sleep(3 * (2 ** attempt))

    raise Exception("Groq max retries exceeded")

def enrich_with_llm(
    titre: str,
    description: str,
    competences_dict: list[str]
) -> dict:

    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — skipping LLM enrichment")
        return {"competences_llm": [], "langues": [], "qualites_pro": []}

    prompt = f"""
        Tu es un système d'extraction d'information pour des offres d'emploi.

        Ta mission : extraire UNIQUEMENT les informations présentes dans le texte.
        Tu ne dois rien inventer, rien déduire.

        #######################
        TEXTE À ANALYSER
        #######################

        Titre:
        {titre}

        Description:
        {description[:2000]}

        Compétences déjà détectées (NE PAS répéter) :
        {competences_dict if competences_dict else "aucune"}

        #######################
        MISSION
        #######################

        Extraire 3 catégories UNIQUEMENT :

        1. competences
        - Technologies, outils, frameworks, méthodes (ex: Python, Spark, Agile, Docker)
        - PAS de langues humaines
        - Normaliser en minuscules (ex: "Python" → "python")

        2. langues
        - UNIQUEMENT langues humaines explicitement mentionnées
        - Extraire TOUTES les langues présentes dans une même phrase
        - IMPORTANT : ne jamais choisir une seule langue dans une liste implicite

        - Les séparateurs suivants doivent être traités comme des séparateurs de langues :
        "et", "ou", "et/ou", "/", ","

        - Exemple CRITIQUE :
        "une bonne compréhension du français et/ou de l'espagnol"
        → ["français", "espagnol"]

        - Exemple :
        "anglais courant exigé, arabe souhaité"
        → ["anglais", "arabe"]

        3. qualites_pro
        - soft skills uniquement (ex: rigueur, autonomie, esprit d’équipe, communication)
        - pas de compétences techniques

        #######################
        RÈGLES STRICTES
        #######################

        - Utilise UNIQUEMENT les informations présentes dans le texte
        - Ne déduis rien
        - Ne reformule pas de façon libre
        - Pas de doublons
        - Réponse en JSON STRICT uniquement
        - Si une catégorie est vide → []

        #######################
        FORMAT DE SORTIE OBLIGATOIRE
        #######################

        {{
        "competences": [],
        "langues": [],
        "qualites_pro": []
        }}

        #######################
        EXEMPLES
        #######################

        Texte: "Maîtrise de Python, Spark et Hadoop"
        → competences: ["python", "spark", "hadoop"]

        Texte: "Bonne compréhension du français et de l'espagnol"
        → langues: ["français", "espagnol"]

        Texte: "Esprit d'équipe, rigueur et autonomie"
        → qualites_pro: ["esprit d'équipe", "rigueur", "autonomie"]

        #######################
        IMPORTANT FINAL
        #######################
        Réponds UNIQUEMENT avec le JSON. Aucun texte avant ou après.
        """
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Tu es un extracteur d'informations JSON. "
                    "Tu réponds TOUJOURS avec un JSON valide uniquement, "
                    "sans markdown, sans explication."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 400,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }

    try:

        raw_text = call_groq_with_retry(payload, headers)

        # Log pour débugger ce que le LLM retourne réellement
        logger.debug("LLM raw response for '%s' : %s", titre, raw_text)

        # Nettoyage backticks
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        result   = json.loads(raw_text)

        enriched = {
            "competences_llm": result.get("competences", []),
            "langues":         result.get("langues", []),
            "qualites_pro":    result.get("qualites_pro", []),
        }

        logger.info(
            "LLM enrichment for '%s' → +%d skills | %d langues | %d qualites",
            titre,
            len(enriched["competences_llm"]),
            len(enriched["langues"]),
            len(enriched["qualites_pro"]),
        )

        return enriched

    except json.JSONDecodeError as e:
        logger.warning("LLM JSON parse error : %s | raw : %s", e, raw_text)
        return {"competences_llm": [], "langues": [], "qualites_pro": []}
    except Exception as e:
        logger.warning("LLM enrichment failed : %s", e)
        return {"competences_llm": [], "langues": [], "qualites_pro": []}

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