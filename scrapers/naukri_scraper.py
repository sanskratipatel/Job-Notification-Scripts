"""
Naukri.com scraper.
Strategy: visit homepage first to get session cookies, then call their JSON search API.
"""

import logging
import time
import random
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

HOMEPAGE = "https://www.naukri.com/"
SEARCH_API = "https://www.naukri.com/jobapi/v3/search"

# Headers that match what a real browser sends to Naukri's search API
API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
    "appid": "109",
    "systemid": "Naukri",
    "gid": "LOCATION,INDUSTRY,EDUCATION,FAREA_ROLE",
    "Referer": "https://www.naukri.com/",
    "Origin": "https://www.naukri.com",
}


def _make_naukri_session():
    import requests
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    })
    try:
        # Visit homepage to get session cookies (required by their API)
        s.get(HOMEPAGE, timeout=15)
        time.sleep(random.uniform(1.0, 2.0))
    except Exception as e:
        logger.warning("Naukri: homepage warmup failed: %s", e)
    return s


def _salary_text(job: dict) -> str:
    try:
        for ph in job.get("placeholders", []):
            if ph.get("type") == "salary":
                label = ph.get("label", "")
                if label and label != "Not disclosed":
                    return label
        mn = job.get("minimumSalary") or 0
        mx = job.get("maximumSalary") or 0
        if mn or mx:
            return f"{mn // 100000:.1f}-{mx // 100000:.1f} LPA"
    except Exception:
        pass
    return "Not disclosed"


def _exp_text(job: dict) -> str:
    for ph in job.get("placeholders", []):
        if ph.get("type") == "experience":
            return ph.get("label", "")
    return ""


def _loc_text(job: dict) -> str:
    for ph in job.get("placeholders", []):
        if ph.get("type") == "location":
            return ph.get("label", "")
    return ""


def scrape(keyword: str = "python backend developer", location: str = "india", pages: int = 2) -> list[dict]:
    session = _make_naukri_session()
    jobs = []

    loc_param = "" if location.lower() in ("india", "remote") else location

    for page in range(1, pages + 1):
        params = {
            "noOfResults": 20,
            "urlType": "search_by_key_loc",
            "searchType": "adv",
            "keyword": keyword,
            "location": loc_param,
            "experience": 0,
            "salary": 480000,   # ~4.8 LPA
            "pageNo": page,
            "jobAge": 3,        # last 3 days
        }
        time.sleep(random.uniform(1.5, 3.0))
        try:
            resp = session.get(SEARCH_API, params=params, headers=API_HEADERS, timeout=20)
            if resp.status_code != 200:
                logger.warning("Naukri API: HTTP %d for '%s'", resp.status_code, keyword)
                continue
            data = resp.json()
        except Exception as e:
            logger.warning("Naukri: request/parse failed for '%s': %s", keyword, e)
            continue

        for j in data.get("jobDetails", []):
            title = j.get("title", "")
            if not title:
                continue

            company = j.get("companyName", "Unknown")
            job_id = j.get("jobId", "")
            # Naukri job URLs use the slug from ambitionBox or direct job ID
            slug = j.get("staticUrl", "")
            url = f"https://www.naukri.com/{slug}" if slug else f"https://www.naukri.com/job-listings-{job_id}"

            skills_raw = j.get("tagsAndSkills", "") or ""
            skills = ", ".join(s.strip() for s in skills_raw.split(",")[:6] if s.strip())

            jobs.append(normalize_job(
                title=title,
                company=company,
                location=_loc_text(j) or location,
                salary=_salary_text(j),
                experience=_exp_text(j) or "0-2 years",
                url=url,
                source="Naukri",
                posted=j.get("footerPlaceholderLabel", ""),
                skills=skills,
            ))

    logger.info("Naukri: found %d jobs for '%s'", len(jobs), keyword)
    return jobs
