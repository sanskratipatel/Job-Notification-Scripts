#!/usr/bin/env python3
"""
Job Notification Bot – Sanskrati Patel
Scrapes Naukri, LinkedIn, Indeed, Internshala, TimesJobs, Shine, Wellfound
and sends matching jobs via Email + WhatsApp.

Usage:
    python main.py            # run once immediately
    python main.py --schedule # run now + every N hours (set in .env)
    python main.py --reset    # clear seen-jobs store, then run once
    python main.py --test     # dry-run (print jobs, no notifications sent)
"""

import os
import sys
import logging
import argparse
import schedule
import time
from dotenv import load_dotenv

load_dotenv()

from config import SEARCH_KEYWORDS, LOCATIONS, ENABLED_PORTALS
from scrapers import (
    naukri_scraper,
    linkedin_scraper,
    indeed_scraper,
    internshala_scraper,
    timesjobs_scraper,
    shine_scraper,
    wellfound_scraper,
)
from utils.job_filter import filter_jobs
from utils.deduplicator import filter_new, reset as reset_seen
from notifiers import email_notifier

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("job_notifier.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")

CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "1"))

# Map portal names → scraper functions
PORTAL_MAP = {
    "naukri": naukri_scraper.scrape,
    "linkedin": linkedin_scraper.scrape,
    "indeed": indeed_scraper.scrape,
    "internshala": internshala_scraper.scrape,
    "timesjobs": timesjobs_scraper.scrape,
    "shine": shine_scraper.scrape,
    "wellfound": wellfound_scraper.scrape,
}


def collect_jobs() -> list[dict]:
    """Run all enabled scrapers across all keywords and return raw jobs."""
    all_jobs: list[dict] = []

    # Portals that take a single keyword slug (no location loop needed)
    single_kw_portals = {"internshala", "shine", "wellfound"}

    for portal, enabled in ENABLED_PORTALS.items():
        if not enabled:
            continue
        scrape_fn = PORTAL_MAP.get(portal)
        if scrape_fn is None:
            continue

        if portal in single_kw_portals:
            # Just call once with first keyword
            try:
                jobs = scrape_fn(keyword=SEARCH_KEYWORDS[0])
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error("Scraper %s crashed: %s", portal, e)
        else:
            # Rotate through keywords × locations
            for kw in SEARCH_KEYWORDS[:3]:       # limit to top 3 keywords per run
                for loc in LOCATIONS[:2]:         # limit to top 2 locations per run
                    try:
                        jobs = scrape_fn(keyword=kw, location=loc)
                        all_jobs.extend(jobs)
                    except Exception as e:
                        logger.error("Scraper %s [%s/%s] crashed: %s", portal, kw, loc, e)

    logger.info("Total raw jobs collected: %d", len(all_jobs))
    return all_jobs


def run(dry_run: bool = False) -> None:
    logger.info("=" * 60)
    logger.info("Job check started")

    raw_jobs = collect_jobs()

    # 1) Filter by skill/exp/salary criteria
    relevant = filter_jobs(raw_jobs)

    # 2) Remove already-notified jobs
    new_jobs = filter_new(relevant)

    if not new_jobs:
        logger.info("No new relevant jobs found this run.")
        return

    logger.info("New jobs to notify: %d", len(new_jobs))

    if dry_run:
        print(f"\n{'='*60}")
        print(f"DRY RUN – {len(new_jobs)} job(s) would be sent:\n")
        for j in new_jobs:
            print(f"  [{j['source']}] {j['title']} @ {j['company']}")
            print(f"    {j['location']} | {j.get('salary','?')} | {j.get('experience','?')}")
            print(f"    {j['url']}\n")
        return

    # 3) Send notifications (email only)
    email_ok = email_notifier.send(new_jobs)

    logger.info("Notifications – Email: %s", "OK" if email_ok else "FAILED")
    logger.info("Job check complete")


def main():
    parser = argparse.ArgumentParser(description="Job Notification Bot")
    parser.add_argument("--schedule", action="store_true", help="Run on a recurring schedule")
    parser.add_argument("--reset", action="store_true", help="Clear seen-jobs store before running")
    parser.add_argument("--test", action="store_true", help="Dry run – print jobs, no notifications")
    args = parser.parse_args()

    if args.reset:
        reset_seen()
        logger.info("Seen-jobs store cleared")

    if args.schedule:
        logger.info("Scheduler started – will check every %d hour(s)", CHECK_INTERVAL_HOURS)
        run(dry_run=args.test)   # run immediately on start
        schedule.every(CHECK_INTERVAL_HOURS).hours.do(run, dry_run=args.test)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run(dry_run=args.test)


if __name__ == "__main__":
    main()
