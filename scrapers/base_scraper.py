"""Base scraper with shared utilities (headers, sessions, retry logic)."""

import time
import random
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Realistic browser headers to avoid bot detection
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(DEFAULT_HEADERS)
    return s


def safe_get(session: requests.Session, url: str, params=None, headers=None, timeout=15) -> requests.Response | None:
    """GET with retry + polite delay. Returns None on failure."""
    time.sleep(random.uniform(1.5, 3.5))   # polite crawling
    try:
        resp = session.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        logger.warning("Request failed for %s: %s", url, e)
        return None


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def normalize_job(
    *,
    title: str,
    company: str,
    location: str,
    salary: str,
    experience: str,
    url: str,
    source: str,
    posted: str = "",
    skills: str = "",
) -> dict:
    """Return a standard job dict used across the whole system."""
    return {
        "title": title.strip(),
        "company": company.strip(),
        "location": location.strip(),
        "salary": salary.strip(),
        "experience": experience.strip(),
        "url": url.strip(),
        "source": source,
        "posted": posted.strip(),
        "skills": skills.strip(),
    }
