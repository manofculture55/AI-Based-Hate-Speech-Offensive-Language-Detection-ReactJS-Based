"""
/api/v1/analytics

The composed dashboard view plus addressable sub-resources, so a client that
only needs the trend line does not have to pull the whole payload (which reads
a CSV and a JSON report from disk).
"""

from flask import Blueprint, jsonify, request

from backend.src.api.errors import ValidationError
from backend.src.services import analytics as service

bp = Blueprint("analytics", __name__)

MAX_TREND_DAYS = 365


def _days_param():
    raw = request.args.get("days", 30)
    try:
        days = int(raw)
    except (TypeError, ValueError):
        raise ValidationError(
            "'days' must be an integer.", details={"days": [f"got {raw!r}"]}
        )
    if not 1 <= days <= MAX_TREND_DAYS:
        raise ValidationError(
            f"'days' must be between 1 and {MAX_TREND_DAYS}.",
            details={"days": [f"got {days}"]},
        )
    return days


@bp.route("/analytics", methods=["GET"])
def get_analytics():
    """Everything the Analytics page renders, in one response."""
    return jsonify(service.dashboard(trend_days=_days_param()))


@bp.route("/analytics/summary", methods=["GET"])
def get_summary():
    return jsonify(service.summary())


@bp.route("/analytics/trend", methods=["GET"])
def get_trend():
    return jsonify(service.trend(_days_param()))


@bp.route("/analytics/languages", methods=["GET"])
def get_languages():
    return jsonify(service.language_intelligence())


@bp.route("/analytics/models", methods=["GET"])
def get_models():
    """
    Metrics from the last training run.

    Returns `available: false` when no report exists rather than the invented
    placeholder numbers the old endpoint served as if they were measured.
    """
    return jsonify(service.model_metrics())


@bp.route("/analytics/dataset", methods=["GET"])
def get_dataset():
    """Composition of the training corpus (previously computed but never served)."""
    return jsonify(service.dataset_stats())


@bp.route("/analytics/errors", methods=["GET"])
def get_errors():
    limit = request.args.get("limit", 50)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        raise ValidationError(
            "'limit' must be an integer.", details={"limit": [f"got {limit!r}"]}
        )
    if not 1 <= limit <= 500:
        raise ValidationError(
            "'limit' must be between 1 and 500.",
            details={"limit": [f"got {limit}"]},
        )
    return jsonify(service.error_analysis(limit))
