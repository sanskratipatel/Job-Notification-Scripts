"""Wellfound (AngelList Talent) scraper – good for startup jobs."""

import logging
import re
from .base_scraper import make_session, safe_get, parse_html, normalize_job

logger = logging.getLogger(__name__)

BASE_URL = "https://wellfound.com/role/r/backend-engineer"


def scrape(**_) -> list[dict]:
    session = make_session()
    jobs = []

    headers_extra = {
        "Accept": "text/html,application/xhtml+xml",
        "Sec-Fetch-Mode": "navigate",
    }

    resp = safe_get(session, BASE_URL, headers=headers_extra)
    if resp is None:
        logger.warning("Wellfound: no response")
        return jobs

    soup = parse_html(resp.text)
    cards = soup.find_all("div", class_=re.compile(r"styles_component|job-listing|JobListing"))

    for card in cards:
        try:
            title_tag = card.find(re.compile(r"h2|h3"), class_=re.compile(r"title|role"))
            company_tag = card.find(re.compile(r"span|a"), class_=re.compile(r"company|startup"))
            loc_tag = card.find("span", class_=re.compile(r"location|loc"))
            salary_tag = card.find("span", class_=re.compile(r"compensation|salary"))
            link_tag = card.find("a", href=re.compile(r"/jobs/|/l/"))

            if not title_tag:
                continue

            href = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""
            if href and not href.startswith("http"):
                href = "https://wellfound.com" + href

            jobs.append(normalize_job(
                title=title_tag.get_text(strip=True),
                company=company_tag.get_text(strip=True) if company_tag else "Unknown",
                location=loc_tag.get_text(strip=True) if loc_tag else "Remote / India",
                salary=salary_tag.get_text(strip=True) if salary_tag else "Not disclosed",
                experience="0-3 years",
                url=href or BASE_URL,
                source="Wellfound",
            ))
        except Exception as e:
            logger.debug("Wellfound card parse error: %s", e)

    logger.info("Wellfound: found %d jobs", len(jobs))
    return jobs
