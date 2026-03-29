# Job Notification Bot – Sanskrati Patel

Automatically scrapes **7 job portals** for Backend Python/FastAPI/Django roles matching your profile and sends alerts via **Email + WhatsApp**.

## Portals Covered

| Portal | Type |
|--------|------|
| Naukri | India's #1 job board |
| LinkedIn | Global + remote roles |
| Indeed India | Wide coverage |
| Internshala | 0-2 yr experience roles |
| TimesJobs | India jobs |
| Shine | India jobs |
| Wellfound | Startup jobs |

## Filter Criteria (pre-configured for Sanskrati)

- **Experience**: 0–2 years required (you have 1.6 yrs)
- **Salary**: ≥ 4.8 LPA minimum
- **Skills**: Python, FastAPI, Django, Backend, REST API, Flask, PostgreSQL, MongoDB
- **Excludes**: Frontend, DevOps, ML, QA, Sales, Java/.NET/PHP/Ruby roles

## Quick Start

### 1. Install & Configure

```bash
./setup.sh
```

Or manually:

```bash
python3 -m pip install --user -r requirements.txt
cp .env.example .env
# Edit .env with your credentials (see below)
```

### 2. Set up Email (Gmail)

1. Go to https://myaccount.google.com/apppasswords
2. Create an App Password for "Mail"
3. Paste the 16-character password into `.env` as `GMAIL_APP_PASSWORD`

### 3. Set up WhatsApp (CallMeBot – FREE, no billing)

1. Save **+34 644 65 21 91** in your WhatsApp contacts as "CallMeBot"
2. Send this exact message to that number via WhatsApp:
   ```
   I allow callmebot to send me messages
   ```
3. You'll receive your API key in a reply
4. Add it to `.env` as `CALLMEBOT_API_KEY`

### 4. Run

```bash
# Test first (no notifications sent, shows what would be found)
python3 main.py --test

# Run once
python3 main.py

# Run every 2 hours automatically (keep terminal open)
python3 main.py --schedule

# Clear job cache (re-notify about all current jobs)
python3 main.py --reset
```

### 5. Auto-run with Cron (recommended)

```bash
crontab -e
# Add this line to check every 2 hours:
0 */2 * * * cd /home/katyayani/Desktop/Job-Notification-Scripts && python3 main.py >> job_notifier.log 2>&1
```

## File Structure

```
├── main.py                  # Entry point + scheduler
├── config.py                # Your profile & filter settings
├── scrapers/
│   ├── naukri_scraper.py
│   ├── linkedin_scraper.py
│   ├── indeed_scraper.py
│   ├── internshala_scraper.py
│   ├── timesjobs_scraper.py
│   ├── shine_scraper.py
│   └── wellfound_scraper.py
├── notifiers/
│   ├── email_notifier.py    # Gmail SMTP
│   └── whatsapp_notifier.py # CallMeBot (free WhatsApp API)
├── utils/
│   ├── job_filter.py        # Salary / exp / skill filtering
│   └── deduplicator.py      # Prevents duplicate alerts
├── data/
│   └── seen_jobs.json       # Tracks already-notified jobs
├── .env                     # Your secrets (never commit this)
├── .env.example             # Template
└── requirements.txt
```

## Customizing

Edit `config.py` to change:
- `SEARCH_KEYWORDS` – what to search for
- `SALARY_MIN_LPA` – minimum salary (currently 4.8)
- `EXP_MAX_YEARS` – max experience required in job posting (currently 2)
- `REQUIRED_SKILLS_ANY` – skills to match
- `EXCLUDE_TITLES` – job titles to skip
- `ENABLED_PORTALS` – turn individual portals on/off

## Logs

All runs are logged to `job_notifier.log` in the project directory.
