"""
http.py
-------
Shared HTTP helper for all Bronze layer scrapers.

Usage:
    from services.ingestion.shared.http import fetch_page
"""

import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def fetch_page(url: str, headers: dict | None = None) -> BeautifulSoup | None:
    """
    Fetches a URL and returns a BeautifulSoup object.
    Returns None on any HTTP or network failure.

    Args:
        url:     The URL to fetch
        headers: Optional override headers (merged with defaults)

    Returns:
        BeautifulSoup object or None
    """
    merged_headers = {**HEADERS, **(headers or {})}

    try:
        response = requests.get(url, headers=merged_headers, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error fetching %s : %s", url, e)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Network error fetching %s : %s", url, e)
        return None