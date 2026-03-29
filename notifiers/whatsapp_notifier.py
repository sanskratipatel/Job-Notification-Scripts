"""
Send WhatsApp alerts via CallMeBot (free, no billing required).

Setup (one-time – takes 2 minutes):
  1. Save +34 644 65 21 91 as a contact named "CallMeBot"
  2. Send the message: I allow callmebot to send me messages
  3. You'll receive your API key via WhatsApp
  4. Add CALLMEBOT_API_KEY=<your_key> to your .env file
"""

import os
import logging
import urllib.parse
import requests

logger = logging.getLogger(__name__)

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"
WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE", "919329496348")
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY", "")

MAX_JOBS_PER_MESSAGE = 5   # WhatsApp message length limit; send in batches


def _format_message(jobs: list[dict], batch_num: int = 1, total_batches: int = 1) -> str:
    header = f"🚀 Job Alert ({batch_num}/{total_batches}) – {len(jobs)} new role(s)\n\n"
    lines = []
    for i, j in enumerate(jobs, 1):
        salary = j.get("salary") or "Not disclosed"
        lines.append(
            f"{i}. *{j['title']}*\n"
            f"   🏢 {j['company']}\n"
            f"   📍 {j['location']}\n"
            f"   💰 {salary}\n"
            f"   🌐 {j['source']}\n"
            f"   🔗 {j['url']}\n"
        )
    return header + "\n".join(lines)


def _send_one(text: str) -> bool:
    if not CALLMEBOT_API_KEY:
        logger.error("WhatsApp: CALLMEBOT_API_KEY not set in .env – see notifiers/whatsapp_notifier.py for setup")
        return False

    params = {
        "phone": WHATSAPP_PHONE,
        "text": text,
        "apikey": CALLMEBOT_API_KEY,
    }
    try:
        resp = requests.get(CALLMEBOT_URL, params=params, timeout=15)
        if resp.status_code == 200 and "Message sent" in resp.text:
            return True
        logger.warning("WhatsApp: unexpected response [%d]: %s", resp.status_code, resp.text[:200])
        return False
    except Exception as e:
        logger.error("WhatsApp: request failed: %s", e)
        return False


def send(jobs: list[dict]) -> bool:
    if not jobs:
        return True

    batches = [jobs[i:i + MAX_JOBS_PER_MESSAGE] for i in range(0, len(jobs), MAX_JOBS_PER_MESSAGE)]
    all_ok = True
    for idx, batch in enumerate(batches, 1):
        msg = _format_message(batch, batch_num=idx, total_batches=len(batches))
        ok = _send_one(msg)
        if not ok:
            all_ok = False
        logger.info("WhatsApp batch %d/%d: %s", idx, len(batches), "sent" if ok else "FAILED")

    return all_ok
