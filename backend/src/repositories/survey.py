"""Data access for the `survey_corrections` table (community label votes)."""

from backend.src.utils import db

COLUMNS = (
    "id, text, original_label, survey_count, vote_trace, resolved_label, "
    "is_resolved, updated_at"
)


def get_by_text(text):
    return db.query_one(
        f"SELECT {COLUMNS} FROM survey_corrections WHERE text = ?", (text,)
    )


def resolved_texts():
    """Set of texts that already reached consensus, so they can be skipped."""
    rows = db.query_all(
        "SELECT text FROM survey_corrections WHERE is_resolved = 1"
    )
    return {row["text"] for row in rows}


def record_vote(text, label, original_label, consensus_threshold=3):
    """
    Add one vote for `text` and re-evaluate consensus.

    `original_label` is the label the dataset currently carries.  The previous
    implementation stored the *voter's* label in `original_label` on first
    insert, which made the column meaningless.

    Returns the survey row as it stands after the vote.
    """
    label = int(label)

    with db.connection() as conn:
        row = conn.execute(
            "SELECT vote_trace, survey_count FROM survey_corrections WHERE text = ?",
            (text,),
        ).fetchone()

        if row is None:
            trace = str(label)
            count = 1
            conn.execute(
                """
                INSERT INTO survey_corrections
                    (text, original_label, survey_count, vote_trace, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    text,
                    None if original_label is None else int(original_label),
                    count,
                    trace,
                ),
            )
        else:
            trace = (row["vote_trace"] or "") + str(label)
            count = int(row["survey_count"] or 0) + 1
            conn.execute(
                """
                UPDATE survey_corrections
                SET vote_trace = ?, survey_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE text = ?
                """,
                (trace, count, text),
            )

        # Consensus = `threshold` votes for the same label. Counting occurrences
        # of a single digit in the trace string is only safe because labels are
        # 0-2; count explicitly so it stays correct if that ever changes.
        votes_for_label = sum(1 for char in trace if char == str(label))
        resolved = votes_for_label >= consensus_threshold

        if resolved:
            conn.execute(
                """
                UPDATE survey_corrections
                SET resolved_label = ?, is_resolved = 1, updated_at = CURRENT_TIMESTAMP
                WHERE text = ?
                """,
                (label, text),
            )

    return get_by_text(text), resolved


def overview():
    """Aggregate participation counters for the admin dashboard."""
    row = db.query_one(
        """
        SELECT
            COUNT(*)                        AS total_texts,
            COALESCE(SUM(survey_count), 0)  AS total_votes,
            COALESCE(SUM(is_resolved), 0)   AS resolved
        FROM survey_corrections
        """
    )

    total_texts = int(row["total_texts"]) if row else 0
    total_votes = int(row["total_votes"]) if row else 0
    resolved = int(row["resolved"]) if row else 0

    return {
        "total_texts": total_texts,
        "total_votes": total_votes,
        "resolved": resolved,
        "unresolved": total_texts - resolved,
        "avg_votes": round(total_votes / total_texts, 2) if total_texts else 0.0,
    }
