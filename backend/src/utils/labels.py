"""
The 0/1/2 -> name mapping used to live as a copy-pasted dict in seven
different functions.  It lives here now.
"""

NORMAL = 0
OFFENSIVE = 1
HATE = 2

LABEL_NAMES = {
    NORMAL: "Normal",
    OFFENSIVE: "Offensive",
    HATE: "Hate",
}

# Reverse lookup is case-insensitive because clients send "hate", "Hate", "HATE".
NAME_TO_LABEL = {name.lower(): value for value, name in LABEL_NAMES.items()}

VALID_LABELS = tuple(LABEL_NAMES)
VALID_LANGUAGES = ("en", "hi", "hi-en")

# Only these two make sense as a reason a word was flagged.
FLAG_CONTEXT_LABELS = (OFFENSIVE, HATE)


def label_name(value, default="Unknown"):
    """Label id -> human name. Never raises."""
    try:
        return LABEL_NAMES.get(int(value), default)
    except (TypeError, ValueError):
        return default


def label_from_name(name):
    """Human name -> label id, or None if unrecognised."""
    if not isinstance(name, str):
        return None
    return NAME_TO_LABEL.get(name.strip().lower())
