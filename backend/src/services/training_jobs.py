"""
Background model retraining.

`POST /admin/retrain` used to call `run_training()` inline, holding the request
open for minutes: the browser timed out, the dev server served nothing else in
the meantime, and the client had no way to learn the outcome.

Training now runs on a worker thread behind a job resource -- the request
returns 202 immediately and the client polls
`GET /api/v1/admin/training-jobs/{id}`.
"""

import threading
import traceback

from backend.src.repositories import training_jobs as repo


def _run(job_id, on_complete=None):
    """Worker body. Imports training lazily -- it pulls in the whole TF stack."""
    try:
        repo.mark_running(job_id)

        from backend.src.training.train import run_training

        run_training()

        repo.mark_finished(job_id, repo.SUCCEEDED, "Training completed.")

        if on_complete:
            try:
                on_complete()
            except Exception as exc:  # reload failure must not fail the job
                print(f"  [Training] Post-training hook failed: {exc}")

    except Exception as exc:
        print(f"  [Training] Job {job_id} failed: {exc}")
        traceback.print_exc()
        # Keep the stored detail short; the traceback stays in the server log.
        repo.mark_finished(job_id, repo.FAILED, f"{type(exc).__name__}: {exc}"[:500])


def start(on_complete=None):
    """
    Queue a training run.

    Returns (job_row, created). `created` is False when a job is already in
    flight, in which case the existing job is returned instead of starting a
    second one -- concurrent training would corrupt the shared tokenizer.
    """
    existing = repo.active_job()
    if existing:
        return existing, False

    job_id = repo.create()

    thread = threading.Thread(
        target=_run,
        args=(job_id, on_complete),
        name=f"training-{job_id}",
        daemon=True,
    )
    thread.start()

    return repo.get(job_id), True


def get(job_id):
    return repo.get(job_id)


def list_recent(limit=20):
    return repo.list_recent(limit)
