"""
Request body validation.

Handlers used to call `request.get_json()` and then `data.get("text")`.  When a
client sent no body, the wrong content type, or malformed JSON, `get_json()`
returned None (or raised) and `.get` blew up with an AttributeError -> HTML 500.
`load_body()` turns all of those into a clean 400/415/422.
"""

from flask import request
from marshmallow import EXCLUDE, Schema, ValidationError as MarshmallowValidationError
from marshmallow import fields, validate

from backend.src.api.errors import BadRequest, ValidationError
from backend.src.utils import config
from backend.src.utils.labels import VALID_LABELS, VALID_LANGUAGES


class _Base(Schema):
    class Meta:
        unknown = EXCLUDE  # tolerate extra keys rather than 422-ing on them


def load_body(schema):
    """Validate the JSON request body against `schema`, or raise an ApiError."""
    if not request.is_json:
        raise BadRequest(
            "Request body must be JSON with Content-Type: application/json.",
            status_code=415,
            code="unsupported_media_type",
        )

    try:
        raw = request.get_json(silent=False)
    except Exception:
        raise BadRequest("Request body is not valid JSON.", code="malformed_json")

    if raw is None:
        raise BadRequest("Request body is required.", code="missing_body")

    if not isinstance(raw, dict):
        raise BadRequest(
            "Request body must be a JSON object.", code="malformed_json"
        )

    try:
        return schema.load(raw)
    except MarshmallowValidationError as exc:
        raise ValidationError(
            "Request body failed validation.", details=exc.messages
        )


# --- predictions -----------------------------------------------------------

class PredictionCreateSchema(_Base):
    text = fields.String(
        required=True,
        validate=[
            validate.Length(
                min=1,
                max=config.MAX_API_TEXT_LENGTH,
                error=(
                    "Length must be between {min} and {max} characters."
                ),
            )
        ],
    )

    def load(self, data, **kwargs):
        # Trim before validating so "   " is rejected as empty, not accepted
        # as three characters.
        if isinstance(data, dict) and isinstance(data.get("text"), str):
            data = {**data, "text": data["text"].strip()}
        return super().load(data, **kwargs)


# --- annotations (human feedback) ------------------------------------------

class AnnotationCreateSchema(_Base):
    text = fields.String(required=True, validate=validate.Length(min=1))
    # `label` is the canonical name; `correct_label` is what the old
    # /feedback endpoint used, so both are accepted.
    label = fields.Integer(load_default=None, validate=validate.OneOf(VALID_LABELS))
    correct_label = fields.Integer(
        load_default=None, validate=validate.OneOf(VALID_LABELS)
    )
    language = fields.String(
        load_default=None, validate=validate.OneOf(VALID_LANGUAGES)
    )
    lang = fields.String(load_default=None, validate=validate.OneOf(VALID_LANGUAGES))
    prediction_id = fields.Integer(load_default=None)

    def load(self, data, **kwargs):
        result = super().load(data, **kwargs)

        label = result.get("label")
        if label is None:
            label = result.get("correct_label")
        if label is None:
            raise MarshmallowValidationError(
                {"label": ["Field is required (or send 'correct_label')."]}
            )
        result["label"] = label
        result.pop("correct_label", None)

        language = result.get("language") or result.get("lang")
        result["language"] = language
        result.pop("lang", None)

        return result


# --- flagged terms ---------------------------------------------------------

class FlaggedTermCreateSchema(_Base):
    words = fields.List(
        fields.String(),
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    # Accepts "Offensive"/"Hate" (what the UI sends) or 1/2.
    label = fields.Raw(required=True)


# --- survey ----------------------------------------------------------------

class SurveyVoteSchema(_Base):
    text = fields.String(required=True, validate=validate.Length(min=1))
    label = fields.Integer(load_default=None, validate=validate.OneOf(VALID_LABELS))
    user_label = fields.Integer(
        load_default=None, validate=validate.OneOf(VALID_LABELS)
    )

    def load(self, data, **kwargs):
        result = super().load(data, **kwargs)

        label = result.get("label")
        if label is None:
            label = result.get("user_label")
        if label is None:
            raise MarshmallowValidationError(
                {"label": ["Field is required (or send 'user_label')."]}
            )

        result["label"] = label
        result.pop("user_label", None)
        return result


# --- admin -----------------------------------------------------------------

class AdminSessionSchema(_Base):
    password = fields.String(required=True, validate=validate.Length(min=1))
