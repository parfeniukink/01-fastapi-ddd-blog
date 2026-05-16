"""Article entities — the business shapes, including domain policies."""

from datetime import date

from src.domain.articles.policies import find_stop_word
from src.domain.base import DomainModel
from src.domain.errors import ArticleContainsStopWord


class ArticleDraft(DomainModel):
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


class ArticleSummary(DomainModel):
    # Same as Article minus the body.
    id: int
    title: str
    slug: str
    summary: str
    published_on: date


def _check_stop_words(**fields: str) -> None:
    for name, value in fields.items():
        word = find_stop_word(value)
        if word is not None:
            raise ArticleContainsStopWord(field=name, word=word)
