"""
/api/v1 root and health check.

The index is generated from Flask's URL map, so it cannot drift out of sync
with the routes that actually exist.
"""

from flask import Blueprint, current_app, jsonify

from backend.src.services.classifier import classifier
from backend.src.utils import config

bp = Blueprint("meta", __name__)

_HIDDEN_METHODS = {"HEAD", "OPTIONS"}


def _describe_routes():
    routes = []
    for rule in current_app.url_map.iter_rules():
        if not str(rule).startswith(config.API_PREFIX):
            continue

        methods = sorted(set(rule.methods or ()) - _HIDDEN_METHODS)
        if not methods:
            continue

        view = current_app.view_functions.get(rule.endpoint)
        summary = None
        if view and view.__doc__:
            summary = view.__doc__.strip().splitlines()[0]

        routes.append(
            {"path": str(rule), "methods": methods, "summary": summary}
        )

    return sorted(routes, key=lambda route: route["path"])


@bp.route("/", methods=["GET"])
def index():
    """Machine-readable index of every endpoint in this API version."""
    return jsonify(
        {
            "name": config.API_TITLE,
            "version": config.API_VERSION,
            "base_path": config.API_PREFIX,
            "documentation": "docs/API.md",
            "authentication": {
                "api_key_header": "X-API-KEY",
                "admin_key_header": "X-ADMIN-KEY",
                "api_key_required_for_predictions": config.REQUIRE_API_KEY,
            },
            "endpoints": _describe_routes(),
        }
    )


@bp.route("/health", methods=["GET"])
def health():
    """Liveness plus model-readiness for monitoring."""
    status = classifier.status()

    return (
        jsonify(
            {
                "status": "ok" if status["loaded"] else "degraded",
                "version": config.API_VERSION,
                "model": status,
            }
        ),
        # Still 200 when degraded: the process is alive and most endpoints work.
        200,
    )
