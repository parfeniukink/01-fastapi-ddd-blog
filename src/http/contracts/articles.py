"""Public request and response shapes for /articles."""

from datetime import date

from src.http._base import PublicModel


class ArticleCreateRequest(PublicModel):
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
    title: str
    slug: str
    summary: str
    published_on: date


class ArticlePublic(ArticleSummaryPublic):
    body: str
