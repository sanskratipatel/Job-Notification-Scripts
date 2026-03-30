"""
Naukri.com scraper using logged-in session cookies.
Cookies are read from .env – no password stored.
"""

import os
import logging
import time
import random
import requests
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

SEARCH_API = "https://www.naukri.com/jobapi/v3/search"

API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
    "appid": "109",
    "systemid": "Naukri",
    "gid": "LOCATION,INDUSTRY,EDUCATION,FAREA_ROLE",
    "Referer": "https://www.naukri.com/",
    "Origin": "https://www.naukri.com",
}


def _get_cookies() -> dict | None:
    nauk_at = os.getenv("NAUKRI_NAUK_AT", "")
    nauk_sid = os.getenv("NAUKRI_NAUK_SID", "")
    is_login = os.getenv("NAUKRI_IS_LOGIN", "")
    if not nauk_at or not nauk_sid:
        return None
    return {
        "nauk_at": nauk_at,
        "nauk_sid": nauk_sid,
        "nauk_rt": nauk_sid,
        "is_login": is_login,
        "J": "0",
    }


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


def _salary_text(job: dict) -> str:
    for ph in job.get("placeholders", []):
        if ph.get("type") == "salary":
            label = ph.get("label", "")
            if label and label.lower() != "not disclosed":
                return label
    mn = job.get("minimumSalary") or 0
    mx = job.get("maximumSalary") or 0
    if mn or mx:
        return f"{mn // 100000:.1f}-{mx // 100000:.1f} LPA"
    return "Not disclosed"


def scrape(keyword: str = "python backend developer", location: str = "india", pages: int = 2) -> list[dict]:
    cookies = _get_cookies()
    if not cookies:
        logger.warning("Naukri: cookies not set in .env – skipping")
        return []

    session = requests.Session()
    session.cookies.update(cookies)
    # Also send token as Bearer header – Naukri API requires both
    session.headers.update({
        **API_HEADERS,
        "Authorization": f"Bearer {cookies['nauk_at']}",
    })

    jobs = []
    loc_param = "" if location.lower() in ("india", "remote") else location

    for page in range(1, pages + 1):
        time.sleep(random.uniform(2, 4))
        params = {
            "noOfResults": 20,
            "urlType": "search_by_key_loc",
            "searchType": "adv",
            "keyword": keyword,
            "location": loc_param,
            "experience": 0,
            "salary": 480000,
            "pageNo": page,
            "jobAge": 3,
        }
        try:
            resp = session.get(SEARCH_API, params=params, headers=API_HEADERS, timeout=20)
            if resp.status_code != 200:
                logger.warning("Naukri: HTTP %d for '%s' (cookies may have expired)", resp.status_code, keyword)
                break
            data = resp.json()
        except Exception as e:
            logger.warning("Naukri: request failed: %s", e)
            break

        for j in data.get("jobDetails", []):
            title = j.get("title", "")
            if not title:
                continue
            slug = j.get("staticUrl", "")
            job_id = j.get("jobId", "")
            url = f"https://www.naukri.com/{slug}" if slug else f"https://www.naukri.com/job-listings-{job_id}"
            skills_raw = j.get("tagsAndSkills", "") or ""
            skills = ", ".join(s.strip() for s in skills_raw.split(",")[:6] if s.strip())

            jobs.append(normalize_job(
                title=title,
                company=j.get("companyName", "Unknown"),
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
