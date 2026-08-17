"""Data access for the `training_jobs` table."""

from backend.src.utils import db

QUEUED = "queued"
RUNNING = "running"
SUCCEEDED = "succeeded"
FAILED = "failed"
INTERRUPTED = "interrupted"

TERMINAL_STATUSES = (SUCCEEDED, FAILED, INTERRUPTED)

COLUMNS = "id, status, detail, created_at, started_at, finished_at"


def create():
    return db.execute(
        "INSERT INTO training_jobs (status) VALUES (?)", (QUEUED,)
    )


def get(job_id):
    return db.query_one(
        f"SELECT {COLUMNS} FROM training_jobs WHERE id = ?", (job_id,)
    )


def list_recent(limit=20):
    return db.query_all(
        f"SELECT {COLUMNS} FROM training_jobs ORDER BY id DESC LIMIT ?",
        (int(limit),),
    )


def mark_running(job_id):
    db.execute(
        """
        UPDATE training_jobs
        SET status = ?, started_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (RUNNING, job_id),
    )


def mark_finished(job_id, status, detail=None):
    db.execute(
        """
        UPDATE training_jobs
        SET status = ?, detail = ?, finished_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, detail, job_id),
    )


def active_job():
    """The queued/running job, if any. Training must not run concurrently."""
    return db.query_one(
        f"""
        SELECT {COLUMNS} FROM training_jobs
        WHERE status IN (?, ?)
        ORDER BY id DESC
        LIMIT 1
        """,
        (QUEUED, RUNNING),
    )


def release_stale_jobs():
    """
    A job left queued/running by a killed process can never finish.  Called at
    startup so a crash doesn't permanently block future retrains.
    """
    return db.execute_returning_rowcount(
        """
        UPDATE training_jobs
        SET status = ?,
            detail = 'Server restarted before this job completed.',
            finished_at = CURRENT_TIMESTAMP
        WHERE status IN (?, ?)
        """,
        (INTERRUPTED, QUEUED, RUNNING),
    )
