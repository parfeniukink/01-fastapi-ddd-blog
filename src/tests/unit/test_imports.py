from datetime import date

import pytest

from src.application import articles as articles_use_cases
from src.domain.articles import ArticleDraft, ExternalSource
from src.domain.errors import ExternalSourceUnreachable
from src.tests.fakes.inbound import FakeArticleSource


def _draft(slug: str, title: str = "A post") -> ArticleDraft:
    return ArticleDraft(
        title=title,
        slug=slug,
        summary="Summary.",
        body="Body.",
        published_on=date(2024, 1, 1),
    )


@pytest.mark.asyncio
async def test_import_creates_new_drafts(repository) -> None:
    source = FakeArticleSource(drafts=[_draft("post-a"), _draft("post-b")])

    report = await articles_use_cases.import_account_articles(
        repository=repository,
        source=source,
        account="someone",
    )

    assert report.source == ExternalSource.MEDIUM
    assert report.account == "someone"
    assert report.imported == 2
    assert report.skipped == 0
    assert report.failed == 0


@pytest.mark.asyncio
async def test_import_skips_drafts_whose_slug_already_exists(
    seeded_repository,
) -> None:
    source = FakeArticleSource(
        drafts=[_draft("first-post"), _draft("new-post")],
    )

    report = await articles_use_cases.import_account_articles(
        repository=seeded_repository,
        source=source,
        account="someone",
    )

    assert report.imported == 1
    assert report.skipped == 1
    assert report.failed == 0


@pytest.mark.asyncio
async def test_import_counts_policy_violations_as_failed(repository) -> None:
    bad = _draft("post-c", title="A clickbait headline")  # stop word
    good = _draft("post-d")
    source = FakeArticleSource(drafts=[bad, good])

    report = await articles_use_cases.import_account_articles(
        repository=repository,
        source=source,
        account="someone",
    )

    assert report.failed == 1
    assert report.imported == 1


@pytest.mark.asyncio
async def test_import_propagates_source_errors(repository) -> None:
    source = FakeArticleSource(
        error=ExternalSourceUnreachable("network down"),
    )

    with pytest.raises(ExternalSourceUnreachable):
        await articles_use_cases.import_account_articles(
            repository=repository,
            source=source,
            account="someone",
        )
