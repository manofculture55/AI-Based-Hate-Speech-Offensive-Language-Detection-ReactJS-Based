"""
SQLite access layer.

Two problems this replaces:

1. Connections were opened with bare `sqlite3.connect(...)` in a dozen places
   and closed only on the happy path, so every raised exception leaked a
   handle (on Windows that eventually locks the .db file).
2. `init_db()` only ever ran CREATE TABLE IF NOT EXISTS, so schema additions
   never reached an existing app.db.

`connection()` is a context manager that always closes and that commits or
rolls back as a unit.  `run_migrations()` applies additive changes to a
database that already holds data.
"""

import sqlite3
from contextlib import contextmanager

from backend.src.utils.paths import DATA_DIR, DB_PATH
import os


# --- connection handling ---------------------------------------------------

@contextmanager
def connection(readonly=False):
    """
    Yield a sqlite3 connection with Row access, committing on clean exit and
    rolling back on error.  Always closes.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    # Enforce the CHECK/UNIQUE constraints declared in the schema.
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        if not readonly:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_all(sql, params=()):
    """Run a SELECT and return a list of plain dicts."""
    with connection(readonly=True) as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def query_one(sql, params=()):
    """Run a SELECT and return the first row as a dict, or None."""
    with connection(readonly=True) as conn:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row is not None else None


def query_scalar(sql, params=(), default=None):
    """Run a SELECT and return the first column of the first row."""
    with connection(readonly=True) as conn:
        row = conn.execute(sql, params).fetchone()
        return default if row is None else row[0]


def execute(sql, params=()):
    """Run a write statement and return lastrowid."""
    with connection() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid


def execute_returning_rowcount(sql, params=()):
    """Run a write statement and return the number of affected rows."""
    with connection() as conn:
        cursor = conn.execute(sql, params)
        return cursor.rowcount


# --- schema ----------------------------------------------------------------

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        lang TEXT CHECK(lang IN ('hi','en','hi-en')),
        predicted_label INTEGER CHECK(predicted_label IN (0,1,2)),
        score REAL NOT NULL,
        model_name TEXT NOT NULL,
        latency_ms INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT,
        macro_f1 REAL,
        accuracy REAL,
        precision REAL,
        recall REAL,
        latency_p95_ms REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Human-supplied corrections ONLY. The normalized training corpus lives in
    # dataset_samples; keeping both in here is what clobbered this table.
    """
    CREATE TABLE IF NOT EXISTS annotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        lang TEXT,
        truelabel INTEGER,
        source TEXT,
        created_at TIMESTAMP
    )
    """,
    # The normalized dataset produced by backend.src.data.normalize.
    """
    CREATE TABLE IF NOT EXISTS dataset_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        truelabel INTEGER,
        lang TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS survey_corrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT UNIQUE,
        original_label INTEGER CHECK(original_label IN (0,1,2)),
        survey_count INTEGER DEFAULT 0,
        vote_trace TEXT DEFAULT '',
        resolved_label INTEGER CHECK(resolved_label IN (0,1,2)),
        is_resolved INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS flagged_terms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL UNIQUE,
        context_label INTEGER NOT NULL,   -- 1 = Offensive, 2 = Hate
        frequency INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Backs POST /api/v1/admin/training-jobs so a retrain survives a page reload.
    """
    CREATE TABLE IF NOT EXISTS training_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT NOT NULL DEFAULT 'queued',
        detail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP,
        finished_at TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_predictions_label ON predictions(predicted_label)",
    "CREATE INDEX IF NOT EXISTS idx_predictions_lang ON predictions(lang)",
    "CREATE INDEX IF NOT EXISTS idx_annotations_text ON annotations(text)",
    "CREATE INDEX IF NOT EXISTS idx_survey_resolved ON survey_corrections(is_resolved)",
    "CREATE INDEX IF NOT EXISTS idx_dataset_samples_text ON dataset_samples(text)",
)

DATASET_SAMPLES_DDL = """
    CREATE TABLE IF NOT EXISTS dataset_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        truelabel INTEGER,
        lang TEXT
    )
"""

ANNOTATIONS_DDL = """
    CREATE TABLE annotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        lang TEXT,
        truelabel INTEGER,
        source TEXT,
        created_at TIMESTAMP
    )
"""

# (table, column, definition) -- applied only when the column is absent.
# SQLite cannot ALTER ... ADD COLUMN with a non-constant default, so timestamp
# columns are added nullable and populated explicitly on insert.
MIGRATIONS = (
    ("predictions", "source", "TEXT DEFAULT 'web'"),
    ("annotations", "source", "TEXT"),
    ("annotations", "created_at", "TIMESTAMP"),
    ("survey_corrections", "created_at", "TIMESTAMP"),
)


def _existing_columns(conn, table):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def _table_exists(conn, table):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _repair_annotations_table(conn):
    """
    Undo the damage from `df.to_sql('annotations', if_exists='replace')`.

    That call replaced the declared annotations schema with a bare
    (text, truelabel, lang) frame holding the whole training corpus, so human
    feedback and corpus rows became indistinguishable -- and every normalize run
    wiped the feedback.

    The corpus rows are copied into dataset_samples (their proper home) and the
    annotations table is recreated with its real schema.  The copy is verified
    before the old table is dropped; on any mismatch the old table is renamed
    rather than removed, so no data can be lost.
    """
    if not _table_exists(conn, "annotations"):
        return None

    columns = _existing_columns(conn, "annotations")
    if "id" in columns:
        return None  # schema is intact, nothing to repair

    row_count = conn.execute("SELECT COUNT(*) FROM annotations").fetchone()[0]

    conn.execute(DATASET_SAMPLES_DDL)

    shared = [name for name in ("text", "truelabel", "lang") if name in columns]
    moved = 0
    if shared and row_count:
        column_list = ", ".join(shared)
        before = conn.execute("SELECT COUNT(*) FROM dataset_samples").fetchone()[0]
        conn.execute(
            f"INSERT INTO dataset_samples ({column_list}) "
            f"SELECT {column_list} FROM annotations"
        )
        after = conn.execute("SELECT COUNT(*) FROM dataset_samples").fetchone()[0]
        moved = after - before

    if moved == row_count:
        conn.execute("DROP TABLE annotations")
        note = f"moved {moved} corpus rows to dataset_samples"
    else:
        # Copy was incomplete -- keep the original around instead of dropping it.
        conn.execute("ALTER TABLE annotations RENAME TO annotations_corpus_backup")
        note = (
            f"copied {moved}/{row_count} rows; original kept as "
            "annotations_corpus_backup"
        )

    conn.execute(ANNOTATIONS_DDL)
    return f"annotations schema restored ({note})"


def run_migrations():
    """Apply additive schema changes to an existing database."""
    applied = []
    with connection() as conn:
        repaired = _repair_annotations_table(conn)
        if repaired:
            applied.append(repaired)

        for table, column, definition in MIGRATIONS:
            if not _table_exists(conn, table):
                continue
            if column in _existing_columns(conn, table):
                continue
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            applied.append(f"{table}.{column}")
    return applied


def init_db(verbose=True):
    """Create the schema then bring an existing database up to date."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with connection() as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)

    applied = run_migrations()

    if verbose:
        print(f"[DB] Initialized at: {DB_PATH}")
        if applied:
            print(f"[DB] Migrations applied: {', '.join(applied)}")
    return applied


if __name__ == "__main__":
    init_db()
