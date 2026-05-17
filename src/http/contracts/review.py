"""Public shapes for the supervisor-side publication endpoints."""

from pydantic import Field

from src.http._base import PublicModel


class RejectRequest(PublicModel):
    """Body for ``POST /articles/{slug}/reject``.

    The supervisor MUST tell the author why the article was rejected
    — the message becomes the only piece of supervisor-emitted text
    persisted on the article, and the author needs it to revise.
    """

    reject_message: str = Field(min_length=1)


class CheckViolationPublic(PublicModel):
    code: str
    field: str | None
    reason: str


class ReviewPickupPublic(PublicModel):
    """Response shape for ``POST /articles/{slug}/review``.

    The article transitions to ``IN_REVIEW`` unconditionally; the
    editorial (cognitive) pipeline output is advisory and rides
    alongside as ``editorial_notes`` so the supervisor can read the
    LLM's grammar/consistency findings before deciding to approve
    or reject.
    """

    article: "ArticlePublic"
    editorial_notes: list[CheckViolationPublic]


# Imported at the bottom to break the cycle with articles.py
from src.http.contracts.articles import ArticlePublic  # noqa: E402

ReviewPickupPublic.model_rebuild()
