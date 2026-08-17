"""
/api/v1/predictions

Replaces POST /predict, POST /api/classify, GET /history and
GET /history/export with a single resource collection.
"""

import csv
import io

from flask import Blueprint, jsonify, request, url_for

from backend.src.api.auth import optional_api_key, request_source, require_admin
from backend.src.api.errors import NotAcceptable, NotFound, ValidationError
from backend.src.api.pagination import paginated, parse_page_params
from backend.src.api.schemas import PredictionCreateSchema, load_body
from backend.src.api import serializers
from backend.src.repositories import predictions as repo
from backend.src.services.classifier import classifier
from backend.src.utils.labels import VALID_LABELS, VALID_LANGUAGES, label_name

bp = Blueprint("predictions", __name__)


def _optional_label_filter():
    raw = request.args.get("label")
    if raw is None or raw == "":
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError(
            "'label' must be an integer.", details={"label": [f"got {raw!r}"]}
        )
    if value not in VALID_LABELS:
        raise ValidationError(
            "'label' must be one of 0, 1, 2.",
            details={"label": [f"got {value}"]},
        )
    return value


def _optional_lang_filter():
    value = request.args.get("lang")
    if not value:
        return None
    if value not in VALID_LANGUAGES:
        raise ValidationError(
            f"'lang' must be one of {', '.join(VALID_LANGUAGES)}.",
            details={"lang": [f"got {value!r}"]},
        )
    return value


# --- collection ------------------------------------------------------------

@bp.route("/predictions", methods=["POST"])
@optional_api_key
def create_prediction():
    """Classify a text, persist it, and return the created resource (201)."""
    body = load_body(PredictionCreateSchema())

    result = classifier.classify(body["text"])

    prediction_id = repo.create(
        text=body["text"],
        lang=result["language"],
        label=result["label"],
        score=result["confidence"],
        model_name=result["model_name"],
        latency_ms=result["latency_ms"],
        source=request_source(),
    )

    payload = {
        "id": prediction_id,
        "text": body["text"],
        "label": result["label"],
        "label_name": label_name(result["label"]),
        "confidence": result["confidence"],
        "probabilities": {
            label_name(index): value
            for index, value in enumerate(result["probabilities"])
        },
        "language": result["language"],
        "model": result["model_name"],
        "latency_ms": result["latency_ms"],
    }

    response = jsonify(payload)
    response.status_code = 201
    if prediction_id is not None:
        response.headers["Location"] = url_for(
            "api_v1.predictions.get_prediction", prediction_id=prediction_id
        )
    return response


@bp.route("/predictions", methods=["GET"])
def list_predictions():
    """Paginated prediction history, newest first."""
    page, per_page = parse_page_params()

    rows, total = repo.list_page(
        page=page,
        per_page=per_page,
        label=_optional_label_filter(),
        lang=_optional_lang_filter(),
        search=request.args.get("q") or None,
    )

    return jsonify(
        paginated(
            [serializers.prediction(row) for row in rows],
            total=total,
            page=page,
            per_page=per_page,
            endpoint="api_v1.predictions.list_predictions",
        )
    )


# --- export ----------------------------------------------------------------

# Declared before the /<int:id> rule so "export" is never read as an id.
def build_csv_export():
    """
    Build the CSV export response. Shared with the deprecated
    /history/export shim.
    """
    requested = (request.args.get("format") or "").lower()
    accept = request.accept_mimetypes

    if requested and requested != "csv":
        raise NotAcceptable(
            f"Unsupported export format {requested!r}. Supported: csv.",
            details={"supported": ["csv"]},
        )

    if not requested and not (
        accept.accept_html  # a browser click sends */* or text/html
        or accept["text/csv"]
        or str(accept) in ("", "*/*")
    ):
        raise NotAcceptable(
            "This endpoint can only produce text/csv.",
            details={"supported": ["text/csv"]},
        )

    rows = repo.list_all(
        label=_optional_label_filter(),
        lang=_optional_lang_filter(),
        search=request.args.get("q") or None,
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "text",
            "language",
            "label",
            "label_name",
            "confidence",
            "model",
            "latency_ms",
            "source",
            "created_at",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row["id"],
                row["text"],
                row["lang"],
                row["predicted_label"],
                label_name(row["predicted_label"]),
                row["score"],
                row["model_name"],
                row["latency_ms"],
                row.get("source") or "web",
                row["created_at"],
            ]
        )

    # utf-8-sig so Excel opens Devanagari text correctly.
    return (
        buffer.getvalue().encode("utf-8-sig"),
        200,
        {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": (
                "attachment; filename=prediction_history.csv"
            ),
        },
    )


@bp.route("/predictions/export", methods=["GET"])
def export_predictions():
    """
    CSV export of the full (optionally filtered) history.

    Honours `?format=csv` and `Accept: text/csv`; anything else is a 406
    rather than the old 400.
    """
    return build_csv_export()


# --- item ------------------------------------------------------------------

@bp.route("/predictions/<int:prediction_id>", methods=["GET"])
def get_prediction(prediction_id):
    """Fetch one prediction. The id returned by POST is now dereferenceable."""
    row = repo.get(prediction_id)
    if row is None:
        raise NotFound(f"No prediction with id {prediction_id}.")
    return jsonify(serializers.prediction(row))


@bp.route("/predictions/<int:prediction_id>", methods=["DELETE"])
@require_admin
def delete_prediction(prediction_id):
    """Remove one prediction (admin only). 204 on success."""
    if not repo.delete(prediction_id):
        raise NotFound(f"No prediction with id {prediction_id}.")
    return "", 204
