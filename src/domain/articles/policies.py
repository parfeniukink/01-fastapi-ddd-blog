"""Domain policies — business rules enforced on the article aggregate."""


STOP_WORDS: frozenset[str] = frozenset({"spam", "clickbait", "scam"})


def find_stop_word(text: str) -> str | None:
    """Return the first stop word found in `text`, or None if clean."""
    lowered = text.lower()
    for word in STOP_WORDS:
        if word in lowered:
            return word
    return None
