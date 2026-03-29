"""
Track already-notified jobs so we never send duplicate alerts.

Storage priority:
  1. /opt/render/project/data/  (Render persistent disk mount point)
  2. ./data/                    (local development)
"""

import os
import json
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Render persistent disk mounts at /opt/render/project/data by convention
_RENDER_DATA = Path("/opt/render/project/data")
_LOCAL_DATA  = Path(__file__).parent.parent / "data"

SEEN_FILE = (_RENDER_DATA / "seen_jobs.json") if _RENDER_DATA.exists() else (_LOCAL_DATA / "seen_jobs.json")


def _job_id(job: dict) -> str:
    """Stable fingerprint: hash of (title + company + source)."""
    key = f"{job.get('title','').lower()}|{job.get('company','').lower()}|{job.get('source','')}"
    return hashlib.md5(key.encode()).hexdigest()


def _load() -> dict:
    if SEEN_FILE.exists():
        try:
            return json.loads(SEEN_FILE.read_text())
        except Exception:
            pass
    return {}


def _save(seen: dict) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(seen, indent=2))


def filter_new(jobs: list[dict]) -> list[dict]:
    """Return only jobs not seen before; persist new IDs to disk."""
    seen = _load()
    new_jobs = []
    for job in jobs:
        jid = _job_id(job)
        if jid not in seen:
            new_jobs.append(job)
            seen[jid] = {"title": job["title"], "company": job["company"], "source": job["source"]}

    if new_jobs:
        _save(seen)
        logger.info("Deduplicator: %d new jobs (skipped %d duplicates)", len(new_jobs), len(jobs) - len(new_jobs))
    else:
        logger.info("Deduplicator: all %d jobs already seen", len(jobs))

    return new_jobs


def reset() -> None:
    """Clear the seen-jobs store (useful for testing)."""
    _save({})
    logger.info("Seen-jobs store cleared")
