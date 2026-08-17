"""
Training-dataset ingestion for the admin endpoints.

The old /admin/upload required the uploaded CSV to have `text` and `label`
columns and appended them verbatim to clean_data.csv.  But the training
pipeline reads `truelabel` -- so every uploaded row landed in the file with a
column training ignores, and the upload could never influence a retrain.  It
also appended without validating the label values, so a typo could poison the
corpus with labels outside 0/1/2.

This module normalises whatever reasonable shape it is given onto the canonical
(text, truelabel, lang) schema and rejects rows it cannot use.
"""

import os

import pandas as pd

from backend.src.api.errors import ValidationError
from backend.src.data.langid import detect_language_strict
from backend.src.data.preprocess import clean_text
from backend.src.utils import paths
from backend.src.utils.labels import VALID_LABELS

CANONICAL_COLUMNS = ["text", "truelabel", "lang"]

# Column aliases accepted on upload, mapped to the canonical name.
LABEL_ALIASES = ("truelabel", "label", "class", "target")
TEXT_ALIASES = ("text", "comment", "tweet", "sentence")


def _pick_column(frame, aliases):
    lowered = {str(name).strip().lower(): name for name in frame.columns}
    for alias in aliases:
        if alias in lowered:
            return lowered[alias]
    return None


def normalize_upload(frame):
    """
    Coerce an uploaded frame onto (text, truelabel, lang).

    Returns (normalized_frame, report). Raises ValidationError when required
    columns are missing entirely.
    """
    text_column = _pick_column(frame, TEXT_ALIASES)
    label_column = _pick_column(frame, LABEL_ALIASES)

    missing = []
    if text_column is None:
        missing.append(f"text (accepted: {', '.join(TEXT_ALIASES)})")
    if label_column is None:
        missing.append(f"truelabel (accepted: {', '.join(LABEL_ALIASES)})")

    if missing:
        raise ValidationError(
            "Uploaded CSV is missing required columns.",
            details={
                "missing": missing,
                "found": [str(name) for name in frame.columns],
            },
        )

    received = len(frame)

    normalized = pd.DataFrame(
        {
            "text": frame[text_column].astype(str).map(clean_text),
            "truelabel": pd.to_numeric(frame[label_column], errors="coerce"),
        }
    )

    # Drop rows we cannot train on, and say how many went where.
    before_blank = len(normalized)
    normalized = normalized[normalized["text"].str.len() > 2]
    dropped_blank = before_blank - len(normalized)

    before_label = len(normalized)
    normalized = normalized[normalized["truelabel"].isin(VALID_LABELS)]
    dropped_label = before_label - len(normalized)

    normalized["truelabel"] = normalized["truelabel"].astype(int)

    # Carry `lang` through when supplied, otherwise derive it.
    lang_column = _pick_column(frame, ("lang", "language"))
    if lang_column is not None:
        normalized["lang"] = (
            frame.loc[normalized.index, lang_column].astype(str).str.strip()
        )
    else:
        normalized["lang"] = normalized["text"].map(
            lambda value: detect_language_strict(value, "english")
        )

    report = {
        "rows_received": received,
        "rows_accepted": len(normalized),
        "rows_dropped_empty_text": int(dropped_blank),
        "rows_dropped_invalid_label": int(dropped_label),
        "mapped_columns": {
            "text": str(text_column),
            "truelabel": str(label_column),
            "lang": str(lang_column) if lang_column else "derived",
        },
    }

    return normalized[CANONICAL_COLUMNS], report


def append_to_corpus(normalized):
    """
    Append rows to clean_data.csv, de-duplicating on text.

    Returns (rows_added, total_rows).
    """
    paths.ensure_dirs()
    target = paths.CLEAN_DATA_CSV

    if os.path.exists(target):
        existing = pd.read_csv(target)
        # Tolerate an older file that used `label`.
        if "truelabel" not in existing.columns and "label" in existing.columns:
            existing = existing.rename(columns={"label": "truelabel"})
        if "lang" not in existing.columns:
            existing["lang"] = "en"
        combined = pd.concat(
            [existing[CANONICAL_COLUMNS], normalized], ignore_index=True
        )
    else:
        existing = pd.DataFrame(columns=CANONICAL_COLUMNS)
        combined = normalized

    before = len(combined)
    combined = combined.drop_duplicates(subset=["text"], keep="last")
    duplicates = before - len(combined)

    combined.to_csv(target, index=False)

    return {
        "rows_added": len(combined) - len(existing),
        "duplicates_merged": int(duplicates),
        "total_rows": len(combined),
        "path": os.path.relpath(target, paths.PROJECT_ROOT),
    }
