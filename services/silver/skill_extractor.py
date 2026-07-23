

import logging
import re
import os
import time
import requests
import json
from dict_matcher import TECH_SKILLS

logger = logging.getLogger(__name__)

SKILLS_WITH_SPECIAL_CHARS = ["c++", "c#", "pl/sql", "ci/cd", "pub/sub", "rest api", "api rest"]

def extract_skills_from_text(text: str) -> list[str]:
    if not text:
        return []

    text_lower = text.lower()
    found = []

    for skill in TECH_SKILLS:
        skill_lower = skill.lower()

        if skill_lower in SKILLS_WITH_SPECIAL_CHARS:
            # Simple substring match for skills with special chars
            # Surrounded by non-alphanumeric or start/end of string
            pattern = r"(?<![a-z0-9])" + re.escape(skill_lower) + r"(?![a-z0-9])"
        else:
            # Word boundary match for normal skills
            pattern = r"\b" + re.escape(skill_lower) + r"\b"

        if re.search(pattern, text_lower):
            found.append(skill)

    return found


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL     = os.getenv("GROQ_URL")

_last_groq_call = 0.0  # timestamp of the last groq call

def call_groq_with_retry(payload: dict, headers: dict, max_retries: int = 3) -> str:
    global _last_groq_call

    # minimum 2s between every call
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