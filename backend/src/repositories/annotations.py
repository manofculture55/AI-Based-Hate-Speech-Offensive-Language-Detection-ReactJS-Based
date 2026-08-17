"""Data access for the `annotations` table (human-supplied correct labels)."""

from backend.src.utils import db


def create(text, language, label, source="feedback"):
    return db.execute(
        """
        INSERT INTO annotations (text, lang, truelabel, source, created_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (text, language, int(label), source),
    )


def get(annotation_id):
    return db.query_one(
        """
        SELECT id, text, lang, truelabel, source, created_at
        FROM annotations WHERE id = ?
        """,
        (annotation_id,),
    )


def list_page(page, per_page):
    total = db.query_scalar("SELECT COUNT(*) FROM annotations", default=0)
    offset = (page - 1) * per_page
    rows = db.query_all(
        """
        SELECT id, text, lang, truelabel, source, created_at
        FROM annotations
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        (per_page, offset),
    )
    return rows, int(total or 0)


def label_distribution():
    """{label_id: count} across every annotation."""
    rows = db.query_all(
        """
        SELECT truelabel AS label, COUNT(*) AS count
        FROM annotations
        WHERE truelabel IS NOT NULL
        GROUP BY truelabel
        """
    )
    return {int(row["label"]): int(row["count"]) for row in rows}


def prediction_disagreements(limit=50):
    """
    Annotations paired with the matching prediction, for error analysis.

    Joins on the most recent prediction for the same (text, lang).
    """
    return db.query_all(
        """
        SELECT
            p.text          AS text,
            p.lang          AS lang,
            p.predicted_label AS predicted_label,
            a.truelabel     AS truelabel
        FROM annotations a
        JOIN predictions p
          ON p.id = (
                SELECT id FROM predictions
                WHERE text = a.text
                  AND (lang = a.lang OR (lang IS NULL AND a.lang IS NULL))
                ORDER BY created_at DESC, id DESC
                LIMIT 1
             )
        ORDER BY a.id DESC
        LIMIT ?
        """,
        (int(limit),),
    )
