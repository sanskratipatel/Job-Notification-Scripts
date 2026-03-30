"""Glassdoor India job scraper."""

import logging
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.glassdoor.co.in/",
}


def scrape(keyword: str = "python backend developer", location: str = "India", **_) -> list[dict]:
    jobs = []
    kw_slug = re.sub(r"\s+", "-", keyword.strip())
    loc_slug = re.sub(r"\s+", "-", location.strip())
    url = f"https://www.glassdoor.co.in/Job/{loc_slug}-{kw_slug}-jobs-SRCH_IL.0,5_IN115_KO6,{6+len(kw_slug)}.htm"

    time.sleep(random.uniform(2, 3.5))
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            logger.warning("Glassdoor: HTTP %d", resp.status_code)
            return jobs
    except Exception as e:
        logger.warning("Glassdoor: request failed: %s", e)
        return jobs

    soup = BeautifulSoup(resp.text, "html.parser")

    # Glassdoor job cards
    cards = soup.find_all("li", class_=re.compile(r"JobsList_jobListItem|react-job-listing"))
    if not cards:
        cards = soup.find_all("div", attrs={"data-test": "jobListing"})
    if not cards:
        # fallback: find all job links
        links = soup.find_all("a", attrs={"data-test": "job-title"})
        for link in links:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if href and not href.startswith("http"):
                href = "https://www.glassdoor.co.in" + href
            if title:
                jobs.append(normalize_job(
                    title=title, company="Unknown", location=location,
                    salary="Not disclosed", experience="0-2 years",
                    url=href, source="Glassdoor",
                ))
        logger.info("Glassdoor: found %d jobs (link fallback)", len(jobs))
        return jobs

    for card in cards:
        try:
            title_tag = card.find("a", attrs={"data-test": "job-title"}) or card.find("a", class_=re.compile(r"jobTitle|job-title"))
            company_tag = card.find("span", attrs={"data-test": "employer-name"}) or card.find("div", class_=re.compile(r"employerName"))
            loc_tag = card.find("div", attrs={"data-test": "emp-location"}) or card.find("span", class_=re.compile(r"location|loc"))
            salary_tag = card.find("span", attrs={"data-test": "detailSalary"}) or card.find("div", class_=re.compile(r"salary"))

            if not title_tag:
                continue

            href = title_tag.get("href", "")
            if href and not href.startswith("http"):
                href = "https://www.glassdoor.co.in" + href

            jobs.append(normalize_job(
                title=title_tag.get_text(strip=True),
                company=company_tag.get_text(strip=True) if company_tag else "Unknown",
                location=loc_tag.get_text(strip=True) if loc_tag else location,
                salary=salary_tag.get_text(strip=True) if salary_tag else "Not disclosed",
                experience="0-2 years",
                url=href or "https://www.glassdoor.co.in",
                source="Glassdoor",
            ))
        except Exception as e:
            logger.debug("Glassdoor card parse error: %s", e)

    logger.info("Glassdoor: found %d jobs for '%s'", len(jobs), keyword)
    return jobs
