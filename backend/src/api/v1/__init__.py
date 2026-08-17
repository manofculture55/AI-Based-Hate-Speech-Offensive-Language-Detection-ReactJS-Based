"""
Assembles every v1 resource under a single versioned blueprint.

Nesting the resource blueprints inside `api_v1` means endpoint names are
namespaced (`api_v1.predictions.get_prediction`), which is what url_for uses to
build Location headers and pagination links.
"""

from flask import Blueprint

from backend.src.api.v1 import (
    admin,
    analytics,
    annotations,
    flagged_terms,
    meta,
    predictions,
    survey,
)
from backend.src.utils import config


def create_v1_blueprint():
    api_v1 = Blueprint("api_v1", __name__, url_prefix=config.API_PREFIX)

    for module in (
        meta,
        predictions,
        annotations,
        flagged_terms,
        analytics,
        survey,
        admin,
    ):
        api_v1.register_blueprint(module.bp)

    return api_v1
