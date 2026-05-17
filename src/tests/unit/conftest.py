"""Fixtures for unit tests."""

from datetime import date

import pytest

from src.domain.articles import Article, ArticleDraft, ArticleStatus
from src.tests.fakes.articles import InMemoryArticlesRepository
from src.tests.fakes.cognitive import FakeCognitiveLayer


@pytest.fixture
def repository() -> InMemoryArticlesRepository:
    return InMemoryArticlesRepository(items=[])


@pytest.fixture
def sample_draft() -> ArticleDraft:
    return ArticleDraft(
        author="jane.doe",
        title="First post",
        slug="first-post",
        summary="A summary.",
        body="Hello.",
        published_on=date(2024, 1, 1),
    )


@pytest.fixture
def seeded_repository(sample_draft: ArticleDraft) -> InMemoryArticlesRepository:
    """Repository pre-loaded with one article (slug='first-post')."""
    return InMemoryArticlesRepository(
        items=[Article(id=1, **sample_draft.model_dump())]
    )


@pytest.fixture
def cognitive() -> FakeCognitiveLayer:
    return FakeCognitiveLayer(suggestion="Improved suggestion.")


@pytest.fixture
def cognitive_clean() -> FakeCognitiveLayer:
    """Cognitive layer that returns 'CLEAN' for all review calls."""
    return FakeCognitiveLayer(suggestion="CLEAN")


@pytest.fixture
def publishable_article(sample_draft: ArticleDraft) -> Article:
    """An article that passes every mechanical check in the pipeline."""
    body = (
        "This is the first paragraph of a publishable article. "
        "It is intentionally long enough to pass the StructureCheck. "
        "It also contains an external citation https://example.com/ref "
        "so the CitationCheck passes. "
    ) * 5
    return Article(
        id=99,
        author="jane.doe",
        title="A reasonable headline about software design",
        slug="publishable-article",
        summary="A summary that is long enough to pass the structure check, easily.",
        body=body,
        published_on=date(2024, 6, 1),
        status=ArticleStatus.DRAFT,
    )


@pytest.fixture
def draft_article(sample_draft: ArticleDraft) -> Article:
    """An article that violates StructureCheck (short body) AND CitationCheck."""
    return Article(id=42, **sample_draft.model_dump(), status=ArticleStatus.DRAFT)
