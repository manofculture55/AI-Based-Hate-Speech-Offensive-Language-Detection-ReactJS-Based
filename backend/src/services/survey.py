"""
Community labelling survey.

Improvements over the previous inline implementation:

* `pd.read_csv` ran on every single GET /survey/next -- a ~68k row parse per
  request. The frame is cached and invalidated by file mtime.
* A missing `truelabel` column raised KeyError -> HTTP 500. It is checked.
* Consensus updates rewrote the whole CSV from inside the request handler with
  no error isolation; failures there are now reported without failing the vote.
"""

import os
import threading

import pandas as pd

from backend.src.api.errors import ServiceUnavailable
from backend.src.repositories import survey as repo
from backend.src.utils import config, paths

_cache = {"frame": None, "mtime": None}
_cache_lock = threading.Lock()

REQUIRED_COLUMNS = ("text", "truelabel")


def _load_corpus():
    """Return the survey corpus, re-reading it only when the file changes."""
    path = paths.CLEAN_DATA_CSV

    if not os.path.exists(path):
        raise ServiceUnavailable(
            "The survey corpus is unavailable. Run "
            "python -m backend.src.data.normalize to generate clean_data.csv.",
            code="corpus_unavailable",
        )

    mtime = os.path.getmtime(path)

    with _cache_lock:
        if _cache["frame"] is None or _cache["mtime"] != mtime:
            frame = pd.read_csv(path)

            missing = [
                column for column in REQUIRED_COLUMNS if column not in frame.columns
            ]
            if missing:
                raise ServiceUnavailable(
                    "The survey corpus is missing required columns: "
                    + ", ".join(missing),
                    code="corpus_malformed",
                    details={"missing": missing, "found": list(frame.columns)},
                )

            _cache["frame"] = frame
            _cache["mtime"] = mtime

        return _cache["frame"]


def invalidate_cache():
    with _cache_lock:
        _cache["frame"] = None
        _cache["mtime"] = None


def next_item():
    """
    One unresolved text to label, or None when the corpus is exhausted.

    Returns a dict shaped like a survey resource.
    """
    frame = _load_corpus()
    resolved = repo.resolved_texts()

    available = frame[~frame["text"].isin(resolved)] if resolved else frame

    if available.empty:
        return None

    row = available.sample(1).iloc[0]

    try:
        original_label = int(row["truelabel"])
    except (TypeError, ValueError):
        original_label = None

    existing = repo.get_by_text(row["text"])

    return {
        "text": str(row["text"]),
        "original_label": original_label,
        "vote_count": int(existing["survey_count"]) if existing else 0,
        "is_resolved": bool(existing["is_resolved"]) if existing else False,
    }


def _corpus_label_for(text):
    """The dataset's current label for `text`, or None if it isn't in the CSV."""
    try:
        frame = _load_corpus()
    except ServiceUnavailable:
        return None

    matches = frame.loc[frame["text"] == text, "truelabel"]
    if matches.empty:
        return None

    try:
        return int(matches.iloc[0])
    except (TypeError, ValueError):
        return None


def _update_corpus_label(text, label):
    """Write a settled label back into clean_data.csv. Returns True on success."""
    path = paths.CLEAN_DATA_CSV
    try:
        frame = pd.read_csv(path)
        if "truelabel" not in frame.columns:
            return False

        mask = frame["text"] == text
        if not mask.any():
            return False

        frame.loc[mask, "truelabel"] = int(label)
        frame.to_csv(path, index=False)
        invalidate_cache()
        return True

    except Exception as exc:
        print(f"  [Survey] Failed to write consensus label to CSV: {exc}")
        return False


def record_vote(text, label):
    """
    Register one vote and apply consensus if it has now been reached.

    Returns (survey_row, resolved, corpus_updated).
    """
    original_label = _corpus_label_for(text)

    row, resolved = repo.record_vote(
        text=text,
        label=label,
        original_label=original_label,
        consensus_threshold=config.SURVEY_CONSENSUS_THRESHOLD,
    )

    corpus_updated = False
    if resolved:
        corpus_updated = _update_corpus_label(text, label)

    return row, resolved, corpus_updated
