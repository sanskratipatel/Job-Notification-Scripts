"""
Hirist.tech scraper – tech-focused India job board.
Uses the public JSON API.
"""

import logging
import time
import random
import requests
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

API_URL = "https://www.hirist.tech/api/v2/jobs"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.hirist.tech/jobs/",
}


def scrape(keyword: str = "python backend", **_) -> list[dict]:
    jobs = []
    time.sleep(random.uniform(1.5, 2.5))

    params = {
        "keywords": keyword,
        "minExp": 0,
        "maxExp": 2,
        "page": 1,
        "limit": 20,
    }

    try:
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            logger.warning("Hirist: HTTP %d", resp.status_code)
            return jobs
        data = resp.json()
    except Exception as e:
        logger.warning("Hirist: request failed: %s", e)
        return jobs

    job_list = data.get("jobs") or data.get("data") or data.get("results") or []
    if not isinstance(job_list, list):
        logger.warning("Hirist: unexpected response shape")
        return jobs

    for j in job_list:
        try:
            title = j.get("jobTitle") or j.get("title", "")
            company = j.get("companyName") or j.get("company", {}).get("name", "Unknown")
            location = j.get("location") or j.get("city", "India")
            if isinstance(location, list):
                location = ", ".join(location[:2])

            job_id = j.get("jobId") or j.get("id") or j.get("slug", "")
            url = j.get("jobUrl") or j.get("url") or (
                f"https://www.hirist.tech/j/{job_id}" if job_id else "https://www.hirist.tech/jobs/"
            )

            min_exp = j.get("minExp") or j.get("experienceMin", 0) or 0
            max_exp = j.get("maxExp") or j.get("experienceMax", 2) or 2
            exp = f"{min_exp}-{max_exp} years"

            min_sal = j.get("minSalary") or j.get("salaryMin", 0) or 0
            max_sal = j.get("maxSalary") or j.get("salaryMax", 0) or 0
            if min_sal or max_sal:
                salary = f"{min_sal // 100000:.0f}-{max_sal // 100000:.0f} LPA"
            else:
                salary = "Not disclosed"

            skills_raw = j.get("skills") or j.get("keySkills") or []
            if isinstance(skills_raw, list):
                skills = ", ".join(
                    (s.get("name") or s if isinstance(s, (str, dict)) else "") for s in skills_raw[:6]
                )
            else:
                skills = str(skills_raw)

            jobs.append(normalize_job(
                title=title,
                company=company,
                location=location,
                salary=salary,
                experience=exp,
                url=url,
                source="Hirist",
                skills=skills,
            ))
        except Exception as e:
            logger.debug("Hirist job parse error: %s", e)

    logger.info("Hirist: found %d jobs for '%s'", len(jobs), keyword)
    return jobs
