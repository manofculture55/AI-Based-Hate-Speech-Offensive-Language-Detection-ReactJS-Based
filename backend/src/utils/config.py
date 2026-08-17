"""
Environment-driven configuration.

Secrets used to be hardcoded here and duplicated in backend/app.py (which
declared ADMIN_KEY *and* ADMIN_SECRET with the same value) and again in the
React bundle.  They now come from the environment / a gitignored .env file.

Defaults intentionally match the old hardcoded values so an existing checkout
without a .env keeps working; `warn_about_insecure_defaults()` prints a notice
at startup when those defaults are still in play.
"""

import os

from backend.src.utils.paths import ENV_FILE

try:  # python-dotenv is in requirements.txt but keep startup resilient
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)
except ImportError:  # pragma: no cover
    pass


# --- helpers ---------------------------------------------------------------

def _str(name, default):
    value = os.environ.get(name)
    return default if value is None or value.strip() == "" else value.strip()


def _int(name, default):
    try:
        return int(_str(name, str(default)))
    except ValueError:
        return default


def _bool(name, default=False):
    return _str(name, "1" if default else "0").lower() in ("1", "true", "yes", "on")


def _list(name, default):
    raw = _str(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --- placeholder defaults (so the app runs before .env exists) -------------
# These are public -- they are in the repository. `warn_about_insecure_defaults`
# prints a startup notice for as long as any of them is still in effect.

_DEFAULT_API_KEY = "dev-api-key-change-me"
_DEFAULT_ADMIN_KEY = "dev-admin-key-change-me"
_DEFAULT_ADMIN_PASSWORD = "admin123"


# --- API ------------------------------------------------------------------

API_TITLE = "Hate Speech Detection API"
API_VERSION = "1.0.0"
API_PREFIX = "/api/v1"

API_KEY = _str("HSD_API_KEY", _DEFAULT_API_KEY)

# When false, POST /api/v1/predictions stays open (the web UI calls it directly,
# exactly as the old unauthenticated /predict did).  An X-API-KEY header is
# still validated when supplied, and is recorded as the prediction's source.
REQUIRE_API_KEY = _bool("HSD_REQUIRE_API_KEY", False)

MAX_API_TEXT_LENGTH = _int("HSD_MAX_TEXT_LENGTH", 500)

DEFAULT_PAGE_SIZE = _int("HSD_DEFAULT_PAGE_SIZE", 20)
MAX_PAGE_SIZE = _int("HSD_MAX_PAGE_SIZE", 100)

MAX_UPLOAD_BYTES = _int("HSD_MAX_UPLOAD_MB", 16) * 1024 * 1024

# Serve the pre-v1 URLs (/predict, /history, ...) as deprecated shims.
ENABLE_LEGACY_ROUTES = _bool("HSD_ENABLE_LEGACY_ROUTES", True)


# --- admin ----------------------------------------------------------------

ADMIN_KEY = _str("HSD_ADMIN_KEY", _DEFAULT_ADMIN_KEY)
ADMIN_PASSWORD = _str("HSD_ADMIN_PASSWORD", _DEFAULT_ADMIN_PASSWORD)


# --- server ---------------------------------------------------------------

HOST = _str("HSD_HOST", "127.0.0.1")
PORT = _int("HSD_PORT", 5000)
DEBUG = _bool("HSD_DEBUG", False)

CORS_ORIGINS = _list(
    "HSD_CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)


# --- survey ---------------------------------------------------------------

# Number of identical votes required before a text's label is considered settled.
SURVEY_CONSENSUS_THRESHOLD = _int("HSD_SURVEY_CONSENSUS", 3)


def using_insecure_defaults():
    """Which secrets are still the shipped defaults."""
    insecure = []
    if API_KEY == _DEFAULT_API_KEY:
        insecure.append("HSD_API_KEY")
    if ADMIN_KEY == _DEFAULT_ADMIN_KEY:
        insecure.append("HSD_ADMIN_KEY")
    if ADMIN_PASSWORD == _DEFAULT_ADMIN_PASSWORD:
        insecure.append("HSD_ADMIN_PASSWORD")
    return insecure


def warn_about_insecure_defaults():
    insecure = using_insecure_defaults()
    if insecure:
        print(
            "  [Config] WARNING: still using shipped default values for: "
            + ", ".join(insecure)
            + " -- copy .env.example to .env and change them."
        )
