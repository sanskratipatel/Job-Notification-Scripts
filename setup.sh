#!/usr/bin/env bash
# ── Job Notification Bot – One-time Setup Script ──────────────────────────────
set -e

PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJ_DIR"

echo ""
echo "======================================================="
echo "  Job Notification Bot – Setup for Sanskrati Patel"
echo "======================================================="
echo ""

# 1. Install Python dependencies
echo "[1/4] Installing Python dependencies..."
python3 -m pip install --user -q -r requirements.txt
echo "      Done."

# 2. Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "[2/4] Created .env file. You MUST fill in your credentials:"
    echo ""
    echo "      GMAIL_APP_PASSWORD  → https://myaccount.google.com/apppasswords"
    echo "      CALLMEBOT_API_KEY   → Send 'I allow callmebot to send me messages'"
    echo "                            to WhatsApp number +34 644 65 21 91"
    echo ""
    echo "      Edit the .env file now, then re-run this script or run:"
    echo "      python3 main.py --test"
else
    echo "[2/4] .env already exists – skipping."
fi

# 3. Optional: set up a cron job to run every 2 hours
echo ""
echo "[3/4] Set up automatic cron job? (y/n)"
read -r SETUP_CRON
if [[ "$SETUP_CRON" =~ ^[Yy]$ ]]; then
    PYTHON=$(which python3)
    CRON_LINE="0 */2 * * * cd $PROJ_DIR && $PYTHON main.py >> $PROJ_DIR/job_notifier.log 2>&1"
    # Add only if not already present
    (crontab -l 2>/dev/null | grep -v "Job-Notification-Scripts"; echo "$CRON_LINE") | crontab -
    echo "      Cron job added: runs every 2 hours."
    echo "      View logs: tail -f $PROJ_DIR/job_notifier.log"
else
    echo "      Skipped. Run manually with: python3 main.py"
fi

# 4. Quick dry-run test
echo ""
echo "[4/4] Running a quick dry-run to verify setup..."
python3 main.py --test 2>&1 | grep -E "Job check|found|Filter|Dedup|DRY RUN|No new|FAILED|ERROR" | head -20

echo ""
echo "======================================================="
echo "  Setup complete!"
echo ""
echo "  Commands:"
echo "    python3 main.py             → run once"
echo "    python3 main.py --schedule  → run every 2h continuously"
echo "    python3 main.py --test      → dry-run (no notifications)"
echo "    python3 main.py --reset     → clear seen-jobs cache"
echo "======================================================="
