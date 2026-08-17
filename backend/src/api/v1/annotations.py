"""
/api/v1/annotations

Human corrections of model output. Replaces POST /feedback, which returned
{"status": "feedback_saved"} with a 200 and gave the client no way to read
back what it had created.
"""

from flask import Blueprint, jsonify, url_for

from backend.src.api.auth import require_admin
from backend.src.api.pagination import paginated, parse_page_params
from backend.src.api.schemas import AnnotationCreateSchema, load_body
from backend.src.api import serializers
from backend.src.repositories import annotations as repo

bp = Blueprint("annotations", __name__)


@bp.route("/annotations", methods=["POST"])
def create_annotation():
    """Record the label a human says is correct for a text (201)."""
    body = load_body(AnnotationCreateSchema())

    annotation_id = repo.create(
        text=body["text"],
        language=body.get("language"),
        label=body["label"],
        source="feedback",
    )

    response = jsonify(serializers.annotation(repo.get(annotation_id)))
    response.status_code = 201
    response.headers["Location"] = url_for(
        "api_v1.annotations.get_annotation", annotation_id=annotation_id
    )
    return response


@bp.route("/annotations", methods=["GET"])
@require_admin
def list_annotations():
    """Paginated feedback log (admin only -- it contains user-submitted text)."""
    page, per_page = parse_page_params()
    rows, total = repo.list_page(page, per_page)

    return jsonify(
        paginated(
            [serializers.annotation(row) for row in rows],
            total=total,
            page=page,
            per_page=per_page,
            endpoint="api_v1.annotations.list_annotations",
        )
    )


@bp.route("/annotations/<int:annotation_id>", methods=["GET"])
@require_admin
def get_annotation(annotation_id):
    from backend.src.api.errors import NotFound

    row = repo.get(annotation_id)
    if row is None:
        raise NotFound(f"No annotation with id {annotation_id}.")
    return jsonify(serializers.annotation(row))
