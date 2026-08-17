"""
Deprecated pre-v1 routes.

These keep every URL the old backend exposed working, returning the *original*
response shapes so existing callers (bookmarks, Postman collections, anything
already integrated) don't break.  A plain redirect would not do: the v1
resources return richer, differently-named fields.

Every response carries `Deprecation: true` and a
`Link: <...>; rel="successor-version"` header naming the replacement.

New work should target /api/v1 -- see docs/API.md.  Set
HSD_ENABLE_LEGACY_ROUTES=0 to drop this blueprint entirely.
"""

from flask import Blueprint, jsonify, make_response

from backend.src.api.auth import require_admin, require_api_key
from backend.src.api.pagination import parse_page_params
from backend.src.api.schemas import (
    AnnotationCreateSchema,
    FlaggedTermCreateSchema,
    PredictionCreateSchema,
    SurveyVoteSchema,
    load_body,
)
from backend.src.api.v1.admin import ingest_uploaded_dataset
from backend.src.api.v1.flagged_terms import _resolve_context_label
from backend.src.api.v1.predictions import build_csv_export
from backend.src.repositories import annotations as annotations_repo
from backend.src.repositories import flagged_terms as flagged_repo
from backend.src.repositories import predictions as predictions_repo
from backend.src.repositories import survey as survey_repo
from backend.src.services import analytics as analytics_service
from backend.src.services import survey as survey_service
from backend.src.services import training_jobs as training_service
from backend.src.services.classifier import classifier
from backend.src.utils import config
from backend.src.utils.labels import label_name

bp = Blueprint("legacy", __name__)

V1 = config.API_PREFIX


def _deprecated(result, successor):
    """Tag any view return value as deprecated in favour of `successor`."""
    response = make_response(result)
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = f'<{successor}>; rel="successor-version"'
    response.headers["X-API-Deprecation-Notice"] = (
        f"This endpoint is deprecated. Use {successor} instead."
    )
    return response


# --- predictions -----------------------------------------------------------

@bp.route("/predict", methods=["POST"])
def legacy_predict():
    """Deprecated. Use POST /api/v1/predictions."""
    body = load_body(PredictionCreateSchema())
    result = classifier.classify(body["text"])

    prediction_id = predictions_repo.create(
        text=body["text"],
        lang=result["language"],
        label=result["label"],
        score=result["confidence"],
        model_name=result["model_name"],
        latency_ms=result["latency_ms"],
        source="web",
    )

    return _deprecated(
        jsonify(
            {
                "label": result["label"],
                "confidence": result["confidence"],
                "language": result["language"],
                "latency_ms": result["latency_ms"],
                "prediction_id": prediction_id,
            }
        ),
        f"{V1}/predictions",
    )


@bp.route("/api/classify", methods=["POST"])
@require_api_key
def legacy_classify():
    """Deprecated. Use POST /api/v1/predictions."""
    body = load_body(PredictionCreateSchema())
    result = classifier.classify(body["text"])
    return _deprecated(jsonify({"label": result["label"]}), f"{V1}/predictions")


# --- history ---------------------------------------------------------------

@bp.route("/history", methods=["GET"])
def legacy_history():
    """Deprecated. Use GET /api/v1/predictions."""
    page, per_page = parse_page_params()
    rows, total = predictions_repo.list_page(page=page, per_page=per_page)

    # The old endpoint returned pre-formatted display strings; preserved here.
    data = [
        {
            "text": row["text"],
            "predicted_label": row["predicted_label"],
            "result": label_name(row["predicted_label"]),
            "score": f"{row['score']:.1%}",
            "latency_ms": f"{row['latency_ms']} ms",
            "created_at": str(row["created_at"]),
        }
        for row in rows
    ]

    pages = (total + per_page - 1) // per_page if per_page else 0

    return _deprecated(
        jsonify({"data": data, "total": total, "page": page, "pages": pages}),
        f"{V1}/predictions",
    )


@bp.route("/history/export", methods=["GET"])
def legacy_export():
    """Deprecated. Use GET /api/v1/predictions/export."""
    return _deprecated(build_csv_export(), f"{V1}/predictions/export")


# --- feedback --------------------------------------------------------------

@bp.route("/feedback", methods=["POST"])
def legacy_feedback():
    """Deprecated. Use POST /api/v1/annotations."""
    body = load_body(AnnotationCreateSchema())
    annotations_repo.create(
        text=body["text"],
        language=body.get("language"),
        label=body["label"],
        source="feedback",
    )
    return _deprecated(jsonify({"status": "feedback_saved"}), f"{V1}/annotations")


@bp.route("/feedback/flag-words", methods=["POST"])
def legacy_flag_words():
    """Deprecated. Use POST /api/v1/flagged-terms."""
    body = load_body(FlaggedTermCreateSchema())
    context_label = _resolve_context_label(body["label"])
    result = flagged_repo.upsert_many(body["words"], context_label)

    return _deprecated(
        jsonify(
            {
                "status": "ok",
                "flagged": len(result["created"]) + len(result["updated"]),
            }
        ),
        f"{V1}/flagged-terms",
    )


@bp.route("/flagged-terms", methods=["GET"])
def legacy_flagged_terms():
    """Deprecated. Use GET /api/v1/flagged-terms."""
    rows = flagged_repo.list_terms(min_frequency=2)
    return _deprecated(
        jsonify({"words": [row["word"] for row in rows]}), f"{V1}/flagged-terms"
    )


# --- analytics -------------------------------------------------------------

@bp.route("/analytics", methods=["GET"])
def legacy_analytics():
    """Deprecated. Use GET /api/v1/analytics."""
    return _deprecated(jsonify(analytics_service.dashboard()), f"{V1}/analytics")


# --- survey ----------------------------------------------------------------

@bp.route("/survey/next", methods=["GET"])
def legacy_survey_next():
    """Deprecated. Use GET /api/v1/survey/items/next."""
    item = survey_service.next_item()
    successor = f"{V1}/survey/items/next"

    if item is None:
        return _deprecated(
            jsonify({"message": "No more texts available for survey"}), successor
        )

    return _deprecated(
        jsonify(
            {"text": item["text"], "original_label": item["original_label"]}
        ),
        successor,
    )


@bp.route("/survey/submit", methods=["POST"])
def legacy_survey_submit():
    """Deprecated. Use POST /api/v1/survey/votes."""
    body = load_body(SurveyVoteSchema())
    survey_service.record_vote(text=body["text"], label=body["label"])
    return _deprecated(
        jsonify({"message": "Survey vote recorded successfully"}),
        f"{V1}/survey/votes",
    )


# --- admin -----------------------------------------------------------------

@bp.route("/admin/survey-labels", methods=["GET"])
@require_admin
def legacy_survey_labels():
    """Deprecated. Use GET /api/v1/survey/stats."""
    return _deprecated(
        jsonify(analytics_service.annotation_label_distribution()),
        f"{V1}/survey/stats",
    )


@bp.route("/admin/survey-overview", methods=["GET"])
@require_admin
def legacy_survey_overview():
    """Deprecated. Use GET /api/v1/survey/stats."""
    return _deprecated(jsonify(survey_repo.overview()), f"{V1}/survey/stats")


@bp.route("/admin/flagged-terms", methods=["GET"])
@require_admin
def legacy_admin_flagged_terms():
    """Deprecated. Use GET /api/v1/flagged-terms?min_frequency=1."""
    rows = flagged_repo.list_terms(min_frequency=1)
    return _deprecated(
        jsonify(
            {
                "data": [
                    {
                        "word": row["word"],
                        "context": label_name(row["context_label"]),
                        "frequency": row["frequency"],
                        "created_at": row["created_at"],
                    }
                    for row in rows
                ]
            }
        ),
        f"{V1}/flagged-terms",
    )


@bp.route("/admin/upload", methods=["POST"])
@require_admin
def legacy_admin_upload():
    """Deprecated. Use POST /api/v1/admin/datasets."""
    report = ingest_uploaded_dataset()
    return _deprecated(
        jsonify(
            {
                "status": "success",
                "rows_added": report.get("rows_added"),
                "saved_to": report.get("path"),
            }
        ),
        f"{V1}/admin/datasets",
    )


@bp.route("/admin/retrain", methods=["POST"])
@require_admin
def legacy_retrain():
    """Deprecated. Use POST /api/v1/admin/training-jobs."""
    job, created = training_service.start(on_complete=classifier.reload)

    # Deliberate behaviour change: this used to block the request (and the
    # whole dev server) for the entire duration of training.
    return _deprecated(
        (
            jsonify(
                {
                    "status": (
                        "training started"
                        if created
                        else "training already running"
                    ),
                    "job_id": job["id"],
                    "poll": f"{V1}/admin/training-jobs/{job['id']}",
                }
            ),
            202,
        ),
        f"{V1}/admin/training-jobs",
    )


@bp.route("/admin/trends", methods=["GET"])
@require_admin
def legacy_trends():
    """Deprecated. Use GET /api/v1/admin/trends."""
    return _deprecated(
        jsonify(analytics_service.recent_label_trends()), f"{V1}/admin/trends"
    )
