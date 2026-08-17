"""
/api/v1/flagged-terms

Community-reported words. Replaces POST /feedback/flag-words,
GET /flagged-terms and GET /admin/flagged-terms -- three routes over one
collection, two of which differed only in how much of each row they returned.
"""

from flask import Blueprint, jsonify, request

from backend.src.api.auth import require_admin
from backend.src.api.errors import NotFound, ValidationError
from backend.src.api.schemas import FlaggedTermCreateSchema, load_body
from backend.src.api import serializers
from backend.src.repositories import flagged_terms as repo
from backend.src.utils.labels import FLAG_CONTEXT_LABELS, label_from_name

bp = Blueprint("flagged_terms", __name__)

# Words below this frequency are treated as unconfirmed noise.
DEFAULT_MIN_FREQUENCY = 2


def _resolve_context_label(value):
    """Accept "Offensive"/"Hate" or 1/2 and normalise to the integer."""
    if isinstance(value, bool):
        label = None
    elif isinstance(value, int):
        label = value
    else:
        label = label_from_name(value)
        if label is None:
            try:
                label = int(str(value).strip())
            except (TypeError, ValueError):
                label = None

    if label not in FLAG_CONTEXT_LABELS:
        raise ValidationError(
            "'label' must be Offensive or Hate (1 or 2).",
            details={"label": [f"got {value!r}"]},
        )
    return label


@bp.route("/flagged-terms", methods=["POST"])
def create_flagged_terms():
    """
    Flag a batch of words (201).

    Reports exactly which words were created, which had their frequency bumped,
    and which were discarded as too short -- the old endpoint echoed back the
    raw input count regardless of what it actually stored.
    """
    body = load_body(FlaggedTermCreateSchema())
    context_label = _resolve_context_label(body["label"])

    result = repo.upsert_many(body["words"], context_label)

    return (
        jsonify(
            {
                "created": result["created"],
                "updated": result["updated"],
                "skipped": result["skipped"],
                "counts": {
                    "created": len(result["created"]),
                    "updated": len(result["updated"]),
                    "skipped": len(result["skipped"]),
                },
            }
        ),
        201,
    )


@bp.route("/flagged-terms", methods=["GET"])
def list_flagged_terms():
    """
    Flagged words at or above `min_frequency` (default 2).

    `words` is a flat convenience array for the highlighter in the UI; `data`
    carries the full rows for the admin table.
    """
    raw = request.args.get("min_frequency", DEFAULT_MIN_FREQUENCY)
    try:
        min_frequency = int(raw)
    except (TypeError, ValueError):
        raise ValidationError(
            "'min_frequency' must be an integer.",
            details={"min_frequency": [f"got {raw!r}"]},
        )
    if min_frequency < 1:
        raise ValidationError(
            "'min_frequency' must be 1 or greater.",
            details={"min_frequency": [f"got {min_frequency}"]},
        )

    rows = repo.list_terms(min_frequency=min_frequency)

    return jsonify(
        {
            "data": [serializers.flagged_term(row) for row in rows],
            "words": [row["word"] for row in rows],
            "total": len(rows),
            "min_frequency": min_frequency,
        }
    )


@bp.route("/flagged-terms/<word>", methods=["DELETE"])
@require_admin
def delete_flagged_term(word):
    """Remove a word from the flag list (admin only). 204 on success."""
    if not repo.delete_word(word):
        raise NotFound(f"No flagged term matching {word!r}.")
    return "", 204
