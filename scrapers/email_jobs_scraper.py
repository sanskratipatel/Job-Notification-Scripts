"""
Read job alert emails from Gmail (Indeed + Naukri alerts).
Uses Gmail IMAP – reads your own emails, no scraping involved.
"""

import imaplib
import email
import logging
import os
import re
from email.header import decode_header
from bs4 import BeautifulSoup
from .base_scraper import normalize_job

logger = logging.getLogger(__name__)

# This reads job alert emails from your Naukri/Indeed alert inbox
GMAIL_USER = os.getenv("ALERT_GMAIL_USER", "patelsanskrati12@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("ALERT_GMAIL_APP_PASSWORD", "")

# Senders whose emails contain job listings
JOB_ALERT_SENDERS = [
    "alert@indeed.com",
    "jobalerts@naukri.com",
    "no-reply@naukri.com",
    "jobupdate@naukri.com",
    "jobs-noreply@linkedin.com",
    "alert@glassdoor.com",
]


def _connect():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    return mail


def _decode_str(s) -> str:
    if s is None:
        return ""
    decoded, enc = decode_header(s)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(enc or "utf-8", errors="ignore")
    return decoded


def _extract_jobs_from_indeed(soup, subject: str) -> list[dict]:
    jobs = []
    # Indeed alert emails have job cards with title + company + location
    cards = soup.find_all("td", class_=re.compile(r"job|result", re.I))
    if not cards:
        # fallback: find all job links
        links = soup.find_all("a", href=re.compile(r"indeed\.com/rc/clk|indeed\.com/viewjob|indeed\.com/pagead"))
        seen = set()
        for link in links:
            href = link.get("href", "")
            title = link.get_text(strip=True)
            if not title or len(title) < 5 or href in seen:
                continue
            if any(skip in title.lower() for skip in ["unsubscribe", "view all", "see more", "click"]):
                continue
            seen.add(href)
            jobs.append(normalize_job(
                title=title,
                company="See listing",
                location="India",
                salary="Not disclosed",
                experience="0-2 years",
                url=href,
                source="Indeed (Email Alert)",
            ))
        return jobs

    for card in cards:
        try:
            title_tag = card.find("a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            company_tag = card.find("span", class_=re.compile(r"company", re.I))
            loc_tag = card.find("span", class_=re.compile(r"location|loc", re.I))
            jobs.append(normalize_job(
                title=title,
                company=company_tag.get_text(strip=True) if company_tag else "See listing",
                location=loc_tag.get_text(strip=True) if loc_tag else "India",
                salary="Not disclosed",
                experience="0-2 years",
                url=href,
                source="Indeed (Email Alert)",
            ))
        except Exception:
            pass
    return jobs


def _extract_jobs_from_naukri(soup, subject: str) -> list[dict]:
    jobs = []
    # Naukri alert emails list jobs as table rows or divs
    links = soup.find_all("a", href=re.compile(r"naukri\.com/.*job|naukri\.com/.*-jobs"))
    seen = set()
    for link in links:
        href = link.get("href", "")
        title = link.get_text(strip=True)
        if not title or len(title) < 5 or href in seen:
            continue
        if any(skip in title.lower() for skip in ["unsubscribe", "view all", "naukri", "click here", "apply"]):
            continue
        seen.add(href)
        # Try to find nearby company text
        parent = link.parent
        company = ""
        if parent:
            siblings = parent.find_all(text=True)
            for t in siblings:
                t = t.strip()
                if t and t != title and len(t) > 2 and len(t) < 60:
                    company = t
                    break
        jobs.append(normalize_job(
            title=title,
            company=company or "See listing",
            location="India",
            salary="Not disclosed",
            experience="0-2 years",
            url=href,
            source="Naukri (Email Alert)",
        ))
    return jobs


def _get_email_body(msg) -> str:
    """Extract HTML body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/html":
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="ignore")
            if ctype == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="ignore")
    else:
        charset = msg.get_content_charset() or "utf-8"
        return msg.get_payload(decode=True).decode(charset, errors="ignore")
    return ""


def scrape(**_) -> list[dict]:
    if not GMAIL_APP_PASSWORD:
        logger.warning("Email Jobs: GMAIL_APP_PASSWORD not set")
        return []

    jobs = []
    try:
        mail = _connect()
        mail.select("INBOX")

        for sender in JOB_ALERT_SENDERS:
            # Search for unread emails from this sender in last 2 days
            _, data = mail.search(None, f'(FROM "{sender}" UNSEEN)')
            if not data or not data[0]:
                continue

            ids = data[0].split()
            logger.info("Email Jobs: %d unread alert emails from %s", len(ids), sender)

            for eid in ids[-10:]:   # max 10 emails per sender
                try:
                    _, msg_data = mail.fetch(eid, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    subject = _decode_str(msg.get("Subject", ""))
                    body = _get_email_body(msg)
                    if not body:
                        continue

                    soup = BeautifulSoup(body, "html.parser")

                    if "indeed" in sender:
                        found = _extract_jobs_from_indeed(soup, subject)
                    elif "naukri" in sender:
                        found = _extract_jobs_from_naukri(soup, subject)
                    else:
                        found = []

                    jobs.extend(found)
                    logger.info("Email Jobs: extracted %d jobs from '%s' email", len(found), sender)

                    # Mark as read so we don't process again
                    mail.store(eid, "+FLAGS", "\\Seen")

                except Exception as e:
                    logger.debug("Email Jobs: failed to parse email %s: %s", eid, e)

        mail.logout()

    except imaplib.IMAP4.error as e:
        logger.warning("Email Jobs: IMAP connection failed: %s", e)
    except Exception as e:
        logger.warning("Email Jobs: unexpected error: %s", e)

    logger.info("Email Jobs: total %d jobs from email alerts", len(jobs))
    return jobs
