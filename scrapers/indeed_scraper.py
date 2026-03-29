"""Indeed India scraper using cloudscraper to bypass bot detection."""

import logging
import re

try:
    import cloudscraper
    _HAS_CLOUDSCRAPER = True
except ImportError:
    _HAS_CLOUDSCRAPER = False

from .base_scraper import make_session, safe_get, parse_html, normalize_job

logger = logging.getLogger(__name__)

BASE_URL = "https://in.indeed.com/jobs"


def _get_session():
    if _HAS_CLOUDSCRAPER:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        scraper.headers.update({
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://in.indeed.com/",
        })
        return scraper
    return make_session()


def scrape(keyword: str = "python backend developer", location: str = "India", pages: int = 2) -> list[dict]:
    session = _get_session()
    jobs = []

    for page in range(pages):
        params = {
            "q": keyword,
            "l": location,
            "fromage": 3,          # last 3 days (more results than 1 day)
            "start": page * 10,
        }
        try:
            import time, random
            time.sleep(random.uniform(2, 4))
            resp = session.get(BASE_URL, params=params, timeout=20)
            if resp.status_code != 200:
                logger.warning("Indeed: HTTP %d for keyword=%s", resp.status_code, keyword)
                continue
        except Exception as e:
            logger.warning("Indeed: request failed for keyword=%s: %s", keyword, e)
            continue

        soup = parse_html(resp.text)

        # Indeed's HTML structure varies; try multiple selectors
        cards = soup.find_all("div", attrs={"data-jk": True})
        if not cards:
            cards = soup.find_all("li", class_=re.compile(r"css-5lfssm|job_seen_beacon"))
        if not cards:
            cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon|resultContent"))

        for card in cards:
            try:
                # Title
                title_tag = card.find("h2", class_=re.compile(r"jobTitle"))
                if not title_tag:
                    title_tag = card.find("a", attrs={"data-jk": True})

                # Company
                company_tag = (
                    card.find("span", attrs={"data-testid": "company-name"})
                    or card.find("span", class_=re.compile(r"companyName|css-63koeb"))
                )

                # Location
                loc_tag = (
                    card.find("div", attrs={"data-testid": "text-location"})
                    or card.find("div", class_=re.compile(r"companyLocation|css-1p0sjhy"))
                )

                # Salary
                salary_tag = card.find("div", attrs={"data-testid": re.compile(r"salary|compensation")})
                if not salary_tag:
                    salary_tag = card.find("div", class_=re.compile(r"salary|compensation|css-1cvvo1r"))

                # Job URL
                job_id = card.get("data-jk", "")
                if not job_id:
                    link_tag = card.find("a", attrs={"data-jk": True})
                    job_id = link_tag.get("data-jk", "") if link_tag else ""

                if not title_tag:
                    continue

                url = f"https://in.indeed.com/viewjob?jk={job_id}" if job_id else "https://in.indeed.com"

                jobs.append(normalize_job(
                    title=title_tag.get_text(strip=True),
                    company=company_tag.get_text(strip=True) if company_tag else "Unknown",
                    location=loc_tag.get_text(strip=True) if loc_tag else location,
                    salary=salary_tag.get_text(strip=True) if salary_tag else "Not disclosed",
                    experience="0-2 years",
                    url=url,
                    source="Indeed",
                ))
            except Exception as e:
                logger.debug("Indeed card parse error: %s", e)

    logger.info("Indeed: found %d jobs for '%s'", len(jobs), keyword)
    return jobs
