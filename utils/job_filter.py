"""Filter jobs based on Sanskrati's profile criteria from config.py."""

import re
import logging
from config import (
    REQUIRED_SKILLS_ANY,
    EXCLUDE_TITLES,
    EXP_MIN_YEARS,
    EXP_MAX_YEARS,
    SALARY_MIN_LPA,
    SALARY_MAX_LPA,
)

logger = logging.getLogger(__name__)

# Regex to extract salary numbers like "5-8 LPA", "₹6,00,000", "6 LPA", "500000"
_SALARY_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*(?:lpa|l\.?p\.?a|lakh|lac|lakhs)?",
    re.IGNORECASE,
)

# Regex to extract experience numbers like "0-2 years", "1 year", "2 yrs"
_EXP_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*(?:yr|year|yrs)?", re.IGNORECASE)


def _parse_salary_lpa(salary_str: str) -> tuple[float | None, float | None]:
    """Return (min_lpa, max_lpa) parsed from a salary string, or (None, None)."""
    s = salary_str.lower().replace(",", "")
    if "not disclosed" in s or "negotiable" in s or not s:
        return None, None

    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if not nums:
        return None, None

    vals = [float(n) for n in nums[:2]]

    # Convert annual rupees → LPA (if values look like full rupee amounts)
    vals = [v / 100_000 if v > 100 else v for v in vals]

    if len(vals) == 1:
        return vals[0], vals[0]
    return vals[0], vals[1]


def _parse_exp_years(exp_str: str) -> tuple[float | None, float | None]:
    """Return (min_years, max_years) from experience string, or (None, None)."""
    s = exp_str.lower()
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if not nums:
        return None, None
    vals = [float(n) for n in nums[:2]]
    if len(vals) == 1:
        return vals[0], vals[0]
    return vals[0], vals[1]


def _title_has_required_skill(title: str) -> bool:
    t = title.lower()
    return any(skill in t for skill in REQUIRED_SKILLS_ANY)


def _title_is_excluded(title: str) -> bool:
    t = title.lower()
    return any(excl in t for excl in EXCLUDE_TITLES)


def _salary_ok(job: dict) -> bool:
    """Return True if salary meets minimum threshold (or is undisclosed)."""
    min_lpa, max_lpa = _parse_salary_lpa(job.get("salary", ""))
    if min_lpa is None:
        # undisclosed – include anyway (can't filter what we can't read)
        return True
    offered = max_lpa if max_lpa else min_lpa
    if SALARY_MAX_LPA and offered > SALARY_MAX_LPA:
        return False
    return offered >= SALARY_MIN_LPA


def _experience_ok(job: dict) -> bool:
    """Return True if required experience overlaps with candidate's eligibility."""
    min_exp, max_exp = _parse_exp_years(job.get("experience", ""))
    if min_exp is None:
        return True   # no info → include
    # accept if required min experience ≤ EXP_MAX_YEARS
    return min_exp <= EXP_MAX_YEARS


def is_relevant(job: dict) -> bool:
    title = job.get("title", "")
    if not title:
        return False
    if _title_is_excluded(title):
        return False
    if not _title_has_required_skill(title):
        # also check skills field
        skills = job.get("skills", "").lower()
        if not any(s in skills for s in REQUIRED_SKILLS_ANY):
            return False
    if not _salary_ok(job):
        return False
    if not _experience_ok(job):
        return False
    return True


def filter_jobs(jobs: list[dict]) -> list[dict]:
    relevant = [j for j in jobs if is_relevant(j)]
    logger.info("Filter: %d / %d jobs passed", len(relevant), len(jobs))
    return relevant
