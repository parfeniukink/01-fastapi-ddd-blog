from datetime import date

import pytest

from src.application import articles
from src.domain.articles import ArticleDraft, ArticleUpdate
from src.domain.errors import (
    ArticleContainsStopWord,
    ArticleNotFound,
    ArticleSlugAlreadyExists,
)


@pytest.mark.parametrize(
    "draft",
    [
        pytest.param(
            ArticleDraft(
                title="Short",
                slug="short",
                summary="Short summary",
                body="Body.",
                published_on=date(2024, 1, 1),
            ),
            id="short-title",
        ),
        pytest.param(
            ArticleDraft(
                title="Headline with multiple words",
                slug="headline-with-multiple-words",
                summary="A longer summary that spans several words.",
                body="Several sentences. With punctuation.",
                published_on=date(2024, 6, 15),
            ),
            id="multi-word-title",
        ),
        pytest.param(
            ArticleDraft(
                title="A" * 100,
                slug="very-long-title",
                summary="x",
                body="y",
                published_on=date(2023, 12, 31),
            ),
            id="max-length-title",
        ),
    ],
)
@pytest.mark.asyncio
async def test_publish_article_persists_various_drafts(
    repository, draft: ArticleDraft
) -> None:
    created = await articles.publish_article(repository, draft)
    fetched = await articles.get_article(repository, draft.slug)
    assert fetched == created


@pytest.mark.parametrize(
    "field, draft",
    [
        pytest.param(
            "title",
            ArticleDraft(
                title="Top 10 spam techniques",
                slug="t1",
                summary="ok",
                body="ok",
                published_on=date(2024, 1, 1),
            ),
            id="stop-word-in-title",
        ),
        pytest.param(
            "summary",
            ArticleDraft(
                title="Ok",
                slug="t2",
                summary="A clickbait piece",
                body="ok",
                published_on=date(2024, 1, 1),
            ),
            id="stop-word-in-summary",
        ),
        pytest.param(
            "body",
            ArticleDraft(
                title="Ok",
                slug="t3",
                summary="ok",
                body="It's a scam, trust me.",
                published_on=date(2024, 1, 1),
            ),
            id="stop-word-in-body",
        ),
    ],
)
@pytest.mark.asyncio
async def test_publish_article_rejects_drafts_with_stop_words(
    repository, field: str, draft: ArticleDraft
) -> None:
    with pytest.raises(ArticleContainsStopWord) as exc_info:
        await articles.publish_article(repository, draft)
    assert exc_info.value.field == field


@pytest.mark.asyncio
async def test_publish_article_rejects_duplicate_slug(
    repository, sample_draft: ArticleDraft
) -> None:
    await articles.publish_article(repository, sample_draft)

    with pytest.raises(ArticleSlugAlreadyExists) as exc_info:
        await articles.publish_article(repository, sample_draft)

    assert exc_info.value.slug == sample_draft.slug


@pytest.mark.asyncio
async def test_update_article_replaces_mutable_fields(
    repository, sample_draft: ArticleDraft
) -> None:
    await articles.publish_article(repository, sample_draft)
    update = ArticleUpdate(
        title="Edited",
        summary="Revised summary.",
        body="New body.",
        published_on=date(2024, 1, 2),
    )

    result = await articles.update_article(repository, sample_draft.slug, update)

    assert result.title == "Edited"
    assert result.slug == sample_draft.slug


@pytest.mark.asyncio
async def test_delete_article_removes_it(
    repository, sample_draft: ArticleDraft
) -> None:
    await articles.publish_article(repository, sample_draft)
    await articles.delete_article(repository, sample_draft.slug)

    with pytest.raises(ArticleNotFound):
        await articles.get_article(repository, sample_draft.slug)


@pytest.mark.asyncio
async def test_get_article_raises_when_slug_is_unknown(repository) -> None:
    with pytest.raises(ArticleNotFound):
        await articles.get_article(repository, "missing")


@pytest.mark.asyncio
async def test_article_lookup_is_polymorphic_on_int_and_str(
    repository, sample_draft: ArticleDraft
) -> None:
    created = await articles.publish_article(repository, sample_draft)
    by_slug = await repository.article(sample_draft.slug)
    by_id = await repository.article(created.id)
    assert by_slug == by_id == created
