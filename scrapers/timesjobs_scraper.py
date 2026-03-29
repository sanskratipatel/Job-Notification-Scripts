"""
TimesJobs scraper.
TimesJobs is now a Next.js SPA – job data is rendered client-side.
We use their public JSON search API instead.
"""

import logging
import time
import random
import requests
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

# TimesJobs has a public search API used by their frontend
SEARCH_API = "https://www.timesjobs.com/candidate/jobs.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.timesjobs.com/",
    "X-Requested-With": "XMLHttpRequest",
}

# TimesJobs has an AJAX search endpoint
AJAX_URL = "https://www.timesjobs.com/candidate/ajax/searchRes.html"


def scrape(keyword: str = "python backend developer", location: str = "india", **_) -> list[dict]:
    jobs = []

    time.sleep(random.uniform(1.5, 2.5))
    params = {
        "searchType": "personalizedSearch",
        "from": "submit",
        "txtKeywords": keyword,
        "txtLocation": location if location.lower() != "india" else "",
        "postWeek": 3,
        "sequence": 1,
        "startPage": 1,
    }

    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        resp = requests.get(
            SEARCH_API,
            params=params,
            headers=HEADERS,
            timeout=20,
            verify=False,   # TimesJobs has SSL cert issues on some networks
        )
        if resp.status_code != 200:
            logger.warning("TimesJobs: HTTP %d", resp.status_code)
            return jobs
    except Exception as e:
        logger.warning("TimesJobs: request failed: %s", e)
        return jobs

    # TimesJobs is Next.js now but their /candidate/jobs.html may return JSON
    content_type = resp.headers.get("Content-Type", "")
    if "json" in content_type:
        try:
            data = resp.json()
            for j in data.get("jobs", []):
                jobs.append(normalize_job(
                    title=j.get("functionalAreaSubArea", {}).get("subArea", ""),
                    company=j.get("company", {}).get("name", "Unknown"),
                    location=j.get("location", location),
                    salary=j.get("salary", "Not disclosed"),
                    experience=j.get("experience", "0-2 years"),
                    url=f"https://www.timesjobs.com/job-detail/job-{j.get('jobId', '')}",
                    source="TimesJobs",
                ))
        except Exception as e:
            logger.debug("TimesJobs JSON parse failed: %s", e)
    else:
        # HTML fallback – parse whatever structure we get
        from bs4 import BeautifulSoup
        import re
        soup = BeautifulSoup(resp.text, "html.parser")
        # Try generic job link pattern
        job_links = soup.find_all("a", href=re.compile(r"/job-detail/"))
        seen_hrefs = set()
        for link in job_links:
            href = link.get("href", "")
            if href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            title = link.get_text(strip=True)
            if not title:
                continue
            if not href.startswith("http"):
                href = "https://www.timesjobs.com" + href
            jobs.append(normalize_job(
                title=title,
                company="Unknown",
                location=location,
                salary="Not disclosed",
                experience="0-2 years",
                url=href,
                source="TimesJobs",
            ))

    logger.info("TimesJobs: found %d jobs for '%s'", len(jobs), keyword)
    return jobs
