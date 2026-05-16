"""Article use cases — orchestrate over the Bookshelf contract."""

from src.domain.articles import (
    Article,
    ArticleDraft,
    ArticleSummary,
    ArticleUpdate,
    BookshelfRepository,
)


async def articles_list(
    repository: BookshelfRepository,
) -> list[ArticleSummary]:
    return await repository.load_articles()


async def get_article(
    repository: BookshelfRepository,
    slug: str,
) -> Article:
    return await repository.article(slug)


async def publish_article(
    repository: BookshelfRepository,
    draft: ArticleDraft,
) -> Article:
    draft.validate_policies()
    return await repository.add_article(draft)


async def update_article(
    repository: BookshelfRepository,
    slug: str,
    data: ArticleUpdate,
) -> Article:
    data.validate_policies()
    existing = await repository.article(slug)
    return await repository.update_article(existing.id, data)


async def delete_article(
    repository: BookshelfRepository,
    slug: str,
) -> None:
    await repository.delete_article(slug)
