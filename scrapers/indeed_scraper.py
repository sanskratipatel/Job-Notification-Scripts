"""Indeed India scraper via RSS feed – no login, no captcha."""

import logging
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

RSS_URL = "https://in.indeed.com/rss"


def _parse_salary(text: str) -> str:
    match = re.search(r"[\₹\$]?[\d,]+\s*[-–]\s*[\₹\$]?[\d,]+|[\d.]+\s*lpa", text, re.IGNORECASE)
    return match.group(0) if match else "Not disclosed"


def _parse_exp(text: str) -> str:
    match = re.search(r"\d+\s*[-–]\s*\d+\s*(?:year|yr|yrs)|[\d.]+\s*(?:year|yr)", text, re.IGNORECASE)
    return match.group(0) if match else "0-2 years"


def scrape(keyword: str = "python backend developer", location: str = "India", **_) -> list[dict]:
    jobs = []

    time.sleep(random.uniform(1.5, 2.5))
    try:
        params = {
            "q": keyword,
            "l": location if location.lower() != "india" else "",
            "fromage": 3,    # last 3 days
            "sort": "date",
        }
        resp = requests.get(
            RSS_URL,
            params=params,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/rss+xml, application/xml"},
            timeout=20,
        )
        if resp.status_code != 200:
            logger.warning("Indeed RSS: HTTP %d for '%s'", resp.status_code, keyword)
            return jobs
    except Exception as e:
        logger.warning("Indeed RSS: request failed: %s", e)
        return jobs

    soup = BeautifulSoup(resp.text, "xml" if "xml" in resp.headers.get("Content-Type","") else "html.parser")
    items = soup.find_all("item")

    for item in items:
        try:
            title = item.find("title")
            link  = item.find("link")
            desc  = item.find("description")
            # Indeed RSS puts company/location in description
            desc_text = BeautifulSoup(desc.get_text(), "html.parser").get_text() if desc else ""

            # Extract company from title: "Job Title - Company Name"
            title_text = title.get_text(strip=True) if title else ""
            parts = title_text.rsplit(" - ", 1)
            job_title = parts[0].strip() if parts else title_text
            company = parts[1].strip() if len(parts) > 1 else "Unknown"

            url = link.get_text(strip=True) if link else "https://in.indeed.com"

            jobs.append(normalize_job(
                title=job_title,
                company=company,
                location=location,
                salary=_parse_salary(desc_text),
                experience=_parse_exp(desc_text),
                url=url,
                source="Indeed",
            ))
        except Exception as e:
            logger.debug("Indeed RSS item parse error: %s", e)

    logger.info("Indeed: found %d jobs via RSS for '%s'", len(jobs), keyword)
    return jobs
