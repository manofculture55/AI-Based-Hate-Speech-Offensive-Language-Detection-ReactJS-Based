"""
Authentication decorators.

The admin header check used to be five copy-pasted `if request.headers.get(...)
!= ADMIN_KEY` blocks comparing against one of two identically-valued constants
(ADMIN_KEY / ADMIN_SECRET).  It is one decorator now, and comparisons use
`secrets.compare_digest` so they aren't timing-sensitive.
"""

import secrets
from functools import wraps

from flask import g, request

from backend.src.api.errors import Unauthorized
from backend.src.utils import config

API_KEY_HEADER = "X-API-KEY"
ADMIN_KEY_HEADER = "X-ADMIN-KEY"


def _matches(supplied, expected):
    if not supplied or not expected:
        return False
    return secrets.compare_digest(str(supplied), str(expected))


def _bearer_token():
    """Accept `Authorization: Bearer <key>` alongside the custom headers."""
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def has_valid_api_key():
    supplied = request.headers.get(API_KEY_HEADER) or _bearer_token()
    return _matches(supplied, config.API_KEY)


def has_valid_admin_key():
    supplied = request.headers.get(ADMIN_KEY_HEADER) or _bearer_token()
    return _matches(supplied, config.ADMIN_KEY)


def require_api_key(view):
    """Reject the request unless a valid API key is present."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not has_valid_api_key():
            raise Unauthorized(
                f"A valid {API_KEY_HEADER} header is required.",
                code="invalid_api_key",
            )
        g.api_client = "api"
        return view(*args, **kwargs)

    return wrapper


def optional_api_key(view):
    """
    Used by POST /predictions.

    - No key supplied: allowed, unless HSD_REQUIRE_API_KEY is set.
    - Key supplied and valid: allowed, and the request is tagged as 'api'.
    - Key supplied but wrong: rejected. Failing loudly beats silently
      downgrading a caller who believes they are authenticated.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        supplied = request.headers.get(API_KEY_HEADER) or _bearer_token()

        if supplied:
            if not _matches(supplied, config.API_KEY):
                raise Unauthorized("Invalid API key.", code="invalid_api_key")
            g.api_client = "api"
        elif config.REQUIRE_API_KEY:
            raise Unauthorized(
                f"A valid {API_KEY_HEADER} header is required.",
                code="invalid_api_key",
            )
        else:
            g.api_client = "web"

        return view(*args, **kwargs)

    return wrapper


def require_admin(view):
    """Reject the request unless a valid admin key is present."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not has_valid_admin_key():
            raise Unauthorized(
                f"A valid {ADMIN_KEY_HEADER} header is required.",
                code="admin_required",
            )
        g.api_client = "admin"
        return view(*args, **kwargs)

    return wrapper


def request_source(default="web"):
    """Which kind of caller produced the current request."""
    return getattr(g, "api_client", default)
