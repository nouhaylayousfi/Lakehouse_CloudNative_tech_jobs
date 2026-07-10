"""
llm_filter.py
-------------
Shared LLM-based tech relevance filter for all Bronze layer scrapers.

Classifies a job offer as tech/non-tech using Groq before ingestion.
This is a Bronze-layer concern: filtering irrelevant offers early avoids
polluting the lakehouse with noise.

Usage:
    from services.ingestion.shared.llm_filter import is_tech_offer_llm
"""

import logging

import requests

from config.settings import GROQ_API_KEY, GROQ_URL

logger = logging.getLogger(__name__)


def is_tech_offer_llm(titre: str, secteur: str = "") -> bool:
    """
    Classifies a job offer as tech/non-tech using Groq (llama-3.1-8b-instant).
    Returns True (tech) by default if the API is unavailable.

    Args:
        titre:   Job title
        secteur: Sector or summary hint (optional)

    Returns:
        True if the offer is tech-related, False otherwise
    """
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — skipping LLM filter")
        return True

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
            timeout=10,
        )
        response.raise_for_status()
        answer = (
            response.json()["choices"][0]["message"]["content"]
            .strip()
            .upper()
        )
        logger.debug("LLM [%s] → %s", titre, answer)
        return answer.startswith("OUI")

    except Exception as e:
        logger.warning("Groq classification failed '%s': %s", titre, e)
        return True