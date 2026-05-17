"""Article entities — the business shapes, including domain policies."""

from datetime import date

from src.domain.base import DomainModel
from src.domain.errors import ArticleContainsStopWord

from .policies import ArticleStatus, find_stop_word


class ArticleDraft(DomainModel):
    author: str
    title: str
    slug: str
    summary: str
    body: str
    published_on: date

    def validate_policies(self) -> None:
        """Enforce domain rules. Raises a `DomainError` subclass on failure."""

        _check_stop_words(title=self.title, summary=self.summary, body=self.body)


class ArticleUpdate(DomainModel):
    # No `slug` — slug is the identifier, not a mutable attribute.
    title: str
    summary: str
    body: str
    published_on: date

    def validate_policies(self) -> None:
        _check_stop_words(title=self.title, summary=self.summary, body=self.body)


class Article(ArticleDraft):
    id: int
    status: ArticleStatus = ArticleStatus.DRAFT
    # reject_message lives directly on the article row because we do
    # not keep a state-change audit table in this PoC. It is internal
    # state — the public HTTP contract masks it unless the article is
    # currently REJECTED.
    reject_message: str | None = None


class ArticleSummary(DomainModel):
    # Same as Article minus the body.
    id: int
    author: str
    title: str
    slug: str
    summary: str
    status: ArticleStatus
    published_on: date


def _check_stop_words(**fields: str) -> None:
    for name, value in fields.items():
        word = find_stop_word(value)
        if word is not None:
            raise ArticleContainsStopWord(field=name, word=word)
