#!/usr/bin/env python
"""
init_database.py  –  Initialise the database (create tables + seed data)

Run once before starting the server for the first time:
    python init_database.py
"""
import os
import sys
from pathlib import Path

# ── Add project root to path ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# ── Load .env ─────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

# ── Django settings (needed by core.security which imports bcrypt) ────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bts_project.settings")

import django
django.setup()

# ── Init DB ───────────────────────────────────────────────────────────────────
from core.db import init_db
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("init_database")

if __name__ == "__main__":
    logger.info("Initialising database …")
    try:
        init_db()
        logger.info("Database ready. You can now start the server.")
    except Exception as e:
        logger.error("Database initialisation failed: %s", e)
        sys.exit(1)
