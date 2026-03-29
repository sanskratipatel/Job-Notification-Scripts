"""LinkedIn public jobs scraper (no login required)."""

import logging
from .base_scraper import make_session, safe_get, parse_html, normalize_job

logger = logging.getLogger(__name__)

# LinkedIn guest jobs API – returns HTML card fragments
LINKEDIN_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

LINKEDIN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Referer": "https://www.linkedin.com/jobs/search/",
}

# f_E codes: 1=Internship, 2=Entry level, 3=Associate
EXP_LEVELS = "1,2,3"


def scrape(keyword: str = "python backend developer", location: str = "India", pages: int = 2) -> list[dict]:
    session = make_session()
    jobs = []

    for page in range(pages):
        params = {
            "keywords": keyword,
            "location": location,
            "f_E": EXP_LEVELS,
            "f_TPR": "r86400",   # posted in last 24 hours
            "start": page * 25,
        }
        resp = safe_get(session, LINKEDIN_URL, params=params, headers=LINKEDIN_HEADERS)
        if resp is None:
            logger.warning("LinkedIn: no response for keyword=%s", keyword)
            continue

        soup = parse_html(resp.text)
        cards = soup.find_all("li")

        for card in cards:
            try:
                title_tag = card.find("h3", class_="base-search-card__title")
                company_tag = card.find("h4", class_="base-search-card__subtitle")
                location_tag = card.find("span", class_="job-search-card__location")
                link_tag = card.find("a", class_="base-card__full-link")
                meta_tag = card.find("time")

                if not title_tag or not link_tag:
                    continue

                jobs.append(normalize_job(
                    title=title_tag.get_text(strip=True),
                    company=company_tag.get_text(strip=True) if company_tag else "Unknown",
                    location=location_tag.get_text(strip=True) if location_tag else location,
                    salary="Not disclosed",
                    experience="0-2 years",
                    url=link_tag["href"].split("?")[0],
                    source="LinkedIn",
                    posted=meta_tag.get("datetime", "") if meta_tag else "",
                ))
            except Exception as e:
                logger.debug("LinkedIn card parse error: %s", e)

    logger.info("LinkedIn: found %d jobs for '%s'", len(jobs), keyword)
    return jobs
