"""
Row -> API resource conversion.

Note that numbers stay numbers.  `/history` used to return `"87.3%"` and
`"120 ms"` because it ran display formatting server-side; the frontend then
parsed those strings back into numbers to do arithmetic on them.  Formatting is
the client's job, so the API emits `0.873` and `120`.
"""

from backend.src.utils.labels import label_name


def prediction(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "text": row["text"],
        "label": row["predicted_label"],
        "label_name": label_name(row["predicted_label"]),
        "confidence": row["score"],
        "language": row["lang"],
        "model": row["model_name"],
        "latency_ms": row["latency_ms"],
        "source": row.get("source") or "web",
        "created_at": str(row["created_at"]) if row["created_at"] else None,
    }


def annotation(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "text": row["text"],
        "label": row["truelabel"],
        "label_name": label_name(row["truelabel"]),
        "language": row["lang"],
        "source": row.get("source"),
        "created_at": str(row["created_at"]) if row.get("created_at") else None,
    }


def flagged_term(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "word": row["word"],
        "context_label": row["context_label"],
        "context": label_name(row["context_label"]),
        "frequency": row["frequency"],
        "created_at": str(row["created_at"]) if row["created_at"] else None,
    }


def survey_item(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "text": row["text"],
        "original_label": row["original_label"],
        "original_label_name": label_name(row["original_label"], default=None),
        "vote_count": row["survey_count"],
        "is_resolved": bool(row["is_resolved"]),
        "resolved_label": row["resolved_label"],
        "resolved_label_name": label_name(row["resolved_label"], default=None),
        "updated_at": str(row["updated_at"]) if row["updated_at"] else None,
    }


def training_job(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "status": row["status"],
        "detail": row["detail"],
        "created_at": str(row["created_at"]) if row["created_at"] else None,
        "started_at": str(row["started_at"]) if row["started_at"] else None,
        "finished_at": str(row["finished_at"]) if row["finished_at"] else None,
    }
