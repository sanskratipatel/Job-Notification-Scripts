"""
Cutshort.io scraper – tech-focused India job board with good API.
No auth needed for basic search.
"""

import logging
import time
import random
import requests
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

API_URL = "https://cutshort.io/api/web/jobs"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://cutshort.io/jobs",
    "Origin": "https://cutshort.io",
}


def scrape(keyword: str = "python backend", **_) -> list[dict]:
    jobs = []
    time.sleep(random.uniform(1.5, 2.5))

    payload = {
        "title": keyword,
        "locations": [],
        "skills": ["Python"],
        "minExp": 0,
        "maxExp": 2,
        "workType": [],
        "page": 1,
        "limit": 20,
    }

    try:
        resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            logger.warning("Cutshort: HTTP %d", resp.status_code)
            return jobs
        data = resp.json()
    except Exception as e:
        logger.warning("Cutshort: request failed: %s", e)
        return jobs

    for j in data.get("data", []):
        try:
            title = j.get("title", "")
            company = j.get("company", {}).get("name", "Unknown")
            loc_list = j.get("locations", [])
            location = ", ".join(loc_list[:2]) if loc_list else "India"
            slug = j.get("slug", "")
            url = f"https://cutshort.io/job/{slug}" if slug else "https://cutshort.io/jobs"

            min_exp = j.get("minExp", 0)
            max_exp = j.get("maxExp", 2)
            exp = f"{min_exp}-{max_exp} years"

            min_sal = j.get("minSalary", 0) or 0
            max_sal = j.get("maxSalary", 0) or 0
            if min_sal or max_sal:
                salary = f"{min_sal // 100000:.0f}-{max_sal // 100000:.0f} LPA"
            else:
                salary = "Not disclosed"

            skills_list = j.get("skills", [])
            skills = ", ".join(s.get("name", "") for s in skills_list[:6] if s.get("name"))

            jobs.append(normalize_job(
                title=title,
                company=company,
                location=location,
                salary=salary,
                experience=exp,
                url=url,
                source="Cutshort",
                skills=skills,
            ))
        except Exception as e:
            logger.debug("Cutshort job parse error: %s", e)

    logger.info("Cutshort: found %d jobs for '%s'", len(jobs), keyword)
    return jobs
