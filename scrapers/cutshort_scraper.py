"""
Cutshort.io scraper – tech-focused India job board.
Uses DuckDuckGo site search since Cutshort's API is not public.
"""

import logging
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

DDG_URL = "https://html.duckduckgo.com/html/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://duckduckgo.com/",
}


def scrape(keyword: str = "python backend", **_) -> list[dict]:
    jobs = []
    time.sleep(random.uniform(2, 3.5))

    query = f'site:cutshort.io/job "{keyword}" OR "python" OR "backend" "0-2" OR "1-2" OR "fresher"'
    try:
        data = {"q": query, "df": "m"}   # last month
        resp = requests.post(DDG_URL, data=data, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            logger.warning("Cutshort: DDG returned HTTP %d", resp.status_code)
            return jobs
    except Exception as e:
        logger.warning("Cutshort: request failed: %s", e)
        return jobs

    soup = BeautifulSoup(resp.text, "html.parser")
    results = soup.find_all("div", class_=re.compile(r"result__body"))
    seen_urls = set()

    for result in results:
        try:
            link_tag = result.find("a", class_=re.compile(r"result__a"))
            if not link_tag:
                continue

            href = link_tag.get("href", "")
            if not href:
                continue

            # Clean up DuckDuckGo redirect URLs
            if "uddg=" in href:
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                href = parsed.get("uddg", [href])[0]

            if "cutshort.io" not in href:
                continue
            if href in seen_urls:
                continue
            seen_urls.add(href)

            title_text = link_tag.get_text(strip=True)

            snippet_tag = result.find("a", class_=re.compile(r"result__snippet")) or result
            snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""

            # Extract company from title (Cutshort titles: "Job Title at Company")
            company = "See listing"
            at_match = re.search(r"\bat\s+([A-Za-z0-9][A-Za-z0-9\s&\-\.]+?)(?:\s*[-|–]|\s*$)", title_text)
            if at_match:
                company = at_match.group(1).strip()

            jobs.append(normalize_job(
                title=title_text or "Python/Backend Developer",
                company=company,
                location="India",
                salary="Not disclosed",
                experience="0-2 years",
                url=href,
                source="Cutshort",
                skills="Python, Backend",
            ))
        except Exception as e:
            logger.debug("Cutshort job parse error: %s", e)

    logger.info("Cutshort: found %d jobs for '%s'", len(jobs), keyword)
    return jobs
