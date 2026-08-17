"""
SUPERSEDED -- kept only so existing imports of `survey_bp` keep resolving.

The survey used to be implemented here as a Flask blueprint that mixed HTTP
handling, SQL and CSV rewriting in two functions.  It now lives in:

    backend/src/services/survey.py   corpus loading, voting, consensus
    backend/src/repositories/survey.py   SQL
    backend/src/api/v1/survey.py     HTTP  (GET  /api/v1/survey/items/next
                                            POST /api/v1/survey/votes
                                            GET  /api/v1/survey/stats)

The pre-v1 URLs (/survey/next, /survey/submit) are served as deprecated shims
from backend/src/api/legacy.py, so nothing that called them has broken.

Do not add routes here.
"""

from backend.src.api.v1.survey import bp as survey_bp

__all__ = ["survey_bp"]
