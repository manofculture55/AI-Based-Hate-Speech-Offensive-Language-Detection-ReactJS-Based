"""
Analytics aggregation.

Two correctness fixes over the old inline helpers in backend/app.py:

1. The report and CSV were read from CWD-relative paths ("reports/..." and
   "data/clean_data.csv") while the files live under backend/.  They never
   loaded, so the endpoint always fell through to a hardcoded dict of invented
   metrics (f1 0.87 / accuracy 0.89 / latency 120ms) that were presented as
   real.  Paths are absolute now, and when no report exists the response says
   so via `"available": false` instead of inventing numbers.

2. Even when a report was found, it was probed for keys that
   `run_training()` never writes ("bilstm_macro_f1", "baseline_f1", ...).  The
   real structure is {model: {"accuracy": float, "report": <sklearn dict>}},
   which is what gets parsed here.
"""

import json
import os

import pandas as pd

from backend.src.repositories import annotations as annotations_repo
from backend.src.repositories import predictions as predictions_repo
from backend.src.repositories import survey as survey_repo
from backend.src.utils import paths
from backend.src.utils.labels import LABEL_NAMES, label_name


# --- prediction volume -----------------------------------------------------

def summary():
    counts = predictions_repo.label_counts()
    averages = predictions_repo.average_metrics()

    avg_confidence = averages["avg_confidence"]
    avg_latency = averages["avg_latency_ms"]

    return {
        "total_predictions": sum(counts.values()),
        "class_counts": {
            "normal": counts[0],
            "offensive": counts[1],
            "hate": counts[2],
        },
        "avg_confidence": round(avg_confidence, 4) if avg_confidence else None,
        "avg_latency_ms": round(avg_latency, 1) if avg_latency else None,
    }


def trend(days=30):
    rows = predictions_repo.daily_trend(days)
    return {
        "days": days,
        "dates": [row["date"] for row in rows],
        "counts": [int(row["count"]) for row in rows],
    }


def language_intelligence():
    """Language volume plus a language x predicted-class matrix."""
    rows = predictions_repo.language_breakdown()

    distribution = {}
    matrix = {}

    for row in rows:
        language = row["lang"] or "unknown"
        count = int(row["count"])

        distribution[language] = distribution.get(language, 0) + count

        bucket = matrix.setdefault(
            language, {name: 0 for name in LABEL_NAMES.values()}
        )
        name = label_name(row["predicted_label"])
        if name in bucket:
            bucket[name] = count

    return {
        "language_distribution": distribution,
        "language_class_matrix": matrix,
    }


# --- trained model metrics -------------------------------------------------

def _macro_f1(report):
    """Pull macro-average F1 out of an sklearn classification_report dict."""
    if not isinstance(report, dict):
        return None
    macro = report.get("macro avg") or report.get("macro_avg")
    if isinstance(macro, dict):
        return macro.get("f1-score")
    return None


def model_metrics():
    """
    Per-model metrics from the last training run.

    Returns {"available": bool, "models": {...}, "source": path or None}.
    Callers must not fabricate numbers when `available` is false.
    """
    report_path = paths.TRAINING_REPORT_JSON

    if not os.path.exists(report_path):
        return {
            "available": False,
            "models": {},
            "source": None,
            "message": (
                "No training report found. Run the training pipeline to "
                "generate backend/reports/training_report_all.json."
            ),
        }

    try:
        with open(report_path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, ValueError) as exc:
        return {
            "available": False,
            "models": {},
            "source": report_path,
            "message": f"Training report could not be read: {exc}",
        }

    models = {}
    for name, payload in (raw or {}).items():
        if not isinstance(payload, dict):
            continue

        report = payload.get("report", {})
        models[name] = {
            "accuracy": payload.get("accuracy"),
            "macro_f1": _macro_f1(report),
            "precision": (report.get("macro avg") or {}).get("precision"),
            "recall": (report.get("macro avg") or {}).get("recall"),
            "support": (report.get("macro avg") or {}).get("support"),
        }

    return {
        "available": bool(models),
        "models": models,
        "source": os.path.relpath(report_path, paths.PROJECT_ROOT),
    }


# --- dataset ---------------------------------------------------------------

def dataset_stats():
    """
    Composition of the normalized training CSV.

    The old version read 'data/clean_data.csv' (wrong directory) and looked for
    a 'label' column; the file actually has (text, truelabel, lang).
    """
    csv_path = paths.CLEAN_DATA_CSV

    if not os.path.exists(csv_path):
        return {
            "available": False,
            "total_samples": 0,
            "language_distribution": {},
            "label_distribution": {},
            "message": (
                "clean_data.csv not found. Run "
                "python -m backend.src.data.normalize first."
            ),
        }

    try:
        frame = pd.read_csv(csv_path)
    except Exception as exc:
        return {
            "available": False,
            "total_samples": 0,
            "language_distribution": {},
            "label_distribution": {},
            "message": f"clean_data.csv could not be read: {exc}",
        }

    language_distribution = {}
    if "lang" in frame.columns:
        language_distribution = {
            str(key): int(value)
            for key, value in frame["lang"].value_counts().items()
        }

    label_distribution = {}
    label_column = "truelabel" if "truelabel" in frame.columns else "label"
    if label_column in frame.columns:
        counts = frame[label_column].value_counts()
        for key, value in counts.items():
            label_distribution[label_name(key, default=str(key))] = int(value)

    return {
        "available": True,
        "total_samples": int(len(frame)),
        "language_distribution": language_distribution,
        "label_distribution": label_distribution,
        "source": os.path.relpath(csv_path, paths.PROJECT_ROOT),
    }


# --- feedback / error analysis --------------------------------------------

def error_analysis(limit=50):
    """
    Where human corrections disagree with what the model predicted.

    The confusion matrix is keyed {actual_label: {predicted_label: count}} with
    human-readable names. The previous `.unstack().to_dict()` produced the
    transposed orientation with numeric keys, which the UI read as if it were
    the other way round.
    """
    rows = annotations_repo.prediction_disagreements(limit)

    if not rows:
        return {"confusion": {}, "samples": [], "total_compared": 0}

    confusion = {}
    samples = []

    for row in rows:
        actual = label_name(row["truelabel"])
        predicted = label_name(row["predicted_label"])

        bucket = confusion.setdefault(
            actual, {name: 0 for name in LABEL_NAMES.values()}
        )
        if predicted in bucket:
            bucket[predicted] += 1

        if row["truelabel"] != row["predicted_label"]:
            text = row["text"] or ""
            samples.append(
                {
                    "text": text[:120] + ("..." if len(text) > 120 else ""),
                    "language": row["lang"],
                    "predicted": row["predicted_label"],
                    "predicted_name": predicted,
                    "actual": row["truelabel"],
                    "actual_name": actual,
                }
            )

    return {
        "confusion": confusion,
        "samples": samples,
        "total_compared": len(rows),
        "total_mismatched": len(samples),
    }


def annotation_label_distribution():
    """Human feedback counts per label."""
    distribution = annotations_repo.label_distribution()
    counts = {name: 0 for name in LABEL_NAMES.values()}

    for label, count in distribution.items():
        name = label_name(label)
        if name in counts:
            counts[name] = count

    return {"counts": counts, "total": sum(counts.values())}


def survey_stats():
    """Participation counters plus the human label distribution."""
    return {
        "participation": survey_repo.overview(),
        "labels": annotation_label_distribution(),
    }


# --- drift -----------------------------------------------------------------

TREND_WINDOW = 20
MIN_TREND_SAMPLES = 10


def recent_label_trends(window=TREND_WINDOW, minimum=MIN_TREND_SAMPLES):
    """
    Change in label mix between the older and newer half of the recent window.

    Reports `sufficient_data: False` rather than erroring when the sample is
    too small -- the old endpoint returned HTTP 400 for this, which the Admin
    page could not distinguish from a real failure.
    """
    labels = predictions_repo.recent_labels(window)

    if len(labels) < minimum:
        return {
            "sufficient_data": False,
            "window_size": len(labels),
            "minimum_required": minimum,
            "trends": {},
        }

    # recent_labels is newest-first; reverse for chronological order.
    chronological = list(reversed(labels))
    midpoint = len(chronological) // 2
    previous, recent = chronological[:midpoint], chronological[midpoint:]

    trends = {}
    for label_id, name in LABEL_NAMES.items():
        previous_count = previous.count(label_id)
        current_count = recent.count(label_id)
        change = ((current_count - previous_count) / max(previous_count, 1)) * 100

        trends[name] = {
            "previous_count": previous_count,
            "current_count": current_count,
            "change_percent": round(change, 1),
        }

    return {
        "sufficient_data": True,
        "window_size": len(chronological),
        "trends": trends,
    }


# --- composed dashboard ----------------------------------------------------

def dashboard(trend_days=30, error_limit=50):
    """Everything the Analytics page needs, in one representation."""
    base = summary()
    return {
        **base,
        "trend": trend(trend_days),
        "models": model_metrics(),
        "language": language_intelligence(),
        "error_analysis": error_analysis(error_limit),
        "dataset": dataset_stats(),
    }
