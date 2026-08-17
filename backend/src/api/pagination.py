"""
Pagination parsing and the shared collection envelope.

`/history` used to do `int(request.args.get("page", 1))`, so `?page=abc` raised
ValueError and returned a 500.  Query parameters are validated here instead.
"""

from flask import request, url_for

from backend.src.api.errors import ValidationError
from backend.src.utils import config


def _positive_int(name, default, maximum=None):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default

    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError(
            f"'{name}' must be an integer.",
            details={name: [f"got {raw!r}"]},
        )

    if value < 1:
        raise ValidationError(
            f"'{name}' must be 1 or greater.",
            details={name: [f"got {value}"]},
        )

    if maximum is not None and value > maximum:
        raise ValidationError(
            f"'{name}' must not exceed {maximum}.",
            details={name: [f"got {value}"]},
        )

    return value


def parse_page_params():
    """Return (page, per_page). Accepts `limit` as an alias for `per_page`."""
    page = _positive_int("page", 1)

    per_page_arg = "per_page" if request.args.get("per_page") is not None else "limit"
    per_page = _positive_int(
        per_page_arg,
        config.DEFAULT_PAGE_SIZE,
        maximum=config.MAX_PAGE_SIZE,
    )

    return page, per_page


def _page_url(endpoint, page, per_page):
    args = {key: value for key, value in request.args.items()}
    args.pop("limit", None)
    args["page"] = page
    args["per_page"] = per_page
    try:
        return url_for(endpoint, _external=False, **args)
    except Exception:  # endpoint not resolvable (e.g. outside a request context)
        return None


def paginated(items, total, page, per_page, endpoint=None):
    """
    Build the standard collection body.

    `total` and `pages` are also mirrored at the top level because the existing
    History page reads `data` and `pages` directly.
    """
    pages = (total + per_page - 1) // per_page if per_page else 0

    body = {
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_prev": page > 1,
            "has_next": page < pages,
        },
        # Kept flat for backwards compatibility with the current frontend.
        "total": total,
        "page": page,
        "pages": pages,
    }

    if endpoint:
        links = {"self": _page_url(endpoint, page, per_page)}
        if page > 1:
            links["prev"] = _page_url(endpoint, page - 1, per_page)
            links["first"] = _page_url(endpoint, 1, per_page)
        if page < pages:
            links["next"] = _page_url(endpoint, page + 1, per_page)
            links["last"] = _page_url(endpoint, pages, per_page)
        body["links"] = links

    return body
