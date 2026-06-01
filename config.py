import os
from dotenv import load_dotenv

load_dotenv()

# ── JWT ───────────────────────────────────────────────────
SECRET_KEY         = os.getenv("SECRET_KEY", "changeme-use-a-long-random-string-in-prod")
ALGORITHM          = "HS256"
TOKEN_EXPIRE_HOURS = 72

# ── OpenRouter (FREE AI - replaces Gemini) ────────────────


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── D-ID Video ────────────────────────────────────────────
DID_API_KEY        = os.getenv("DID_API_KEY", "")

# ── File storage ──────────────────────────────────────────
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

import pathlib
pathlib.Path(UPLOAD_DIR).mkdir(exist_ok=True)
pathlib.Path(OUTPUT_DIR).mkdir(exist_ok=True)