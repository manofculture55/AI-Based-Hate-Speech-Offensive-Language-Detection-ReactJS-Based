"""
/api/v1/admin

Replaces /admin/upload, /admin/retrain, /admin/trends, /admin/flagged-terms,
/admin/survey-overview and /admin/survey-labels.
"""

import secrets

import pandas as pd
from flask import Blueprint, jsonify, request, url_for

from backend.src.api.auth import require_admin
from backend.src.api.errors import BadRequest, NotFound, Unauthorized, ValidationError
from backend.src.api.schemas import AdminSessionSchema, load_body
from backend.src.api import serializers
from backend.src.services import analytics as analytics_service
from backend.src.services import datasets as dataset_service
from backend.src.services import training_jobs as training_service
from backend.src.services.classifier import classifier
from backend.src.utils import config

bp = Blueprint("admin", __name__)


# --- sessions --------------------------------------------------------------

@bp.route("/admin/sessions", methods=["POST"])
def create_session():
    """
    Exchange the admin password for the admin key (201).

    The React app previously hardcoded the admin key in its bundle and checked
    the password client-side (`if (password === "admin123")`), so the key was
    readable by anyone who opened devtools and the check was trivially
    bypassable. The password is verified here instead.
    """
    body = load_body(AdminSessionSchema())

    if not secrets.compare_digest(body["password"], config.ADMIN_PASSWORD):
        raise Unauthorized("Incorrect password.", code="invalid_credentials")

    return (
        jsonify({"token": config.ADMIN_KEY, "token_type": "admin_key"}),
        201,
    )


@bp.route("/admin/sessions/current", methods=["DELETE"])
@require_admin
def delete_session():
    """Log out. Stateless -- the client discards its stored token."""
    return "", 204


# --- datasets --------------------------------------------------------------

def ingest_uploaded_dataset():
    """
    Validate and append the uploaded CSV. Returns a plain report dict.

    Shared by the v1 route and the deprecated /admin/upload shim.
    """
    if "file" not in request.files:
        raise BadRequest(
            "A multipart form field named 'file' is required.",
            code="missing_file",
        )

    upload = request.files["file"]

    if not upload.filename:
        raise BadRequest("No file was selected.", code="missing_file")

    if not upload.filename.lower().endswith(".csv"):
        raise ValidationError(
            "Only .csv uploads are accepted.",
            details={"filename": [upload.filename]},
        )

    try:
        frame = pd.read_csv(upload.stream)
    except Exception as exc:
        raise ValidationError(f"The CSV could not be parsed: {exc}")

    normalized, report = dataset_service.normalize_upload(frame)

    if normalized.empty:
        raise ValidationError(
            "No usable rows found in the upload.", details=report
        )

    result = dataset_service.append_to_corpus(normalized)

    # The survey reads the same file.
    from backend.src.services import survey as survey_service

    survey_service.invalidate_cache()

    return {**report, **result}


@bp.route("/admin/datasets", methods=["POST"])
@require_admin
def upload_dataset():
    """
    Append a labelled CSV to the training corpus (201).

    Accepts `truelabel` or `label` as the label column; the old endpoint
    demanded `label` and wrote it through unchanged, which the trainer -- which
    reads `truelabel` -- then ignored entirely.
    """
    return jsonify(ingest_uploaded_dataset()), 201


@bp.route("/admin/datasets", methods=["GET"])
@require_admin
def get_dataset():
    """Current composition of the training corpus."""
    return jsonify(analytics_service.dataset_stats())


# --- training jobs ---------------------------------------------------------

@bp.route("/admin/training-jobs", methods=["POST"])
@require_admin
def create_training_job():
    """
    Queue a retrain and return 202 immediately.

    Training used to run inline, holding the connection open for minutes while
    blocking every other request on the dev server.
    """
    job, created = training_service.start(on_complete=classifier.reload)

    status = 202 if created else 409
    payload = serializers.training_job(job)

    if not created:
        payload = {
            **payload,
            "message": "A training job is already in progress.",
        }

    response = jsonify(payload)
    response.status_code = status
    response.headers["Location"] = url_for(
        "api_v1.admin.get_training_job", job_id=job["id"]
    )
    return response


@bp.route("/admin/training-jobs", methods=["GET"])
@require_admin
def list_training_jobs():
    jobs = training_service.list_recent()
    return jsonify(
        {"data": [serializers.training_job(job) for job in jobs], "total": len(jobs)}
    )


@bp.route("/admin/training-jobs/<int:job_id>", methods=["GET"])
@require_admin
def get_training_job(job_id):
    """Poll a queued/running/succeeded/failed job."""
    job = training_service.get(job_id)
    if job is None:
        raise NotFound(f"No training job with id {job_id}.")
    return jsonify(serializers.training_job(job))


# --- trends ----------------------------------------------------------------

@bp.route("/admin/trends", methods=["GET"])
@require_admin
def get_trends():
    """
    Shift in label mix between the older and newer half of the recent window.

    Returns 200 with `sufficient_data: false` when there aren't enough
    predictions yet; this used to be a 400, which the Admin page treated as a
    failure and silently rendered nothing for.
    """
    return jsonify(analytics_service.recent_label_trends())
