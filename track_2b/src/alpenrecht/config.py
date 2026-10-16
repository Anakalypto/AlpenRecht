"""Settings, read from environment variables or a local .env file."""
import os
from pathlib import Path

# track_2b/ (holds .env, data/ and cache/); this file is track_2b/src/alpenrecht/config.py
ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "cache"
CACHE_DIR.mkdir(exist_ok=True)


def _load_dotenv():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

# Judges' convention LLM_API_KEY / LLM_BASE_URL / LLM_NAME; APERTUS_* still work.
APERTUS_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("APERTUS_API_KEY", "")
APERTUS_BASE_URL = (os.environ.get("LLM_BASE_URL") or os.environ.get("APERTUS_BASE_URL")
                    or "https://api.inference.cscs.ch/v1").rstrip("/")
APERTUS_MODEL = os.environ.get("LLM_NAME") or os.environ.get("APERTUS_MODEL") or "swiss-ai/Apertus-v1.5-70B"
# Fact-checking model for the 3 verification rounds; defaults to the answer model.
VERIFY_MODEL = os.environ.get("VERIFY_MODEL") or None
# Reads scanned regulations page by page (Apertus v1.5 takes images); the 8B is ~2x faster and accurate enough.
OCR_MODEL = os.environ.get("OCR_MODEL", "swiss-ai/Apertus-v1.5-8B")
PORT = int(os.environ.get("PORT", "5055"))
HOST = os.environ.get("HOST", "127.0.0.1")  # 0.0.0.0 inside Docker

USER_AGENT = "AlpenrechtAI/0.1 (Hack Apertus prototype)"
