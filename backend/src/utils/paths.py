"""
Single source of truth for every filesystem path used by the backend.

Historically several modules built paths relative to the *current working
directory* (e.g. "backend/models/deep", "reports/training_report_all.json").
Those only resolved correctly when the process happened to be launched from
the project root, and silently failed everywhere else -- which is why the
analytics endpoint used to serve hardcoded placeholder metrics.  Everything
here is anchored to this file's location instead, so it works regardless of
how the app is started.
"""

import os

# .../backend/src/utils/paths.py -> .../backend
BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))

DATA_DIR = os.path.join(BACKEND_DIR, "data")
MODELS_DIR = os.path.join(BACKEND_DIR, "models")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
DOCS_DIR = os.path.join(BACKEND_DIR, "docs")

BASELINE_MODEL_DIR = os.path.join(MODELS_DIR, "baseline")
DEEP_MODEL_DIR = os.path.join(MODELS_DIR, "deep")
TRANSFORMER_MODEL_DIR = os.path.join(MODELS_DIR, "transformer")

DB_PATH = os.path.join(DATA_DIR, "app.db")
CLEAN_DATA_CSV = os.path.join(DATA_DIR, "clean_data.csv")

TOKENIZER_PATH = os.path.join(DEEP_MODEL_DIR, "tokenizer.pickle")
TRAINING_REPORT_JSON = os.path.join(REPORTS_DIR, "training_report_all.json")

ENV_FILE = os.path.join(PROJECT_ROOT, ".env")


def deep_model_path(architecture="bilstm"):
    """Path of a saved Keras model, e.g. bilstm -> models/deep/bilstm_model.h5"""
    return os.path.join(DEEP_MODEL_DIR, f"{architecture}_model.h5")


def ensure_dirs():
    """Create every writable directory the backend expects. Idempotent."""
    for directory in (
        DATA_DIR,
        MODELS_DIR,
        REPORTS_DIR,
        BASELINE_MODEL_DIR,
        DEEP_MODEL_DIR,
        TRANSFORMER_MODEL_DIR,
    ):
        os.makedirs(directory, exist_ok=True)
