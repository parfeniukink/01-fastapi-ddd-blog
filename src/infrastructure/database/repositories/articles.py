"""Article repository implementations.

Two implementations of the same domain contract:

- `InMemoryArticlesRepository` — used by tests.
- `SqlAlchemyArticlesRepository` — used by the running app. Inherits
  the session + flush plumbing from `SqlAlchemyDAL`.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.articles import (
    Article,
    ArticleDraft,
    ArticleSummary,
    ArticleUpdate,
    BookshelfRepository,
)
from src.domain.errors import ArticleNotFound, ArticleSlugAlreadyExists
from src.infrastructure.database.dal import SqlAlchemyDAL
from src.infrastructure.database.tables import ArticlesTable


class InMemoryArticlesRepository(BookshelfRepository):
    def __init__(self, items: list[Article] | None = None) -> None:
        BookshelfRepository.__init__(self)
        seed = (
            items
            if items is not None
            else [
                Article(
                    id=1,
                    title="DDD blog intro",
                    slug="ddd-blog-intro",
                    summary="A small article used as a teaching example.",
                    body="This body is stored by the infrastructure implementation.",
                    published_on=date(2024, 3, 1),
                )
            ]
        )
        self._by_slug: dict[str, Article] = {item.slug: item for item in seed}
        self._by_id: dict[int, Article] = {item.id: item for item in seed}
        self._next_id: int = max(self._by_id, default=0) + 1

    async def load_articles(self) -> list[ArticleSummary]:
        self._articles = [
            ArticleSummary(
                id=a.id,
                title=a.title,
                slug=a.slug,
                summary=a.summary,
                published_on=a.published_on,
            )
            for a in self._by_id.values()
        ]
        return self._articles

    async def add_article(self, draft: ArticleDraft) -> Article:
        if draft.slug in self._by_slug:
            raise ArticleSlugAlreadyExists(draft.slug)
        article = Article(id=self._next_id, **draft.model_dump())
        self._by_slug[article.slug] = article
        self._by_id[article.id] = article
        self._next_id += 1
        return article

    async def update_article(self, id: int, data: ArticleUpdate) -> Article:
        try:
            existing = self._by_id[id]
        except KeyError as exc:
            raise ArticleNotFound(id) from exc
        updated = existing.model_copy(update=data.model_dump())
        self._by_id[id] = updated
        self._by_slug[updated.slug] = updated
        return updated

    async def _article_by_id(self, identifier: int) -> Article:
        try:
            return self._by_id[identifier]
        except KeyError as exc:
            raise ArticleNotFound(identifier) from exc

    async def _article_by_slug(self, identifier: str) -> Article:
        try:
            return self._by_slug[identifier]
        except KeyError as exc:
            raise ArticleNotFound(identifier) from exc

    async def _delete_by_id(self, identifier: int) -> None:
        try:
            article = self._by_id.pop(identifier)
        except KeyError as exc:
            raise ArticleNotFound(identifier) from exc
        self._by_slug.pop(article.slug, None)

    async def _delete_by_slug(self, identifier: str) -> None:
        try:
            article = self._by_slug.pop(identifier)
        except KeyError as exc:
            raise ArticleNotFound(identifier) from exc
        self._by_id.pop(article.id, None)


class SqlAlchemyArticlesRepository(SqlAlchemyDAL, BookshelfRepository):
    def __init__(self, session: AsyncSession | None = None) -> None:
        SqlAlchemyDAL.__init__(self, session)
        BookshelfRepository.__init__(self)

    async def load_articles(self) -> list[ArticleSummary]:
        stmt = select(
            ArticlesTable.id,
            ArticlesTable.title,
            ArticlesTable.slug,
            ArticlesTable.summary,
            ArticlesTable.published_on,
        )
        rows = (await self.session.execute(stmt)).all()
        self._articles = [
            ArticleSummary(
                id=row.id,
                title=row.title,
                slug=row.slug,
                summary=row.summary,
                published_on=row.published_on,
            )
            for row in rows
        ]
        return self._articles

    async def add_article(self, draft: ArticleDraft) -> Article:
        row = ArticlesTable(**draft.model_dump())
        self.session.add(row)
        try:
            await self.flush()
        except IntegrityError as exc:
            if _is_unique_slug_violation(exc):
                raise ArticleSlugAlreadyExists(draft.slug) from exc
            raise
        return self._to_entity(row)

    async def update_article(self, id: int, data: ArticleUpdate) -> Article:
        row = await self._fetch_row_by_id(id)
        for field, value in data.model_dump().items():
            setattr(row, field, value)
        await self.flush()
        return self._to_entity(row)

    async def _article_by_id(self, identifier: int) -> Article:
        return self._to_entity(await self._fetch_row_by_id(identifier))

    async def _article_by_slug(self, identifier: str) -> Article:
        return self._to_entity(await self._fetch_row_by_slug(identifier))

    async def _delete_by_id(self, identifier: int) -> None:
        row = await self._fetch_row_by_id(identifier)
        await self.session.delete(row)
        await self.flush()

    async def _delete_by_slug(self, identifier: str) -> None:
        row = await self._fetch_row_by_slug(identifier)
        await self.session.delete(row)
        await self.flush()

    async def _fetch_row_by_id(self, identifier: int) -> ArticlesTable:
        stmt = select(ArticlesTable).where(ArticlesTable.id == identifier)
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise ArticleNotFound(identifier)
        return row

    async def _fetch_row_by_slug(self, identifier: str) -> ArticlesTable:
        stmt = select(ArticlesTable).where(ArticlesTable.slug == identifier)
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise ArticleNotFound(identifier)
        return row

    @staticmethod
    def _to_entity(row: ArticlesTable) -> Article:
        return Article(
            id=row.id,
            title=row.title,
            slug=row.slug,
            summary=row.summary,
            body=row.body,
            published_on=row.published_on,
        )


def _is_unique_slug_violation(exc: IntegrityError) -> bool:
    message = str(getattr(exc, "orig", exc)).lower()
    return "unique" in message and "slug" in message
