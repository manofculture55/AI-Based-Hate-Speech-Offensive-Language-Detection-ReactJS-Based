"""
One error shape for the entire API.

Before this, a bad request could produce `{"error": "Empty text"}`, a missing
route produced Flask's **HTML** 404 page, and an unhandled exception produced
an HTML traceback -- all of which made the frontend's `res.json()` throw a
SyntaxError instead of surfacing the real problem.

Every failure now leaves as JSON:

    {
      "error": {
        "code": "validation_error",
        "message": "text must not be empty",
        "details": {"text": ["must not be empty"]}
      },
      "status": 400
    }
"""

import traceback

from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Raise anywhere in a request to return a structured JSON error."""

    status_code = 400
    code = "bad_request"

    def __init__(self, message, status_code=None, code=None, details=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.details = details

    def to_response(self):
        payload = {
            "error": {
                "code": self.code,
                "message": self.message,
            },
            "status": self.status_code,
        }
        if self.details:
            payload["error"]["details"] = self.details
        return jsonify(payload), self.status_code


class BadRequest(ApiError):
    status_code = 400
    code = "bad_request"


class ValidationError(ApiError):
    status_code = 422
    code = "validation_error"


class Unauthorized(ApiError):
    status_code = 401
    code = "unauthorized"


class Forbidden(ApiError):
    status_code = 403
    code = "forbidden"


class NotFound(ApiError):
    status_code = 404
    code = "not_found"


class Conflict(ApiError):
    status_code = 409
    code = "conflict"


class NotAcceptable(ApiError):
    status_code = 406
    code = "not_acceptable"


class ServiceUnavailable(ApiError):
    status_code = 503
    code = "service_unavailable"


# Maps werkzeug's HTTP exceptions onto our machine-readable codes.
_HTTP_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    406: "not_acceptable",
    409: "conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    503: "service_unavailable",
}


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def _handle_api_error(exc):
        return exc.to_response()

    @app.errorhandler(HTTPException)
    def _handle_http_exception(exc):
        status = exc.code or 500
        payload = {
            "error": {
                "code": _HTTP_CODES.get(status, "http_error"),
                "message": exc.description or exc.name,
            },
            "status": status,
        }
        # 405 should tell the client which methods *are* allowed.
        allowed = getattr(exc, "valid_methods", None)
        if allowed:
            payload["error"]["details"] = {"allowed_methods": sorted(allowed)}
        return jsonify(payload), status

    @app.errorhandler(Exception)
    def _handle_unexpected(exc):
        # Log the full traceback server-side; never leak it to the client.
        app.logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
        return (
            jsonify(
                {
                    "error": {
                        "code": "internal_error",
                        "message": "An unexpected error occurred.",
                    },
                    "status": 500,
                }
            ),
            500,
        )
