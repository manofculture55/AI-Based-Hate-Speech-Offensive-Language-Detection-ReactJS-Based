"""
/api/v1/survey

Replaces GET /survey/next, POST /survey/submit, GET /admin/survey-overview and
GET /admin/survey-labels.
"""

from flask import Blueprint, jsonify

from backend.src.api.auth import require_admin
from backend.src.api.errors import NotFound
from backend.src.api.schemas import SurveyVoteSchema, load_body
from backend.src.api import serializers
from backend.src.services import analytics as analytics_service
from backend.src.services import survey as service
from backend.src.utils import config
from backend.src.utils.labels import label_name

bp = Blueprint("survey", __name__)


@bp.route("/survey/items/next", methods=["GET"])
def get_next_item():
    """
    The next unlabelled text.

    404 with code `survey_exhausted` once everything is resolved -- the old
    endpoint returned 200 with {"message": "..."} and no text, so clients had
    to sniff for a missing field to notice.
    """
    item = service.next_item()

    if item is None:
        raise NotFound(
            "No texts are left to label. Thank you!",
            code="survey_exhausted",
        )

    return jsonify(item)


@bp.route("/survey/votes", methods=["POST"])
def create_vote():
    """
    Cast one vote (201).

    Returns the survey item's resulting state so the client can show progress
    toward consensus instead of a bare success message.
    """
    body = load_body(SurveyVoteSchema())

    row, resolved, corpus_updated = service.record_vote(
        text=body["text"], label=body["label"]
    )

    payload = {
        "item": serializers.survey_item(row),
        "vote": {
            "label": body["label"],
            "label_name": label_name(body["label"]),
        },
        "consensus": {
            "reached": resolved,
            "threshold": config.SURVEY_CONSENSUS_THRESHOLD,
            "corpus_updated": corpus_updated,
        },
    }

    return jsonify(payload), 201


@bp.route("/survey/stats", methods=["GET"])
@require_admin
def get_stats():
    """Participation counters plus the human label distribution."""
    return jsonify(analytics_service.survey_stats())
