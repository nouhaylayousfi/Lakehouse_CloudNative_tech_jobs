

import logging
import re
import os
import time
import requests
import json
from services.silver.dict_matcher import TECH_SKILLS

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
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

logger.info("GROQ_API_KEY présent : %s", bool(GROQ_API_KEY))
logger.info("Variables d'env visibles (extrait) : %s", 
            {k: v for k, v in os.environ.items() if "GROQ" in k or "SPARK" in k})

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
        return {"competences_brutes": [], "langues": [], "qualites_pro": []}

    prompt = f"""
        You are an information extraction system for job postings (job title + description).

        Your task: extract ONLY information that is explicitly present in the text below.
        Never invent, never infer, never guess.

        #######################
        TEXT TO ANALYZE
        #######################

        Job title:
        {titre}

        Description:
        {description[:6000]}

        Skills already detected (DO NOT repeat them):
        {competences_dict if competences_dict else "none"}

        #######################
        TASK
        #######################

        Extract EXACTLY 3 categories. Nothing else.

        1. "competences"
        - Technical skills only: technologies, tools, frameworks, methodologies,
        programming languages, software, certifications
        (e.g. Python, Spark, Agile, Docker, AWS, Scrum)
        - Do NOT include human/spoken languages here
        - Normalize to lowercase (e.g. "Python" → "python")
        - Do not repeat any skill already listed in "Skills already detected" above

        2. "langues"
        - ONLY human/spoken languages explicitly mentioned (e.g. French, English, Arabic, Spanish)
        - Keep the language names in the SAME language as the source text
        (e.g. "français", "anglais" — do NOT translate them to English)
        - Extract ALL languages present in the same sentence or list, never just one
        - Treat these as separators between multiple languages:
        "et", "ou", "et/ou", "/", ","
        - If a proficiency level is mentioned (e.g. "anglais courant"), extract only the
        language name, not the level

        CRITICAL example:
        Text: "une bonne compréhension du français et/ou de l'espagnol"
        → ["français", "espagnol"]

        Example:
        Text: "anglais courant exigé, arabe souhaité"
        → ["anglais", "arabe"]

        3. "qualites_pro"
        - Soft skills of the CANDIDATE only (personal/behavioral qualities expected from
        the applicant), e.g. rigueur, autonomie, esprit d'équipe, communication,
        sens de l'organisation, force de proposition
        - Keep them in the SAME language as the source text (do not translate to English)
        - Do NOT include technical skills here
        - STRICTLY EXCLUDE any sentence about the company's own policies, values, or
        commitments, even if it uses similar vocabulary. This includes (non-exhaustive):
        diversity, inclusion, equal opportunity ("égalité des chances"), disability
        policy ("RQTH", "handicap"), gender equality, non-discrimination, CSR/RSE
        statements, employer branding phrases ("nous rejoindre", "notre culture
        d'entreprise", "pourquoi nous choisir")
        - These are statements ABOUT the company, not qualities expected FROM the
        candidate — never extract them as qualites_pro

        Example to EXTRACT:
        Text: "Esprit d'équipe, rigueur et autonomie sont attendus"
        → qualites_pro: ["esprit d'équipe", "rigueur", "autonomie"]

        Example to NOT extract (company policy, not a candidate quality):
        Text: "Notre entreprise s'engage pour la diversité, l'inclusion et l'égalité
        des chances, et étudie toutes les candidatures y compris celles de personnes
        en situation de handicap"
        → qualites_pro: []

        #######################
        STRICT RULES
        #######################

        - Use ONLY information explicitly present in the text
        - Never infer, never guess, never complete a partial list with assumptions
        - Never paraphrase or rewrite terms freely — extract them as close to the
        original wording as possible
        - No duplicates within a category
        - If a category has nothing to extract → return an empty array []
        - Output values in "langues" and "qualites_pro" stay in the original language
        of the source text (French). Only "competences" is normalized to lowercase.
        - Respond with STRICT JSON only — no markdown, no code fences, no explanation,
        no text before or after the JSON object

        #######################
        REQUIRED OUTPUT FORMAT
        #######################

        {{
        "competences": [],
        "langues": [],
        "qualites_pro": []
        }}

        #######################
        FULL EXAMPLES
        #######################

        Text: "Maîtrise de Python, Spark et Hadoop"
        → competences: ["python", "spark", "hadoop"]

        Text: "Bonne compréhension du français et de l'espagnol"
        → langues: ["français", "espagnol"]

        Text: "Esprit d'équipe, rigueur et autonomie"
        → qualites_pro: ["esprit d'équipe", "rigueur", "autonomie"]

        Text: "Nous encourageons la diversité et l'égalité des chances au sein de nos équipes"
        → qualites_pro: []

        #######################
        FINAL REMINDER
        #######################
        Respond with the JSON object ONLY. No text before or after it.
        """
    payload = {
        "model": "llama-3.3-70b-versatile",
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
        "max_tokens": 800,
        
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }

    try:

        raw_text = call_groq_with_retry(payload, headers)
        print("RAW LLM RESPONSE:", raw_text)  # debug temporaire

        # Log pour débugger ce que le LLM retourne réellement
        logger.debug("LLM raw response for '%s' : %s", titre, raw_text)

        # Nettoyage backticks
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        result   = json.loads(raw_text)

        enriched = {
            "competences_brutes": result.get("competences", []),
            "langues":         result.get("langues", []),
            "qualites_pro":    result.get("qualites_pro", []),
        }

        logger.info(
            "LLM enrichment for '%s' → +%d skills | %d langues | %d qualites",
            titre,
            len(enriched["competences_brutes"]),
            len(enriched["langues"]),
            len(enriched["qualites_pro"]),
        )

        return enriched

    except json.JSONDecodeError as e:
        logger.warning("LLM JSON parse error : %s | raw : %s", e, raw_text)
        return {"competences_brutes": [], "langues": [], "qualites_pro": []}
    except Exception as e:
        logger.warning("LLM enrichment failed : %s", e)
        return {"competences_brutes": [], "langues": [], "qualites_pro": []}