"""
LinkedIn Hiring Posts scraper.
Strategy: Search DuckDuckGo for recent LinkedIn posts about Python hiring.
No auth needed – finds public posts where recruiters announce openings.
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

# Search queries to find LinkedIn hiring posts
SEARCH_QUERIES = [
    'site:linkedin.com/posts "hiring" "python" "backend" "1-2 years" OR "0-2 years" OR "fresher"',
    'site:linkedin.com/posts "we are hiring" "python developer" OR "backend developer"',
    'site:linkedin.com/posts "#hiring" "#python" "#backenddev"',
]


def _search_ddg(query: str) -> list[dict]:
    jobs = []
    time.sleep(random.uniform(2, 4))
    try:
        data = {"q": query, "df": "d2"}   # df=d2 → last 2 days
        resp = requests.post(DDG_URL, data=data, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return jobs
    except Exception as e:
        logger.debug("DDG search failed: %s", e)
        return jobs

    soup = BeautifulSoup(resp.text, "html.parser")
    results = soup.find_all("div", class_=re.compile(r"result__body|result__snippet"))

    for result in results:
        try:
            link_tag = result.find("a", class_=re.compile(r"result__url|result__a"))
            if not link_tag:
                link_tag = result.find_previous("a", class_=re.compile(r"result__a"))
            snippet_tag = result.find("a", class_=re.compile(r"result__snippet")) or result

            if not link_tag:
                continue

            href = link_tag.get("href", "")
            if not href:
                href = link_tag.get_text(strip=True)
            if "linkedin.com" not in href:
                continue

            # Clean up DuckDuckGo redirect URLs
            if "uddg=" in href:
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                href = parsed.get("uddg", [href])[0]

            snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""

            # Extract company name from snippet if possible
            company_match = re.search(r"at\s+([A-Z][A-Za-z\s&]+?)(?:\s+is|\s+are|\s+we|\.|,)", snippet)
            company = company_match.group(1).strip() if company_match else "See post"

            # Extract title hint from snippet
            title_match = re.search(
                r"(python|backend|django|fastapi|flask|api)\s+developer|developer.{0,20}(python|backend)",
                snippet, re.IGNORECASE
            )
            title = title_match.group(0).strip().title() if title_match else "Python/Backend Developer"

            jobs.append(normalize_job(
                title=f"[LinkedIn Post] {title}",
                company=company,
                location="India (see post)",
                salary="Not disclosed",
                experience="0-2 years",
                url=href,
                source="LinkedIn Posts",
                posted="Last 2 days",
                skills="Python, Backend",
            ))
        except Exception as e:
            logger.debug("LinkedIn post parse error: %s", e)

    return jobs


def scrape(**_) -> list[dict]:
    jobs = []
    seen_urls = set()

    for query in SEARCH_QUERIES:
        found = _search_ddg(query)
        for j in found:
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                jobs.append(j)

    logger.info("LinkedIn Posts: found %d hiring posts", len(jobs))
    return jobs
