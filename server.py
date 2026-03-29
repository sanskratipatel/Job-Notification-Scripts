"""
FastAPI server wrapper for Render deployment.
- Render detects Python via uvicorn
- Scheduler runs in a background thread
- /health endpoint lets Render know the service is alive
"""

import threading
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from main import run
import schedule
import time
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger("server")

CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "2"))


def scheduler_loop():
    logger.info("Scheduler started – checking every %d hour(s)", CHECK_INTERVAL_HOURS)
    run()  # run immediately on startup
    schedule.every(CHECK_INTERVAL_HOURS).hours.do(run)
    while True:
        schedule.run_pending()
        time.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    logger.info("Background job scheduler thread started")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {"status": "running", "service": "Job Notification Bot"}


@app.get("/health")
def health():
    return {"status": "ok"}
