"""Data access for the `predictions` table."""

from backend.src.utils import db

COLUMNS = (
    "id, text, lang, predicted_label, score, model_name, latency_ms, "
    "created_at, source"
)


def create(text, lang, label, score, model_name, latency_ms, source="web"):
    return db.execute(
        """
        INSERT INTO predictions
            (text, lang, predicted_label, score, model_name, latency_ms, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (text, lang, int(label), float(score), model_name, int(latency_ms), source),
    )


def get(prediction_id):
    return db.query_one(
        f"SELECT {COLUMNS} FROM predictions WHERE id = ?", (prediction_id,)
    )


def _filters(label=None, lang=None, search=None):
    """Build a parameterised WHERE clause from optional filters."""
    clauses = []
    params = []

    if label is not None:
        clauses.append("predicted_label = ?")
        params.append(int(label))

    if lang:
        clauses.append("lang = ?")
        params.append(lang)

    if search:
        clauses.append("text LIKE ?")
        params.append(f"%{search}%")

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def list_page(page, per_page, label=None, lang=None, search=None):
    """Return (rows, total) for one page, newest first."""
    where, params = _filters(label, lang, search)

    total = db.query_scalar(
        f"SELECT COUNT(*) FROM predictions{where}", tuple(params), default=0
    )

    offset = (page - 1) * per_page
    rows = db.query_all(
        f"""
        SELECT {COLUMNS}
        FROM predictions{where}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        tuple(params) + (per_page, offset),
    )

    return rows, int(total or 0)


def list_all(label=None, lang=None, search=None):
    """Every matching row, newest first. Used by the CSV export."""
    where, params = _filters(label, lang, search)
    return db.query_all(
        f"SELECT {COLUMNS} FROM predictions{where} ORDER BY id DESC",
        tuple(params),
    )


def delete(prediction_id):
    """True if a row was removed."""
    return (
        db.execute_returning_rowcount(
            "DELETE FROM predictions WHERE id = ?", (prediction_id,)
        )
        > 0
    )


def label_counts():
    """{0: n, 1: n, 2: n} with missing labels filled in as 0."""
    rows = db.query_all(
        """
        SELECT predicted_label AS label, COUNT(*) AS count
        FROM predictions
        GROUP BY predicted_label
        """
    )
    counts = {0: 0, 1: 0, 2: 0}
    for row in rows:
        label = row["label"]
        if label in counts:
            counts[label] = int(row["count"])
    return counts


def daily_trend(days=30):
    """Prediction volume per calendar day for the last `days` days."""
    return db.query_all(
        """
        SELECT DATE(created_at) AS date, COUNT(*) AS count
        FROM predictions
        WHERE created_at >= datetime('now', ?)
        GROUP BY DATE(created_at)
        ORDER BY date
        """,
        (f"-{int(days)} days",),
    )


def language_breakdown():
    """One row per (lang, predicted_label) pair with its count."""
    return db.query_all(
        """
        SELECT lang, predicted_label, COUNT(*) AS count
        FROM predictions
        GROUP BY lang, predicted_label
        """
    )


def recent_labels(limit=20):
    """The most recent `limit` predicted labels, newest first."""
    rows = db.query_all(
        "SELECT predicted_label FROM predictions ORDER BY id DESC LIMIT ?",
        (int(limit),),
    )
    return [row["predicted_label"] for row in rows]


def average_metrics():
    """Mean confidence and latency across all stored predictions."""
    row = db.query_one(
        """
        SELECT AVG(score) AS avg_score, AVG(latency_ms) AS avg_latency
        FROM predictions
        """
    )
    if not row:
        return {"avg_confidence": None, "avg_latency_ms": None}
    return {
        "avg_confidence": row["avg_score"],
        "avg_latency_ms": row["avg_latency"],
    }
