"""Internshala jobs scraper (good for 0-2 year experience roles)."""

import logging
import time
import random
import requests
from bs4 import BeautifulSoup
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

SLUG_MAP = {
    "python": "python-developer-jobs",
    "backend": "backend-developer-jobs",
    "django": "python-developer-jobs",
    "fastapi": "python-developer-jobs",
    "flask": "python-developer-jobs",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Referer": "https://internshala.com/",
}


def scrape(keyword: str = "python backend", **_) -> list[dict]:
    jobs = []

    slug = "python-developer-jobs"
    for k, v in SLUG_MAP.items():
        if k in keyword.lower():
            slug = v
            break

    urls = list({
        f"https://internshala.com/jobs/{slug}",
        "https://internshala.com/jobs/backend-developer-jobs",
    })

    for url in urls:
        time.sleep(random.uniform(1.5, 2.5))
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                logger.warning("Internshala: HTTP %d for %s", resp.status_code, url)
                continue
        except Exception as e:
            logger.warning("Internshala: request failed: %s", e)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("div", class_="individual_internship")

        for card in cards:
            try:
                # Title
                title_tag = card.find("a", class_="job-title-href") or card.find("a", id="job_title")
                # Company
                company_tag = card.find("p", class_="company-name")
                # Location
                loc_tag = card.find("p", class_="locations")
                # Salary – desktop span has the cleaner value
                sal_span = card.find("span", class_="desktop")
                if not sal_span:
                    sal_span = card.find("span", class_="mobile")
                # Link
                href = card.get("data-href", "")
                if href:
                    url_full = f"https://internshala.com{href}"
                elif title_tag and title_tag.has_attr("href"):
                    url_full = f"https://internshala.com{title_tag['href']}"
                else:
                    url_full = "https://internshala.com"

                if not title_tag:
                    continue

                loc_text = ""
                if loc_tag:
                    loc_text = loc_tag.get_text(" ", strip=True).replace("Map Pin", "").strip()

                salary = sal_span.get_text(strip=True) if sal_span else "Not disclosed"

                jobs.append(normalize_job(
                    title=title_tag.get_text(strip=True),
                    company=company_tag.get_text(strip=True) if company_tag else "Unknown",
                    location=loc_text or "India",
                    salary=salary,
                    experience="0-2 years",
                    url=url_full,
                    source="Internshala",
                ))
            except Exception as e:
                logger.debug("Internshala card parse error: %s", e)

    # Deduplicate by URL within this scraper
    seen = set()
    unique = []
    for j in jobs:
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)

    logger.info("Internshala: found %d jobs", len(unique))
    return unique
