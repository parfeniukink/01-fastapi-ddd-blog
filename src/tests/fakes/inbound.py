"""Fake external article source for tests."""

from collections.abc import AsyncIterator

from src.domain.articles import (
    ArticleDraft,
    ExternalArticleSource,
    ExternalSource,
)


class FakeArticleSource(ExternalArticleSource):
    """Yields a canned list of drafts, or raises an injected error."""

    def __init__(
        self,
        drafts: list[ArticleDraft] | None = None,
        kind: ExternalSource = ExternalSource.MEDIUM,
        error: Exception | None = None,
    ) -> None:
        self._drafts = drafts or []
        self.kind = kind
        self._error = error

    async def fetch(self, account: str) -> AsyncIterator[ArticleDraft]:
        if self._error is not None:
            raise self._error
        for draft in self._drafts:
            yield draft
