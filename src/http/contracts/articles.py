"""Public request and response shapes for /articles."""

from datetime import date
from typing import Any

from pydantic import model_serializer

from src.domain.articles import ArticleStatus
from src.http._base import PublicModel


class ArticleCreateRequest(PublicModel):
    author: str
    title: str
    slug: str
    summary: str
    body: str
    published_on: date


class ArticleUpdateRequest(PublicModel):
    # `slug` is in the URL path, not the body.
    title: str
    summary: str
    body: str
    published_on: date


class ArticleSummaryPublic(PublicModel):
    id: int
    author: str
    title: str
    slug: str
    summary: str
    status: ArticleStatus
    published_on: date


class ArticlePublic(ArticleSummaryPublic):
    body: str
    # reject_message is on the persistence row as a plain column. The
    # HTTP contract masks it unless the article is currently REJECTED
    # — it has no meaning in any other state, and exposing it would
    # leak internal lifecycle history into the public response.
    reject_message: str | None = None

    @model_serializer(mode="wrap")
    def _mask_reject_message(self, handler) -> dict[str, Any]:
        data = handler(self)
        if self.status != ArticleStatus.REJECTED:
            data.pop("reject_message", None)
        return data
