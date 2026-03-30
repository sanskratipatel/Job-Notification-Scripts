"""Foundit.in (formerly Monster India) scraper."""

import logging
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

BASE_URL = "https://www.foundit.in/srp/results"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.foundit.in/",
}

# Foundit API endpoint (used by their frontend)
API_URL = "https://www.foundit.in/middleware/jobsearch/search"


def scrape(keyword: str = "python backend developer", location: str = "India", **_) -> list[dict]:
    jobs = []

    # Try their search API first
    time.sleep(random.uniform(1.5, 2.5))
    try:
        params = {
            "query": keyword,
            "location": location if location.lower() != "india" else "",
            "experienceRanges": "0~2",   # 0-2 years experience
            "sort": "1",                  # sort by date
            "limit": 25,
            "start": 0,
        }
        api_headers = {**HEADERS, "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}
        resp = requests.get(API_URL, params=params, headers=api_headers, timeout=20)

        if resp.status_code == 200 and "application/json" in resp.headers.get("Content-Type", ""):
            data = resp.json()
            for j in data.get("jobSearchResponse", {}).get("data", []):
                salary = j.get("salary", "Not disclosed") or "Not disclosed"
                exp = j.get("experienceRange", "0-2 years") or "0-2 years"
                jobs.append(normalize_job(
                    title=j.get("jobTitle", ""),
                    company=j.get("companyName", "Unknown"),
                    location=j.get("location", location),
                    salary=salary,
                    experience=exp,
                    url=f"https://www.foundit.in/job/{j.get('jobId', '')}",
                    source="Foundit",
                    skills=", ".join(j.get("keySkills", [])[:6]),
                ))
            if jobs:
                logger.info("Foundit: found %d jobs via API for '%s'", len(jobs), keyword)
                return jobs
    except Exception as e:
        logger.debug("Foundit API failed: %s", e)

    # HTML fallback
    try:
        params = {
            "query": keyword,
            "locations": location,
            "experience": "0,2",
        }
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            logger.warning("Foundit: HTTP %d", resp.status_code)
            return jobs

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("div", class_=re.compile(r"card-apply-content|jobCard|job-card-container"))

        for card in cards:
            try:
                title_tag = card.find("h3") or card.find("a", class_=re.compile(r"job-title|title"))
                company_tag = card.find("span", class_=re.compile(r"company|comp"))
                loc_tag = card.find("span", class_=re.compile(r"location|loc"))
                salary_tag = card.find("span", class_=re.compile(r"salary|sal"))
                exp_tag = card.find("span", class_=re.compile(r"experience|exp"))
                link_tag = card.find("a", href=re.compile(r"/job/"))

                if not title_tag:
                    continue

                href = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""
                if href and not href.startswith("http"):
                    href = "https://www.foundit.in" + href

                jobs.append(normalize_job(
                    title=title_tag.get_text(strip=True),
                    company=company_tag.get_text(strip=True) if company_tag else "Unknown",
                    location=loc_tag.get_text(strip=True) if loc_tag else location,
                    salary=salary_tag.get_text(strip=True) if salary_tag else "Not disclosed",
                    experience=exp_tag.get_text(strip=True) if exp_tag else "0-2 years",
                    url=href or BASE_URL,
                    source="Foundit",
                ))
            except Exception as e:
                logger.debug("Foundit card parse error: %s", e)

    except Exception as e:
        logger.warning("Foundit HTML fallback failed: %s", e)

    logger.info("Foundit: found %d jobs for '%s'", len(jobs), keyword)
    return jobs
