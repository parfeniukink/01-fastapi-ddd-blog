"""Articles repository contract — the Bookshelf."""

import abc
import functools

from .entities import Article, ArticleDraft, ArticleSummary, ArticleUpdate


class BookshelfRepository(abc.ABC):
    """Interface to manage articles in the persistent storage"""

    def __init__(self) -> None:
        self._articles: list[ArticleSummary] = []
        self._last_loaded_article: Article | None = None

    @abc.abstractmethod
    async def load_articles(self) -> list[ArticleSummary]:
        """Query articles and preserve them in memory"""

    @abc.abstractmethod
    async def add_article(self, draft: ArticleDraft) -> Article:
        """Add a new article"""

    @abc.abstractmethod
    async def update_article(self, id: int, data: ArticleUpdate) -> Article:
        """Update existing article"""

    @functools.singledispatchmethod
    async def article(self, identifier) -> Article:
        """Polymorphic article retrieval by ID or Slug"""
        raise NotImplementedError(
            f"Unsupported identifier type: {type(identifier).__name__}"
        )

    @article.register
    async def _(self, identifier: int) -> Article:
        return await self._article_by_id(identifier)

    @article.register
    async def _(self, identifier: str) -> Article:
        return await self._article_by_slug(identifier)

    @abc.abstractmethod
    async def _article_by_id(self, identifier: int) -> Article:
        """Get article by id"""

    @abc.abstractmethod
    async def _article_by_slug(self, identifier: str) -> Article:
        """Get article by slug"""

    @functools.singledispatchmethod
    async def delete_article(self, identifier) -> None:
        """Polymorphic article removal by ID or Slug"""
        raise NotImplementedError(
            f"Unsupported identifier type: {type(identifier).__name__}"
        )

    @delete_article.register
    async def _(self, identifier: int) -> None:
        return await self._delete_by_id(identifier)

    @delete_article.register
    async def _(self, identifier: str) -> None:
        return await self._delete_by_slug(identifier)

    @abc.abstractmethod
    async def _delete_by_id(self, identifier: int) -> None:
        """Delete article by id"""

    @abc.abstractmethod
    async def _delete_by_slug(self, identifier: str) -> None:
        """Delete article by slug"""
