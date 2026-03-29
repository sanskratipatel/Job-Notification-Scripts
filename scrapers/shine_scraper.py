"""Shine.com scraper using their Next.js rendered HTML."""

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
    "Referer": "https://www.shine.com/",
}

SEARCH_URL = "https://www.shine.com/job-search/{slug}"


def scrape(keyword: str = "python backend developer", **_) -> list[dict]:
    jobs = []
    slug = re.sub(r"\s+", "-", keyword.lower().strip()) + "-jobs"
    url = SEARCH_URL.format(slug=slug)

    time.sleep(random.uniform(1.5, 2.5))
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            logger.warning("Shine: HTTP %d for %s", resp.status_code, url)
            return jobs
    except Exception as e:
        logger.warning("Shine: request failed: %s", e)
        return jobs

    soup = BeautifulSoup(resp.text, "html.parser")

    # Shine uses Next.js CSS modules – class names have hashes like jobCardNova_bigCard__W2xn3
    cards = soup.find_all("div", class_=re.compile(r"jobCardNova_bigCard__"))

    for card in cards:
        try:
            # Title & URL from <h3> → <a>
            title_tag = card.find("h3", class_=re.compile(r"bigCardTopTitleHeading"))
            link_tag = title_tag.find("a") if title_tag else None

            # Company
            company_tag = card.find("span", class_=re.compile(r"bigCardTopTitleName"))

            # Location
            loc_tag = card.find("span", class_=re.compile(r"bigCardLocation"))

            # Experience
            exp_tag = card.find("span", class_=re.compile(r"bigCardExp|bigCardExperience"))

            # Salary
            salary_tag = card.find("span", class_=re.compile(r"bigCardSalary|bigCardCtc"))

            # Skills
            skills_div = card.find("div", class_=re.compile(r"bigCardBottomSkills"))
            skills = ""
            if skills_div:
                skill_tags = skills_div.find_all("span")
                skills = ", ".join(s.get_text(strip=True) for s in skill_tags[:6] if s.get_text(strip=True))

            # Posted date
            posted_tag = card.find("span", class_=re.compile(r"postedData"))

            if not title_tag:
                continue

            href = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""

            jobs.append(normalize_job(
                title=title_tag.get_text(strip=True),
                company=company_tag.get_text(strip=True) if company_tag else "Unknown",
                location=loc_tag.get_text(strip=True) if loc_tag else "India",
                salary=salary_tag.get_text(strip=True) if salary_tag else "Not disclosed",
                experience=exp_tag.get_text(strip=True) if exp_tag else "0-2 years",
                url=href or "https://www.shine.com",
                source="Shine",
                posted=posted_tag.get_text(strip=True) if posted_tag else "",
                skills=skills,
            ))
        except Exception as e:
            logger.debug("Shine card parse error: %s", e)

    logger.info("Shine: found %d jobs for '%s'", len(jobs), keyword)
    return jobs
