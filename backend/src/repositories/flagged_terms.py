"""Data access for the `flagged_terms` table (community-reported words)."""

import re

from backend.src.utils import db

# Keep letters/marks/digits from any script (notably Devanagari U+0900-U+097F)
# and drop punctuation, emoji and whitespace.  This must stay in sync with the
# normalisation the frontend applies in FeedbackModal/Home.
_STRIP_PATTERN = re.compile(r"[^\wऀ-ॿ]", flags=re.UNICODE)

MIN_WORD_LENGTH = 2


def normalize_word(word):
    """Lowercase and strip punctuation. Returns '' for unusable input."""
    if not isinstance(word, str):
        return ""
    return _STRIP_PATTERN.sub("", word.strip().lower())


def upsert_many(words, context_label):
    """
    Insert new words, bump `frequency` for words already present.

    Returns a report so the caller can tell the client exactly what happened
    rather than echoing back a raw input count.
    """
    created, updated, skipped = [], [], []

    with db.connection() as conn:
        for raw in words:
            word = normalize_word(raw)

            if len(word) < MIN_WORD_LENGTH:
                skipped.append(raw)
                continue

            row = conn.execute(
                "SELECT id FROM flagged_terms WHERE word = ?", (word,)
            ).fetchone()

            if row:
                conn.execute(
                    """
                    UPDATE flagged_terms
                    SET frequency = frequency + 1,
                        context_label = ?
                    WHERE word = ?
                    """,
                    (int(context_label), word),
                )
                updated.append(word)
            else:
                conn.execute(
                    """
                    INSERT INTO flagged_terms (word, context_label, frequency)
                    VALUES (?, ?, 1)
                    """,
                    (word, int(context_label)),
                )
                created.append(word)

    return {"created": created, "updated": updated, "skipped": skipped}


def list_terms(min_frequency=2, context_label=None, limit=None):
    clauses = ["frequency >= ?"]
    params = [int(min_frequency)]

    if context_label is not None:
        clauses.append("context_label = ?")
        params.append(int(context_label))

    sql = f"""
        SELECT id, word, context_label, frequency, created_at
        FROM flagged_terms
        WHERE {' AND '.join(clauses)}
        ORDER BY frequency DESC, word ASC
    """

    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))

    return db.query_all(sql, tuple(params))


def delete_word(word):
    """True if the word existed and was removed."""
    normalized = normalize_word(word)
    if not normalized:
        return False
    return (
        db.execute_returning_rowcount(
            "DELETE FROM flagged_terms WHERE word = ?", (normalized,)
        )
        > 0
    )
